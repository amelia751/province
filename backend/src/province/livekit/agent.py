"""
LiveKit AI Agent for Province Legal Operating System.

This module implements a real-time voice agent for legal consultations,
document drafting assistance, and legal Q&A using LiveKit's agent framework.
"""

import asyncio
import hashlib
import json
import os
import signal
import sys
import threading
import time
import traceback
import httpx
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, AsyncIterable, Dict, List

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentSession,
    ChatContext,
    ChatMessage,
    JobContext,
    JobRequest,
    ModelSettings,
    RoomInputOptions,
    WorkerOptions,
    WorkerType,
    ErrorEvent,
    CloseEvent,
    UserStateChangedEvent,
    AgentStateChangedEvent,
    FunctionTool,
    llm,
    tts,
)
from livekit.plugins import deepgram, google, cartesia, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()

AGENT_ENV = os.getenv("AGENT_ENV", "production")
AWS_BACKEND_URL = os.getenv("AWS_BACKEND_URL", "http://localhost:8000")

# Constants
AGENT_TYPING_START = "AGENT_TYPING_START"
AGENT_TYPING_STOP = "AGENT_TYPING_STOP"
AGENT_INITIALIZATION_FAILED = "AGENT_INITIALIZATION_FAILED"

# Global health status tracking
agent_health_status = {
    "status": "starting",
    "active_jobs": 0,
    "start_time": time.time(),
    "last_heartbeat": time.time(),
}


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check server for monitoring"""

    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            agent_health_status["last_heartbeat"] = time.time()
            uptime = time.time() - agent_health_status["start_time"]
            is_healthy = (
                agent_health_status["status"] in ["running", "ready"]
                and uptime > 10
            )

            status_code = 200 if is_healthy else 503
            response = {
                "status": agent_health_status["status"],
                "active_jobs": agent_health_status["active_jobs"],
                "uptime_seconds": int(uptime),
                "healthy": is_healthy,
                "timestamp": time.time(),
            }

            self.send_response(status_code)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return  # Suppress logs


def start_health_server():
    """Start health check server in background thread"""
    port = int(os.getenv("HEALTH_CHECK_PORT", "8080"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        print(f"[AGENT] Health server failed to start: {e}")


class InterruptionManager:
    """Centralized interruption management for speech and text generation"""

    def __init__(self, room: rtc.Room, assistant=None, session=None):
        self.room = room
        self.assistant = assistant
        self.session = session
        self.is_generating = False
        self.current_generation_task = None
        self.lock = asyncio.Lock()

    async def interrupt(self, reason: str = "user_input"):
        """Interrupt any ongoing generation/speech"""
        async with self.lock:
            if self.session:
                try:
                    print(f"[INTERRUPTION] Clearing audio buffer: {reason}")
                    await self.session.interrupt()
                except Exception as e:
                    print(f"[INTERRUPTION] Failed to interrupt session: {e}")

            if self.is_generating and self.current_generation_task:
                print(f"[INTERRUPTION] Canceling generation: {reason}")
                self.current_generation_task.cancel()
                try:
                    await self.current_generation_task
                except asyncio.CancelledError:
                    print("[INTERRUPTION] Generation cancelled")
                except Exception as ex:
                    print(f"[INTERRUPTION] Error: {ex}")
                finally:
                    self.is_generating = False
                    self.current_generation_task = None
                    if self.assistant:
                        self.assistant.is_speaking = False

    async def generate_reply_with_interruption_support(
        self, session: AgentSession, user_input: str, context: str = ""
    ):
        """Generate reply with full interruption support"""

        async def _generation_task():
            try:
                self.is_generating = True
                await session.generate_reply(user_input=user_input)
                print(f"[INTERRUPTION] Generation completed - {context}")
            except asyncio.CancelledError:
                print(f"[INTERRUPTION] Generation cancelled - {context}")
                raise
            except Exception as ex:
                print(f"[INTERRUPTION] Generation failed: {ex}")

        self.current_generation_task = asyncio.create_task(_generation_task())
        try:
            await self.current_generation_task
        except asyncio.CancelledError:
            print("[INTERRUPTION] Task was cancelled")


class LegalAssistant(Agent):
    """Legal AI Assistant for Province"""

    def __init__(self, room: rtc.Room) -> None:
        super().__init__(chat_ctx=None, instructions="")
        self.room = room
        self.initial_context_received: bool = False
        self.user_id = None
        self.matter_id = None
        self.document_type = None
        self.is_speaking = False
        self.interruption_manager = InterruptionManager(room, assistant=self)

    async def send_typing_start(self):
        try:
            await self.room.local_participant.publish_data(
                AGENT_TYPING_START.encode("utf-8"), topic="agent_status"
            )
        except Exception as e:
            print(f"[AGENT] Error sending typing start: {e}")

    async def send_typing_stop(self):
        try:
            await self.room.local_participant.publish_data(
                AGENT_TYPING_STOP.encode("utf-8"), topic="agent_status"
            )
        except Exception as e:
            print(f"[AGENT] Error sending typing stop: {e}")

    async def generate_reply(
        self, session: AgentSession, user_input: str, context: str = ""
    ):
        """Unified method to generate replies with interruption support"""
        await self.send_typing_start()
        await self.interruption_manager.generate_reply_with_interruption_support(
            session, user_input, context
        )

    async def handle_voice_interruption(self):
        """Handle voice-based interruptions"""
        await self.interruption_manager.interrupt("voice_input")
        self.is_speaking = False

    async def stt_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> AsyncIterable[str]:
        try:
            async for transcription_chunk in Agent.default.stt_node(
                self, audio, model_settings
            ):
                try:
                    event_type = transcription_chunk.type

                    if str(event_type) == "SpeechEventType.INTERIM_TRANSCRIPT":
                        if (
                            transcription_chunk.alternatives
                            and len(transcription_chunk.alternatives) > 0
                        ):
                            text = transcription_chunk.alternatives[0].text.strip()
                            if len(text) > 2:
                                try:
                                    await self.handle_voice_interruption()
                                except Exception as e:
                                    print(f"[STT] Error handling interruption: {e}")

                    elif str(event_type) == "SpeechEventType.FINAL_TRANSCRIPT":
                        if (
                            hasattr(transcription_chunk, "alternatives")
                            and transcription_chunk.alternatives
                        ):
                            for alternative in transcription_chunk.alternatives:
                                if hasattr(alternative, "text") and alternative.text:
                                    print(f"[STT] Final: {alternative.text}")
                                    try:
                                        user_message = f"USER_SPEECH:{alternative.text}"
                                        await self.room.local_participant.publish_data(
                                            user_message.encode("utf-8"),
                                            topic="user_transcription",
                                        )
                                    except Exception as e:
                                        print(f"[STT] Error publishing: {e}")

                    yield transcription_chunk

                except Exception as e:
                    print(f"[STT] Error processing chunk: {e}")
                    yield transcription_chunk

        except Exception as e:
            print(f"[STT] Critical error: {e}")

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        try:
            self.is_speaking = True
            self.interruption_manager.is_generating = True

            raw_text = ""
            async for chunk in text:
                if not self.is_speaking:
                    print("[TTS] Interrupted during text gathering")
                    return
                raw_text += chunk

            cleaned_text = raw_text.strip()
            print(f"[TTS] Text: {cleaned_text}")

            if not raw_text or not raw_text.strip():
                print("[TTS] Empty response, skipping")
                return

            await self.send_typing_stop()

            try:
                await self.room.local_participant.publish_data(
                    raw_text.rstrip("\n").encode("utf-8"), topic="chat_message"
                )
            except Exception as e:
                print(f"[TTS] Error publishing message: {e}")

            async def single_chunk_iter():
                yield cleaned_text

            if not self.is_speaking:
                print("[TTS] Interrupted before TTS start")
                return

            try:
                print("[TTS] Starting audio generation...")
                frame_count = 0
                async for frame in Agent.default.tts_node(
                    self, single_chunk_iter(), model_settings
                ):
                    if not self.is_speaking:
                        print("[TTS] Interrupted by user")
                        break

                    frame_count += 1
                    if frame_count == 1:
                        print("[TTS] First frame received")
                    yield frame

                print(f"[TTS] Completed, frames: {frame_count}")

            except Exception as e:
                print(f"[TTS] Error: {e}")

        finally:
            self.is_speaking = False
            if self.interruption_manager.is_generating:
                self.interruption_manager.is_generating = False
            print("[TTS] Stopped")

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[FunctionTool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[llm.ChatChunk]:
        """
        Custom LLM node that delegates to AWS System Agent instead of local LLM.
        This implements the two-layer architecture: LiveKit Edge Agent → AWS System Agent.
        """
        try:
            await self.send_typing_start()
            
            # Extract the last user message from chat context
            user_message = ""
            if chat_ctx.messages:
                for msg in reversed(chat_ctx.messages):
                    if msg.role == "user":
                        user_message = msg.content
                        break
            
            if not user_message:
                print("[LLM] No user message found in chat context")
                await self.send_typing_stop()
                return
            
            print(f"[LLM] Delegating to AWS System Agent: {user_message[:100]}...")
            
            # Delegate to AWS System Agent via /api/v1/agent/invoke
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "tenant_id": "default",
                    "matter_id": self.matter_id,
                    "utterance": user_message,
                    "room_id": self.room.name if self.room else None,
                    "session_id": self.user_id,
                    "trace_id": f"lk_{int(time.time())}_{self.user_id}",
                    "agent_name": "legal_drafting"
                }
                
                response = await client.post(
                    f"{AWS_BACKEND_URL}/api/v1/agent/invoke",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"[LLM] AWS System Agent error: {response.status_code} - {error_text}")
                    response_text = "I apologize, but I'm experiencing technical difficulties. Please try again."
                else:
                    result = response.json()
                    response_text = result.get("text", "I'm sorry, I didn't receive a proper response.")
                    
                    # Log citations if present
                    if result.get("citations"):
                        print(f"[LLM] Citations received: {len(result['citations'])}")
                    
                    print(f"[LLM] AWS response: {response_text[:100]}...")
            
            # Convert response to LLM chunks (simulate streaming)
            chunk = llm.ChatChunk(
                choices=[
                    llm.Choice(
                        delta=llm.ChoiceDelta(
                            content=response_text,
                            role="assistant"
                        )
                    )
                ]
            )
            
            yield chunk
            
        except Exception as e:
            print(f"[LLM] Error delegating to AWS: {e}")
            # Fallback response
            fallback_chunk = llm.ChatChunk(
                choices=[
                    llm.Choice(
                        delta=llm.ChoiceDelta(
                            content="I apologize, but I'm experiencing technical difficulties connecting to our legal AI system. Please try again.",
                            role="assistant"
                        )
                    )
                ]
            )
            yield fallback_chunk
        finally:
            await self.send_typing_stop()


@dataclass
class SessionState:
    room_id: str
    context: dict
    start_time: datetime
    last_activity: datetime
    error_count: int = 0


def _setup_event_handlers(session: AgentSession):
    """Setup event handlers for the session"""

    @session.on("error")
    def on_error(event: ErrorEvent):
        print(f"[AGENT] Error from {event.source}: {event.error}")
        if not event.error.recoverable:
            print("[AGENT] Unrecoverable error detected")

    @session.on("close")
    def on_close(event: CloseEvent):
        if event.error:
            print(f"[AGENT] Session closed with error: {event.error}")
        else:
            print("[AGENT] Session closed normally")

    @session.on("user_state_changed")
    def on_user_state_changed(event: UserStateChangedEvent):
        print(f"[AGENT] User state: {event.old_state} -> {event.new_state}")

    @session.on("agent_state_changed")
    def on_agent_state_changed(event: AgentStateChangedEvent):
        print(f"[AGENT] Agent state: {event.old_state} -> {event.new_state}")


async def entrypoint(ctx: JobContext):
    """Main entrypoint for LiveKit agent"""
    try:
        print("[AGENT] Entrypoint started")

        await ctx.connect()
        print("[AGENT] Connected to LiveKit")

        participant = await ctx.wait_for_participant()
        print(f"[AGENT] Participant joined: {participant.identity}")

        user_identity = participant.identity

        # Create TTS with fallback
        cartesia_tts = cartesia.TTS(
            model="sonic-2", voice="f8f5f1b2-f02d-4d8e-a40d-fd850a487b3d", speed=0.5
        )
        deepgram_tts = deepgram.TTS(model="aura-asteria-en")
        tts_with_fallback = tts.FallbackAdapter([cartesia_tts, deepgram_tts])

        session = AgentSession(
            stt=deepgram.STT(),
            llm=google.LLM(temperature=0.2),
            tts=tts_with_fallback,
            vad=silero.VAD.load(
                min_silence_duration=0.3,
                prefix_padding_duration=0.2,
                activation_threshold=0.25,
            ),
            turn_detection=MultilingualModel(),
        )

        _setup_event_handlers(session)

        assistant = LegalAssistant(room=ctx.room)
        assistant.user_id = user_identity
        assistant.interruption_manager.session = session

        print(f"[AGENT] Starting session in room: {ctx.room.name}")

        # Register RPC handlers
        async def handle_set_instructions(data):
            try:
                await assistant.interruption_manager.interrupt("set_instructions")

                parsed = json.loads(data.payload)
                assistant.initial_context_received = True
                assistant.matter_id = parsed.get("matter_id")
                assistant.document_type = parsed.get("document_type")

                # Set legal assistant instructions
                instructions = f"""You are a legal AI assistant for Province, a legal operating system.

You help with:
- Legal document drafting and review
- Citation validation and legal research
- Deadline management and matter tracking
- Legal Q&A and consultation

Be professional, precise, and cite relevant legal authorities when applicable.
Keep responses concise but thorough."""

                await assistant.update_instructions(instructions)

                # Send greeting
                greeting = "Hello! I'm your legal AI assistant. How can I help you today?"
                await assistant.generate_reply(session, greeting, "initial_greeting")

                return "ok"
            except Exception as ex:
                print(f"[AGENT] Error in set_instructions: {ex}")
                return "error"

        async def handle_user_message(data):
            try:
                payload = data.payload
                text = None

                try:
                    parsed = json.loads(payload)
                    if isinstance(parsed, dict):
                        text = parsed.get("text") or parsed.get("message")
                    elif isinstance(parsed, str):
                        text = parsed
                except Exception:
                    text = payload

                if not text or not str(text).strip():
                    return "error: empty_message"

                text = str(text).strip()
                await assistant.interruption_manager.interrupt("user_text_message")

                if len(text) >= 1:
                    await assistant.generate_reply(session, text, "text_message")

                return "ok"
            except Exception as e:
                print(f"[AGENT] Error in user_message: {e}")
                return f"error: {str(e)}"

        async def handle_ping(data):
            print(f"[AGENT] Ping: {data.payload}")
            return "pong"

        # Register RPC methods
        print(f"[AGENT] Registering RPC methods for: {participant.identity}")
        participant.register_rpc_method("set_instructions", handle_set_instructions)
        participant.register_rpc_method("user_message", handle_user_message)
        participant.register_rpc_method("ping", handle_ping)

        print("[AGENT] RPC methods registered")

        await ctx.room.local_participant.publish_data(
            "AGENT_READY".encode("utf-8"), topic="agent_status"
        )
        print("[AGENT] Agent ready signal sent")

        await session.start(
            assistant,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC()
            ),
        )

        print(f"[AGENT] Agent joined room: {ctx.room.name}")

    except Exception as e:
        print(f"[AGENT] Critical error: {e}")
        traceback.print_exc()
        raise


async def request_fnc(req: JobRequest):
    """Handle job requests"""
    print(f"[REQUEST] Job request for room: {req.room.sid}")

    room_metadata = json.loads(req.room.metadata or "{}")
    job_env = room_metadata.get("agent_env", "production")

    if job_env != AGENT_ENV:
        print(f"[REQUEST] Rejecting job, env mismatch: {job_env} != {AGENT_ENV}")
        return

    await req.accept(
        name="LegalAssistant",
        identity="assistant",
        attributes={"role": "legal_assistant"},
    )
    print(f"[REQUEST] Job accepted for room: {req.room.sid}")

    room = rtc.Room()
    disconnect_event = asyncio.Event()

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant):
        if len(room.remote_participants) == 0:
            print("[REQUEST] All participants left")
            disconnect_event.set()

    @room.on("disconnected")
    def on_room_disconnected():
        print("[REQUEST] Room disconnected")
        disconnect_event.set()

    try:
        await disconnect_event.wait()
    except asyncio.CancelledError:
        print("[REQUEST] Agent cancelled")
    finally:
        await room.disconnect()
        print("[REQUEST] Agent shutdown")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("[AGENT] Shutdown signal received")
    sys.exit(0)


def compute_load(worker) -> float:
    """Compute worker load"""
    active_jobs = len(worker.active_jobs) if hasattr(worker, "active_jobs") else 0
    agent_health_status["active_jobs"] = active_jobs

    max_concurrent_jobs = int(os.getenv("AGENT_MAX_CONCURRENT_JOBS", "8"))
    load = min(active_jobs / max_concurrent_jobs, 1.0)

    print(f"[AGENT] Load: {load:.2f} ({active_jobs}/{max_concurrent_jobs})")

    if load > 0.9:
        agent_health_status["status"] = "high_load"
    elif load > 0:
        agent_health_status["status"] = "running"
    else:
        agent_health_status["status"] = "ready"

    return load


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "download-files":
            print("[AGENT] Downloading model files...")
            sys.exit(0)
        elif command in ("start", "dev"):
            print(f"[AGENT] Starting with '{command}' command")
        else:
            print(f"[AGENT] Unknown command: {command}")
            sys.exit(1)
    else:
        print("[AGENT] Starting agent directly")

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("[AGENT] Starting agent worker...")

    # Start health server
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    print(f"[AGENT] LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    print(f"[AGENT] API Key: {os.getenv('LIVEKIT_API_KEY')[:10] if os.getenv('LIVEKIT_API_KEY') else 'Not set'}...")

    max_concurrent_jobs = int(os.getenv("AGENT_MAX_CONCURRENT_JOBS", "8"))
    load_threshold = float(os.getenv("AGENT_LOAD_THRESHOLD", "0.9"))
    shutdown_timeout = int(os.getenv("AGENT_SHUTDOWN_TIMEOUT", "60"))

    print(f"[AGENT] Max concurrent jobs: {max_concurrent_jobs}")
    print(f"[AGENT] Load threshold: {load_threshold}")
    print(f"[AGENT] Shutdown timeout: {shutdown_timeout}s")

    try:
        agent_health_status["status"] = "ready"

        agents.cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint,
                request_fnc=request_fnc,
                worker_type=WorkerType.ROOM,
                load_fnc=compute_load,
                load_threshold=load_threshold,
                shutdown_process_timeout=shutdown_timeout,
                agent_name="LegalAssistant",
            )
        )
    except Exception as e:
        print(f"[AGENT] Error starting worker: {e}")
        traceback.print_exc()

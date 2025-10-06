"""
LiveKit API routes for Province.

Provides REST API endpoints for creating rooms, generating tokens,
and managing LiveKit real-time sessions.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit import api
from livekit.api import LiveKitAPI
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

router = APIRouter(prefix="/livekit", tags=["livekit"])

# LiveKit credentials
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")


def validate_livekit_config():
    """Validate LiveKit configuration"""
    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        raise HTTPException(
            status_code=500,
            detail="Missing LiveKit configuration. Please set LIVEKIT_URL, "
            "LIVEKIT_API_KEY, and LIVEKIT_API_SECRET environment variables.",
        )


# Request/Response Models
class TokenRequest(BaseModel):
    room_name: str
    participant_identity: str
    participant_name: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    url: str


class CreateRoomRequest(BaseModel):
    room_name: str
    metadata: Optional[Dict[str, Any]] = None


class RoomInfo(BaseModel):
    sid: str
    name: str
    created_at: int


class CreateRoomResponse(BaseModel):
    room: RoomInfo


class ListRoomsResponse(BaseModel):
    rooms: list[Dict[str, Any]]


class ParticipantInfo(BaseModel):
    sid: str
    identity: str
    name: str
    is_publisher: bool


class ListParticipantsResponse(BaseModel):
    participants: list[ParticipantInfo]


class HealthResponse(BaseModel):
    status: str
    livekit_configured: bool


@router.post("/token", response_model=TokenResponse)
async def create_token(request: TokenRequest) -> TokenResponse:
    """
    Create a LiveKit access token for a user.

    Args:
        request: Token request with room_name and participant_identity

    Returns:
        Access token and LiveKit URL
    """
    try:
        validate_livekit_config()

        participant_name = request.participant_name or request.participant_identity

        # Create access token
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(request.participant_identity).with_name(
            participant_name
        ).with_grants(
            api.VideoGrants(
                room_join=True,
                room=request.room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )

        return TokenResponse(token=token.to_jwt(), url=LIVEKIT_URL)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create token: {str(e)}"
        )


@router.post("/room", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest) -> CreateRoomResponse:
    """
    Create a LiveKit room.

    Args:
        request: Room creation request with room_name and optional metadata

    Returns:
        Created room information
    """
    try:
        validate_livekit_config()

        metadata = request.metadata or {}

        # Add default agent environment if not specified
        if "agent_env" not in metadata:
            metadata["agent_env"] = os.getenv("AGENT_ENV", "production")

        # Create LiveKit API client
        lk_api = LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)

        # Create room
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=request.room_name,
                empty_timeout=300,  # 5 minutes
                max_participants=10,
                metadata=str(metadata),
            )
        )

        return CreateRoomResponse(
            room=RoomInfo(
                sid=room.sid, name=room.name, created_at=room.creation_time
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create room: {str(e)}"
        )


@router.get("/room", response_model=ListRoomsResponse)
async def list_rooms() -> ListRoomsResponse:
    """
    List all active LiveKit rooms.

    Returns:
        List of active rooms
    """
    try:
        validate_livekit_config()

        lk_api = LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())

        return ListRoomsResponse(
            rooms=[
                {
                    "sid": room.sid,
                    "name": room.name,
                    "num_participants": room.num_participants,
                }
                for room in rooms.rooms
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list rooms: {str(e)}"
        )


@router.delete("/room/{room_name}")
async def delete_room(room_name: str):
    """
    Delete a LiveKit room.

    Args:
        room_name: Name of the room to delete

    Returns:
        Success message
    """
    try:
        validate_livekit_config()

        lk_api = LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        await lk_api.room.delete_room(api.DeleteRoomRequest(room=room_name))

        return {"message": "Room deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete room: {str(e)}"
        )


@router.get("/room/{room_name}/participants", response_model=ListParticipantsResponse)
async def list_participants(room_name: str) -> ListParticipantsResponse:
    """
    List participants in a room.

    Args:
        room_name: Name of the room

    Returns:
        List of participants in the room
    """
    try:
        validate_livekit_config()

        lk_api = LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        participants = await lk_api.room.list_participants(
            api.ListParticipantsRequest(room=room_name)
        )

        return ListParticipantsResponse(
            participants=[
                ParticipantInfo(
                    sid=p.sid,
                    identity=p.identity,
                    name=p.name,
                    is_publisher=p.permission.can_publish,
                )
                for p in participants.participants
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list participants: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for LiveKit service.

    Returns:
        Service health status and configuration status
    """
    try:
        validate_livekit_config()
        configured = True
    except HTTPException:
        configured = False

    return HealthResponse(
        status="ok" if configured else "error", livekit_configured=configured
    )

# LiveKit Real-Time Communication Setup

This directory contains the LiveKit integration for Province's real-time AI legal assistant.

## Overview

The LiveKit integration provides:
- Real-time voice communication with AI legal assistant
- Speech-to-text (STT) using Deepgram
- Text-to-speech (TTS) using Cartesia/Deepgram
- AI responses using Google Gemini
- Voice activity detection (VAD) using Silero
- Interruption handling for natural conversations

## Components

### 1. Agent (`agent.py`)
The main LiveKit agent that handles:
- Real-time voice conversations
- Speech recognition and synthesis
- AI-powered legal assistance
- Session management and interruption handling
- Health monitoring

### 2. API Routes (`../api/v1/livekit.py`)
FastAPI endpoints for:
- Creating LiveKit rooms
- Generating access tokens
- Managing participants
- Room lifecycle management

## Environment Variables

Required environment variables (see `backend/.env.local`):

```bash
# LiveKit Connection
LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Agent Configuration
AGENT_ENV=production
AGENT_MAX_CONCURRENT_JOBS=8
AGENT_LOAD_THRESHOLD=0.9
AGENT_SHUTDOWN_TIMEOUT=60
HEALTH_CHECK_PORT=8080

# TTS/STT API Keys
DEEPGRAM_API_KEY=your_deepgram_api_key
CARTESIA_API_KEY=your_cartesia_api_key
GOOGLE_APPLICATION_CREDENTIALS=your_google_credentials_json
```

## Running the Agent

### Development Mode

```bash
cd backend
python -m province.livekit.agent dev
```

### Production Mode

```bash
cd backend
python -m province.livekit.agent start
```

### Using Docker

```bash
cd backend
docker build -t province-livekit-agent -f Dockerfile.agent .
docker run -e LIVEKIT_URL=$LIVEKIT_URL \
           -e LIVEKIT_API_KEY=$LIVEKIT_API_KEY \
           -e LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET \
           province-livekit-agent
```

## API Usage

### 1. Create a Room

```bash
curl -X POST http://localhost:8000/api/v1/livekit/room \
  -H "Content-Type: application/json" \
  -d '{
    "room_name": "legal-consultation-123",
    "metadata": {
      "matter_id": "matter-456",
      "document_type": "contract"
    }
  }'
```

### 2. Generate Access Token

```bash
curl -X POST http://localhost:8000/api/v1/livekit/token \
  -H "Content-Type: application/json" \
  -d '{
    "room_name": "legal-consultation-123",
    "participant_identity": "user-789",
    "participant_name": "John Doe"
  }'
```

### 3. List Active Rooms

```bash
curl http://localhost:8000/api/v1/livekit/room
```

### 4. Delete a Room

```bash
curl -X DELETE http://localhost:8000/api/v1/livekit/room/legal-consultation-123
```

## Frontend Integration

### Install LiveKit Client SDK

```bash
cd frontend
npm install livekit-client @livekit/components-react
```

### Example Usage

```typescript
import { Room } from 'livekit-client';

async function connectToLegalAssistant() {
  // Get token from backend
  const response = await fetch('/api/v1/livekit/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      room_name: 'legal-consultation-123',
      participant_identity: userId,
      participant_name: userName,
    }),
  });

  const { token, url } = await response.json();

  // Connect to room
  const room = new Room();
  await room.connect(url, token);

  // Start conversation
  await room.localParticipant.enableMicrophone();

  return room;
}
```

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ◄─────► │ LiveKit Room │ ◄─────► │ AI Agent    │
│   (React)   │  WebRTC │   (Cloud)    │  WebRTC │  (Python)   │
└─────────────┘         └──────────────┘         └─────────────┘
      │                                                  │
      │                                                  │
      ▼                                                  ▼
┌─────────────┐                                  ┌─────────────┐
│  Backend    │                                  │   AI LLM    │
│  (FastAPI)  │                                  │  (Gemini)   │
└─────────────┘                                  └─────────────┘
      │                                                  │
      │                                                  │
      ▼                                                  ▼
┌─────────────┐                                  ┌─────────────┐
│  DynamoDB   │                                  │  STT/TTS    │
│  (Matters)  │                                  │ (Deepgram)  │
└─────────────┘                                  └─────────────┘
```

## Features

### 1. Voice Interruption
The agent supports natural conversation interruption. Users can interrupt the AI at any time by speaking.

### 2. Real-Time Transcription
All user speech is transcribed in real-time and can be displayed in the UI.

### 3. Text Messaging
Users can also send text messages to the agent via RPC calls.

### 4. Session Management
The agent maintains conversation context and can be updated with new instructions dynamically.

### 5. Health Monitoring
A health check server runs on port 8080 for monitoring agent status.

## Troubleshooting

### Agent Not Connecting
1. Check LiveKit credentials are set correctly
2. Verify network connectivity to LiveKit cloud
3. Check agent logs for errors

### No Audio
1. Ensure microphone permissions are granted
2. Check browser console for WebRTC errors
3. Verify audio tracks are published

### AI Not Responding
1. Check API keys for Deepgram/Google are valid
2. Verify agent received initial instructions via RPC
3. Check agent logs for LLM errors

## Dependencies

All dependencies are listed in `backend/requirements.txt`:
- livekit
- livekit-api
- livekit-agents
- livekit-plugins-deepgram
- livekit-plugins-google
- livekit-plugins-cartesia
- livekit-plugins-silero

## Security Notes

1. Never expose API keys in client-side code
2. Always generate tokens server-side
3. Use short-lived tokens (default 1 hour)
4. Implement proper authentication before token generation
5. Monitor room creation to prevent abuse

## Next Steps

1. Integrate with Province's matter management system
2. Add citation validation during conversations
3. Implement document context awareness
4. Add legal knowledge base integration
5. Create conversation transcripts and summaries

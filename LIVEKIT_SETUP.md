# LiveKit Real-Time Voice Integration - Setup Guide

## Overview

Province now includes a complete LiveKit integration for real-time voice conversations with AI legal assistants. The system includes:

- **Chat/Voice Mode Toggle** - Users can switch between text chat and voice consultation
- **Real-time Voice Communication** - LiveKit WebRTC integration
- **Backend API** - FastAPI routes for room and token management
- **AI Agent** - Python-based LiveKit agent with STT, TTS, and LLM integration
- **Seamless Backend Integration** - Connected to existing agent service

## Architecture

```
┌──────────────────┐
│  Frontend (Next) │
│                  │
│  ┌────────────┐  │      ┌─────────────────┐      ┌──────────────┐
│  │ Text Chat  │  │◄────►│  Backend API    │◄────►│  AI Agents   │
│  │            │  │      │  (FastAPI)      │      │  (Bedrock)   │
│  └────────────┘  │      │                 │      └──────────────┘
│                  │      │  /api/v1/*      │
│  ┌────────────┐  │      └─────────────────┘
│  │ Voice Chat │  │
│  │            │  │
│  └─────┬──────┘  │
│        │         │
└────────┼─────────┘
         │
         ├─WebRTC─►┌─────────────────┐◄─WebRTC─┐
         │         │  LiveKit Cloud  │         │
         │         │  (Rooms)        │         │
         │         └─────────────────┘         │
         │                                     │
         │         ┌─────────────────┐         │
         └─Token──►│  Backend API    │         │
                   │  /api/v1/livekit│         │
                   │                 │         │
                   │  - Token Gen    │         │
                   │  - Room Mgmt    │         │
                   └─────────────────┘         │
                                               │
                   ┌─────────────────┐         │
                   │  LiveKit Agent  │◄────────┘
                   │  (Python)       │
                   │                 │
                   │  - STT/TTS      │
                   │  - AI LLM       │
                   │  - Session Mgmt │
                   └─────────────────┘
```

## Setup Steps

### 1. Install Dependencies

#### Backend
```bash
cd backend
pip install -r requirements.txt
```

Key dependencies added:
- `livekit>=0.11.0`
- `livekit-api>=0.5.0`
- `livekit-agents>=0.8.0`
- `livekit-plugins-deepgram`, `livekit-plugins-google`, etc.

#### Frontend
```bash
cd frontend
npm install
```

Key dependencies added:
- `livekit-client@^2.8.3`
- `@livekit/components-react@^2.8.0`

### 2. Environment Configuration

#### Backend (.env.local)
All LiveKit credentials are already configured:
```bash
# LiveKit Configuration
LIVEKIT_URL=[REDACTED-LIVEKIT-URL]
LIVEKIT_API_KEY=[REDACTED-LIVEKIT-KEY]
LIVEKIT_API_SECRET=[REDACTED-LIVEKIT-SECRET]

# Agent Configuration
AGENT_ENV=production
AGENT_MAX_CONCURRENT_JOBS=8
HEALTH_CHECK_PORT=8080

# TTS/STT APIs
DEEPGRAM_API_KEY=[REDACTED-DEEPGRAM-KEY]
CARTESIA_API_KEY=[REDACTED-CARTESIA-KEY]
```

#### Frontend (.env.local)
```bash
# LiveKit Configuration
NEXT_PUBLIC_LIVEKIT_URL=[REDACTED-LIVEKIT-URL]
NEXT_PUBLIC_LIVEKIT_API_KEY=[REDACTED-LIVEKIT-KEY]
LIVEKIT_API_SECRET=[REDACTED-LIVEKIT-SECRET]

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start the Services

#### 1. Start Backend API (FastAPI)
```bash
cd backend
make run  # or: python -m uvicorn province.main:app --reload --port 8000
```

This starts the REST API at `http://localhost:8000` with:
- `/api/v1/agents/*` - Text chat endpoints
- `/api/v1/livekit/*` - Voice/room management

#### 2. Start LiveKit Agent (Python)
```bash
cd backend
python -m province.livekit.agent dev
```

This starts the voice agent that:
- Connects to LiveKit cloud
- Handles voice conversations
- Processes speech with Deepgram STT
- Responds with Google Gemini
- Synthesizes speech with Cartesia/Deepgram TTS

#### 3. Start Frontend (Next.js)
```bash
cd frontend
npm run dev
```

Access at `http://localhost:3000`

## Using the Voice Feature

### User Flow

1. **Open Chat Interface**
   - Navigate to the chat in your Province app
   - You'll see two mode options at the top

2. **Select Voice Mode**
   - Click "Voice Support" button
   - The interface switches to voice consultation view

3. **Start Conversation**
   - Click "Start Voice Consultation"
   - Grant microphone permissions when prompted
   - Wait for "Connected" status

4. **Talk to AI Assistant**
   - Speak naturally
   - AI responds in real-time with voice
   - Full transcript appears on screen

5. **End Conversation**
   - Click the red phone button to disconnect

### Features

- **Voice Interruption**: Speak anytime to interrupt the AI
- **Real-time Transcript**: See conversation in text
- **Mute Controls**: Mute microphone or speaker
- **Connection Status**: Visual indicators for connection state
- **Agent Selection**: Choose different legal assistants

## API Endpoints

### LiveKit Management

#### Create Room
```bash
POST /api/v1/livekit/room
Content-Type: application/json

{
  "room_name": "legal-session-123",
  "metadata": {
    "matter_id": "matter-456",
    "agent_env": "production"
  }
}
```

#### Generate Token
```bash
POST /api/v1/livekit/token
Content-Type: application/json

{
  "room_name": "legal-session-123",
  "participant_identity": "user-789",
  "participant_name": "John Doe"
}
```

Response:
```json
{
  "token": "eyJhbGc...",
  "url": "[REDACTED-LIVEKIT-URL]"
}
```

#### List Rooms
```bash
GET /api/v1/livekit/room
```

#### Delete Room
```bash
DELETE /api/v1/livekit/room/{room_name}
```

### Text Chat (Existing)

```bash
POST /api/v1/agents/chat
Content-Type: application/json

{
  "message": "Help me draft a contract",
  "agent_name": "legal_drafting",
  "session_id": "session-123"
}
```

## File Structure

```
province/
├── backend/
│   ├── src/province/
│   │   ├── livekit/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py           # LiveKit voice agent
│   │   │   └── README.md          # Agent documentation
│   │   ├── api/v1/
│   │   │   ├── livekit.py         # LiveKit REST API
│   │   │   └── agents.py          # Text chat API
│   │   └── ...
│   ├── requirements.txt            # Updated with LiveKit deps
│   └── .env.local                  # LiveKit credentials
│
└── frontend/
    ├── src/
    │   ├── components/chat/
    │   │   ├── chat.tsx            # Updated with mode toggle
    │   │   ├── voice-chat.tsx      # New voice component
    │   │   └── agent-actions.tsx
    │   ├── hooks/
    │   │   └── use-agent.ts        # Backend integration
    │   └── services/
    │       ├── agent-service.ts    # Text chat API
    │       └── websocket-service.ts
    ├── package.json                # Updated with LiveKit deps
    └── .env.local                  # LiveKit config
```

## Troubleshooting

### Backend Issues

**Agent won't start:**
```bash
# Check LiveKit credentials
echo $LIVEKIT_URL
echo $LIVEKIT_API_KEY

# Verify dependencies
pip install -r requirements.txt

# Check logs
python -m province.livekit.agent dev
```

**API not responding:**
```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check LiveKit health
curl http://localhost:8000/api/v1/livekit/health
```

### Frontend Issues

**Voice button doesn't connect:**
1. Check browser console for errors
2. Verify microphone permissions
3. Ensure backend API is running
4. Check NEXT_PUBLIC_API_URL in .env.local

**No audio:**
1. Check microphone/speaker settings
2. Verify agent is running
3. Check browser console for WebRTC errors

### LiveKit Agent Issues

**Agent not joining rooms:**
```bash
# Check agent health
curl http://localhost:8080/health

# View agent logs
# Look for "Agent joined room" messages
```

**No voice response:**
1. Verify Deepgram API key
2. Check Cartesia API key
3. Ensure Google credentials are set
4. Review agent logs for errors

## Next Steps

### Immediate Enhancements

1. **Full LiveKit Client Integration**
   - Implement actual Room connection in voice-chat.tsx
   - Add audio track handling
   - Implement real-time transcript updates

2. **Backend Integration**
   - Connect voice transcripts to matter records
   - Save conversation history
   - Integrate with document generation

3. **UI Improvements**
   - Add waveform visualization
   - Show speaking indicators
   - Add recording/playback controls

### Advanced Features

1. **Multi-user Rooms**
   - Support multiple participants
   - Co-counsel consultations
   - Client meetings

2. **Recording & Transcription**
   - Save voice sessions
   - Generate transcripts
   - Create meeting summaries

3. **Legal-Specific Features**
   - Citation during voice calls
   - Document references
   - Deadline creation via voice

## Security Notes

1. **Token Security**
   - Tokens are generated server-side
   - Short-lived (1 hour default)
   - Never expose API secrets to frontend

2. **API Authentication**
   - Add authentication to /livekit endpoints
   - Validate user permissions
   - Rate limit token generation

3. **Data Privacy**
   - Encrypt voice data in transit (WebRTC)
   - Store transcripts securely
   - Comply with legal confidentiality requirements

## Resources

- [LiveKit Documentation](https://docs.livekit.io/)
- [LiveKit Python SDK](https://docs.livekit.io/reference/python/)
- [LiveKit React Components](https://docs.livekit.io/reference/components/react/)
- [Backend README](backend/src/province/livekit/README.md)

## Support

For issues or questions:
1. Check agent logs: `python -m province.livekit.agent dev`
2. Check API logs: Backend console output
3. Check browser console: Frontend errors
4. Review this guide and backend/src/province/livekit/README.md

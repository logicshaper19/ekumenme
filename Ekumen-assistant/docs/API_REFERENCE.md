# API Reference

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`

---

## Authentication

All API endpoints require JWT authentication.

```bash
# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}

# Use token
curl -H "Authorization: Bearer eyJ..." http://localhost:8000/api/v1/...
```

---

## Chat Endpoints

### POST /api/v1/chat/message

Send a chat message.

**Request:**
```json
{
  "message": "What's the weather forecast?",
  "conversation_id": "uuid-here"
}
```

**Response:**
```json
{
  "response": "The weather forecast shows...",
  "agent_type": "weather",
  "confidence": 0.95,
  "conversation_id": "uuid-here"
}
```

### WebSocket /ws/chat

Real-time chat with streaming responses.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat?token=JWT_TOKEN');

ws.send(JSON.stringify({
  message: "Help me plan spring planting",
  conversation_id: "uuid-here"
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.chunk); // Streaming response
};
```

---

## Farm Data Endpoints

### GET /api/v1/farm-data/{siret}

Get farm data for SIRET.

**Response:**
```json
{
  "siret": "12345678901234",
  "exploitations": [...],
  "parcelles": [...]
}
```

---

## Health Endpoints

### GET /health

Application health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "Ekumen Assistant",
  "version": "1.0.0"
}
```

---

## Error Responses

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

**Status Codes:**
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

---

For complete API documentation, see [Architecture](ARCHITECTURE.md).

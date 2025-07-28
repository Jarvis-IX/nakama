# API Reference

This document provides detailed information about the Jarvis AI Assistant API endpoints, including request/response formats and examples.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require API key authentication. Include your API key in the `X-API-Key` header:

```http
GET /api/v1/status
X-API-Key: your-api-key-here
```

## Endpoints

### Health Check

#### GET /

Check if the API is running.

**Response**

```json
{
  "message": "Welcome to the Jarvis AI Assistant API!"
}
```

### Chat

#### POST /chat

Send a message to the AI and receive a response.

**Request Body**

```json
{
  "message": "What is the capital of France?",
  "conversation_id": "optional-conversation-id",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| message | string | Yes | The user's message |
| conversation_id | string | No | ID to maintain conversation context |
| temperature | float | No | Controls randomness (0.0-2.0) |
| max_tokens | integer | No | Maximum number of tokens to generate |

**Response**

```json
{
  "response": "The capital of France is Paris.",
  "conversation_id": "generated-or-provided-id",
  "tokens_used": 15
}
```

### Streaming Chat

#### POST /chat/stream

Stream the AI's response in real-time.

**Request Body**

Same as the regular chat endpoint.

**Response**

Stream of JSON objects:

```json
{"chunk": "The", "conversation_id": "id"}
{"chunk": " capital", "conversation_id": "id"}
{"chunk": " of France is Paris.", "conversation_id": "id"}
{"done": true, "conversation_id": "id"}
```

### Knowledge Base

#### POST /knowledge/add-text

Add text to the knowledge base.

**Request Body**

```json
{
  "text": "Jarvis is an AI assistant created to help with various tasks.",
  "metadata": {
    "source": "internal",
    "author": "user@example.com"
  }
}
```

**Response**

```json
{
  "status": "success",
  "document_id": "doc-12345",
  "chunks_added": 1
}
```

#### POST /knowledge/add-file

Upload and process a file (PDF, TXT, DOCX).

**Request**

```http
POST /api/v1/knowledge/add-file
Content-Type: multipart/form-data

file=@document.pdf
metadata={"source":"upload","user_id":"user-123"}
```

**Response**

```json
{
  "status": "success",
  "filename": "document.pdf",
  "document_id": "doc-67890",
  "chunks_added": 5,
  "file_size": 1024
}
```

### Search

#### GET /search

Search the knowledge base.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query |
| limit | integer | No | Maximum results to return (default: 5) |
| threshold | float | No | Minimum similarity score (0.0-1.0) |

**Response**

```json
{
  "query": "AI assistant",
  "results": [
    {
      "text": "Jarvis is an AI assistant created to help with various tasks.",
      "score": 0.92,
      "source": "internal",
      "document_id": "doc-12345"
    }
  ]
}
```

### System Status

#### GET /status

Get system status and metrics.

**Response**

```json
{
  "status": "operational",
  "version": "1.0.0",
  "llm": {
    "model": "llama3.2:3b",
    "status": "ready"
  },
  "database": {
    "status": "connected",
    "documents": 42,
    "size_mb": 12.5
  },
  "performance": {
    "avg_response_time_ms": 245.6,
    "requests_processed": 1024
  }
}
```

## Error Handling

Errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error": "error_type"
}
```

### Common Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Request validation failed |
| 500 | Internal Server Error | Server error |

## Rate Limiting

API is rate limited to 60 requests per minute per IP address. Exceeding this limit will result in a `429 Too Many Requests` response.

## Versioning

API version is included in the URL path (e.g., `/api/v1/...`).

## Support

For support, please open an issue in the [GitHub repository](https://github.com/yourusername/jarvis-ai-assistant/issues).

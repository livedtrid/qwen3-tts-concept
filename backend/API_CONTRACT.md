# API Contract

## `POST /api/generate`

Generate a Portuguese TTS clip and return a WAV file.

### Request

- Content-Type: `application/json`
- Body:

```json
{
  "name": "Carlos"
}
```

### Success Response

- Status: `200`
- Content-Type: `audio/wav`
- Body: binary WAV file stream

### Error Responses

- `400` invalid payload (e.g., missing `name`)
- `500` missing server configuration (`DASHSCOPE_API_KEY`)
- `502` upstream DashScope/API/network failure

Error format:

```json
{
  "error": "Human-readable message"
}
```


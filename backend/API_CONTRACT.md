# API Contract

## `POST /api/generate`

Generate a Portuguese TTS clip and return a WAV file.

### Request

- Content-Type: `application/json`
- Body:

```json
{
  "name": "Carlos",
  "phraseIndex": 2
}
```

- `name` is required.
- `phraseIndex` is optional and 1-based. When omitted, the backend picks a random phrase.
- When server env `CHEAP_MODE=true`, `phraseIndex` is ignored and output audio is composed as:
  - generated TTS from raw `name` text
  - followed by one random WAV from `backend/audio/` (auto-converted to match generated WAV format when needed)

### Success Response

- Status: `200`
- Content-Type: `audio/wav`
- Body: binary WAV file stream

### Error Responses

- `400` invalid payload (e.g., missing `name`)
- `500` missing server configuration (`DASHSCOPE_API_KEY`)
- `500` invalid `CHEAP_MODE` local audio setup (missing WAV files or incompatible WAV formats)
- `502` upstream DashScope/API/network failure

Error format:

```json
{
  "error": "Human-readable message"
}
```

## `GET /api/phrases?name=Carlos`

Return the current phrase templates plus their rendered text for the provided name.

### Success Response

- Status: `200`
- Content-Type: `application/json`

```json
{
  "count": 3,
  "phrases": [
    {
      "index": 1,
      "template": "Faltavas tu {name}! ...",
      "text": "Faltavas tu Carlos! ..."
    }
  ]
}
```


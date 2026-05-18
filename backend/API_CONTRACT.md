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


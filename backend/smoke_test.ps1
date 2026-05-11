param(
  [string]$BaseUrl = "http://localhost:5000",
  [string]$Name = "Carlos",
  [string]$OutFile = "sample.wav"
)

Invoke-WebRequest `
  -Uri "$BaseUrl/api/generate" `
  -Method POST `
  -ContentType "application/json" `
  -Body ("{\"name\":\"$Name\"}") `
  -OutFile $OutFile

Write-Host "Saved audio to $OutFile"


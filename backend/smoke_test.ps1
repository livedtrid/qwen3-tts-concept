param(
  [string]$BaseUrl = "http://localhost:5000",
  [string]$Name = "Rita",
  [string]$OutFile = "sample.wav",
  [int]$PhraseIndex,
  [switch]$AllPhrases
)

function Invoke-TtsRequest {
  param(
    [string]$TargetOutFile,
    [int]$TargetPhraseIndex
  )

  $payload = @{
    name = $Name
  }

  if ($PSBoundParameters.ContainsKey('TargetPhraseIndex')) {
    $payload.phraseIndex = $TargetPhraseIndex
  }

  Invoke-WebRequest `
    -Uri "$BaseUrl/api/generate" `
    -Method POST `
    -ContentType "application/json" `
    -Body ($payload | ConvertTo-Json -Compress) `
    -OutFile $TargetOutFile

  if ($PSBoundParameters.ContainsKey('TargetPhraseIndex')) {
    Write-Host "Saved phrase $TargetPhraseIndex audio to $TargetOutFile"
    return
  }

  Write-Host "Saved audio to $TargetOutFile"
}

if ($AllPhrases) {
  $phrasesResponse = Invoke-RestMethod -Uri "$BaseUrl/api/phrases?name=$([uri]::EscapeDataString($Name))"

  foreach ($phrase in $phrasesResponse.phrases) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($OutFile)
    $extension = [System.IO.Path]::GetExtension($OutFile)
    if (-not $extension) {
      $extension = '.wav'
    }

    $targetOutFile = "{0}-phrase-{1}{2}" -f $baseName, $phrase.index, $extension
    Invoke-TtsRequest -TargetOutFile $targetOutFile -TargetPhraseIndex ([int]$phrase.index)
  }

  return
}

if ($PSBoundParameters.ContainsKey('PhraseIndex')) {
  Invoke-TtsRequest -TargetOutFile $OutFile -TargetPhraseIndex $PhraseIndex
  return
}

Invoke-TtsRequest -TargetOutFile $OutFile


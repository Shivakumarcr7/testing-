## Team A — Week 1
- Set up project structure (services/, tests/, scripts/), venv, requirements.txt
- Sarvam API key configured with fail-loud loader
- TTS smoke test: Kannada, Hindi, English audio all produced and verified (bulbul:v2)
- STT smoke test: correct transcripts for Kannada/Hindi; minor mishearing on English
  ("Hello" → "Fellow") — flagged as expected STT variance, not a pipeline bug
- Model names corrected from roadmap doc: saarika:v2.5 (not saaras:v2/saarika:v2,
  both deprecated); multipart uploads need explicit (filename, file, content-type) tuple
- Manual voice-echo demo working end to end
- Git/GitHub setup deferred — will commit full week's work in one batch
- Blockers: none

## Team A — Week 2
- STT service live on port 8001 (POST /transcribe): input validation (file type, size,
  empty check), graceful error handling (400 for bad input, 502 for upstream Sarvam
  failures), 30s timeouts, 3 passing tests
- TTS service live on port 8005 (POST /synthesize): same hardening pattern — language
  validation, text length limits, 30s timeouts, 3 passing tests
- Fixed a real bug during TTS hardening: an invalid `language` value was crashing with
  an unhandled 500 (KeyError on the language-code lookup) — now returns a clean 400
  with a helpful message instead
- Voice-echo demo rebuilt to call the two live services over HTTP (localhost:8001 /
  localhost:8005) instead of calling Sarvam directly — confirmed working end to end
  for Kannada, including audio playback
- Operational note: hit a ConnectionRefusedError when the TTS service's terminal had
  stopped running unnoticed — going forward, labeling terminal tabs (STT-8001,
  TTS-8005, etc.) to avoid losing track of which service is up
- Pushing to GitHub now
- Blockers: none
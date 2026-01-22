# Sample Assets

T012 seeds a reproducible location for demo audio used by the `hb-align process` independent test (spec.md §User Story 1).

- `samples/genesis-001.mp3` is a **placeholder** file so scripts/tests can rely on the path existing in the repo.
- Replace the placeholder with a short mono MP3 (≤30 seconds works) of Genesis 1 narrated according to the pronunciation profile you plan to test. The filename pattern **must** remain `genesis-001.mp3`.
- Recommended encoding: 16 kHz sample rate, 128 kbps, mono channel. Alignments will convert to WAV internally before calling Montreal Forced Aligner.

## Provenance & Licensing

We cannot check real narration audio into the repo because typical recordings remain under copyright. Instead:

1. Record your own short sample or use a public-domain reading (verify license).
2. Drop the MP3 in this folder, overwriting the placeholder.
3. Document the source in commit notes or internal tracker if you plan to share it with the team.

## Regenerating Test Audio (optional)

If you need a synthetic voice for testing, run a short TTS snippet and export it to MP3, then normalize with ffmpeg:

```bash
ffmpeg -i my-tts-output.wav -ar 16000 -ac 1 samples/genesis-001.mp3
```

This keeps the repo portable while giving contributors a canonical location for the sample file.

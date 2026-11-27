# S7 — On-device engine catalog (packaging survey, decision date)

| Engine ID | Packaging | Prebuilt for Windows on ARM64 | Licence |
|---|---|---|---|
| `sherpa-onnx-sensevoice` | Official Rust crate (`static` feature) over ONNX Runtime; one library for VAD, ASR and speaker diarization; no Python | yes | Apache-2.0 |
| `whisper-cpp-turbo` | C/C++ library with Whisper large-v3-turbo weights | yes | MIT |
| `faster-whisper-sidecar` | Python sidecar process; depends on CTranslate2 | **no** — CTranslate2 publishes no Windows ARM64 wheel; it would have to be built from source on the clinician's machine | MIT |
| `handrolled-onnx-whisper` | The app's current in-house module (~700 lines: own mel spectrogram, greedy decode with no beam search or temperature fallback, non-overlapping 30-second hard cuts) | yes (compiled with the app) | in-house |

Model files (download sizes, MB):

| Engine | File | Role | Size MB |
|---|---|---|---|
| `sherpa-onnx-sensevoice` | Silero VAD | voice activity detection — required before ASR | 2 |
| `sherpa-onnx-sensevoice` | SenseVoiceSmall (zh/en/yue/ja/ko) | ASR | 135 |
| `sherpa-onnx-sensevoice` | pyannote segmentation 3.0 (ONNX) | acoustic diarization — segmentation | 7 |
| `sherpa-onnx-sensevoice` | CAM++ speaker embedding, zh_en | acoustic diarization — embeddings | 28 |
| `sherpa-onnx-sensevoice` | Zipformer streaming ASR, English only | optional live-caption model; not used by batch transcription | 70 |
| `whisper-cpp-turbo` | large-v3-turbo | ASR | 1500 |
| `faster-whisper-sidecar` | large-v3 (CTranslate2) | ASR | 3000 |
| `handrolled-onnx-whisper` | Whisper ONNX export | ASR | 1500 |

Channel-based diarization needs no model file. Acoustic diarization (either
`acoustic-fixed-2` or `acoustic-auto-threshold`) needs both diarization model
files listed above.

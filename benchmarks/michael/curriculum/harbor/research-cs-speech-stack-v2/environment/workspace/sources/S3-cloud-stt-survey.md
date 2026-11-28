# S3 — Off-device speech-to-text survey (vendor documentation, decision date)

| Service ID | Mandarin + English | Language switching, per vendor documentation | BAA for a solo practitioner |
|---|---|---|---|
| `azure-speech` | yes | Continuous language identification "doesn't support changing languages within the same sentence". | verified, self-service |
| `aws-transcribe` | yes | Language identification is per stream / per segment; no within-sentence switching documented. | verified, self-service |
| `google-stt` | yes | Alternative languages are chosen per request or per segment; no within-sentence switching documented. | verified, self-service |
| `deepgram` | English yes; Chinese only in single-language mode | Markets code-switching more heavily than any other vendor ("multilingual" mode). The multilingual mode's language list does **not** include Chinese. | not assessed |
| `speechmatics` | yes | Bilingual Mandarin–English mode documented, including switches within a sentence. | unverified — terms for a solo practitioner not confirmed |
| `assemblyai` | yes | Code-switching between supported languages, including Mandarin and English, documented. | unverified — terms for a solo practitioner not confirmed |

None of these services has been run on the project's fixtures: sending
fixture-like session audio to a vendor requires a BAA-covered account first,
so no measured error rate exists for any off-device service.

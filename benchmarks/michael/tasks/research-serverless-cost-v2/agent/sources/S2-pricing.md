# S2 — Price sheet (region-independent excerpt, USD)

| Meter | Monthly free grant | Price beyond the grant |
|---|---|---|
| Function executions | 1,000,000 executions | 0.20 per million |
| Function compute | 400,000 GB-s | 0.000016 per GB-s |
| Log ingestion | 5 GB | 2.30 per GB |
| Blob storage — write-class operations | none | 0.055 per 10,000 |
| Blob storage — list-class operations | none | 0.055 per 10,000 |
| Blob storage — read-class operations | none | 0.0044 per 10,000 |

Operation classes: PutBlob, CreateContainer and LeaseBlob are write-class;
ListBlobs is list-class; GetBlob and GetBlobProperties are read-class.
Capacity (GB stored) is negligible for this service and may be ignored.
This sheet does not cover table storage or email delivery services.

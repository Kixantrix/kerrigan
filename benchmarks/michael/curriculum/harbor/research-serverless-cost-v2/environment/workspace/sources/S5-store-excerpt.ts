// S5 — State store excerpt (application code at the time of measurement).
// One BlobStateStore is constructed for every watched race on every timer tick.
export class BlobStateStore {
  constructor(private readonly service: BlobService, private readonly race: string) {}

  async load(): Promise<RaceState | null> {
    const container = this.service.container("watcher-state");
    await container.createIfNotExists();               // CreateContainer
    const blob = container.blob(`${this.race}.json`);
    if (!(await blob.exists())) return null;             // GetBlobProperties
    return JSON.parse(await blob.downloadText());        // GetBlob
  }

  async save(state: RaceState): Promise<void> {
    const container = this.service.container("watcher-state");
    await container.blob(`${this.race}.json`).upload(JSON.stringify(state)); // PutBlob
  }
}
// Planned fix: cache one container client per process (no per-tick
// createIfNotExists) and drop the pre-read exists() check, catching
// not-found on download instead. Host-level traffic is unaffected.

// In-memory blob store with the subset of the storage SDK the API uses (read-only support).
export class MemoryBlobStore {
  constructor(baseUrl = "https://media.example.test") {
    this.baseUrl = baseUrl;
    this.blobs = new Map();
  }
  /** Blobs whose name starts with prefix, sorted by name: [{ name, metadata }]. */
  async list(prefix) {
    return [...this.blobs.keys()].filter((name) => name.startsWith(prefix)).sort()
      .map((name) => ({ name, metadata: { ...this.blobs.get(name).metadata } }));
  }
  async exists(name) { return this.blobs.has(name); }
  async get(name) {
    if (!this.blobs.has(name)) throw new Error(`BlobNotFound: ${name}`);
    return this.blobs.get(name).bytes;
  }
  async put(name, bytes, metadata = {}) { this.blobs.set(name, { bytes, metadata: { ...metadata } }); }
  async setMetadata(name, metadata) {
    if (!this.blobs.has(name)) throw new Error(`BlobNotFound: ${name}`);
    this.blobs.get(name).metadata = { ...metadata };
  }
  url(name) { return `${this.baseUrl}/${name}`; }
}

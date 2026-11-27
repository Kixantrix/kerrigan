/**
 * Deploy API helpers (T25). The full module wires the deploy/update/remove
 * routes; this slice keeps only the typed error the control-plane services
 * throw for a missing host, adapter capability, or discovered project (the HTTP
 * layer maps it to 404).
 */
export class NotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NotFoundError";
  }
}

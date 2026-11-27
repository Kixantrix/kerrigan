/**
 * Benchmark stand-in for the `pizzip` package, built on Node built-ins only.
 *
 * The application uses `pizzip`; this export has no npm dependencies, so this
 * module provides the small subset of its API the report modules use:
 * `new PizZip(bytes)`, `zip.files[name].asText()`, `zip.file(name, text)` and
 * `zip.generate({ type: "uint8array" })`. Entries are read with STORE or
 * DEFLATE and written with STORE. It is support code, not part of the task.
 */

import { crc32, inflateRawSync } from "node:zlib";

interface ZipEntry {
  name: string;
  asText(): string;
}

function entry(name: string, data: Uint8Array): ZipEntry {
  return { name, asText: () => new TextDecoder().decode(data) };
}

export default class PizZip {
  files: Record<string, ZipEntry> = {};
  private data: Record<string, Uint8Array> = {};

  constructor(bytes?: Uint8Array) {
    if (bytes !== undefined) this.load(bytes);
  }

  private load(bytes: Uint8Array): void {
    if (!(bytes instanceof Uint8Array)) throw new Error("zip input must be bytes");
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    let end = -1;
    for (let i = bytes.length - 22; i >= Math.max(0, bytes.length - 65557); i--) {
      if (view.getUint32(i, true) === 0x06054b50) {
        end = i;
        break;
      }
    }
    if (end < 0) throw new Error("End of central directory not found");
    const count = view.getUint16(end + 10, true);
    let offset = view.getUint32(end + 16, true);
    for (let n = 0; n < count; n++) {
      if (offset + 46 > bytes.length || view.getUint32(offset, true) !== 0x02014b50) {
        throw new Error("Corrupted central directory");
      }
      const method = view.getUint16(offset + 10, true);
      const size = view.getUint32(offset + 20, true);
      const nameLength = view.getUint16(offset + 28, true);
      const extraLength = view.getUint16(offset + 30, true);
      const commentLength = view.getUint16(offset + 32, true);
      const local = view.getUint32(offset + 42, true);
      const name = new TextDecoder().decode(bytes.subarray(offset + 46, offset + 46 + nameLength));
      if (local + 30 > bytes.length || view.getUint32(local, true) !== 0x04034b50) {
        throw new Error(`Corrupted local header for ${name}`);
      }
      const start = local + 30 + view.getUint16(local + 26, true) + view.getUint16(local + 28, true);
      const raw = bytes.subarray(start, start + size);
      let data: Uint8Array;
      if (method === 0) data = raw;
      else if (method === 8) data = new Uint8Array(inflateRawSync(raw));
      else throw new Error(`Unsupported compression method ${method}`);
      this.data[name] = data;
      this.files[name] = entry(name, data);
      offset += 46 + nameLength + extraLength + commentLength;
    }
  }

  file(name: string, text: string): this {
    const data = new TextEncoder().encode(text);
    this.data[name] = data;
    this.files[name] = entry(name, data);
    return this;
  }

  generate(_options: { type: "uint8array" }): Uint8Array {
    const locals: Uint8Array[] = [];
    const centrals: Uint8Array[] = [];
    let offset = 0;
    for (const [name, data] of Object.entries(this.data)) {
      const nameBytes = new TextEncoder().encode(name);
      const crc = crc32(data);
      const local = new Uint8Array(30 + nameBytes.length);
      const lv = new DataView(local.buffer);
      lv.setUint32(0, 0x04034b50, true);
      lv.setUint16(4, 20, true);
      lv.setUint32(14, crc, true);
      lv.setUint32(18, data.length, true);
      lv.setUint32(22, data.length, true);
      lv.setUint16(26, nameBytes.length, true);
      local.set(nameBytes, 30);
      const central = new Uint8Array(46 + nameBytes.length);
      const cv = new DataView(central.buffer);
      cv.setUint32(0, 0x02014b50, true);
      cv.setUint16(4, 20, true);
      cv.setUint16(6, 20, true);
      cv.setUint32(16, crc, true);
      cv.setUint32(20, data.length, true);
      cv.setUint32(24, data.length, true);
      cv.setUint16(28, nameBytes.length, true);
      cv.setUint32(42, offset, true);
      central.set(nameBytes, 46);
      locals.push(local, data);
      centrals.push(central);
      offset += local.length + data.length;
    }
    const centralSize = centrals.reduce((sum, part) => sum + part.length, 0);
    const end = new Uint8Array(22);
    const ev = new DataView(end.buffer);
    ev.setUint32(0, 0x06054b50, true);
    ev.setUint16(8, centrals.length, true);
    ev.setUint16(10, centrals.length, true);
    ev.setUint32(12, centralSize, true);
    ev.setUint32(16, offset, true);
    const parts = [...locals, ...centrals, end];
    const out = new Uint8Array(parts.reduce((sum, part) => sum + part.length, 0));
    let at = 0;
    for (const part of parts) {
      out.set(part, at);
      at += part.length;
    }
    return out;
  }
}

// Untrusted-side staging of a host-constructed, answer-free ustar archive from stdin.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, normalize } from "node:path";
const data = readFileSync(0);
if (data.length > 400000) throw new Error("archive too large");
for (let at = 0; at + 512 <= data.length;) {
  const header = data.subarray(at, at + 512);
  if (header.every((b) => b === 0)) break;
  const field = (start, length) => header.subarray(start, start + length).toString().replace(/\0.*$/s, "");
  const name = normalize(field(345, 155) ? `${field(345, 155)}/${field(0, 100)}` : field(0, 100));
  const size = parseInt(field(124, 12).trim() || "0", 8);
  if (name.startsWith("..") || name.startsWith("/") || !["0", ""].includes(field(156, 1))) throw new Error("unsafe entry");
  const target = join("/work/app", name);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, data.subarray(at + 512, at + 512 + size));
  at += 512 + Math.ceil(size / 512) * 512;
}
await import("/work/app/harness.mjs");

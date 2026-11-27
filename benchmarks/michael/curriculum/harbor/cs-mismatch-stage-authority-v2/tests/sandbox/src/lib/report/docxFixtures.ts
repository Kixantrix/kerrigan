/**
 * Building `.docx` bytes for tests, from run-level specs.
 *
 * Test-only, and deliberately run-level: a case says what each `<w:t>` run
 * contains, which is the only way to reproduce Word splitting a placeholder
 * across runs. A helper that took whole paragraphs could not express the one
 * shape these tests exist for.
 */

import PizZip from "./zip.ts";

const CONTENT_TYPES = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>`;

const RELS = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`;

const WORDML = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"';

/** One paragraph per run, so runs stay individually addressable. */
function paragraphs(runs: readonly string[]): string {
  return runs
    .map((run) => `<w:p><w:r><w:t xml:space="preserve">${run}</w:t></w:r></w:p>`)
    .join("");
}

/** All runs in one paragraph, which is how Word stores a split placeholder. */
function oneParagraph(runs: readonly string[]): string {
  const inner = runs
    .map((run) => `<w:r><w:t xml:space="preserve">${run}</w:t></w:r>`)
    .join("");
  return `<w:p>${inner}</w:p>`;
}

export interface DocxSpec {
  /** Part name -> its `<w:t>` runs. */
  parts: Record<string, readonly string[]>;
  /** Put every run of a part in one paragraph, as Word does when it splits. */
  split?: boolean;
  /** Append a trailing `<w:sectPr>`, as a real document has. */
  sectPr?: boolean;
}

export function buildDocx(spec: DocxSpec): Uint8Array {
  const zip = new PizZip();
  zip.file("[Content_Types].xml", CONTENT_TYPES);
  zip.file("_rels/.rels", RELS);

  for (const [name, runs] of Object.entries(spec.parts)) {
    const body = spec.split ? oneParagraph(runs) : paragraphs(runs);
    const tail = spec.sectPr
      ? '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/></w:sectPr>'
      : "";
    zip.file(
      name,
      `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
        `<w:document ${WORDML}><w:body>${body}${tail}</w:body></w:document>`,
    );
  }
  return zip.generate({ type: "uint8array" }) as Uint8Array;
}

/** A template whose only content is one paragraph per placeholder. */
export function templateWithSlots(...slots: string[]): Uint8Array {
  return buildDocx({
    parts: { "word/document.xml": slots.map((s) => `{{${s}}}`) },
    sectPr: true,
  });
}

/** The raw `word/document.xml` of a rendered document. */
export function renderedPart(bytes: Uint8Array): string {
  return new PizZip(bytes).files["word/document.xml"].asText();
}

/** The visible text of a rendered document, runs concatenated. */
export function documentText(bytes: Uint8Array): string {
  const zip = new PizZip(bytes);
  const xml = zip.files["word/document.xml"].asText();
  return (
    [...xml.matchAll(/<w:t\b[^>]*>([\s\S]*?)<\/w:t>/g)]
      .map((m) => m[1].replace(/<[^>]+>/g, ""))
      .join("")
      // `&amp;` last, or `&amp;lt;` would unescape twice into `<`.
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&apos;/g, "'")
      .replace(/&amp;/g, "&")
  );
}

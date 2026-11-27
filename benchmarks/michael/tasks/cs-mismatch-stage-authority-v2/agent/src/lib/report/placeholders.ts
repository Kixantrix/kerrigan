/**
 * Reading the placeholders out of her `.docx`, the way Word actually writes it.
 *
 * The only implementation. `tools/agents/template.py` was a second one, in
 * Python, with no production consumer; D22 deleted it. Two parsers of one file
 * format, obliged to agree forever, is the hazard AGENTS.md describes as a
 * defect neither branch contains — and a shared corpus mitigates that rather
 * than removing it. One reader cannot drift.
 *
 * `tests/fixtures/templates/word-shapes.json` survives the deletion and is
 * still what pins this to Word's actual behaviour, case by case, with a
 * non-emptiness assertion on the corpus itself.
 *
 * ## The part that is silent when it is wrong
 *
 * Word stores text in runs and splits a run whenever formatting or a spell
 * check boundary changes, so `{{referral_question}}` typed into Word
 * frequently lands on disk as
 *
 *     <w:t>{{referral_</w:t><w:t>question}}</w:t>
 *
 * Matching the raw XML finds neither half and reports the placeholder as
 * absent -- which renders as "this slot is unfilled" for a slot that is present
 * and correct. That is the false-positive direction aimed straight at her: a
 * template she built correctly, refused by our reader, with nothing wrong with
 * her document and no way to understand it (D19).
 *
 * So runs are concatenated before matching, which is what docxtemplater itself
 * does when it renders.
 */

import PizZip from "./zip.ts";

/** A docxtemplater placeholder: `{{referral_question}}`. */
const PLACEHOLDER = /\{\{\s*([A-Za-z0-9_.\-]+)\s*\}\}/g;

/** One `<w:t>` text run inside a Word document. */
const WORD_TEXT_RUN = /<w:t\b[^>]*>([\s\S]*?)<\/w:t>/g;

/** Anything tag-shaped, for stripping out of a run's contents. */
const XML_TAG = /<[^>]+>/g;

export class TemplateError extends Error {}

export function placeholdersInText(text: string): Set<string> {
  const found = new Set<string>();
  for (const match of String(text).matchAll(PLACEHOLDER)) found.add(match[1]);
  return found;
}

/**
 * The parts of a `.docx` that can carry a placeholder.
 *
 * Headers and footers are included because her template puts the client name
 * and report date there, and a reader that only looked at `word/document.xml`
 * would report those slots as absent.
 */
function templateParts(zip: PizZip): string[] {
  return Object.keys(zip.files).filter(
    (name) =>
      name === "word/document.xml" ||
      /^word\/(header|footer)\d*\.xml$/.test(name),
  );
}

/** Concatenate a part's text runs, as docxtemplater does, then match. */
export function placeholdersInPart(xml: string): Set<string> {
  let joined = "";
  for (const run of xml.matchAll(WORD_TEXT_RUN)) {
    joined += run[1].replace(XML_TAG, "");
  }
  // Word escapes these; a placeholder never legitimately contains one.
  joined = joined
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
  return placeholdersInText(joined);
}

/**
 * Every placeholder in a `.docx`, including ones Word has split apart.
 *
 * Matched per part rather than over every part concatenated together. A
 * document ending in an unclosed `{{a` and a header opening with `b}}` would
 * otherwise join into a placeholder `ab` that exists in neither -- a phantom
 * slot, reported to her as unfilled, in a template with no such slot to fix.
 */
export function placeholdersInDocx(bytes: Uint8Array): Set<string> {
  let zip: PizZip;
  try {
    zip = new PizZip(bytes);
  } catch (err) {
    throw new TemplateError(
      `the template is not a readable .docx: ${(err as Error).message}`,
    );
  }

  const parts = templateParts(zip);
  if (!parts.includes("word/document.xml")) {
    throw new TemplateError(
      "the template is a zip but has no word/document.xml; it is not a Word document",
    );
  }

  const found = new Set<string>();
  for (const part of parts.sort()) {
    const xml = zip.files[part].asText();
    for (const name of placeholdersInPart(xml)) found.add(name);
  }
  return found;
}

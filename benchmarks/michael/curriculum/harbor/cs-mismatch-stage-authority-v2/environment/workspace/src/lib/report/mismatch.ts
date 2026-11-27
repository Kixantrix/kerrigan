/**
 * Does her template have a slot for every section, and vice versa? (D21)
 *
 * The only implementation. There was a Python one, `tools/agents/template.py`,
 * with no production consumer; D22 deleted it rather than carrying a second
 * Word parser obliged to agree with this one forever. `git log` has it if a
 * Python consumer ever appears.
 *
 * D21 ranks two checks. The save-time one is advisory and stored only with the
 * timestamp it was taken at; the render-time one is authoritative, every time,
 * not skippable and not cached. This module serves both — the `stage` records
 * which was asked for — and the renderer only ever asks for the live one.
 *
 * Nothing here is keyed to a section name. A playbook may call its sections
 * anything; this compares two sets of strings and has no opinion about them.
 */

import { placeholdersInDocx } from "./placeholders.ts";

/**
 * Provenance and header slots a template legitimately carries that no section
 * fills. Matched by exact key, not by guessing, and pinned against
 * `tests/fixtures/templates/word-shapes.json` by `placeholders.test.ts` so the
 * convention lives in one reviewable place rather than only in code.
 */
export const RESERVED_SLOTS: readonly string[] = [
  "clinician_name",
  "client_name",
  "report_date",
  "playbook_id",
  "dossier_id",
];

/**
 * Reduce a human section name to a placeholder-shaped key.
 *
 * `"Referral Questions"` -> `"referral_questions"`. Used only to *match* a
 * section against a slot; it never renames anything.
 */
export function slugify(name: string): string {
  return String(name ?? "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

export interface Mismatch {
  /** Sections the playbook names that the template has no slot for. */
  sectionsWithoutSlot: string[];
  /** Slots in the template that no section fills. */
  slotsWithoutSection: string[];
  /** Groups of sections sharing one key, as `[key, name, name, ...]`. */
  collidingSections: string[][];
  checkedAt: string;
  /** `render` results are authoritative; `save` results are advisory. */
  stage: "render" | "save";
  template: string;
  agrees: boolean;
  authoritative: boolean;
}

export function describeMismatch(mismatch: Mismatch): string[] {
  const lines: string[] = [];
  for (const section of mismatch.sectionsWithoutSlot) {
    lines.push(
      `the report has a section '${section}' that this template has no slot ` +
        `for, so it could not be placed in the document`,
    );
  }
  for (const slot of mismatch.slotsWithoutSection) {
    lines.push(
      `the template has a slot {{${slot}}} that no section fills, so it was ` +
        `left empty`,
    );
  }
  for (const group of mismatch.collidingSections) {
    const [key, ...names] = group;
    lines.push(
      `the sections ${names.map((n) => `'${n}'`).join(", ")} all reduce to ` +
        `the same slot {{${key}}}, so none of them was written into it`,
    );
  }
  return lines;
}

/**
 * Which sections, if any, share a slot key. Keyed by slug, in section order.
 *
 * Grouped rather than keyed by a `Map` built from a one-liner, for the reason
 * the Python side was fixed: an index that keeps one section per key silently
 * drops the other, so nothing is reported missing and one section overwrites
 * the other in her document.
 */
export function groupSectionsByKey(sections: readonly string[]): Map<string, string[]> {
  const wanted = new Map<string, string[]>();
  for (const name of sections) {
    const key = slugify(name);
    const existing = wanted.get(key);
    if (existing) existing.push(name);
    else wanted.set(key, [name]);
  }
  return wanted;
}

export class TemplateMismatchError extends Error {}

export interface CheckOptions {
  stage?: "render" | "save";
  now?: Date;
  templateName?: string;
}

/**
 * Compare the report's sections against the template's slots, live.
 *
 * Takes template *bytes* rather than a cached slot list, because the file is
 * the thing that can have changed: she edits her `.docx` in Word, on disk,
 * outside this application, and a verdict taken earlier describes the file as
 * it was at that moment.
 */
export function checkMismatch(
  sections: readonly string[],
  templateBytes: Uint8Array,
  options: CheckOptions = {},
): Mismatch {
  const stage = options.stage ?? "render";
  const named = sections.map((s) => String(s)).filter((s) => s.trim());

  if (named.length === 0) {
    // Vacuity guard, applied to the check itself: comparing nothing would
    // report agreement, and a gate that finds zero inputs must fail rather
    // than pass.
    throw new TemplateMismatchError(
      "the report names no sections, so a mismatch check would compare " +
        "nothing and report agreement",
    );
  }

  const slots = placeholdersInDocx(templateBytes);
  const wanted = groupSectionsByKey(named);

  const sectionsWithoutSlot: string[] = [];
  const collidingSections: string[][] = [];
  for (const [key, names] of wanted) {
    if (!slots.has(key)) sectionsWithoutSlot.push(...names);
    // An empty key means the name reduced to no placeholder-shaped characters
    // at all. Those are already reported individually as having no slot, which
    // is true and readable; grouping them would print a collision on `{{}}`.
    if (key && names.length > 1) collidingSections.push([key, ...names]);
  }

  const reserved = new Set(RESERVED_SLOTS);
  const slotsWithoutSection = [...slots]
    .filter((slot) => !wanted.has(slot) && !reserved.has(slot))
    .sort();

  const agrees =
    sectionsWithoutSlot.length === 0 &&
    slotsWithoutSection.length === 0 &&
    collidingSections.length === 0;

  return {
    sectionsWithoutSlot,
    slotsWithoutSection,
    collidingSections,
    checkedAt: (options.now ?? new Date()).toISOString().replace(/\.\d+Z$/, "Z"),
    stage,
    template: options.templateName ?? "",
    agrees,
    authoritative: stage === "render",
  };
}

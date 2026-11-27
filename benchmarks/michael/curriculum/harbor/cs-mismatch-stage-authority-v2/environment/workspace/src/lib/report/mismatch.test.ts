/**
 * The D21 mismatch check, at the level of the check itself.
 *
 * Benchmark export: the upstream suite runs under vitest; these cases are the
 * same kind of checks rewritten for `node:test` so they run with Node built-ins
 * only (`node --test src/lib/report/`). Section names are neutral examples.
 *
 * Nothing here is keyed to a section name. Every case would behave identically
 * if the playbook renamed everything.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildDocx, templateWithSlots } from "./docxFixtures.ts";
import {
  RESERVED_SLOTS,
  TemplateMismatchError,
  checkMismatch,
  describeMismatch,
  slugify,
} from "./mismatch.ts";

describe("a template built from the playbook", () => {
  const playbooks = [
    ["Purpose", "Background", "Methods Used", "Summary"],
    ["Opening Notes", "Approach", "Discussion", "Next Steps", "Appendix"],
  ];

  for (const sections of playbooks) {
    it(`agrees for the ${sections.length}-section playbook`, () => {
      const template = templateWithSlots(...sections.map(slugify));
      const mismatch = checkMismatch(sections, template);
      assert.equal(mismatch.agrees, true, describeMismatch(mismatch).join("; "));
    });
  }
});

describe("what disagreed, named rather than counted", () => {
  it("names a section the template has no slot for", () => {
    const mismatch = checkMismatch(["Purpose", "Summary"], templateWithSlots("purpose"));
    assert.equal(mismatch.agrees, false);
    assert.deepEqual(mismatch.sectionsWithoutSlot, ["Summary"]);
  });

  it("names a slot no section fills", () => {
    const mismatch = checkMismatch(["Purpose"], templateWithSlots("purpose", "orphan_slot"));
    assert.deepEqual(mismatch.slotsWithoutSection, ["orphan_slot"]);
  });

  it("does not report provenance slots as unfilled", () => {
    const template = templateWithSlots("summary", ...RESERVED_SLOTS.slice(0, 2));
    assert.equal(checkMismatch(["Summary"], template).agrees, true);
  });

  it("finds a placeholder split across runs", () => {
    const template = buildDocx({
      parts: { "word/document.xml": ["{{sum", "mary}}"] },
      split: true,
    });
    assert.equal(checkMismatch(["Summary"], template).agrees, true);
  });

  it("records the moment it looked", () => {
    const now = new Date("2026-08-22T12:00:00Z");
    const mismatch = checkMismatch(["Summary"], templateWithSlots("summary"), { now });
    assert.equal(mismatch.checkedAt, "2026-08-22T12:00:00Z");
  });
});

describe("comparing nothing", () => {
  it("is refused rather than reported as agreement", () => {
    assert.throws(() => checkMismatch([], templateWithSlots("anything")), TemplateMismatchError);
  });
});

describe("two sections that reduce to one slot", () => {
  it("names both rather than silently keeping the last", () => {
    const mismatch = checkMismatch(["Summary", "Summary."], templateWithSlots("summary"));
    assert.equal(mismatch.agrees, false);
    assert.deepEqual(mismatch.collidingSections, [["summary", "Summary", "Summary."]]);
  });
});

describe("the stage a result was taken at", () => {
  it("defaults to the authoritative one", () => {
    const mismatch = checkMismatch(["Summary"], templateWithSlots("summary"));
    assert.equal(mismatch.stage, "render");
    assert.equal(mismatch.authoritative, true);
  });

  it("marks a save-time look as not authoritative", () => {
    const mismatch = checkMismatch(["Summary"], templateWithSlots("summary"), {
      stage: "save",
    });
    assert.equal(mismatch.authoritative, false);
  });
});

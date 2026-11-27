// Trusted, answer-free held-out scenarios for the mismatch stage check.
// Inputs are built here (some are not expressible in JSON); every emitted
// value is an untrusted observation graded on the host.
import { readFileSync } from "node:fs";

const R = "/work/app/src/lib/report";

async function load() {
  const mismatch = await import(`${R}/mismatch.ts`);
  const fixtures = await import(`${R}/docxFixtures.ts`);
  const placeholders = await import(`${R}/placeholders.ts`);
  return { ...mismatch, ...fixtures, TemplateError: placeholders.TemplateError };
}

function outcome(m, run) {
  try {
    const result = run();
    if (!result || typeof result !== "object") return { returned: typeof result };
    return { stage: result.stage ?? null, authoritative: result.authoritative ?? null };
  } catch (error) {
    if (error instanceof m.TemplateMismatchError) return "refused";
    if (error instanceof m.TemplateError) return "error:TemplateError";
    return `error:${error?.constructor?.name ?? typeof error}`;
  }
}

const STAGES = {
  misspelt: { rendre: "rendre", saved: "saved", advisory: "advisory", live: "live", empty: "" },
  variants: { Render: "Render", SAVE: "SAVE", leading: " render", trailing: "save ", inner: "ren der" },
  prototype: {
    constructor: "constructor", proto: "__proto__", toString: "toString",
    hasOwnProperty: "hasOwnProperty", valueOf: "valueOf",
  },
  primitives: { zero: 0, one: 1, true: true, false: false, nan: NaN },
  objects: {
    boxed: () => new String("render"),
    array: () => ["render"],
    arraySave: () => ["save"],
    empty: () => ({}),
    toStringy: () => ({ toString: () => "render" }),
  },
};

export async function stageValues(args) {
  const m = await load();
  const template = m.templateWithSlots("summary");
  const out = {};
  for (const [label, raw] of Object.entries(STAGES[args.set])) {
    const stage = typeof raw === "function" ? raw() : raw;
    out[label] = outcome(m, () => m.checkMismatch(["Summary"], template, { stage }));
  }
  return out;
}

const PAYLOADS = {
  capital: '{"stage":"Render","templateName":"letter.docx"}',
  number: '{"stage":1,"templateName":"letter.docx"}',
  list: '{"stage":["save"]}',
  nested: '{"stage":{"value":"render"}}',
  boolean: '{"stage":false}',
  protoKey: '{"stage":"__proto__","templateName":"letter.docx"}',
  validSave: '{"stage":"save","templateName":"letter.docx","extra":1,"constructor":"x"}',
  validRender: '{"stage":"render","requestId":"r-1"}',
  nullStage: '{"stage":null,"templateName":"letter.docx"}',
  noStage: '{"templateName":"letter.docx"}',
};

export async function ipcPayloads() {
  const m = await load();
  const template = m.templateWithSlots("summary", "next_steps");
  const out = {};
  for (const [label, text] of Object.entries(PAYLOADS)) {
    out[label] = outcome(m, () => m.checkMismatch(["Summary", "Next Steps"], template, JSON.parse(text)));
  }
  return out;
}

export async function refuseFirst() {
  const m = await load();
  const garbage = new Uint8Array([80, 75, 1, 2, 9, 9, 9]);
  const good = m.templateWithSlots("summary");
  return {
    emptySections: outcome(m, () => m.checkMismatch([], good, { stage: "rendre" })),
    blankSections: outcome(m, () => m.checkMismatch(["  ", ""], good, { stage: "Save" })),
    unreadableTemplate: outcome(m, () => m.checkMismatch(["Summary"], garbage, { stage: "rendre" })),
    unreadableNumber: outcome(m, () => m.checkMismatch(["Summary"], garbage, { stage: 2 })),
  };
}

export async function validStages() {
  const m = await load();
  const template = m.templateWithSlots("summary");
  const sections = ["Summary"];
  return {
    render: outcome(m, () => m.checkMismatch(sections, template, { stage: "render" })),
    save: outcome(m, () => m.checkMismatch(sections, template, { stage: "save" })),
    undefinedStage: outcome(m, () => m.checkMismatch(sections, template, { stage: undefined })),
    nullStage: outcome(m, () => m.checkMismatch(sections, template, { stage: null })),
    noOptions: outcome(m, () => m.checkMismatch(sections, template)),
    emptyOptions: outcome(m, () => m.checkMismatch(sections, template, {})),
    extraOptions: outcome(m, () => m.checkMismatch(sections, template, { stage: "save", trace: true, retries: 2 })),
  };
}

export async function otherOptions() {
  const m = await load();
  const template = m.templateWithSlots("summary");
  const now = new Date("2027-03-04T05:06:07.890Z");
  const save = m.checkMismatch(["Summary"], template, { stage: "save", now, templateName: "memo.docx" });
  const render = m.checkMismatch(["Summary"], template, { now, templateName: "memo.docx" });
  const bare = m.checkMismatch(["Summary"], template, { stage: "render" });
  return {
    save: { checkedAt: save.checkedAt, template: save.template, stage: save.stage, authoritative: save.authoritative },
    render: { checkedAt: render.checkedAt, template: render.template, stage: render.stage, authoritative: render.authoritative },
    bareTemplate: bare.template,
    bareCheckedAtIsIso: /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(bare.checkedAt),
  };
}

function answer(result) {
  return {
    agrees: result.agrees,
    sectionsWithoutSlot: result.sectionsWithoutSlot,
    slotsWithoutSection: result.slotsWithoutSection,
    collidingSections: result.collidingSections,
  };
}

export async function sameAnswer() {
  const m = await load();
  const cases = {
    agreeing: [["Opening", "Field Notes", "Wrap Up"], m.templateWithSlots("opening", "field_notes", "wrap_up", "report_date")],
    missingAndOrphan: [["Opening", "Field Notes"], m.templateWithSlots("opening", "zeta_slot", "alpha_slot")],
    colliding: [["Wrap Up", "Wrap-Up", "Opening"], m.templateWithSlots("opening")],
    splitAndHeader: [["Opening", "Wrap Up"], m.buildDocx({
      parts: { "word/document.xml": ["{{open", "ing}}"], "word/header1.xml": ["{{wrap_up}}", "{{extra_note}}"] },
      split: true,
    })],
  };
  const out = {};
  for (const [label, [sections, template]] of Object.entries(cases)) {
    const save = m.checkMismatch(sections, template, { stage: "save" });
    const render = m.checkMismatch(sections, template, { stage: "render" });
    out[label] = {
      save: answer(save),
      render: answer(render),
      authority: [save.authoritative, render.authoritative],
      stages: [save.stage, render.stage],
    };
  }
  return out;
}

export async function existingErrors() {
  const m = await load();
  const good = m.templateWithSlots("summary");
  return {
    emptySections: outcome(m, () => m.checkMismatch([], good, { stage: "save" })),
    blankSections: outcome(m, () => m.checkMismatch(["   "], good)),
    unreadableTemplate: outcome(m, () => m.checkMismatch(["Summary"], new Uint8Array([1, 2, 3]), { stage: "render" })),
    exports: ["RESERVED_SLOTS", "TemplateMismatchError", "checkMismatch", "describeMismatch",
      "groupSectionsByKey", "slugify"].filter((name) => name in m),
  };
}

const VOCAB = [
  "unknown-stage-demotes-authority", "stage-changes-answer", "vacuous-agreement",
  "colliding-sections-dropped", "split-run-placeholder-missed", "header-footer-slots-ignored",
  "reserved-slot-reported", "cached-template-verdict",
];

export async function findings() {
  let ledger;
  try {
    ledger = JSON.parse(readFileSync("/work/app/REVIEW.json", "utf8"));
  } catch {
    return { parsed: false, categories: [], wellFormed: false, count: 0 };
  }
  const list = ledger && Array.isArray(ledger.findings) ? ledger.findings : null;
  if (!list) return { parsed: true, categories: [], wellFormed: false, count: 0 };
  const wellFormed = list.every((item) => item && typeof item === "object"
    && VOCAB.includes(item.category)
    && typeof item.location === "string" && item.location.trim() !== ""
    && typeof item.defect === "string" && item.defect.trim() !== "");
  const categories = [...new Set(list.map((item) => String(item?.category)))].sort();
  return { parsed: true, categories, wellFormed, count: list.length };
}

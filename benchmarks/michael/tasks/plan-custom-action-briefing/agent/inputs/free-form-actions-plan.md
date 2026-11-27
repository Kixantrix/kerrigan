# Plan — free-form actions

> Companion to [`free-form-actions.md`](./free-form-actions.md). That document
> says what this is and why; this one says what would be changed, in what order,
> and how it would be checked. **Nothing here is built.** Post-preview, no
> deadline.
>
> Written 2026-08-21 against `main`. Files are named rather than cited by line
> number: a coordinate is an index into one tree and rots the moment anything
> above it shifts, which is a rule this repo already enforces on its journals
> (`tools/validators/check_unpinned_claims.py`). Quotes are given instead, so a
> later reader can grep for them.
>
> **Revised three times the same day**, all on the boundary section, and in
> different directions each time. Too broad and on the wrong axis (an *audience*
> rule rather than a *harm* rule, which forbade ordinary organising and with it
> the motivating example). Then too quiet (*"the app is not the tool for doing
> it"*, read as though it should say nothing about content, when advice is most
> of the value). Then too absolute — *"no artefact production"* forbids the
> **action item**, which is the feature, and so did the agent's own replacement
> rule about unsupplied substance. Four wrong versions, three caught by the
> owner.
>
> The rule that survives is the owner's: **the app writes the plan, not the
> deliverable**, with a second rule constraining whatever it does write.
>
> Re-derived rather than patched each time: §2.3 describes **two** gates and
> names the false positive as the one to guard; §2.4 sequences the advice line
> as prompt → measurement → only-then-guard; the test table gains FF18–FF23.
> That one section moved four times is itself worth knowing — **the boundary is
> the hard part of this feature, and the data model is not.**

## Sequencing

Two phases, and the gate between them is a decision rather than a task.

| Phase | What | Gate |
|---|---|---|
| **1** | Surface A — the person writes their own commitment. Carries the whole data-model change. | None. Independently useful; no authenticity ambiguity; no model. |
| **2** | Surface B — the conversation proposes actions. | **Owner decision D1.** A no here costs nothing already built. |

Phase 1 first is not just risk ordering. It means the data-model change is
exercised end-to-end by a feature with zero generated content, so if something
about nullable opportunities is wrong, it is found while the only content in
play is text the owner typed themselves.

Inside each phase, work is ordered so that **nothing renders before it can be
rendered honestly**. The authenticity statement (§4 of the spec) ships in the
same slice as the thing it labels, not in a follow-up. This repo has a
documented pattern of the opposite — several modules finished, tested and
unreachable for a milestone, and the promises they implied left visible in
copy — and the ladder's own comment names how it ends: *"the ordinary way an
unwired feature becomes a lie: something finally shows it to somebody."*

---

## Phase 1 — Surface A

### 1.1 The domain type

`apps/api/src/actions/state.ts`. Introduce the discriminated `origin` from spec
§3 and rename the heading field to `title`.

`transition()`, `hasExpired()`, `displayStatus()`, `STATUS_WORDING`,
`allowedFrom()` and the whole `TRANSITIONS` table are **untouched**. This is
worth stating because it is the argument for the design: a free-form commitment
is the same promise with a different provenance, and if any of these needed a
branch, the model would be wrong.

Add `provenance: Provenance` — a commitment has none today and inherits its
standing from the opportunity it points at. Cut that link and there is nowhere
for it to live.

### 1.2 The migration

`apps/api/drizzle/`, new numbered file. **Additive only:**

- `opportunity_id` and `action_id` → nullable
- `opportunity_title_encrypted` → keep the column; it now holds `title`
- new `origin` text column, defaulting to `'opportunity'` for every existing row
- new `provenance` jsonb (or text) column, nullable

Nothing is dropped and nothing is renamed **in the database**. That is the
constraint that matters: `commitment.id` is the encryption AAD
(`actions/store.ts` `toRow`), so every existing ciphertext still opens. A rename
at the domain layer costs a mapping in `fromRow`/`toRow`; a rename at the column
layer would cost a re-encryption pass, and there is no reason to buy one.

**Backfill rule:** every existing row is `origin = 'opportunity'`. There are no
free-form commitments before this migration, so there is no ambiguous row and no
guess.

### 1.3 The eight readers

Every place that reads `opportunityTitle` or `opportunityId` today. The compiler
finds all of them once the type changes; they are listed so the plan can be
checked against reality rather than trusted.

| File | What changes |
|---|---|
| `apps/api/src/actions/store.ts` | `toRow` / `fromRow` map `title` ↔ the existing column; read `origin` |
| `apps/api/src/actions/routes.ts` | `coerceNew` stops requiring `opportunityId`/`actionId` and requires them **only** when `origin.kind === 'opportunity'` |
| `apps/api/src/reminders/calendar.ts` | `SUMMARY` ← `title` (unchanged behaviour for sourced); `DESCRIPTION` gains the own-plan line for free-form |
| `apps/api/src/export/service.ts` | `ExportedCommitment` gains `title` and `origin`; keeps emitting `opportunityTitle` for one release |
| `apps/api/src/export/render.ts` | Markdown and CSV renderers use `title`; CSV gains an `origin` column |
| `apps/api/src/import/service.ts` | Accepts `title` **or** legacy `opportunityTitle`; missing `origin` reads as `'opportunity'` |
| `apps/mobile/app/(tabs)/act.tsx` | Heading ← `title`; the free-form card carries the unsourced statement |
| `apps/api/src/opportunities/routes.ts` | Wherever it composes a commitment from a ladder rung |

`apps/api/src/actions/{ladder,message,reflection}.ts` are listed by grep but
operate on opportunities rather than on commitments, except `reflection.ts`,
which reads `commitment.actionTitle` for its `because` sentence — unchanged.

### 1.4 The API surface

`POST /commitments` accepts an `origin`. `coerceNew`'s existing
`OPENING_STATUSES` guard (`saved | committed`) applies unchanged — a free-form
commitment cannot be created already completed for the same reason a sourced one
cannot: it would let a client write a follow-through history that never
happened.

No new route for creation. Adding `POST /commitments/free-form` would be a
second door into one thing, and the transition route's own comment explains why
this repo prefers one: a second entry point is a second place for the rules to
be enforced differently.

### 1.5 The screen

Act gains a control and a short form (spec §7). The card gains the unsourced
statement. Both in the same change.

---

## Phase 2 — Surface B

Only on a yes to owner decision D1.

### 2.1 Extraction, not tool-calling

A new module beside `apps/api/src/profile/proposals.ts`, following it closely
enough that a reader of one can read the other. A `structuredExtraction` call
with a schema and a validator, over the transcript, on demand — **not** inside
`ConversationService.respond`.

`conversation/prompt.ts` is **not edited**. That is a deliverable, not an
omission: the rule *"you cannot update, save, build or change… anything in this
app — you can only talk"* stays literally true, which is the whole reason this
is an extraction pass rather than a tool.

### 2.2 The checks

Spec §5's table, built on functions that already exist: `collectOwnWords` and
`verifyQuotes` from `actions/message.ts`, and the representative data from
`represent`. A proposal failing its quote check is dropped **before** display,
not shown with a warning — the difference from `draftMessage` being that a
warned draft is still something the person asked for, whereas an ungrounded
proposal is something the app volunteered.

### 2.3 The gates, and there are two of them

**The harm gate** ([spec §6a](./free-form-actions.md#6a-the-harm-boundary-at-a-person-not-with-other-people)):
an action is withheld only when it has an identifiable private individual as its
object **and** an adverse intended effect on them. Both conditions. An
officeholder in their public role is not a private individual.

The thing to guard hardest is the **false positive**, not the false negative.
An over-eager gate that swallows *"knock on twenty doors and ask people what
they think"* looks exactly like a working feature — it produces fewer, safer
proposals and nobody sees what it ate. That is the failure the corrected §6
exists to prevent, and FF18's second mutation is the only thing that would
catch it.

**The doctrine gate** (`outcome-doctrine.md` §4a and Test B, via the four
verdicts in `conduct-not-identity-examples.md`), which handles the *group* case
— including the encampment example. A `redirect` is an offer of a conversation,
per that page's decision of 2026-08-16, and never a block; and a redirect that
names no route is a refusal wearing a nicer word (FF19). What is not proposed is
visible as a decision.

**These are the parts most likely to be wrong**, and the page they come from
says so: *"Whether any of this is automated"* is explicitly undecided, and twelve
worked rows is *"not a corpus"*. The plan does not pretend otherwise. If owner
decision D1 is yes, both should be built last and reviewed hardest.

### 2.4 Advice, and the measurement before the guard

The advice half of [§6b](./free-form-actions.md#6b-the-scope-boundary-the-plan-not-the-deliverable)
is not a separate feature — the interviewer already talks, and talking through
how to run a survey is talking. What is new is a line it must not cross, and the
sequencing matters:

1. **Prompt first**, stating the line: advise on how, do not emit the thing.
2. **Measure it** (FF22): n=20 turns in the shape the service actually sends,
   counting replies containing a block meant to be used verbatim by somebody
   else. Report the rate.
3. **Only then decide whether a guard is worth it**, and that decision is the
   owner's, because the guard's shape — trimming somebody's reply — is a product
   choice. Open question 7.

**Do not skip to step 3.** `conversation/prompt.ts` contains the worked example
of why: a rule was extended to name its tell, re-measured at n=20, and came back
*unchanged at 7/20*. The value of that entry is the measurement, not the fix,
and it exists because somebody ran it rather than reasoned about it. A guard
designed against a guessed rate is a guard nobody can evaluate.

### 2.5 The review surface

Reuse `ProposalsList`'s shape: accept, decline, accept-after-rewording, and the
authorship flip. A cap on how many proposals exist at once — open question 5 in
the spec — must be decided before this ships, because the compass already
learned what happens without one.

---

## Tests, and the mutation each must fail on

**Every test below is stated with the change that must turn it red.** This is
not ceremony. The warning that produced this section is that several tests in
this repo passed while asserting a defect, and several mocks returned values
production could never produce. A test whose red condition nobody has written
down is a test nobody has checked — and the check is *running the mutation*, not
reasoning about it.

Two standing rules for anyone implementing these:

- **Mutate, run, observe red, revert.** The `font-coverage` entry in
  [`plan.md`](./plan.md) is the worked example of doing this properly, down to
  recording the baseline count and the exact failing assertion.
- **No mock may return a value production cannot produce.** In particular, a
  fixture commitment must go through the same construction path as a real one;
  a hand-built object literal with both an `origin` and an `opportunityId` would
  be asserting against a state the type forbids.

### Phase 1

| AC | Test | Must go red when |
|---|---|---|
| FF1 | `commitments-routes.test.ts` | `POST /commitments` with `origin.kind === 'own'` is accepted while `opportunityId` is still required — i.e. revert `coerceNew`'s conditional and the test must fail, not pass with a placeholder id |
| FF2 | `act-screen.test.tsx` | The heading falls back to `?? ''` or to a placeholder string for a free-form commitment. Assert on the **rendered heading text equalling the owner's words**, not on the absence of an error |
| FF3 | new `free-form-has-no-source.test.ts` | Any code path returns a non-null `handoffUrl`, `sourceUrl`, `organizer` or `documentUrl` for an `origin.kind === 'own'` commitment. Written as an exhaustive assertion over the presented object, so a **newly added** URL field fails it too |
| FF4 | `opportunity-route-boundary.test.ts` | A free-form commitment is included in the feed response |
| FF5 | `reminders-calendar.test.ts` | The own-plan line is removed from `DESCRIPTION`. Second case: `?discreet=1` leaks the title — assert the discreet body **does not contain** the commitment's own words |
| FF6 | `reminder-sweep.test.ts` | A dateless free-form commitment produces a due reminder instead of a `no-date` skip. Companion UI assertion: the screen states no reminder will arrive |
| FF7 | new `commitment-origin-parity.test.ts` | Any branch on `origin` is added inside `transition()`. Written as: the full transition table produces identical results for a sourced and a free-form commitment. **A new file, deliberately** — there is no dedicated state-machine test today; the table is exercised indirectly through `action-ladder.test.ts` and `commitments-routes.test.ts`, and indirect coverage of a table is exactly what lets a branch slip into it |
| FF8 | `import-round-trip.test.ts` | Two mutations, both required. (a) The legacy alias is removed from the import reader — an archive containing `opportunityTitle` and no `title` must then fail to import. (b) A mixed archive of sourced and free-form commitments must not round-trip equal if `origin` is dropped on either side |
| FF9 | `deletion-scopes.test.ts` | `deleteAllFor` misses free-form rows, or reports a count from a list read beforehand rather than from what storage removed |

The FF3 test is the one worth building carefully, because it is the mechanical
half of owner decision D2. If the recommendation there (Option 3 — no new
authenticity category, plus a mandatory unsourced statement) is taken, then FF3
plus a rendering assertion that the statement is present is what stops the
convention decaying. **State honestly what that does not cover:** a new surface
added later that renders a free-form commitment without either check would pass
both. A category in an exhaustive union would catch that; a convention will not.
That gap is the reason decision D2 is the owner's.

### Phase 2

| AC | Test | Must go red when |
|---|---|---|
| FF10 | `conversation-*.test.ts` | Any path from a chat turn creates a commitment. Assert on the store: after N turns, the commitment count is unchanged |
| FF11 | new proposal test | Proposals are produced for a user with no approved compass |
| FF12 | new proposal test | A proposal whose `groundedIn` quotes are absent from the person's material is returned rather than dropped. Use a **fabricated quote** in the fixture, as `action-message.test.ts` does |
| FF13 | new proposal test | An institution the person has no representative for survives into the presented proposal |
| FF14 | new proposal test | Copy asserting an outcome passes. Assert on the **presented card fields**, not on the prompt |
| FF15 | proposal accept test | An unedited accept sets authorship to the person's, or an edited accept leaves it as the app's. Both directions, because `profile/proposals.ts` shows this is the pair that gets confused |
| FF16 | new doctrine test | A declined-to-serve proposal disappears with no trace the person can find |
| FF17 | proposal decline test | A declined proposal is re-proposed on the next extraction |
| FF18 | new `harm-boundary.test.ts` | **Two mutations, and both are required.** (a) A fixture action targeting an identifiable private individual with adverse intent is proposed. (b) A fixture action that convenes, surveys or organises other people **without** targeting one is *withheld* — the false-positive direction, which is the one that matters, because a gate that quietly swallows ordinary organising is the exact failure §6 was corrected for and it would look like a passing test |
| FF19 | new doctrine test | A redirect is emitted with no named route. Assert on the **presented redirect having a non-empty route**, not on the verdict string |
| FF20 | new `advice-not-artefact.test.ts` | The reply to *"how do I go about this?"* is empty, or is a refusal with no advice in it. **Asserted as a presence** — the failure guarded here is the app going quiet, and a test checking only that no artefact was emitted passes on an empty string |
| FF21 | same file | A request to *write the survey* produces a verbatim-usable block; **or** the refusal is a dead end. Both halves, because `conversation/prompt.ts` records that a model told it cannot do something *"goes looking for the nearest helpful substitute"* — the refusal path is where the leak actually happens, not the direct request |
| FF22 | `evals/` harness, not a unit test | **Nothing.** This one reports a rate rather than passing or failing, per open question 7. It goes red only if the harness stops measuring — assert the run produces a number over n=20, not that the number is good |
| FF23 | new `scope-rule.test.ts` | **Three assertions, and the first two are the ones that matter.** The rule permits the action item; the rule permits the advice; the rule excludes the questionnaire, form, contact list and responses. Every one of the four wrong versions of this boundary would have passed a test that checked only the third |

**FF22 is deliberately not a pass/fail criterion**, and that is the point rather
than a weakness. Open question 7 argues the advice/artefact line will not hold
perfectly by prompt, on this repo's own measured evidence. A criterion asserting
that it does would be **asserting a defect** — the failure named in the warning
that produced this whole section — and would go green while the thing it claims
to guard was broken a third of the time. What is asserted instead is that the
measurement exists, because the blind spot in `acceptance-tests.md` is exactly
this: *"a blind spot is worse than a failing case, because a failing case is at
least counted."*

**Fixture rule for Phase 2.** The AI provider stub must return a payload that
the real `structuredExtraction` validator accepts, and the validator must run in
the test. A stub that returns an already-validated object tests nothing about
the path production takes — which is the second half of the warning that
produced this section.

---

## What this does not include

- **No implementation.** This change adds two documents and a pointer.
- **No new authenticity category** unless owner decision D2 says so. The
  recommendation (spec §4, Option 3) needs no resolver change at all.
- **No change to `conversation/prompt.ts`.** Phase 2 is specified precisely so
  that none is needed.
- **No entry in [`acceptance-tests.md`](./acceptance-tests.md).** That file
  records what was observed on the deployment; unbuilt work does not belong in
  it. The criteria live in the spec until something exercises them.
- **No survey host, no mailing list, no contact store, and no generated
  questionnaire, flyer or form** — per spec
  [§6b](./free-form-actions.md#6b-the-scope-boundary-the-plan-not-the-deliverable).
  **The action item itself is produced by the app, and advice on how to run the
  thing is in scope** — the app writes the plan, not the deliverable. Three
  earlier drafts of this plan got that wrong in three different directions, two
  of them by forbidding the feature.

## Rollback

Phase 1's migration is additive, so rolling the code back leaves rows with an
`origin` column nothing reads and nullable columns nothing writes null to — a
harmless state. The one-way door is the **export archive**: once an archive
containing free-form commitments exists in somebody's possession, an older
importer cannot read it. That is why §1.3 keeps emitting `opportunityTitle`
alongside `title` for a release, and why the import reader accepts both. Drop
the alias only when there is a reason, and write down what the reason was.

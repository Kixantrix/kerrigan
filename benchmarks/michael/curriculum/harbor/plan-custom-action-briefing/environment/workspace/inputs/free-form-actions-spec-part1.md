# Free-form actions: letting somebody commit to something nobody scheduled

> **Status: shaped, not built. All four owner decisions answered 2026-08-21.**
> This document is a specification and it proposes decisions; four were the
> owner's and **all four now have answers**, recorded in place with the argument
> that preceded them left intact. **D1 is yes**, so nothing in here is
> conditional any more. Nothing has been implemented and no code in this change
> does anything. The companion is
> [`free-form-actions-plan.md`](./free-form-actions-plan.md).
>
> **Surface A is no longer post-preview** — the owner has said it can ship before
> the private preview. Surface B remains later. The A-then-B staging was written
> as a hedge against a no on D1 and survives the yes as a schedule, which is why
> it is unchanged below.
>
> One thing is still the owner's and is easy to miss because D2 reads as
> answered: the **name** is settled (*custom action*) but the **authenticity
> mechanic** carrying that name is not. See the D2 row.
>
> Written 2026-08-21 against `main`. Every claim about the **code** cites the
> file it came from. Every claim about **doctrine** quotes the document and
> names it, and where this document proposes a rule of its own it says so in the
> same sentence.
>
> That last part is not boilerplate.
> [§6b](#6b-the-scope-boundary-the-plan-not-the-deliverable) has been wrong
> **four times** — once for stating an invented rule in the repo's voice, once
> for reading as though the app should stay quiet, and twice for forbidding the
> action item, which is the feature. All four are recorded there, along with the
> three-way test that now has to be run before any scope sentence is written
> down. A spec whose inventions are indistinguishable from its citations is
> worse than no spec; a spec whose rules have never been run against a case is
> not much better.

> _Excerpt note: "Why this exists" (lines 35-75 of the original) is omitted here._

## The decisions this needs from the owner

Listed by weight, not by where they appear. Each is argued in full in the
section named. Answered ones are struck through and dated in place rather than
removed, following the convention in
[`outcome-doctrine.md`](./outcome-doctrine.md) — a list that quietly loses an
item reads as though the item was never there.

| | Decision | Where | Why it is not the agent's |
|---|---|---|---|
| ~~**D1**~~ | ~~Does the app generate proposed actions at all?~~ **Answered 2026-08-21: yes.** | [§7](#7-where-it-comes-from-in-the-ui) | The owner overruled the doctrine objection knowingly and in his own words — *"D1 yes — thought we already discussed that."* The argument in §7 and the encampment evidence below it stand as the record of what was weighed; they are no longer a question. Everything specified as conditional on D1 is now unconditional. |
| ~~**D2**~~ | ~~How a free-form action is **labelled**~~ **Answered 2026-08-21: it is called a _custom action_, and the Plan screen points at it.** | [§4](#4-authenticity-how-a-free-form-action-announces-what-it-is) | The owner named the thing — *"maybe call it custom action or something like that"* — and added a placement that was not in this document: *"add an item to the plan view saying something like 'if you can't find something useful to do here, brainstorm custom actions in chat'."* That turns an empty Plan screen from a dead end into the entry point, which is a better answer than either option offered. **Still the owner's and not yet answered:** whether *custom action* is an eighth authenticity category or the existing `inferred` plus a mandatory unsourced statement. A distinct user-facing name argues for the eighth category, but that is an inference from a naming choice and `source/authenticity-addendum.md` promises seven. Do not read it as settled. |
| ~~**D3**~~ | ~~The **claim ceiling**~~ **Answered 2026-08-21: confirmed, and scoped to what the app asserts rather than to what may be discussed.** | [§5](#5-is-it-worth-somebodys-afternoon-and-can-that-be-checked) | *"Sure we can't say effectiveness for certain but the Agent should be able to brainstorm with the user in that regard."* The ceiling binds the app's own copy — a card, a label, a summary — which is where a quiet raise would happen and what §5 was written to protect. It does not bind the conversation: the interviewer may think aloud with somebody about whether a thing is likely to work, because that is a discussion between two parties and not a claim the product has made. The two must not be collapsed. A sentence the agent reasons its way to in conversation does not thereby become something the app may print on a card. |
| ~~**D4**~~ | ~~Where does drafting fall?~~ **Answered 2026-08-21: the app writes the plan and advises on the deliverable; it does not produce the deliverable.** | [§6b](#6b-the-scope-boundary-the-plan-not-the-deliverable) | Answered by the owner, after the section had been wrong four times. What remains open is the agent's proposed *reason* — two composing rules meant to generalise — which stands or falls separately. |

> **The concrete evidence for D1, and it comes from the owner's own example.**
> *"Collect your neighbours' complaints about this homeless encampment"* covers
> both *document conditions so services reach this block* and *build a case to
> move these people on* — and **nothing in the sentence distinguishes them.**
>
> That is not a hypothetical edge found by theorising. It is the sentence that
> prompted the feature, and it lands exactly where
> [`conduct-not-identity-examples.md`](./conduct-not-identity-examples.md) says
> the line is hardest — the page that also records that its twelve worked rows
> are *"not a corpus"*, that *"whether any of this is automated"* is
> **undecided**, and that *"a classifier confident enough to act on row 10 is
> confident enough to be wrong about it silently."*
>
> A model generating actions has to tell those two readings apart, in a live
> call, on the first try. Argued in full in
> [§5](#the-doctrine-gate-and-why-the-owners-own-example-is-the-hard-case).

---

## 1. What a free-form action is, and what it is not

A **free-form action** is a commitment with no opportunity behind it. Nobody
scheduled it, no organiser is running it, there is no official calendar entry
and no page to check. It exists because a person decided to do it.

| It is | It is not |
|---|---|
| A promise the person made to themselves, recorded | A civic event |
| **The plan** — a push, plus advice on how to go about it | **The deliverable** — the thing you make while doing it |
| Something the app remembers, reminds about, and asks how it went | Something the app runs, hosts, or does on their behalf |
| Grounded in something they actually said they care about | A model's idea about what would be good for them |

The distinction that matters most: a sourced opportunity is the app reporting
that **the world contains this**. A free-form action is the app recording that
**you said you would**. Those are different claims and the product must never
let the second borrow the first's authority. Section 4 is entirely about how.

### Two surfaces, and they are not the same feature

The request says "chat". Reading the code, there are two distinct features
hiding in that word, and only one of them is hard.

**Surface A — you write it.** A control on Act: *"Something you decided to do."*
The person types what they are going to do, roughly when, and how long they
think it will take. No model is involved at any point. Provenance is `user`,
authenticity is `user-provided`, and there is nothing to verify because nothing
was generated.

**Surface B — the conversation proposes it.** A separate pass over the
transcript produces *proposals*; they appear in a review list; accepting one
mints the commitment; editing one before accepting makes the wording theirs.

Surface A has none of the hard problems in §4, §5 or §6. It carries the entire
data-model change (§3) on its own, and it is genuinely useful to somebody who
already knows what they want to do — which, on a thin feed, is most of the
reason anybody opens Act. **A is specified as shipping first and alone**, and
the owner has since placed it *before* the private preview. B was specified as
conditional on owner decision D1; **D1 was answered yes on 2026-08-21**, so B is
approved rather than conditional, and still second.

### What is deliberately absent

There is deliberately no **survey host, mailing list or contact store inside the
app**, and deliberately **no generated questionnaire, flyer or form**. There is
deliberately **plenty of advice on how to run one**, and the **action item
itself is produced by the app** — that is the feature, not the boundary case.
See [§6b](#6b-the-scope-boundary-the-plan-not-the-deliverable): the app writes
the plan, not the deliverable.

There is deliberately no **free-form action attached to an opportunity**. If
there is a real hearing behind it, the existing action ladder is the surface for
that, and blurring the two would cost the clarity that §4 exists to protect.

There is deliberately no **`remove`-equivalent** — nothing proposes that
somebody drop a commitment they made. This mirrors `profile/proposals.ts`, which
states the reason for its own absence: an AI proposing that you no longer
believe something *"is a much heavier claim than proposing they believe
something new"*. The same asymmetry applies to promises.

---

## 2. What the code says today

Read before proposing anything. Each of these is load-bearing for a decision
below.

**A commitment cannot exist without an opportunity.** `actions/state.ts` has
`opportunityId` and `actionId` as non-null strings, and denormalises
`actionTitle` and `opportunityTitle` — `db/schema.ts` says why: *"so a
commitment still reads sensibly once the source has dropped the opportunity from
its feed."* `actions/routes.ts` `coerceNew` requires all five.

**The headline slot is already the right shape.** On the Act card
(`apps/mobile/app/(tabs)/act.tsx`) and in the `.ics`
(`apps/api/src/reminders/calendar.ts`), `opportunityTitle` is the **heading**
and `actionTitle` is the small line under it. Both were fixed by walkthroughs,
and the comment says why: *"Whatever a person sees at a glance should name what
they committed to; what we think they should do about it is detail."* For a
free-form action, what they committed to **is** the action — so the field is
misnamed rather than the layout being wrong.

**The interviewer cannot do anything, and that is enforced in the prompt.**
`conversation/prompt.ts`:

> Never claim to have done something. You cannot update, save, build or change
> their compass, their profile, their plan or anything else in this app — you
> can only talk.

The file records that this rule was added **after the live model broke it**, and
that a second clause had to be added when refusing made the model reach for a
substitute. There is no tool-calling anywhere in `conversation/`;
`ConversationService.respond` is a plain `chatCompletion`.

**The repo already has the pattern for "a conversation proposes changes to a
settled thing".** `profile/proposals.ts` and `apps/mobile/src/proposals/`:
proposals carry `whyInferred` and `confidence`, are `pending | accepted |
declined`, and accepting *with an edit* flips authorship — an unedited accept
keeps `userConfirmed: false` ("our wording"), an edited one sets it true ("your
words"). The module explains what it replaced: a second conversation used to
copy the whole compass forward and re-ask for approval of things already
settled.

**The repo already has the pattern for "check the model rather than trust it".**
`actions/message.ts` asks the model for its quotes, verifies every one against
the person's real material (`verifyQuotes`), flags position-taking sentences the
compass does not cover (`checkAgainstCompass`), downgrades `status`, and refuses
outright via `NoOwnWordsError` when there is nothing of the person's to build
on: *"A message drafted without your own words would be generic advocacy text
with your name on it."*

**Dateless commitments already degrade correctly.** `reminders/sweep.ts` skips
with `reason: 'no-date'` and the comment *"We do not invent a date… a reminder
about a made-up deadline is worse than none"*; the `.ics` route answers
`nothing-to-schedule` as a readable 409. A free-form action with no deadline
therefore needs no new handling — it needs the person to be told plainly that
no reminder will come.

**A commitment carries no `Provenance` at all.** It inherits its standing from
the opportunity it points at. Cut that link and there is nowhere for provenance
to live, so the field has to be added whichever way §4 is decided.

---

## 3. Decision: how a commitment exists without an opportunity

### Rejected — a synthetic `Opportunity`

Mint a fake opportunity row and point the commitment at it. **This is the worst
of the options and it is worth saying why at length**, because it is the one
that looks cheapest.

It puts a fabricated row in the same store as real civic data, where
`hideStagedInProduction`, `sourceServes`, `expiresAt`, `feed()` and
`matchingNorthStars` all operate on it. Constitution III forbids exactly this —
*"no silent fallback to fabricated data"* — and the addendum §9 forbids staged
and real items being indistinguishable. It would also not survive:
`opportunities/store.ts` `replaceForSource` deletes a source's rows and rewrites
them on every refresh, so the synthetic row either vanishes or requires a fake
source that is never refreshed, which is a second lie propping up the first.

### Rejected — a second kind of commitment

A separate table and a parallel type. This repo has a written scar from exactly
this shape, in `actions/store.ts`:

> the app had two models of the same idea: a careful one that nothing could
> reach, and a crude one that could not remember.

It duplicates the state machine, the reminder sweep, the `.ics`, export, import
and the Act screen. Six places to keep in step, and the file above exists
because two were already one too many.

### Rejected — plain nullable columns

Make `opportunityId` and `opportunityTitle` nullable. Cheapest in the database,
and it pushes `?? ''` into every one of the eight readers listed in the plan.
TypeScript would force each caller to *handle* null; nothing would force any of
them to handle it *well*, and a `?? ''` renders an empty heading on the Act
card. This is the drift failure this repo documents repeatedly — a rule that
holds in the place it was written and quietly does not in the place it was
copied.

### Proposed — a discriminated origin, and one honest rename

```ts
export interface Commitment {
  id: string
  userId: string
  /** What they committed to. The heading, on every surface. */
  title: string
  /** How they are doing it. The line under the heading. */
  actionTitle: string
  rung: string
  origin:
    | { kind: 'opportunity'; opportunityId: string; actionId: string }
    | { kind: 'own'; author: 'you' | 'proposed'; conversationId?: string }
  provenance: Provenance
  // …unchanged: northStarId, status, deadline, remindAt, committedAt,
  //   resolvedAt, reflection
}
```

Three properties earn the extra work over nullable columns:

1. **A reader cannot reach `opportunityId` without having established there is
   one.** Not "should not" — cannot. The compiler is the enforcement, so a new
   surface added in a year cannot forget.
2. **`title` is a name that is true of both kinds.** `opportunityTitle` on a
   commitment with no opportunity is a field lying about itself, and this repo's
   most-repeated lesson (`expiresAt`, `occursAt`, `source` vs
   `provenance.sourceName`) is that one field meaning two things is how a defect
   survives a walkthrough.
3. **`author` records who wrote the words**, matching the compass's
   `userConfirmed`. `'proposed'` means the app's wording, accepted; `'you'`
   means they wrote or reworded it. The Act card can then say *"your words"* or
   *"our wording, which you accepted"* without guessing.

**Cost, stated plainly.** A migration; a change to eight readers; a change to
the export archive shape. Two things keep it survivable, both in the plan:
`opportunity_id` becomes nullable and an `origin` column is *added* — no column
is dropped or renamed, so the encryption AAD (`commitment.id`) is untouched and
old ciphertext still opens. And the archive reader accepts `opportunityTitle` as
an alias for `title`, so archives exported before this change still import.
`import-round-trip.test.ts` is the guard, and the plan says what must make it go
red.

---


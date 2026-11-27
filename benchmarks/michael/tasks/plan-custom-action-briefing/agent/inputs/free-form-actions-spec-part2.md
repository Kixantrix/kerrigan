# Free-form actions (spec), part 2 of 2

> _Excerpt note: sections 5 and 6 (Surface B checks and boundaries), 9 and 10 are omitted; sections 4, 7 and 8 are verbatim._

## 4. Authenticity: how a free-form action announces what it is

This is the part that would be worse to get wrong than to not ship.

### The addendum already has a slot, and it is narrower than it looks

`source/authenticity-addendum.md` §6 defines **Inferred for you** as *"inferred
relevance, alignment, or meaning based on the user's approved civic profile"*,
and lists as an example: ***"which action may suit the user."***

That is close enough that it must be quoted rather than talked around. But it is
a claim about **relevance among things that exist** — which of the ladder's
rungs suits you — not about **minting something that does not exist**. The seven
categories all answer *how do we know this?* A free-form action's missing fact
is different: *who says this is a thing?* And the answer is nobody.

### Three options for the owner

**Option 1 — an eighth category.** Add `proposed` to `AuthenticityCategory`,
whose comment invites exactly this: *"a new kind of content must be classified
explicitly rather than defaulting into something reassuring."*
*Cost:* changes a seven-item promise in a source document, touches the resolver,
the token table, the badge, and every exhaustive `switch` over the union.

**Option 2 — reuse `inferred` and say nothing more.** Free. Also wrong: the
badge would tell a person how the app arrived at the idea and never tell them
that nothing is behind it.

**Option 3 — reuse `inferred`, and state the missing fact where it belongs.
(Recommended.)** Provenance is `ai-inferred` → category `inferred`, whose
existing sentence is already true of a proposed action: *"The system inferred
this… It is an interpretation, not a fact from an external source."* No resolver
change at all. Separately and always, the card carries an **unsourced
statement** in the slot where a sourced item names its organiser and source URL.

The argument for 3 is that the product's own model already separates these
concerns and this would be conflating them. `opportunities/types.ts` keeps
`OpportunityClaim` (the epistemic status of a claim) distinct from
`OrganizerStance` (who is behind it) distinct from `Provenance` (where it came
from). "Nobody is running this" is an **organiser** fact, not a provenance one.
An eighth provenance category would be answering the right question in the wrong
column.

> **Owner decision D2 — answered 2026-08-21, in part.** The name is settled: a
> free-form action is a **custom action**. The owner also placed it, which this
> section had not thought to ask for — *"add an item to the plan view saying
> something like 'if you can't find something useful to do here, brainstorm
> custom actions in chat'."* An empty Plan screen becomes the entry point rather
> than a dead end, which is a better answer than any of the three options here.
>
> **What is still open, and do not read the name as having settled it:** which of
> the three mechanics carries that label. A distinct user-facing term is an
> argument for Option 1's eighth category, but it is an argument and not the
> decision, and `source/authenticity-addendum.md` promises seven. The
> recommendation is unchanged — Option 3 — and so is its honest weakness: "always
> carries a statement" is a convention enforced by review, whereas a category is
> enforced by a compiler. The plan proposes a test that closes most of that gap;
> §8 says what the test must fail on.

### Four rules that hold whichever option wins

These are structural, not guidance, and the plan gives each one a test.

1. **A free-form action never carries a `sourceUrl`, `handoffUrl`, `organizer`
   or `documentUrl`.** Enforced by construction rather than by discipline: it
   has no `Opportunity`, so `buildActionLadder` has nothing to build from and
   `buildHandoffBriefing` has no destination to brief. **No code path may
   synthesise one** — the same rule `ladder.ts` already states for handoffs:
   *"Synthesising one would send someone to a page that may not exist, which is
   worse than offering no link at all."*
2. **It never appears in the Plan feed beside sourced opportunities.** The feed
   is where the app asserts *these things are happening*. A proposal is not
   happening. It lives on Act, and in the conversation that produced it.
3. **The `.ics` says what it is.** `SUMMARY` carries their own words, which is
   right. `DESCRIPTION` gains a line naming it as their own plan, so a calendar
   entry read six months later cannot be mistaken for a civic event somebody
   scheduled. `discreet=1` behaviour is unchanged — it already strips civic
   specifics and must keep doing so.
4. **It is not staged, and the guards must not treat it as staged.**
   `assertNoStagedInProduction` exists to stop fabricated demo content
   triggering real outreach. A free-form action is a real promise a real person
   made; reminders for it are legitimate. Wiring the staged guard here would be
   a plausible-looking mistake that silently removes a working feature in
   production only.

---

## 7. Where it comes from in the UI

**Surface A — Act.** A control reading *"Something you decided to do"*, opening
a short form: what you are going to do, the first step, roughly when, and how
long you think it will take. Nothing is generated. The commitment opens in
`saved` or `committed`, the same two openings `coerceNew` already allows,
because deciding to do something and noting it for later are different acts and
`OPENING_STATUSES` already knows that.

**Surface B — the conversation.** Following `profile/proposals.ts` exactly:

1. The interviewer keeps talking, and its prompt is **unchanged**. It still
   cannot do anything, so the rule quoted in §2 stays literally true.
2. A separate structured-extraction pass over the transcript — a different call,
   with a schema and a validator, like `propose-profile` — produces action
   proposals with their evidence (§5).
3. Proposals surface in a review list. Accept, decline, or accept after
   rewording. Editing makes the wording theirs.
4. Accepting mints the commitment.

**Why not give the chat model a tool.** Three reasons, in order of weight. It
falsifies a prompt rule that exists because the live model already broke it
(§2). It puts a political judgement inside a live call, which is the pattern
`outcome-doctrine.md` §6 identifies as the one deliberately not done — *"an
agent reasoning in a pull request is auditable; the same agent reasoning inside
`fetch()` is not."* And it removes the review step, making the model the thing
that decides rather than the thing that suggests.

> **Owner decision D1, and it is the load-bearing one.** Does the app generate
> actions at all — Surface A alone, or A and then B?
>
> The case against B is `outcome-doctrine.md` §6, quoted above. It is not a
> safety argument, it is an auditability one, and it is the strongest single
> objection to this feature.
>
> The case for B is that the objection was written about a **live classifier at
> ingestion** deciding whether an organisation is worthy, and four things
> differ. It is **additive**, not subtractive — the model offers something
> rather than silently withholding it. It is **visible by construction** — the
> artefact is a card the person reads. It is **person-gated** — nothing exists
> until they accept. And it is **per-person**, not applied to a shared feed. The
> pattern is also already running in this product for a comparable claim:
> north-star proposals are model-generated, person-accepted, and nobody
> considered that a violation.
>
> That is an argument, not a settlement, and the agent making it is not the
> right party to decide it. **A no here is a legitimate outcome.** Surface A
> alone is a real feature that answers most of the owner's complaint, and
> shipping it first is specified precisely so that a no costs nothing already
> built.

> **Answered 2026-08-21: yes — A and then B.** *"D1 yes — thought we already
> discussed that."* The owner also said Surface A can ship before the private
> preview, which keeps the staging above intact rather than making it moot: A
> first is now a schedule rather than a hedge against a no.
>
> The argument above is kept in full and unedited, and that is deliberate. It
> records what was weighed against `outcome-doctrine.md` §6 at the moment the
> doctrine was overruled — including the encampment case under the decisions
> table, which is the concrete evidence *against* the answer that was given. A
> decision that keeps only its winning argument is indistinguishable later from
> one where nobody noticed there was a question.
>
> Everything in this document specified as conditional on D1 is now
> unconditional.

**The action ladder does not change.** *"What could I do about this?"* on the
opportunity card stays exactly as it is. A free-form commitment gets a `rung` —
the vocabulary is good and Act already renders it — but **no ladder**, because a
ladder is rungs for an opportunity and there is no opportunity. Adding a third
entry point on the opportunity card would blur the sourced/unsourced line at the
one place it is currently unmistakable.

---

## 8. Acceptance criteria

Given/When/Then, in the format of [`acceptance-tests.md`](./acceptance-tests.md).
They are **not** copied into that file yet, and deliberately: that file records
what was *observed on the deployed app*, and pre-filling it with unbuilt work
would break its own stated rule that an empty box means "not yet checked" and
never "does not exist".

Each criterion names the automated test that would cover it, per Constitution V.
The plan states, for each, the mutation that must turn it red — a test whose red
condition nobody has written down is a test nobody has checked.

### Surface A — you write it

- **AC-FF1.** Given the owner is authenticated, When they write a commitment of
  their own on Act and save it, Then it persists across a reload, appears in the
  open-commitments list, and its authenticity label reads as user-provided.
- **AC-FF2.** Given a free-form commitment, When it is rendered anywhere, Then
  its heading is the owner's own words and no surface presents an empty or
  placeholder opportunity title.
- **AC-FF3.** Given a free-form commitment, When any surface renders it, Then it
  carries no source URL, no handoff, no organiser and no document link, and no
  code path can produce one for it.
- **AC-FF4.** Given a free-form commitment, When the Plan feed is rendered, Then
  it does not appear there.
- **AC-FF5.** Given a free-form commitment with a date, When the owner downloads
  its `.ics`, Then the file names it as the owner's own plan rather than a
  scheduled civic event, and `?discreet=1` still strips civic specifics.
- **AC-FF6.** Given a free-form commitment with no date, When the reminder sweep
  runs, Then it is skipped for `no-date` and the owner is told plainly that no
  reminder will arrive — not left to infer it from silence.
- **AC-FF7.** Given a free-form commitment, When it moves through the state
  machine, Then every transition legal for a sourced commitment is legal for it
  and none is special-cased.
- **AC-FF8.** Given a mixture of sourced and free-form commitments, When the
  owner exports and re-imports their archive, Then the archive round-trips
  equal, and an archive exported **before** this feature still imports.
- **AC-FF9.** Given a free-form commitment, When the owner deletes their
  account, Then it is destroyed with everything else and the count reported is
  what storage actually removed.
- **AC-FF9a.** Given the Plan screen, When it is rendered, Then it offers a way
  into custom actions, worded so that somebody who found nothing useful in the
  feed is pointed at chat rather than left at a dead end.

  The owner's, added after this document was drafted: *"add an item to the plan
  view saying something like 'if you can't find something useful to do here,
  brainstorm custom actions in chat'."* It is written as an AC and not as a copy
  suggestion because it changes what Surface A is for. §2 argues Act is empty;
  this says the emptiness a person actually notices is on **Plan**, where they
  went looking for something to do and the feed was thin. That is the same
  complaint `civic-sources-proposal.md` addresses by widening the feed, answered
  from the other end.

  Deliberately not conditioned on the feed being empty. A pointer that appears
  only on a bad week is a pointer nobody learns exists, and the reader who has
  six items none of which are theirs is in exactly the position this serves.
  Whether it is always present or promoted when the feed is thin is a design
  question the plan should settle with the Plan screen's existing headings —
  which, as of this writing, now say what the list is sorted by.

### Surface B — the conversation proposes it

Owner decision D1 was **answered yes on 2026-08-21**, so these are approved
rather than conditional. Still second: A ships first, and now ships before the
private preview.

- **AC-FF10.** Given a conversation, When the interviewer replies, Then it never
  claims to have created, saved or scheduled anything, and no chat turn mints a
  commitment.
- **AC-FF11.** Given a person with no approved compass, When an action proposal
  is requested, Then nothing is proposed and the reason is stated.
- **AC-FF12.** Given a proposed action, When it is shown, Then it carries at
  least one verified quote from the owner's own words, and a proposal whose
  quotes do not verify is never shown.
- **AC-FF13.** Given a proposed action naming an institution, When that
  institution does not resolve against the owner's real representatives, Then
  the claim is removed rather than softened.
- **AC-FF14.** Given a proposed action, When it is shown, Then it states how
  long it takes and that nobody has scheduled it, and makes no claim about what
  it will achieve.
- **AC-FF15.** Given a proposed action, When the owner accepts it unedited, Then
  the commitment records the wording as the app's; When they reword it first,
  Then the commitment records the wording as theirs.
- **AC-FF16.** Given a proposal the doctrine declines to serve as written, When
  the owner looks, Then they can see that a decision was made and what it was —
  a refusal they cannot see is a shadow ban.
- **AC-FF17.** Given a proposed action, When it is declined, Then it does not
  reappear.
- **AC-FF18.** Given a proposed action whose object is an identifiable private
  individual **and** whose intended effect on them is adverse, When proposals are
  produced, Then it is not proposed — and Given both conditions are not met, When
  an action involves other people without targeting one, Then it **is** proposed.
  Both directions, because a check that only ever fires one way is
  indistinguishable from a check that always fires.
- **AC-FF19.** Given an action the doctrine declines to serve as written, When
  the app offers a redirect, Then the redirect names a route rather than only
  declining — *"a redirect that does not name a better route is a refusal
  wearing a nicer word."*
- **AC-FF20.** Given a person asking how to go about a commitment they made,
  When the app answers, Then it gives advice on how to proceed. **Asserted as a
  presence, not an absence** — the failure this guards is the app going quiet
  about content, and a test that only checks nothing was emitted would pass on
  an empty reply.
- **AC-FF21.** Given a person asking the app to write the artefact itself, When
  the app answers, Then it declines to emit a verbatim-usable block, says where
  that is done instead, and **continues being useful about how to do it** — the
  shape `conversation/prompt.ts` already requires of a refusal, because *"refuse
  and stop" with nothing following it is how a refusal turns into a dead end.*
- **AC-FF22.** Given the interviewer over a run of turns about a commitment,
  When the replies are measured, Then the rate of replies containing a
  verbatim-usable block is **reported as a number**. Not a pass/fail: per open
  question 7 this line is not expected to hold perfectly by prompt, and a
  criterion asserting that it does would be asserting a defect.
- **AC-FF23.** Given the scope rule as written in §6b, When it is applied to the
  three cases of the three-way test, Then it **permits** the action item,
  **permits** the advice, and **excludes** the questionnaire, form, contact list
  and collected responses. All three assertions, in one test, against the
  encampment case — because this rule has been wrong four times and every one of
  those versions would have passed a test that checked only the third.

---


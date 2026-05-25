# Skill: ui-design-perspective

**When:** any project that produces user-facing UI (web, dashboard, app, embedded widget).
**Output:** principles baked into the spec/plan + a pre-vis artifact before deep implementation.
**Why:** Kerrigan's UI projects should look intentional, not accidental. Curated taste prevents bland defaults.

## The four principles

### 1. Pre-vis before commit

Before any task that builds production UI, produce a **single-page mockup** in HTML+CSS (no build chain, no framework) that captures the intended look and key interactions. This is the cheapest fidelity-test.

- **What it is**: one `mockup.html` per major screen, opened directly in a browser, demonstrating layout, hierarchy, type, color, and the show-stopper element (principle 3).
- **What it isn't**: not a clickable prototype, not framework code, not pixel-perfect.
- **Where it lives**: `specs/projects/<name>/previs/` during planning. Discarded or evolved into the real implementation once the direction is approved.
- **Dispatch shape**: a "pre-vis" task is a normal cloud-dispatched task with an AC like "open `previs/index.html` in a browser; the layout/aesthetic matches the spec's design direction".
- **Approval gate**: the human approves the pre-vis in the spec issue before any `/speckit.plan` finalization.

### 2. Sleek, modern, responsive — researched, not invented

Default UI from cloud agents tends toward Bootstrap-circa-2018. Counter this by **finding references first**.

- **Research step** (during planning, before pre-vis): list 3-5 *current* (last 12 months) production sites/apps that nail the target aesthetic and capture *what specifically* makes them good — type pairing, spacing rhythm, motion, accent color, density, etc.
- **Reference artifact**: `specs/projects/<name>/design-references.md` with named examples + extracted lessons + (where licit) screenshots/links.
- **Responsive is non-negotiable**: every pre-vis must work at 360px, 768px, 1280px, 1920px. The agent demonstrates this with browser-resize screenshots in the PR.
- **Performance is design**: first contentful paint < 1s on a typical connection, no layout shift, no janky scroll. These are ACs, not afterthoughts.

### 3. One show-stopper per project

Every UI project has **exactly one** element that is unique, delightful, and characteristic of *this* project — not borrowed from any reference site.

- **What qualifies**: a novel interaction, a custom data visualization, an unexpected use of motion, a clever empty state, a meaningful audio/haptic cue, a domain-specific affordance. Something a user would screenshot and share.
- **What doesn't**: a gradient, a glassmorphism panel, a generic loading spinner, a stock chart library.
- **Where it goes in the spec**: a dedicated `## Show-stopper` section in `spec.md` describing the element, why it fits this project, and how a user encounters it.
- **Identification timing**: surfaced during initial spec/clarify, not bolted on at the end. If the show-stopper isn't clear from the project's purpose, `/speckit.clarify` should ask the human.

### 4. Simplicity — few elements, well-curated

Fewer elements done well beat more elements done adequately. This applies at every scale.

- **Information density**: surface only what the user needs *right now*. Progressive disclosure for everything else.
- **Component count**: prefer reusing 5 well-built components over 20 one-offs. Every new component pattern needs a justification in `architecture.md`.
- **Color palette**: 2 neutrals + 1 brand + 1 accent. Add only when a real semantic need appears (success/warning/error).
- **Type scale**: 4-5 sizes maximum.
- **Motion**: any animation > 300ms or that doesn't aid comprehension is a smell.
- **Copy**: every label, button, and microcopy line gets the same care as a component. Vague verbs ("Submit", "Continue") fail this principle.

## How this skill is applied

The `kerrigan` profile preloads this skill via briefing-packet's `Relevant skills (preload)` section whenever a project's spec touches user-facing UI. The cloud agent reads it before producing pre-vis or implementation work, and treats the four principles as additional implicit acceptance criteria.

## Required artifacts per UI project

| Artifact | Path | When |
|---|---|---|
| Design references | `specs/projects/<name>/design-references.md` | Before pre-vis dispatch |
| Pre-vis mockup | `specs/projects/<name>/previs/index.html` (and per-screen as needed) | Before plan finalization |
| Show-stopper section | `specs/projects/<name>/spec.md` § Show-stopper | Initial spec |
| Responsive screenshots | PR body | Every UI-touching PR |

## Anti-patterns to flag in review

- Pre-vis skipped or produced after implementation started — direction wasn't actually approved.
- "Modern" achieved purely by copy-pasting Tailwind UI / shadcn examples with no curation.
- Show-stopper missing or hand-waved ("the whole experience is the show-stopper" = no show-stopper).
- More than 7 distinct colors, 6 type sizes, or 3 button styles without justification.
- Animations on hover/load that don't communicate state change.
- Mobile breakpoint as an afterthought rather than designed-from.

## See also

- [playbooks/design-iteration.md](../../../playbooks/design-iteration.md) — iteration workflow with the design agent.
- [.github/skills/briefing-packet/SKILL.md](../briefing-packet/SKILL.md) — preload this skill in UI project briefings.
- [.github/skills/kerrigan-acquire/SKILL.md](../kerrigan-acquire/SKILL.md) — used to acquire stack-specific UI skills (React, Next.js, Vite, etc.) once a stack is chosen.

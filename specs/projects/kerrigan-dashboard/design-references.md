# Design References: kerrigan-dashboard

> Per `.github/skills/ui-design-perspective/SKILL.md` principle 2: every UI project cites 3–5 current production examples with what we're borrowing and what we're rejecting. This is the brief the pre-vis must visually answer.

## 1. Linear — workspace inbox + multi-project status

**What it does**: Project management surface with a unified inbox across projects, sharp keyboard-first navigation, restrained motion, and confident typography.

**What we borrow**:
- Inbox-as-first-class-surface. Linear's "Inbox" is the conductor's intervention queue.
- Restrained accent color (single brand color carrying state) — proves the 2 neutrals + 1 brand + 1 accent budget works at scale.
- Snappy view transitions (≤200ms) — no fade-fade-fade theater.
- Keyboard-first interactions; mouse is a fallback.

**What we reject**:
- Linear is web-first; our app is local — we don't need account/auth chrome.
- Linear's information density is for many people; ours is for one. We can give breathing room.

**Visual signals**: monochrome with one electric accent. Dense lists. Subtle gridlines. Whisper-quiet motion.

---

## 2. Vercel Dashboard — portfolio card grid

**What it does**: Top-level grid of project cards, each showing live deployment status, framework, last activity, and a tiny activity sparkline.

**What we borrow**:
- Card-per-project portfolio layout. Cards are scannable; status is glanceable.
- Tiny activity indicators (live deployments) — translates directly to "current wave" + "blocked count" badges on our cards.
- The "click a card → fluid transition to project detail" pattern.

**What we reject**:
- Vercel's gradients on hover are slightly louder than our brief. We dial that back.
- Their card density assumes many projects; we tolerate fewer but richer cards.

**Visual signals**: clean card grid, subtle status pills, careful use of color (green=healthy, yellow=warning, red=critical).

---

## 3. Retool Workflows — node-based DAG editor

**What it does**: Visual DAG editor for workflow automation. Drag nodes, connect edges, see live state of each step.

**What we borrow**:
- The node-and-edge canvas is the right visual metaphor for plan stages and dependencies.
- Per-node status pill + small icon stack — clear without being noisy.
- The "data flowing along edges" indicator (Retool shows it when a workflow is mid-execution).
- Auto-layout (dagre or elk under the hood) so the user doesn't position nodes manually.

**What we reject**:
- Retool is fully edit-from-canvas; our DAG is mostly read-only (plan editing happens in the text pane, not by dragging nodes).
- Retool's heavy chrome around each node is overkill for our scale — we want lighter cards.

**Visual signals**: rectangular nodes with a status strip, clean orthogonal edges, calm grid background, animated edge highlights during execution.

---

## 4. Warp / Cursor — embedded AI chat pane

**What it does**: Terminal (Warp) / editor (Cursor) with an integrated chat pane that streams agent responses and lets the AI invoke tools.

**What we borrow**:
- Chat pane as a permanent right-rail, not a modal or popover.
- Streaming token rendering with smooth scroll-pin.
- Tool-call expansion: each "the agent ran X" appears as a collapsible card, not a wall of text.
- Slash-commands for power users (e.g., `/dispatch`, `/status`).

**What we reject**:
- Warp leans heavily on terminal aesthetics; we render Copilot output as rich markdown, not as a terminal transcript.
- Cursor's chat is single-thread; we may want per-project history persistence (deferred to v2 but design must not preclude it).

**Visual signals**: right-rail chat with a clear input affordance at the bottom, message bubbles with subtle differentiation between user/agent/tool, generous monospace for code blocks.

---

## 5. GitHub Projects (v2, classic projects roadmap) — cross-repo status roll-up

**What it does**: Native GitHub surface for tracking issues/PRs across multiple repos with grouping, filtering, and state visualization.

**What we borrow**:
- The mental model of "items roll up across repos under a project umbrella".
- Familiar status terminology aligned with GitHub's own labels — reduces cognitive load for users who live in GH.
- Filter chips at the top of the view (status, repo, assignee).

**What we reject**:
- GitHub Projects is generic; we hardcode Kerrigan-specific status taxonomy (blocked, needs-attestation, etc.) for tighter signal.
- GitHub Projects' UI is web-heavy; our local-only context lets us be snappier and quieter.

**Visual signals**: clear filter chips, dense table/board, status pills using GitHub's own color vocabulary as anchor.

---

## Synthesis — the kerrigan-dashboard visual identity

Combining these:

- **Layout**: portfolio cards (Vercel) → project detail with three panes (Cursor right-rail chat + Retool middle canvas + Tiptap left text editor).
- **Color**: 2 neutrals (near-black background + near-white text) + 1 brand (cool indigo or near-cyan; final pick during pre-vis) + 1 accent (warm amber or green for status moments).
- **Type**: 4 sizes (display 28px, heading 18px, body 14px, micro 12px). One sans family (Inter or system). Monospace only inside code blocks.
- **Motion**: ≤300ms per transition. Easing curves that feel mechanical, not theatrical. Show-stopper PR-flow particles can run longer (≤2s) but at a calm pace, not a sparkle storm.
- **Density**: tighter than Vercel, looser than Linear. Single-user context lets us breathe.
- **Tone**: confident, restrained, occasionally playful in the show-stopper. No emoji, no exclamation marks, no rainbow status colors.

## Show-stopper detail

The PR-flow animation (see `spec.md` § Show-stopper) sits on the DAG canvas. References:

- The flowing-edge highlight in Retool Workflows during a live run.
- The "deployment in progress" animation on Vercel project cards.
- The way Apple Maps renders a route being calculated — particles tracing an arc.

Pre-vis must demonstrate the animation in a static HTML+CSS+JS prototype on at least one node before any production code is written.

## Decisions locked

The following visual decisions were resolved during M1 pre-vis and are now design-locked. All subsequent production milestones must match these choices.

- **Brand color**: `#5965F2` (cool indigo). Selected over `#22D3EE` because indigo reads more "orchestration tool" than "observability dashboard", and it pairs cleanly with the near-black background without washing out on dim displays.
- **Accent color**: `#F59E0B` (warm amber). Used for intervention states (blocked counts, attestation needed) — amber reads as "needs attention" without the alarm of red, keeping the red palette reserved for true blocks.
- **Type scale**: `28px` (display heading), `18px` (section heading), `14px` (body), `12px` (metadata / labels), `10px` (node status strips / micro). Five sizes total, within budget.
- **Default animation variant**: `dots`. Three variants are present in the pre-vis (dots, line trail, glow trail); dots was selected as the default because it communicates "many discrete events" most faithfully to the PR-flow metaphor without the visual weight of the glow trail distracting from the DAG structure.

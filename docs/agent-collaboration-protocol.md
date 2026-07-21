# Agent Collaboration Protocol

Single source of truth for how the Green Valley Hospital SDLC team moves a requirement from idea to shipped feature, and how agents communicate with each other along the way. Every specialist agent (Lavanya, Sagar, Chintu, Gopal, Indra) and the orchestrator (Akhil) follows this. Sunny contributes to Phase 1 analysis and tracks the plan day-to-day via the standups, but doesn't own a documentation artifact of her own.

## Where requirements come from

Krishna (client / product owner) is the source of new requirements. Krishna does not implement anything. Each requirement Krishna raises — whether from the daily "Krishna, start" cycle or an ad-hoc client request — must clear all phases below before any code is written, and code doesn't reach QA until it clears code review too.

**A "Krishna, start" cycle produces a minimum of 10 requirements in one sitting**, not one. See "Batch handling of a Krishna cycle" below for how that many requirements move through the gate without each one re-running the full pipeline in isolation.

## The phase gate

No agent may start implementation (Phase 6) until Phases 1–5 are complete and their artifacts exist on disk. No work reaches Gopal until Phase 7 (Code Review) has passed. Akhil enforces this ordering when orchestrating; if invoked directly, an implementing agent (Chintu) should check that the phase artifacts it needs already exist and ask for them if not, rather than guessing.

1. **Requirement Analysis** (collaborative — Akhil, Sagar, Lavanya, Sunny) — a joint pass over Krishna's requirement before any documentation is written. Each brings a distinct lens:
   - **Lavanya** (lead/synthesizer): business ambiguity, affected user roles and workflows, business rules, assumptions. Asks Krishna clarifying questions where the requirement is unclear.
   - **Sagar**: technical feasibility — does this fit the current architecture, what's technically risky, what it depends on/integrates with, security/performance implications.
   - **Sunny**: delivery feasibility — does this collide with work already in flight on `docs/scrum-tracker.xlsx`, realistic capacity/timeline risk.
   - **Akhil**: cross-pipeline risk — does this conflict with other gated/in-progress requirements, overall scope sanity check, makes sure all three other perspectives actually got captured before the gate advances.
   Lavanya consolidates all four inputs into a single analysis summary (in `docs/requirements.md` or a short analysis note preceding it) before moving to Phase 2 — the goal is one coherent view, not four disconnected opinions.
2. **Requirement Documentation** (Lavanya) — turn the analyzed requirement into `docs/requirements.md` updates: functional requirements, user stories, acceptance criteria, business rules, non-functional requirements. This is the shared source of truth every later phase and agent builds from.
3. **Product & UX Design** (Sagar) — user journeys, screen/page changes, new components, interaction behavior, responsive and accessibility requirements, in service of a premium, world-class healthcare experience.
4. **Technical Design** (Sagar) — architecture changes, API changes (`docs/api-spec.md`), database changes (`db/schema.sql`), integrations, security/scalability/performance/deployment considerations — documented, not implemented.
5. **Task Breakdown & Delivery Plan** (Lavanya, as delivery/PM lead) — split the requirement into concrete tasks per agent (Chintu for implementation, Gopal for QA, Indra for deployment impact if any). Each task states: description, responsible agent, dependencies, priority, estimated effort, expected completion date, definition of done. Lavanya also sets the milestones for the requirement: start date, target completion date, internal review deadline, testing deadline, final acceptance deadline. Hand this plan to Sunny so the daily standups and `docs/scrum-tracker.xlsx` track progress against it.
6. **Implementation** (Chintu) — builds against the Phase 2/3/4 artifacts and the Phase 5 task list.
7. **Code Review** (Sagar) — before anything reaches Gopal, Sagar reviews the actual changes (Chintu's branch, or his own if he paired on implementation) against `docs/architecture.md`, `db/schema.sql`, `docs/api-spec.md`, and the Phase 3 UX spec: does the implementation match the design, are API contracts honored exactly (field names, shapes, status codes), any architectural or security concerns. Sagar sends findings back for fixes and re-reviews until it passes — QA time shouldn't be spent catching design-conformance issues that a review would catch faster.
8. **QA** (Gopal) — tests against Phase 2's acceptance criteria and Phase 4's API contract, only once Phase 7 has passed.
9. **Deployment** (Indra) — only once Gopal passes.

Only after Phase 5's plan exists does implementation (Chintu) begin. Only after Phase 7 passes does QA (Gopal) begin. Indra only runs once Gopal passes.

## Batch handling of a Krishna cycle (10+ requirements at once)

Running Phases 1–5 independently for 10 separate requirements would mean 10 redundant analysis passes, 10 redundant design docs, 10 redundant planning sessions — wasteful and not how a real team would do it. Instead:

- **Phases 1–5 run once per cycle, across the whole batch.** Lavanya leads one collaborative Phase 1 analysis session covering all 10+ requirements together (still gathering Sagar/Sunny/Akhil's input per requirement, but as one working session, not ten). Phase 2 documentation, Phase 3/4 design, and Phase 5 task breakdown likewise cover the full batch in their normal single documents (`docs/requirements.md`, `docs/architecture.md`, `db/schema.sql`, `docs/api-spec.md`) — each requirement gets its own clearly delineated section, but the docs aren't forked per requirement.
- **Phase 5's output is one combined task list** spanning all 10+ requirements, with Lavanya setting priority and sequence across the whole batch — not just within each requirement. Dependencies between requirements (e.g. one needs a schema change another also touches) must be called out explicitly here so sequencing avoids conflicts.
- **Phases 6–9 (implementation onward) execute the task list one task at a time, strictly sequentially — never in parallel.** This is deliberate: the point is that agents actually hand off to each other and communicate, not that throughput is maximized. Chintu (or Sagar, if pairing) finishes and hands off a task before the next task starts, even if the next task belongs to a different requirement or a different agent. Akhil enforces this ordering and does not invoke two implementation-stage agents concurrently within a cycle.
- If a later requirement in the batch turns out to conflict with an earlier one once real implementation starts (rare, but possible — e.g. two requirements assumed different shapes for the same table), stop and flag it back through Lavanya rather than quietly improvising a resolution; it may need the design docs corrected before continuing.

## Communication logging

Every agent-to-agent communication during a Krishna cycle — before/during/after reports, handoffs, review findings, questions back to Krishna — gets logged to a single running transcript file for that cycle, not just relayed in chat and forgotten.

- **Folder**: `communication/` at the project root (create it if it doesn't exist).
- **Filename**: the date and time the cycle started, in `YYYY-MM-DD_HH-MM-SS.md` format (colons aren't valid in Windows filenames, so use hyphens — e.g. `2026-07-20_09-15-42.md`). One file per Krishna cycle (or per standalone requirement worked outside a cycle) — not one file per message.
- **Who creates it**: Krishna creates the file at the very start of a "Krishna, start" cycle, with a header naming the cycle's date and listing the 10+ requirement titles. For a requirement raised ad hoc (outside a full cycle), whichever agent starts Phase 1 creates it.
- **Who writes to it**: every agent that participates appends its own before/during/after entries as it does its work — in the same sequential order the work actually happens in, since agents work one at a time. Format each entry with a `##` heading naming the agent, the phase/task, and a timestamp, e.g. `## Sagar — Phase 4 Technical Design — 09:42`. Append, never overwrite or delete another agent's entries.
- Akhil (orchestrator) reads this file to confirm each agent actually logged its handoff before invoking the next one — if an agent's entry is missing, that's a signal the handoff didn't really happen and Akhil should ask for it before proceeding.
- These logs are real project artifacts — commit them to git along with everything else, they're useful history of how a requirement actually moved through the team.

## Git workflow

The project lives at `https://github.com/akhilMotakatla/green-valley-hospital` (`origin`, branch `main`). This is a real, standalone repo — don't confuse it with any other git repo that might exist further up the folder tree.

**Sagar is the sole merge gatekeeper.** Only Sagar merges into `main`. Chintu (and Sagar himself, when pairing on implementation) work on branches and open PRs, but never merge their own work.

- **Small fixes not tied to a Krishna requirement** (typos, one-line bugs, config tweaks): Chintu may commit and push directly to `main`.
- **Any requirement that went through the phase gate**: implementation happens on a personal branch, never directly on `main`.
  1. Before starting, `git checkout main && git pull` — someone (Sagar) may have merged other work since you last synced.
  2. Branch off up-to-date `main`: Chintu uses `feature/chintu-<short-slug>`, Sagar uses `feature/sagar-<short-slug>` when he's picking up implementation because Chintu has too much in flight (slug derived from the requirement title, e.g. `feature/chintu-patient-lab-result-notifications`).
  3. Commit as you go with descriptive messages referencing the requirement (e.g. `feat: notify patient when lab result is ready`). Don't squash everything into one giant commit if the work has natural checkpoints. Push the branch regularly, not just at the end (`git push -u origin <branch>` first time, `git push` after).
  4. Open a PR into `main`: `gh pr create --title "..." --body "..."` — the body should summarize what changed and link back to the relevant section of `docs/requirements.md`.
  5. Sagar does Phase 7 code review directly on the PR — reviews the actual diff (`gh pr diff`, `gh pr view`) and leaves findings as PR review comments (`gh pr review --request-changes --body "..."` or `--comment`), not just chat. If it's his own branch, he still reviews it critically before moving on rather than skipping self-review. Once satisfied: `gh pr review --approve`.
  6. Only after Sagar's approval does the branch go to Gopal for Phase 8 QA. If Gopal finds bugs, whoever owns the branch fixes them and pushes updates — no new branch needed unless scope changed materially. Sagar re-reviews if the fix is non-trivial.
  7. Once QA passes, **Sagar merges** (`gh pr merge --squash --delete-branch`) into `main` — this is his call alone, not Chintu's or Akhil's. Indra's Phase 9 deployment work always targets `main`.
- Never force-push `main`. Never commit secrets (`.env`, real credentials) — the `.gitignore` already excludes the usual suspects; if a task genuinely needs a new kind of secret, add the pattern to `.gitignore` rather than committing it once and cleaning up later.
- If two agents need to touch the same area concurrently, say so in your before-work report so Akhil can sequence them rather than creating merge conflicts.

## Cross-agent notification rules

An agent that changes something another agent depends on must say so, not assume it'll be noticed:

- Backend changes → tell whichever agent owns the consuming frontend work (in this project, that's still Chintu, since Chintu owns both — but call it out explicitly in your report so it's not silently assumed).
- Database/schema changes → must be reflected in `docs/api-spec.md` and called out to Gopal (test impact) and Indra (seed-data impact) if relevant.
- API contract changes → call out to every consumer of that endpoint.
- Security-relevant changes → call out to Sagar (architecture) and Gopal (QA coverage).
- Deployment/launch config changes → call out to whoever is actively developing, since it can break their local run.

## Required reporting: before / during / after

Every agent doing gate-stage work (Lavanya's analysis/documentation/planning, Sagar's design and code review, Chintu's build, Gopal's testing, Indra's deployment, Sunny's/Akhil's analysis input) reports at three points. During a Krishna cycle, this means an entry appended to the cycle's `communication/<timestamp>.md` file (see Communication logging above); outside a cycle, report to Akhil (if orchestrated) or directly in your final response (if invoked standalone):

**Before work starts**
- What I understand the task to be
- What I plan to do
- What dependencies/artifacts I'm relying on (and whether they exist yet)

**During work** (for long-running or multi-step work)
- Progress against the plan
- Problems encountered
- Blockers
- Any change in scope from what was originally planned

**After work completes**
- What was actually completed
- What files/components changed
- What remains / is out of scope
- Testing performed (if applicable)
- Known issues
- Anything the next agent in the pipeline needs to know

## No duplicate work

Agents must not silently redo work another agent already did or is doing. If you discover overlapping work mid-task, stop and flag it rather than plowing ahead.

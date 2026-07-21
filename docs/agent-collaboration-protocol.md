# Agent Collaboration Protocol

Single source of truth for how the Green Valley Hospital SDLC team moves a requirement from idea to shipped feature, and how agents communicate with each other along the way. Every specialist agent (Lavanya, Sagar, Chintu, Gopal, Indra) and the orchestrator (Akhil) follows this. Sunny contributes to Phase 1 analysis and tracks the plan day-to-day via the standups, but doesn't own a documentation artifact of her own.

## Where requirements come from

Krishna (client / product owner) is the source of new requirements. Krishna does not implement anything. Each requirement Krishna raises — whether from the daily "Krishna, start" cycle or an ad-hoc client request — must clear all phases below before any code is written, and code doesn't reach QA until it clears code review too.

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
7. **Code Review** (Sagar) — before anything reaches Gopal, Sagar reviews Chintu's actual changes against `docs/architecture.md`, `db/schema.sql`, `docs/api-spec.md`, and the Phase 3 UX spec: does the implementation match the design, are API contracts honored exactly (field names, shapes, status codes), any architectural or security concerns. Sagar sends findings back to Chintu for fixes and re-reviews until it passes — QA time shouldn't be spent catching design-conformance issues that a review would catch faster.
8. **QA** (Gopal) — tests against Phase 2's acceptance criteria and Phase 4's API contract, only once Phase 7 has passed.
9. **Deployment** (Indra) — only once Gopal passes.

Only after Phase 5's plan exists does implementation (Chintu) begin. Only after Phase 7 passes does QA (Gopal) begin. Indra only runs once Gopal passes.

## Cross-agent notification rules

An agent that changes something another agent depends on must say so, not assume it'll be noticed:

- Backend changes → tell whichever agent owns the consuming frontend work (in this project, that's still Chintu, since Chintu owns both — but call it out explicitly in your report so it's not silently assumed).
- Database/schema changes → must be reflected in `docs/api-spec.md` and called out to Gopal (test impact) and Indra (seed-data impact) if relevant.
- API contract changes → call out to every consumer of that endpoint.
- Security-relevant changes → call out to Sagar (architecture) and Gopal (QA coverage).
- Deployment/launch config changes → call out to whoever is actively developing, since it can break their local run.

## Required reporting: before / during / after

Every agent doing gate-stage work (Lavanya's analysis/documentation/planning, Sagar's design and code review, Chintu's build, Gopal's testing, Indra's deployment, Sunny's/Akhil's analysis input) reports at three points, either to Akhil (if orchestrated) or directly in its final response (if invoked standalone):

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

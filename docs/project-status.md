# Project Status — Read This First

**Every agent (Krishna, Akhil, Lavanya, Sagar, Chintu, Gopal, Indra, Sunny) reads this file at the start of every invocation, before doing anything else.** This is the fast-orientation doc — what exists, what was recently done, where things stand right now. It exists so no one has to re-Glob/re-Grep/re-read the entire codebase from scratch every time a requirement comes in. Treat it the way a real team member treats picking up from yesterday: you already know the codebase, you just need to know what changed since you last looked.

**Rule for every agent**: read this file first. Only read/grep full source files when you're actually about to touch, verify, or reference something specific for your current task — not to "figure out what the project is" in general. When you finish meaningful work, add a dated entry to the Changelog below and update the relevant summary section, so the next invocation (yours or anyone else's) doesn't have to rediscover it. This file is only useful if it stays current — an agent that finishes work without updating it is quietly breaking this for everyone else.

If something here conflicts with what you actually find in the code, the code wins — update this file to match reality, don't trust a stale note over what you can see.

Last updated: 2026-07-20.

---

## What this project is

Green Valley Hospital: a hospital web application with a public marketing site and six role-based authenticated portals. Built as a full SDLC simulation — a fictional client (Krishna) drives requirements, an agent team (Lavanya, Sagar, Chintu, Gopal, Indra, Sunny, orchestrated by Akhil) delivers them through a five-phase-plus gate (see `docs/agent-collaboration-protocol.md`).

**Stack**: FastAPI + SQLAlchemy 2.x + SQLite backend, React 19 + Vite + TypeScript frontend (plain CSS, no Tailwind), JWT auth (python-jose + bcrypt).

## Roles / portals implemented

Admin, Doctor, Patient, Staff (nurse+receptionist combined), Lab, BillingSpecialist — all functional with role-guarded routing. Full capability list per role lives in `docs/requirements.md` §2 (long — only open it if you need role-specific detail beyond what you already know).

## Public site pages

Home, About, Departments (listing), Department Doctors, Doctor Profile, Contact, Blog (list + article), Login, Signup. Shared nav/footer in `PublicLayout.tsx`, authenticated shell in `AppShell.tsx`.

## Current visual design system — IMPORTANT, read before touching any public-page styling

The public site went through **two full redesigns**. Only the second one is current:

1. ~~Light "luxury" teal/gold theme~~ (`docs/luxury-redesign-requirements.md`) — **superseded, do not follow this doc for styling.** Kept for historical reference only.
2. **Current: dark, cinematic, glassmorphism theme.** Full-screen sections, deep charcoal/navy/brown palette (not pure black), sparing gold/bronze accent, frosted-glass cards/panels (`backdrop-filter: blur()` + translucent dark fill + thin border) layered over full-bleed photography. Dark tokens are scoped under the `.public-page` class in `src/frontend/src/index.css` (`:root` still has old light tokens for reference/fallback — the actual public site never uses them because `.public-page` overrides them). Fonts unchanged: Playfair Display (headings, public only) + Inter (body/UI). Authenticated portal pages (`AppShell.tsx` and everything under `pages/admin|doctor|patient|staff|lab|billing`) were **not** touched by this redesign and remain on the original functional styling — that's intentional scope, not an oversight.
3. Homepage hero is `src/frontend/src/components/MosaicHero.tsx`, now a full-screen (100svh) cinematic hero with parallax — the earlier "masked card mosaic" 4-window technique was retired in favor of this; the masked-card hooks (`useMaskPositions`, `MaskedCard`, etc.) still exist in the codebase but are unused by the current hero.

## Content / seed data

10 departments (Cardiology, Pediatrics, Orthopedics, Neurology, Oncology, Radiology, Emergency Medicine, Ophthalmology, Gynecology, Dermatology), 10 doctors (1 per department), 8 published blog articles. Seeded via `db/seed/seed.py` (idempotent, safe to re-run). Real, visually-verified photos exist in `src/frontend/public/images/` for hero/about/contact/departments-hero/auth-panel/facility gallery (6 images)/blog covers/all 10 department cards — **don't blindly trust any doc's photo-ID-to-subject mapping** (several turned out wrong when actually checked pixel-by-pixel); if you need a new image, verify it visually before committing to a filename.

`GET /api/public/home` featured-departments cap was raised from 4 to 9; homepage "Meet Our Specialists" shows up to 8 doctors (was 4).

## Git / GitHub

Standalone repo (not part of any parent folder's git history): **https://github.com/akhilMotakatla/green-valley-hospital**, public, `origin`/`main`. `.gitignore` already excludes venvs/node_modules/db file/uploads/.env.

**Branch + merge model**: Chintu implements on `feature/chintu-<slug>` branches, Sagar can pair on implementation via `feature/sagar-<slug>` when Chintu's overloaded. Sagar does Phase 7 code review as real GitHub PR reviews (`gh pr review`) and is the **sole merge gatekeeper** — nobody else merges into `main`. Full detail in `docs/agent-collaboration-protocol.md`.

## The agent team and process

Krishna (client/product owner) → collaborative Phase 1 analysis (Akhil + Sagar + Lavanya + Sunny, Lavanya leads/consolidates) → Lavanya documents (`docs/requirements.md`) → Sagar designs UX + technical (`docs/architecture.md`, `db/schema.sql`, `docs/api-spec.md`) → Lavanya breaks into tasks/milestones → Chintu (or Sagar) implements on a branch → Sagar code-reviews the PR → Gopal QA's it → Sagar merges → Indra handles deployment/launch config. Sunny runs daily standups tracking Lavanya's milestones. Full detail (including the before/during/after reporting convention and cross-agent notification rules) is in `docs/agent-collaboration-protocol.md` — read that once per task type, not this summary alone, when you're actually doing gate-stage work.

**A "Krishna, start" cycle produces a minimum of 10 requirements at once**, not one — Phases 1–5 run once across the whole batch, then Phase 6 onward executes the resulting combined task list one task at a time, strictly sequentially (never in parallel), so real agent-to-agent handoffs happen. Every agent-to-agent communication during a cycle is logged to `communication/<YYYY-MM-DD_HH-MM-SS>.md` (one file per cycle, created by Krishna at the start, appended to by every participating agent in order) — see "Communication logging" in `docs/agent-collaboration-protocol.md`.

Krishna keeps her own no-repeat history in `docs/krishna-daily-requirements-log.md` — she checks that before proposing anything in a "Krishna, start" cycle, not this file, though this file gives her the current product baseline to reason from.

## Known state / what's NOT done

- No CI/CD, no Docker, no cloud deployment — local dev run only (`docs/deployment-guide.md`).
- `docs/luxury-redesign-requirements.md` is superseded (see above) — don't implement from it.
- Authenticated portal UI has not received the dark/glassmorphism treatment — still on original functional styling.
- No requirement has yet gone through the full Krishna → phase-gate → PR → merge cycle end to end as a live test of the new process (the process itself was just set up). The next "Krishna, start" cycle is the first real test of the whole pipeline including the batch model, sequential task execution, communication logging, and the git workflow.

## Changelog

Newest first. Keep entries short — a sentence or two, dated, what changed and by whom (or "user-directed" if done in direct conversation rather than via an agent invocation).

- **2026-07-20** — Krishna's cycle changed from "1 requirement per cycle" to "minimum 10 requirements per cycle, run as a batch." Phases 1–5 now run once across the whole batch instead of once per requirement; Phase 6 onward executes the resulting task list strictly one task at a time (never in parallel), so real handoffs happen. New `communication/` folder: one timestamped file per cycle, every participating agent appends its before/during/after reports there in order. All 8 agent definitions and `docs/agent-collaboration-protocol.md` updated accordingly.
- **2026-07-20** — GitHub repo created (`akhilMotakatla/green-valley-hospital`), git/PR workflow established (Chintu + Sagar branches, Sagar sole merge gatekeeper). Agent team expanded: Krishna (client) added, Lavanya gained PM/delivery-planning duties, Phase 1 requirement analysis made collaborative (Akhil/Sagar/Lavanya/Sunny), Phase 7 code review (Sagar) added between implementation and QA. This memory system (`docs/project-status.md`, this file) established.
- **2026-07-20** — Dark cinematic + glassmorphism redesign of the entire public site (superseding the light teal/gold "luxury" theme). Full-screen hero rebuilt in `MosaicHero.tsx`. Fixed a real mobile overflow bug (hero CTA button clipped under a fixed-height card) found during browser verification.
- **2026-07-20** — Seed data expanded from 4 to 10 departments, 4 to 10 doctors, 3 to 8 blog articles (user-directed, "more content, screen filled up"). Fixed a hard-coded `.limit(4)` cap in `GET /api/public/home` that was the real bottleneck. Corrected several department images that were visually mismatched to their labels in the original doc (e.g. "pediatrics" pointed to a brain model photo, "ophthalmology" pointed to a beach photo).
- **2026-07-20** — Real photography downloaded and swapped in across the public site, replacing placeholder SVGs that were mislabeled `.jpg` (browsers silently failed to render them). Hero content centered per user direction.
- **Earlier** — Original project build (roles, public site, billing specialist role, performance/scale requirements for 4,000+ patients, email notifications) — see `docs/requirements.md` and `docs/qa-report*.md` for full detail if needed.

# Krishna's Daily Requirements Log

Krishna reads this before proposing anything new — the point is to never raise a requirement that's a rerun of one already logged here, and to make sure a "new" requirement is a genuinely different, measurable improvement over anything similar already listed. Every "Krishna, start" cycle appends one dated entry in the format below. Ad-hoc requirements raised outside the daily cycle get logged too, marked "(ad hoc)".

Entries below predate Krishna's formal daily-cycle process — they're backfilled from direct user requests so Krishna starts with real history instead of a blank slate. They don't follow the full Requirement Title/Business Problem/etc. format since they weren't originally raised by Krishna, but the "don't repeat this" function is the same.

---

## 2026-07-20 (backfilled, ad hoc — user-directed, not from a "Krishna, start" cycle)

**Area: Visual design system overhaul.** Site moved from a light teal/gold "luxury" theme to a dark, cinematic, glassmorphism theme across the entire public site (full-screen sections, frosted-glass cards, deep charcoal/navy/brown palette, large editorial typography over imagery). Homepage hero rebuilt as a full-screen parallax hero. **Do not re-propose "modernize the visual design" or "add glassmorphism" — it's done.** A legitimate follow-up would be something specific and different, e.g. extending the same treatment to the authenticated portal dashboards (explicitly not yet done), or a specific section that still reads as weak.

## 2026-07-20 (backfilled, ad hoc)

**Area: Content depth / homepage density.** Departments expanded 4→10, doctors 4→10, blog articles 3→8. Root cause fixed: `GET /api/public/home` had a hardcoded `.limit(4)` capping featured departments regardless of how much seed data existed. **Do not re-propose "add more departments/doctors/content" as a generic ask** — if a specific new department or specialist is a genuine business need (e.g. a real market gap), that's a legitimate, different requirement; "the site feels sparse" in general is not, since that's already addressed.

## 2026-07-20 (backfilled, ad hoc)

**Area: Real photography.** Placeholder SVG files mislabeled `.jpg` (silently failed to render) replaced with real, visually-verified photos across hero/about/contact/departments/facility-gallery/blog/doctor sections. **Do not re-propose "add real images" — it's done**, though a specific still-weak image (subject mismatch, low quality) is a legitimate targeted fix, not a repeat.

## 2026-07-20 (backfilled, ad hoc)

**Area: Delivery infrastructure.** Standalone GitHub repo created, branch/PR/merge workflow established (Chintu + Sagar branches, Sagar sole merge gatekeeper), full agent team + five-phase-plus gate process defined (`docs/agent-collaboration-protocol.md`). Not a product requirement in the traditional sense — logged here for completeness so it doesn't get proposed again as "set up version control" or "define a dev process."

---

## Reference: what NOT to repeat, by category

- **UI/visual modernization** — done (dark cinematic + glassmorphism). Only propose visual changes that are specific to a section/page not yet covered, or a genuinely new interaction pattern, not a repeat of "make it look more premium."
- **Content volume** — done (10 departments, 10 doctors, 8 articles). Only propose specific new content tied to a real business reason (new specialty, new campaign), not "add more stuff."
- **Real imagery** — done. Only propose image work for a specific identified gap.
- **Process/infrastructure** — git workflow and agent team structure are set. Only propose changes here if there's a demonstrated process failure, not a preemptive tweak.

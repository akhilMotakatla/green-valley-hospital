# Green Valley Hospital — Frontend Design Document

Status: Draft v1.0 (covers Section 6 Visual & UI Enhancement Requirements)
Owner: Solution Architect (Sagar)
Consumers: Frontend Developer (Chintu — primary implementer), Backend Developer (Pavan — backend changes noted inline)
Companion docs: `docs/api-spec.md` (endpoint contract), `db/schema.sql` (DDL), `docs/architecture.md` (system overview)

---

## 1. Scope of This Document

This document translates `requirements.md` Section 6 into concrete, code-ready decisions. It does not contain application code — it specifies component boundaries, CSS token values, image asset contracts, layout strategy, responsive rules, and architectural decisions that Chintu and Pavan must follow exactly so the two layers stay aligned.

---

## 2. CSS Design Tokens (`:root` in `src/frontend/src/index.css`)

Add or replace the following CSS custom properties in the `:root` block. Existing variable names are preserved where already present; new names are additive.

```css
:root {
  /* Primary brand — warmer teal */
  --color-primary:        #0e8a7a;
  --color-primary-dark:   #096b5d;
  --color-primary-light:  #e6f5f2;

  /* Accent — emergency numbers, primary CTA buttons on public marketing pages ONLY */
  --color-accent:         #e05c2a;
  --color-accent-light:   #fdf0eb;

  /* Neutrals */
  --color-bg:             #f4f7f6;
  --color-surface:        #ffffff;
  --color-surface-alt:    #f0f5f3;
  --color-border:         #d8e3e0;
  --color-border-dark:    #b3c8c2;

  /* Text */
  --color-text:           #1a2422;
  --color-text-muted:     #536560;
  --color-text-light:     #8fa8a2;

  /* Semantic */
  --color-danger:         #c0392b;
  --color-warn:           #b7791f;
  --color-ok:             #1e8e5a;
  --color-info:           #1f5aa8;

  /* Elevation */
  --shadow-sm:  0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:  0 4px 12px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06);
  --shadow-lg:  0 10px 28px rgba(0,0,0,0.12), 0 4px 10px rgba(0,0,0,0.06);

  /* Border radii */
  --radius-sm:  6px;
  --radius-md:  10px;
  --radius-lg:  16px;
  --radius-xl:  24px;

  /* Layout */
  --content-max-width: 1200px;

  /* Typography */
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}
```

### Heading scale (global in `index.css`)

```css
h1 { font-size: 2rem;     font-weight: 700; line-height: 1.2; letter-spacing: -0.02em; color: var(--color-text); }
h2 { font-size: 1.5rem;   font-weight: 700; line-height: 1.3; color: var(--color-text); }
h3 { font-size: 1.125rem; font-weight: 600; color: var(--color-text); }
body { font-size: 1rem; line-height: 1.6; }
.text-sm { font-size: 0.875rem; line-height: 1.5; }
```

Remove any existing global rule that applies `--color-primary-dark` to `h1, h2, h3`. Heading color on dark/hero sections is overridden at the component level with `color: #fff`.

### Button base updates

```css
.btn {
  font-weight: 600;
  font-size: 0.9375rem;   /* 15px */
  border-radius: var(--radius-md);
  padding: 0.625rem 1.375rem;
}
```

### `.public-main` max-width update

```css
.public-main {
  max-width: var(--content-max-width); /* 1200px, was 1100px */
  margin: 0 auto;
  padding: 0 1rem;
}
```

---

## 3. Typography / Font Loading

In `src/frontend/index.html`, inside `<head>`, add before existing `<link>` tags:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

---

## 4. Icon Library

Install: `npm install lucide-react` (one-time; add to `package.json` under `dependencies`).

Usage pattern throughout the app:

```tsx
import { Heart, CalendarPlus } from 'lucide-react';
// Inline usage
<Heart size={20} />
```

Icon-to-context size rules:
- Navigation items (public nav, sidebar): `size={18}`
- Stat/feature cards: `size={28}` to `size={36}`
- Doctor cards, department cards: `size={20}` to `size={24}`
- Empty state illustrations: `size={80}`
- Page error: `size={32}`
- Back-to-top button: `size={20}`

Full icon assignment table: see `requirements.md` §6.3, table VI-ICON-2. Chintu must not deviate from that table — it is the single source of truth for icon selection.

---

## 5. Component Hierarchy

Below is the full component tree reflecting both existing components and all new/modified components required by Section 6. New components are marked **[NEW]**; modified existing components are marked **[MOD]**.

```
src/frontend/src/
├── index.html                         [MOD] add Google Fonts link tags
├── main.tsx
├── App.tsx
├── index.css                          [MOD] add tokens, heading scale, btn base
│
├── components/
│   ├── Logo.tsx                       [NEW] SVG logo mark + text, two variants: default (teal) and white
│   ├── SkeletonBlock.tsx              [NEW] animated shimmer placeholder bars
│   ├── PageError.tsx                  [NEW] error card with AlertCircle icon + retry button
│   ├── BackToTopButton.tsx            [NEW] floating scroll-to-top, appears after 400px scroll
│   ├── StatusBadge.tsx                [MOD] add inline Lucide icon per status value
│   └── Pager.tsx                      (unchanged)
│
├── layouts/
│   ├── PublicLayout.tsx               [MOD] emergency strip + Logo + hamburger menu + 4-col footer
│   └── AppShell.tsx                   [MOD] Logo (white variant) + icons on nav items + user info block + topbar improvements
│
└── pages/
    ├── public/
    │   ├── HomePage.tsx               [MOD] hero, stats band, Why Choose Us, Featured Departments, Meet Our Specialists, Testimonials, Recent Blog Posts
    │   ├── AboutPage.tsx              [MOD] page hero, mission/vision/values cards, facility gallery, accreditations strip, history timeline
    │   ├── DepartmentsPage.tsx        [MOD] page hero, search filter input, redesigned cards
    │   ├── DepartmentDoctorsPage.tsx  [MOD] department header banner, redesigned doctor cards
    │   ├── DoctorProfilePage.tsx      [MOD] two-column layout with photo, Book CTA strip
    │   ├── ContactPage.tsx            [MOD] split two-column layout, info cards, map placeholder, styled form
    │   ├── BlogListPage.tsx           [MOD] page hero, redesigned article cards
    │   ├── BlogArticlePage.tsx        [MOD] full-width header image, meta row, constrained body, back link
    │   ├── LoginPage.tsx              [MOD] split-screen layout with panel image
    │   └── SignupPage.tsx             [MOD] split-screen layout, info banner
    │
    ├── admin/
    │   ├── AdminDashboardPage.tsx     [MOD] stat card icons, color theming, quick-action buttons
    │   └── (other admin pages)        [MOD] tables: zebra striping, sticky header, hover; SkeletonBlock; PageError
    │
    ├── patient/
    │   ├── PatientAppointmentsPage.tsx [MOD] greeting card, empty state
    │   └── (other patient pages)       [MOD] empty states, SkeletonBlock, PageError
    │
    └── (doctor, staff, lab pages)      [MOD] SkeletonBlock, PageError, icon badges in tables
```

---

## 6. New Component Specifications

### 6.1 `Logo.tsx`

**Path:** `src/frontend/src/components/Logo.tsx`

Props:
```ts
interface LogoProps {
  variant?: 'default' | 'white';  // 'default' = teal icon + dark text; 'white' = white icon + white text
  size?: number;                   // icon mark height in px, default 36
}
```

Structure:
- An inline SVG: a circle filled with `--color-primary` (or `#fff` in white variant) containing a white (or `--color-primary`) plus/cross symbol.
- Followed by a `<span>` with two lines: "Green Valley" (font-weight 700, 1rem) and "Hospital" (font-weight 400, 0.75rem), stacked via `display: flex; flex-direction: column`.
- Container: `display: flex; align-items: center; gap: 0.5rem`.

Usage locations:
- `PublicLayout.tsx` navbar — `variant="default"`
- `AppShell.tsx` sidebar — `variant="white"`
- `LoginPage.tsx` and `SignupPage.tsx` inside panel or above mobile form — `variant="white"` on panel image, `variant="default"` on mobile

---

### 6.2 `SkeletonBlock.tsx`

**Path:** `src/frontend/src/components/SkeletonBlock.tsx`

Props:
```ts
interface SkeletonBlockProps {
  lines?: number;       // default 3
  widths?: string[];    // e.g. ['80%', '60%', '90%']; cycles if lines > widths.length
}
```

Structure: a `<div>` containing `lines` number of `<div>` elements, each with a shimmer animation. The shimmer uses `background: linear-gradient(90deg, var(--color-surface-alt) 25%, var(--color-border) 50%, var(--color-surface-alt) 75%)` with `background-size: 200% 100%` and a `@keyframes shimmer` that animates `background-position` from `200% 0` to `-200% 0` over 1.5 s infinite.

Replace every instance of `<p className="muted">Loading…</p>` in the codebase with `<SkeletonBlock />`.

---

### 6.3 `PageError.tsx`

**Path:** `src/frontend/src/components/PageError.tsx`

Props:
```ts
interface PageErrorProps {
  message: string;
  onRetry?: () => void;  // if provided, shows "Try again" button
}
```

Structure: a centered `<div>` with `AlertCircle` icon (32px, `--color-danger`), the message text, and optionally a `<button>` that calls `onRetry`. Styled as a card (white, `--shadow-sm`, `--radius-lg`, 32px padding, `text-align: center`).

Replace every instance of `<p className="error-text">{error}</p>` at page level with `<PageError message={error} onRetry={refetch} />`.

---

### 6.4 `BackToTopButton.tsx`

**Path:** `src/frontend/src/components/BackToTopButton.tsx`

No props. Internal behavior:
- `useState(false)` for visibility.
- `useEffect` adds a `scroll` event listener; sets visible `true` when `window.scrollY > 400`.
- On click: `window.scrollTo({ top: 0, behavior: 'smooth' })`.
- Renders a `<button>` in the bottom-right corner: `position: fixed; bottom: 24px; right: 24px; z-index: 50`. Size 44x44px, border-radius 50%, background `--color-primary`, white `ChevronUp` icon (20px). `opacity: 0; pointer-events: none` when not visible; transitions via CSS `opacity 200ms ease`.

Mount this component in: `AboutPage.tsx`, `DepartmentDoctorsPage.tsx`, `BlogArticlePage.tsx`, and any other page that can be taller than two viewport heights.

---

## 7. Layout Architecture Decisions

### 7.1 Full-bleed sections and `.public-main`

The current `PublicLayout.tsx` wraps all page content inside `<main className="public-main">`, which constrains to `max-width: 1200px`. Hero banners, the stats band, and testimonials sections must span full viewport width — they must break out of this constraint.

**Chosen approach: render full-bleed sections as siblings to `.public-main`, not inside it.**

This means `PublicLayout.tsx` changes from:

```tsx
// BEFORE
<main className="public-main">
  <Outlet />
</main>
```

to:

```tsx
// AFTER — Outlet renders the page; each page is responsible for its own full-bleed vs constrained sections
<main className="page-root">
  <Outlet />
</main>
```

And `.page-root` has no max-width or padding — it is `width: 100%`. Each page component manages its own layout:

- Full-bleed sections (hero banners, stats band, testimonial band): `width: 100%; background: ...; padding: 64px 1rem`.
- Constrained content sections: wrap content in `<div className="container">` which applies `max-width: var(--content-max-width); margin: 0 auto; padding: 0 1rem`.

**Implementation note for Chintu:** Do not use the `margin-left: calc(-50vw + 50%)` negative-margin trick inside `.public-main` — it causes horizontal scrollbar issues on some browsers. The sibling approach above is cleaner and is the required implementation.

The footer in `PublicLayout.tsx` stays as a sibling to `<main className="page-root">` — it is already full-width.

The emergency strip and `<header>` navbar also stay at the `<div className="site">` level.

---

### 7.2 PublicLayout.tsx restructure summary

The updated `PublicLayout.tsx` renders this DOM tree:

```
<div className="site">
  <div className="emergency-strip">          ← NEW: 36px tall, --color-primary-dark bg
    PhoneCall icon + "Emergency: +1 (555) 000-9999  |  Open 24 hours, 7 days a week"
  </div>
  <header className="public-nav">            ← MOD: Logo component, sticky shadow on scroll
    <Logo />
    <nav>…NavLinks…</nav>
    <div className="nav-auth">
      Login (btn-outline) | Book Appointment (btn-accent)
    </div>
    <button className="hamburger">…</button>  ← NEW: visible only < 768px
    <div className="mobile-menu">…</div>      ← NEW: toggle dropdown
  </header>
  <main className="page-root">              ← MOD: no max-width constraint
    <Outlet />
  </main>
  <footer className="public-footer">        ← MOD: 4-column layout
    …
  </footer>
</div>
```

---

### 7.3 AppShell.tsx restructure summary

The updated `AppShell.tsx`:
- Replaces plain text "Green Valley" brand with `<Logo variant="white" size={32} />`.
- Removes the `<p className="role-badge">` element (role now shown in the user info block at the bottom).
- Each `NavLink` in `sidebar-nav` renders its Lucide icon (from the mapping in `requirements.md` §6.3) to the left of the label text, via `display: flex; align-items: center; gap: 0.625rem`.
- A new user info block at the very bottom of the sidebar (`margin-top: auto`): avatar circle with initials, full name, role text, logout icon button.
- The topbar replaces `{user?.email}` with the current page title (passed as prop or derived from `useMatch`) on the left, and user name + role badge + Bell icon + logout on the right.

The `navByRole` map in `AppShell.tsx` needs to be extended with icon names per role. Since this is a design doc (not implementation code), Chintu derives the icon for each item from the table in `requirements.md` §6.3.

---

## 8. Page-by-Page Design Specifications

### 8.1 HomePage.tsx

The home page renders the following sections in order, all direct children of the page root (no shared container wrapper):

| Order | Section | Full-bleed? | Background |
|---|---|---|---|
| 1 | Hero | Yes | `/images/hero-banner.jpg` + gradient overlay |
| 2 | Stats band | Yes | `--color-primary-light` |
| 3 | Why Choose Us | No (constrained) | `--color-surface` |
| 4 | Featured Departments | No (constrained) | `--color-surface` |
| 5 | Meet Our Specialists | No (constrained) | `--color-bg` |
| 6 | Testimonials | Yes | `--color-surface-alt` |
| 7 | Recent Blog Posts | No (constrained) | `--color-surface` |

**Hero section details:**
- Outer: `position: relative; width: 100%; min-height: 600px; max-height: 700px; overflow: hidden`.
- `<img src="/images/hero-banner.jpg" alt="" />` with `position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover`.
- Overlay `<div>` with `position: absolute; inset: 0; background: linear-gradient(to right, rgba(9,107,93,0.88) 0%, rgba(9,107,93,0.55) 60%, rgba(9,107,93,0.15) 100%)`.
- Content `<div>` with `position: relative; z-index: 1` — contains hospital name (h1, white, 2.5rem, font-weight 800), tagline (p, white, 1.125rem), two buttons side by side.
- CTA buttons: "Book an Appointment" (`--color-accent` bg, white text, height 48px) and "Explore Departments" (white outline, white text, height 48px).
- On desktop: content positioned left-aligned with 10% left padding, text-align left.
- On mobile: text centered, buttons stacked full-width.

**Stats band counter animation:**
- Use `IntersectionObserver` on the stats band `<div>` with `threshold: 0.3`.
- On first intersection, start a `requestAnimationFrame` loop for each counter: `Math.ceil(elapsed / duration * target)` where `duration = 1500` ms.
- Store "animated" state in a `useRef<boolean>` — do NOT use `useState` for this flag (avoids a re-render on subsequent intersections). The observer disconnects after first trigger.
- Displayed values contain suffixes: `15,000+`, `80+`, `25`, `18` — animate the numeric part only; the `+` and `,` are static in the label string.

**Section headers (Why Choose Us, Featured Departments, etc.):**
The centered section header with colored underline pattern:
```tsx
<div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
  <h2>Our Departments</h2>
  <div style={{ width: 48, height: 3, background: 'var(--color-primary)', margin: '0.5rem auto 0' }} />
</div>
```

**Meet Our Specialists — data source:**
Data comes from `content.featured_departments[].first_doctor` in the home API response. If `first_doctor` is null for a department, that department is skipped (no empty card rendered). If all `first_doctor` fields are null, the entire section is hidden. Do not make a separate API call.

---

### 8.2 AboutPage.tsx

Page sections in order:

| Order | Section | Full-bleed? |
|---|---|---|
| 1 | Page hero banner | Yes |
| 2 | Mission / Vision / Values cards | No |
| 3 | Facility gallery | No |
| 4 | Accreditations strip | No |
| 5 | History timeline | No |
| 6 | `<BackToTopButton />` | Floating |

**History timeline alignment:**
- On desktop (≥ 1024px): alternating left/right cards. Items at even index (0, 2, 4) have content left of the center line, odd index right. Year circle is centered on the line.
- On mobile (< 1024px): all cards right-aligned (content to the right of the vertical line). The line is at ~32px from the left edge.
- Data: 4 static milestone entries + one dynamic entry from `content.history` (label: "Present").

---

### 8.3 DepartmentsPage.tsx

- Search input: controlled `useState<string>('')`. Filter applied with `department.name.toLowerCase().includes(q) || department.description?.toLowerCase().includes(q)`. The `Search` icon (Lucide) is rendered via `position: absolute` inside the input's wrapper — input has `padding-left: 2.5rem` to clear the icon.
- Department card image: `<img src={`/images/dept-${slug}.jpg`} alt="" onError={handleImageError} />`. The `handleImageError` handler replaces the broken `<img>` with the fallback `<div>` (gradient circle + icon) using a `useState<boolean>` error flag per card.
- The `slug` is derived client-side: `department.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')`.

---

### 8.4 DepartmentDoctorsPage.tsx

- Data comes from `GET /api/public/departments/{department_id}/doctors` — now returns `{department, items}`.
- The `department_id` param from `useParams()` provides the id.
- Background image for header banner: `/images/dept-{slug}.jpg` where slug is derived the same way as in DepartmentsPage. Falls back to `--color-primary-dark` solid if image missing (same `onError` approach).
- Doctor card photo: if `doctor.profile_photo_path` is set, render `<img src={doctor.profile_photo_path} alt={doctor.full_name} style={{ borderRadius: '50%', width: 90, height: 90, objectFit: 'cover' }} />`. If null, render a gradient `<div>` with the doctor's initials computed as `full_name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()`.

---

### 8.5 DoctorProfilePage.tsx (public)

- Two-column layout: `display: grid; grid-template-columns: 30% 70%; gap: 2rem` on desktop. Single column (photo above content) on mobile.
- Photo: 200px circle. Same profile_photo_path / initials fallback as in department doctors page.
- "Book an Appointment" CTA strip: a `<div>` below the two-column section, full-width, `--color-primary-light` background, `--radius-lg`, 28px padding, flexbox row (text left, button right on desktop; stacked on mobile).
- The CTA button links to `/signup` if `!isAuthenticated`, or to `/patient/book?doctor_id={doctor_id}` if the current user's role is "Patient".

---

### 8.6 ContactPage.tsx

- Two-column grid: `display: grid; grid-template-columns: 1fr 1fr; gap: 2.5rem` on desktop (≥ 1024px); `grid-template-columns: 1fr` on mobile.
- Map placeholder: a `<div style={{ position: 'relative' }}>` containing `<img src="/images/map-placeholder.jpg" />` with a child `<div>` absolutely positioned at `bottom: 0; left: 0` with `background: rgba(0,0,0,0.6); color: #fff; font-size: 0.75rem; padding: 4px 8px`.
- Form success state: replace form JSX with the success card JSX when `submitted === true` (controlled by `useState`).

---

### 8.7 BlogListPage.tsx and BlogArticlePage.tsx

**BlogListPage:**
- Page hero: same full-bleed pattern, `/images/blog-hero.jpg`, 240px height.
- Cards use CSS `-webkit-line-clamp` for title (2 lines) and summary (3 lines). These properties require the Webkit prefix and are widely supported — no JS truncation needed.

**BlogArticlePage:**
- Article header: `position: relative; max-height: 400px; overflow: hidden`. Cover image or gradient fallback. Title overlaid at bottom-left via `position: absolute; bottom: 0; left: 0; padding: 1.5rem; color: #fff` with a local gradient `background: linear-gradient(to top, rgba(0,0,0,0.7), transparent)`.
- Read time calculation: `Math.ceil(body.split(/\s+/).length / 200)` — split on whitespace sequence, not single space, for accuracy.
- Body constraint: `<div style={{ maxWidth: 720, margin: '0 auto', fontSize: '1.0625rem', lineHeight: 1.75 }}>`.
- `<BackToTopButton />` mounted in this page.

---

### 8.8 LoginPage.tsx and SignupPage.tsx

- Split-screen wrapper: `display: flex; min-height: 100vh`. Left panel `width: 45%; position: relative; overflow: hidden` — hidden below 768px via `display: none`. Right panel `flex: 1; display: flex; align-items: center; justify-content: center`.
- Left panel contains `<img src="/images/auth-panel.jpg" alt="" style={{ objectFit: 'cover', width: '100%', height: '100%' }} />` and a `<div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0.1) 60%)' }} />`. At the bottom of the panel: `<Logo variant="white" />` + tagline in white.
- Right panel form: `max-width: 400px; width: 100%; padding: 2rem`.
- On mobile (< 768px): left panel `display: none`; right panel is `width: 100%; padding: 1.5rem`. The `<Logo variant="default" />` renders above the form title in mobile.
- Password field: `position: relative`. The Eye/EyeOff toggle button is `position: absolute; right: 12px; top: 50%; transform: translateY(-50%)`. Input has `padding-right: 2.75rem`.

---

### 8.9 Admin Dashboard

Stat cards: each receives a `border-left: 4px solid <color>` where the color per card:
- Patient count: `--color-primary`
- Doctor count: `--color-info`
- Appointments today: `--color-warn`
- Pending lab orders: `--color-accent`

The icon for each stat renders inside a 64px circle (`width: 64px; height: 64px; border-radius: 50%; background: var(--color-primary-light); display: flex; align-items: center; justify-content: center`).

---

### 8.10 Patient Portal

**Greeting card in PatientAppointmentsPage:**
Time-of-day logic: `new Date().getHours()` — `< 12` → "Good morning", `< 17` → "Good afternoon", else → "Good evening". The patient's full name comes from `GET /api/patients/me` (already called on this page).

**Empty state pattern:**
```tsx
<div className="empty-state">
  <IconComponent size={80} color="var(--color-text-light)" />
  <h3>No appointments yet</h3>
  <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>…description…</p>
  {/* optional CTA */}
  <Link to="/patient/book" className="btn btn-primary">Book your first appointment</Link>
</div>
```

---

## 9. Shared Component Pattern Changes

### 9.1 StatusBadge.tsx

Add a `size={12}` Lucide icon before the text:
- `"Completed"` → `<Check size={12} />`
- `"Scheduled"` / `"Pending"` → `<Clock size={12} />`
- `"Cancelled"` / `"NoShow"` → `<X size={12} />`
- `"InProgress"` → `<Loader size={12} />`

Container: `display: inline-flex; align-items: center; gap: 4px`.

### 9.2 Table styling (applies to all authenticated page tables)

Add to `index.css` or a shared table class:

```css
.data-table tbody tr:nth-child(even) td { background: var(--color-surface-alt); }
.data-table tbody tr:hover td           { background: var(--color-primary-light); }
.data-table thead th {
  position: sticky; top: 0; z-index: 1;
  background: var(--color-surface);
  border-bottom: 2px solid var(--color-border);
}
```

### 9.3 Card hover lift (clickable cards only)

```css
a .card,
.card-link {
  transition: transform 200ms ease, box-shadow 200ms ease;
}
a .card:hover,
.card-link:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
```

---

## 10. Responsive Breakpoints Strategy

All layout changes use a mobile-first approach: base CSS targets mobile (single column, stacked), then `@media (min-width: ...)` progressively enhances.

| Breakpoint | CSS min-width | Description |
|---|---|---|
| Mobile | (default) | Single column, hamburger nav, stacked cards, full-width buttons |
| Tablet | 640px | 2-column card grids begin, department cards 2-up |
| Desktop | 1024px | 3-column grids, side-by-side panels (About, Contact, Auth), sidebar always visible |
| Wide | 1280px | Container capped at `--content-max-width: 1200px` centered |

**Grid utility (in `index.css`):**

```css
.grid-1 { display: grid; grid-template-columns: 1fr; gap: 1.5rem; }
@media (min-width: 640px)  { .grid-2-up { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .grid-3-up { grid-template-columns: repeat(3, 1fr); } }
```

Chintu should apply these utility classes to card grids where possible rather than writing per-page media queries for the same pattern.

**Hamburger menu (public nav):**
- `<button className="hamburger">` is `display: none` at ≥ 768px.
- Below 768px: nav link list and auth buttons have `display: none` by default; get `display: flex; flex-direction: column` when parent `<header>` has class `menu-open`.
- Mobile menu drops down via `max-height: 0; overflow: hidden` → `max-height: 500px` transition (200ms ease). Class toggled by `hamburger` button click. Closed by clicking outside (via a `useEffect` `mousedown` listener on `document`).

---

## 11. Image Asset Contract

All images live in `src/frontend/public/images/`. The frontend dev server serves `public/` at the root, so `<img src="/images/hero-banner.jpg" />` resolves correctly in both dev and prod Vite builds.

**Chintu's responsibility:** source and place all images from Unsplash/Pexels before writing component code. Compress to WebP (max 300 KB) or JPEG fallback.

**Broken image fallback pattern (Chintu must implement for every `<img>` that can fail):**

```tsx
const [imgError, setImgError] = useState(false);

{imgError || !src
  ? <FallbackComponent />
  : <img src={src} alt={alt} onError={() => setImgError(true)} />
}
```

Full image file list:

| Filename | Dimensions | Used in | Subject |
|---|---|---|---|
| `hero-banner.jpg` | 1600 x 700 | Home hero | Modern hospital exterior, daytime |
| `about-hero.jpg` | 1400 x 400 | About page hero | Hospital lobby interior, bright |
| `departments-hero.jpg` | 1400 x 400 | Departments page hero | Multi-specialist medical team |
| `blog-hero.jpg` | 1400 x 400 | Blog list page hero | Doctor reading tablet / research setting |
| `auth-panel.jpg` | 800 x 1000 | Login + Signup left panel | Friendly doctor / reception desk, warm lighting |
| `map-placeholder.jpg` | 800 x 300 | Contact page map section | City map with pin marker |
| `facility-icu.jpg` | 600 x 300 | About facilities gallery | ICU patient room |
| `facility-er.jpg` | 600 x 300 | About facilities gallery | Emergency room corridor |
| `facility-lab.jpg` | 600 x 300 | About facilities gallery | Clinical laboratory with technician |
| `facility-maternity.jpg` | 600 x 300 | About facilities gallery | Maternity ward, newborn |
| `facility-outpatient.jpg` | 600 x 300 | About facilities gallery | Hospital waiting area |
| `facility-pharmacy.jpg` | 600 x 300 | About facilities gallery | Hospital pharmacy counter |
| `dept-cardiology.jpg` | 600 x 250 | Departments page card, dept-doctors banner | Heart monitor / ECG |
| `dept-pediatrics.jpg` | 600 x 250 | Departments page card, dept-doctors banner | Pediatrician with child |
| `dept-orthopedics.jpg` | 600 x 250 | Departments page card, dept-doctors banner | X-ray bone |
| `dept-neurology.jpg` | 600 x 250 | Departments page card, dept-doctors banner | Brain scan, neurologist |
| `dept-oncology.jpg` | 600 x 250 | Departments page card, dept-doctors banner | Cancer treatment |
| `dept-radiology.jpg` | 600 x 250 | Departments page card, dept-doctors banner | MRI scanner |
| `dept-emergency.jpg` | 600 x 250 | Departments page card, dept-doctors banner | Emergency ambulance bay |
| `dept-ophthalmology.jpg` | 600 x 250 | Departments page card, dept-doctors banner | Eye examination |
| `dept-gynecology.jpg` | 600 x 250 | Departments page card, dept-doctors banner | Women's health consultation |
| `dept-dermatology.jpg` | 600 x 250 | Departments page card, dept-doctors banner | Dermatology consultation |
| `dept-default.jpg` | 600 x 250 | Any department without a specific image | Stethoscope / generic medical background |

Department image slug derivation (implemented client-side, not from API):
```ts
const deptSlug = (name: string) =>
  name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
// "Cardiology" → "cardiology" → "/images/dept-cardiology.jpg"
// "Women's Health" → "womens-health" → "/images/dept-womens-health.jpg"
```

If the resulting filename does not exist in the image list above, the `onError` fallback triggers the gradient+icon placeholder.

---

## 12. Footer Architecture

The updated `PublicLayout.tsx` footer renders four columns using CSS grid:

```
grid-template-columns: 2fr 1fr 1fr 1.5fr  (desktop ≥ 1024px)
grid-template-columns: 1fr 1fr            (tablet ≥ 640px)
grid-template-columns: 1fr               (mobile)
```

Column 3 (Services — top 6 department links) is rendered from a **static hardcoded list** in the `PublicLayout.tsx` file, not from an API call. The footer is a layout component that must render without data fetching. The static list:
```ts
const FOOTER_DEPARTMENTS = [
  { name: 'Cardiology',    id: 1 },
  { name: 'Pediatrics',    id: 2 },
  { name: 'Orthopedics',   id: 3 },
  { name: 'Neurology',     id: 4 },
  { name: 'Oncology',      id: 5 },
  { name: 'Radiology',     id: 6 },
];
```

**Important:** these IDs are demo placeholders. If the actual seeded department IDs differ, Chintu updates this list once after Pavan seeds the database. This is acceptable because the footer links are marketing copy, not dynamic data.

---

## 13. Accent Color Usage Policy

`--color-accent` (#e05c2a, warm orange-red) is reserved exclusively for:
1. Emergency phone number text in the emergency strip and footer.
2. The "Book Appointment" primary CTA button in the public nav.
3. The "Book an Appointment" CTA button in hero sections and doctor profile.
4. The "Send Message" submit button on the contact form.
5. The left-border accent on the "Pending Lab Orders" admin stat card.
6. Auth form primary submit buttons (Sign In, Create Account).

It must NOT appear on any other UI element. General interactive elements use `--color-primary`.

---

## 14. Animations and Motion

All animations use only CSS transitions and native Web APIs:
- Card hover lift: CSS `transition: transform 200ms ease, box-shadow 200ms ease` — no JS.
- Hamburger menu open/close: CSS `max-height` transition, class toggled by React `useState`.
- Nav scroll shadow: scroll event listener adds/removes `.scrolled` class on `<header>`.
- Stats counter animation: `IntersectionObserver` + `requestAnimationFrame` (plain JS loop in a `useEffect`).
- Skeleton shimmer: CSS `@keyframes` animation.
- Back-to-top button fade: CSS `opacity` transition, visibility toggled by scroll listener.

No Framer Motion, GSAP, or any external animation library may be introduced (requirements.md §6.21).

---

## 15. What Pavan Needs to Build (Backend Checklist)

The following changes are required in the backend before the frontend visual work can be completed end-to-end. All other Section 6 changes are pure frontend.

| # | Change | Endpoint(s) affected | Schema change |
|---|---|---|---|
| 1 | Add `profile_photo_path` to all doctor response schemas | `GET /api/public/departments/{id}/doctors`, `GET /api/public/doctors/{id}`, `GET /api/doctor/me`, `PATCH /api/doctor/me` (accepts it), `GET /api/patients/doctors`, `GET /api/staff/directory` | `doctors.profile_photo_path TEXT` — **already added to `db/schema.sql`** |
| 2 | `GET /api/public/departments/{id}/doctors` returns `{department: {department_id, name, description}, items: [...]}` | `GET /api/public/departments/{id}/doctors` | None — query join only |
| 3 | `GET /api/public/home` includes `recent_articles` (up to 3 Published articles, most recent first) and `featured_departments[].first_doctor` | `GET /api/public/home` | None — query change only |

No other backend changes are needed for Section 6.

---

## 16. Decisions on Open Items

| Item | Decision |
|---|---|
| `GET /public/home` vs `GET /public/blog?limit=3` for recent articles | `GET /public/home` includes `recent_articles` array. Frontend does NOT make a second blog call on the home page. |
| `profile_photo_path` — new field or assumed existing? | New field, explicitly added to `db/schema.sql` via `doctors.profile_photo_path TEXT` column. Field was implied by DOC-1 but not listed in §3.4. Now canonical. |
| Testimonials — database or static? | Static/hardcoded in `HomePage.tsx`. These are marketing copy, not dynamic CMS content. No backend endpoint or database table. |
| Stat band values (15,000+, 80+, 25 yrs, 18 depts) — API or static? | Static/hardcoded in `HomePage.tsx`. These are marketing copy. |
| Footer department links — API or static? | Static hardcoded list in `PublicLayout.tsx`. Footer must render without API calls. IDs updated once after seed. |
| History timeline milestones — static or from API? | 4 milestone entries are static; the "Present" entry is the `content.history` string from `GET /api/public/about`. |
| Accreditations display — how parsed? | Comma-split of `content.accreditations` string: `content.accreditations.split(',').map(s => s.trim())`. Each entry renders as a badge card. |
| Image file format | WebP preferred; JPEG acceptable if WebP encoder not available. Maximum 300 KB per file. |
| `profile_photo_path` value format | A path relative to the static root, e.g. `/images/doctors/dr-john-smith.jpg`. The frontend uses this value directly as the `<img src>` attribute. Pavan's file-serving: Vite already serves `public/` statically — no new endpoint needed. For doctor photo uploads, the path is set manually via Admin/Doctor edit form (plain text input), consistent with VI-IMG-3. |

---

## 17. Section 7 — CSS Conflict Analysis (Scroll Animation Class Names)

Status: Reviewed against `src/frontend/src/index.css` as of the time Section 7 was written.

### 17.1 Conflict Check Results

The following class names are introduced by `requirements.md` §7.2.2 and were checked against every existing class name in `index.css`:

| New class name | Exists in index.css? | Verdict |
|---|---|---|
| `scroll-fade-up` | No | Clear — no conflict |
| `scroll-fade` | No | Clear — no conflict |
| `scroll-slide-left` | No | Clear — no conflict |
| `scroll-slide-right` | No | Clear — no conflict |
| `scroll-scale-in` | No | Clear — no conflict |
| `animated` | No | Clear — no conflict |
| `anim-delay-1` through `anim-delay-6` | No | Clear — no conflict |
| `section-underline` (extension only) | **Yes — already defined** | Additive extension, not a conflict (see §17.2) |

**Note on prompt wording**: The task brief refers to "stagger-1 through stagger-6" but `requirements.md` §7.2.2 defines the actual class names as `anim-delay-1` through `anim-delay-6`. There is no class named `stagger-{n}` in Section 7. The correct names to implement are `anim-delay-1` through `anim-delay-6`. Chintu must use these exact names.

**Note on `section-underline-reveal`**: The task brief also names this class, but it does not appear anywhere in `requirements.md` §7.2.2. The underline animation is applied by adding `animated` to the existing `.section-underline` element — there is no separate `section-underline-reveal` class to add or check. No action needed for this name.

### 17.2 The `section-underline` Extension

`index.css` already defines `.section-underline` as:

```css
.section-underline {
  width: 48px;
  height: 3px;
  background: var(--color-primary);
  margin: 0 auto;
  border-radius: 2px;
}
```

Section 7.2.2 adds these new rules inside the `/* === Scroll Animation Utilities === */` block:

```css
.section-underline {
  transform-origin: left center;
}
.section-underline.animated {
  animation: expandUnderline 0.5s ease forwards;
  animation-delay: 0.15s;
}
```

These are purely additive. The `transform-origin` rule is safe to add: it only matters when a CSS `transform` is applied (which only happens during the animation), so it does not visually change the underline before animation fires. The `.section-underline.animated` modifier is a new compound selector and cannot conflict with anything existing. **No changes to the existing rule set are required.**

### 17.3 One Required Fix: Pre-animation Visibility of `.section-underline`

**Problem identified during review:** The existing `.section-underline` has no `opacity: 0` initial state. The `expandUnderline` keyframe starts from `opacity: 0; transform: scaleX(0)`. Without a matching initial hidden state, the underline is fully visible on page load, then jumps invisible when the animation starts, then expands — causing a visible flash.

**Resolution:** Add the following rule to the `/* === Scroll Animation Utilities === */` block, immediately after the `.section-underline { transform-origin: left center; }` rule:

```css
/* Hide section-underline in animated contexts until the animation fires.
   This selector is safe: .section-underline is only ever placed inside
   .section-header containers (confirmed across HomePage, AboutPage,
   DepartmentsPage). It does not affect underlines outside section-header
   because there are none in the current codebase. */
.section-header .section-underline {
  opacity: 0;
}
```

This must be inside the animation utilities block so it is easy to find and so the `prefers-reduced-motion` override below it (which forces `opacity: 1 !important`) correctly cancels it.

---

## 18. Section 7 — Confirmed CSS Animation Classes

The final canonical list of class names and keyframes for Chintu to add to `index.css` inside the `/* === Scroll Animation Utilities === */` block (place immediately after the `:root` block, before `.emergency-strip`):

### 18.1 Keyframes

```css
/* === Scroll Animation Utilities === */

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-50px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes slideInRight {
  from { opacity: 0; transform: translateX(50px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.94); }
  to   { opacity: 1; transform: scale(1); }
}
@keyframes expandUnderline {
  from { transform: scaleX(0); opacity: 0; }
  to   { transform: scaleX(1); opacity: 1; }
}
```

### 18.2 Base Utility Classes (Elements Start Invisible)

```css
.scroll-fade-up,
.scroll-fade,
.scroll-slide-left,
.scroll-slide-right,
.scroll-scale-in {
  opacity: 0;
}

.scroll-fade-up.animated     { animation: fadeInUp     0.6s ease forwards; }
.scroll-fade.animated        { animation: fadeIn       0.5s ease forwards; }
.scroll-slide-left.animated  { animation: slideInLeft  0.6s ease forwards; }
.scroll-slide-right.animated { animation: slideInRight 0.6s ease forwards; }
.scroll-scale-in.animated    { animation: scaleIn      0.5s ease forwards; }
```

### 18.3 Section Underline Rules (Extension of Existing Class + Conflict Fix)

```css
/* Extension of the existing .section-underline rule */
.section-underline {
  transform-origin: left center;
}

/* Fix: hide underline in animated contexts until expandUnderline fires */
.section-header .section-underline {
  opacity: 0;
}

.section-underline.animated {
  animation: expandUnderline 0.5s ease forwards;
  animation-delay: 0.15s;
}
```

### 18.4 Stagger Delay Helpers (Correct Names: `anim-delay-{n}`)

```css
.anim-delay-1 { animation-delay: 0.1s; }
.anim-delay-2 { animation-delay: 0.2s; }
.anim-delay-3 { animation-delay: 0.3s; }
.anim-delay-4 { animation-delay: 0.4s; }
.anim-delay-5 { animation-delay: 0.5s; }
.anim-delay-6 { animation-delay: 0.6s; }
```

### 18.5 Reduced-Motion Override (Mandatory, Must Be Last in the Block)

```css
@media (prefers-reduced-motion: reduce) {
  .scroll-fade-up,
  .scroll-fade,
  .scroll-slide-left,
  .scroll-slide-right,
  .scroll-scale-in,
  .section-underline,
  .section-header .section-underline {
    opacity: 1 !important;
    transform: none !important;
    animation: none !important;
  }
}
```

The `section-header .section-underline` selector is added to the reduced-motion block to cancel the `opacity: 0` fix from §18.3.

---

## 19. Section 7 — SectionHeader Component Specification (Confirmed)

### 19.1 Pattern Review

All three reviewed pages use the same pattern consistently:

**`HomePage.tsx`** (multiple instances):
```tsx
<div className="section-header">
  <h2>Why Choose Us</h2>
  <div className="section-underline" />
</div>
```

**`AboutPage.tsx`** (multiple instances):
```tsx
<div className="section-header">
  <h2>Our Purpose</h2>
  <div className="section-underline" />
</div>
```

**`DepartmentsPage.tsx`**: No explicit section-header in the current code (the departments page has a hero and search input only, with the card grid directly below). The SectionHeader component will be used when scroll animations are added.

The existing CSS for `.section-header` and `.section-underline` is already correctly defined in `index.css` (lines 481–496). The component is a safe, exact wrap of this pattern.

### 19.2 Confirmed Component Spec

**Path:** `src/frontend/src/components/SectionHeader.tsx`

**Props:**
```ts
interface SectionHeaderProps {
  title: string;
  subtitle?: string;
}
```

**Behavior:**
- Renders `<div className="section-header">` as the container.
- Inside: `<h2 className="scroll-fade-up">{title}</h2>` followed by `<div className="section-underline" />`.
- If `subtitle` is provided, renders `<p className="scroll-fade-up anim-delay-1" style={{ color: 'var(--color-text-muted)', marginTop: '0.75rem' }}>{subtitle}</p>` after the underline div.
- Uses `useSingleScrollReveal` internally. The ref is attached to the outer `<div className="section-header">`.
- When the IntersectionObserver fires: queries the container's children and adds `"animated"` to the `<h2>` (which has `scroll-fade-up`) and to the `.section-underline` div. The h2 and underline can be targeted by `containerRef.current.querySelector('h2')` and `containerRef.current.querySelector('.section-underline')`. If a subtitle `<p>` is present, also add `"animated"` to it.
- The observer disconnects after firing once (handled inside `useSingleScrollReveal`).

**Usage (replaces every manual `div.section-header` block):**
```tsx
<SectionHeader title="Our Departments" />
// or with subtitle:
<SectionHeader title="Our Departments" subtitle="World-class care across 18 specialties" />
```

**Migration note for Chintu:** Every existing `<div className="section-header">` / `<h2>` / `<div className="section-underline" />` group in `HomePage.tsx`, `AboutPage.tsx`, `DepartmentsPage.tsx`, and other public pages must be replaced with `<SectionHeader title="..." />`. The authenticated dashboard pages (admin/doctor/patient/staff/lab) that use the same pattern should also be migrated, but the scroll animation will fire based on viewport intersection — confirm that dashboard section headers are below the fold before adding; if they are above the fold on initial render, use the `setTimeout(300ms)` approach instead.

---

## 20. Section 7 — Parallax Implementation Approach (Confirmed)

### 20.1 Current Hero Structure in `HomePage.tsx`

The hero `<section>` currently (lines 344–437 of `HomePage.tsx`) uses:
- An `<img src="/images/hero-banner.svg" alt="" onError={...} />` element with `position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover` as the background.
- A `heroBgError` state variable with a `setHeroBgError` setter that shows a gradient fallback `<div>` when the image fails to load.
- A gradient overlay `<div>` (unchanged).
- A content `<div>` with `position: relative; z-index: 1` (unchanged).

The section element itself has `position: relative; width: 100%; minHeight: 600; maxHeight: 700; overflow: hidden; display: flex; alignItems: center`.

### 20.2 Compatibility Assessment

The CSS `backgroundImage` parallax approach from §7.2.4 is compatible with the current hero structure. The required changes are:

1. **Remove**: The entire `{!heroBgError ? <img .../> : <div gradient fallback />}` conditional block and the `heroBgError` state declaration.

2. **Add to `<section>` inline style**: `backgroundImage: "url('/images/hero-banner.jpg')"`, `backgroundSize: 'cover'`, `backgroundPosition: 'center top'`, `willChange: 'background-position'`.

3. **Add a CSS fallback color**: Set `backgroundColor: 'var(--color-primary-dark)'` on the section. This ensures that if the image is absent or slow to load, the gradient overlay still shows over the primary dark color. This replaces the previous `onError` fallback mechanism (the `backgroundImage` CSS property has no equivalent of `onError`).

4. **Gradient overlay `<div>` and content `<div>`**: Remain unchanged.

5. **Add `heroRef` and scroll effect**:
   - `const heroRef = useRef<HTMLElement>(null)` — attach to the `<section>` element.
   - Add `useEffect` per §7.2.4 spec: check `window.innerWidth >= 768` and `!window.matchMedia('(prefers-reduced-motion: reduce)').matches` before attaching; use `requestAnimationFrame` throttling; set `heroRef.current.style.backgroundPositionY = \`${window.scrollY * 0.4}px\``; return cleanup `removeEventListener`.

6. **`overflow: hidden` is compatible**: The section's `overflow: hidden` clips the shifted background correctly. No change needed.

7. **`maxHeight: 700` consideration**: With `backgroundSize: 'cover'` on a 1600x700px image in a 600–700px tall container, the browser scales the image to cover the element's width. The resulting image height at desktop viewport widths will typically exceed 700px (because the image is scaled to fill the full width), providing vertical headroom for the parallax shift of up to ~120px (scrollY of 300 * 0.4). The effect will be visible and smooth at desktop viewports. At narrow viewports, parallax is disabled (`window.innerWidth < 768` check).

### 20.3 Hero Section Background Extension for Fallback

Add `backgroundColor: 'var(--color-primary-dark)'` alongside `backgroundImage` in the section's inline style. This is the sole change to the fallback strategy — no `useState` needed.

```tsx
// AFTER — section opening tag inline style
style={{
  position: 'relative',
  width: '100%',
  minHeight: 600,
  maxHeight: 700,
  overflow: 'hidden',
  display: 'flex',
  alignItems: 'center',
  backgroundColor: 'var(--color-primary-dark)',     // ← fallback color
  backgroundImage: "url('/images/hero-banner.jpg')", // ← replaces <img>
  backgroundSize: 'cover',
  backgroundPosition: 'center top',
  willChange: 'background-position',
}}
```

### 20.4 Image Reference Updates (Section 7.1.4)

The `DeptCardImage` component in both `HomePage.tsx` (line 282) and `DepartmentsPage.tsx` (line 18) currently loads `/images/dept-${deptSlug}.svg`. This must be changed to `.jpg` as part of the Section 7.1 image replacement work. Similarly:

- `AboutPage.tsx` line 12: `FACILITIES` array — all 6 `.svg` filenames → `.jpg`
- `AboutPage.tsx` line 101: `src="/images/about-hero.svg"` → `.jpg`
- `DepartmentsPage.tsx` line 80: `src="/images/departments-hero.svg"` → `.jpg`
- `LoginPage.tsx` / `SignupPage.tsx`: `src="/images/auth-panel.svg"` → `.jpg`
- `ContactPage.tsx`: `src="/images/map-placeholder.svg"` → `.jpg`
- `HomePage.tsx`: hero is switching to `backgroundImage` (no `src` attribute); `DeptCardImage` line 282: `.svg` → `.jpg`

A scoped VS Code find-and-replace of `"/images/` + `.svg"` → `.jpg"` across all `.tsx` files is safe. After the replace, verify no Lucide SVG import strings were accidentally changed — Lucide imports use component names, not string paths, so they are unaffected.

---

## 21. Section 7 — Backend Changes Required

**No backend changes are required for Section 7.** Section 7 covers only:
- Real image file downloads and placement (frontend static assets)
- Scroll animation CSS and hooks (frontend CSS + React hooks)
- Component updates (frontend TypeScript)

All three backend changes listed in §15 above were already requested as part of Section 6. Pavan does not need to do any new work for Section 7. The `profile_photo_path` doctor field (§15, item 1) is the only data field that drives new image rendering in Section 7, and it was already specified in §15.

---

## 22. Handoff Note for Chintu — Section 7 Implementation Order

This is the canonical ordered task list for implementing Section 7. Do these steps in order. Do not skip ahead — steps 1 and 2 must be done before any component work begins.

---

**Step 1 — Download real images (Section 7.1)**

1. Create the subdirectory `src/frontend/public/images/doctors/` if it does not exist.
2. Save `src/frontend/public/images/download-images.ps1` using the exact script content in `requirements.md` §7.1.7.
3. Open a PowerShell terminal, `cd` to `src/frontend/public/images/`, and run `.\download-images.ps1`.
4. After the script completes, open every downloaded file in Windows Photos. Any file that displays as a colored rectangle with text is an SVG placeholder (the CDN URL failed silently). For those files, open the search fallback URL from `requirements.md` §7.1.6, find a suitable photo, right-click its download button, copy the image address, then re-run the `Invoke-WebRequest` line for that file with the new URL.
5. Check the duplicate pairs listed in `requirements.md` §7.1.8: `dept-neurology.jpg` vs `facility-er.jpg`, and `dept-oncology.jpg` vs `dept-gynecology.jpg`. If any pair is identical, download a distinct photo for the department image using the search URL.
6. Verify every file is under 500 KB. If any file exceeds 500 KB, compress it at Squoosh (https://squoosh.app) using MozJPEG quality 75–80.

---

**Step 2 — Update `.svg` → `.jpg` references in source files (Section 7.1.4)**

1. In VS Code: Edit > Find in Files, search `"/images/` followed by `.svg"` across `src/frontend/src/**/*.tsx`. Replace all instances with `.jpg"`. This is a string-scoped find-and-replace — it only matches `src` attributes containing `/images/...svg"`.
2. Manually handle `HomePage.tsx` hero section: the `<img src="/images/hero-banner.svg" ...>` element is being **removed entirely** (not just its `.svg` extension changed) as part of Step 4. Do not change it here — leave it for Step 4 to remove cleanly.
3. After the replace, run `npm run dev` and visually confirm the affected pages render images correctly (or show the gradient fallback for any images not yet downloaded).

---

**Step 3 — Add scroll animation CSS to `index.css` (Section 7.2.2 + §18 of this doc)**

1. In `src/frontend/src/index.css`, locate the `:root` block (ends around line 46). Immediately after the closing `}` of `:root` and before `.emergency-strip`, insert the complete `/* === Scroll Animation Utilities === */` block defined in §18.1 through §18.5 of this document.
2. Verify the conflict-fix rule `.section-header .section-underline { opacity: 0; }` (§17.3 / §18.3) is present in this block.
3. Verify the `prefers-reduced-motion` block is the last entry in the animation utilities block and includes both `.section-underline` and `.section-header .section-underline` (§18.5).
4. Do a visual check: open any page with a `.section-header` in the browser. Confirm the colored underline bar is NOT visible before the section scrolls into view, then expands left-to-right when it enters the viewport.

---

**Step 4 — Create the two scroll hooks (Section 7.2.3)**

Create these two files in `src/frontend/src/hooks/`:

**`useScrollReveal.ts`** (for containers of multiple children):
- Accepts `options?: { threshold?: number; stagger?: boolean }` (defaults: threshold 0.15, stagger false).
- Returns a `ref` (`RefObject<HTMLElement>`).
- On mount: creates an `IntersectionObserver`; when observed container intersects, iterates all direct children that have `data-scroll` attribute; adds `"animated"` to each. If `stagger: true`, also adds `anim-delay-{i+1}` (i = 0-indexed, capped at 5 so max is `anim-delay-6`) before adding `"animated"`.
- Calls `observer.disconnect()` after firing once.
- Cleans up with `observer.disconnect()` in the `useEffect` return.

**`useSingleScrollReveal.ts`** (for one element):
- Accepts optional `threshold?: number` (default 0.15).
- Returns a `ref` for a single element.
- When element intersects, adds `"animated"` to its classList and disconnects.
- Cleans up on unmount.

---

**Step 5 — Create the `SectionHeader` component (Section 7.2.6 + §19 of this doc)**

Create `src/frontend/src/components/SectionHeader.tsx` per the spec in §19.2 of this document.

After creating the component, replace every manual `<div className="section-header"> ... </div>` pattern in the following files with `<SectionHeader title="..." />`:
- `HomePage.tsx` (5 instances: Why Choose Us, Our Departments, Meet Our Specialists, What Our Patients Say, Health Tips & News)
- `AboutPage.tsx` (4 instances: Our Purpose, Our Facilities, Accreditations, Our History)
- Any other public page that has the pattern

**Important**: For section headers that are visible above the fold on initial render (if any are not scroll-triggered), you must use a `useEffect` with `setTimeout(200)` to add `"animated"` instead of relying on `IntersectionObserver`. Review each page after implementation to confirm — IntersectionObserver will not fire for elements that are already in the viewport on page load.

---

**Step 6 — Apply page-by-page scroll animations (Section 7.2.5)**

For each page listed in `requirements.md` §7.2.5, apply the specified CSS classes and hook calls. The order to work through the pages:

1. `HomePage.tsx` — most complex; includes the hero "on mount" animations and the `StatsBand` integration (§7.2.7)
2. `AboutPage.tsx` — includes the `Timeline` component's per-card animations
3. `DepartmentsPage.tsx`
4. `ContactPage.tsx` — also add the 200px hero banner (currently missing; see §7.2.5 Contact Page note)
5. `BlogListPage.tsx`
6. `DepartmentDoctorsPage.tsx`
7. `DoctorProfilePage.tsx`
8. `BlogArticlePage.tsx`

For each "on mount" animation (above-fold elements): use `useEffect(() => { const t = setTimeout(() => { el.classList.add('animated'); }, delay); return () => clearTimeout(t); }, [])` where `el` is obtained via `useRef`.

For each "IntersectionObserver" animation: use `useSingleScrollReveal` (single element) or `useScrollReveal({ stagger: true })` (card grid container with `data-scroll` children) per the tables in §7.2.5.

**StatsBand integration note (§7.2.7):** The existing `StatsBand` IntersectionObserver callback (lines 96–101 of `HomePage.tsx`) calls `setTriggered(true)` and `obs.disconnect()`. Add the scroll class toggle here. Each `StatItem` wrapper `<div>` must get `className="scroll-fade-up"` initially, and within the observer callback, after `setTriggered(true)`, add `"animated"` to each stat item div. The simplest way: add `data-scroll` to each `StatItem`'s wrapper, attach the `bandRef` to a parent div inside `StatsBand`, and use `useScrollReveal({ stagger: true })` — but the existing observer already controls the counter animation. Consolidate: replace the manual `IntersectionObserver` in `StatsBand` with `useScrollReveal({ stagger: true })` for the CSS classes, but keep a separate `IntersectionObserver` (or integrate into the existing one) for `setTriggered(true)`. The simplest approach: keep the existing `IntersectionObserver` callback, add `"animated"` to all `[data-scroll]` children there alongside `setTriggered(true)`.

---

**Step 7 — Implement hero parallax in `HomePage.tsx` (Section 7.2.4 + §20 of this doc)**

1. Remove the `heroBgError` state and the `{!heroBgError ? <img ...> : <div fallback />}` block from the hero `<section>`.
2. Add `const heroRef = useRef<HTMLElement>(null)` at the top of `HomePage`.
3. Attach `ref={heroRef}` to the hero `<section>` element.
4. Update the hero section's inline style to include `backgroundColor`, `backgroundImage`, `backgroundSize`, `backgroundPosition`, `willChange` per §20.3 of this document.
5. Add the parallax scroll `useEffect` per `requirements.md` §7.2.4 (check `window.innerWidth >= 768`, check `prefers-reduced-motion`, add `scroll` listener with RAF throttle, return cleanup).
6. Confirm the gradient overlay `<div>` remains in place.
7. Verify AC-ANIM-4: scroll 200px on desktop — the background image visibly shifts upward relative to its initial position.

---

**Step 8 — Final verification against acceptance criteria**

Check each AC in `requirements.md` §7.3:

- AC-IMG-1 through AC-IMG-5: images display correctly; fallbacks work when files are missing.
- AC-ANIM-1: "Why Choose Us" cards stagger-scale-in on scroll.
- AC-ANIM-2: Timeline cards alternate slide-left/slide-right independently.
- AC-ANIM-3: Contact page left column slides left, right column slides right simultaneously.
- AC-ANIM-4: Hero parallax visible at ≥ 768px viewport, 200px scroll.
- AC-ANIM-5: Section underline expands left-to-right 150ms after h2 fades in.
- AC-ANIM-6: With `prefers-reduced-motion: reduce` (enable in Windows Settings or DevTools), all content is immediately visible with no animation.
- AC-ANIM-7: Hero heading, tagline, and CTA buttons are fully visible within 1 second of page load (they use `setTimeout(300ms)` + `animated` class, so they complete at ~900ms total).
- AC-ANIM-8: Animations do not replay on scroll-back (observer disconnects after first fire).
- AC-ANIM-9: Blog article body has no animation class — confirm no `scroll-*` class is on the article body `<div>`.
- AC-ANIM-10: StatsBand — counter animation and fade-up fire simultaneously when band enters viewport.

---

**No Pavan work required for Section 7.** All changes are within `src/frontend/`. Pavan's three backend tasks from §15 (above) were already part of Section 6 delivery and are unchanged.

---

## 23. Section 8 — BillingSpecialist Portal Component Hierarchy

Status: Draft v1.3 (Section 8)

### 23.1 Route Structure

All BillingSpecialist routes live under the `/billing` path prefix, protected by the existing `PrivateRoute` or role-guard mechanism. Add the following routes to `src/frontend/src/App.tsx`:

```
/billing              → BillingOverviewPage     (dashboard tiles + ledger first page)
/billing/invoices     → BillingInvoicesPage     (full paginated ledger)
/billing/invoices/:id → BillingInvoiceDetailPage (single invoice full detail)
/billing/claims       → BillingClaimsPage       (filtered view: has_insurance_claim=1)
/billing/records      → BillingRecordsPage      (read-only patient demographic list)
```

These five routes are the complete BillingSpecialist surface. No other route is accessible to this role.

### 23.2 Component Tree

```
src/frontend/src/
├── pages/
│   └── billing/                               [NEW directory]
│       ├── BillingOverviewPage.tsx            [NEW] tiles + first-page ledger
│       ├── BillingInvoicesPage.tsx            [NEW] full paginated ledger + filters
│       ├── BillingInvoiceDetailPage.tsx       [NEW] single invoice read + status actions
│       ├── BillingClaimsPage.tsx              [NEW] ledger pre-filtered has_insurance_claim=1
│       └── BillingRecordsPage.tsx             [NEW] patient demographic list (read-only)
│
├── components/
│   └── billing/                               [NEW directory]
│       ├── BillingTiles.tsx                   [NEW] four stat tiles row
│       ├── BillingLedger.tsx                  [NEW] shared table component used by Overview + Invoices + Claims
│       ├── BillingFilters.tsx                 [NEW] status select + insurance checkbox + search bar
│       ├── InvoiceStatusModal.tsx             [NEW] edit-status inline modal (select + note + Save)
│       └── ResendNotificationButton.tsx       [NEW] calls POST resend-notification; shows 3-sec confirmation
```

`BillingLedger` is the canonical shared component. It accepts:
```ts
interface BillingLedgerProps {
  invoices: InvoiceListItem[];
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onStatusEdit: (invoiceId: number) => void;
  onResend: (invoiceId: number) => void;
  loading: boolean;
}
```
Both `BillingOverviewPage` (shows 20 records, no filter controls, no Pager) and `BillingInvoicesPage` (shows full set with filters and Pager) render `<BillingLedger />` with different props. `BillingClaimsPage` renders `<BillingLedger />` with `?has_insurance_claim=1` pre-applied and `BillingFilters` with the insurance checkbox locked to `true`.

### 23.3 Sidebar Navigation

The `AppShell` `navByRole` map must include an entry for `BillingSpecialist`:

```ts
BillingSpecialist: [
  { label: 'Overview',  icon: 'LayoutDashboard', path: '/billing' },
  { label: 'Invoices',  icon: 'Receipt',          path: '/billing/invoices' },
  { label: 'Claims',    icon: 'FileCheck',         path: '/billing/claims' },
  { label: 'Records',   icon: 'FileText',          path: '/billing/records' },
]
```

No other nav items appear for this role. The sidebar user block at the bottom reads `full_name` and `role` from `AuthContext` (see Section 26).

---

## 24. Section 8 — Email Notification File-Sink Architecture

### 24.1 Delivery Flow

The notification handler runs **synchronously within the `PATCH /billing/invoices/{id}` request handler**, in this order:

1. Read current `invoices.status` from DB (`old_status`).
2. Apply the PATCH update and `session.commit()`.
3. If `status` field was in the request and `new_status != old_status`:
   a. Generate `timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')`.
   b. Build the HTML string (Section 8.3.3 structure).
   c. Ensure directory `uploads/email_log/` exists (`os.makedirs(..., exist_ok=True)`).
   d. Write file to `uploads/email_log/{timestamp}_{patient_id}_invoice_{invoice_id}.html`.
   e. Insert `email_notifications` row: `status = 'Sent'` on success, `status = 'Failed'` on `OSError` or `IOError`.
   f. If file write fails: log the error server-side (`logger.error(...)`); do NOT raise an exception that rolls back the invoice update (NOTIFY-3).
4. Return HTTP 200 with the updated invoice object.

### 24.2 File Path Pattern

```
uploads/email_log/YYYYMMDD_HHMMSS_{patient_id}_invoice_{invoice_id}.html
```

Example: `uploads/email_log/20260719_143022_7_invoice_1042.html`

- `uploads/` is the project-root-relative path (same directory as `uploads/lab_results/` if that exists).
- The directory is created at startup and also created lazily before the first write.
- Filenames are unique because the timestamp is to-the-second and concurrent writes within the same second for the same invoice are prevented by the PATCH endpoint being a synchronous handler (no async job queue).

### 24.3 HTML Email Template Contract

The HTML file must be a self-contained document with all styles as inline `style="..."` attributes. No `<link>` to external CSS. Structure in order:

| Section | Content |
|---|---|
| Header bar | `<div style="background:#0e8a7a;padding:24px;text-align:center;"><span style="color:#fff;font-size:28px;font-weight:700;">Green Valley Hospital</span></div>` |
| Greeting | `<p style="font-size:16px;color:#1a2422;">Dear {patient.full_name},</p>` |
| Body paragraph | Static text per Section 8.3.3 item 3 |
| Status change block | Two-row inline-styled table: Previous Status (amber badge if Pending), New Status (green badge if Paid, grey if Waived) |
| Invoice summary | Amount formatted as `$X,XXX.XX`; due date or "On receipt" |
| CTA button | Centered `<a href="#">View Your Invoice</a>` with inline styles per Section 8.3.3 item 6 |
| Footer | Divider + hospital address + disclaimer text |

Status badge inline styles (used in both the email template and the `BillingLedger` table column):
- `Pending`: `background:#fef3c7; color:#b7791f; border-radius:4px; padding:2px 8px; font-size:0.8125rem; font-weight:600;`
- `Paid`: `background:#d1fae5; color:#1e8e5a; border-radius:4px; padding:2px 8px; font-size:0.8125rem; font-weight:600;`
- `Waived`: `background:#f0f5f3; color:#536560; border-radius:4px; padding:2px 8px; font-size:0.8125rem; font-weight:600;`

These exact hex values are used inline in the email HTML (no CSS variable references — the email is a static file).

### 24.4 Manual Resend Flow

`POST /api/billing/invoices/{id}/resend-notification`:
- Retrieves the invoice and the patient's `full_name` and `email`.
- Sets `trigger_event = 'manual_resend'`; `old_status = current status`, `new_status = current status` (no change — this is a re-send of the current state).
- Generates and writes the HTML file (same template as status-change notification).
- Inserts `email_notifications` row.
- Returns `201` with the new `email_notifications` row (`notification_id`, `status`, `sent_at`).

---

## 25. Section 8 — Pagination Pattern and Pager Component Wiring

### 25.1 Envelope Shape

Every paginated endpoint now returns exactly five fields (updated from four in v1.0):

```ts
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;   // ceil(total / page_size); 0 when total is 0
}
```

The existing `Pager` component at `src/frontend/src/components/Pager.tsx` must receive:
- `page: number` — current page (1-indexed)
- `totalPages: number` — from `response.total_pages`
- `onPageChange: (newPage: number) => void` — callback that sets the page state variable

### 25.2 Wiring Pattern (applies to all 13 paginated list views)

```ts
// State
const [page, setPage] = useState(1);
const PAGE_SIZE = 20;

// Fetch
const { data } = useQuery(['billing-invoices', page, filters], () =>
  apiFetch(`/billing/invoices?page=${page}&page_size=${PAGE_SIZE}&${filterParams}`)
);

// Render
<BillingLedger ... />
<Pager
  page={page}
  totalPages={data?.total_pages ?? 1}
  onPageChange={setPage}
/>
```

### 25.3 Query Parameter Validation

Pavan enforces server-side:
- `page <= 0` → `400 Bad Request` `{"detail": "page must be >= 1"}`
- `page_size <= 0` → `400 Bad Request` `{"detail": "page_size must be >= 1"}`
- `page_size > 100` → silently clamped to 100; `page_size` in response is `100`

Chintu does not need client-side validation for page or page_size — the `Pager` component only emits valid page numbers (1 ≤ page ≤ totalPages).

### 25.4 Affected Endpoints List (Section 8.2.2)

All 13 of these endpoints now return the five-field envelope including `total_pages`. No new work required on endpoints already documented above — this is a note for Pavan to confirm each returns the new field:

1. `GET /admin/users`
2. `GET /admin/appointments`
3. `GET /admin/invoices`
4. `GET /patients/me/appointments`
5. `GET /patients/me/records`
6. `GET /patients/me/invoices`
7. `GET /doctor/me/appointments`
8. `GET /billing/invoices`
9. `GET /billing/notifications`
10. `GET /lab/orders`
11. `GET /staff/appointments`
12. `GET /public/blog`
13. `GET /public/departments/{id}/doctors` (if applicable — confirm with Pavan)

---

## 26. Section 8 — AuthContext Extension (JWT Claims)

### 26.1 New Context Fields

The JWT payload now carries `email` and `full_name` in addition to the existing `sub`, `role`, and `exp` claims (Section 8.2.4, AC-JWT-FIELDS).

The `AuthContext` type (located at `src/frontend/src/contexts/AuthContext.tsx` or equivalent) must be extended:

```ts
interface AuthContextValue {
  user: {
    user_id: number;
    role: string;
    email: string;       // NEW — decoded from JWT claim
    full_name: string;   // NEW — decoded from JWT claim
  } | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}
```

### 26.2 Login Flow Change

On `POST /api/auth/login` success:
1. Receive `{ access_token, token_type, expires_in, role, user_id }` from the API.
2. Decode the JWT payload (base64 decode the middle segment, `JSON.parse`). Do not verify the signature client-side — that is the backend's job.
3. Extract `email` and `full_name` from the decoded payload.
4. Store all five values in context state and in `localStorage` (same mechanism as the existing `role` / `user_id` storage).

No additional `/api/auth/me` call is required on page load or on component mount. The context is initialised from the stored JWT on app startup.

### 26.3 Usage in UI Components

| Component | Field used | Source |
|---|---|---|
| `AppShell` sidebar user block | `full_name`, `role` | `AuthContext.user` |
| `AppShell` topbar | `full_name`, `role` | `AuthContext.user` |
| `BillingOverviewPage` topbar | `full_name` | `AuthContext.user` |
| `PatientAppointmentsPage` greeting | `full_name` | `AuthContext.user` (no extra `/patients/me` call needed for name only) |

The existing `GET /api/auth/me` call may still be used on pages that need full profile data (phone, date of birth, etc.) — the JWT change only eliminates the need for a `/me` call solely to display the user's name and role.

---

## 27. Section 8 — New CSS Classes (Billing Specialist)

All rules below go into `src/frontend/src/index.css` under the section comment `/* === Billing Specialist === */`. This comment must be added if it does not already exist. No Tailwind classes. No utility-first classes. Dynamic per-tile values (left-border color, icon circle background) are passed as inline `style` props from the component — not as CSS class variants.

```css
/* === Billing Specialist === */

/* Tiles row — responsive grid */
.billing-tiles {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 2rem;
}

/* Individual tile card */
.billing-tile {
  flex: 1 1 200px;
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.5rem;
  /* border-left color is set via inline style prop per tile (see 8.4.3) */
  border-left: 4px solid transparent;
}

/* Icon circle inside tile */
.billing-tile__icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.75rem;
  /* background color is set via inline style prop per tile */
}

/* Tile numeric value */
.billing-tile__value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 0.25rem;
  color: var(--color-text);
}

/* Tile label text */
.billing-tile__label {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  font-weight: 500;
}

/* Master billing ledger table */
.billing-ledger {
  width: 100%;
  border-collapse: collapse;
}

/* Sticky header cells */
.billing-ledger th {
  position: sticky;
  top: 0;
  background: var(--color-surface);
  z-index: 1;
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.8125rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted);
  border-bottom: 2px solid var(--color-border);
}

/* Data cells */
.billing-ledger td {
  padding: 0.75rem 1rem;
  font-size: 0.9375rem;
  border-bottom: 1px solid var(--color-border);
}

/* Zebra striping (matches VI-SHARED-2 pattern) */
.billing-ledger tbody tr:nth-child(even) td {
  background: var(--color-surface-alt);
}

/* Row hover */
.billing-ledger tbody tr:hover td {
  background: var(--color-primary-light);
}

/* Filter bar above ledger */
.billing-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1rem;
}

/* Insurance claim badge */
.badge-insurance {
  background: #dbeafe;
  color: var(--color-info);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 0.8125rem;
  font-weight: 600;
}

/* Status badges for billing ledger — these mirror the inline email styles
   but as classes for the UI table (email HTML uses inline styles) */
.badge-status-pending {
  background: #fef3c7;
  color: #b7791f;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.badge-status-paid {
  background: #d1fae5;
  color: var(--color-ok);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.badge-status-waived {
  background: var(--color-surface-alt);
  color: var(--color-text-muted);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 0.8125rem;
  font-weight: 600;
}

/* Inline confirmation message shown after Resend Notification action */
.billing-resend-confirm {
  font-size: 0.8125rem;
  color: var(--color-ok);
  font-weight: 500;
}

/* Responsive: 2-column tile grid at 640px, 4-column at 1024px */
@media (min-width: 640px) {
  .billing-tile { flex: 1 1 calc(50% - 0.5rem); }
}

@media (min-width: 1024px) {
  .billing-tile { flex: 1 1 calc(25% - 0.75rem); }
}
```

---

## 28. Section 8 — Handoff Notes

---

### 28.1 Pavan (Backend) — Implementation Order

Work through these tasks in the order listed. Each task has enough information to begin without asking questions.

**Task 1 — Extend `users.role` CHECK constraint and ORM model**
- In `db/schema.sql`: already done (v1.2 DDL includes `'BillingSpecialist'`).
- In `src/backend/app/models.py`, `User.__table_args__`: change `CheckConstraint("role IN ('Admin','Doctor','Patient','Staff','Lab')", ...)` to `CheckConstraint("role IN ('Admin','Doctor','Patient','Staff','Lab','BillingSpecialist')", ...)`.
- This is a `require_role` string comparison — no other ORM change.

**Task 2 — Add `BillingSpecialist` ORM model**
- Add a new `BillingSpecialist` class to `models.py` mirroring the `billing_specialists` table in `db/schema.sql`: `billing_specialist_id` (PK), `user_id` (FK UNIQUE), `employee_id` (nullable String), `created_at` (String, default `_now_iso`). Add `user: Mapped[User] = relationship("User")`.

**Task 3 — Extend `Invoice` ORM model with `has_insurance_claim`**
- In `models.py`, `Invoice` class: add `has_insurance_claim: Mapped[int] = mapped_column(Integer, nullable=False, default=0)`.
- Add `CheckConstraint("has_insurance_claim IN (0,1)", name="ck_invoices_has_insurance_claim")` to `Invoice.__table_args__`.
- Add `Index("idx_invoices_has_insurance_claim", "has_insurance_claim")` to `Invoice.__table_args__`.
- Add `Index("idx_invoices_created_at", "created_at")` to `Invoice.__table_args__`.
- Update all existing invoice Pydantic response schemas to include `has_insurance_claim: int` (default 0). This applies to: admin invoice list, patient invoice list, and all new billing endpoints.

**Task 4 — Add performance indexes to existing ORM models**
- The DDL in `db/schema.sql` already contains all new indexes (v1.2). For the SQLAlchemy ORM, add the corresponding `Index(...)` entries to `__table_args__` in:
  - `Appointment`: `Index("idx_appointments_scheduled_at", "scheduled_at")`, `Index("idx_appointments_created_at", "created_at")`
  - `VisitNote`: `Index("idx_visit_notes_created_at", "created_at")`
  - `Prescription`: `Index("idx_prescriptions_created_at", "created_at")`
  - `LabOrder`: `Index("idx_lab_orders_created_at", "created_at")`
  - `LabResult`: `Index("idx_lab_results_created_at", "created_at")`
  - `BlogArticle`: `Index("idx_blog_articles_published_at", "published_at")`
  - `ContactMessage`: `Index("idx_contact_messages_created_at", "created_at")`
  Note: `patients.user_id` and `users.email` are already UNIQUE (implicit index) — no new Index() needed for those.

**Task 5 — Add `EmailNotification` ORM model**
- Add `EmailNotification` class to `models.py` mirroring `email_notifications` in `db/schema.sql`.
- Columns: `notification_id` (PK AUTOINCREMENT), `recipient_user_id` (FK → users.id, NOT NULL), `subject` (String NOT NULL), `body_html` (Text NOT NULL), `sent_at` (String NOT NULL), `trigger_event` (String NOT NULL), `related_invoice_id` (FK → invoices.invoice_id, nullable), `status` (String NOT NULL).
- `__table_args__`: `CheckConstraint("trigger_event IN ('invoice_status_change','manual_resend')", ...)`, `CheckConstraint("status IN ('Queued','Sent','Failed')", ...)`, `Index("idx_email_notifications_recipient", "recipient_user_id")`, `Index("idx_email_notifications_sent_at", "sent_at")`.

**Task 6 — Extend `POST /admin/users` to handle `BillingSpecialist` role**
- The existing admin user-creation endpoint creates role-profile rows for Doctor, Staff, Lab. Add a branch for `role = "BillingSpecialist"` that inserts a `billing_specialists` row with `user_id` and optional `employee_id` from the request body.
- Request body addition: `employee_id?: str` — optional field passed through when `role = "BillingSpecialist"`.

**Task 7 — Update `POST /auth/login` to include `email` and `full_name` in JWT**
- In `create_access_token` (wherever JWT minting happens), add `"email": user.email` and `"full_name": user.full_name` to the payload dict before encoding.
- No other endpoint changes needed for this task.
- Verify with AC-JWT-FIELDS: decode the issued token and confirm both fields are present for every role.

**Task 8 — Update `POST /auth/signup` to block non-Patient roles**
- The existing endpoint already ignores any `role` field in the request body (AC-AUTH-1). Add an explicit check: if the request body contains a `role` key with any value other than `"Patient"` (or `None`/absent), return `400 Bad Request` `{"detail": "Self-registration is available for Patient role only"}` (AC-BILL-ROLE-1).

**Task 9 — Add `total_pages` to all paginated endpoint responses**
- Every endpoint in the affected list (Section 25.4) currently returns `{items, total, page, page_size}`. Add `total_pages: ceil(total / page_size)` to each.
- Create a shared helper function `paginate_response(items, total, page, page_size)` that computes `total_pages` and returns the dict. Call it from every list endpoint.
- Also enforce: `page_size > 100` → silently clamp to 100; `page <= 0` or `page_size <= 0` → `400 Bad Request`.

**Task 10 — Implement `GET /billing/dashboard`**
- Role check: `require_role("BillingSpecialist")`.
- Execute four aggregate queries against the `invoices` table (see Section 9.2).
- For `collected_this_month_cents`, compute `start_of_current_month_UTC` as `datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()`.
- Return the four-field JSON object.

**Task 11 — Implement `GET /billing/invoices` (paginated list with filters)**
- Role check: `require_role("BillingSpecialist")`.
- Join `invoices` with `patients` (via `patients.patient_id`) and `users` (via `patients.user_id`) to resolve `patient_name`.
- Left-join `appointments` (via `invoices.appointment_id`) to resolve `appointment_date`.
- Apply server-side filters: `status`, `has_insurance_claim`, `search` (LIKE on `users.full_name` OR exact `invoice_id` match).
- Apply pagination via the shared helper from Task 9.
- No caching (PERF-CONS-1).

**Task 12 — Implement `GET /billing/invoices/{id}` (full detail)**
- Role check: `require_role("BillingSpecialist")`.
- Join to `appointments → doctors → departments` to resolve `doctor_name` and `department_name` (NULL-safe: null when `appointment_id` is null).
- Parse `line_items_json` into a Python list before returning (response field is `line_items`, not `line_items_json`).

**Task 13 — Implement `POST /billing/invoices` (create)**
- Role check: `require_role("BillingSpecialist")`.
- `line_items` in request body → serialized as JSON string in `line_items_json` column.
- `has_insurance_claim` defaults to `0` if not supplied.
- `created_by_user_id` = authenticated BillingSpecialist's `users.id`.
- Return the created invoice in full-detail shape.

**Task 14 — Implement `PATCH /billing/invoices/{id}` (update + notification)**
- Role check: `require_role("BillingSpecialist")`.
- Apply partial update (only fields supplied in the request body are changed).
- Notification side-effect: if `status` changed, run the email notification flow (Tasks 16–17 build the helper used here).
- Return updated invoice.

**Task 15 — Implement `DELETE /billing/invoices/{id}`**
- Role check: `require_role("BillingSpecialist")`.
- If `invoices.status != 'Pending'` → `409 Conflict` `{"detail": "Only Pending invoices may be deleted"}`.
- Otherwise: `session.delete(invoice)` + `session.commit()` + `204 No Content`.

**Task 16 — Implement email notification helper (`send_invoice_notification`)**
- Signature: `def send_invoice_notification(db, invoice, patient_user, old_status, new_status, trigger_event) -> EmailNotification`.
- Builds the HTML string per Section 8.3.3 (all inline styles, exact section order).
- Ensures `uploads/email_log/` exists.
- Writes file; captures `OSError`.
- Inserts `email_notifications` row with `status = 'Sent'` or `'Failed'`.
- On `OSError`: logs error, still inserts row with `status = 'Failed'`, returns the row. Does NOT raise or rollback.
- Returns the `EmailNotification` ORM instance.

**Task 17 — Implement `POST /billing/invoices/{id}/resend-notification`**
- Role check: `require_role("BillingSpecialist")`.
- Fetch invoice + patient user.
- Call `send_invoice_notification(..., old_status=invoice.status, new_status=invoice.status, trigger_event='manual_resend')`.
- Return `201` with `{notification_id, status, sent_at}`.

**Task 18 — Implement `GET /billing/patients`**
- Role check: `require_role("BillingSpecialist")`.
- SELECT only: `patients.patient_id`, `users.full_name`, `patients.date_of_birth`, `users.phone`, `users.email`.
- Do NOT include `address`, `gender`, `emergency_contact_name`, `emergency_contact_phone` (AUTHZ-9).
- Apply `?search` as LIKE on `users.full_name`.
- Paginate.

**Task 19 — Implement `GET /billing/appointments`**
- Role check: `require_role("BillingSpecialist")`.
- SELECT only: `appointments.appointment_id`, `appointments.patient_id`, `users.full_name AS patient_name`, `appointments.scheduled_at`, `appointments.status`, `doctor_users.full_name AS doctor_name`, `departments.name AS department_name`.
- Do NOT include `reason`, `diagnosis`, or any clinical fields (AUTHZ-8).
- Filter by `patient_id?` and `status?` if supplied. Paginate.

**Task 20 — Implement `GET /billing/notifications` and `GET /billing/notifications/{id}`**
- Role check: `require_role("BillingSpecialist", "Admin")` on both.
- List endpoint: ORDER BY `sent_at DESC`; join `users.full_name` as `recipient_name`; EXCLUDE `body_html` from list serialization.
- Detail endpoint: include `body_html`.
- Paginate list endpoint.

**Task 21 — Verify `has_insurance_claim` on all existing invoice endpoints**
- `GET /admin/invoices`: add `has_insurance_claim` to the response item.
- `GET /patients/me/invoices`: add `has_insurance_claim` to the response item.
- `POST /staff/appointments` billing path (if any): confirm `has_insurance_claim` defaults to `0`.
- Any endpoint that creates an invoice must default `has_insurance_claim = 0`.

**Task 22 — Create `uploads/email_log/` directory at startup**
- In the FastAPI startup event (or `lifespan` context), call `os.makedirs("uploads/email_log", exist_ok=True)`.

---

### 28.2 Chintu (Frontend) — Implementation Order

Work through these tasks in the order listed. Do not begin Task 3 until Pavan's Tasks 7 and 9 are deployed (JWT extension and pagination envelope). All other tasks can proceed with mock data.

**Task 1 — Add CSS for Billing Specialist portal**
- Open `src/frontend/src/index.css`.
- Add `/* === Billing Specialist === */` section comment after the scroll animation utilities block.
- Paste the full CSS block from Section 27 of this document into that section.
- Verify in browser DevTools that `.billing-tile`, `.billing-ledger`, `.billing-filters`, and badge classes parse without errors.

**Task 2 — Add BillingSpecialist routes to `App.tsx`**
- Import (lazily if desired): `BillingOverviewPage`, `BillingInvoicesPage`, `BillingInvoiceDetailPage`, `BillingClaimsPage`, `BillingRecordsPage` from `src/frontend/src/pages/billing/`.
- Wrap with the existing role-guard mechanism. The route guard must check `role === 'BillingSpecialist'` and redirect to `/login` if not.
- Add five routes: `/billing`, `/billing/invoices`, `/billing/invoices/:id`, `/billing/claims`, `/billing/records`.

**Task 3 — Extend `AuthContext` to store `email` and `full_name`**
- In `src/frontend/src/contexts/AuthContext.tsx` (or wherever the context is defined), update the context type per Section 26.1.
- In the `login` function: after receiving `access_token`, base64-decode the JWT payload segment, JSON-parse it, extract `email` and `full_name`, and store alongside `user_id` and `role`.
- Update `localStorage` serialization to include the two new fields.
- Update the context initializer (app startup) to read them back from `localStorage`.
- Verify: after login as any role, `AuthContext.user.email` and `AuthContext.user.full_name` are non-empty strings.

**Task 4 — Update `AppShell` sidebar user block**
- The sidebar user block currently reads from `user?.email`. Replace with `user?.full_name` for the name line and `user?.role` for the role line.
- Add the BillingSpecialist nav item map entry (Section 23.3) to the `navByRole` object.

**Task 5 — Create `BillingTiles` component**
- Path: `src/frontend/src/components/billing/BillingTiles.tsx`.
- Fetches `GET /api/billing/dashboard` on mount.
- Renders four `.billing-tile` cards in a `.billing-tiles` flex row.
- Each tile: `.billing-tile__icon` div (with inline `background` color + Lucide icon), `.billing-tile__value` (formatted number or currency), `.billing-tile__label`.
- Tile specs (left-border color token as inline style, icon, format):
  - Outstanding Invoices: `border-left-color: var(--color-warn)`, icon `Clock`, value = `outstanding_invoices` as integer
  - Awaiting Claims: `border-left-color: var(--color-info)`, icon `FileCheck`, value = `awaiting_claims` as integer
  - Collected This Month: `border-left-color: var(--color-ok)`, icon `TrendingUp`, value = format cents as `$X,XXX.XX`
  - Total Patients Billed: `border-left-color: var(--color-primary)`, icon `Users`, value = `total_patients_billed` as integer
- Show `<SkeletonBlock lines={1} />` while loading; `<PageError>` on error.

**Task 6 — Create `BillingFilters` component**
- Path: `src/frontend/src/components/billing/BillingFilters.tsx`.
- Props: `status: string`, `onStatusChange`, `hasInsuranceClaim: boolean`, `onInsuranceChange`, `search: string`, `onSearchChange`.
- Renders: a `<select>` with options All/Pending/Paid/Waived; a checkbox "Insurance claims only"; a text input with `Search` Lucide icon inside the left edge (same pattern as DepartmentsPage search — `padding-left: 2.5rem`, icon `position: absolute`).
- All changes call their respective `on*` prop immediately (controlled inputs). No debounce — the parent component decides when to refetch.

**Task 7 — Create `BillingLedger` component**
- Path: `src/frontend/src/components/billing/BillingLedger.tsx`.
- Props per Section 23.2 interface.
- Renders a `<table className="billing-ledger">` with the eight columns from Section 8.4.4:
  - Invoice ID: `#{invoice.invoice_id}`
  - Patient Name: `<Link to={/billing/patients?id=${invoice.patient_id}}>{invoice.patient_name}</Link>`
  - Appointment Date: `invoice.appointment_date` formatted as `MMM D, YYYY` using `new Date(...).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'})`, or `—` if null.
  - Amount: `$${(invoice.total_amount_cents / 100).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}` — the `BillingLedger` component contains this formatter inline.
  - Status: `<span className={badge-status-pending/paid/waived}>{invoice.status}</span>`
  - Insurance Claim: `<span className="badge-insurance">Claimed</span>` if `has_insurance_claim === 1`, else `—`.
  - Created Date: `invoice.created_at` formatted as `MMM D, YYYY`.
  - Actions: three buttons — `View` (navigates to `/billing/invoices/${invoice.invoice_id}`), `Edit Status` (calls `onStatusEdit`), `Resend` (calls `onResend`).
- Show `<SkeletonBlock lines={5} />` when `loading` prop is true.
- Show `<PageError>` if the parent passes an error prop (add `error?: string` to props if needed).

**Task 8 — Create `InvoiceStatusModal` component**
- Path: `src/frontend/src/components/billing/InvoiceStatusModal.tsx`.
- Props: `invoiceId: number`, `currentStatus: string`, `onClose: () => void`, `onSaved: () => void`.
- Renders a modal overlay (`position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100`).
- Modal content: `<select>` with Pending/Paid/Waived options (defaulting to `currentStatus`), a `<textarea>` placeholder "Optional internal note (not sent to patient)", a Save button and Cancel button.
- On Save: calls `PATCH /api/billing/invoices/{invoiceId}` with `{status: selectedStatus}`.
- On success: calls `onSaved()` (which causes the parent to refetch) then `onClose()`.
- Show inline spinner on the Save button while the request is in flight.

**Task 9 — Create `ResendNotificationButton` component**
- Path: `src/frontend/src/components/billing/ResendNotificationButton.tsx`.
- Props: `invoiceId: number`.
- Renders a small button "Resend" (or icon button with `RefreshCw` Lucide icon + tooltip).
- On click: calls `POST /api/billing/invoices/{invoiceId}/resend-notification`.
- On success: replaces the button text with `.billing-resend-confirm` span "Notification sent." for 3 seconds (using `setTimeout`), then reverts to the button.
- On error: shows inline error text in `--color-danger` for 3 seconds.

**Task 10 — Create `BillingOverviewPage`**
- Path: `src/frontend/src/pages/billing/BillingOverviewPage.tsx`.
- Renders `<BillingTiles />` at the top.
- Below: a `<BillingLedger>` showing the first 20 invoices (`page=1, page_size=20`), NO `<BillingFilters>`, NO `<Pager>`. A "View all invoices" link below the ledger navigates to `/billing/invoices`.
- Page title for topbar: "Overview".

**Task 11 — Create `BillingInvoicesPage`**
- Path: `src/frontend/src/pages/billing/BillingInvoicesPage.tsx`.
- State: `page`, `status`, `hasInsuranceClaim`, `search`.
- Renders `<BillingFilters>` → `<BillingLedger>` → `<Pager>` (from `src/frontend/src/components/Pager.tsx`).
- On any filter change: reset `page` to `1` before refetching.
- `Pager` props: `page={page}`, `totalPages={data?.total_pages ?? 1}`, `onPageChange={setPage}`.
- The `InvoiceStatusModal` is conditionally rendered here (controlled by `editingInvoiceId` state: `null` = hidden, `number` = shown for that invoice).
- On `onSaved`: call refetch (invalidate the query or re-trigger the API call).
- Page title for topbar: "Invoices".

**Task 12 — Create `BillingInvoiceDetailPage`**
- Path: `src/frontend/src/pages/billing/BillingInvoiceDetailPage.tsx`.
- Fetches `GET /api/billing/invoices/{id}` using `useParams()` for the id.
- Renders a two-section layout:
  - Top: patient info card (name, DOB, phone, email) + appointment info (date, doctor, department) if linked.
  - Bottom: invoice details card (line items table, total, status badge, insurance claim badge, created date).
- Below: `<InvoiceStatusModal>` trigger button ("Edit Status") and `<ResendNotificationButton>`.
- "Back to Invoices" link at top-left with `ArrowLeft` Lucide icon.
- Show `<SkeletonBlock>` while loading; `<PageError>` on error.
- Page title for topbar: `Invoice #${id}`.

**Task 13 — Create `BillingClaimsPage`**
- Path: `src/frontend/src/pages/billing/BillingClaimsPage.tsx`.
- Identical to `BillingInvoicesPage` but with `has_insurance_claim=1` permanently applied to the API call and `BillingFilters` showing the insurance checkbox as checked and disabled (read-only).
- Page title: "Claims".

**Task 14 — Create `BillingRecordsPage`**
- Path: `src/frontend/src/pages/billing/BillingRecordsPage.tsx`.
- Fetches `GET /api/billing/patients` with `?page&page_size&search`.
- Renders a search input (same pattern as `BillingFilters` search bar, standalone) above a table with columns: Patient ID, Full Name, Date of Birth, Phone, Email.
- Table uses `.data-table` class for zebra striping (per Section 9.2 of this design doc).
- Renders `<Pager>` below.
- No edit controls — this is read-only.
- Page title: "Records".

**Task 15 — Add `BillingSpecialist` icon to Lucide icon assignment table**
- `FileCheck` icon is used for Claims nav item and Awaiting Claims tile — confirm `FileCheck` is imported from `lucide-react` in the relevant components.
- `TrendingUp` icon is used for Collected This Month tile.
- Both are available in `lucide-react` — no package update needed if `lucide-react` is already installed.

**Task 16 — Update `Pager` component to accept `totalPages` if not already present**
- Open `src/frontend/src/components/Pager.tsx`.
- Confirm the prop interface includes `totalPages: number`. If it currently uses `total` and `pageSize` to compute pages internally, add a `totalPages` prop (or keep the computed approach and update all call sites to pass `total` and `pageSize` instead of `totalPages` — pick one convention and document it here in a comment).
- The billing pages use `totalPages` from `response.total_pages` directly — this avoids re-computing on the client and is the canonical approach.

**Task 17 — Final verification against Section 8 acceptance criteria**
After all tasks complete, manually verify each AC:
- AC-BILL-ROLE-1: POST /auth/signup with role=BillingSpecialist → 400.
- AC-BILL-ROLE-2: Authenticated BillingSpecialist GET /patients/{id}/records → 403.
- AC-BILL-NOTIFY-1: Update invoice status to Paid → file appears at uploads/email_log/ and notification row exists.
- AC-BILL-NOTIFY-2: Make email_log unwritable → invoice still updates, notification row has status=Failed.
- AC-JWT-FIELDS: Decode login token → `email` and `full_name` present.
- AC-PAGINATE-1: GET /billing/invoices?page=2&page_size=10 with 35 invoices → total=35, total_pages=4, items count=10.
- AC-PAGINATE-2: page_size=500 → response page_size=100, items ≤ 100.
- AC-DASH-TILES: Verify all four tile counts match DB state.
- AC-LEDGER-SEARCH: search=pat → only Alice Patel invoices returned.
- AC-INSURANCE-FLAG: Set has_insurance_claim=1 → persisted and returned in GET.
- AC-BILL-ADMIN-DENY: BillingSpecialist GET /admin/dashboard → 403.

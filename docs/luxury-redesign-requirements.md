# Green Valley Hospital — Luxury Redesign Requirements

**Document version:** 1.0  
**Status:** Final  
**Owner:** Lavanya (Requirements Analyst)  
**Primary consumer:** Chintu (Full-Stack Developer)  
**Companion docs:** `docs/design.md` (existing design spec), `docs/requirements.md` (functional requirements), `docs/api-spec.md` (endpoint contracts)  
**Date:** 2026-07-20

---

## 1. Executive Summary

The goal of this document is to guide the transformation of the Green Valley Hospital website from its current functional-but-generic implementation into a premium, luxury-class digital experience on par with the world's leading private healthcare institutions — Cleveland Clinic, Mayo Clinic, and Apollo Hospitals. The redesign is not a cosmetic reskin: it is a deliberate elevation of every visible surface. Real, high-quality photography must replace all placeholder gradients and SVG assets. Typography must shift from a generic SaaS scale to a refined editorial hierarchy anchored by Playfair Display for all public marketing headings. The color system must introduce a carefully constrained gold accent to signal prestige. Interactions must feel considered and purposeful — not flashy, but unmistakably high-end. The authenticated portals (Admin, Doctor, Patient, Staff, Lab, BillingSpecialist) must not regress visually or functionally; they receive polish, not redesign. This document is the single source of truth for Chintu's implementation. Every specification below is directly actionable — no interpretation required.

---

## 2. Real Image Strategy

This is the highest-priority new requirement. Every gradient-only hero and card placeholder must be replaced by a real photograph before any other luxury polish is considered "done."

### 2.1 Free Stock Image Sources (No API Key Required)

Chintu must use the following sources. All URLs are usable directly as `<img src="...">` or as CSS `background-image` values.

**Unsplash Source API (keyword-based, non-deterministic)**

```
https://source.unsplash.com/1920x800/?hospital,medical
https://source.unsplash.com/1920x800/?doctor,clinic
https://source.unsplash.com/800x600/?cardiology,heart
```

Format: `https://source.unsplash.com/{width}x{height}/?{keyword1},{keyword2}`  
Limitation: URL resolves to a different image on each request. Suitable for downloading and saving locally; not suitable as a live `<img src>` in production because the image will change on every page load.

**Unsplash Direct Photo ID (deterministic, preferred for production)**

Format: `https://images.unsplash.com/photo-{id}?auto=format&fit=crop&w=1920&q=80`

These URLs are stable — the same photo ID always returns the same image. Chintu must hard-code these for all hero and department card images.

Curated photo IDs for Green Valley Hospital use:

| Use case | Photo ID | Description |
|---|---|---|
| Homepage hero | `1519494026892-80bbd2d6fd0d` | Bright hospital corridor, modern, clinical |
| Homepage hero (alternate) | `1576091160399-112ba8d25d1d` | Medical team in scrubs, confident pose |
| About page hero | `1551601651-2a8555f1a136` | Doctor team group, warm lighting, diverse |
| Cardiology department | `1628348068343-c6a848d2b6dd` | Heart monitor / ECG waveform close-up |
| Pediatrics department | `1559757148-5c350d0d3c56` | Pediatrician with young child, welcoming |
| Orthopedics department | `1551190822-a9333d879b1f` | X-ray of bones, clinical lightbox |
| Neurology department | `1559757175-5c350d0d3c56` | Brain scan imagery, neurologist at desk |
| Blog article cover | `1506126613408-eca07ce68773` | Doctor reviewing digital tablet, research |
| Blog article cover (alt) | `1579684385127-1ef15d508118` | Medical research laboratory, warm tones |

Full construction example:
```
https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1920&q=80
```

**Picsum Photos (seeded, fully deterministic)**

Format: `https://picsum.photos/seed/{seed}/1200/600`

Seeded Picsum returns the same image for the same seed every time, making it reliable for local fallback testing. It is NOT suitable for production use on a healthcare site because the photos are random (may include inappropriate content). Use Picsum only during development when Unsplash images have not yet been downloaded.

Example: `https://picsum.photos/seed/greenvalley-hero/1920/800`

**RandomUser.me (doctor and patient avatar portraits)**

Format:
```
https://randomuser.me/api/portraits/men/{n}.jpg      n = 1–99
https://randomuser.me/api/portraits/women/{n}.jpg    n = 1–99
```

These are consistent, realistic human portrait photos, suitable for doctor cards and testimonial avatars when no real staff photo exists. They are stable URLs — the same number always returns the same portrait.

Doctor portrait assignments (use these numbers to avoid duplication):

| Doctor slot | URL |
|---|---|
| Doctor 1 (male) | `https://randomuser.me/api/portraits/men/32.jpg` |
| Doctor 2 (male) | `https://randomuser.me/api/portraits/men/45.jpg` |
| Doctor 3 (male) | `https://randomuser.me/api/portraits/men/67.jpg` |
| Doctor 4 (female) | `https://randomuser.me/api/portraits/women/28.jpg` |
| Doctor 5 (female) | `https://randomuser.me/api/portraits/women/44.jpg` |
| Doctor 6 (female) | `https://randomuser.me/api/portraits/women/61.jpg` |
| Doctor 7 (male) | `https://randomuser.me/api/portraits/men/12.jpg` |
| Doctor 8 (female) | `https://randomuser.me/api/portraits/women/17.jpg` |

Testimonial patient avatar assignments:

| Patient slot | URL |
|---|---|
| Patient 1 | `https://randomuser.me/api/portraits/women/52.jpg` |
| Patient 2 | `https://randomuser.me/api/portraits/men/81.jpg` |
| Patient 3 | `https://randomuser.me/api/portraits/women/36.jpg` |

### 2.2 Image Component Requirements

Every `<img>` element in the frontend must comply with all four of the following rules without exception:

1. **`loading` attribute:** All images must have `loading="lazy"` except the homepage hero image, which must have `loading="eager"` to avoid layout shift on initial paint.

2. **`alt` text:** All images must have meaningful descriptive `alt` text that describes the content for a screen reader. Empty `alt=""` is acceptable only for purely decorative images where the surrounding text already conveys the meaning (e.g., the hero background photo). Doctor portrait images must have `alt={doctor.full_name}`. Department images must have `alt={`${department.name} department`}`.

3. **Graceful fallback:** Every `<img>` that could fail (remote URL, user-uploaded path) must implement the `onError` fallback pattern already established in the codebase:

```tsx
const [imgError, setImgError] = useState(false);

{imgError || !src
  ? <FallbackComponent />   // gradient div with icon/initials
  : <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setImgError(true)}
    />
}
```

The fallback component for hero sections is a CSS gradient using `--color-primary-dark`. The fallback for department cards is the existing gradient circle with a Lucide icon. The fallback for doctor/patient avatars is a gradient circle with the person's initials.

4. **`object-fit: cover`:** All images that fill a fixed-height container (hero images, card images, avatar circles, facility gallery images) must use `object-fit: cover`. Aspect ratios must be enforced by the container, not the image element itself.

### 2.3 Section-by-Section Image Requirements

The following table is the complete, authoritative specification for which image appears in each section. Chintu must not deviate from this mapping.

| Section | Image source | Alt text | Notes |
|---|---|---|---|
| Homepage hero | Unsplash ID `1519494026892-80bbd2d6fd0d`, 1920px wide | `""` (decorative) | `loading="eager"`. Use CSS `backgroundImage` on the `<section>`, not an `<img>` element, to enable parallax. |
| About page hero | Unsplash ID `1551601651-2a8555f1a136`, 1920px wide | `""` (decorative) | Must differ from homepage hero. |
| Department cards | One photo per specialty per table in §2.3a below | `"{department.name} department"` | `loading="lazy"`, `object-fit: cover`, 600px wide download. |
| Doctor portrait cards | randomuser.me portrait assigned per §2.1 table; fall back to initials circle | `{doctor.full_name}` | 90x90px, border-radius 50%. |
| Doctor profile page | Same as card portrait but displayed at 200x200px | `{doctor.full_name}` | Larger display — same URL, CSS resizes. |
| Testimonial avatars | randomuser.me portrait assigned per §2.1 table | `"{patient.name}, patient"` | 56x56px, border-radius 50%. |
| Blog article covers | Unsplash IDs from §2.1 table, alternated per article | `"{article.title} — health article"` | 600x300px display. |
| Login/Signup left panel | Unsplash ID `1551601651-2a8555f1a136` or a distinct warm clinic photo | `""` (decorative) | Hidden below 768px. Full-height `object-fit: cover`. |
| "How It Works" steps | No photo. Icon-only (Lucide icons). | N/A | Icons, not images. |
| CTA banner section | No photo. Pure gradient: `linear-gradient(135deg, var(--color-primary-dark), var(--color-primary))`. | N/A | Gradient only. |
| Footer | No photo. Dark background `--color-surface-dark`. | N/A | No images in footer. |

**§2.3a — Department-to-Unsplash Photo ID Mapping**

| Department | Unsplash Photo ID | Subject |
|---|---|---|
| Cardiology | `1628348068343-c6a848d2b6dd` | Heart monitor ECG |
| Pediatrics | `1559757148-5c350d0d3c56` | Doctor with young child |
| Orthopedics | `1551190822-a9333d879b1f` | Bone X-ray on lightbox |
| Neurology | `1559757175-5c350d0d3c56` | Brain scan / MRI imagery |
| Oncology | `1579684385127-1ef15d508118` | Clinical research setting |
| Radiology | `1559757148-5c350d0d3c56` | MRI scanner room |
| Emergency | `1576091160399-112ba8d25d1d` | Emergency medical team |
| Ophthalmology | `1506126613408-eca07ce68773` | Eye examination slit lamp |
| Gynecology | `1551601651-2a8555f1a136` | Women's health consultation |
| Dermatology | `1576091160399-112ba8d25d1d` | Dermatology clinical setting |
| Default (fallback) | Gradient fallback only | N/A — no photo needed |

For any department not in the above table, the existing onError gradient fallback is sufficient. Do not leave a broken `<img>` tag visible.

**Local file download (required before pushing to production):**

Chintu must download each Unsplash photo locally into `src/frontend/public/images/` rather than referencing Unsplash URLs directly in production. Direct Unsplash CDN URLs in production HTML violate Unsplash's hotlinking terms for commercial use. The correct workflow:

1. Download each photo using the Unsplash URL with the `?auto=format&fit=crop&w=1920&q=80` query string.
2. Save it to `src/frontend/public/images/{filename}.jpg`.
3. Reference it in code as `src="/images/{filename}.jpg"`.
4. Compress to under 300 KB per file using Squoosh (https://squoosh.app) at MozJPEG quality 75.

Filename mapping:

| Filename | Unsplash ID |
|---|---|
| `hero-banner.jpg` | `1519494026892-80bbd2d6fd0d` |
| `about-hero.jpg` | `1551601651-2a8555f1a136` |
| `auth-panel.jpg` | `1551601651-2a8555f1a136` |
| `dept-cardiology.jpg` | `1628348068343-c6a848d2b6dd` |
| `dept-pediatrics.jpg` | `1559757148-5c350d0d3c56` |
| `dept-orthopedics.jpg` | `1551190822-a9333d879b1f` |
| `dept-neurology.jpg` | `1559757175-5c350d0d3c56` |
| `dept-oncology.jpg` | `1579684385127-1ef15d508118` |
| `dept-radiology.jpg` | `1559757148-5c350d0d3c56` |
| `dept-emergency.jpg` | `1576091160399-112ba8d25d1d` |
| `dept-ophthalmology.jpg` | `1506126613408-eca07ce68773` |
| `dept-gynecology.jpg` | `1551601651-2a8555f1a136` |
| `dept-dermatology.jpg` | `1576091160399-112ba8d25d1d` |
| `blog-cover-1.jpg` | `1506126613408-eca07ce68773` |
| `blog-cover-2.jpg` | `1579684385127-1ef15d508118` |

---

## 3. Typography Refinements

### 3.1 Font Pairing — Final Specification

The font pairing is already partially implemented via the `--font-serif` token in `index.css`. This section finalizes exactly which elements use which font. No new fonts are introduced — only Playfair Display and Inter.

| Use case | Font | Weight | Style |
|---|---|---|---|
| h1, h2 on all public pages (HomePage, AboutPage, DepartmentsPage, DepartmentDoctorsPage, DoctorProfilePage, ContactPage, BlogListPage, BlogArticlePage) | Playfair Display | 700 | Normal |
| h3 on public pages (card titles, subsection headers) | Inter | 600 | Normal |
| Hero tagline / site subtitle | Playfair Display | 400 | Italic |
| Testimonial quotes | Playfair Display | 400 | Italic |
| Pull quotes and feature callout text | Playfair Display | 400 | Italic |
| Body text, captions, form labels, table cells | Inter | 400 | Normal |
| Button labels, nav links | Inter | 600 | Normal |
| Uppercase category labels ("OUR SERVICES", "ABOUT US") | Inter | 500 | Normal, `letter-spacing: 0.08em`, `text-transform: uppercase` |
| All authenticated portal pages (Admin, Doctor, Patient, Staff, Lab, Billing) — all text | Inter | various | Normal |

**Critical rule:** Playfair Display is exclusively a public marketing font. It must not appear anywhere inside the authenticated app shell (sidebar, topbar, dashboard cards, tables, forms). Authenticated pages use Inter only.

**Google Fonts link tag (must be present in `src/frontend/index.html` `<head>`):**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

The `display=swap` parameter is mandatory for performance — it prevents fonts from blocking render.

### 3.2 Heading Size Scale — Exact Values

All values are in `rem`. The base font size is `16px` (browser default, not overridden).

| Element | Desktop (≥1024px) | Tablet (640–1023px) | Mobile (<640px) |
|---|---|---|---|
| h1 — hero headline | `3.75rem` (60px) | `2.75rem` (44px) | `2rem` (32px) |
| h1 — page title | `3rem` (48px) | `2.25rem` (36px) | `1.75rem` (28px) |
| h2 — section title | `2.25rem` (36px) | `1.875rem` (30px) | `1.5rem` (24px) |
| h3 — card / subsection title | `1.25rem` (20px) | `1.125rem` (18px) | `1rem` (16px) |
| Body text | `1.0625rem` (17px) | `1rem` (16px) | `1rem` (16px) |
| Caption / muted text | `0.875rem` (14px) | `0.875rem` (14px) | `0.875rem` (14px) |

Implement via CSS custom properties and media queries in `index.css`, scoped to `.public-page` or `:is(.public-page) h1` selectors so they do not accidentally override authenticated portal typography.

```css
/* Public page heading scale */
.public-page h1.hero-title {
  font-family: var(--font-serif);
  font-size: 3.75rem;
  font-weight: 700;
}
.public-page h1.page-title {
  font-family: var(--font-serif);
  font-size: 3rem;
}
.public-page h2 {
  font-family: var(--font-serif);
  font-size: 2.25rem;
}
@media (max-width: 1023px) {
  .public-page h1.hero-title { font-size: 2.75rem; }
  .public-page h1.page-title { font-size: 2.25rem; }
  .public-page h2 { font-size: 1.875rem; }
}
@media (max-width: 639px) {
  .public-page h1.hero-title { font-size: 2rem; }
  .public-page h1.page-title { font-size: 1.75rem; }
  .public-page h2 { font-size: 1.5rem; }
}
```

Add `className="public-page"` to the outermost `<div>` in `PublicLayout.tsx` so the scoping works automatically for all public routes.

### 3.3 Letter Spacing and Line Height

These rules apply within `.public-page` only.

| Element | `letter-spacing` | `line-height` |
|---|---|---|
| h1, h2 | `-0.02em` | `1.15` |
| h3 | `-0.01em` | `1.3` |
| Body / p | `0` (default) | `1.7` |
| Caption `.text-muted` | `0` | `1.5` |
| Uppercase labels | `0.08em` | `1.4` |
| Testimonial / italic quotes | `0.01em` | `1.6` |

---

## 4. Color System Refinements

### 4.1 Complete Final Token Set

The following tokens are the canonical final state. Tokens already present in `index.css` that match are confirmed correct. New tokens must be added. Tokens that differ must be updated.

```css
:root {
  /* === Primary brand palette === */
  --color-primary:        #0e8a7a;   /* confirmed — no change */
  --color-primary-dark:   #096b5d;   /* confirmed — no change */
  --color-primary-light:  #e6f5f2;   /* confirmed — no change */
  --color-primary-deeper: #064e43;   /* NEW — for hero gradient overlays only */

  /* === Gold accent (luxury tier — use sparingly) === */
  --color-gold:           #c9a84c;   /* confirmed — already in index.css */
  --color-gold-light:     #f9f3e3;   /* confirmed — already in index.css as --color-gold-light */

  /* === Standard accent (emergency / CTA) === */
  --color-accent:         #e05c2a;   /* confirmed — no change */
  --color-accent-light:   #fdf0eb;   /* confirmed — no change */

  /* === Neutral system === */
  --color-bg:             #f8faf9;   /* confirmed — already updated */
  --color-surface:        #ffffff;   /* confirmed */
  --color-surface-alt:    #f0f5f3;   /* confirmed */
  --color-surface-dark:   #1a2f2b;   /* NEW — dark section backgrounds */
  --color-border:         #d8e3e0;   /* confirmed */
  --color-border-dark:    #b3c8c2;   /* confirmed */

  /* === Text === */
  --color-text:           #1a2422;   /* confirmed */
  --color-text-muted:     #536560;   /* confirmed */
  --color-text-light:     #8fa8a2;   /* confirmed */
  --color-text-on-dark:   #e8f5f2;   /* NEW — body text on dark backgrounds */

  /* === Semantic === */
  --color-danger:         #c0392b;   /* confirmed */
  --color-warn:           #b7791f;   /* confirmed */
  --color-ok:             #1e8e5a;   /* confirmed */
  --color-info:           #1f5aa8;   /* confirmed */

  /* === Elevation === */
  --shadow-sm:         0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:         0 4px 12px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06);
  --shadow-lg:         0 10px 28px rgba(0,0,0,0.12), 0 4px 10px rgba(0,0,0,0.06);
  --shadow-xl:         0 20px 60px rgba(0,0,0,0.12), 0 8px 20px rgba(0,0,0,0.06);
  --shadow-colored:    0 8px 32px rgba(14,138,122,0.22);
  --shadow-colored-lg: 0 12px 48px rgba(14,138,122,0.30);

  /* === Border radii === */
  --radius-sm:   6px;
  --radius-md:   10px;
  --radius-lg:   16px;
  --radius-xl:   24px;
  --radius-pill: 999px;
}
```

### 4.2 Gold Accent Usage Policy

`--color-gold` (#c9a84c) is a luxury signal color. It must appear in exactly these locations and nowhere else:

- The "Ranked #1 in the Region" badge on the homepage hero floating card.
- Star rating icons (filled stars) on doctor cards and testimonial cards.
- The "JCI Accredited" or "NABH Accredited" badge on the About page accreditations strip.
- Award icons on the "Why Choose Us" section if an item is specifically about awards or recognition.

`--color-gold` must NOT be used for:
- Buttons (primary or secondary)
- Nav links or hover states
- Form focus rings
- Any interactive element
- Body text or headings

### 4.3 `--color-surface-dark` Usage

`--color-surface-dark` (#1a2f2b) is the background for the CTA banner section ("Ready to Experience World-Class Care?"). On this background, all text must use `color: var(--color-text-on-dark)` or `color: #ffffff`. Do not render normal `--color-text` (#1a2422) on dark backgrounds — it fails WCAG contrast.

---

## 5. Section-by-Section Detailed Requirements

### 5.1 Emergency Strip

**Content:** Lucide `PhoneCall` icon (size 14, animated pulse) + text: `Emergency: +1 (555) 000-9999  |  Open 24 hours, 7 days a week`

**Layout:** Full-width, 36px tall, single centered row. The emergency number text uses `color: var(--color-accent)` and `font-weight: 600`. The rest of the text uses `color: rgba(255,255,255,0.85)`.

**Background:** `var(--color-primary-deeper)` (#064e43).

**Image:** None.

**Animation:** The `PhoneCall` icon has a `pulse-phone` CSS animation (scale 1 → 1.2 → 1, 1.5s ease-in-out infinite). This animation is already defined in `index.css`.

**Mobile behavior:** On screens below 480px, hide the `|  Open 24 hours...` part. Show only `Emergency: +1 (555) 000-9999`.

**Acceptance criteria:**
- Emergency strip is visible on all public pages above the navbar.
- Phone number text is `--color-accent` orange-red, clearly distinguishable.
- Strip is exactly 36px tall on desktop; collapses to number-only text on mobile below 480px.

---

### 5.2 Navigation

**Content (left to right):** `<Logo />` component | nav links: Home, About, Departments, Contact, Blog | auth buttons: Login (outline), Book Appointment (accent-filled) | hamburger button (mobile only).

**Layout:** Sticky, `position: sticky; top: 0; z-index: 100`. Height 64px on desktop. Full-width. Content constrained to `--content-max-width` centered.

**Glassmorphism on scroll:** When `window.scrollY > 10`, add class `.scrolled` to `<header>`. `.scrolled` applies:
```css
.public-nav.scrolled {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--shadow-sm);
}
```
Before `.scrolled`, the nav has `background: transparent` when it sits above the hero section on the homepage. On all other pages the nav starts with `background: var(--color-surface)` (not transparent) because there is no hero directly underneath.

**Nav link hover:** Smooth `color` transition from `--color-text` to `--color-primary`. No underline. Instead, a 4px × 4px dot (border-radius 50%, background `--color-primary`) appears centered below the link text via a `::after` pseudo-element that fades in on hover. Do not use `border-bottom` — it shifts layout.

**Active link:** Same dot indicator as hover, permanently visible for the current route. Use React Router's `NavLink` `isActive` prop to add class `nav-link--active`.

**Image:** None.

**Animation:** Logo fades in from `opacity: 0` to `opacity: 1` over 400ms on mount. Nav links stagger in from left over 300ms.

**Mobile behavior:** Below 768px, nav links and auth buttons are hidden. Hamburger button visible. On hamburger click, a dropdown panel slides down (`max-height: 0` to `max-height: 500px`, `overflow: hidden`, 250ms ease-in-out). Panel contains all nav links stacked, then Login and Book Appointment buttons stacked full-width. Panel closes on outside click or nav link click.

**Acceptance criteria:**
- On the homepage at scroll position 0, the nav background is transparent.
- After scrolling 10px, the glassmorphism background and shadow are visible.
- Active page nav link shows the dot indicator permanently.
- On 375px viewport the hamburger is visible and the dropdown works.
- The "Book Appointment" button uses `--color-accent` background on all viewports.

---

### 5.3 Hero Section

**Content:**
- Eyebrow label: `TRUSTED HEALTHCARE SINCE 1998` — uppercase, `--color-gold`, `letter-spacing: 0.08em`, `font-size: 0.875rem`, `font-weight: 500`, `font-family: var(--font-sans)`.
- h1: `World-Class Healthcare, Close to Home` — Playfair Display 700, `font-size: 3.75rem`, white.
- Tagline: `Compassionate doctors. Cutting-edge technology. Your health, our purpose.` — Playfair Display italic 400, `font-size: 1.25rem`, `color: rgba(255,255,255,0.88)`.
- CTA row: "Book an Appointment" button (`--color-accent` bg, white text, 48px height) and "Explore Departments" button (white outline, white text, 48px height, `border: 2px solid rgba(255,255,255,0.6)`). Buttons side-by-side with 16px gap.
- Floating card (glassmorphism): positioned bottom-right of hero content area on desktop. Contains: a green check icon, the text "Ranked #1 in the Region", and a gold star badge. Glass effect: `background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.2); border-radius: var(--radius-lg); padding: 1rem 1.25rem`. The "Ranked #1" text uses `--color-gold`. The card has `animation: float-card 3s ease-in-out infinite`.

**Image:** `/images/hero-banner.jpg` as CSS `backgroundImage` on the `<section>` element. Overlay: `linear-gradient(to right, rgba(6,78,67,0.92) 0%, rgba(6,78,67,0.65) 55%, rgba(6,78,67,0.2) 100%)`. Background fallback color: `var(--color-primary-deeper)`.

**Layout:** Full-bleed section, `min-height: 620px`, `max-height: 720px`, `display: flex; align-items: center`. Content div: `max-width: var(--content-max-width); margin: 0 auto; padding: 0 2rem; position: relative; z-index: 1; display: flex; justify-content: space-between; align-items: center`.

**Parallax:** On desktop (≥768px) and when `prefers-reduced-motion` is not set, a scroll listener updates `backgroundPositionY` at `window.scrollY * 0.4` using `requestAnimationFrame` throttling. See `docs/design.md` §20 for the exact implementation spec.

**Animation:** Hero heading, tagline, and CTA buttons animate in on mount using `setTimeout(300ms)` to add `animated` class to elements with `scroll-fade-up` class. Eyebrow label fades in first (0ms delay), h1 next (150ms), tagline (300ms), CTA buttons (450ms), floating card (600ms).

**Mobile behavior:** Below 768px: `min-height: 480px`. Content is centered and text-aligned center. CTA buttons stack vertically, each `width: 100%`. Floating card is hidden (`display: none`) below 768px.

**Acceptance criteria:**
- Hero photo is visible behind the gradient overlay on desktop and mobile.
- Eyebrow text is `--color-gold` and uppercase.
- h1 uses Playfair Display font.
- Floating card is visible on desktop, hidden on mobile.
- On 375px viewport, buttons stack vertically and fill the container width.
- Parallax scroll effect is visible when scrolling on desktop.
- With `prefers-reduced-motion: reduce`, the photo is still visible but no parallax or fade-in animations run.

---

### 5.4 Stats Band

**Content (4 stats):**

| Stat | Value | Label |
|---|---|---|
| Patients Served | `15,000+` | "Patients Served Annually" |
| Specialists | `80+` | "Expert Specialists" |
| Years of Excellence | `25` | "Years of Excellence" |
| Departments | `18` | "Medical Departments" |

Values are static/hardcoded marketing copy — not from an API.

**Image:** None. Background: `var(--color-primary-light)` (#e6f5f2).

**Layout:** Full-bleed section, `padding: 48px 1rem`. A 4-column CSS grid inside the content-max-width container. Each stat is a centered column: large animated number, small label below.

**Animation:** Counter animation using `IntersectionObserver` with `threshold: 0.3`. When band enters viewport, `requestAnimationFrame` increments each counter from 0 to its target over 1500ms. The numeric part animates; the `+` suffix is static. Each stat div also receives `animated` class on intersection for a `scroll-fade-up` entrance. Observer disconnects after first trigger.

**Mobile behavior:** 2×2 grid on both mobile and tablet. 4-in-a-row only at desktop (≥1024px).

**Acceptance criteria:**
- Stats counter animation fires exactly once when the band scrolls into view.
- Numbers animate smoothly from 0 to target value.
- On 375px viewport, stats display in a 2×2 grid.
- Background is `--color-primary-light` teal tint, not white.

---

### 5.5 Why Choose Us

**Content:** Section header "Why Choose Us" (Playfair Display h2) + subtitle "Committed to your health with technology and compassion". Six feature cards:

| # | Icon (Lucide) | Title | Body |
|---|---|---|---|
| 1 | `Award` | "JCI Accredited" | "Internationally accredited for patient safety and quality standards." |
| 2 | `Microscope` | "Advanced Technology" | "State-of-the-art diagnostics and minimally invasive surgical suites." |
| 3 | `Clock` | "24/7 Emergency Care" | "Round-the-clock emergency services with rapid response teams." |
| 4 | `Users` | "Expert Specialists" | "80+ board-certified physicians across 18 medical specialties." |
| 5 | `HeartHandshake` | "Patient-First Culture" | "Every care decision is guided by your comfort and well-being." |
| 6 | `ShieldCheck` | "Transparent Pricing" | "Clear, upfront billing with no hidden charges." |

**Image:** None. Icon in a 56px circle, `background: var(--color-primary-light)`, icon color `var(--color-primary)`, `size={28}`.

**Layout:** Section constrained to `--content-max-width`. 3-column card grid on desktop, 2-column on tablet, 1-column on mobile.

**Animation:** Cards stagger-scale-in using `useScrollReveal({ stagger: true })` with `data-scroll` on each card wrapper.

**Card hover:** `translateY(-6px)` + `box-shadow: var(--shadow-xl)` + `border-top: 3px solid var(--color-primary)`. Transition: `transform 220ms ease, box-shadow 220ms ease`.

**Acceptance criteria:**
- Six cards visible with Lucide icons.
- Cards stagger-animate in on first scroll into viewport.
- Hover lift and top border are visible on desktop.
- 2-column layout visible at 768px viewport.

---

### 5.6 Featured Departments

**Content:** Section header "Our Departments" + subtitle "World-class care across 18 specialties". Department cards sourced from `GET /api/public/home` response `content.featured_departments`. Each card shows:
- Department photo (from `/images/dept-{slug}.jpg`, with onError fallback).
- Department name (h3, Inter 600).
- Short description (2-line clamp).
- "Learn More →" link to `/departments/{department_id}`.

**Image:** Department-specific photos per §2.3a mapping.

**Layout:** 3-column grid on desktop, 2-column on tablet (≥640px), 1-column on mobile. Card image: `height: 200px`, `object-fit: cover`, `border-radius: var(--radius-lg) var(--radius-lg) 0 0`.

**Image hover:** On card hover, the image scales to `scale(1.05)`. The image wrapper must have `overflow: hidden` to clip the scale effect.

**Animation:** `useScrollReveal({ stagger: true })` on the cards container. `anim-delay-1` through `anim-delay-6` applied to individual cards.

**Acceptance criteria:**
- Department photos load correctly for cardiology, pediatrics, and orthopedics.
- Gradient fallback displays for departments without a matching image file.
- Image scales on card hover without overflowing its container.
- "Learn More" link navigates to the correct department page.

---

### 5.7 Care Journey (How It Works)

**Content:** Section header "Your Care Journey" + subtitle "Simple steps to exceptional care". Four steps:

| Step | Icon | Title | Description |
|---|---|---|---|
| 1 | `CalendarCheck` | "Book Appointment" | "Choose your specialist and schedule online or by phone." |
| 2 | `ClipboardList` | "Consultation" | "Meet your doctor for a thorough evaluation and diagnosis." |
| 3 | `FlaskConical` | "Diagnostics" | "Advanced lab and imaging for precise results." |
| 4 | `HeartPulse` | "Treatment & Follow-up" | "Personalized treatment plan and ongoing care support." |

**Image:** No photos. Icon-only. Each step has a large icon (Lucide, `size={40}`) in a 72px circle, `background: var(--color-primary-light)`, followed by a step number badge in `--color-gold`.

**Layout:** Horizontal 4-column grid on desktop (≥1024px). Vertical stack (single column) on tablet and mobile. Connecting line between steps: on desktop only, a horizontal dashed line `border-top: 2px dashed var(--color-border)` spans between the icon circles. Implemented via a `position: absolute` line element behind the icon row.

**Animation:** `scroll-scale-in` class on each step, staggered with `anim-delay-1` through `anim-delay-4`.

**Acceptance criteria:**
- Four steps visible with distinct Lucide icons.
- Horizontal layout with connecting dashed line at ≥1024px viewport.
- Vertical stack at 768px and 375px viewports.
- Step number badges use `--color-gold`.

---

### 5.8 Meet Our Specialists

**Content:** Section header "Meet Our Specialists" + subtitle "Experienced physicians dedicated to your health". Up to 4 doctor cards, sourced from `content.featured_departments[].first_doctor` in the home API response. If a department has no `first_doctor`, skip it. If all are null, hide the section entirely. Do not make a separate API call.

Each doctor card shows:
- Portrait photo (randomuser.me URL from §2.1 table or `profile_photo_path` from API, with initials fallback). 90×90px circle.
- Doctor name (Inter 600, `1.125rem`).
- Specialty badge (`--color-primary-light` background, `--color-primary` text, `border-radius: var(--radius-pill)`).
- "View Profile →" link to `/departments/{department_id}/doctors/{doctor_id}`.

**Image:** Doctor portraits per §2.1 table.

**Layout:** 4-column on desktop, 2-column on tablet, 1-column on mobile.

**Animation:** `scroll-fade-up` + stagger on each doctor card.

**Acceptance criteria:**
- Doctor portraits display as circles.
- Initials fallback (gradient circle with 2-letter initials) displays when portrait URL fails.
- Specialty badge uses primary light teal.
- "View Profile" link navigates correctly.

---

### 5.9 Testimonials

**Content:** Section header "What Our Patients Say". Three testimonial cards, hardcoded static data:

```ts
const TESTIMONIALS = [
  {
    quote: "The care I received at Green Valley was exceptional. The doctors listened, the nurses were attentive, and I felt safe throughout my recovery.",
    name: "Sarah Mitchell",
    role: "Cardiac Care Patient",
    avatar: "https://randomuser.me/api/portraits/women/52.jpg",
    rating: 5,
  },
  {
    quote: "From booking to follow-up, everything was seamless. The pediatrics team put my daughter completely at ease. We will always come back here.",
    name: "James Okonkwo",
    role: "Pediatrics Patient Parent",
    avatar: "https://randomuser.me/api/portraits/men/81.jpg",
    rating: 5,
  },
  {
    quote: "Green Valley's orthopedic team got me back on my feet faster than I expected. Their rehabilitation program is truly world-class.",
    name: "Priya Sharma",
    role: "Orthopedics Patient",
    avatar: "https://randomuser.me/api/portraits/women/36.jpg",
    rating: 5,
  },
];
```

Each card:
- Glassmorphism style: `background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.4); border-radius: var(--radius-xl); padding: 2rem`.
- Quote icon (`Quote` Lucide icon, `size={32}`, `color: var(--color-primary-light)`) at top-left.
- Quote text in Playfair Display italic 400.
- Star rating row: 5 filled `Star` icons, `color: var(--color-gold)`, `size={16}`.
- Patient avatar: 56px circle with `border: 2px solid var(--color-primary-light)`.
- Patient name (Inter 600) and role (`--color-text-muted`).

**Image:** Patient avatar photos from §2.1 randomuser.me table.

**Background:** Full-bleed section, `background: var(--color-surface-alt)`.

**Layout:** 3-column on desktop, 2-column on tablet, 1-column on mobile. On mobile: carousel behavior — one card visible at a time, swipe or arrow-button navigation.

**Mobile carousel:** Simple implementation using `useState<number>` for the active index and Previous/Next buttons (Lucide `ChevronLeft`/`ChevronRight`, 40px circle buttons). CSS: `display: flex; overflow: hidden` on the container, `transform: translateX(-{index * 100}%)` on the inner track, `transition: transform 300ms ease`. Arrow keys must also navigate (keyboard event listener on the section when focused).

**Animation:** `scroll-fade-up` on the section header. Each card `scroll-scale-in` with stagger.

**Acceptance criteria:**
- Glassmorphism card effect is visible (frosted glass look against `--color-surface-alt` background).
- Star ratings are `--color-gold` color.
- Quote text uses Playfair Display italic.
- Patient avatar photos load from randomuser.me.
- Initials fallback displays if avatar URL fails.
- On 375px viewport, one card is visible and Previous/Next buttons navigate between testimonials.
- Arrow keys navigate the carousel when the section is focused.

---

### 5.10 Blog / Health Tips

**Content:** Section header "Health Tips & News" + subtitle "Expert advice from our physicians". Up to 3 most recent published blog articles sourced from `content.recent_articles` in the home API response. If no articles, hide the section. Do not make a separate API call.

Each article card:
- Cover image: `/images/blog-cover-{n}.jpg` cycling (`n = 1` or `2`) based on article index, with gradient fallback. `height: 200px`, `object-fit: cover`.
- Category badge (article category or "Health Tips" default).
- Article title — 2-line `-webkit-line-clamp`.
- Summary — 3-line `-webkit-line-clamp`.
- Author name, publish date (formatted as "July 15, 2026").
- "Read More →" link to `/blog/{article_id}`.

**Image:** `blog-cover-1.jpg` for index 0, `blog-cover-2.jpg` for index 1, cycling back to `blog-cover-1.jpg` for index 2.

**Layout:** 3-column on desktop, 2-column on tablet, 1-column on mobile.

**Animation:** `scroll-fade-up` + stagger on article cards.

**Acceptance criteria:**
- Blog section renders when at least one published article exists in the API response.
- Blog section is hidden completely when `recent_articles` is empty.
- Cover images display with correct aspect ratio.
- Title and summary are clamped (no text overflow past 2 and 3 lines respectively).
- "Read More" links navigate to correct article detail pages.

---

### 5.11 CTA Banner

**Content:** "Ready to Experience World-Class Care?" (Playfair Display h2, white) + "Book your appointment today and take the first step toward better health." (Inter 400, `rgba(255,255,255,0.85)`) + "Book an Appointment" button (`--color-accent` bg, white text, 52px height, `border-radius: var(--radius-pill)`).

**Image:** No photo. Background: `linear-gradient(135deg, var(--color-surface-dark) 0%, var(--color-primary-dark) 100%)`.

**Layout:** Full-bleed section, `padding: 80px 1rem`, centered content, `text-align: center`. Button is centered below the body text.

**Animation:** `scroll-fade-up` on the h2, `scroll-fade-up anim-delay-1` on the paragraph, `scroll-fade-up anim-delay-2` on the button.

**Mobile behavior:** Identical to desktop — centered text and button, reduced padding to `56px 1.5rem`.

**Acceptance criteria:**
- Gradient background is dark — NOT the same as the primary teal sections.
- h2 uses Playfair Display.
- Button uses `--color-accent` orange-red, not `--color-primary`.
- Content animates in on scroll.

---

### 5.12 Footer

**Content:** 4-column layout:
- Column 1 (2fr): `<Logo variant="white" />`, tagline, address, emergency phone (`--color-accent` text), social media links (icons only: Facebook, Twitter, Instagram, LinkedIn — Lucide icons).
- Column 2 (1fr): "Quick Links" heading + links: Home, About, Departments, Contact, Blog, Book Appointment.
- Column 3 (1fr): "Our Services" heading + top 6 department links (static list per `docs/design.md` §12).
- Column 4 (1.5fr): "Contact Us" heading + address block + phone + "Emergency: +1 (555) 000-9999" (`--color-accent`) + operating hours.

Bottom bar: `© 2026 Green Valley Hospital. All rights reserved.` | Privacy Policy | Terms of Service — all in `--color-text-light`, `font-size: 0.8125rem`.

**Image:** None. Background: `var(--color-surface-dark)` (#1a2f2b). All text `color: var(--color-text-on-dark)` or white.

**Layout:** 4-column CSS grid on desktop (≥1024px), 2-column on tablet (≥640px), 1-column on mobile.

**Animation:** None (footer is below fold; skip scroll animations to avoid complexity).

**Acceptance criteria:**
- Footer uses dark background `--color-surface-dark`.
- Logo white variant is visible.
- Emergency number is `--color-accent` orange-red.
- 4-column layout at 1280px viewport, 2-column at 768px, single column at 375px.

---

## 6. Inner Page Specifications

### 6.1 About Page

**Sections in order:**
1. Page hero banner — full-bleed, `/images/about-hero.jpg`, `height: 400px`, overlay `linear-gradient(to right, rgba(6,78,67,0.85), rgba(6,78,67,0.4))`. h1 "About Green Valley Hospital" in Playfair Display, white, left-aligned. Tagline in Playfair Display italic, white, `opacity: 0.88`.
2. Mission / Vision / Values — 3 cards in a row. `scroll-scale-in` staggered. Each card: Lucide icon (56px circle), title, body text.
3. Facility Gallery — 6 images in a 3×2 grid, each `height: 220px`, `object-fit: cover`, `border-radius: var(--radius-lg)`. Images: `/images/facility-icu.jpg`, `facility-er.jpg`, `facility-lab.jpg`, `facility-maternity.jpg`, `facility-outpatient.jpg`, `facility-pharmacy.jpg`.
4. Accreditations Strip — horizontal row of accreditation badges. Gold star icon + badge name. Background `var(--color-primary-light)`, `border-radius: var(--radius-xl)`.
5. History Timeline — alternating left/right on desktop; right-aligned on mobile. Per `docs/design.md` §8.2 spec.
6. `<BackToTopButton />` floating component.

**Acceptance criteria:**
- About hero photo is different from the homepage hero photo.
- Facility gallery shows all 6 photos or gradient fallbacks.
- Accreditation badges use `--color-gold` for star icons.
- Timeline alternates left/right on desktop, all right-aligned on mobile.

---

### 6.2 Departments Listing Page

**Sections:**
1. Page hero banner — full-bleed, `/images/departments-hero.jpg` (use same Unsplash `1576091160399-112ba8d25d1d` ID), `height: 300px`. h1 "Our Medical Departments".
2. Search input — controlled filter, Lucide `Search` icon inside input. Updates card grid in real time.
3. Department cards grid — 3-column on desktop, 2-column on tablet, 1-column on mobile. Each card: department photo (`/images/dept-{slug}.jpg`), name, description (3-line clamp), "View Doctors →" link.

**Image hover on cards:** `scale(1.05)` on the photo, `overflow: hidden` on the photo wrapper.

**Acceptance criteria:**
- Search input filters cards by name and description in real time (no API call — client-side filter).
- Department photos load; gradient fallback for unknown departments.
- Image scale hover effect works without overflow.

---

### 6.3 Department Detail / Doctors Page

**Sections:**
1. Department header banner — full-bleed, `/images/dept-{slug}.jpg` as background, `height: 280px`. Department name as h1 (Playfair Display, white), description below.
2. Doctor cards grid — 2-column on desktop, 1-column on mobile. Each card: portrait circle (90px), name, specialty, education, "View Profile" link.

**Image:** Portrait circles per §2.1 mapping or `profile_photo_path` from API.

**Acceptance criteria:**
- Department banner photo matches the department being viewed.
- Initials fallback works for doctors without a photo.
- `<BackToTopButton />` is present.

---

### 6.4 Doctor Profile Page

**Layout:** Two-column on desktop (30% photo panel, 70% info panel). Single column on mobile (photo above info).

**Photo:** 200px circle. Same portrait URL logic as doctor cards.

**Content:** Doctor name (Playfair Display h1), specialty badge, department, education, languages, bio. "Book an Appointment" CTA strip below the two-column section: `--color-primary-light` background, `border-radius: var(--radius-lg)`, flex row (text left, button right on desktop; stacked on mobile). CTA button links to `/signup` if not authenticated, `/patient/book?doctor_id={id}` if Patient role.

**Acceptance criteria:**
- Two-column layout on desktop, single column on mobile.
- CTA strip is visible below doctor details.
- CTA button route is correct for both unauthenticated and Patient users.

---

### 6.5 Contact Page

**Layout:** Two-column on desktop (≥1024px): left column = contact info + map placeholder; right column = contact form. Single column on mobile.

**Contact info cards:** Address (Lucide `MapPin`), Phone (Lucide `Phone`), Email (Lucide `Mail`), Hours (Lucide `Clock`). Each in a card with a `--color-primary-light` icon circle.

**Map placeholder:** `<div>` with `/images/map-placeholder.jpg`, `height: 240px`, `object-fit: cover`, `border-radius: var(--radius-lg)`. A badge overlay at bottom: "123 Medical Center Dr, Green Valley, CA 90210".

**Form:** Full name, email, phone (optional), subject, message textarea, Submit button (`--color-accent`). Form success state: replace form with a green success card ("Thank you! We will contact you within 24 hours.").

**Acceptance criteria:**
- Two-column layout at 1024px+, single column at 768px and below.
- Map placeholder image displays with the address badge overlay.
- Form submission shows success card without page reload.
- All form fields have properly associated `<label>` elements.

---

### 6.6 Blog List Page

**Sections:**
1. Page hero banner — `/images/blog-hero.jpg` (use `1506126613408-eca07ce68773` Unsplash ID), `height: 280px`. h1 "Health Tips & News".
2. Article cards grid — 3-column on desktop, 2-column on tablet, 1-column on mobile. Each card: cover image, category badge, title (2-line clamp), summary (3-line clamp), author + date, "Read More →".

**Acceptance criteria:**
- Blog hero photo is distinct from the homepage hero.
- Title and summary clamping works via `-webkit-line-clamp`.
- Pagination controls are visible when there are more than 12 articles.

---

### 6.7 Blog Article Page

**Layout:** Full-width article header image (`height: 380px`, `object-fit: cover`). Article title overlaid at bottom-left via `position: absolute; bottom: 0; left: 0` with local gradient. Below header: constrained article body `max-width: 720px; margin: 0 auto`.

**Meta row:** Category badge | Author name | Publish date | "X min read" (calculated: `Math.ceil(body.split(/\s+/).length / 200)`).

**Body text:** `font-size: 1.0625rem`, `line-height: 1.75`, `color: var(--color-text)`. No animation on body content.

**`<BackToTopButton />`** is mounted on this page.

**Acceptance criteria:**
- Cover image fills the full width of the page header area.
- Article title is overlaid on the image at bottom-left.
- Read time is calculated correctly from word count.
- Body text is constrained to 720px on desktop, full-width on mobile.

---

### 6.8 Login and Signup Pages

**Layout:** Split-screen, `min-height: 100vh`. Left panel: 45% width, hidden below 768px. Right panel: `flex: 1`, centered form.

**Left panel:** `/images/auth-panel.jpg`, full `object-fit: cover`. Dark gradient overlay `linear-gradient(to top, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0.1) 60%)`. At bottom: `<Logo variant="white" />` + tagline in white italic.

**Right panel form:** `max-width: 400px`, form title (Inter 700, `1.75rem`), inputs, primary submit button (`--color-accent`), link to the other auth page.

**Password field:** Relative wrapper, Eye/EyeOff toggle button `position: absolute; right: 12px`, input `padding-right: 2.75rem`.

**Mobile (below 768px):** Left panel `display: none`. Right panel is full width. `<Logo variant="default" />` renders above form title.

**Acceptance criteria:**
- Auth panel photo is visible on desktop.
- Left panel is hidden on 375px and 768px viewports.
- Logo white variant is visible on the panel at bottom.
- Password show/hide toggle works.
- Submit button uses `--color-accent` orange-red.

---

## 7. Animation and Interaction Specification

### 7.1 Scroll Animations

All scroll animations use the existing `.reveal` / `.scroll-fade-up` / `.scroll-scale-in` / `useScrollReveal` hook system defined in `docs/design.md` §18. No new animation library is to be introduced.

The `prefers-reduced-motion: reduce` override block (defined in `docs/design.md` §18.5) must be the last rule in the animation utilities CSS block and must force all animated elements to be immediately visible.

### 7.2 Hover States — Exact Specifications

**Cards (all department cards, doctor cards, blog cards, Why Choose Us cards):**
```css
.card-hover {
  transition: transform 220ms ease, box-shadow 220ms ease, border-top-color 220ms ease;
  border-top: 3px solid transparent;
}
.card-hover:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-xl);
  border-top-color: var(--color-primary);
}
```

**Buttons:**
```css
.btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-colored);
}
```
Transition: `transform 180ms ease, box-shadow 180ms ease`.

**Nav links:** Color transition `220ms ease` from `--color-text` to `--color-primary`. The 4px dot indicator (`::after` pseudo-element) fades in via `opacity 180ms ease`.

**Images inside cards:** The image `<img>` or background image wrapper gets `transition: transform 400ms ease`. On parent card hover, apply `transform: scale(1.05)`. The image wrapper must have `overflow: hidden; border-radius: var(--radius-lg) var(--radius-lg) 0 0` to clip the scale.

**Doctor/patient avatar circles:** No hover scale — these are identity elements, not interactive cards.

### 7.3 Micro-Interactions

| Element | Interaction | Implementation |
|---|---|---|
| Emergency strip phone icon | Pulse animation, 1.5s infinite | CSS `animation: pulse-phone` (already defined in `index.css`) |
| Hero floating card | Gentle float, 3s infinite | CSS `animation: float-card` (already defined in `index.css`) |
| Stats counters | Count up from 0 to target on scroll | `requestAnimationFrame` loop inside `IntersectionObserver` callback |
| Testimonial carousel | Slide on prev/next | CSS `transform: translateX` on the track, `transition: 300ms ease` |
| Back-to-top button | Fade in after 400px scroll | CSS `opacity` transition, toggled by scroll listener |
| Hamburger menu | Slide open/close | CSS `max-height` transition, 250ms ease-in-out |
| Nav scroll glassmorphism | Glassmorphism activates after 10px scroll | `scroll` event listener adds `.scrolled` class to `<header>` |

### 7.4 Reduced Motion Compliance

All animations defined in `index.css` must be wrapped or overridden by:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Additionally, the parallax scroll effect in `HomePage.tsx` must check `window.matchMedia('(prefers-reduced-motion: reduce)').matches` before attaching the scroll listener. If true, do not attach the listener.

---

## 8. Responsive Breakpoints

### 8.1 Breakpoint Definitions

| Name | CSS min-width | Description |
|---|---|---|
| Mobile | (base, no query) | Single column, stacked layout, hamburger nav |
| Tablet | `640px` | 2-column grids begin |
| Desktop | `1024px` | 3–4 column grids, side-by-side panels |
| Wide | `1280px` | Content capped at `--content-max-width` (1200px) centered |

### 8.2 Grid Behavior Per Section

| Section | Mobile (<640px) | Tablet (640–1023px) | Desktop (≥1024px) |
|---|---|---|---|
| Stats band | 2×2 grid | 2×2 grid | 4 in a row |
| Why Choose Us | 1 col | 2 col | 3 col |
| Featured Departments | 1 col | 2 col | 3 col |
| Care Journey | vertical stack | vertical stack | horizontal 4-col |
| Meet Our Specialists | 1 col | 2 col | 4 col |
| Testimonials | carousel (1 visible) | 2 col | 3 col |
| Blog / Health Tips | 1 col | 2 col | 3 col |
| Footer | 1 col | 2 col | 4 col |
| About facility gallery | 1 col | 2 col | 3 col |
| Auth pages (Login/Signup) | 1 col (left panel hidden) | 1 col (left panel hidden) | 2 col (split screen) |
| Contact page | 1 col | 1 col | 2 col |
| Doctor cards | 1 col | 2 col | 4 col |

### 8.3 Touch and Mobile Behavior

- All tap targets (buttons, links, nav items) must be at minimum 44×44px on mobile.
- The testimonial carousel must respond to touch swipe events via a `touchstart` / `touchend` listener computing `deltaX` — swipe left advances to next, swipe right goes to previous.
- The mobile hamburger menu must close on outside tap via a `mousedown` listener on `document`.

---

## 9. Accessibility Requirements

All public pages and authenticated portals must meet the following requirements:

**Semantic HTML:**
- `<header>` for the public nav bar.
- `<nav>` with `aria-label="Main navigation"` for the nav link list.
- `<main>` for the page content root.
- `<section>` with `aria-labelledby` pointing to its h2 for each major homepage section.
- `<footer>` for the site footer.
- `<article>` for each blog post card and blog article page.

**Focus management:**
- All interactive elements (buttons, links, inputs, carousel buttons) must have a visible focus ring: `outline: 2px solid var(--color-primary); outline-offset: 2px`.
- Do not use `outline: none` without a CSS replacement focus indicator.
- `tabindex` values greater than 0 are prohibited.

**Skip link:**
- A "Skip to main content" `<a href="#main-content">` link must be the very first focusable element in the DOM. It is visually hidden by default (`position: absolute; left: -9999px`) and becomes visible on focus (`left: 1rem`).
- The `<main>` element must have `id="main-content"`.

**Color contrast:**
- All normal body text must achieve WCAG AA minimum 4.5:1 contrast ratio against its background.
- All large text (≥18pt or ≥14pt bold, per WCAG definition) must achieve minimum 3:1 contrast ratio.
- `--color-text` (#1a2422) on `--color-surface` (#ffffff): ratio ~15:1. Pass.
- `--color-text-muted` (#536560) on `--color-surface` (#ffffff): verify with a contrast tool — must be ≥4.5:1.
- White text on `--color-primary` (#0e8a7a): verify — must be ≥3:1 for large text.
- `--color-gold` (#c9a84c) on white: do NOT use `--color-gold` for text except on dark backgrounds where contrast is sufficient.

**Images:**
- Decorative images (hero backgrounds, panel photos): `alt=""`.
- Content images (doctor portraits, department photos, blog covers): descriptive `alt` text as specified in §2.2.

**Forms:**
- Every `<input>` and `<textarea>` must have a `<label>` element with `htmlFor` matching the input's `id`.
- Error messages must be associated with their input via `aria-describedby`.

**Carousel:**
- The testimonial carousel container must have `role="region"` and `aria-label="Patient Testimonials"`.
- Previous and Next buttons must have `aria-label="Previous testimonial"` and `aria-label="Next testimonial"`.
- Arrow key navigation: `ArrowLeft` triggers previous, `ArrowRight` triggers next, when the carousel container or its buttons are focused.

---

## 10. Performance Requirements

**Image loading:**
- Hero image: `loading="eager"` (no lazy loading — it is above the fold).
- All other images: `loading="lazy"`.
- Hero image URL must be a stable, non-changing URL (the local `/images/hero-banner.jpg` static file — not a live Unsplash source URL that changes per request).

**Font loading:**
- Google Fonts `<link>` must use `display=swap` to prevent FOIT (flash of invisible text).
- `<link rel="preconnect" href="https://fonts.googleapis.com">` and `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` must precede the font stylesheet link.

**CSS animations:**
- `will-change: transform` must be applied only to actively animating elements (hero floating card, parallax hero section, hover-lifted cards). Do not apply `will-change` globally.
- Remove `will-change` in the `prefers-reduced-motion` block.

**JavaScript:**
- No external animation libraries (Framer Motion, GSAP, Animate.css) are permitted.
- Counter animation uses native `requestAnimationFrame` — no third-party library.
- Carousel uses CSS `transform` and `transition` — no Swiper, Slick, or similar library.

**Build:**
- `npm run build` must pass with zero TypeScript errors and zero TypeScript warnings at `strict: true`.
- No `any` type suppressions introduced by this redesign work.
- Bundle size must not increase by more than 50 KB gzipped compared to the pre-redesign baseline (new images are static assets in `public/`, not part of the JS bundle).

---

## 11. Acceptance Criteria — Definition of Done

Chintu must verify every item in this checklist before declaring the luxury redesign complete. QA (or the next sprint's review) will test each item independently.

**Build and code quality:**
- [ ] `npm run build` completes with zero TypeScript errors.
- [ ] No `console.error` or `console.warn` output on any public page in the browser DevTools.
- [ ] No React key warnings in the console.
- [ ] No `any` types introduced in redesign-related TypeScript files.

**Real images:**
- [ ] Homepage hero photo loads on desktop (1280px viewport). The photo is a real hospital/medical image, not a gradient placeholder.
- [ ] Homepage hero photo loads on mobile (375px viewport).
- [ ] About page hero is a different photo from the homepage hero.
- [ ] All three testimonial cards display patient avatar photos (randomuser.me portraits).
- [ ] Doctor cards on the home page "Meet Our Specialists" section display portrait photos.
- [ ] Doctor profile page displays a portrait photo (not initials fallback) for at least one doctor.
- [ ] Initials fallback (gradient circle, 2-letter initials) displays correctly when a portrait URL is intentionally broken (test by changing the URL in dev tools).
- [ ] At least 3 department cards display relevant specialty photos (not gradient fallbacks).
- [ ] Gradient fallback renders for departments without a matching image file — no broken `<img>` tag visible.
- [ ] Blog article cover images are visible on the home page blog section and the blog list page.

**Typography:**
- [ ] Playfair Display font is visibly different from Inter on h1 and h2 elements on the homepage.
- [ ] Homepage h1 hero title is approximately 3.75rem (60px) on desktop.
- [ ] Testimonial quote text uses Playfair Display italic.
- [ ] Eyebrow label above the hero h1 is uppercase with `letter-spacing: 0.08em`.
- [ ] No Playfair Display font appears on any authenticated portal page (Admin, Doctor, Patient, Staff, Lab, Billing).

**Color:**
- [ ] Gold accent (`--color-gold`) is visible on the "Ranked #1" badge on the hero floating card.
- [ ] Gold accent is visible on the 5-star rating icons in testimonial cards.
- [ ] No gold color appears on any button or primary interactive element.
- [ ] CTA Banner section background is dark (`--color-surface-dark` #1a2f2b), clearly distinct from the teal sections.
- [ ] Emergency phone number text is `--color-accent` orange-red in both the emergency strip and the footer.

**Sections and components:**
- [ ] Emergency strip is visible above the navbar on all public pages.
- [ ] Navigation glassmorphism effect is visible after scrolling 10px on the homepage.
- [ ] Mobile hamburger menu opens and closes correctly at 375px viewport.
- [ ] Hero floating card is visible on desktop and hidden on mobile.
- [ ] Stats counters animate from 0 on scroll (test by refreshing at the top of the page and scrolling to the stats band).
- [ ] Stats band displays in 2×2 grid on 375px, 4-in-a-row on 1280px.
- [ ] Care Journey section shows 4 steps with connecting dashed line on desktop.
- [ ] Care Journey switches to vertical stack on 768px viewport.
- [ ] Testimonial carousel shows one card at a time on 375px viewport.
- [ ] Previous/Next carousel buttons are visible and functional on mobile.
- [ ] Back-to-top button appears after scrolling 400px on About, Blog Article, and Department Doctors pages.
- [ ] Footer uses dark background with white text.
- [ ] Footer 4-column layout on 1280px, 2-column on 768px, single column on 375px.

**Interactions:**
- [ ] Card hover lift (`translateY(-6px)`) is visible on department cards, doctor cards, blog cards.
- [ ] Department card image scales on hover without overflowing the card container.
- [ ] Nav link dot indicator is visible on hover and on the active page.
- [ ] "Book Appointment" CTA button link navigates to `/signup` when not logged in.

**Responsive:**
- [ ] All layouts verified at 375px, 768px, and 1280px viewport widths.
- [ ] No horizontal scrollbar at any of the three viewport widths.
- [ ] No text overflow or content clipping at any of the three viewport widths.

**Accessibility:**
- [ ] "Skip to main content" link is the first focusable element and becomes visible on keyboard focus.
- [ ] All form inputs on Login, Signup, and Contact pages have associated `<label>` elements.
- [ ] All interactive elements have a visible focus ring when tabbed to.
- [ ] Testimonial carousel is navigable with ArrowLeft and ArrowRight keys.
- [ ] Hero image has `alt=""` (decorative, empty alt).
- [ ] Doctor portrait images have `alt="{doctor.full_name}"`.

**Authenticated portals (non-regression):**
- [ ] Admin dashboard loads and all stat cards display correctly.
- [ ] Doctor portal — appointments list loads and shows data.
- [ ] Patient portal — appointments and records pages load.
- [ ] Staff portal — schedule and directory pages load.
- [ ] Lab portal — test orders list loads.
- [ ] Billing portal — invoices list loads.
- [ ] No visual regressions on any authenticated page (verified visually at 1280px).

---

## 12. Out of Scope

The following items are explicitly excluded from this luxury redesign. Chintu must not implement these, and the architect must not ask for them during this build phase.

- **Dark mode toggle:** The design is light mode only. A dark mode variant is not planned for this build phase.
- **Video hero / background video:** The hero section uses a static photograph only. No `<video>` element or YouTube/Vimeo embed in the hero.
- **Parallax libraries:** Only native scroll events and CSS `backgroundPositionY` are used. No `react-scroll-parallax` or similar.
- **Image CDN or optimization pipeline:** Images are served as static files from Vite's `public/` directory. No Cloudinary, imgix, or Next/Image-style on-the-fly resizing.
- **User-uploaded profile photos via the UI:** The `profile_photo_path` field for doctors is set manually via plain-text input in the admin/doctor edit form. No file upload UI or drag-and-drop is required.
- **Animated page transitions (route transitions):** Routes transition instantly. No slide or fade between pages when navigating between routes.
- **Skeleton loading on public pages:** Skeleton loading (via `SkeletonBlock`) is only for authenticated portal pages. Public pages show a spinner or nothing while data loads — they do not need skeleton shimmer.
- **Internationalization (i18n) or RTL support:** English only. Left-to-right layout only.
- **Print stylesheet:** No `@media print` rules required.
- **Third-party chat widget (Intercom, Drift, etc.):** No chat or live support widget.
- **Cookie consent banner:** Not required for this demo build.
- **A/B testing framework:** Not required.
- **Analytics integration (Google Analytics, Mixpanel, etc.):** Not required.
- **PWA / service worker:** Not required.
- **SEO meta tags beyond basic `<title>` and `<meta name="description">`:** Open Graph, Twitter Card, and structured data (Schema.org) are out of scope.

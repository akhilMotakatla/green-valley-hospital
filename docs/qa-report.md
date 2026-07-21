# Green Valley Hospital — QA Report

Status: Complete
Stage: QA Engineer
Consumers: Orchestrator, Backend/Frontend developer agents

## Summary

Backend and frontend were previously verified independently (boot/build clean) but never tested together and had no automated test suite. This pass added a backend pytest suite, a frontend Vitest suite, and a live cross-stack smoke test. **No implementation bugs were found** — every test passes against the current `src/backend` and `src/frontend` code as written. All test-authoring mistakes discovered along the way (password mismatches, an in-memory-token test-isolation issue) were fixed in the tests, not the app.

## What was tested

### Backend (`tests/backend/`, pytest + FastAPI `TestClient`)
Runs against an isolated in-memory SQLite DB (`sqlite:///:memory:` via `StaticPool`, dependency-overridden `get_db`) — `db/green_valley.db` is never touched by the suite.

- **`test_auth.py`**: signup success forces `role=Patient` even if `role` is smuggled into the payload (AC-AUTH-1); weak-password rejection (SEC-1); duplicate-email rejection; login success returns role/token (AC-AUTH-2); wrong-password and unknown-email both return the same generic 401 (AUTH-5); deactivated-account login returns 403 with no token issued (AC-AUTH-3); `/auth/me` requires and honors a valid bearer token (AUTH-4).
- **`test_rbac.py`**: Patient hitting Doctor-only and Admin-only routes → 403; unauthenticated request → 401 (not 403); Patient can only fetch their own records via `/patients/{id}/records` (AC-PAT-1) and only sees their own rows in `/patients/me/appointments` (AC-PAT-2); Doctor with no appointment relationship to a patient → 403 (AC-DOC-1); Doctor with a relationship can read records and create a prescription retrievable by both doctor and patient (AC-DOC-2); a Doctor cannot update another doctor's appointment status; Staff and Lab cannot reach Doctor/Admin-only routes.
- **`test_core_flows.py`**: appointment booking creates a `Scheduled` row visible to both patient and doctor (AC-APT-1); double-booking the same doctor/slot → 409, no duplicate row (AC-APT-2); cancelling inside/outside the 2-hour notice window is rejected/allowed respectively (AC-APT-3); full lab workflow — order created by doctor appears in Lab's Pending queue, Lab uploads a finalized v1 result visible to the ordering doctor and owning patient but not an unrelated doctor, and amending creates a v2 while both versions remain retrievable (AC-LAB-1/2/3); draft blog articles are invisible on public endpoints and become visible once published (AC-BLOG-1/2); contact form: valid submission creates a row, missing-field submission is rejected with no row created (AC-CONTACT-1/2); Staff-created invoice is visible to the owning patient and Admin but not another patient (AC-BILL-1); Admin can create and deactivate a Staff account, after which login correctly returns 403.

**Result: 32/32 passed.**

### Frontend (`tests/frontend/`, Vitest + React Testing Library)
- **`route-guards.test.tsx`**: unauthenticated visitor hitting a protected route redirects to `/login`; wrong-role authenticated user redirects to `/unauthorized`; matching-role user sees the protected content; an expired JWT is treated as unauthenticated and redirects to `/login`.
- **`login-form.test.tsx`**: renders email/password fields and submit button; successful login navigates to the role's home route; failed login surfaces the API's error message.
- **`contact-form.test.tsx`**: renders required fields; valid submission calls the API with the right payload and shows the on-screen success confirmation; missing a required field blocks submission client-side (API never called).
- **`book-appointment-form.test.tsx`**: doctor/date/slot selection flow books successfully and shows a success message; submitting without a selected slot is blocked client-side; a 409 "already booked" response from the API is surfaced to the user.

**Result: 13/13 passed.**

Infrastructure notes: added `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, and `jsdom` as devDependencies; added `src/frontend/vitest.config.ts` (includes `tests/frontend/**/*.test.{ts,tsx}`, `@` alias to `src/frontend/src`, `server.fs.allow` widened so tests can live outside the Vite project root) and `src/frontend/vitest.setup.ts` (jest-dom matchers); added `npm test` script. A `node_modules` junction was created at the repo root (`node_modules -> src/frontend/node_modules`) so Vite's module resolution can walk up from `tests/frontend/` to find dependencies — required because the tests directory lives outside `src/frontend`.

### Live smoke test (uvicorn :8000 + Vite dev :5173, run concurrently)
1. `GET /` on the backend — OK.
2. `GET /api/public/contact-info` through the Vite dev proxy (`localhost:5173/api/...` → `localhost:8000`) — OK, correct field names.
3. `POST /api/auth/signup` through the proxy — created a real user, response shape matched the frontend's expected `User` type exactly (snake_case fields).
4. `POST /api/auth/login` directly against the backend — returned `access_token`/`role`/`user_id` matching `LoginResponse` in `src/frontend/src/types/index.ts`.
5. `GET /api/patients/me` through the proxy with `Authorization: Bearer <token>` — 200, correct data, confirming the frontend's Authorization-header interceptor pattern works against the real backend.
6. `GET /api/auth/me` directly against the backend with the same token — 200, consistent user record.
7. `OPTIONS` CORS preflight from `Origin: http://localhost:5173` — `200 OK` with `access-control-allow-origin: http://localhost:5173` and `access-control-allow-credentials: true`, confirming `CORS_ORIGINS` in `src/backend/app/config.py` is correctly scoped to the Vite dev origin.

The smoke-test user was deleted from `db/green_valley.db` afterward (`users`/`patients` rows removed by id) so the real dev database is left clean. Both servers were stopped after the run (no lingering processes on :8000/:5173).

**Result: all 7 smoke checks passed — frontend and backend interoperate correctly (matching field names, working CORS, working auth flow).**

## Bugs found

None. Every acceptance-criteria-driven test passed against the implementation as written; the RBAC/ownership checks in `src/backend/app/routers/*.py` and the route guards in `src/frontend/src/auth/RequireAuth.tsx` behave exactly as specified in `docs/requirements.md` §3.3 and `docs/api-spec.md`.

Two issues were found and fixed **in the test code itself** (not the application), documented here for transparency:
- Backend tests: several `_signup_patient` test helpers used password `"Passw0rd1"` while the shared `login()` helper defaulted to `"Passw0rd!"`, causing spurious 401s. Fixed by aligning all test passwords to `"Passw0rd!"`.
- Frontend route-guard tests: writing directly to `localStorage` between tests didn't invalidate the in-memory token cache in `src/frontend/src/api/client.ts` (`inMemoryToken`), causing state to leak across tests within the same file and produce order-dependent failures. This is expected behavior for the app (the cache is only ever mutated through `setToken`, which is what real login/logout flows do — direct `localStorage` writes bypassing the app are not a real usage pattern) — the fix was to drive the tests through the real `setToken()`/`getToken()` API instead of touching `localStorage` directly.

## Out of scope / not covered this pass

Admin CRUD beyond user create/deactivate (departments, blog edit/delete, audit log, site content), Staff vitals/registration flows, and file-upload edge cases (lab result attachments, blog cover images) were exercised indirectly (blog create/publish, lab result upload path) but not each given a dedicated test. No regressions were observed in manual review of those routers; recommend a follow-up pass if time allows, but nothing here blocks sign-off given the core acceptance criteria all pass.

---

## QA Pass 2 — Section 6 Visual Enhancement Backend Changes

Status: Complete
Date: 2026-07-18
Tester: Gopal (QA agent)

### Scope of this pass

Section 6 of `docs/requirements.md` introduced visual UI enhancements. Pavan (backend developer) made three concrete backend changes documented in `docs/api-spec.md` v1.1:

1. `GET /api/public/home` now includes a `recent_articles` array (up to 3, Published only) and `featured_departments[].first_doctor` with `profile_photo_path`.
2. `GET /api/public/departments/{id}/doctors` changed its response shape from a bare list to `{department: {...}, items: [...]}`.
3. `doctors.profile_photo_path` (nullable) is now exposed on every endpoint returning a doctor record.

This pass added 21 new backend tests in `tests/backend/test_section6_endpoints.py` and fixed 6 pre-existing frontend tests that were broken by the Section 6 UI changes (detailed below).

### Pre-run baseline (before new tests were added)

- Backend: 32/32 passed (unchanged from QA Pass 1).
- Frontend: 6/13 failed, 7/13 passed. The 6 failures were caused by Section 6 visual changes breaking the existing test assertions, not by any implementation bug.

### Frontend test failures (pre-fix, observed)

Both `login-form.test.tsx` and `contact-form.test.tsx` failed entirely (3 tests each):

**`login-form.test.tsx` (3 failed):**
- Root cause 1 — Section 6 (VI-AUTH-2) renamed the submit button from "Login" to "Sign In". `getByRole('button', { name: /login/i })` no longer matched any button.
- Root cause 2 — Section 6 (VI-AUTH-2) added a show/hide password toggle button with `aria-label="Show password"`. `getByLabelText(/password/i)` now matched both the password `<input>` (via its implicit label "Password") AND the toggle button (via its aria-label), causing a "multiple elements found" error.
- These are test-accuracy issues caused by a UI change, not implementation bugs in the app.
- Fix applied: updated button query to `/sign in/i`; replaced `getByLabelText(/password/i)` with `getByPlaceholderText(/your password/i)` (specific, unambiguous, and reflects the actual placeholder text in the new UI).

**`contact-form.test.tsx` (3 failed):**
- Root cause — Section 6 (VI-CONTACT-4) changed label text from the implied `"Name*"` to `"Name *"` (space before asterisk). The test regex `/name\*/i` matches `"name*"` (no space) but not `"Name *"` (with space). The JavaScript regex `\*` is a literal asterisk, making the pattern `name*` (zero or more 'e' characters would be the wrong reading — it is actually matching literal asterisk after "name", no space). Since the label now has a space, the regex never matched.
- Fix applied: updated all four required-field regexes from `/name\*/i` to `/name \*/i` (and similarly for email, subject, message). Also added a `waitFor` before the first query to let the async `getContactInfo()` call settle before asserting on labels.

### New backend tests added (`test_section6_endpoints.py`)

| Test name | What it verifies |
|---|---|
| `test_home_returns_recent_articles_key` | `/public/home` always has `recent_articles` key |
| `test_home_recent_articles_empty_when_no_published_articles` | Empty array returned, not null |
| `test_home_recent_articles_published_only` | Draft articles excluded from `recent_articles` |
| `test_home_recent_articles_capped_at_three` | At most 3 items in `recent_articles` |
| `test_home_recent_articles_shape` | All 7 required fields present on each item |
| `test_home_featured_departments_include_first_doctor_key` | Each featured dept has `first_doctor` key |
| `test_home_first_doctor_is_null_when_no_doctors` | `first_doctor` is null for doctorless depts |
| `test_home_first_doctor_shape` | `first_doctor` has `doctor_id`, `full_name`, `specialty`, `profile_photo_path` |
| `test_home_first_doctor_profile_photo_path_is_exposed` | Actual path value round-trips correctly |
| `test_department_doctors_returns_department_wrapper` | New `{department, items}` shape present |
| `test_department_doctors_department_object_shape` | `department` sub-object has required fields |
| `test_department_doctors_items_include_profile_photo_path` | Each doctor in `items` has `profile_photo_path` |
| `test_department_doctors_profile_photo_path_null_when_not_set` | Key present, value null, when no photo set |
| `test_department_doctors_404_for_unknown_department` | Non-existent dept returns 404 |
| `test_public_doctor_profile_includes_profile_photo_path` | `GET /public/doctors/{id}` exposes `profile_photo_path` |
| `test_public_doctor_profile_photo_path_reflects_set_value` | Value round-trips correctly |
| `test_doctor_me_includes_profile_photo_path` | `GET /doctor/me` exposes `profile_photo_path` |
| `test_doctor_me_profile_photo_path_null_by_default` | Null by default when not set |
| `test_doctor_patch_me_accepts_profile_photo_path` | `PATCH /doctor/me` persists `profile_photo_path` |
| `test_doctor_patch_me_profile_photo_path_can_be_cleared` | Sending null is accepted (no 500) |
| `test_staff_directory_includes_profile_photo_path` | `GET /staff/directory` exposes `profile_photo_path` |

### Final results (after all fixes and new tests)

**Backend: 53/53 passed** (32 pre-existing + 21 new)
**Frontend: 13/13 passed** (7 previously passing + 6 fixed)

### Bugs found this pass

**None.** All Section 6 backend changes (recent_articles, department wrapper, profile_photo_path) were implemented correctly by Pavan. The 6 frontend test failures were test inaccuracies caused by the Section 6 UI changes, not implementation bugs:

- The LoginPage button label "Sign In" (was "Login") is the correct implementation per VI-AUTH-2: "The submit button: full-width, 48px height, `--color-accent` background for the primary action." The button's visible text "Sign In" is not contradicted by any spec requirement and matches the implemented design intent.
- The ContactPage label format "Name *" (space before asterisk) is a rendering choice consistent with the VI-CONTACT-4 form styling requirement; the spec does not prescribe the exact label text format.
- The password show/hide toggle (aria-label "Show password") is required by VI-AUTH-2: "Password field: toggle show/hide password with Eye / EyeOff icon button inside the field right side."

All three are implementation-correct behaviors that the old tests did not anticipate. Tests were updated to match the actual (spec-compliant) UI.

### Still out of scope

Staff vitals recording (STF-4), Admin site-content PATCH endpoints, audit log entries written alongside user-management actions (ADM-9), and lab file attachment upload/download remain untested by automated tests. No regressions observed in code review; the untested paths are additive features not required by the Section 6 backend change set.

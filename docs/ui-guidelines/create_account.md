# Регистрация — Панель управления — UI Guidelines

**Source of truth:** `templates/create_account.html`, `endpoints/auth_login.py`
**Target page:** `GET /registr` → `render_template("create_account.html")`
**Conformance:** WCAG 2.2 AA · keyboard-first · token-driven
**Density (measured):** inputs (6) · buttons (1) · links (1 primary) · cards (1) · navigation (1)

---

## 1. Context and goals

**Design intent (one sentence):** The registration screen must let a technical user self-provision an account in one pass on a pure-black, single-card surface — collect identity, credentials, and the required invite code, then confirm — keyboard-first and WCAG 2.2 AA compliant.

**Goals**
- One task per screen: submit **name, email, password, password confirmation, invite code, terms** and create the account.
- Match `login.html` exactly: same black canvas, same card, same control metrics, so the two screens read as one product.
- Every interactive element is operable, visible, and announced with a keyboard.
- All values resolve to semantic tokens — no raw hex in component rules.

**Non-goals**
- No multi-step wizard, no marketing content, no billing or organization provisioning.
- No SSO / social login. Registration is invite-only through a shared server-side code.
- No custom focus styling outside the shared focus token; no per-component spacing/typography.

**Ground-truth note:** The auto-extracted brand context carries a *low-confidence* flag and conflicts with the live `login.html` in several places (§2.6). Where they conflict, the shipped page wins; the extracted palette (`color.text.secondary=#4446e1`, `color.surface.base=#000000`) is treated as a **reference palette**, not shipped truth. This page intentionally mirrors `login.html`'s reference palette so navigation between `/` and `/registr` is seamless; both pages share the same migration map.

---

## 2. Design tokens and foundations

Components **must** consume the semantic layer (§2.2–§2.5). Raw values (hex, px) **must not** appear in component CSS.

### 2.1 Reference palette

Raw values currently present in the template. Components **must not** reference these directly.

| Raw value | Role today | Contrast on `#000000` | Verdict |
|---|---|---|---|
| `#ffffff` | inverse / primary button text | 21.0:1 | pass AAA |
| `#ededed` | text tertiary / focus ring / button bg hover | 17.9:1 | pass AAA |
| `#dcdcdc` | text secondary (labels, links) | 15.3:1 | pass AAA |
| `#afafaf` | text primary (muted body, hints, placeholders) | 9.6:1 | pass AAA |
| `#ff9a9a` | text error | 10.3:1 | pass AAA |
| `#000000` | surface base | — | — |
| `#131313` | surface muted (card) | — | — |
| `#1a1a1a` | surface raised (flash) | — | — |
| `#4446e1` (extracted brand blue) | decorative accent only | **3.2:1** | **fail AA text** |
| `rgba(255,255,255,0.24)` | border strong (input/control edge) | **~1.9:1** on `#000` | **fail 1.4.11** |

> **Blocking findings (shared with login).** (1) The extracted brand blue `#4446e1` **must not** be used for text or glyphs — 3.2:1 fails AA; reserve it for `color.accent.brand` decoration only. (2) The input border at `rgba(255,255,255,0.24)` is ~1.9:1 against its `#000` fill and fails **1.4.11 Non-text Contrast (≥3:1)**; it **must** be raised to at least `rgba(255,255,255,0.36)` (§2.4).

### 2.2 Typography

| Semantic token | Value | Usage on this page |
|---|---|---|
| `font.family.primary` | `-apple-system` | platform chrome font |
| `font.family.stack` | `-apple-system, system-ui, "SF Pro Display", "SF Pro Text", system-ui, sans-serif` | body + controls |
| `font.size.base` | `12.75px` | smallest body/labels |
| `font.weight.base` | `500` | default weight |
| `font.lineHeight.base` | `19.125px` | default leading |
| `font.size.xs` | `12.75px` | labels, hints, errors, checkbox, footnote |
| `font.size.sm` | `13.5px` | inputs, buttons, subtitle |
| `font.size.md` | `13.95px` | reserved |
| `font.size.lg` | `15px` | reserved |
| `font.size.display` | `30px` **named token** | `auth__title` |
| `font.weight.strong` | `600` | title, primary button label |

**Rules**
- Headings **must** use `font.size.display` + `font.weight.strong`; the value `30px` **must not** be re-inlined.
- Body, labels, inputs, buttons **must not** exceed `font.size.sm`; the brand scale stops at 15px.
- Display letter-spacing **must** be `-0.01em` tokenized as `font.tracking.display`.
- Field hints (`password`, `invite_code`) **must** use `font.size.xs` + `color.text.primary` and **must not** be styled like errors.

### 2.3 Spacing

| Token | Value | Page usage (target) |
|---|---|---|
| `space.1` | `4px` | checkbox offset, hairline rules |
| `space.2` | `6px` | label→field gap, field→hint, field→error |
| `space.3` | `10px` | field→field gap, page gutters ≤480px |
| `space.4` | `14px` | card inner rhythm |
| `space.5` | `20px` | subtitle→form, footnote top, card padding ≤480px |
| `space.6` | `36px` | card padding (was `32px`) |
| `space.7` | `40px` | page gutters at ≥md |

**Rules**
- Field-to-field spacing **must** be `space.3`; label-to-control and field-to-error **must** be `space.2`.
- Card padding **must** be `space.6`; on ≤480px it **must** drop to `space.5`.
- **Must not** introduce interpolated spacing such as `21.28px`; it is not on the scale.

### 2.4 Color — semantic layer

| Semantic token | Value | Consumed by |
|---|---|---|
| `color.text.primary` | `#afafaf` | body copy, hints, placeholders, checkbox label, footnote |
| `color.text.secondary` | `#dcdcdc` | field labels, links (default) |
| `color.text.tertiary` | `#ededed` | headings, input value, toggle icon, link hover |
| `color.text.inverse` | `#ffffff` | text on primary button |
| `color.text.error` | `#ff9a9a` | field error, flash text |
| `color.surface.base` | `#000000` | page canvas, input fill |
| `color.surface.muted` | `#131313` | auth card |
| `color.surface.raised` | `#1a1a1a` | flash/alert container |
| `color.border.subtle` | `rgba(255,255,255,0.10)` | card edge |
| `color.border.strong` | `rgba(255,255,255,0.36)` **raised** | input/control outline |
| `color.border.error` | `#ff9a9a` | invalid field outline |
| `color.overlay.hover` | `rgba(255,255,255,0.06)` | toggle hover |
| `color.overlay.active` | `rgba(255,255,255,0.12)` | toggle active |
| `color.focus.ring` | `#ededed` | every `:focus-visible` |
| `color.control.primary.bg` | `#ffffff` | primary button fill |
| `color.control.primary.bg.hover` | `#ededed` | primary hover |
| `color.control.primary.bg.active` | `#dcdcdc` | primary active |
| `color.accent.brand` | `#4446e1` | **decorative only** — never text |

**Rules**
- All text **must** be ≥4.5:1; non-text UI boundaries and focus rings **must** be ≥3:1 (1.4.11 / 2.4.11).
- `color.border.strong` **must** resolve to `rgba(255,255,255,0.36)` or darker-on-black equivalent so inputs pass 1.4.11; verify ≥3:1 after compositing (§5, T-07).
- Checkbox `accent-color` **must** be `color.text.tertiary`; its checked glyph **must** remain distinguishable from `color.surface.base`.
- Error and hint text **must not** share a token; error uses `color.text.error`, hint uses `color.text.primary`.

### 2.5 Radius, shadow, motion, focus

| Token | Value | Usage |
|---|---|---|
| `radius.xs` | `8px` | inputs, flash, link focus rounding |
| `radius.sm` | `20px` | auth card |
| `radius.pill` | `9999px` **named token** | buttons, password toggle |
| `shadow.1` | `rgba(68,70,225,0.3) 0 2px 12px 0` | brand glow (decorative, optional) |
| `shadow.2` | `rgba(0,0,0,0.6) 0 12px 40px 0` | card elevation |
| `motion.duration.instant` | `200ms` | **default** interactive transition |
| `motion.duration.fast` | `150ms` | color/border micro-transitions (legacy) |
| `motion.easing.standard` | `cubic-bezier(0.2, 0, 0, 1)` | all transitions |
| `focus.width` | `2px` | ring thickness |
| `focus.offset` | `2px` | ring offset |

**Rules**
- Every `:focus-visible` **must** be `outline: focus.width solid color.focus.ring; outline-offset: focus.offset;`. `outline: none` is prohibited.
- Radius **must not** be inlined; migrate `radius-xs: 16px` → `radius.xs: 8px` (visual review — inputs become less rounded).
- Transitions **must** be suppressed under `prefers-reduced-motion: reduce` (present — keep it).

### 2.6 Token reconciliation (migration map)

| Current in `create_account.html` | Target token | Impact |
|---|---|---|
| `--font-family-primary: "OpenAI Sans"` | `font.family.stack` | font swap — visual review |
| `--font-size-md: 30px` | `font.size.display` | none (rename) |
| card `32px` | `space.6` (36px) | layout shift +4px |
| `--space-2: 12px` (label gap) | `space.2` (6px) | layout shift −6px |
| `--space-3: 16px` | `space.3` (10px) | field gaps tighten |
| `--space-5: 21.28px` | `space.5` (20px) | remove off-scale value |
| `--radius-xs: 16px` | `radius.xs` (8px) | rounding change |
| `--radius-md: 9999px` | `radius.pill` | rename |
| `--color-border-strong: 0.24` | `0.36` | **a11y fix** (shared with login) |
| `--motion-duration-instant: 120ms` | `200ms` | timing change |
| brand `color.text.secondary: #4446e1` | `color.accent.brand` | **must not be text** |

---

## 3. Component-level rules

Every interactive component **must** define: `default, hover, focus-visible, active, disabled, loading, error`. Missing any state is a blocker.

### 3.1 Page shell (`.auth`)

- **Anatomy:** full-viewport grid, single centered child, `background: color.surface.base`.
- **Rules:** `min-height: 100vh`; centering via grid `place-items: center`; page padding `space.4` (≥481px) / `space.3` (≤480px). Content **must** stay reachable when the viewport is shorter than the card (allow vertical scroll; no clipping).
- **Edge case:** the registration card is taller than the login card (6 fields) — on short viewports it **must** scroll, not overflow behind the fold; `min-height` **should** be `100dvh` where supported.

### 3.2 Auth card (`.auth__card`)

- **Anatomy:** `surface.muted` container → brand → title → subtitle → alert slot → form → footnote.
- **Variants:** default only.
- **States:** static container; **must not** be interactive.
- **Rules:** `max-width: 400px`, `width: 100%`, `border: 1px solid color.border.subtle`, `radius.sm`, `padding: space.6` (→ `space.5` ≤480px), optional `shadow.2`.
- **Responsive:** at ≤480px the card **should** go edge-to-edge within `space.3` page padding; `max-width` **must** still cap on large screens.
- **Edge case:** a long flash or long terms sentence **must** wrap and grow the card; the card **must not** set a fixed height.

### 3.3 Brand lockup (`.auth__brand` / `.auth__logo`) — navigation (1)

- **Anatomy:** centered logo image with `alt` = product name.
- **Rules:** logo height `40px`, width auto; `alt` **must not** be empty and **must not** duplicate the `<h1>` ("Intelligencerai" is acceptable).
- **Navigation rule:** the logo **must not** be a link to the current page; the card + lockup are the only navigation surface. The page **must not** add a nav bar.
- **Edge case:** if the logo 404s, the `width`/`height` attributes **must** preserve layout (no shift).

### 3.4 Heading & subtitle (`.auth__title` / `.auth__subtitle`)

- **Rules:** exactly one `<h1>` per page (`id="register-heading"`) and it **must** remain the `aria-labelledby` target of the card section. Title uses `font.size.display` + `font.weight.strong` + `color.text.tertiary`, centered. Subtitle uses `font.size.xs`, `color.text.primary`, centered; it **should** set the expectation that an invite code is required.
- **Edge case:** long translations **must** wrap; no truncation, no ellipsis.

### 3.5 Alert / flash (`.flash`)

- **Anatomy:** `<ul role="alert">` list of messages (e.g. `«Код приглашения недействителен.»`).
- **States:** hidden (no messages) / visible (≥1 message). Visible uses `color.text.error` on `color.surface.raised`, `1px solid color.border.error`, `radius.xs`, `padding: space.2 space.3`.
- **Rules:** `role="alert"` **must** remain; announce **must** happen once. Each `<li>` **must** be a complete, actionable sentence.
- **Edge case:** multi-message and long-message content **must** wrap within the card; the alert **must not** overlap the form.

### 3.6 Text fields (`.field__input`) — 5 controls + 1 checkbox

Variants: **name** (`autocomplete=name`), **email** (`type=email`, `inputmode=email`, `autocomplete=email`), **password** (`autocomplete=new-password`, `minlength=8`, toggle), **password confirmation** (`autocomplete=new-password`, `minlength=8`), **invite code** (`autocomplete=off`, `spellcheck=false`), plus the **terms checkbox** (§3.9).

| State | Signal | Tokens |
|---|---|---|
| default | border strong, fill base | `color.border.strong`, `color.surface.base`, text `color.text.tertiary` |
| hover | border brightens | border `color.text.primary` |
| focus-visible | 2px ring, offset 2 | `color.focus.ring` |
| active | inherits focus | — |
| disabled | dimmed, no pointer | `opacity: 0.5`, `cursor: not-allowed` |
| loading | inputs `readonly` + `aria-busy` on form | see §3.8 |
| error | red border + visible message | `color.border.error`, `color.text.error` |

- **Rules:** min height `44px` (touch target ≥44×44); padding `0 space.3`; radius `radius.xs`; font `font.size.sm`; placeholder `color.text.primary`. Error **must** be linked via `aria-describedby` and `aria-invalid="true"`. When error is shown, border **and** message **must both** change (never color-only).
- **Invite code:** **must** be `required`; input **should** be trimmed and case-normalized before validation. The accepted value is a single shared activation code that **must** live server-side (`ACTIVATE_INVITE_CODE`) and **must not** appear in HTML, JS, placeholder, hint, or error copy. Mismatch **must** surface on the field, never in a generic toast.
- **Password confirmation:** **must** validate equality with the password field; on mismatch the message **must** read `«Пароли не совпадают.»`.
- **Keyboard:** `Tab` enters/leaves; `Enter` submits; native validation **must not** be relied on (`novalidate` stays) — errors are rendered in DOM.
- **Pointer/touch:** tap focuses and opens the correct mobile keyboard (`inputmode`); long-press selection **must** work; native paste **must not** be disabled.
- **Responsive:** width `100%`; the password field reserves right padding for the toggle so text **must not** run under the icon.
- **Edge cases:** long email/organization **must** scroll horizontally inside the input; empty submit **must** focus the first invalid field in DOM order; pasted leading/trailing spaces **should** be trimmed before validation.

### 3.7 Password visibility toggle (`.field__toggle`)

- **Anatomy:** icon-only `<button type="button">` inside the password control.
- **States:** default (icon `color.text.primary`) / hover (`color.overlay.hover`) / focus-visible (ring) / pressed (`aria-pressed="true"`, icon `color.text.tertiary`) / disabled (inherits field disabled).
- **Rules:** target **should** grow to ≥44×44px (current `34px` needs invisible hit padding); `aria-pressed` **must** reflect state; `aria-label` **must** toggle between `«Показать пароль»` / `«Скрыть пароль»`; `aria-controls` **must** point to the password input; icon **must** be `aria-hidden`.
- **Keyboard:** reachable by `Tab`; `Space`/`Enter` toggles; focus **must** stay on the toggle.
- **Pointer/touch:** single tap toggles; **must not** submit the form (`type="button"`).
- **Edge case:** toggling **must not** clear the typed value or move the caret.

### 3.8 Button (`.btn`) — 1 on page

**Primary** submit (`«Создать аккаунт»`) is the only button; the screen is intentionally single-action.

| State | Primary |
|---|---|
| default | bg `control.primary.bg`, text `text.inverse` |
| hover | bg `control.primary.bg.hover` |
| focus-visible | ring `focus.ring` |
| active | bg `control.primary.bg.active` |
| disabled | `opacity:0.5`, `cursor:not-allowed`, no pointer events |
| loading | spinner `::after`, label hidden, `aria-busy="true"`, `cursor:progress` |
| error | n/a (use alert) |

- **Rules:** min height `44px`; `radius.pill`; `padding: 0 space.3`; label `font.size.sm`; label weight `font.weight.strong`; width **must** be `100%`.
- **Keyboard:** `Enter`/`Space` activates; **must not** trap focus; loading **must** keep focus on the button and announce busy.
- **Pointer/touch:** ≥44px height; hover affordance is additive, not required to discover the action.
- **Loading edge cases:** loading **must** be reversible on failure (remove `is-loading`, restore label, re-enable); spinner **must** respect reduced-motion.
- **Responsive:** unchanged; **must not** shrink below 44px height.
- **Prohibited:** adding a secondary/SSO button reintroduces a second action and is not allowed on this screen.

### 3.9 Terms checkbox (`.checkbox`)

- **Anatomy:** native `<input type="checkbox">` + `<label>` text (plain sentence, no inline links per density).
- **States:** unchecked / checked / hover / focus-visible / disabled / error.
- **Rules:** control ≥44px effective touch target **should** be met via label hit area; `accent-color: color.text.tertiary`; label `font.size.xs`, `color.text.primary`, top-aligned wrap. Label **must** be associated via `for`/`id`; the checkbox **must** be `required` and its error **must** be linked via `aria-describedby`.
- **Keyboard:** `Space` toggles; `Tab` enters/leaves; focus ring **must** be visible on the control.
- **Edge case:** long label **must** wrap without detaching from the box (alignment to first line); the whole label **should** be the hit target.

### 3.10 Link (`.link`) — 1 primary

**Footnote** `«Войти»` (→ `url_for('login')`).

- **Anatomy:** inline text link inside the footnote.
- **States:** default `color.text.secondary` / hover `color.text.tertiary` + underline / focus-visible ring (`radius.xs`) / active inherits / visited **must not** change color.
- **Rules:** `font.size.xs`; hover underline required — **must not** rely on color alone. Link text **must** be descriptive (`«Войти»`, not `«Нажмите здесь»`). The `href` **must** resolve to the real login route; `href="#"` is prohibited.
- **Keyboard:** `Enter` activates; last in tab order.
- **Touch:** hit area **should** be padded to ≥44px tall where it stands alone.
- **Policy references:** the terms sentence **must not** ship dead links. If policies are linked, they **must** use real `href`s and are then counted as additional links.

---

## 4. Accessibility requirements (testable)

| # | Requirement | Pass check |
|---|---|---|
| A-01 | Every interactive element has a visible focus indicator | Tab through all: each shows 2px `color.focus.ring`, offset 2, never removed |
| A-02 | Focus ring contrast ≥3:1 vs adjacent color | `#ededed` on `#000` = 17.9:1 → pass |
| A-03 | All body text ≥4.5:1 | §2.1 all pass |
| A-04 | Non-text UI boundaries ≥3:1 (1.4.11) | Input + checkbox borders ≥`0.36` white on black; verify composited ≥3:1 |
| A-05 | Inputs have programmatic labels | `name/email/password/password_confirm/invite_code/terms` resolve to `<label for>` |
| A-06 | Errors are announced and linked | `aria-invalid="true"` + `aria-describedby` → error `<p>`; read on focus |
| A-07 | Alert is announced | `role="alert"` on flash; message read without focus move |
| A-08 | Password toggle state is conveyed | `aria-pressed` flips; `aria-label` updates; `aria-controls` = password id |
| A-09 | No color-only meaning | Error uses border **+** text; link hover uses color **+** underline |
| A-10 | Touch targets ≥44×44px | Toggle, buttons, checkbox label padded to ≥44px effective target |
| A-11 | Reduced motion honored | With `prefers-reduced-motion: reduce`, no spinner rotation / transitions |
| A-12 | Zoom to 200% / 320px without loss | No horizontal scroll, no clipped controls at 200% and 320px |
| A-13 | Language set | `<html lang="ru">` present |
| A-14 | Loading is announced | Submit sets `aria-busy="true"`; failure clears it and restores focus |
| A-15 | Heading structure | Exactly one `<h1>`; card `aria-labelledby` points to it |
| A-16 | Focus order is logical | Name → Email → Password → Toggle → Confirm → Invite → Terms → Submit → Login |
| A-17 | Password confirmation matches | Mismatch blocks submit, focuses confirmation, shows linked error |
| A-18 | Invite code is required and server-checked | Client blocks empty; server validates against the allowed code |

**Keyboard map (required)**

| Key | Action |
|---|---|
| `Tab` / `Shift+Tab` | move through A-16 order |
| `Enter` (in field) | submit form |
| `Space` | toggle checkbox / toggle password button |
| `Enter` / `Space` (on button) | activate |
| `Escape` | no handler required; **must not** clear data |

**Pointer/touch:** every action reachable by tap; hover-only affordances prohibited; no gesture-only interactions.

---

## 5. Content and tone standards

**Voice:** concise, confident, implementation-focused. Russian. Sentence case. No exclamation marks, no marketing fluff, no blame (`«Ошибка»` alone is prohibited — say what to do).

**Field / control labels**

| Use | Avoid |
|---|---|
| «Имя и фамилия» | «ФИО» (ambiguous format) |
| «Электронная почта» | «Email адрес» (mixed script) |
| «Пароль» | «Введите пароль» as a label (that is a placeholder) |
| «Подтверждение пароля» | «Повторите» (too vague) |
| «Код приглашения» | «Промокод» (different concept) |
| «Я принимаю условия использования и политику конфиденциальности.» | «Ознакомлен(а)» (ambiguous consent) |
| «Создать аккаунт» | «Отправить» (non-descriptive) |
| «Показать пароль» / «Скрыть пароль» | «Глаз» / unlabeled icon |

**Errors (label + guidance, never blame)**

| Context | Copy |
|---|---|
| Missing name | «Укажите имя и фамилию.» |
| Invalid email | «Введите корректный адрес электронной почты.» |
| Missing / short password | «Пароль должен содержать не менее 8 символов.» |
| Mismatch | «Пароли не совпадают.» |
| Bad invite code | «Проверьте код приглашения.» |
| Terms not accepted | «Примите условия, чтобы продолжить.» |

**Empty / loading / links**
- Subtitle: «Заполните данные, чтобы получить доступ к панели управления. Понадобится код приглашения.»
- Password hint: «Не менее 8 символов, строчные и заглавные буквы, цифра.»
- Invite hint: «Код выдаёт администратор вашей команды.»
- Footnote: «Уже есть аккаунт? Войти»
- Loading a11y text: «Создаётся аккаунт…»
- **Must not** say «Произошла ошибка». Always actionable.

---

## 6. Anti-patterns and prohibited implementations

- **Must not** ship raw hex / px inside component CSS — only semantic tokens.
- **Must not** use `color.accent.brand` (`#4446e1`) for any text or icon: 3.2:1 fails AA.
- **Must not** keep the input border at `rgba(255,255,255,0.24)` — fails 1.4.11.
- **Must not** remove, hide, or thin the focus ring; no `outline: none` without a replacement.
- **Must not** signal errors with color alone; no red border without a message.
- **Must not** use a placeholder as a label (fails A-05).
- **Must not** use `href="#"` links in production — the terms text stays unlinked until real policy URLs exist.
- **Must not** add a terms checkbox without linking a visible, linked error — silent consent failure is prohibited.
- **Must not** introduce off-scale spacing (`21.28px`), a second "instant" duration, or an inline `30px` heading.
- **Must not** exceed `font.size.sm` in body/controls; display size is title-only.
- **Must not** animate the spinner under `prefers-reduced-motion: reduce`.
- **Must not** ship more than one action; a secondary/SSO button is prohibited on this screen.
- **Must not** write the invite code value into the client — it **must** live only in `ACTIVATE_INVITE_CODE` server-side.
- **Must not** disable native copy/paste on password fields.
- **Must not** ship client-only invite validation — the server **must** verify the code.

---

## 7. QA checklist

**Tokens**
- [ ] No raw hex/px in component rules; all resolve to §2 tokens.
- [ ] `color.border.strong` = `rgba(255,255,255,0.36)`+ (composited ≥3:1).
- [ ] `radius.xs` = 8px; `radius.pill` used for controls; display token replaces inline `30px`.
- [ ] Single `motion.duration.instant` value; reduces under reduced-motion.

**States**
- [ ] Button (primary): default/hover/focus/active/disabled/loading verified; loading reversible.
- [ ] 5 inputs: default/hover/focus/disabled/error verified; error shows border + text.
- [ ] Checkbox: focus ring visible; `Space` toggles; error links and blocks submit.
- [ ] Toggle: pressed/unpressed + label swap verified.
- [ ] Link: hover underline + focus ring; real `href`; no visited-color drift.

**Accessibility**
- [ ] A-01…A-18 pass with a screen reader + keyboard only.
- [ ] 200% zoom and 320px width: no horizontal scroll, no clipping.
- [ ] Contrast re-measured after any visual token change.
- [ ] Alert announced once; not duplicated by JS.

**Content**
- [ ] All copy matches §5; labels descriptive; errors actionable.
- [ ] No `href="#"`; no «Произошла ошибка».
- [ ] The invite code value appears nowhere in HTML/JS/placeholder/hint; only server-side `ACTIVATE_INVITE_CODE`.

**Responsive / edge cases**
- [ ] ≤480px: card padding `space.5`, page padding `space.3`, no overflow.
- [ ] Short viewport: card scrolls past the fold, nothing clipped.
- [ ] Long name/email/flash/terms wrap correctly; card grows.
- [ ] Logo failure preserves layout.
- [ ] Client-side and server-side invite validation align.

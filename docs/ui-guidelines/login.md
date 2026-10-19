# Вход — Панель управления — UI Guidelines

**Source of truth:** `templates/login.html`, `endpoints/auth_login.py`
**Target page:** `GET /` → `render_template("login.html")`
**Conformance:** WCAG 2.2 AA · keyboard-first · token-driven
**Density (measured):** buttons (2) · inputs (2) · links (1 primary) · cards (1) · navigation (1)

---

## 1. Context and goals

**Design intent (one sentence):** The login screen must let a technical user authenticate into the control panel with minimal friction on a pure-black, single-card surface — keyboard-first, fully token-driven, and WCAG 2.2 AA compliant.

**Goals**
- One task per screen: submit email + password. Nothing competes for attention.
- Zero decorative noise: black canvas, one card, one primary action.
- Every interactive element is operable, visible, and announced with a keyboard.
- All values resolve to semantic tokens — no raw hex in component rules.

**Non-goals**
- No multi-step wizard, no marketing content, no social login beyond the SSO slot that already exists.
- No custom focus styling outside the shared focus token.
- No new spacing/typography per component.

**Ground-truth note:** The auto-extracted brand context carries a *low-confidence* flag and conflicts with the live page in three places (see §2.6). Where they conflict, `templates/login.html` wins; the extracted brand palette is treated as a *reference palette*, not shipped truth.

---

## 2. Design tokens and foundations

Components **must** consume the semantic layer (§2.2–§2.5). Raw values (hex, px) **must not** appear in component CSS.

### 2.1 Reference palette

These are the raw values currently present in `login.html`. Components **must not** reference them directly.

| Raw value | Role today | Contrast on `#000000` | Verdict |
|---|---|---|---|
| `#ffffff` | inverse / primary button text | 21.0:1 | pass AAA |
| `#ededed` | text tertiary / focus ring / button bg hover | 17.9:1 | pass AAA |
| `#dcdcdc` | text secondary | 15.3:1 | pass AAA |
| `#afafaf` | text primary (muted body copy) | 9.6:1 | pass AAA |
| `#ff9a9a` | text error | 10.3:1 | pass AAA |
| `#000000` | surface base | — | — |
| `#131313` | surface muted (card) | — | — |
| `#1a1a1a` | surface raised (flash) | — | — |
| `#4446e1` (brand `color.text.secondary`) | extracted brand blue | **3.2:1** | **fail AA text** |
| `rgba(255,255,255,0.24)` | border strong (input) | **~1.9:1** on `#000` | **fail 1.4.11** |

> **Blocking findings.** (1) The extracted brand blue `#4446e1` **must not** be used for text or any glyph — it is 3.2:1 and fails AA. Reserve it for `color.accent.brand`, and only for non-text decoration (e.g. the `shadow.1` glow). (2) The input border at `rgba(255,255,255,0.24)` is ~1.9:1 against its own `#000` fill and fails **1.4.11 Non-text Contrast (≥3:1)**. It **must** be raised to at least `rgba(255,255,255,0.36)` (§2.4).

### 2.2 Typography

Brand scale is intentionally compact; the page heading sits above it and **must** be promoted to a named display token rather than a one-off.

| Semantic token | Value | Usage on this page |
|---|---|---|
| `font.family.primary` | `-apple-system` | enforces platform chrome font |
| `font.family.stack` | `-apple-system, system-ui, "SF Pro Display", "SF Pro Text", system-ui, sans-serif` | body + controls |
| `font.size.base` | `12.75px` | smallest body/labels |
| `font.weight.base` | `500` | default weight |
| `font.lineHeight.base` | `19.125px` | default leading |
| `font.size.xs` | `12.75px` | labels, helper, errors, footnote |
| `font.size.sm` | `13.5px` | inputs, buttons, subtitle |
| `font.size.md` | `13.95px` | reserved — see note |
| `font.size.lg` | `15px` | reserved — see note |
| `font.size.display` | `30px` **new token** | `auth__title` (currently `--font-size-md: 30px`) |
| `font.weight.strong` | `600` | title, primary button label |

**Rules**
- Headings **must** use `font.size.display` + `font.weight.strong`; the value `30px` **must not** be inlined again.
- Body, labels, inputs, buttons **must not** exceed `font.size.sm`; the brand scale stops at 15px.
- `letter-spacing` for display text **must** be `-0.01em` tokenized as `font.tracking.display`; **must not** be a per-component literal.
- Line-height for body **must** be `font.lineHeight.base`; display uses ratio `1.2` tokenized as `font.lineHeight.display`.

### 2.3 Spacing

Brand scale is odd-numbered; the page currently mixes `1/12/16/20/21.28`. Migrate to the brand scale.

| Token | Value | Page usage (target) |
|---|---|---|
| `space.1` | `4px` | hairline divider, icon gaps |
| `space.2` | `6px` | label→field gap, label→error |
| `space.3` | `10px` | field→field gap (form row gap) |
| `space.4` | `14px` | card inner vertical rhythm |
| `space.5` | `20px` | subtitle→form, footnote top |
| `space.6` | `36px` | card padding (was `32px`) |
| `space.7` | `40px` | page gutters at ≥md |

**Rules**
- Field-to-field spacing **must** be `space.3`; label-to-control **must** be `space.2`.
- Card padding **must** be `space.6`; on ≤480px it **must** drop to `space.5`.
- **Must not** introduce `21.28px` or any interpolated spacing; it is not on the scale.

### 2.4 Color — semantic layer

| Semantic token | Value | Consumed by |
|---|---|---|
| `color.text.primary` | `#afafaf` | body copy, placeholders, muted labels, footnote |
| `color.text.secondary` | `#dcdcdc` | field labels, links (default) |
| `color.text.tertiary` | `#ededed` | headings, input value, toggle icon, link hover |
| `color.text.inverse` | `#ffffff` | text on primary button |
| `color.text.error` | `#ff9a9a` | field error, flash text |
| `color.surface.base` | `#000000` | page canvas, input fill |
| `color.surface.muted` | `#131313` | auth card |
| `color.surface.raised` | `#1a1a1a` | flash/alert container |
| `color.border.subtle` | `rgba(255,255,255,0.10)` | card edge, divider rules |
| `color.border.strong` | `rgba(255,255,255,0.36)` **raised** | input/control outline, secondary button edge |
| `color.border.error` | `#ff9a9a` | invalid field outline |
| `color.overlay.hover` | `rgba(255,255,255,0.06)` | ghost/toggle hover |
| `color.overlay.active` | `rgba(255,255,255,0.12)` | ghost/toggle active |
| `color.focus.ring` | `#ededed` | every `:focus-visible` |
| `color.control.primary.bg` | `#ffffff` | primary button fill |
| `color.control.primary.bg.hover` | `#ededed` | primary hover |
| `color.control.primary.bg.active` | `#dcdcdc` | primary active |
| `color.accent.brand` | `#4446e1` | **decorative only** — never text |

**Rules**
- All text **must** be ≥4.5:1; all non-text UI boundaries and focus rings **must** be ≥3:1 (1.4.11 / 2.4.11).
- `color.text.primary` (`#afafaf`) **must not** be used for the input error or flash text; those **must** use `color.text.error`.
- `color.border.strong` **must** resolve to `rgba(255,255,255,0.36)` or darker-on-black equivalent so inputs pass 1.4.11; verify at 3:1 after compositing (§5, T-07).

### 2.5 Radius, shadow, motion, focus

| Token | Value | Usage |
|---|---|---|
| `radius.xs` | `8px` | inputs, flash, link focus rounding |
| `radius.sm` | `20px` | auth card |
| `radius.pill` | `9999px` **new token** | buttons, password toggle |
| `shadow.1` | `rgba(68,70,225,0.3) 0 2px 12px 0` | brand glow (decorative, optional) |
| `shadow.2` | `rgba(0,0,0,0.6) 0 12px 40px 0` | card elevation |
| `motion.duration.instant` | `200ms` | **default** interactive transition |
| `motion.duration.fast` | `150ms` | color/border micro-transitions (legacy) |
| `motion.easing.standard` | `cubic-bezier(0.2, 0, 0, 1)` | all transitions |
| `focus.width` | `2px` | ring thickness |
| `focus.offset` | `2px` | ring offset |

**Rules**
- Radius **must not** be inlined; the current `radius-xs: 16px` **must** be migrated to `radius.xs: 8px` (visual review required — inputs become less rounded).
- The page's `--motion-duration-instant: 120ms` **must** be aligned to `motion.duration.instant: 200ms` unless the design owner signs off on the brand value 200ms; do not keep two "instant" definitions.
- Every `:focus-visible` **must** be `outline: focus.width solid color.focus.ring; outline-offset: focus.offset;`. `outline: none` is prohibited.
- Transitions **must** be suppressed under `prefers-reduced-motion: reduce` (already present — keep it).

### 2.6 Token reconciliation (migration map)

| Current in `login.html` | Target token | Impact |
|---|---|---|
| `--font-family-primary: "OpenAI Sans"` | `font.family.stack` | font swap — visual review |
| `--font-size-md: 30px` | `font.size.display` | none (rename) |
| `--space-6?` n/a; card `32px` | `space.6` (36px) | layout shift +4px |
| `--space-2: 12px` | `space.2` (6px) label gap | layout shift −6px |
| `--space-3: 16px` | `space.3` (10px) | field gaps tighten |
| `--space-5: 21.28px` | `space.5` (20px) | remove off-scale value |
| `--radius-xs: 16px` | `radius.xs` (8px) | rounding change |
| `--radius-md: 9999px` | `radius.pill` | rename |
| `--color-border-strong: 0.24` | `0.36` | **a11y fix** |
| `--motion-duration-instant: 120ms` | `200ms` | timing change |
| brand `color.text.secondary: #4446e1` | `color.accent.brand` | **must not be text** |

---

## 3. Component-level rules

Every interactive component **must** define: `default, hover, focus-visible, active, disabled, loading, error`. Missing any state is a blocker.

### 3.1 Page shell (`.auth`)

- **Anatomy:** full-viewport grid, single centered child, `background: color.surface.base`.
- **Rules:** `min-height: 100vh`; centering via grid `place-items: center`; page padding `space.4` (≥481px) / `space.3` (≤480px). Content **must** remain reachable when the viewport is shorter than the card (allow vertical scroll; no clipping).
- **Edge case:** on viewports < ~420px tall the card **must** scroll, not overflow behind the fold; `min-height` **should** be `100dvh` where supported.

### 3.2 Auth card (`.auth__card`)

- **Anatomy:** `surface.muted` container → brand → title → subtitle → alert slot → form → footnote.
- **Variants:** default only. No accent/dark variants.
- **States:** static container; **must not** be interactive.
- **Rules:** `max-width: 400px`, `width: 100%`, `border: 1px solid color.border.subtle`, `radius.sm`, `padding: space.6` (→ `space.5` ≤480px), optional `shadow.2`.
- **Responsive:** at ≤480px the card **should** go edge-to-edge within `space.3` page padding; `max-width` **must** still cap on large screens.
- **Edge case:** very long flash content **must** wrap and grow the card; the card **must not** set a fixed height.

### 3.3 Brand lockup (`.auth__brand` / `.auth__logo`)

- **Anatomy:** centered logo image with `alt` = product name.
- **Rules:** logo height `40px`, width auto; `alt` **must not** be empty and **must not** duplicate the `<h1>` ("Intelligencerai" is acceptable, `alt=""` only if the h1 already names the product — here keep text).
- **Edge case:** if the logo 404s, the `width`/`height` attributes **must** preserve layout (no shift).

### 3.4 Heading & subtitle (`.auth__title` / `.auth__subtitle`)

- **Rules:** exactly one `<h1>` per page; `id="login-heading"` **must** remain the `aria-labelledby` target of the card section. Title uses `font.size.display` + `font.weight.strong` + `color.text.tertiary`, centered. Subtitle uses `font.size.xs`, `color.text.primary`, centered.
- **Edge case:** long translations **must** wrap; no truncation, no ellipsis.

### 3.5 Alert / flash (`.flash`)

- **Anatomy:** `<ul role="alert">` list of messages.
- **States:** hidden (no messages) / visible (≥1 message). Visible state uses `color.text.error` on `color.surface.raised`, `1px solid color.border.error`, `radius.xs`, `padding: space.2 space.3`.
- **Rules:** `role="alert"` **must** remain so it is announced immediately; announce **must** happen once (do not duplicate via JS). Message list **must** be ordered and each `<li>` a complete sentence.
- **Accessibility note:** `role="alert"` is assertive — for non-urgent info **should** prefer a polite region.
- **Edge case:** multi-message and long-message content **must** wrap within the card; the alert **must not** overlap the form.

### 3.6 Text field (`.field__input`) — email & password

- **Anatomy:** `label` → control wrapper → `input` → inline error `<p>`; password adds an affordance toggle (§3.7).
- **Variants:** email (`type=email`, `inputmode=email`, `autocomplete=email`), password (`type=password`, `autocomplete=current-password`, `minlength=8`).
- **States (all required):**

| State | Signal | Tokens |
|---|---|---|
| default | border strong, fill base | `color.border.strong`, `color.surface.base`, text `color.text.tertiary` |
| hover | border brightens | border `color.text.primary` |
| focus-visible | 2px ring, offset 2 | `color.focus.ring` |
| active | inherits focus | — |
| disabled | dimmed, no pointer | `opacity: 0.5`, `cursor: not-allowed` |
| loading | inputs `readonly` + `aria-busy` on form | see §3.9 |
| error | red border + visible message | `color.border.error`, `color.text.error` |

- **Rules:** min height `44px` (touch target ≥44×44); padding `0 space.3`; radius `radius.xs`; font `font.size.sm`; placeholder uses `color.text.primary`. Error **must** be programmatically linked via `aria-describedby` and `aria-invalid="true"`. When error state is shown, the border **and** the message **must both** change (never color-only independent of text).
- **Keyboard:** `Tab` enters/leaves; `Enter` submits the form; browsers' native validation **must not** be relied on (`novalidate` stays) — errors are rendered in DOM.
- **Pointer/touch:** tap focuses and opens the correct mobile keyboard (`inputmode`); long-press selection **must** work.
- **Responsive:** field width `100%`; the password field reserves right padding for the toggle (`space` + 44px) so text **must not** run under the icon.
- **Edge cases:** long email **must** scroll horizontally inside the input (no layout break); paste of trailing spaces **should** be trimmed before validation; empty submit **must** focus the first invalid field.

### 3.7 Password visibility toggle (`.field__toggle`)

- **Anatomy:** icon-only `<button type="button">` inside the password control.
- **States:** default (icon `color.text.primary`) / hover (`color.overlay.hover`) / focus-visible (ring) / pressed (`aria-pressed="true"`, icon `color.text.tertiary`) / disabled (inherits field disabled).
- **Rules:** target ≥44×44px → the current `34px` **should** grow to ≥44px or gain invisible hit padding; `aria-pressed` **must** reflect state; `aria-label` **must** toggle between "Показать пароль" / "Скрыть пароль"; `aria-controls` **must** point to the password input. Icon **must** be `aria-hidden`.
- **Keyboard:** reachable by `Tab`; `Space`/`Enter` toggles; focus **must** stay on the toggle (no jump to input).
- **Pointer/touch:** single tap toggles; **must not** submit the form (`type="button"`).
- **Edge case:** toggling **must not** clear the typed value or move the caret.

### 3.8 Checkbox (`.checkbox` — «Оставаться в системе»)

- **Anatomy:** native `<input type="checkbox">` + `<label>` text, one row.
- **States:** unchecked / checked / hover / focus-visible / disabled.
- **Rules:** control ≥44px touch target **should** be met via label hit area; `accent-color: color.text.tertiary`; label text `font.size.xs`, `color.text.primary`. Label **must** be associated via `for`/`id`.
- **Keyboard:** `Space` toggles; `Tab` enters/leaves. Focus ring **must** be visible on the control.
- **Edge case:** long label **must** wrap without detaching from the box (alignment to first line).

### 3.9 Buttons (`.btn`) — 2 on page

**Primary** («Продолжить») and **secondary** (SSO slot, if rendered).

- **Anatomy:** optional leading icon (20×20) + label; `inline-flex`, centered, full width.
- **States (all required):**

| State | Primary | Secondary |
|---|---|---|
| default | bg `control.primary.bg`, text `text.inverse` | transparent, border `border.strong`, text `text.tertiary` |
| hover | bg `control.primary.bg.hover` | bg `overlay.hover` |
| focus-visible | ring `focus.ring` | ring `focus.ring` |
| active | bg `control.primary.bg.active` | bg `overlay.active` |
| disabled | `opacity:0.5`, `cursor:not-allowed`, no pointer events | same |
| loading | spinner `::after`, label hidden, `aria-busy="true"`, `cursor:progress` | same |
| error | n/a (use alert) | n/a |

- **Rules:** min height `44px`; `radius.pill`; `padding: 0 space.3`; label `font.size.sm`; primary label weight `font.weight.strong`. Full width **must** be `100%` in this layout.
- **Keyboard:** `Enter`/`Space` activates; **must not** trap focus; loading **must** move focus per §4 (keep on button, announce busy).
- **Pointer/touch:** ≥44px height; hover affordance is additive, not required to discover the action.
- **Loading edge cases:** loading **must** be reversible on request failure (remove `is-loading`, restore label, re-enable); spinner **must** respect reduced-motion (never a hard spin under `reduce` — swap to a non-animated busy indicator or static text).
- **Responsive:** unchanged; **must not** shrink below 44px height.

### 3.10 Links (`.link`) — primary 1

**«Забыли пароль?»** (+ optional «Создать аккаунт»).

- **Anatomy:** text link, optional in a row with a label.
- **States:** default `color.text.secondary` / hover `color.text.tertiary` + underline / focus-visible ring (`radius.xs` rounding) / active inherits / visited **must not** change color (token has no visited variant).
- **Rules:** `font.size.xs`; underline on hover is required — **must not** rely on color alone (hover state difference is color + underline). Link text **must** be descriptive ("Забыли пароль?", not "Нажмите здесь").
- **Keyboard:** `Enter` activates; `Tab` order follows DOM (email → password → toggle → remember → forgot → submit → create account).
- **Touch:** inline text link — hit area **should** be padded to ≥44px tall where it stands alone in a row.
- **Edge case:** links **must** have a real `href`; `href="#"` (current placeholder) **must** be replaced before ship or rendered as disabled text.

### 3.11 Divider (`.divider`)

- **Anatomy:** centered label flanked by two rules.
- **Rules:** rules `1px color.border.subtle`; label `font.size.xs`, `color.text.primary`; vertical margin `space.4`. **Must not** be used as a section separator inside a single-provider form.

### 3.12 Footnote (`.auth__footnote`)

- **Rules:** `font.size.xs`, `color.text.primary`, centered, top margin `space.5`; embedded link inherits size. **Must** be the last focusable content in tab order.

### 3.13 Navigation (1)

The brand lockup + card act as the only navigation surface. The page **must not** add a nav bar; the logo **must not** be a link unless it returns to a meaningful destination (a logo linking to the same login page is prohibited).

---

## 4. Accessibility requirements (testable)

| # | Requirement | Pass check |
|---|---|---|
| A-01 | Every interactive element has a visible focus indicator | Tab through all: each shows 2px `color.focus.ring`, offset 2, never removed |
| A-02 | Focus ring contrast ≥3:1 vs adjacent color | `#ededed` on `#000` = 17.9:1 → pass |
| A-03 | All body text ≥4.5:1 | §2.1 table all pass |
| A-04 | Non-text UI boundaries ≥3:1 (1.4.11) | Input border must be ≥`0.36` white on black; verify composited ≥3:1 |
| A-05 | Inputs have programmatic labels | `email`/`password` resolve to `<label for>`; DOM inspector shows accessible name |
| A-06 | Errors are announced and linked | `aria-invalid="true"` + `aria-describedby` → error `<p>`; screen reader reads message on focus |
| A-07 | Alert is announced | `role="alert"` on flash; message read without focus move |
| A-08 | Password toggle state is conveyed | `aria-pressed` flips; `aria-label` updates; `aria-controls` = password id |
| A-09 | No color-only meaning | Error uses border **+** text; link hover uses color **+** underline |
| A-10 | Touch targets ≥44×44px | Password toggle and links padded to ≥44px effective target |
| A-11 | Reduced motion honored | With `prefers-reduced-motion: reduce`, no spinner rotation / transitions |
| A-12 | Zoom to 200% without loss | Reflow at 200% and 320px width; no horizontal scroll, no clipped controls |
| A-13 | Language set | `<html lang="ru">` present |
| A-14 | Loading is announced | Submit sets `aria-busy="true"`; failure clears it and restores focus |
| A-15 | Heading structure | Exactly one `<h1>`; card `aria-labelledby` points to it |
| A-16 | Focus order is logical | Email → Password → Toggle → Remember → Forgot → Submit → Create account |

**Keyboard map (required)**

| Key | Action |
|---|---|
| `Tab` / `Shift+Tab` | move through A-16 order |
| `Enter` (in field) | submit form |
| `Space` | toggle checkbox / toggle password button |
| `Enter` / `Space` (on button) | activate submit |
| `Escape` | no handler required; **must not** close or lose data |

**Pointer/touch:** every action reachable by tap; hover-only affordances prohibited; no gesture-only interactions.

---

## 5. Content and tone standards

**Voice:** concise, confident, implementation-focused. Russian. Sentence case. No exclamation marks, no marketing fluff, no blame ("Ошибка" alone is prohibited; say what to do).

**Field / control labels**

| Use | Avoid |
|---|---|
| «Электронная почта» | «Email адрес» (mixed script) |
| «Пароль» | «Введите пароль» as label (that's a placeholder) |
| «Оставаться в системе» | «Запомнить меня» (ambiguous scope) |
| «Продолжить» | «Войти» when the next step may be MFA |
| «Показать пароль» / «Скрыть пароль» | «Глаз» / icon-only with no label |

**Errors (label + guidance, never blame)**

| Context | Copy |
|---|---|
| Invalid email | «Введите корректный адрес электронной почты.» |
| Missing password | «Введите пароль.» |
| Too short | «Пароль должен содержать не менее 8 символов.» |
| Auth failed | «Неверный адрес электронной почты или пароль.» |

**Empty / loading / links**
- Subtitle: «Введите данные вашей учётной записи, чтобы продолжить.»
- Footnote: «Впервые в Intelligencerai? Создать аккаунт»
- Loading label (a11y text): «Выполняется вход…»
- **Must not** say "Произошла ошибка". Always actionable.

---

## 6. Anti-patterns and prohibited implementations

- **Must not** ship raw hex / px inside component CSS — only semantic tokens.
- **Must not** use `color.accent.brand` (`#4446e1`) for any text or icon: 3.2:1 fails AA.
- **Must not** keep the input border at `rgba(255,255,255,0.24)` — fails 1.4.11.
- **Must not** remove, hide, or thin the focus ring; no `outline: none` without a replacement.
- **Must not** signal errors with color alone; no red border without a message.
- **Must not** use a placeholder as a label (disappears on input, fails A-05).
- **Must not** use `href="#"` links in production — dead actions must be real or honestly disabled.
- **Must not** introduce a second "instant" duration, off-scale spacing (`21.28px`), or a one-off heading size (`30px` inline).
- **Must not** exceed `font.size.sm` in body/controls; the display size is title-only.
- **Must not** animate the spinner under `prefers-reduced-motion: reduce`.
- **Must not** add marketing content, nav bars, or social-login providers beyond the existing SSO slot in the auth flow.
- **Must not** disable native copy/paste on password fields.

---

## 7. QA checklist

**Tokens**
- [ ] No raw hex/px in component rules; all resolve to §2 tokens.
- [ ] `color.border.strong` = `rgba(255,255,255,0.36)`+ (composited ≥3:1).
- [ ] `radius.xs` = 8px; `radius.pill` used for controls; display token replaces inline `30px`.
- [ ] Single `motion.duration.instant` value; reduces under reduced-motion.

**States**
- [ ] Button: default/hover/focus/active/disabled/loading verified; loading reversible.
- [ ] Inputs: default/hover/focus/disabled/error verified; error shows border + text.
- [ ] Toggle: pressed/unpressed + label swap verified.
- [ ] Checkbox: focus ring visible; `Space` toggles.
- [ ] Link: hover underline + focus ring; no visited-color drift.

**Accessibility**
- [ ] A-01…A-16 all pass with a screen reader + keyboard only.
- [ ] 200% zoom and 320px width: no horizontal scroll, no clipping.
- [ ] Contrast re-measured after any visual token change.
- [ ] Alert announced once; not duplicated by JS.

**Content**
- [ ] All copy matches §5; labels descriptive; errors actionable.
- [ ] No `href="#"`; no "Произошла ошибка".

**Responsive / edge cases**
- [ ] ≤480px: card padding `space.5`, page padding `space.3`, no overflow.
- [ ] Short viewport: card scrolls, nothing clipped.
- [ ] Long email/error/label wrap correctly; card grows.
- [ ] Logo failure preserves layout.

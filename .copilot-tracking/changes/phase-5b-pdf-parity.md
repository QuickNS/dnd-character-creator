<!-- markdownlint-disable-file -->
# Phase 5b — Printable Sheet (PDF Parity) (Changes Log)

**Status:** COMPLETE — awaiting user approval to proceed to Phase 6 (PWA + persistence).

## Summary

Added a printable, pixel-precise character sheet at `/sheet/pdf` that
mirrors the legacy Jinja `templates/character_sheet_pdf.html` view.
Renders an 8.5×11in canvas with the official sheet PNG background and
overlays read-only fields at the same absolute positions as the
legacy template, so `window.print()` produces the same output.

Read-only by design: the React SPA's source of truth is the wizard.
Edit in the wizard, print here.

Desktop-only gate: viewports < 900px get a friendly message instead
of the (intentionally non-responsive) absolute layout.

## Files Added

- `frontend/src/pages/SheetPdf.tsx` — full printable sheet:
  - Toolbar (back to summary, print).
  - Page 1: header, level/size/PB, AC/initiative/speed/HP/hit dice/passive,
    six ability blocks (score, modifier, save proficiency + bonus,
    skill proficiency + bonus), six weapon-or-cantrip rows
    (weapons first, then damage cantrips from
    `/api/v1/character/derived?view=damage_cantrips`), armor proficiency
    checkboxes, weapon/tool proficiency lists, three feature columns
    (class / species / feats).
  - Page 2: background image only (legacy template's page-2 fields
    were also blank — kept for parity).
  - Inlined stylesheet duplicates the legacy field selectors verbatim.
- `frontend/public/pdf_template/sheet1.png`,
  `frontend/public/pdf_template/sheet2.png` — copied from
  `static/pdf_template/` so Vite serves them at `/pdf_template/`.

## Files Modified

- `frontend/src/app/router.tsx` — registered `/sheet/pdf` route.
- `frontend/src/pages/Sheet.tsx` — added "Printable sheet →" link in
  the page header.
- `frontend/vite.config.ts` — added
  `workbox.globIgnores: ["**/pdf_template/**"]` so the 5.7 MB of sheet
  PNGs are not precached by the PWA service worker (they are still
  served on-demand from `/pdf_template/`).

## Verified

- `npm run typecheck` clean.
- `npm run build` clean. Sheet PNGs confirmed absent from
  `dist/sw.js` precache; bundle is ~410 kB JS / ~27 kB CSS.

## Pending / Next Actions

- Present Phase 5b for user approval.
- **Phase 6**: Vite PWA plugin tuning, offline asset strategy, and
  localStorage persistence with a forward-compatible migration shim
  for a future Postgres backend.

## Suggested Commit Message

```text
feat(frontend): Phase 5b — printable PDF-parity character sheet

- Add /sheet/pdf route rendering an 8.5×11in canvas with the
  official sheet PNG background and read-only overlay fields at
  the same positions as templates/character_sheet_pdf.html.
- Pull weapons + damage cantrips from /api/v1/character/build and
  /api/v1/character/derived?view=damage_cantrips.
- Desktop-only gate (<900px shows a friendly message).
- Toolbar with Print to PDF (window.print()) and back link.
- Copy sheet1.png/sheet2.png into frontend/public/pdf_template/ so
  Vite serves them; exclude from PWA precache via workbox.globIgnores.
- Verified: npm run typecheck clean, npm run build clean.
```

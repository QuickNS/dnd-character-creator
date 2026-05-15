<!-- markdownlint-disable-file -->
# Phase 6 — PWA + Persistence (Changes Log)

**Status:** COMPLETE — awaiting user approval to proceed to Phase 7
(cutover + legacy removal).

## Summary

Brought the React SPA to a "real PWA" state and replaced the
single-character localStorage assumption with a multi-character roster
backed by a swappable persistence adapter. The adapter interface is
designed to be the seam where a future Postgres + auth backend plugs
in without touching the rest of the app.

## Files Added

- `frontend/src/lib/persistence.ts` — `PersistenceAdapter` interface,
  `LocalStoragePersistence` implementation, versioned migration shim
  (`CURRENT_VERSION` + `MIGRATIONS` table), `getPersistence()`
  singleton, `summarizeChoices()` and `newEntryId()` helpers.
- `frontend/src/store/rosterStore.ts` — Zustand store wrapping the
  adapter (`load`, `saveCurrent`, `delete`).
- `frontend/src/components/UpdatePrompt.tsx` — uses
  `virtual:pwa-register/react`'s `useRegisterSW` to surface
  "new version available" reload prompts and a transient
  "offline ready" toast; checks for updates every hour.
- `frontend/src/components/OfflineIndicator.tsx` — small status pill
  driven by `navigator.onLine`.

## Files Modified

- `frontend/src/store/characterStore.ts` — added `version: 1` and a
  defensive `migrate` callback to the `persist` middleware so the
  in-progress wizard blob is forward-migratable.
- `frontend/src/app/providers.tsx` — mount `<UpdatePrompt />` and
  `<OfflineIndicator />` alongside the router.
- `frontend/src/pages/Home.tsx` — added a "Saved Characters" section:
  - Save current wizard progress with a custom name (defaults to the
    in-progress `character_name`).
  - List of saved entries with summary, save timestamp, Load, Delete.
  - Inline confirmation flash on save; window confirm on delete.

## Verified

- `npm run typecheck` clean.
- `npm run build` clean (~420 kB JS / ~29 kB CSS; PWA precache 44
  entries / ~19 MB — sheet PNGs still excluded from precache via the
  Phase 5b `globIgnores`).

## Pending / Next Actions

- Present Phase 6 for user approval.
- **Phase 7**: Serve the built React bundle from Flask at `/`,
  retire the legacy Jinja routes that the SPA now covers, and tighten
  CORS to production-only posture.

## Forward-compat notes for Postgres backend

When a remote backend is ready:
1. Add `RemotePersistence implements PersistenceAdapter` that calls
   `/api/v1/roster/*` (load/save/delete/clear).
2. Swap `getPersistence()` to return the remote adapter when
   authenticated, falling back to `LocalStoragePersistence` for
   anonymous sessions (or layer them: write-through cache).
3. Bump `CURRENT_VERSION` and add the corresponding entry to
   `MIGRATIONS` whenever a stored shape changes; the loader walks
   versions sequentially.

## Suggested Commit Message

```text
feat(frontend): Phase 6 — PWA prompts + multi-character persistence

- Add PersistenceAdapter abstraction (frontend/src/lib/persistence.ts)
  with LocalStoragePersistence implementation and a versioned
  migration shim (CURRENT_VERSION + MIGRATIONS table) so the storage
  backend can swap to Postgres later without touching consumers.
- Add rosterStore (Zustand) for save/load/delete of multiple
  character snapshots; surface in Home page as a "Saved Characters"
  section with name, summary, timestamp, Load and Delete.
- Bump character store with persist `version: 1` + defensive
  `migrate` callback.
- Add UpdatePrompt using virtual:pwa-register/react: shows a Reload
  toast when a new SW is waiting and a transient "offline ready"
  toast on first install; auto-checks for updates hourly.
- Add OfflineIndicator pill driven by navigator.onLine.
- Verified: npm run typecheck clean, npm run build clean.
```

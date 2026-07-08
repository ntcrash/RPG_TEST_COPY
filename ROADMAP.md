# Megitech RPG — Automation Roadmap

Living backlog of work sized for autonomous/agent-driven execution. Generated 2026-07-07 from `README.md`, `CHANGELOG.md`, `HELP.md`, and a repo scan of `main.py` + `Code/`.

## How to work this list

- Gitflow: branch every item off `develop` as `feature/<slug>` (or `hotfix/<slug>` for P0 bugs), never commit directly to `main` or `develop`.
- Version every merge: bump the version in `CHANGELOG.md` following the existing `MM/DD/YYYY - vX.Y.Z` convention and tag releases going forward (only `v1.3.0` and `v1.4` are currently tagged, despite releases through v1.7.4 — start tagging again from the next release).
- Push every commit to `origin` per project convention.
- Check an item off by moving it to a `## Done` section with the commit hash and date, not by deleting it.

---

## P0 — Known bugs (carried from CHANGELOG.md ToDo)

1. **Dying doesn't take credits** — player death should deduct credits per existing design intent; currently doesn't. Locate death handling in `Code/enhanced_combat_integration.py` / `Code/combat_system.py`.
2. **Main game sound is broken** — investigate music/sound loading in `main.py` audio init path; README notes a fallback system exists for missing files, so this may be a path or trigger bug rather than missing assets.

## P1 — Repo hygiene (blocks safe automation)

3. **Add a `.gitignore`** — none exists today. At minimum ignore `**/__pycache__/`, `*.pyc`, `venv/`, `.idea/`, `.DS_Store`.
4. **Untrack committed `.pyc` files** — 13 compiled bytecode files under `Code/__pycache__/` are currently tracked in git and show up as noisy diffs on every run (`git rm -r --cached Code/__pycache__`). Do this in the same commit as #3.
5. **Decide on save-file tracking policy** — `Characters/*.json` and `SaveProgression/*.json` are tracked in git and change on every local playtest (seen in current uncommitted diff: `nora.json`, `vozy.json`, `progression_Nora.json`). Either gitignore actual save state and commit only fixture/sample data, or explicitly document that these are meant to be versioned as save snapshots.
6. **Remove/gate debug output** — 19 `print(f"DEBUG: ...")` statements in `Code/combat_system.py` (14) and `Code/settings_system.py` (5) run unconditionally. Wrap behind a `DEBUG` flag in `settings_system.py` or Python's `logging` module at DEBUG level.
7. **Add `requirements.txt`** — no dependency manifest exists; README states pygame 2.6.1 on Python 3.11 as the only real dependency, but pinning it removes an onboarding/automation guesswork step.

## P2 — Testing & CI (enables safe automated changes)

8. **Add a minimal test suite** — no `tests/` directory or test framework currently exists. Start with unit tests for pure-logic modules least coupled to Pygame's display: `Code/crafting_system.py` (recipe/material logic), `Code/level_system.py` (progression/unlock logic), `Code/combat_system.py` damage/hit-chance calculations (`calculate_spell_damage`, hit chance functions flagged by the DEBUG prints above — good coverage target).
9. **Add a CI workflow** (GitHub Actions) — run the new test suite plus a `python -m py_compile` / lint pass on push and PR against `develop` and `main`, matching the gitflow branches already in use.
10. **Add a linter config** (`ruff` or `flake8`) — codebase is large (main.py alone is ~1,950 lines) with no enforced style; a lint pass would catch dead code and unused imports cheaply before larger refactors.

## P3 — Documentation debt

11. **Sync `README.md` architecture section with actual code** — README's "Recent Changes" section is frozen at a 2025-09-08 Replit import note; the file-structure list references `game_states.py` as entry point, but that file was renamed to `main.py` back in v1.6 per CHANGELOG. Update README to reflect current `main.py` + `Code/` module layout.
12. **Reconcile version history** — CHANGELOG.md's early history (v20–v29, "GUI Client for Multiplayer") describes a multiplayer/server architecture (`NetworkManager_Class.py`, `Server_v1`–`v3`) that no longer appears in the current single-player codebase. Either archive that history clearly as "legacy multiplayer branch, discontinued" or confirm if multiplayer is still a live goal — affects whether future roadmap items should plan around a server component.

## P4 — Feature ideas (lower priority, larger scope)

13. **Tag past releases retroactively** — v1.5–v1.7.4 shipped without git tags; consider tagging historical commits (`git tag -a v1.7.4 7540cc2`) so `git describe` and release automation have a clean baseline.
14. **Automated save-file migration check** — with a versioned save schema (`Characters/*.json`), add a lightweight migration/validation step so old saves don't silently break on load after combat/stat formula changes (e.g., the v1.7.3 spell-damage level-scaling change).
15. **Difficulty/balance regression checks** — CHANGELOG shows multiple past hotfixes for difficulty multiplier and stat scaling bugs (v1.4.1, v1.7.3). Once #8's test suite exists, add regression tests pinning expected damage/AC output for a few reference character/enemy stat combos to catch future balance regressions automatically.

---

## Done

_(move completed items here with commit hash + date)_

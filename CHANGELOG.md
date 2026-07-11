# Changelog
All notable changes to this project will be documented in this file.

## - ToDo
- Fix the 42 Ruff findings surfaced by the linter (unused imports, unused variables, unused loop vars, placeholder-less f-strings, 1 redefinition) — deferred from v2.1.2 to keep that change config-only. Once fixed, make the CI `ruff check` step blocking (remove `continue-on-error` in `.github/workflows/ci.yml`).

## 07/10/2026 - v2.5.0
### ⛏️ Resource-node harvest feedback — ready vs. depleted at a glance (roadmap P5 #26)
**Rocks, metal veins, streams, and brush now clearly show whether they can be harvested right now or are still regrowing**, extending the harvest-state feedback that trees got in v2.4.0 to every gathering node. Previously these nodes only did a crude binary colour swap (full colour vs. one dark shade) with no regrowth cue and no "you can gather this" indicator, so a depleted node and a ready one were easy to confuse from a distance.
- **Shared `HarvestableNode` mixin** (`Code/ui_components.py`) — Rock, Metal, Stream, and Brush now inherit one place for the harvest-feedback math: `regrow_fraction()` (0.0 just-harvested → 1.0 ready, mapped over the respawn timer, mirroring `Tree`), a `_lerp_color` helper, a `harvest_pulse()` sine used for the ready glow, and `draw_ready_marker()` which paints a **pulsing sparkle above any harvestable node** (and nothing on a depleted one).
- **Depleted → ready tween per node** — instead of snapping between two colours, each node now interpolates from a dark "spent" appearance back to its full colour as it regrows: rock/metal refill their ore colour (and rock shrinks slightly while spent), a stream runs dark and murky then brightens back to clear blue, and brush greens up and fills back out (foliage radius scales with regrowth). The pulsing ready-sparkle only appears once a node is fully harvestable, so players can tell ready nodes from regrowing ones without walking up to each one.
- **Tests** — added `tests/test_resource_node_feedback.py` (13 tests): regrow-fraction mapping + clamping across all four node types, colour-lerp endpoints/midpoint/clamp, `harvest_pulse` range and oscillation, and a headless draw pass in both the ready and depleted states plus that the ready-marker is drawn only when harvestable (rendered through the `Code.gfx` shim, no GPU).
- **Also** — removed a pre-existing dead `flow` local in `Stream.draw` (one of the deferred Ruff findings) while editing that block; `Code/ui_components.py` + the new test are Ruff-clean.
- **Verification**: `py_compile` clean; Ruff clean on the touched files; full suite **155 → 168** green (6 skipped when arcade/display absent).
- **Result**: roadmap **P5 #26 (resource-node visual feedback) is done.**

## 07/10/2026 - v2.4.0
### 🌳 Animated trees — swaying canopies + harvest-state colour (roadmap P5 #25)
**Trees now sway naturally and visibly wither and regrow with their harvest state**, replacing the old flat single-circle canopy that just turned solid grey when depleted.
- **Swaying animation** (`Code/ui_components.py` `Tree.draw`) — the canopy now sways with a primary breeze plus a slower gust term and a gentle vertical bob, while the trunk stays rooted. Each tree gets a stable per-tree `sway_phase` (seeded from its world x) and a mild `sway_strength` variation so a forest no longer sways in lock-step. Pine layers lean with the wind (upper layers lean more); leafy trees use a fuller multi-blob canopy with a black outline and a sun-catch highlight blob instead of one flat circle.
- **Colour + size by harvestable status** — added `regrow_fraction()` (0.0 just-harvested → 1.0 full, mapped over the respawn timer) and a `_lerp_color` helper. A depleted tree now starts small and withered grey-brown (`leaf_withered`) and **tweens back** to healthy green (`leaf_color`/`leaf_highlight`) and full size as its respawn timer counts down — so the player can read a tree's harvest state and regrowth progress at a glance. Sway amplitude also scales with growth, so a fresh sapling barely stirs while a full tree sways widely.
- **Tests** — added `tests/test_tree_animation.py` (11 tests): regrow-fraction mapping + clamping, canopy colour interpolation endpoints/midpoint, distinct per-tree sway phase, sway varying across frames, and a headless draw pass across all three tree types in both healthy and mid-regrow states (rendered through the `Code.gfx` shim, no GPU).
- **Verification**: `py_compile` clean; full suite **144 → 155** green (6 skipped when arcade/display absent).
- **Result**: roadmap **P5 #25 (animated trees) is done.**

## 07/10/2026 - v2.3.6
### 🔑 Define K_F1 in the shim — fix keypress crash on the pygame-free venv
**A keypress in combat no longer crashes the game with `AttributeError: module 'Code.gfx' has no attribute 'K_F1'`.** `main.py`'s key handler compares against `pygame.K_F1` (the instruction-toggle key), but `Code/gfx.py` never defined `K_F1`, so the lookup fell through the shim's `__getattr__` to real pygame. That only *appeared* to work because the old external venv happened to have pygame installed as a fallback; on the new pygame-free Arcade venv (Python 3.12 + arcade 3.3), the fallback found nothing and raised on **every** keypress that reached the F1 check.
- **Root cause** — the pygame→Arcade key-constant port (v2.1.x) inventoried "the subset actually referenced" but missed `K_F1`. An audit of every `pygame.<attr>` the game touches at runtime, tested with pygame forced absent, confirmed `K_F1` was the *only* remaining gap — all other constants/attributes (Rect, Surface, draw, event, mixer, K_0-9, arrows, …) resolve natively.
- **Fix** (`Code/gfx.py`) — defined the full `K_F1`–`K_F12` SDL keycode row natively so the shim is self-sufficient and this class of gap can't recur. (`arcade_app.py`) — mapped `arcade.key.F1` → `gfx.K_F1` so the toggle actually fires under the Arcade backend, not just avoids the crash.
- **Verification**: reproduced the crash with pygame absent, confirmed fixed; full suite **144/144** green on the Python 3.12 / arcade 3.3.3 venv (pygame not installed).

## 07/10/2026 - v2.3.5
### 🎯 Selection highlight no longer slices through the menu text
**The combat action and item menu selection boxes now fully wrap the highlighted row's text.** The highlight rectangle was 20px tall around a 24px font, drawn as a 1–2px outline, so its bottom border ran straight through the lower half of the selected line's glyphs — reading like a strikethrough (most visible on "Cast Spell" in the action menu). Rows were also pitched at only 25px, nearly touching.
- **Action menu** (`Code/enhanced_combat_system.py`) — row pitch 25→30px and highlight box 20→28px, positioned 3px above the text so the 24px glyphs sit fully inside the border. Panel grown 150→175px to hold the taller rows and still clear the combat log at y=455.
- **Item menu** — highlight box 26→28px at a -3px offset (was -2) for the same full-wrap; row pitch already 30px from v2.3.3.
- **Store** (`Code/inventory_system.py`) — unchanged: its highlight is a *filled* bar with text drawn on top, so no border ever crossed the glyphs.
- **Verification**: re-rendered the action/item menus headlessly (selected row = "Cast Spell" / "Greater Health Potion") and confirmed the highlight cleanly encloses the text; full suite **144/144** green.

## 07/10/2026 - v2.3.4
### 🐌 Stop real pygame from loading on every launch (startup / repo hygiene)
**The Arcade backend no longer imports real `pygame` at all during a normal play session.** `Code/gfx.py` — the Arcade-native drawing/audio/timing shim — was importing real pygame *eagerly* at module load (`import pygame as _pygame`) purely to back a handful of never-exercised `__getattr__` fallbacks (`locals`, `Color`, `Vector2`, `mouse`, …). Since v2.2.5 the game drives everything through the shim, so that eager import bought nothing but pygame's SDL load cost and its support-prompt banner on every startup — which is exactly why "why is pygame launching under the Arcade backend?" kept showing up. (`pygame` is no longer even a declared dependency as of v2.2.5, so on a clean install the eager `try/except` was also silently swallowing an `ImportError` on every launch.)
- **Lazy, cached, banner-silenced import** — replaced the module-load `import pygame` with `_get_pygame()`, which imports real pygame only the first time a fallback actually fires, caches the result (and a `_pygame_tried` flag so a failed import isn't retried on every miss), and sets `PYGAME_HIDE_SUPPORT_PROMPT=1` before importing so no banner prints. Both `__getattr__` hooks (module-level and `_KeyModule`) now route through it.
- **Effect**: a normal Arcade play session never imports pygame; nothing the game exercises at runtime hits a fallback, so `_get_pygame()` is never called. The opt-in real-pygame backend (`MEGITECH_BACKEND=pygame`, for devs who install pygame themselves) is unaffected — it still goes through `Code/backend.py`, not this shim path.
- **Verification**: `py_compile` clean; full suite **144/144** green (6 skipped when arcade/display absent); the 66 `tests/test_gfx.py` shim tests still pass with pygame absent.
- **Also**: gitignored `*.log` / `importtime.log` and removed a stray `importtime.log` profiling artifact (`python -X importtime` output) that had been accidentally git-added.

## 07/10/2026 - v2.3.3
### 🧩 Fix overlapping in-game menus (roadmap P5 #34)
**Combat, spell, item, and store sub-menus no longer overlap the panels beneath them.** Each menu was drawn at a fixed y-coordinate sized for a shorter list, so a full list ran under the combat log, the control-instruction bar, or (in Arcade) the leftover migration dev overlay.
- **Combat log** (`Code/enhanced_combat_system.py`) — moved the log background + text down from y=390/400 to y=455/463, freeing the upper area so the action / spell / item sub-menus above it have room to grow.
- **Spell menu** — moved the dynamically-sized spell box from y=210 to y=190. An aspect exposes at most 3 spells (levels 1/3/5) → worst case 3×45+80 = 215px tall, so the box (bottom ~y=405) and its instruction bar now clear the log at y=455.
- **Item menu** — started the potion list at y=190 and introduced an explicit 30px `row_pitch` (was a hardcoded 35px that overran on long potion lists), tightening the selection highlight to 26px so even a 7+ potion inventory stays above the combat log.
- **Store** (`Code/inventory_system.py`) — capped `EnhancedStoreManager.items_per_page` from 12 → 9. Rows list from y=150 at a 30px pitch with a name + description line each; 12 rows ran to ~y=510 and collided with the control instructions (~y=470). Nine rows end ~y=420; PgUp/PgDn scroll the remainder.
- **Arcade dev overlay** (`arcade_app.py`) — the migration-era banner / state-readout / footer-hint drew on top of the live combat HUD (e.g. the "ESC: Forfeit" line and combat log) now that the pygame→Arcade migration is complete (v2.2.5). It is now OFF by default and only rendered when `MEGITECH_DEBUG` is set to a truthy value.
- **Verification**: `py_compile` clean; full suite **144/144** green (6 skipped when arcade/display absent).
- **Result**: roadmap **P5 #34 (fix menu items overlapping) is done.**

## 07/10/2026 - v2.3.2
### 🚪 Window close & Quit now fully end the app (roadmap P5 #24)
**Every exit route — the window "X" button, the Quit menu item, and Escape — now cleanly terminates the whole program.** Under the Arcade entry point (`arcade_app.py`) exit handling was inconsistent: `on_close()` called `_shutdown()` and then `super().on_close()`, which closed the already-closed window a second time (raising on the dead window), and `_shutdown()` used `arcade.close_window()` with no re-entry guard — so a stray second `on_close` from pyglet during teardown could save progression twice or error, and on some setups a lingering background (audio) thread kept the interpreter alive after the window vanished, leaving the app "not really closed."
- **One idempotent shutdown path** — `on_close()` (window X / OS close) now simply delegates to `_shutdown()` and no longer calls `super().on_close()` (which would double-close). `_shutdown()` guards against re-entry via `self._closing`, so the window X, the Quit menu item (`handle_keypress` → `return False` → `on_key_press` → `_shutdown`), and Escape all funnel through the same routine exactly once.
- **Actually ends the program** — `_shutdown()` now saves progression once (failure-tolerant), calls `self.close()` to close the window, then `arcade.exit()` to stop the pyglet/Arcade event loop so `arcade.run()` returns. `main()` then calls `os._exit(0)` as a belt-and-suspenders guarantee that no non-daemon background thread (e.g. `arcade.Sound` audio streaming) can keep the process alive — progression is already persisted, so the immediate exit loses nothing.
- **New `tests/test_window_close.py`** (5 tests, arcade-guarded skip like `render_smoke`) — pins that `_shutdown` saves-closes-exits, is idempotent across repeated calls, survives a save failure, works with no `level_manager`, and that `on_close` routes through `_shutdown`. GPU-free: `arcade.Window.__init__` is bypassed with `object.__new__` so no display/GL context is needed.
- **Verification**: `py_compile` clean; full suite **139 → 144** green (6 skipped: display-dependent render_smoke + the 5 new arcade-guarded shutdown tests when arcade is absent).
- **Result**: roadmap **P5 #24 (fix window close) is done.**

## 07/10/2026 - v2.3.1
### ⚖️ Difficulty / balance regression checks (roadmap P4 #15)
**Pins the numeric output of the balance-critical formulas so future tuning edits can't silently regress.** The CHANGELOG records repeated past hotfixes to the difficulty-multiplier and stat-scaling systems (v1.4.1, v1.7.3); until now nothing guarded their exact output. New `tests/test_balance_regression.py` (16 tests) locks down reference character/enemy stat combos with all randomness pinned via `mock.patch`:
- **Enemy HP scaling** (`EnemyManager.create_scaled_enemy`) — the `(hp_base + (level-1)*12 + variance) * difficulty_multiplier` formula at normal/hard(2.0)/easy(0.5) difficulty, the `int()` truncation, that variance is applied *before* the multiplier, the `max(1, …)` HP floor, and the `int(level * multiplier)` enemy-level scaling.
- **Tier boundaries** — the book-level→tier map (basic ≤3, elite 4–6, champion 7–10, ancient 11–15, boss 16+) checked at every edge.
- **Boss scaling** (`create_scaled_boss`) — the steeper `(level-1)*30` HP curve and the `(book_level+3)*multiplier` boss level.
- **Difficulty clamp** — `set_difficulty_multiplier` clamps to `[0.1, 3.0]`.
- **Armor class** (`CharacterManager.get_armor_class`) — `10 + dex_bonus + best_armor`, explicitly pinning that multiple equipped armors take the **max** bonus, never the sum (Plate Mail 7 + Basic Armor 2 → AC 19, not 21), plus the no-character default of 10.
- **Verification**: `py_compile` clean; full suite **123 → 139** green (1 skipped: display-dependent render_smoke).
- **Result**: roadmap **P4 #15 (difficulty/balance regression checks) is done.** Any future edit that shifts the tuning now fails a test instead of shipping a balance regression.

## 07/10/2026 - v2.3.0
### 💾 Versioned save schema + automatic save-file migration (roadmap P4 #14)
**Old/partial character saves are now healed on load instead of silently breaking.** Character saves (`Characters/*.json`) are live player state, and over the project's history the set of fields a character carries has drifted (e.g. the v1.7.3 spell-damage level-scaling rework). Much of the runtime reads fields by **direct index** — `character_data["Aspect1_Mana"]`, `["Hit_Points"]`, `["Credits"]`, `["Inventory"]`, weapon/armor slots — so a save missing any of those raises an uncaught `KeyError` mid-combat. This release adds a versioned schema and a lightweight migration/validation pass that backfills missing structure before the game touches it.
- **New `Code/save_migration.py`** — dependency-free module exposing:
  - `SAVE_SCHEMA_VERSION` (currently `1`) — bump when the required-field set or a coercion rule changes so older saves are detectably stale.
  - `migrate_character(data) -> (data, changed, notes)` — backfills every required field with a sensible default (mirroring `create_sample_character`), coerces the numeric fields (`Level`, `Hit_Points`, `Credits`, `Experience_Points`, `Aspect1_Mana`) to `int` and clamps the non-negative ones, guarantees `Inventory` is a dict and all six ability scores exist, and stamps `Save_Version`. Conservative by design: it only *adds* missing structure and fixes obviously-wrong types — it never deletes unknown/hand-authored keys, and a second pass is a no-op (idempotent). A non-dict save is replaced wholesale with a default character.
  - `validate_character(data) -> [issues]` — read-only diagnostic used by tests/logging.
- **`Code/game_data.py`** — `CharacterManager.load_character()` now runs `migrate_character` on every load; when anything changed it logs what it did and re-saves the healed file to disk (so the fix persists rather than re-running each load). `create_sample_character()` stamps `Save_Version` so fresh saves start current.
- **Tests** — new `tests/test_save_migration.py` (14 tests): field backfill, value preservation, version stamping, numeric string/float coercion, negative clamping, non-dict `Inventory` reset, non-dict-save replacement, idempotency, already-current no-op, `validate_character` behavior, and a `CharacterManager.load_character` integration test proving a legacy save on disk is migrated **and re-written**.
- **Verification**: `py_compile` clean; new module + tests ruff-clean (no new findings); full suite **109 → 123** green (1 skipped: display-dependent render_smoke).
- **Result**: roadmap **P4 #14 (automated save-file migration check) is done.** Establishes `Save_Version` as the anchor for future save-format changes — bump the constant and add a migration rule rather than risking silent breakage.

## 07/10/2026 - v2.2.5
### 🏁 Arcade migration COMPLETE: drop the `pygame` dependency (roadmap P1 #1 — CLOSED, migration step 6 — final part)
**`pygame` is no longer a dependency of Magitech RPG.** This is the last piece of the pygame→Arcade migration begun in v2.0.1. With audio/timing (v2.2.2), sprite/locals (v2.2.3), and display/event/init (v2.2.4) all ported to the Arcade-native `Code/gfx.py` shim, nothing the game runs at runtime needed real pygame anymore — it survived only as an inert import. This release removes that last import path, drops the dependency, and simplifies the backend switch to a single source of truth.
- **`requirements.txt`** — removed `pygame>=2.5`. Arcade is now the sole runtime dependency (rendering, windowing, game loop, audio via `arcade.Sound`, input). The game imports **and runs** with no `pygame` installed.
- **`Code/backend.py` (single source of truth, simplified)** — inverted the default so the Arcade shim is the baseline instead of real pygame: `MEGITECH_BACKEND` unset / empty / `"arcade"` → `Code.gfx` shim; `MEGITECH_BACKEND=pygame` → real pygame (explicit, best-effort opt-in that requires the caller to install pygame). Previously "unset" meant real pygame, which is no longer installed.
- **`Code/ui_components.py`** — replaced its inline duplicate of the backend switch (and the now-unused `import os`) with `from Code.backend import pygame`, so the whole game's `pygame` name (star-exported everywhere) comes from the one switch.
- **All 11 gameplay modules** — replaced the bare, redundant `import pygame` (which was silently overridden by the `ui_components` star-export but still hard-crashed if pygame was absent) with `from Code.backend import pygame`: `combat_system`, `combat_integration`, `enhanced_combat_system`, `enhanced_combat_integration`, `crafting_system`, `inventory_system`, `level_system`, `rest_system`, `settings_system`, `store_system`, `character_creation`. (`tile_map`/`animated_player` already used `Code.backend` from v2.1.5/v2.2.3.)
- **Test suite reworked to run without pygame** — `tests/__init__.py` now defaults the suite onto the Arcade shim (`MEGITECH_BACKEND=arcade`) and initializes via `from Code.backend import pygame` instead of hard-importing real pygame; the three modules that hard-imported pygame (`test_combat_system`, `test_level_system`, `test_crafting_system`) do the same. The shim's headless font/draw/audio stand-ins mean no display, audio device, or pygame install is required. Run the legacy backend (if pygame is installed) with `MEGITECH_BACKEND=pygame`.
- **Verification** (all with **pygame UNINSTALLED**): full `Code/*.py` import sweep **20/20 clean** under the default (shim) backend; full test suite **109/109 green** (1 skipped: display-dependent render_smoke, needs arcade+display); `py_compile` clean across `main.py`, `arcade_app.py`, `Code/*.py`, `tests/*.py`; backend resolution matrix confirmed (unset→`Code.gfx`, `arcade`→`Code.gfx`, `pygame`→ImportError as expected for the opt-in path); `ruff check` adds **no** new findings (net −1: removed the redundant `import os`).
- **Result**: roadmap **P1 #1 (pygame→Arcade migration) is fully CLOSED.** The `Code/gfx.py` shim still keeps a lazy `import pygame` guarded by `try/except` purely so the opt-in `MEGITECH_BACKEND=pygame` path works for developers who install pygame themselves — it is never required.

## 07/10/2026 - v2.2.4
### 🖥️ Arcade migration: port DISPLAY + EVENT off pygame (roadmap P1 #1, migration step 6 — part 3)
**`main.py`'s window/display and event construction no longer route through real pygame.** These were the last runtime call sites still falling through the shim's `__getattr__` to real pygame: `pygame.display.set_mode()` / `pygame.display.set_caption()` in `EnhancedGameManager.__init__`, and `pygame.event.Event(pygame.KEYDOWN, key=...)` in the crafting input path. With this release, **nothing the game exercises at runtime under the Arcade backend touches real pygame** — only never-used extras (`locals`/`Color`/`Vector2`/`mouse`) would still delegate. This clears the way for the final step: dropping the `pygame>=2.5` dependency and simplifying the backend switch.
- **What changed** (`Code/gfx.py`):
  - **`display`** — new native `_DisplayModule` (exposed as `gfx.display`). `set_mode((w, h))` returns an off-screen, screen-flagged `gfx.Surface` instead of opening an SDL window (arcade_app owns the real `arcade.Window` and overwrites `game.screen` with its own Surface right after construction, so this is just a working stand-in). `set_caption()`/`get_caption()` store/return the title in memory; `init`/`quit`/`get_init`/`flip`/`update`/`get_surface` are faithful no-ops (Arcade presents its own frames). Defined at module level so it wins over `__getattr__`.
  - **`event`** — new native `_EventModule` (exposed as `gfx.event`) with `Event` aliased to the existing native `gfx.Event` class, plus `get()`/`poll()`/`pump()`/`clear()`/`post()` as faithful no-ops. Under Arcade the game never polls a queue — arcade_app pushes translated key/text events straight into `handle_event` — so only `Event` construction matters. Added a `NOEVENT = 0` constant for `poll()`.
  - **`init()` / `quit()`** — no longer delegate to real pygame. Every subsystem the game touches is now Arcade-native (font→`arcade.Text`, mixer→`arcade.Sound`, time→stdlib, display/event→this shim), so `init()` is a native no-op returning pygame's `(successes, failures)` tuple shape `(0, 0)`, and `quit()` stops music + releases the display surface.
- **Tests** (`tests/test_gfx.py`): +7 tests (`DisplayEventShimTests`) — `set_mode` Surface sizing + `get_surface`, caption round-trip, display lifecycle no-ops, `event.Event` identity + construction, queue no-ops (`get`/`poll`/`pump`/`clear`/`post`), native `init()` shape, and safe `quit()`. Also explicitly verified with `gfx._pygame = None` that display/event/init use **no** real pygame.
- **Why a patch bump (2.2.3 → 2.2.4)**: internal shim change; no behavior change on `python main.py` (display/event already "worked", just via pygame delegation).
- **Verification** (all green): `py_compile` clean (`Code/gfx.py`, `main.py`, `arcade_app.py`); full suite **102→109** under both `MEGITECH_BACKEND=arcade` and `=pygame` (1 skipped: display-dependent render_smoke); `ruff check Code/gfx.py tests/test_gfx.py` clean.
- **Still remaining for step 6 (P1 #1 stays open — the FINAL piece)**: real `pygame` is now imported by the shim only as an inert `__getattr__` fallback for unused extras. The remaining work is to **drop `pygame>=2.5` from `requirements.txt` and simplify the backend switch** (`Code/backend.py` / `Code/ui_components.py` / the test suite's `MEGITECH_BACKEND=pygame` default). That requires reworking the tests to run on the Arcade shim without a real pygame install, so it's split out as the last migration item.

## 07/10/2026 - v2.2.3
### 🧩 Arcade migration: port SPRITE + LOCALS off pygame (roadmap P1 #1, migration step 6 — part 2)
**`Code/tile_map.py` and `Code/animated_player.py` no longer import real pygame.** These were the last two modules still pulling pygame directly (via `from pygame.locals import *`) and subclassing `pygame.sprite.Sprite`; the shim couldn't reach either because both bypass the `ui_components`/`backend` drawing switch for those specific imports. This release makes both shim-native, continuing the step-6 goal of getting everything off the `pygame` runtime dependency.
- **What changed** (`Code/gfx.py`):
  - **`Sprite`** — added a native `class Sprite` (a minimal `pygame.sprite.Sprite` stand-in) plus a `sprite` namespace (`gfx.sprite.Sprite`). `EnhancedTileMap` and `AnimatedPlayer` subclass this only to call `super().__init__()`; they never use Group membership or collision helpers, so the base implements `__init__`/`add`/`remove`/`kill`/`groups`/`alive`/`update` as faithful no-ops for drop-in parity. Because it's defined at module level it takes precedence over the `__getattr__` delegation, so `pygame.sprite.Sprite` resolves to the shim under the Arcade backend instead of importing real `pygame.sprite`.
- **What changed** (`Code/tile_map.py`, `Code/animated_player.py`):
  - Removed `from pygame.locals import *` from both. `tile_map` referenced **no** names from it (dead import). `animated_player` used `Rect` and `K_UP/K_DOWN/K_LEFT/K_RIGHT` — now qualified as `pygame.Rect` / `pygame.K_*`, which resolve to the shim's module-level `Rect` class and `K_*` constants under Arcade and to real pygame's top-level re-exports under the pygame backend. No behavior change either way.
- **Verification**: `py_compile` clean; both modules import clean under BOTH backends; confirmed `EnhancedTileMap`/`AnimatedPlayer` now have the shim `gfx.Sprite` in their MRO under `MEGITECH_BACKEND=arcade`. Added `SpriteTests` (4 tests) to `tests/test_gfx.py`. Full suite **98→102 green** under both `MEGITECH_BACKEND=arcade` and `=pygame` (1 skipped: display-dependent render_smoke). **Remaining before the `pygame` dep can be dropped**: only `display` (`main.py` `set_mode`/`set_caption`) and `event` (`Event` construction in `main.py`) still route through real pygame — the last piece of migration step 6.

## 07/10/2026 - v2.2.2
### 🔊 Arcade migration: port AUDIO + TIMING off pygame (roadmap P1 #1, migration step 6 — part 1)
**Audio and timing now run through Arcade instead of real pygame.** Step 6 is the final migration item — get everything off the `pygame` runtime dependency so it can be dropped. This release does the two self-contained halves that were pure delegation before: `pygame.mixer` (SFX + background music) and `pygame.time`. The `Code/gfx.py` shim previously forwarded both straight to real pygame via its module `__getattr__`; those names are now defined natively on the shim and take precedence, so under `MEGITECH_BACKEND=arcade` (the default) nothing routes audio/timing through pygame anymore.
- **What changed** (`Code/gfx.py`):
  - **`error`** — added a `class error(Exception)` (pygame.error stand-in). The audio code catches `except pygame.error` / `except (pygame.error, FileNotFoundError)`; under the Arcade backend `pygame` *is* the shim, so it needs its own exception type rather than borrowing real pygame's. Prerequisite for dropping the dep.
  - **`mixer`** — new Arcade-backed `_MixerModule`: `Sound(path)` wraps `arcade.Sound(streaming=False)` with pygame-shaped `set_volume()`/`play(loops)`/`stop()`; `mixer.music` is a single streaming track (`arcade.Sound(streaming=True)`) with `load/set_volume/play(loops)/stop/get_busy` (pygame semantics: `loops=-1` → loop forever, `0` → once); `init(**kwargs)`/`get_init()`/`quit()`/`stop()` manage state. Every op is **defensive** — missing arcade or no audio device raises `error` (which callers already catch) or is a silent no-op, so the game runs without sound exactly as it did under pygame's dummy driver.
  - **`time`** — new `_TimeModule` backed by the stdlib clock: `wait(ms)`/`delay(ms)` (the only calls the game makes — blocking pauses on level transitions in `main.py`), plus `Clock` (`tick(fps)` self-throttles and returns elapsed ms) and `get_ticks()` for a faithful drop-in.
- **Tests** (`tests/test_gfx.py`): +17 tests (`AudioTimingShimTests`) covering the `error` type, `time.wait`/`Clock.tick`/`get_ticks`, mixer lifecycle, `Sound` volume-clamp/play/stop, and music load/loop(-1 vs 0)/stop — all via a `_FakeArcade` so no real audio device is needed. Also verified against a **real** `arcade.Sound` under `xvfb`: `SoundManager` loads **20/20** WAV effects, `sound_available=True`, play/stop crash-free.
- **Why a patch bump (2.2.1 → 2.2.2)**: internal shim change; no behavior change on the default `python main.py` path (audio/timing already "worked", just via pygame).
- **Verification** (all green): `py_compile` clean; full suite **98/98** (was 85; +17 audio/timing, plus other prior additions) under both `MEGITECH_BACKEND=arcade` and headless; `tests/render_smoke.py` **13/13** screens under `xvfb`; `ruff check --select F,E9,B Code/gfx.py tests/test_gfx.py` clean.
- **Still remaining for step 6 (P1 #1 stays open)**: real pygame is STILL imported — `Code/gfx.py` and the un-migrated modules still delegate `display`, `event`, `sprite`, `locals` (and `main.py`'s `pygame.display.set_mode/set_caption`, `pygame.event.Event`). Input **constants** are already shim-native (the `K_*`/event ints), but those last delegations must be ported before `pygame>=2.5` can leave `requirements.txt`.

## 07/10/2026 - v2.2.1
### 🧹 Arcade migration: RETIRE the deprecated pygame run() loop (roadmap P1 #1, migration step 5)
**The legacy hand-rolled pygame `while running:` game loop is gone — Arcade is now the ONLY entry point.** v2.2.0 flipped the default to Arcade but kept the old loop one release as an opt-in fallback (`MEGITECH_BACKEND=pygame python main.py`). With the Arcade path verified crash-free across all 13 screens (`tests/render_smoke.py`), that fallback is now removed.
- **What changed**:
  - **`main.py` (`EnhancedGameManager.run()`)** — the ~40-line deprecated pygame loop (`pygame.time.Clock`, `pygame.event.get()`, `pygame.display.flip()`, `clock.tick(15)`, `pygame.quit()`) was **deleted**. The live loop is `arcade_app`'s `arcade.Window` driving the state machine at 15 Hz.
  - **`main.py` (`__main__`)** — dropped the `if MEGITECH_BACKEND == "pygame"` branch that instantiated `EnhancedGameManager().run()`. `python main.py` now unconditionally delegates to `arcade_app.main()`.
  - **`main.py` (top-of-file comment)** — rewritten to describe Arcade as the sole entry point; the `MEGITECH_BACKEND` env var now only selects the *drawing* binding star-exported by `ui_components` (real pygame vs. `Code.gfx` shim), which the headless test suite still forces to `pygame` for pure-logic imports.
  - **`main.py`** — removed the now-unused `import sys` (its only use was `sys.exit()` inside the deleted loop).
  - **`Code/version.py`** — bumped to **2.2.1**; `BACKEND` doc comment updated.
  - **`requirements.txt`** — comment rewritten. **pygame is intentionally KEPT**: `Code/gfx.py` still delegates audio (`pygame.mixer`), timing, and input constants to real pygame, so it remains a hard runtime dependency under Arcade. Dropping it requires porting audio/timing/input to Arcade — split out as the new final migration item.
- **Why a patch bump (2.2.0 → 2.2.1)**: removes a deprecated, already-non-default code path; no change to the default `python main.py` behavior established in v2.2.0.
- **Verification** (all green): `py_compile` clean; full unittest suite **85/85** (incl. `tests/render_smoke.py` **13/13** screens under `xvfb`); `python main.py` launched the Arcade window headlessly (`xvfb`) and ran crash-free (only harmless ALSA no-audio-device noise); `ruff check main.py` shows only the 12 pre-existing deferred findings (the `import sys` removal cleared one potential F401, added none).
- **Roadmap**: migration step 5's headline (remove the pygame `run()` loop + fallback, simplify the switch) is ✅ done. P1 #1 stays open for ONE remaining item: **port audio/timing/input off pygame** so the `pygame` runtime dependency can finally be dropped.

## 07/10/2026 - v2.2.0
### 🎮 Arcade migration: FLIP THE DEFAULT — `python main.py` now launches Arcade (roadmap P1 #1, migration step 4)
**The pygame → Arcade migration reaches its headline milestone: the game now boots on the Arcade renderer by default.** Every prior v2.x entry gated Arcade behind `MEGITECH_BACKEND=arcade` / running `arcade_app.py`, with plain `python main.py` still driving the legacy hand-rolled pygame `while running:` loop. Step 1 (on-device visual verification, v2.1.21) proved all 13 screens render crash-free through the `Code/gfx.py` shim, which unblocked this flip.
- **What changed**:
  - **`main.py` (top-of-file)** — before any `Code.*` import (so the `ui_components` star-export binds the right renderer), `main.py` now does `os.environ.setdefault("MEGITECH_BACKEND", "arcade")` and, on the Arcade path, `setdefault("SDL_VIDEODRIVER", "dummy")` (keeps the un-retired pygame display/convert/font calls headless so they never steal the GL context from Arcade/pyglet). `setdefault` means an explicit env var — tests forcing `pygame`, `arcade_app` forcing `arcade` — always wins.
  - **`main.py` (`__main__`)** — dispatches on `MEGITECH_BACKEND`: the default (`arcade`) path delegates to `arcade_app.main()` and opens the Arcade window; `MEGITECH_BACKEND=pygame` still runs the original `EnhancedGameManager().run()` pygame loop. The legacy loop and its `run()` method are **DEPRECATED but retained one release** as a fallback (full removal is the final migration cleanup).
  - **`Code/version.py`** — bumped to **2.2.0**; `BACKEND` default constant flipped `"pygame"` → `"arcade"` with the doc comment rewritten to describe the new launch behavior.
- **Why a minor bump (2.1.21 → 2.2.0)**: this changes the default runtime behavior of `python main.py` (now requires `arcade` installed and opens an Arcade window instead of a pygame one) — a notable, user-visible behavior change, not a bug fix.
- **Verification** (all green): `py_compile` clean; full unittest suite **85/85** (tests pin `MEGITECH_BACKEND=pygame`, unaffected); default no-env import binds `main.pygame == Code.gfx` (Arcade shim) with `SDL_VIDEODRIVER=dummy`; `MEGITECH_BACKEND=pygame` import binds real `pygame`; `tests/render_smoke.py` renders **13/13** screens crash-free under `xvfb`; and `python main.py` itself launched the Arcade window headlessly (`xvfb`) and ran for 6s with no traceback / no "No GL context" / no draw-loop error (only harmless ALSA "no audio device" noise from the sandbox).
- **Roadmap**: migration step 4 (flip the default) is now ✅ done. P1 #1 stays open for the final cleanup only — retiring/removing the deprecated pygame `run()` loop once the Arcade default has proven out in real play.

## 07/10/2026 - v2.1.21
### ✅ Arcade migration: on-device VISUAL verification, now automated & passing (roadmap P1 #1, migration step 1)
**Migration "step 1" — the on-device visual pass that had blocked flipping the Arcade backend on by default — is now DONE, and it's automated so it can never silently rot.** Every prior migration entry (v2.0.x–v2.1.20) noted that step 1 "still requires a display" because the sandbox had no GL context; that assumption no longer holds. Drove the REAL game (`arcade_app.MagitechWindow` → `EnhancedGameManager`) through all 13 `GameState` screens under the Arcade rendering shim and confirmed each one paints through `Code/gfx.py` without crashing.
- **Result**: **13/13 screens rendered crash-free** under `MEGITECH_BACKEND=arcade` — opening, main menu, character select, create-character, game board (tile map + player sprite + HUD), store, inventory, character sheet, help, level select, settings, crafting, and fight. Frames are non-black (menus/UI 100%, tiled game board/crafting ~85%, store ~75%). Visually spot-checked the main-menu (gradient title bar, gold-highlighted selection), game board (grass/path/water tiles, trees, rocks, enemies, treasure, shop/rest icons, player sprite), and the semi-transparent HUD panel — confirming the v2.1.18 `set_alpha` fix dims rather than blots. No new shim primitives needed fixing; the shim as of v2.1.20 renders every screen correctly.
- **New file: `tests/render_smoke.py`** — a standalone, runnable harness that opens the Arcade window headlessly, builds a sample character + world, renders each screen to a PNG (in a temp dir), and asserts no draw call raises and no frame is fully black. Exits 0 (pass or clean skip) / 1 (a screen crashed). Prints a per-screen OK/CRASH table. Run with `xvfb-run -a python3 tests/render_smoke.py` on a headless box (or plain `python3 tests/render_smoke.py` with a display).
- **New file: `tests/test_render_smoke.py`** — a unittest wrapper that subprocess-runs the harness (env isolation so `MEGITECH_BACKEND=arcade` can't leak into the pygame-backed tests, and so a native pyglet SIGSEGV can't kill the suite). It auto-uses `xvfb-run` when present and **skips cleanly** (never fails) when `arcade` isn't installed or no GL context is available — so CI without a display stays green while developers with a display get real coverage.
- **Verification**: full suite now **85/85** green (was 84/84); the new render-smoke test executed live via `xvfb` (arcade 3.3.3 + pygame 2.6.1) and passed. `py_compile` clean.
- **Roadmap**: marked migration step 1 ✅ done in the in-progress entry and noted step 4 (flip the default + retire the legacy pygame `run()` loop) is now unblocked. P1 #1 stays open until step 4 lands.

## 07/10/2026 - v2.1.20
### 🔤 Arcade migration: implement missing `Font.get_height()` on the shim (roadmap P1 #1, migration step 2)
**Under the Arcade backend, opening the inventory/store screen crashed: `Code/inventory_system.py` calls `self.font.get_height()` to size a selection highlight, but the `gfx` shim's `Font` implemented only `render()` and `size()` — no `get_height()`.** Real `pygame.font.Font` exposes `get_height()`, so this "just worked" on the legacy pygame backend and silently became an uncaught `AttributeError` once the module renders through the shim. The call sits *outside* the surrounding `try/except`, so it aborts the whole inventory/store draw rather than falling back.
- **Root cause**: incomplete `Font` API surface in `Code/gfx.py`. The shim covered text drawing and measuring but omitted the font-metric accessors (`get_height`, `get_linesize`, `get_ascent`, `get_descent`) that pygame Fonts provide and that un-migrated game code is free to call.
- **Fix**: added `get_height()` (renders a tall ascender+descender sample `"Ay"` and returns its pixel height; the no-arcade fallback returns the point size), plus companion `get_linesize()`, `get_ascent()`, and `get_descent()` (pygame's descent is negative) so the shim `Font` is a faithful drop-in. Text-independent by construction, matching pygame semantics.
- **Tests**: added 3 cases to `tests/test_gfx.py` — `get_height()` is callable and equals the point size in the metric fallback, and the three companion accessors are present with the right signs. Full suite now **84/84** (gfx module 42); `py_compile` clean.
- **Roadmap**: appended a progress note under the migration in-progress entry (P1 #1). The item stays open — on-device visual verification (step 1) and flipping the default (step 4) still require a display.

## 07/10/2026 - v2.1.19
### 🔤 Arcade migration: fix `Font.size(text)` being shadowed by an int attribute (roadmap P1 #1, migration step 2)
**The `gfx` shim's `Font` broke pygame's drop-in API: `pygame.font.Font.size(text) -> (w, h)` is a *method* that measures a string, but the shim's `Font.__init__` stored the point size as `self.size`, shadowing the class's `size()` method with an int.** Any caller doing the standard pygame text-measuring idiom `font.size("text")` would hit `TypeError: 'int' object is not callable`. The current game code happens not to call `font.size()` yet (it measures via `render(...).get_width()`), so this was a latent trap rather than a live crash — but it violates the shim's whole reason to exist (be a faithful `import pygame` replacement so un-migrated modules "just work").
- **Root cause**: name collision in `Code/gfx.py` `Font` — instance attribute `self.size` (int, set in `__init__`) vs. method `size(self, text)` defined on the class. Instance attributes win attribute lookup, so the method became unreachable.
- **Fix**: renamed the stored point size to `self.font_size` throughout `Font` (init + both `render` paths + the `_get_cached_text` call), freeing the `size(text)` method to work. Added a class docstring documenting *why* the field must not be named `size`. Verified no code reads `font.size` as an attribute anywhere in `Code/`/`main.py` (grep-swept both), so the rename is safe. Confirmed live under `MEGITECH_BACKEND=arcade`: `Font(None, 24).size("Hello")` now returns `(66, 24)` instead of crashing.
- **Tests**: added 2 cases to `tests/test_gfx.py` — `size()` is callable and returns a sane `(w, h)`, and the size is stored/honored as `font_size` in the metric fallback. Suite now **82/82** (was 80/80); `py_compile` clean; ruff clean.
- **Roadmap**: appended a progress note under the migration in-progress entry (P1 #1). The item stays open — on-device visual verification (step 1) and flipping the default (step 4) still require a display.

## 07/10/2026 - v2.1.18
### 🎨 Arcade migration: fix `set_alpha` being ignored on off-screen surface replay (roadmap P1 #1, migration step 2)
**Under the Arcade backend, semi-transparent overlays rendered as fully opaque, blotting out the whole screen instead of dimming it.** The crafting, inventory, and store screens use pygame's classic dimmer pattern: build an off-screen `Surface`, `fill(BLACK)`, `set_alpha(180/200)`, then `blit` it over the game world. The `gfx` shim records an off-screen surface's draw ops and replays them at blit time — but the replay path ignored the surface's alpha for every fill/shape op (only nested blits threaded it through). So the overlay painted solid black and hid everything behind the panel.
- **Root cause**: `Surface._replay()` in `Code/gfx.py` called `_draw_rect`/`_draw_circle`/… with the raw recorded color, dropping the `alpha` argument it already received from `set_alpha`. Confirmed live in `crafting_system.py` (alpha 180) and `inventory_system.py` store (alpha 200), both of which fill BLACK over the full screen.
- **Fix**: added `_apply_alpha(color, alpha)` — multiplies a color's alpha channel by the surface-level alpha (treating RGB as opaque, composing multiplicatively with an already-translucent RGBA source, and short-circuiting when alpha is `None`/≥255). Threaded it through every shape op in `_replay` (fill, rect, circle, ellipse, line, lines, polygon). Nested blits already carried alpha and are unchanged.
- **Tests**: added 2 cases to `tests/test_gfx.py` covering `_apply_alpha` (opaque passthrough, half/partial modulation, the exact 180/200 overlay values, multiplicative RGBA compose, zero-alpha). Suite now **80/80** (was 78/78); `py_compile` clean; ruff clean.
- **Roadmap**: appended a progress note under the migration in-progress entry (P1 #1). The item stays open — on-device visual verification (step 1) and flipping the default (step 4) still require a display.

## 07/10/2026 - v2.1.17
### 🧪 Arcade migration: regression tests for the `gfx` shim (roadmap P1 #1, migration step 2 safety net)
**The `Code/gfx.py` shim is the single point every draw call flows through during the Pygame→Arcade migration, yet it had zero direct test coverage — its two most fragile jobs (the pygame→Arcade Y-axis flip and off-screen surface record/replay) could regress silently as the shim is extended for the pending on-device visual pass. Added a headless test module that pins that behaviour so the upcoming visual/shim-tuning work has a net under it.**
- **New file: `tests/test_gfx.py`** — 36 tests across 8 groups: pure helpers (`_flip_y` inversion about screen height, `_norm_color` clamping/defaults, `_rect_xywh`, `_finite` NaN/inf rejection), `_safe_text` CoreText-crash guard (strips variation selectors / ZWJ / combining-keycap / astral-plane emoji, keeps BMP arrows), the full `Rect` API (edges, size aliases, center/anchor setters, collide, move/copy/inflate, clamp/union/contains, xywh unpacking), `Surface` (size queries, alpha clamping, off-screen classification, `fill`/`blit` op recording incl. `Rect` dest), `pygame.draw.*` op recording onto off-screen surfaces, `Font` metric fallback + `SysFont`/`init`, and key/event constants matching pygame's values + held-key roundtrip.
- **GPU-free by design**: a `NoArcadeMixin` forces `gfx._arcade = None` for each test (and pins the screen size to 800×600), so every `_draw_*` primitive early-returns. That drives the coordinate-flip, area-clip, and op-recording *logic* right up to the draw boundary without needing a display or an installed `arcade` — so the suite is deterministic whether or not `arcade` is present on the runner, and `replay()` is exercised as a safe no-op smoke test.
- **Why now**: migration "Remaining" steps 1 (on-device visual pass) and 2 (extend the shim for primitives that render wrong) both mean *editing `gfx.py`*. These tests catch coordinate/anchor/recording regressions introduced during that tuning; they intentionally do NOT assert pixels (that is the human visual pass's job).
- **Verification**: `tests/test_gfx.py` 36/36 green; full suite now **78/78** (was 42/42); `py_compile` clean across `main.py`, `arcade_app.py`, `Code/*.py`, `tests/*.py`; `ruff check tests/test_gfx.py` clean.
- **Roadmap**: appended a progress note under the migration's in-progress entry (P1 #1). The item stays open — visual verification (step 1) and flipping the default (step 4) still require on-device work.

## 07/10/2026 - v2.1.16
### 📜 Documentation: reconcile the legacy multiplayer version history (roadmap P3 #12)
**The CHANGELOG's earliest entries (v23–v29, Aug 2025) describe a client/server multiplayer prototype whose code is entirely absent from the current single-player tree — a trap for anyone (human or agent) reading the history and assuming a server component still exists. Annotated it as a discontinued prototype and clarified how it relates to the *planned* future multiplayer work.**
- **Finding**: the v23–v29 history references `NetworkManager_Class.py`, `Server_v1`/`v2`/`v3`, `config.py`, and `classes.py` — a repo scan confirms **none of these files exist** anywhere in the current codebase, and there is no `socket`/`socketserver`/network import in any `Code/*.py`, `main.py`, or `arcade_app.py`. The prototype was abandoned and the project rebuilt as the single-player game the entire `v1.x`/`v2.x` history documents. The only remnants are two orphaned SQLite files in `assets/` (`rpg_server.db`, `OLD_rpg_server.db`) that no live code opens.
- **Decision**: multiplayer is **not** a discontinued idea — it is a *future, from-scratch* goal (ROADMAP.md **P6 #40/#41, v3.0.1**), which explicitly adds a fresh server/client layer alongside single-player. That effort shares no code with this early prototype, so the history is archived as legacy rather than treated as a live server the roadmap should plan around.
- **File: `CHANGELOG.md`** — added a `⚠️ LEGACY / DISCONTINUED PROTOTYPE` banner directly above the v29 section explaining the above, pointing forward to P6, and noting the orphaned DB files. The historical entries are preserved verbatim.
- **Roadmap**: moved P3 #12 from the open backlog to Done.
- **Docs/metadata-only change** — no application code touched; `py_compile` stays clean and the test suite is unaffected (42/42).

## 07/10/2026 - v2.1.15
### 📦 Dependency manifest confirmed / roadmap reconciliation (roadmap P1 #7)
**Closed roadmap P1 #7 ("Add `requirements.txt`") — the manifest already exists and fully satisfies the item, so this run reconciles the stale backlog entry rather than re-adding the file.** The roadmap item was written against an earlier state ("no dependency manifest exists"); the manifest was in fact added during the v2.x migration and pins the project's only two third-party runtime dependencies.
- **Verification: `requirements.txt` covers every third-party runtime import.** A full import sweep of `main.py`, `arcade_app.py`, and `Code/*.py` shows exactly two non-stdlib, non-local packages imported at runtime: `pygame` and `arcade`. Both are pinned in `requirements.txt` (`pygame>=2.5`, `arcade>=3.3`). NumPy was only used by the one-off v2.1.3 SFX generator script, not at runtime, so it is correctly absent from the runtime manifest (dev-only `ruff` lives in `requirements-dev.txt`). The lower-bound (`>=`) pins are intentional for the migration window, during which both backends must be installable together.
- **No dependency drift**: nothing to add or remove — the manifest and the actual imports agree.
- **Roadmap**: moved P1 #7 from the open backlog to the Done section.
- **Docs/metadata-only change** — no application code touched; `py_compile` stays clean and the test suite is unaffected (42/42).

## 07/10/2026 - v2.1.14
### 📝 Documentation: sync README architecture with the real code layout (roadmap P3 #11)
**The README's "Project Architecture" section was frozen at the pre-v1.6 structure and actively misled anyone (human or agent) trying to navigate the code.** It named `game_states.py` as the main game engine and entry point (that file was renamed to `main.py` back in v1.6) and listed every module as a flat, root-level file — but all game modules have long lived under the `Code/` package, and the v2.x migration added a second entry point.
- **File: `README.md`.** Rewrote the stale sections to match reality:
  - **Entry points**: `main.py` (default, pygame) and `arcade_app.py` (Arcade backend) — replaced the single `game_states.py` reference. `EnhancedGameManager` now correctly attributed to `main.py`.
  - **Backend note**: documented the `MEGITECH_BACKEND` runtime switch (unset → pygame; `arcade` → the `Code/gfx.py` shim, set by `arcade_app.py`) and that modules import the backend via `Code/backend.py` / `Code/ui_components.py`, not `import pygame` directly.
  - **Dependencies**: pygame ≥ 2.5 **and** arcade ≥ 3.3 (per `requirements.txt`), replacing the lone "pygame 2.6.1".
  - **File Structure**: replaced the flat root listing with the actual `Code/` package tree (all 20 modules, including the migration-era `version.py`, `backend.py`, `gfx.py`), plus `tests/`, gitignored `Characters/`/`SaveProgression/` runtime dirs, and the tooling/config files (`requirements*.txt`, `pyproject.toml`, `CHANGELOG.md`, `ROADMAP.md`).
  - **Running the Game**: `pip install -r requirements.txt`, then `python main.py` (default) or `MEGITECH_BACKEND=arcade python arcade_app.py`.
  - **Overview / Version Metadata**: noted the in-progress Pygame→Arcade migration and the central `Code/version.py`.
- **Docs-only change** — no application code touched. `py_compile` across `main.py`, `arcade_app.py`, and `Code/*.py` stays clean; test suite unaffected (42/42).

## 07/09/2026 - v2.1.13
### 🤖 Continuous Integration: first GitHub Actions workflow (roadmap P2 #9)
**Added the repository's first CI pipeline so every push and pull request is automatically byte-compiled, linted, and tested — closing roadmap P2 #9 and giving the ongoing Arcade migration a safety net.**
- **New file: `.github/workflows/ci.yml`.** Triggers on `push` and `pull_request` against the gitflow integration branches `main` and `develop`, plus manual `workflow_dispatch`. A `concurrency` group cancels superseded runs on the same ref.
- **Job steps** (Ubuntu, Python 3.11 matrix, pip cache): install `requirements.txt` (pygame + arcade) and `requirements-dev.txt` (ruff) → `python -m py_compile main.py arcade_app.py Code/*.py` → `ruff check .` → `python -m unittest discover -s tests -v`.
- **Headless by design**: `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` are set at job scope so the pygame-coupled modules import without a display or audio device on the runner — the same mechanism the local test harness uses.
- **Lint is non-blocking for now** (`continue-on-error: true`): the 43 pre-existing Ruff findings are already tracked in the ToDo above and deferred to a dedicated cleanup pass, so the step reports without failing the build. It becomes a hard gate once that cleanup lands.
- **Verification** (local, before commit): workflow YAML parses via `yaml.safe_load`; `py_compile` clean across all sources; `ruff check .` reports the expected **43** findings; test suite **42/42 green** under the dummy SDL drivers. No application code changed.

## 07/09/2026 - v2.1.9
### 🧹 Arcade migration: fix combat_integration standalone import (roadmap P1 #1, remaining step 3)
**Cleared the last pre-existing import bug blocking a clean full-module import sweep.** `Code/combat_integration.py` did a bare `from game_data import CharacterManager`, but `game_data` lives under the `Code/` package — so the module raised `ModuleNotFoundError: No module named 'game_data'` when imported standalone under *both* backends (it only survived at runtime because `main.py` had already put `Code` on the path first). Every other module references siblings as `from Code.<mod> import …`; this one was inconsistent.
- **File: `Code/combat_integration.py`** — changed line 9 to `from Code.game_data import CharacterManager`. The bare `import pygame` on line 6 is left as-is on purpose: the subsequent `from Code.ui_components import *` star-export rebinds `pygame` to the selected backend (same established pattern as `combat_system.py`), so it is not a bug.
- **Verification**: full `Code/*.py` import sweep now **20/20 clean** under the pygame backend and 20/20 under `MEGITECH_BACKEND=arcade` (both headless, `SDL_VIDEODRIVER=dummy`); previously combat_integration was the one failure. Test suite still **42/42 green**. This resolves item 3 of the migration's "Remaining to fully retire pygame" list — remaining work is the on-device visual pass (step 1), shim primitive coverage (step 2), and flipping the default (step 4).

## 07/09/2026 - v2.1.12
### 🎮 Gameplay fixes surfaced by the Arcade playtest: store, boss persistence, next-world portal
**Three issues found once the Arcade build was actually playable (all pre-existing game logic, not rendering):**
- **Store was missing on every level.** `setup_enhanced_world_objects()` clears `self.shops` and rebuilds enemies/treasures/trees/rest area on each level entry, but never recreated a shop — so the only shop was the one-time startup safety-shop, wiped the instant the player entered any level. Now recreates a `Shop(world_width - 80, 20)` alongside the rest area (matching the reserved zone in `get_reserved_positions()`). File: `main.py`.
- **Boss remained on screen after defeat.** `complete_level_after_boss()` cleared the boss dungeon, but `check_level_completion()` runs every frame and — seeing all enemies dead and no dungeon — immediately **respawned** the boss dungeon, so it reappeared perpetually. Added a `self.level_boss_defeated` flag (set on boss defeat, reset when a level is (re)built) and gated the respawn on it. Files: `main.py`.
- **New: portal to the newly-opened world.** After a boss is beaten, instead of the entrance just vanishing, a **forward portal** (`Dungeon(is_portal=True)`) now opens at world centre. Walking into it and pressing space advances to the next unlocked world/level (`enter_level_portal` → `get_next_level` → `change_level`) rather than starting another boss fight. The existing `Dungeon` already renders as a mystical portal; added an `is_portal` flag and routed the interaction dispatch accordingly. Files: `main.py`, `Code/ui_components.py`.
- **Verification**: full 18/18 module import sweep clean under `MEGITECH_BACKEND=arcade` (+ `main` imports clean); `py_compile` clean. Needs on-device playtest: clear a level → beat the boss → confirm the boss entrance is replaced by a portal, the store is present, and the portal advances to the next world.

## 07/09/2026 - v2.1.11
### 💥 Arcade migration: fix the combat SIGSEGV — CoreText emoji crash (roadmap P1 #1)
**`faulthandler` localized the segfault: `enhanced_combat_system.py:1124` renders `self.large_font.render("️ COMBAT ", …)`, and that string's leading character is a lone `U+FE0F` variation selector (left behind when an emoji was stripped from the source). Creating an `arcade.Text` from it drives pyglet's macOS CoreText renderer (`pyglet/font/quartz.py:283`) into a hard SIGSEGV — uncatchable, hence the bare `exit 139`.**
- **File: `Code/gfx.py`** — new `_safe_text()` sanitizer, applied in `Font.render` before building any `arcade.Text`: strips variation selectors (`U+FE00–FE0F`), zero-width joiner, combining enclosing keycap, and astral-plane (`> U+FFFF`) emoji/symbols — exactly the classes pyglet's CoreText path crashes on. Decorative game emoji are dropped; readable text and BMP symbols (arrows `↑↓`, box-drawing) are kept. A string that sanitizes to empty returns a 0×0 surface instead of an empty `Text`.
- **Hardening in the same path**: font size is now clamped to `[6, 200]` px (0/negative/absurd sizes also crash CoreText), and the default font stack dropped the never-installed `"Kenney Pixel"` in favor of `("arial", "helvetica", "calibri")` so CoreText resolves a real face immediately.
- **Verification**: `_safe_text` unit-checked — `"️ COMBAT "` → `" COMBAT "`, `"🏆 Victory"` → `" Victory"`, `"↑↓ Nav"` preserved, emoji-only → `""`. Combat should no longer crash. (This is why menus were fine and only combat died — only the combat title carried the orphaned selector.)

## 07/09/2026 - v2.1.10
### 🛡️ Arcade migration: guard degenerate geometry + enable crash diagnostics (roadmap P1 #1)
**Combat still SIGSEGV'd (signal 11) after the v2.1.8 caching fix — a hard C-level crash inside Arcade/pyglet/OpenGL that `try/except` can't catch (only the exit code showed).** Two-pronged response:
- **Defensive geometry guards in `Code/gfx.py`** — pygame silently no-ops degenerate shapes, but Arcade's GL/tessellation layer can hard-crash on them. Every draw primitive now bails on bad input: rects/ellipses/texture blits with width or height ≤ 0, circles with radius ≤ 0, polygons with < 3 points, and any coordinate that is NaN/inf (new `_finite` helper). Combat draws health-bar widths, sprite rects, and effect polygons from live values that can hit 0 or negative — a prime segfault source.
- **`arcade_app.py`: `faulthandler.enable()`** — so a native crash now prints the Python traceback at the fault point (module + line) instead of a bare `exit code 139`. This is the only way to localize a segfault; safe to leave on (fires only on an actual fault).
- **Next step**: if combat still crashes, the `faulthandler` dump will name the exact draw call — paste it and the fix is targeted. If the geometry guards were the cause, combat now survives.

## 07/09/2026 - v2.1.8
### ⚡ Arcade migration: fix lag, combat SIGSEGV, and "can't set attribute" (roadmap P1 #1)
**On-device: movement was slow/laggy and entering combat hard-crashed the process (SIGSEGV / signal 11), preceded by `draw() error: can't set attribute`.** Three distinct shim bugs:
- **`can't set attribute`** — `Code/gfx.py` `Rect` exposed `left`/`right`/`top`/`bottom` as read-only, but pygame lets you assign them (combat code does `rect.top = …`). Added setters for all four edges (mirroring pygame: setting `right`/`bottom` moves `x`/`y` by width/height). Verified.
- **Lag + SIGSEGV** — the real killer was **per-frame GPU resource creation**. Every tile blit called `arcade.Texture.crop` and every text draw built a new `arcade.Text` — hundreds of fresh GPU objects per frame, which thrash and then **overflow the texture atlas** (lag → segfault, worst in combat's full-screen redraw). Added two caches in `gfx.py`: `_crop_texture` now memoizes crops by `(source-texture-id, x, y, w, h)`, and `Font.render` memoizes `arcade.Text` by `(text, size, font, color)` via `_get_cached_text` (position/alpha still set per-draw, so sharing is safe; crude 4000-entry bound handles churning HP/damage strings). Each distinct tile cell / string is now uploaded to the GPU exactly once.
- **Verification**: Rect edge-setter smoke test passes; import harness 17/18 under both backends. Movement should be smooth and combat should no longer crash — re-run and report any remaining `draw() error:` lines.

## 07/09/2026 - v2.1.7
### 🕹️ Arcade migration: fix character movement (held-key state) (roadmap P1 #1)
**Game loaded and rendered under Arcade, but the character wouldn't move.** Continuous movement (`AnimatedPlayer.update_position`, and `main.py:1088`) polls `pygame.key.get_pressed()`, but under the Arcade backend the real pygame window receives no input — Arcade owns the window — so `get_pressed()` was always all-False. (Menus worked because they use discrete KEYDOWN events, which were already translated.)
- **File: `Code/gfx.py`** — added a real `key` module to the shim: a module-level held-key set plus `set_key(keyint, down)` and a pygame-shaped `key.get_pressed()` that indexes it (`_PressedKeys`, `_KeyModule`). Any other `pygame.key.*` attribute (`get_mods`, `name`, `set_repeat`, …) still delegates to real pygame. Because the shim now defines `key`, it takes precedence over the hybrid `__getattr__` passthrough.
- **File: `arcade_app.py`** — `on_key_press` now calls `gfx.set_key(key, True)` (in addition to firing the discrete KEYDOWN for menu nav), and a new `on_key_release` calls `gfx.set_key(key, False)`. So the shim's held-key state mirrors what Arcade sees, and polled movement works.
- **Verification**: shim key-state smoke test passes (press→held→release); import harness still 17/18 under both backends. Arrow-key movement should now work on-device — re-run and report any remaining `draw() error:` lines for the next shim-coverage batch.

## 07/09/2026 - v2.1.6
### 🐞 Arcade migration: complete the shim's Rect API + harden shutdown frame (roadmap P1 #1)
**On-device run surfaced per-frame `draw() error: 'Rect' object has no attribute 'inflate'` — the shim's `Rect` was missing methods real `pygame.Rect` has, so any module using them silently failed to paint. Also a benign `No GL context` traceback on the final frame after the window closes.**
- **File: `Code/gfx.py`** — completed `Rect` to match the pygame.Rect surface the code uses: methods `inflate`/`inflate_ip` (grow/shrink keeping center), `copy`, `move_ip`, `colliderect`, `clamp`, `union`, `contains`, and `collidepoint((x,y))` tuple form; plus `w`/`h`/`size` aliases and the `topright`/`bottomleft`/`bottomright`/`midtop`/`midbottom`/`midleft`/`midright` anchors (get + set). Verified in isolation: `inflate` preserves center, `copy` is independent, `colliderect` hit/miss correct.
- **File: `arcade_app.py`** — `on_draw` now guards `self.clear()` and early-returns on a new `_closing` flag (set in `_shutdown`). After the window closes, pyglet can fire one more scheduled frame with no GL context; this skips that dying frame instead of dumping a `pyglet.gl.lib.GLException` traceback (process already exits 0).
- **Verification**: `Rect` smoke test passes; import harness still 17/18 under both backends. Remaining errors from the on-device run should now be down to genuinely-missing render primitives (report the next batch of `draw() error:` lines and I'll extend the shim).

## 07/09/2026 - v2.1.5
### 🎮 Arcade migration: switch the two non-star-import modules + shim sprite-sheet support (roadmap P1 #1)
**The runtime backend switch (v2.0.5) reaches every module that does `from Code.ui_components import *`, but `Code/tile_map.py` and `Code/animated_player.py` don't — they bound real pygame directly, so they never rendered through the Arcade shim. Migrated both, and taught the shim the sprite-sheet operations they need.**
- **File: `Code/backend.py`** (new) — DRY single-source-of-truth backend switch (`from Code.backend import pygame`) using the same `MEGITECH_BACKEND` logic as `ui_components` (unset → real pygame; `arcade` → `Code.gfx`). Lets a module that can't reach the `ui_components` star-export flip backends with a one-line import.
- **File: `Code/tile_map.py`** — `import pygame` → `from Code.backend import pygame`. Tile-sheet cell blits (`screen.blit(sheet, pos, area)`) now route through the shim.
- **File: `Code/animated_player.py`** — `import pygame` → `from Code.backend import pygame`. Sprite-frame extraction now routes through the shim. (`from pygame.locals import *` and `pygame.sprite.Sprite` keep delegating to real pygame — backend-agnostic.)
- **File: `Code/gfx.py`** — added the sprite-sheet primitives these modules require: `Surface.subsurface(rect)` (frame extraction) and texture-backed `blit(source, dest, area)` now **crop** the sheet to the requested cell instead of drawing the whole texture. New helpers `_crop_texture` (uses `arcade.Texture.crop`, PIL-crop fallback) and `_rect_xywh`.
- **Verification**: headless import harness on-device under BOTH backends (`SDL_VIDEODRIVER=dummy`, and again with `MEGITECH_BACKEND=arcade`) — 17/18 modules import clean in each mode. The one failure, `Code/combat_integration.py`'s bare `import game_data`, is a pre-existing relative-import bug (identical in both backends, unrelated to this change) and is logged in ROADMAP P1 #1 remaining work. Pixel-level rendering still needs an on-device visual pass (`MEGITECH_BACKEND=arcade python arcade_app.py`).

## 07/09/2026 - v2.1.4
### 🗺️ Spawned items are now always accessible (roadmap P1 #3)
**World items (trees, rocks, metal veins, streams, brushes) were placed at random coordinates constrained ONLY by min-distance to other spawned entities. They didn't reserve space around the player's spawn point or the key interactables, and the x/y ranges were hardcoded to the old 800×600 window instead of the actual 768×576 world — so a blocking rock/metal/tree could land on the player's start point (trapping them) or on top of the rest area, shop, or the world-centre where the boss dungeon appears (burying an interactable), and none of the ranges would adapt if the map size changed.**
- **World-derived spawn bounds** — new `EnhancedGameManager.get_spawn_bounds(margin)` computes the min/max spawn x,y from `tile_map.get_world_pixel_size()` with an inset margin, replacing the hardcoded `random.randint(40, 760)` / `(60, 740)` / `(40, 560)` ranges in `create_trees` and `create_map_objects`. Every item now lands inside reachable world bounds and the logic scales automatically if the tile dimensions change. Bounds are clamped so they never invert on a tiny world.
- **Reserved interactable zones** — new `get_reserved_positions()` returns the player start `(480, 480)`, the rest-area corner `(w-60, h-60)`, the shop `(w-80, 20)`, and the boss-dungeon centre `(w/2, h/2)`. Both spawn loops now reject any candidate within `RESERVED_CLEARANCE = 70`px of these points (larger than the 50px interaction radius so an interactable is never buried, and larger than the player sprite so the spawn point is never blocked). This replaces the old ad-hoc "avoid player start by 80px" check that covered trees only.
- **Walkable-tile guard** — candidates are now validated against `tile_map.is_position_walkable()` before placement, future-proofing the pipeline for non-uniform maps (all tiles are walkable today, so behaviour is unchanged now).
- **New regression test** — `tests/test_spawn_accessibility.py` (6 tests): pins `get_spawn_bounds` (default world, scaling, tiny-world clamp) and `get_reserved_positions`, then drives the real `create_map_objects` and `create_trees` loops across 60 RNG seeds each, asserting every placed item stays inside bounds and ≥70px from every reserved point. Uses a bare `__new__` instance + lightweight stubs so it runs headlessly. Suite now **42 tests, all green**; `py_compile` clean; no new Ruff findings. See ROADMAP.md P1 #3 (moved to Done).

## 07/09/2026 - v2.1.3
### 🔊 Replaced 0-byte placeholder SFX with real audio (roadmap P4 #17)
**Six sound effects shipped as empty 0-byte `.wav` files (`player_hurt`, `run_away`, `victory`, `menu_select`, `menu_move`, `door_open`), so `pygame.mixer.Sound` failed to load them — the game degraded gracefully but those cues were silent (surfaced while fixing the P0 #2 audio-path bug).**
- **Generated real audio procedurally** with NumPy (no external asset dependency, reproducible via a fixed RNG seed). All files are 44.1 kHz, 16-bit stereo with short attack/release envelopes so they don't click:
  - `menu_move.wav` — 60 ms soft 880 Hz blip (navigation tick).
  - `menu_select.wav` — 130 ms two-note up-confirm (660 → 990 Hz).
  - `player_hurt.wav` — 250 ms descending 300→120 Hz tone mixed with noise (grunt/impact).
  - `run_away.wav` — 300 ms rising 200→1400 Hz whoosh sweep with a fading noise layer (flee).
  - `victory.wav` — 800 ms four-note C-E-G-C (523/659/784/1047 Hz) major-arpeggio fanfare with a second harmonic.
  - `door_open.wav` — 400 ms low 90→140 Hz creak with an 18 Hz flutter amplitude-modulation and light noise.
- **Verification**: each file loads through `pygame.mixer.Sound` under headless dummy SDL drivers (`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`) and reports its expected non-zero length. No code changes were needed — the loader in `Code/enhanced_combat_system.py` already referenced these filenames; only the assets were missing. See ROADMAP.md P4 #17 (moved to Done).

## 07/08/2026 - v2.1.2
### 🧹 Added a Ruff linter config (roadmap P2 #10)
**The codebase is large (`main.py` alone is ~1,950 lines) with no enforced style or dead-code check, so unused imports and stray dead code accumulated silently before every refactor.**
- **New `pyproject.toml`** with a `[tool.ruff]` section — the project's first tooling config. Targets `py311`, `line-length = 120`, and excludes vendored/generated/content dirs (`venv`, `__pycache__`, `Books`, `assets`, `Images`, `Sounds`, `Characters`, `Enemies`, `SaveProgression`).
- **High-signal, low-noise rule set**: `select = ["F", "E9", "B"]` (pyflakes dead-code/unused-import/undefined-name checks, syntax errors, and flake8-bugbear likely-bugs). Style rules (E1/E2/E3/E7, W) are deliberately left OFF so this is not a reformat diff.
- **Silenced the star-import noise**: the whole game distributes its `pygame` binding via `from Code.ui_components import *` (the documented v2.0.5 backend switch), which makes `F403`/`F405` fire on essentially every pygame call — **484 of 527 raw findings were that pattern**. Ignoring `F403`/`F405` (plus `B008`/`B905`) drops the report to **43 real findings**: 13 unused imports, 12 unused variables, 13 unused loop control vars, 4 f-strings without placeholders, 1 redefinition. Per-file ignores relax `F401`/`F811` in `tests/` and `F401` in `__init__.py` re-export shims.
- **New `requirements-dev.txt`** — dev-only tools (`ruff>=0.15`) kept separate from the runtime `requirements.txt` so playing the game needs no linter install.
- **Scope note**: this change adds the config only; the 43 findings it surfaces are logged under ToDo above for a dedicated cleanup pass (17 are Ruff `--fix`-safe). Run with `ruff check .`. Tests still green (36/36); `py_compile` clean. See ROADMAP.md P2 #10 (moved to Done).

## 07/08/2026 - v2.1.1
### 🧪 Added a minimal unit-test suite (roadmap P2 #8)
**The project had no `tests/` directory or test framework, so there was no automated safety net for the pure-logic modules — every balance/formula change had to be verified by hand in-game.**
- **New `tests/` package** using only the standard-library `unittest` (no third-party runner needed). `tests/__init__.py` forces SDL's dummy video/audio drivers (`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`) so the Pygame-coupled game modules import and run in a headless environment (CI, containers) with no display or sound card.
- **`tests/test_combat_system.py`** — pins `CombatManager.calculate_damage`, `calculate_spell_damage`, and `calculate_hit_chance` (strength/int/wisdom/level bonuses, critical multipliers, the 5%/75% hit-chance boundaries and the 5% floor) plus `SpellManager` level-gated spell availability. Randomness is controlled with `mock.patch` on the module's `random.randint` so every expected value is exact.
- **`tests/test_level_system.py`** — covers `LevelManager` unlock gating, level selection, and the completion cascade (finishing a boss level unlocks the next world), plus the deterministic `WorldLevelGenerator` enemy/treasure count helpers. Progression JSON is written inside a temp CWD so the repo is never touched.
- **`tests/test_crafting_system.py`** — covers recipe/material catalog sizes, level-gated recipe availability, rarity-colour lookup, and the random material drop table (with `random.randint` patched to hit each rarity branch).
- **Run**: `python -m unittest discover -s tests -v`. Current status: **36 tests, all green** (`Ran 36 tests ... OK`). `py_compile` clean. See `tests/README.md` and ROADMAP.md P2 #8 (moved to Done).
- **Note for next run**: while writing the combat tests I saw one unconditional `print("DEBUG: Spell base damage ...")` still live at `Code/combat_system.py:266` — it slipped past the v1.7.8 debug-gating pass. Small follow-up, not addressed here to keep this change scoped to the test suite.

## 07/08/2026 - v2.1.0
### ✨ Characters now spawn into their last-played level (roadmap P1 #4)
**Loading (or creating) a character sent the player straight to the game board without rebuilding the world, so every character spawned into the default World 1-1 regardless of how far they'd progressed.**
- **Root cause**: `LevelManager` already persists `current_world`/`current_level` per character in `SaveProgression/progression_<name>.json` and restores it via `set_character()` → `load_progression()`. But the `CHARACTER_SELECT` and `CREATE_CHARACTER` key-handlers set `current_state = GameState.GAME_BOARD` *without* calling `setup_world_for_current_level()`. The world had only been built once, at startup, for the default 1-1 level — so the restored progression pointer was ignored and the player always landed in 1-1.
- **File: `main.py`** — added `enter_game_board_for_current_level()`: recenters the player (480, 480), calls `setup_world_for_current_level()` to regenerate the world/enemies/theme for the persisted level, snaps the camera to the player, then enters `GAME_BOARD`. Mirrors the world-setup half of `change_level()`.
- **File: `main.py`** — both the load-character and create-character paths now call `enter_game_board_for_current_level()` after `set_character()` instead of setting the state inline.
- **Unchanged**: explicit level selection still routes through `change_level()` (the "unless selected another level" case), and a brand-new character correctly starts in 1-1 (its fresh progression defaults there).
- **Verification**: `py_compile` clean; a headless progression round-trip test confirms a character advanced to World 2-3 has that level restored on re-select, which `enter_game_board_for_current_level()` then builds. See ROADMAP.md P1 #4 (moved to Done).

## 07/08/2026 - v2.0.6
### 🧹 Save-file tracking policy — runtime saves are no longer versioned (roadmap P1 #5)
**`Characters/*.json` and `SaveProgression/*.json` were tracked in git, so every local playtest produced a noisy uncommitted diff (character level/credits/inventory churn) that had nothing to do with code changes and risked clobbering another machine's saves on merge.**
- **Decision**: these are *live per-player save state*, not source or fixtures, so they are now **gitignored** rather than versioned. A fresh clone starts with no saved characters; the in-game character-creation flow writes them at runtime, and the loader already discovers characters by scanning `Characters/` for `*.json` (`Code/game_data.py`), so nothing depends on a committed save existing.
- **File: `.gitignore`** — added `Characters/*.json` and `SaveProgression/*.json` (with `!*/.gitkeep` negations), plus ignores for the stray `_t2` scratch file and `.git/*.stalebak` lock backups.
- **Untracked** the five previously committed live saves (`Characters/nora.json`, `Characters/vozy.json`, `SaveProgression/progression_Nora.json`, `progression_Vozy.json`, `progression_default.json`) via `git rm --cached` — the files stay on disk for the local player, they just leave version control.
- **Added** `Characters/.gitkeep` and `SaveProgression/.gitkeep` so both directories still exist in a fresh clone.
- Effect: playtesting no longer dirties the working tree with save churn, and pulling on another machine can't overwrite local progress. See ROADMAP.md P1 #5 (moved to Done).

## 07/07/2026 - v2.0.5
### 🚀 pygame → Arcade migration — central backend switch + hybrid shim (roadmap P1 #1)
**The Arcade backend is now wired end-to-end: rendering can route through `Code.gfx` (Arcade) while audio/timing/input keep using real pygame — controlled by a single switch. The legacy `python main.py` path is byte-for-byte unchanged.**
- **Why this was the blocker**: every gameplay module gets its `pygame` name from `Code/ui_components.py` via `from Code.ui_components import *` (and `main.py` has *no* pygame import of its own). Because that star-export re-binds `pygame` in each importer, flipping an individual module's own `import pygame` line had no effect — the star import always won. So the backend can only be switched from one place: ui_components.
- **File: `Code/ui_components.py`** — added the single backend switch. Reads `MEGITECH_BACKEND`: unset → `import pygame` (legacy, unchanged); `=arcade` → `from Code import gfx as pygame`. This selection star-exports to every gameplay module **and** `main.py` at once.
- **File: `arcade_app.py`** — sets `MEGITECH_BACKEND=arcade` before importing the game, so its `arcade.Window` now actually renders through the shim; marks its window surface `is_screen=True` so screen draws paint immediately (not recorded).
- **File: `Code/gfx.py`** — made the shim a **hybrid**: a module-level `__getattr__` (PEP 562) delegates any non-render attribute (`mixer`, `time`, `display`, `event`, `key`, `mouse`, `sprite`, `locals`, `error`, `Color`, …) to real pygame, while `draw`/`font`/`Rect`/`Surface`/`image`/`transform`/key-constants stay Arcade-backed. `init()`/`quit()` now delegate to real pygame so audio/font subsystems still initialize.
- **File: `Code/gfx.py`** — `Surface` now supports **off-screen draw targets**: a plain sized surface records draw ops (`fill`/`rect`/`circle`/`ellipse`/`line`/`lines`/`polygon`/`blit`) and **replays** them — translated, y-flipped, and optionally sub-rect clipped — when blitted onto the window. This unlocks the two patterns every render module uses: the semi-transparent HUD overlay (`Surface((w,h), SRCALPHA)` → draw onto it → blit to screen) and tile-sheet cell blitting (`screen.blit(sheet, pos, area_rect)`). Accepts pygame's positional `flags` arg (e.g. `SRCALPHA`).
- **Verification**: added a headless stub-backed test suite (5 tests, all passing): default path binds real pygame; arcade path binds gfx and star-exports it; hybrid delegation returns real pygame submodules; overlay replay produces correct y-flipped Arcade coords; tile-sheet `area` blit selects only the addressed cell. Full-tree `py_compile` clean.
- **⚠️ On-device smoke test still pending**: sandbox has no display/Arcade install; `pip install arcade && python arcade_app.py` on the Mac remains the final visual check.

## 07/07/2026 - v2.0.4
### 🐞 Resource regeneration was ~15× too fast (roadmap P4 #16)
**Harvestable resource nodes respawned every 40–80 seconds instead of the 10–20 minutes their own comments claimed.**
- **Root cause**: respawn timers were computed as `minutes * 60` (i.e. *seconds*) but the game loop runs at 15 FPS (`clock.tick(15)`), so each value was consumed as *frames* and ran 15× too fast.
- **File: `Code/ui_components.py`** — corrected `max_respawn_time` to true 15-FPS frame counts: Tree & Stream 600→9000 (10 min), Rock 900→13500 (15 min), Metal 1200→18000 (20 min), Brush 750→11250 (12.5 min).
- **File: `Code/crafting_system.py`** — `ResourceNode` respawn 3000→4500 (default arg and `max_respawn_time`), now a true 5 minutes at 15 FPS.
- Effect: harvested trees, rocks, metal, streams, brush, and crafting material nodes now take their intended real-world minutes to regrow, making resources a meaningful constraint again.

## 07/07/2026 - v2.0.3
### 🐞 Arcade foundation hotfix — pygame/Arcade OpenGL context conflict
**`python arcade_app.py` opened the window then crashed with `pyglet.gl.lib.GLException: No GL context; create a Window first`.**
- **Root cause**: `EnhancedGameManager.__init__` still calls `pygame.display.set_mode()` (needed so un-migrated modules can build fonts/convert images). On a real SDL video driver that creates a *second* OpenGL context and makes it current, stealing the context from Arcade/pyglet — so Arcade's `self.clear()` had no GL context.
- **File: `arcade_app.py`** - Set `SDL_VIDEODRIVER=dummy` before pygame's display initializes, giving pygame a valid off-screen video mode (surface/convert/font ops still work) with no real GL context to steal. Audio driver untouched, so sound still works. Also call `self.switch_to()` after building the manager to reclaim pyglet's GL context.
- **Note**: the per-frame `draw() error: argument 1 must be pygame.surface.Surface, not Surface` messages are expected and harmless during migration — they are un-migrated modules calling real pygame draw on the gfx shim surface, caught so the window stays alive. They disappear module-by-module as each is ported to `Code.gfx`.

## 07/07/2026 - v2.0.2
### 🐞 Arcade foundation hotfix — Window.screen attribute collision
**`python arcade_app.py` crashed on launch with `AttributeError: can't set attribute`.**
- **File: `arcade_app.py`** - `arcade.Window` (via pyglet) already defines a read-only `screen` property for the display, so the manager's render-target assignment `self.screen = gfx.Surface(...)` collided with it. Renamed the window's shim surface to `self._surface` and pointed `self.game.screen` at it instead. Window now constructs and launches.

## 07/07/2026 - v2.0.1
### 🚀 MAJOR: pygame → Arcade migration — foundation (Roadmap: GUI backend swap)
**Beginning the move from pygame to Arcade 3.x. This release lays the foundation; the legacy pygame path stays fully runnable while modules migrate one at a time.**
- **File: `Code/version.py`** (new) - Central single-source-of-truth for the game version (`__version__ = "2.0.1"`), window `CAPTION`, and active render `BACKEND`. Replaces scattered hardcoded version strings.
- **File: `Code/gfx.py`** (new) - pygame→Arcade compatibility/rendering shim. Emulates the exact slice of the pygame surface/draw/font API the codebase uses (`Surface.fill/blit/get_rect/set_alpha`, `draw.rect/circle/polygon/line/lines/ellipse`, `font.Font.render`, `image.load`, `transform.scale`, key + event constants) backed by Arcade draw calls. Handles the pygame(top-left, y-down) → Arcade(bottom-left, y-up) coordinate flip automatically so per-module migration is mechanical rather than a rewrite.
- **File: `arcade_app.py`** (new) - New Arcade `Window` entry point. Replaces main.py's hand-rolled `while running:` loop with `on_update`/`on_draw` callbacks, throttled to the original 15 Hz logic tick. Translates Arcade (pyglet) key + text events into the pygame-shaped events the existing `EnhancedGameManager` state machine already consumes — the game's state machine runs unchanged on the Arcade loop. Includes an on-screen backend/state overlay so the window is never blank during migration.
- **File: `main.py`** - Window caption now sourced from `Code.version.CAPTION` (central version) instead of a hardcoded string. No behavior change; `python main.py` still runs the legacy pygame build.
- **File: `requirements.txt`** (new) - Pins both backends during transition: `pygame>=2.5`, `arcade>=3.3`.
- **Migration path**: each render module (`ui_components`, `tile_map`, combat, inventory, store, rest, settings, crafting, character_creation, animated_player) will be ported `import pygame` → `from Code import gfx as pygame`, committed individually per gitflow, until pygame is fully retired.
- **⚠️ Verification pending on-device**: this sandbox has no display and no Arcade install; `pip install arcade` then `python arcade_app.py` on the Mac is required to smoke-test the window/loop/input foundation.

## 07/07/2026 - v1.7.8
### 🐞 Gate Debug Output (Roadmap P1 #6) ✅
**Verbose developer diagnostics no longer spam the player console**
- **File: `Code/debug.py`** (new) - Added a central `DEBUG` flag (off by default, opt-in via the `MEGITECH_DEBUG` env var) and a `debug_print()` helper that only emits when DEBUG is enabled, prefixing output with `DEBUG:` to preserve the prior log format
- **File: `Code/combat_system.py`** - Replaced all 14 unconditional `print(f"DEBUG: ...")` calls (spell/hit/damage/crit/stat diagnostics) with `debug_print(...)`
- **File: `Code/settings_system.py`** - Replaced all 5 unconditional `print(f"DEBUG: ...")` difficulty-application calls with `debug_print(...)`
- **Verified**: `py_compile` passes on all three files; with DEBUG off (default) `debug_print` is silent, and `MEGITECH_DEBUG=1` restores full output

## 07/07/2026 - v1.7.7
### 🔊 Main Game Sound Fix (Roadmap P0 #2) ✅
**Background music now plays correctly regardless of how the game is launched**
- **File: `Code/enhanced_combat_system.py`** - `SoundManager.play_music()` now resolves relative/working-directory-dependent paths against the absolute `sounds_dir`, so music loads no matter the current working directory (SFX already used absolute paths; music did not)
- **File: `Code/enhanced_combat_integration.py`** - Fixed `../Sounds` vs `Sounds` mismatch where `end_combat()` and the GAME_BOARD branch of `play_contextual_music()` checked `os.path.exists("../Sounds/world_music.ogg")` (always false from the repo root) but tried to play `"Sounds/world_music.ogg"` — world music never resumed. Now pass bare filenames and let `play_music()` resolve them
- **File: `Code/enhanced_combat_integration.py`** - Defined the missing `start_world_music()` hook on the game manager; `main.py` called `self.start_world_music()` when fleeing combat, which raised `AttributeError` (undefined method)
- **File: `Code/enhanced_combat_integration.py`** - Stopped calling `create_sound_directories()` during init and repointed it at the absolute Sounds dir; it previously created a stray `../Sounds` folder and wrote empty placeholder `.wav`/`.ogg` files that then failed to load
- **Verified**: headless smoke test (SDL dummy driver) confirms `world_music.ogg` and `battle_music.ogg` load and play from a non-repo working directory; missing menu/shop music degrades gracefully
- **Note**: Six SFX files ship as 0-byte placeholders and still can't load (`player_hurt`, `run_away`, `victory`, `menu_select`, `menu_move`, `door_open`) — tracked as ROADMAP #17

## 07/07/2026 - v1.7.6
### 💀 Death Credit Loss Fix (Roadmap P0 #1) ✅
**Dying now deducts credits on every death path**
- **File: `main.py`** - Legacy combat death (`handle_combat_action`) now deducts 5-15% of credits on death (was: respawn with no penalty)
- **File: `main.py`** - Removed duplicated victory block in `handle_combat_action` that double-awarded XP and credits
- **File: `main.py`** - `enter_boss_dungeon()` only switches to FIGHT state if `start_combat()` succeeds; previously a cooldown-blocked start left the game in FIGHT state with the penalty-free legacy combat path active
- **File: `Code/enhanced_combat_integration.py`** - `handle_combat_input()` now routes victory/defeat through `handle_victory()`/`handle_defeat()` before ending combat (rewards/penalties were skipped on the keypress path)
- **File: `Code/enhanced_combat_integration.py`** - Death now always costs at least 1 credit when the player has any (int truncation made small balances lose 0)

## 07/07/2026 - v1.7.5
### 🧹 Repo Hygiene (Roadmap items #3 & #4) ✅
**Added .gitignore and removed compiled bytecode from version control**
- **File: `.gitignore`** (new) - Ignores `__pycache__/`, `*.pyc`, `venv/`, `.idea/`, `.vscode/`, `.DS_Store`, and build artifacts
- **Untracked**: 13 compiled `.pyc` files under `Code/__pycache__/` and `assets/__pycache__/` plus root `.DS_Store` removed from git tracking (`git rm --cached`) - files remain on disk but no longer generate noisy diffs
- **File: `main.py`** - Main menu subtitle updated to "Start your Adventure NOW!"
- **Note**: Save-file tracking policy (`Characters/*.json`, `SaveProgression/*.json`) intentionally left unchanged pending roadmap item #5 decision

## 09/10/2025 - v1.7.3
### 🎮 UI Square Outline Fixes ✅
**Fixed menu item square outlines to properly fit all text content**
- **File: `Code/ui_components.py`** - Enhanced `draw_enhanced_menu()` function to dynamically calculate rectangle width based on actual text dimensions instead of using fixed width
- **File: `Code/inventory_system.py`** - Updated inventory item selection highlights to size rectangles based on item text content with proper padding
- **File: `Code/enhanced_combat_system.py`** - Fixed spell selection menu highlights to accommodate varying spell name lengths with dynamic width calculation
- **Result**: Menu items, inventory items, and spell selection now show perfectly fitted square outlines that expand to contain all text content

### 🏰 Boss Dungeon System Final Fixes ✅
**Resolved final combat system integration issues**
- **File: `main.py`** - Fixed `enter_boss_dungeon()` method to use correct `combat_integration` attribute instead of non-existent `enhanced_combat_manager`
- **File: `main.py`** - Corrected GameState reference from non-existent `ENHANCED_COMBAT` to proper `FIGHT` state
- **Result**: Boss dungeon spacebar interaction now properly starts boss battles with visual "🐉 BOSS BATTLE BEGINS! 🐉" feedback

### 📊 XP Bar System Fix ✅
**Fixed XP progress bar not updating or showing incorrect progress**
- **Problem**: Two different XP calculation systems were conflicting - character leveling used 150 XP per level, but XP bar used complex exponential system
- **File: `Code/ui_components.py`** - Updated `_get_xp_for_level()` method to match the simple 150 XP per level system used in `Code/game_data.py`
- **Result**: XP bar now correctly shows progress toward next level, updating properly after combat victories and other XP gains

### 🔮 Magic Damage Level Scaling ✅
**Enhanced magic damage to scale with both player stats and level**
- **File: `Code/enhanced_combat_system.py`** - Enhanced `calculate_spell_damage()` method to include player level parameter and level-based damage bonus
- **File: `Code/combat_system.py`** - Updated legacy combat system's spell damage calculation to include level scaling
- **Mechanics**: Magic damage now receives +1 damage bonus every 2 character levels (level bonus = (level-1)/2)
- **Critical Enhancement**: Spell critical hit chance now slightly increases with level (+1% every 5 levels)
- **Result**: All magic spells (damage, healing, drain) become more powerful as the player progresses in level, in addition to existing Intelligence/Wisdom stat bonuses


## 09/09/2025 - v1.7.1
### 🌍 Interactive Map Objects System
- **Tree Harvesting**: Trees now provide crafting materials when interacted with using spacebar
- **Resource Nodes**: Rocks, metal veins, streams, and brushes all provide crafting materials
- **Respawn Timers**: All harvestable objects respawn after being depleted
- **Balanced World Generation**: Reduced spawn counts for better navigation (8 trees vs 20+, fewer resource nodes)
- **World Aesthetics**: Removed flowers entirely, replaced with grass tiles for cleaner appearance
- **Structured Paths**: Created walking paths from center toward shop and rest areas in bottom-right

### 🏰 Boss Dungeon System
- **Boss Dungeons**: Mystical portal dungeons now spawn when all enemies are defeated in a level
- **Level Progression**: Players must defeat a boss to unlock the next level instead of auto-completing
- **Boss Battles**: Challenging boss enemies scaled to current world and difficulty level
- **Enhanced Rewards**: Boss victories provide 500 base credits vs 200 for regular completion

### 📁 Files Modified:

#### **main.py** (Extensive Changes):
- Added `self.dungeons = []` list for boss dungeon tracking
- Added `self.trees = []`, `self.rocks = []`, `self.metals = []`, `self.streams = []`, `self.brushes = []` lists
- Modified `check_level_completion()` to spawn dungeons instead of completing immediately
- Added `complete_level_after_boss()` method for post-boss level completion
- Added `enter_boss_dungeon()` method to trigger boss fights
- Enhanced `check_interactive_objects()` to detect all interactive objects (trees, rocks, metals, streams, brushes, dungeons)
- Completely rewrote `handle_map_object_interaction()` to handle spacebar harvesting and dungeon entry
- Added dungeon drawing in `draw_game_board()` method
- Updated tree respawn timers in `update()` method
- Updated help instructions to include harvesting and dungeon interaction
- Enhanced collision detection for trees and other objects

#### **Code/enhanced_combat_integration.py**:
- Modified `handle_victory()` method to detect boss fights via "Tier" == "boss"
- Added automatic level completion when boss enemies are defeated
- Enhanced victory messages for boss defeats with special formatting
- Boss victories now trigger `complete_level_after_boss()` automatically

#### **Code/ui_components.py**:
- Enhanced `Tree` class with harvesting mechanics, respawn timers, and material generation
- Enhanced `Rock` class with interactive mining and material drops
- Enhanced `Metal` class with vein harvesting and ore generation
- Enhanced `Stream` class with water collection mechanics
- Enhanced `Brush` class with foliage harvesting
- Added comprehensive `Dungeon` class with mystical portal effects, animations, and boss fight integration

#### **Code/tile_map.py**:
- Modified world generation to reduce object spawn counts
- Removed flower generation entirely
- Enhanced path generation toward shop and rest areas
- Improved object placement algorithms for better navigation

### 🎮 Gameplay Changes:
- **Interactive World**: All trees, rocks, metal veins, streams, and brushes can be harvested for crafting materials
- **Spacebar Interaction**: Universal spacebar key for harvesting resources and entering dungeons
- **Resource Management**: Objects respawn after depletion, creating sustainable resource gathering
- **Level Progression**: Level completion now requires defeating a boss in a mystical dungeon
- **Boss Dungeons**: Portal entrances appear in center of map with animated magical effects
- **Enhanced Combat**: Boss enemies provide significantly higher XP and credit rewards
- **Cleaner Navigation**: Reduced object density for easier movement and exploration

### 🎨 Visual Enhancements:
- **Animated Trees**: Swaying animation and color changes based on harvestable status
- **Resource Nodes**: Visual feedback showing when objects can be harvested vs depleted
- **Mystical Dungeons**: Animated portal entrances with glowing magical effects and floating particles
- **"BOSS DUNGEON" Text**: Golden glow effects and mystical styling
- **Special Victory Messages**: Boss defeats show trophy emojis and enhanced formatting
- **World Aesthetics**: Cleaner grass-based terrain without flower clutter
- **Structured Paths**: Clear walking routes toward important areas

### 🔧 Technical Improvements:
- **Modular Object System**: All interactive objects follow consistent patterns for harvesting and respawn
- **Boss Enemy Integration**: Proper boss scaling using existing `create_scaled_boss()` method
- **Enhanced Combat System**: Boss fight detection via enemy "Tier" property
- **Dungeon Architecture**: Portal objects integrate seamlessly with existing interaction system
- **Performance Optimization**: Reduced object counts improve game performance
- **Material Integration**: All harvested materials connect to existing crafting system
- **State Management**: Proper tracking of object states, respawn timers, and dungeon availability

### 🎯 User Experience:
- **Clear Progression**: Clear enemies → Enter dungeon → Defeat boss → Next level
- **Resource Gathering**: Intuitive spacebar interaction for all harvestable objects
- **Visual Feedback**: Console messages and visual effects for all player actions
- **Balanced Difficulty**: Higher stakes and rewards for level completion
- **Engaging Endgame**: More exciting conclusion to each level via boss battles
- **Maintained Features**: All existing systems (crafting, shops, rest areas) continue to work seamlessly

### 📋 Console Output Examples:
```
Harvested: Wood
Harvested: Iron Ore  
Harvested: Leather
Boss dungeon has appeared! Approach and press spacebar to enter.
🏰 BOSS DUNGEON APPEARS! 🏰
🐉 BOSS BATTLE BEGINS! 🐉
🏆 BOSS DEFEATED! Level Complete! Gained 500 XP and 750 credits!
```
- Spacebar interaction to enter boss dungeons
- Boss enemies provide significantly higher XP and credit rewards
- Visual feedback for dungeon appearance and boss victories

### 🎨 Visual Enhancements:
- Animated portal entrances with glowing magical effects
- Floating mystical particles around dungeon portals
- "BOSS DUNGEON" text with golden glow effects
- Special boss victory messages with trophy emojis

### 🔧 Technical Improvements:
- Proper boss enemy scaling using existing `create_scaled_boss()` method
- Integration with enhanced combat system for boss battles
- Dungeon objects follow same interaction pattern as other map objects
- Boss fight detection via enemy "Tier" property

### 🎯 User Experience:
- Clear progression system: Clear enemies → Enter dungeon → Defeat boss → Next level
- Higher stakes and rewards for level completion
- More engaging end-game for each level
- Maintains all existing features (harvesting, crafting, shops, rest areas)

## 09/08/2025 - v1.6
### - Fixed v.1.6.1
- Bug fixes, rest area, xp bar, xp when clearing world, combat increase. progression fixed to single player.
- Cleaned up file system, renamed game_states.py to main.py

## 09/07/2025 - v1.5.x
09/07/2025 - v1.5.2 - CRAFTING UPDATE
- Added
🔨 Complete Crafting System

New crafting_system.py module with comprehensive crafting mechanics
30+ crafting materials across 5 tiers (Common to Legendary)
20+ crafting recipes for consumables, weapons, armor, and accessories
Material drops from enemies and treasures based on level and type
Boss enemies have increased drop rates for rare materials
Treasure chests provide different material loot tables

⚗️ Crafting Features

Recipe categories: Consumables, Weapons, Armor, Accessories
Level requirements for advanced recipes
Material tier system (Common, Uncommon, Rare, Epic, Legendary)
Visual crafting UI with category filtering
Recipe availability based on player level and materials
Real-time inventory checking for craftable items

🎮 Crafting Integration

Press 'F' to open crafting menu
Arrow keys to navigate recipes
Left/Right arrows to change categories
Enter/Space to craft selected item
Materials automatically added to inventory from combat and treasures
Floating text notifications for material drops
Sound effects for successful crafting and material collection

📦 Material Drop System

Dynamic drop rates based on enemy level
Elite enemies: 2x drop rate multiplier
Boss enemies: Better tier materials
Treasure scaling: Higher value = better materials
Quantity varies by material tier (Common: 1-3, Rare: 1)

- Changed
🔧 Enhanced Loot System

Enemies now drop both items and crafting materials
Treasures provide credits and crafting materials
Combat rewards include material notifications
Updated floating text system for multi-line drops

## 09/05/2025 - v1.4.1
### - Fixed
🔧 **Difficulty Mode System** - Fixed difficulty multiplier not being applied to enemy HP and stats
- Added `set_difficulty_multiplier()` method to EnemyManager
- Enhanced settings integration to properly apply difficulty to all enemy managers
- Enemy HP and level now scale correctly with difficulty setting (0.5x to 2.0x)
- Added debug logging for difficulty application verification

⚔️ **Player Combat Stats Integration** - Fixed player stats not being used in combat calculations
- Enhanced `get_player_stats()` method with proper error handling and fallbacks
- Added `get_stats_from_character_data()` fallback method for direct stat reading
- Fixed combat damage, hit chance, and spell damage calculations to use actual player stats
- Added comprehensive debug logging for stat calculations
- Improved stat validation and null value handling

🎯 **Combat Balance Improvements**
- Enemy stats now properly scale with difficulty multiplier
- Added armor class scaling for enemies based on difficulty
- Enhanced critical hit calculations using actual player dexterity
- Improved spell damage scaling with intelligence/wisdom modifiers
- Added difficulty multiplier storage in enemy data for combat reference

### - Enhanced
📊 **Debug Information** - Added extensive debug logging for combat stat calculations
🎮 **Difficulty Display** - Enhanced difficulty setting display names (Very Easy to Nightmare)
⚙️ **Settings Integration** - Improved settings application across all game managers

## 09/04/2025 - v1.3.0 - ENVIRONMENTAL TREE SYSTEM
### - Added
🌳 **Complete Tree System**
- Tree class with collision detection for blocking player movement
- Three tree types: Normal, Oak, and Pine with distinct visual styles
- Animated tree swaying effects for more natural environment
- World-themed tree generation based on current level/world
- Smart tree placement avoiding conflicts with other objects
- Collision system prevents player from walking through trees

🎨 **Enhanced Environmental Generation**
- Level-based tree count and type selection
- World 1 (Grassland): 15-25 mixed trees (Normal, Oak)
- World 2 (Ice): 8-15 Pine trees for arctic theme
- World 3 (Shadow): 12-20 darker trees for mysterious atmosphere
- World 4 (Elemental): 5-12 mixed types for chaotic environment
- World 5 (Cosmic): 3-8 mystical trees for otherworldly feel

🎮 **Improved Gameplay Mechanics**
- Tree collision detection with movement rollback system
- Trees drawn behind other objects for proper depth layering
- Updated movement system to handle environmental obstacles
- Enhanced world navigation requiring strategic pathfinding around trees

🔧 **Technical Improvements**
- Tree objects inherit proper collision and drawing systems
- Integration with existing world generation and level systems
- Camera-aware tree rendering for performance optimization
- Proper tree scaling and positioning within world bounds

### - Changed
🗺️ **World Generation Updates**
- Modified setup_enhanced_world_objects() to include tree creation
- Enhanced setup_world_objects() fallback method with tree support
- Updated collision detection to prioritize tree blocking
- Improved object spacing algorithms to accommodate larger tree objects

🎯 **Movement System Enhancements**
- Added previous position tracking for collision rollback
- Tree collision checking with movement prevention
- Enhanced player update loop with environmental obstacle detection
- Improved camera update logic to handle blocked movement

### - Technical Details
- Tree class with configurable size, type, and collision properties
- Smart positioning algorithm with 45-pixel minimum distance from other objects
- Visual variety with trunk colors, leaf colors, and size variations
- Animation system with subtle swaying based on world position and time
- Proper integration with existing game state and level management systems

---

## 09/03/2025 - v1.3.0 - MULTI-LEVEL SYSTEM WITH WORLD PROGRESSION
### - Added
🗺️ Complete Multi-Level System

5 distinct worlds with 4 levels each (20 total levels)
Progressive difficulty scaling with world themes
Level completion system with automatic unlocking
World progression: Grasslands → Ice Kingdom → Shadow Realm → Elemental Chaos → Cosmic Nexus
Level persistence system saves current world/level on exit
Each world has unique enemy types, themes, and visual styles

🎮 Enhanced Level Selection Interface

Comprehensive level select screen accessible from main menu and in-game (L key)
Visual world tabs with unlock status indicators
Level difficulty ratings (Easy, Normal, Hard, Expert, Nightmare)
Recommended character level for each area
Current level highlighting and selection animations
Locked level indicators with progression requirements

⚔️ World-Themed Enemy System

5 unique enemy themes matching world aesthetics
50+ different enemy types across all difficulty tiers
Theme-specific boss encounters for each world
Progressive enemy scaling: Basic → Elite → Champion → Ancient → Boss
World-appropriate enemy names and combat aspects
Enhanced reward multipliers based on enemy tier

🌍 Dynamic World Generation

Level-based enemy and treasure spawning
Multiple rest areas in higher difficulty worlds
World-specific background colors and atmospheric effects
Treasure quantity scaling with world difficulty
Strategic rest area placement for challenging levels

📊 Enhanced Progression System

Level completion bonuses with scaling rewards
Automatic next-level unlocking upon area completion
World progression tracking with persistent save system
Enhanced status overlay showing current world and difficulty
Character progression now tied to world completion

🎨 Visual and Audio Enhancements

World-specific color schemes and themes
Enhanced status display with level information
Improved enemy variety with thematic designs
Level completion celebration effects
World transition animations and feedback

- Technical Improvements

Modular LevelManager class for progression tracking
WorldLevelGenerator for dynamic content creation
LevelSelectScreen with full navigation system
Enhanced EnemyManager with theme-based generation
Persistent progression system with JSON save files
Integration with existing combat and character systems

- Gameplay Balance

Difficulty curves calibrated for character progression
World-appropriate loot multipliers (1.0x to 4.0x)
Enemy health scaling from 60 HP (basic) to 666 HP (final boss)
Strategic rest area placement increases with world difficulty
Level completion requirements encourage full exploration

## 09/03/2025 - v1.2.0 - REST SYSTEM WITH COOLDOWN
### - Added
🛌 **Complete Rest System**
- Strategic rest areas placed throughout the world (8 locations)
- 3-minute cooldown timer system for balanced gameplay
- 75-90% HP/MP restoration with randomized recovery amounts
- Visual availability indicators (pulsing when ready, cooldown display)
- Enhanced rest area graphics with blue tent designs
- Free healing alternative to expensive consumable potions

🎨 **Enhanced Rest Area Visuals**
- Dynamic color-coded rest areas (blue=available, red=cooldown, gray=recently used)
- Pulsing animations and glow effects for available rest areas
- Cooldown timer display directly on rest areas
- "Walk into to rest" interaction hints with fade effects
- Enhanced tent graphics with improved visual feedback

📊 **Rest Status HUD System**
- Bottom-left corner rest status display
- Real-time cooldown timer (MM:SS format)
- "Rest Available" indicator when ready to use
- Integration with existing UI systems
- Persistent status tracking across game sessions

🎵 **Audio Integration**
- Rest interaction sound effects
- Healing audio feedback for successful rest
- Error sounds for cooldown attempts
- Integration with existing enhanced audio system

⚖️ **Balanced Resource Management**
- Strategic rest area placement in world corners and center
- Collision detection prioritizes rest areas for better UX  
- Rest areas safe from enemy spawn interference
- Cooldown system prevents rest spam while allowing strategic planning

### - Technical Improvements
- Modular RestManager class for cooldown and interaction logic
- EnhancedRestArea class extending base RestArea with animations
- Integration with existing collision detection system
- Proper world-to-screen coordinate conversion for rest areas
- Rest system update loop integration with main game logic

## 09/02/2025 - v1.1.2 - COMBAT SYSTEM HOTFIX
### - Fixed
🔧 Combat System Fixes

Fixed 'EnhancedCombatManager' object has no attribute 'add_combat_log' error
Enhanced music loading error handling to prevent crashes when sound files are missing
Improved sound system fallback behavior for missing audio files
Added proper error messages for missing music files instead of silent failures
Fixed combat system integration issues that were causing crashes on startup
Fixed "invalid color argument" errors in UI components and combat animations
Fixed "invalid color argument" error when colliding with enemies and entering combat
CRITICAL FIX: Replaced Unicode emojis with ASCII text in combat interface to prevent rendering errors
Fixed combat title rendering error that was preventing combat screen from displaying
Replaced all problematic Unicode characters (⚔️🔮🧪🏃❤️💙⭐🔥❄️⚡✨💚) with safe ASCII alternatives
Added comprehensive error handling in combat text creation and rendering
Fixed color validation in combat animations and particle systems
Added coordinate validation to prevent invalid drawing positions

- Improved
🎵 Audio System Improvements

Better file existence checking before attempting to load music files
More graceful degradation when sound system is unavailable
Enhanced error reporting for debugging audio issues
Sound system now continues working even if individual files are missing

🎨 Visual System Improvements

Added robust color validation throughout the UI system
Enhanced drawing coordinate handling to prevent rendering errors
Improved animation system stability with better value bounds checking
Better fallback handling for visual effects when rendering fails
Added comprehensive error handling in combat text and animation systems
Enhanced combat entry animations with safer initialization
Improved particle system color validation
Combat interface now uses safe ASCII characters instead of Unicode emojis for better compatibility

## 09/02/2025 - v1.1.1 - MODULAR STORE SYSTEM
### - Added
🏪 **Store System Modularization**
- Created dedicated store_system.py module for better code organization
- Enhanced StoreManager class with improved functionality and UI
- StoreIntegration class for seamless game integration
- Improved error handling and visual feedback for purchases
- Better separation of concerns between game logic and store functionality

### - Changed
📦 **Code Architecture Improvements**
- Moved Store class and StoreItem class to store_system.py
- Refactored game_states.py to use new modular store system
- Simplified store input handling and purchase logic
- Enhanced store UI with better visual organization
- Improved collision detection for store interactions

### - Fixed
🔧 **Store System Fixes**
- Fixed store exit cooldown handling through proper integration
- Improved store navigation and scrolling functionality
- Better visual feedback for purchase attempts and insufficient funds
- Enhanced auto-equipment functionality for purchased items

## 09/01/2025 - v1.1.0 - COMBAT EDITION WITH SOUND & ANIMATION
### - Added
🎵 **Complete Audio System Integration**
- Dynamic background music system (menu, world, combat, shop themes)
- Comprehensive sound effects library (40+ different sounds)
- Contextual audio that changes based on game state
- Volume controls and audio fallback for missing files

⚔️ **Enhanced Combat System**
- Advanced turn-based combat with visual effects
- Animated spell casting circles with rotating magical runes
- Sword slash animations with motion blur trails
- Impact flash effects for hits and critical strikes
- Healing sparkle animations for restoration spells
- Screen shake effects for powerful attacks and criticals
- Enhanced floating combat text with bounce and fade effects

🎭 **Visual Combat Enhancements**
- Spell-specific animations (fire, ice, lightning, heal, drain)
- Combat animation system with multiple effect types
- Pulsing health warnings when HP is low
- Enhanced UI with animated selection highlights
- Status effect icons and visual indicators
- Combat log with color-coded messages and fade effects

🔊 **Sound Effect Categories**
- Combat sounds: sword hits, spell casting, critical hits
- UI sounds: menu navigation, item pickup, shop interactions  
- World sounds: footsteps, door opening, treasure collection
- Victory/defeat musical stings and fanfares
- Character-specific sounds for different spell types

⏰ **Combat Balance System**
- Post-combat immunity periods to prevent spam
- Combat entry cooldowns for strategic gameplay
- Enhanced reward system based on enemy difficulty
- Level-scaled loot drops and experience gains
- Elite/Ancient enemy bonus reward multipliers

🎯 **Enhanced Game Integration**
- Seamless integration with existing game systems
- Automatic sound directory creation with placeholders
- Backward compatibility with existing save files
- No breaking changes to existing gameplay mechanics

### - Technical Improvements
- Modular sound manager with fallback support
- Enhanced combat manager with animation pipeline
- Improved combat text system with multiple effect types
- Screen shake system with intensity scaling
- Audio context switching based on game state

## 09/01/2025 - v1.0.4
### - Fixed
🏪 Store exit collision loop - Player now moves away from store on exit
🔒 Added store entry cooldown to prevent immediate re-entry
🎯 Enhanced store exit with proper player repositioning and camera update

## 09/01/2025 - v1.0.3
### - Added
- 🎮 Enhanced Magitech RPG - Combat Edition
- 🏃 Animated character with 8-frame sprites
- 🗺️ Tile-based world map system
- 📷 Smooth camera following
- ✨ Modular code architecture
- 🎯 Enhanced collision detection
- 👤 Character selection system
- 🎛️ Toggleable instructions panel (F1)
- ⚔️ Advanced turn-based combat system
- 🔮 Spell casting with mana management
- 💊 Inventory items usable in combat
- 📊 Character stats affect combat
- 🌟 Status effects and critical hits

---

> **⚠️ LEGACY / DISCONTINUED PROTOTYPE (v23–v29, Aug 2025) — read before trusting the entries below.**
>
> The version history from here down (v23–v29, plus the `2025-07-25` seed entry) documents an **early client/server multiplayer prototype** — a separate "GUI Client for Multiplayer" that talked to a standalone HTTP server. It referenced modules and components that **no longer exist anywhere in this repository**: `NetworkManager_Class.py`, `Server_v1`/`Server_v2`/`Server_v3`, `config.py`, and `classes.py`. That prototype was **abandoned**; the project was subsequently rebuilt as the **single-player** game that all `v1.x`/`v2.x` history describes. The only surviving artifacts are two orphaned SQLite files under `assets/` (`rpg_server.db`, `OLD_rpg_server.db`), which are dead data, not live dependencies — no current code opens them.
>
> **Is multiplayer still a goal?** Yes, but as a *future, from-scratch* effort — see ROADMAP.md **P6 (#40/#41): "Change version number to v3.0.1 — Add multi player"**. That work is planned to add a fresh server/client layer alongside the existing single-player mode; it is **not** a resumption of this discontinued prototype and shares none of its code. Future roadmap items should plan around a *new* server component, and should not assume any of the `Server_v*` / `NetworkManager_*` code below is available.
>
> _Reconciliation note: this banner closes ROADMAP.md P3 #12 (v2.1.16, 07/10/2026). The entries below are preserved verbatim as historical record._

## 08/17/2025 - v29...
### - Added
- Added delete character from local and server (v24)
- Added delete session from server (v25)
- Added sync multiplayer game board/book/chapter/enemy/loot (v26)
- Added Take turns in multi-player battle with all players. (v27)
- Added config.py holds mostly vars that could be easily changed
- Added NetworkManager_Class.py moved class to it
- Added classes.py and moved all other classes to it

### - Fixed
- Server_v1 with the correct functions to fix session deletion.
- Server_v1 to sync player and game status/book/chapter/enemy/loot
- Fixed Server_v2 database location to assets folder 
- Fixed Server_v3 with turns in the fight screen while in multi-player
- Fixed Single player combat screen health and damage issues
- Fixed ESC from game board single player, now directs you back to the main menu
- Started cleaning up code
- Fixed Need to nerf player damage, by making the enemy stronger
- Clean up old files

### - Bugs
- Second players actions not syncing to server... (Working on this v28)
- Delete character from server not an option at this time...
- Need to nerf player damage... 
- Battle screen not taking turns

## 08/16/2025 - v23
### - Notes
This is a GUI Client for Multiplayer
This is based off the GUI_v18 Single player game... (This is the BEST Code at this time 08/14/2025)
This uses Server_v1 as of 08/14/2025
- Server_v1 uses HTTP on port 8080, API, and JSON...
This is NOT working code at this time, going to be merging the client_gui_v2 into this codeset.

### Added
- Added Class NetworkManager
- Added all extra imports
- Changed to v23, v20 seemed pretty close.
- Multiplayer Create screen now has dropdowns for Class and Race

### - Fixed
- Chat window not in front (FIXED)
- Battling with multiplayer game board not showing other player, Session getting stuck on server. (FIXED)
- Need to change game board sub menus to ctrl key vs just letter, causing issues. (FIXED)
- Fixed Character data not saving to server


## - 2025-07-25
### Added
- Basic structure and initial features.

### Fixed
- None




The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Describe new features.
- If applicable, mention the issue or pull request number (e.g., #123).

### Changed
- Describe changes in existing functionality.
- For example, refactoring or improvements to existing features.

### Deprecated
- Describe features that are still available but will be removed in future releases.
- Explain why they are deprecated and suggest alternatives.

### Removed
- Describe features that have been removed in this release.
- Link to previous changelog entries or discussions if necessary.

### Fixed
- Describe bug fixes.
- Mention the bug report or issue number (e.g., #456).

### Security
- Describe any security vulnerabilities addressed.


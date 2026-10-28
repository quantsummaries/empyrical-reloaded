# Empyrical Reloaded — Learning Roadmap

Entry-points and recommended reading order for learning this codebase.
All paths below are relative to the repo root `empyrical-reloaded/`.

Empyrical is intentionally small and flat: `src/empyrical/` has no
sub-packages. Everything lives in four top-level modules.

## 0. Layout at a glance

| File | Size | Purpose |
|---|---|---|
| `src/empyrical/__init__.py` | 2 KB | Public API — re-exports everything users import |
| `src/empyrical/stats.py` | 66 KB | All return / risk / alpha-beta metrics |
| `src/empyrical/utils.py` | 22 KB | Input validation, annualization, date helpers |
| `src/empyrical/perf_attrib.py` | 6 KB | Regression-based factor attribution |
| `src/empyrical/periods.py` | <1 KB | `DAILY / WEEKLY / MONTHLY / QUARTERLY / YEARLY` |
| `src/empyrical/deprecate.py` | 1.5 KB | Deprecation decorators |

There are **no notebooks** in this repo. The two best "usage examples" are
`tests/test_stats.py` (73 KB) and `tests/conftest.py`.

## 1. Setup and orientation

- [ ] Install in editable mode inside the existing `.venv` (or verify it
      already is: `pip show empyrical-reloaded`).
- [ ] Read `README.md` end-to-end (Python 3.10+, numpy>=1.23.5, pandas>=1.3,
      scipy>=0.15.1; optional `yfinance` / `pandas-datareader`).
- [ ] Skim `docs/source/index.rst`, `stats.rst`, `utils.rst`,
      `perf_attrib.rst` — these are the auto-generated API reference.
- [ ] Run the test suite once to confirm green: `pytest tests/ -q`.

## 2. Master the data contract (do this before any metric)

Every function in `stats.py` takes a returns series. Before reading any
metric, understand:

- [ ] What shape / dtype / index does `returns` need? (look at
      `utils.py:to_series`, `utils.py:downcast`, `utils.py:convert_to_pandas`).
- [ ] What is the `period` argument and how does `annualization_factor` in
      `stats.py` convert DAILY/WEEKLY/... into a yearly multiplier?
- [ ] Why do pairs like `alpha_beta` vs `alpha_beta_aligned` exist? Read one
      pair (e.g. `stats.py:alpha_beta` and `stats.py:alpha_beta_aligned`)
      back-to-back and note the index-alignment logic.
- [ ] Pick one benchmark-free metric (`max_drawdown`) and trace its call
      graph: `max_drawdown → drawdown_series → utils`.

## 3. Walk through `stats.py` in groups

Read in this order — each group adds one concept. Open the corresponding
test section in `tests/test_stats.py` side-by-side.

- [ ] **Basic returns**: `simple_returns`, `cum_returns`, `cum_returns_final`,
      `aggregate_returns`, `annual_return`, `cagr`.
- [ ] **Drawdown**: `drawdown_series`, `max_drawdown`, `roll_max_drawdown`.
- [ ] **Volatility**: `annual_volatility`, `roll_annual_volatility`,
      `downside_risk`.
- [ ] **Risk-adjusted return**: `sharpe_ratio`, `sortino_ratio`,
      `calmar_ratio`, `omega_ratio`, `tail_ratio`, `excess_sharpe`,
      `stability_of_timeseries`.
- [ ] **Alpha / beta vs a benchmark**: `alpha_beta`, `alpha`, `beta` and
      their `_aligned` twins; then `roll_alpha_beta`, `roll_alpha`,
      `roll_beta`.
- [ ] **Capture ratios**: `capture`, `up_capture`, `down_capture`,
      `up_down_capture`, `batting_average`, `up_alpha_beta`,
      `down_alpha_beta`, plus the `roll_*` versions.
- [ ] **Tail risk**: `value_at_risk`, `conditional_value_at_risk`,
      `gpd_risk_estimates` (generalized Pareto — this is the most
      advanced piece; read it last, it's self-contained).

## 4. Support modules

- [ ] Read `src/empyrical/periods.py` (~10 lines — the period constants and
      their annualization multipliers).
- [ ] Read `src/empyrical/utils.py` fully — this is where all input
      coercion, NaN handling, and date arithmetic happens; most "weird
      behavior" surprises live here.
- [ ] Read `src/empyrical/deprecate.py` (~50 lines) — note which public
      functions are deprecated.

## 5. Performance attribution

- [ ] Read `src/empyrical/perf_attrib.py`: `perf_attrib`, `compute_exposures`.
      Understand how it regresses strategy returns on Fama-French factor
      returns and decomposes performance into factor exposures + specific
      return.
- [ ] Cross-read `tests/test_perf_attrib.py` to see expected inputs
      (factor returns DataFrame, positions DataFrame).

## 6. Hands-on verification

Empyrical has no demo notebook; build a tiny one.

- [ ] Pull a few years of returns with `yfinance` (e.g. SPY vs. a
      benchmark) — optional dep already installed?
- [ ] Compute `sharpe_ratio`, `sortino_ratio`, `max_drawdown`, `cagr`,
      `alpha_beta` against SPY. Sanity-check the numbers by hand or against
      a second source (e.g. a quick Excel calculation).
- [ ] Deliberately feed mis-aligned series to `alpha_beta` vs
      `alpha_beta_aligned` and observe the difference — this locks in why
      the aligned variants exist.

## 7. Reverse-engineering angle (cross-library)

- [ ] Open `pyfolio-reloaded/src/pyfolio/timeseries.py` and list which
      empyrical functions pyfolio wraps. This is how empyrical is actually
      consumed in practice.
- [ ] Open `alphalens-reloaded/src/alphalens/performance.py` and see how it
      uses empyrical for IC-related statistics.
- [ ] Note any wrappers that add conventions pyfolio/alphalens expect
      (e.g. NaN handling, risk-free rate default, period default) — these
      should be captured in `CODE_REVIEW.md`.

## 8. Deliverable

- [ ] Write `CODE_REVIEW.md` at the repo root, following the structure
      already used in `pyfolio-reloaded/CODE_REVIEW.md` and
      `alphalens-reloaded/CODE_REVIEW.md`:
      warmup → overview → dependencies → module guide → primary workflow →
      findings (ordered by severity) → API / behavior changes →
      documentation updates completed.
- [ ] Update `../../PROJECT-CONVENTIONS.md` section 7 (working-state
      snapshot) to reflect that empyrical is now documented.

## Suggested order

1. Setup + run tests green (§1)
2. Lock in the data contract (§2) — 30 min, saves hours later
3. Walk `stats.py` groups (§3) with tests open
4. Read `utils.py` (§4)
5. `perf_attrib.py` (§5)
6. Hands-on yfinance notebook (§6)
7. Cross-library consumption (§7)
8. Write `CODE_REVIEW.md` (§8)

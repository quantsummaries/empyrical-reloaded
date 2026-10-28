# Empyrical Documentation

> **Version**: written against branch `yzeng` at HEAD `bc01011` (2026-10-27, Python 3.12 / pandas 3.x compatibility). Prior revision: HEAD `fa0bbd7` (2026-10-09).

## Table of Contents
- [Review Addendum](#review-addendum)
- [Overview](#overview)
- [Package dependencies](#package-dependencies)
- [alphalens-style module guide](#module-guide)
  - [stats](#stats)
  - [utils](#utils)
  - [perf_attrib](#perf_attrib)
  - [periods](#periods)
  - [deprecate](#deprecate)
- [Primary workflow](#primary-workflow)


## Review Addendum
_Originally written at HEAD on 2026-10-09 (branch `yzeng`); last re-verified
at HEAD `bc01011` on 2026-10-27._

### Scope reviewed

- `src/empyrical/stats.py`
- `src/empyrical/utils.py`
- `src/empyrical/perf_attrib.py`
- `src/empyrical/periods.py`
- `src/empyrical/deprecate.py`
- `src/empyrical/__init__.py`
- related tests under `tests/`

### Findings (ordered by severity)

1. **Medium (optional dep drift)**: `utils.get_fama_french` and
   `utils.get_treasury_yield` rely on `pandas-datareader`, which is
   incompatible with Python >= 3.12. **Improved in `bc01011`**: the import
   failure is now captured (`_pandas_datareader_import_error`) and re-raised
   as a clear `ImportError("Install a pandas-3-compatible pandas-datareader
   build ...")`, so these paths fail loudly instead of silently on modern
   Python. The dependency drift itself is unresolved — an alternative data
   source still needs to be wired in.
   - Ref: `README.md`, `src/empyrical/utils.py`.
2. **Low (naming)** : `roll_downsize_risk` is a deprecated alias of
   `roll_downside_risk`; the typo ("downsize") is preserved for backwards
   compatibility but should not be used in new code.
   - Ref: `src/empyrical/stats.py`.
3. **Low (rolling factory indirection)**: Most `roll_*` functions are
   generated at import time by `utils._create_unary_vectorized_roll_function`
   / `_create_binary_vectorized_roll_function`. Their bodies are not
   visible as `def roll_*` source, which makes static readers (and IDE
   jump-to-definition) harder to navigate.
   - Ref: `src/empyrical/utils.py`.

### Re-verified 2026-10-27 at HEAD `bc01011` (fa0bbd7..bc01011)

The pandas 3.x / Python 3.12 pass (`47aa89f`, `bc01011`) hardened many
metrics against degenerate inputs. Key additions to watch:

- `stats.aggregate_returns` — WEEKLY grouping now pairs the **ISO week with
  the ISO year** (`isocalendar()[0]`) instead of the calendar year, so a
  week that crosses the year boundary is no longer split.
- `stats.drawdown_series` — ndarray input now drops the anchor row
  (`out = out[1:]`), so its shape matches the number of returns (Series /
  DataFrame inputs already did).
- New private `stats._zero_dispersion_std` — forces the denominator std to 0
  when all present values are identical, so `sharpe_ratio` and
  `excess_sharpe` return NaN (not an arbitrary ~1e15 finite ratio) for
  constant returns; `excess_sharpe` also leaves an undefined tracking error
  as NaN instead of converting to 0 (which became infinity).
- `stats.gpd_es_calculator` — returns `np.inf` when the fitted shape ≥ 1
  (the fitted GPD tail has no finite mean).
- `stats.conditional_value_at_risk` / `value_at_risk` — omit NaN before
  computing the tail; empty or all-NaN input returns NaN.
- `stats.batting_average` — drops non-finite active / benchmark observations
  and aligns Series by date; an empty subset returns NaN.
- `stats.beta_fragility_heuristic_aligned` — returns NaN for < 3 pairs and
  uses floor division for the mid index; the convex-combination weights were
  swapped to the correct orientation.
- `utils.up` / `utils.down` — filter with a new `_paired_mask` so only
  present return / factor pairs are used.
- `utils._roll_pandas` — rewritten to build a value list plus an index slice
  (no dict reconstruction), preserving dtype and the tail index.
- `utils.get_fama_french` / `get_treasury_yield` / `get_symbol_returns_from_yahoo`
  — clearer `ImportError`s; `end` optional; `PeriodIndex` → timestamp before
  tz-localize; Yahoo now uses `auto_adjust=False` and re-raises after
  warning; `get_returns_cached` uses `pd.to_datetime(..., utc=True)`.
- `perf_attrib.perf_attrib` — `pd.concat(..., sort=False)` added.

### API / behavior changes captured

- Public API is exported from `empyrical/__init__.py` as
  `from empyrical import stats, perf_attrib, periods, utils, deprecate`.
- `stats.annualization_factor(period, annualization)` is the single point
  where period labels (`DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, `YEARLY`)
  are converted into yearly multipliers; every annualized metric flows
  through it.
- Pairs of functions `foo` vs. `foo_aligned` exist for cross-sectional
  statistics (alpha, beta, alpha_beta, capture, tail-risk, GPD estimates):
  the un-suffixed variant aligns inputs via `utils._aligned_series`; the
  `_aligned` variant assumes pre-aligned inputs and is faster.
- Most `roll_*` statistics are factory-generated; `roll_alpha_beta` is
  handwritten and delegates to `roll_alpha_beta_aligned`.
- `perf_attrib.perf_attrib(...)` regresses portfolio returns on Fama-French
  factor returns and decomposes performance into factor exposures +
  specific return.

### Documentation updates completed

- `DEPENDENCIES.md` — layered function call graph (Level 0–4, rolling
  factory table, module tree, key observations).
- `CODE_LEARN.md` — learning roadmap.
- Re-verified at HEAD `bc01011` on 2026-10-27 (this addendum): the pandas
  3.x / Python 3.12 pass `fa0bbd7..bc01011`.

[⬆ 回到目录](#table-of-contents)

## Overview
Empyrical is a flat, dependency-light library of financial return and risk
metrics. It is the numeric core consumed by `pyfolio-reloaded` and
`alphalens-reloaded`: both projects forward deprecated metrics to
empyrical at runtime. The package has no sub-packages; every public
function lives in one of five top-level modules.

[⬆ 回到目录](#table-of-contents)

## Package dependencies
- Runtime: `numpy>=1.23.5`, `pandas>=1.3.0`, `scipy>=0.15.1`.
- Optional: `yfinance` (price data; `auto_adjust=False` since `bc01011`),
  `pandas-datareader` (Fama-French factors, FRED treasury yields; requires a
  pandas-3-compatible build on Python >= 3.12 — the code now raises a clear
  `ImportError` when it is missing).
- Downstream: `pyfolio-reloaded` and `alphalens-reloaded`.

[⬆ 回到目录](#table-of-contents)

## Module guide
### `stats`

The 66 KB main module. All metrics take a returns series (plus, where
relevant, a benchmark returns series) and a `period` argument defaulting
to `DAILY`.

Grouped by purpose:

- **Basic returns**: `simple_returns`, `cum_returns`, `cum_returns_final`,
  `aggregate_returns`, `annual_return`, `cagr`.
- **Drawdown**: `drawdown_series`, `max_drawdown` (and `roll_max_drawdown`).
- **Volatility**: `annual_volatility`, `roll_annual_volatility`,
  `downside_risk`.
- **Risk-adjusted return**: `sharpe_ratio`, `sortino_ratio`,
  `calmar_ratio`, `omega_ratio`, `tail_ratio`, `excess_sharpe`,
  `stability_of_timeseries`.
- **Alpha / beta vs benchmark**: `alpha_beta`, `alpha`, `beta` and their
  `_aligned` twins; rolling variants `roll_alpha_beta`, `roll_alpha`,
  `roll_beta`.
- **Capture**: `capture`, `up_capture`, `down_capture`, `up_down_capture`,
  `batting_average`, `up_alpha_beta`, `down_alpha_beta` (plus `roll_*`).
- **Tail risk**: `value_at_risk`, `conditional_value_at_risk`,
  `gpd_risk_estimates` (generalized Pareto; self-contained, most advanced).

### `utils`

Shared plumbing. Most "weird behavior" surprises live here.

- Input coercion: `to_series`, `downcast`, `convert_to_pandas`,
  `_flatten`, `_to_pandas`.
- Alignment: `_aligned_series`, `_adjust_returns`.
- NaN reductions: `nanmean`, `nanstd`, `nansum`, `nanmax`, `nanmin`,
  `nanargmax`, `nanargmin`, `up`, `down`.
- Rolling: `rolling_window`, `_roll_ndarray`, `_roll_pandas`,
  `_create_unary_vectorized_roll_function`,
  `_create_binary_vectorized_roll_function`.
- Data retrieval: `get_fama_french`, `get_symbol_returns_from_yahoo`,
  `get_treasury_yield`, `get_returns_cached`, `_1_bday_ago`,
  `cache_dir`, `ensure_directory`, `data_path`, `get_utc_timestamp`.

### `perf_attrib`

- `compute_exposures(positions, factor_returns)` — regression-based factor
  exposure aggregation.
- `perf_attrib(returns, positions, factor_returns, ...)` — end-to-end
  attribution: decomposes portfolio return into factor contributions plus
  specific return.

### `periods`

Four constant strings: `DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`,
`YEARLY`. No functions. The annualization multipliers live alongside in
`stats.annualization_factor`.

### `deprecate`

Single `deprecated` decorator. Used by `pyfolio.timeseries` legacy
wrappers to forward to empyrical; rarely invoked inside empyrical itself.

[⬆ 回到目录](#table-of-contents)

## Primary workflow
Empyrical is a library, not an application. Typical call pattern:

```python
from empyrical import sharpe_ratio, max_drawdown, alpha_beta

sr = sharpe_ratio(returns, risk_free=0.02, period='daily')
mdd = max_drawdown(returns)
a, b = alpha_beta(returns, benchmark_returns)
```

Downstream callers (pyfolio, alphalens) usually:

1. Build a returns series from their internal data model.
2. Call the relevant `stats.*` function directly.
3. Treat empyrical as a stateless numeric layer; no state is held between
   calls.

[⬆ 回到目录](#table-of-contents)
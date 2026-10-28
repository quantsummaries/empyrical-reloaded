# Empyrical Documentation

> **Version**: written against branch `yzeng` at HEAD `fa0bbd7` (2026-10-09).

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
_Originally written at HEAD on 2026-10-09 (branch `yzeng`)._

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
   incompatible with Python >= 3.12 (noted in README). These paths will
   silently fail on modern Python unless an alternative data source is
   wired in.
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
- Optional: `yfinance` (price data), `pandas-datareader` (Fama-French
  factors, FRED treasury yields; incompatible with Python >= 3.12).
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
# Empyrical Function Dependencies

> **Version**: written against branch `yzeng` at HEAD `bc01011` (2026-10-27, Python 3.12 / pandas 3.x compatibility). Prior revision: HEAD `fa0bbd7` (2026-10-09).

This document maps the in-package function calls in `src/empyrical`. It is
intended as a navigation aid for reviewing implementation changes: a change to
a lower-level function may affect every caller listed beneath it.

Dependencies below are direct calls between Empyrical functions. Calls into
NumPy, pandas, SciPy, Bottleneck, and optional data providers are not listed.
Some functions accept a callback (`function` or `update_func`) or are built by
a rolling-function factory; those dynamic edges are called out separately.
The graph follows the checked-in source and may need updating when functions
are added or refactored.

## Table of Contents
- [Function dependency layers](#function-dependency-layers)
  - [Level 0 — foundational functions and values](#level-0--foundational-functions-and-values)
  - [Level 1 — calculations and shared operations](#level-1--calculations-and-shared-operations)
  - [Level 2 — composite statistics](#level-2--composite-statistics)
  - [Level 3 — composed and conditional metrics](#level-3--composed-and-conditional-metrics)
  - [Level 4 — multi-stage aggregates](#level-4--multi-stage-aggregates)
- [Rolling-statistic dependencies](#rolling-statistic-dependencies)
- [Module dependency overview](#module-dependency-overview)
- [Key observations](#key-observations)

## Function dependency layers
Levels indicate the direction of dependency: higher-level functions rely on
lower-level functions. Functions within a level are grouped by purpose rather
than guaranteed to be entirely independent.

### Level 0 — foundational functions and values

These functions do not call another Empyrical function directly.

1. `empyrical.stats`: `annualization_factor`, `simple_returns`,
   `cum_returns`, `cum_returns_final`, `omega_ratio`,
   `stability_of_timeseries`, `tail_ratio`,
   `beta_fragility_heuristic_aligned`, `gpd_es_calculator`,
   `gpd_var_calculator`, `gpd_loglikelihood_scale_and_shape`,
   `gpd_loglikelihood_scale_only`, `value_at_risk`,
   `conditional_value_at_risk`, `_zero_dispersion_std` (new in `bc01011`;
   forces the denominator std to 0 for identical values, so ratios stay
   NaN instead of becoming arbitrary ~1e15 values).
2. `empyrical.utils`: `_roll_ndarray`, `_roll_pandas`, `cache_dir`,
   `ensure_directory`, `get_utc_timestamp`, `_1_bday_ago`, `get_fama_french`,
   `get_symbol_returns_from_yahoo`, `rolling_window`,
   `_flatten`, `_to_pandas`, `_adjust_returns`, `nanmean`, `nanstd`, `nansum`,
   `nanmax`, `nanmin`, `nanargmax`, `nanargmin`, `up`, `down`,
   `_paired_mask` (new in `bc01011`; selects present 1-D return / factor
   pairs, used by `up` and `down`).
3. `empyrical.perf_attrib`: `compute_exposures`.
4. `empyrical.deprecate`: `deprecated` (its returned wrapper calls the
   decorated function dynamically).
5. `empyrical.periods` supplies period labels and annualization constants;
   it defines no functions.

### Level 1 — calculations and shared operations

1. `aggregate_returns` → `cum_returns`.
2. `drawdown_series` → `cum_returns`.
3. `annual_return` → `annualization_factor`, `cum_returns_final`.
4. `annual_volatility` → `annualization_factor`, utility `nanstd`.
5. `downside_risk` → `annualization_factor`, utility `nanmean`.
6. `excess_sharpe` → utility `_adjust_returns`, `nanmean`, `nanstd`,
   `_zero_dispersion_std` (new in `bc01011`).
7. `beta_aligned` → utility `nanmean`.
8. `beta_fragility_heuristic` → utility `_aligned_series`.
9. `get_treasury_yield` → `_1_bday_ago` when `end` is omitted.
10. `gpd_loglikelihood_scale_and_shape_factory` →
    `gpd_loglikelihood_scale_and_shape`.
11. `gpd_loglikelihood_scale_only_factory` →
    `gpd_loglikelihood_scale_only`.
12. `gpd_loglikelihood` → `gpd_loglikelihood_scale_and_shape`,
    `gpd_loglikelihood_scale_only`.
13. Utility `data_path` → `cache_dir`.
14. Utility `get_returns_cached` → `cache_dir`, `ensure_directory`;
    invokes its `update_func` callback when refreshing the cache.
15. Utility `_create_unary_vectorized_roll_function` and
    `_create_binary_vectorized_roll_function` → `_flatten`, `rolling_window`.
16. `perf_attrib` → `compute_exposures`.
17. `up` → `_paired_mask`; `down` → `_paired_mask` (new in `bc01011`; the
    mask restricts to present return / factor pairs before the `<0` / `>0`
    filter).
18. `downside_risk` → `_adjust_returns` (aligned to the returns index before
    array conversion, new in `bc01011`), `annualization_factor`, utility
    `nanmean`.

### Level 2 — composite statistics

1. `max_drawdown` → `drawdown_series`, utility `nanmin`.
2. `cagr` → `annual_return`.
3. `sharpe_ratio` → `annualization_factor`, utility `_adjust_returns`,
   `nanmean`, `nanstd`, `_zero_dispersion_std` (new in `bc01011`).
4. `sortino_ratio` → `annualization_factor`, utility `_adjust_returns`,
   `nanmean`, `downside_risk`.
5. `beta` → utility `_aligned_series` for non-NumPy inputs, `beta_aligned`.
6. `alpha_aligned` → `annualization_factor`, `beta_aligned`, utility
   `_adjust_returns`, `nanmean`.
7. `capture` → `annual_return`.
8. `gpd_loglikelihood_factory` → `gpd_loglikelihood`.
10. `load_portfolio_risk_factors` → `_1_bday_ago`, `data_path`,
    `get_returns_cached`, `get_utc_timestamp`.
11. `default_returns_func` → `_1_bday_ago`, `data_path`,
    `get_returns_cached`, `get_symbol_returns_from_yahoo`,
    `get_utc_timestamp`.
12. `roll` → `_roll_ndarray` or `_roll_pandas`, according to input type;
    each invokes its `function` callback once per window.
13. `load_portfolio_risk_factors` supplies `get_fama_french` as the
    `get_returns_cached` update callback.
14. `default_returns_func` supplies `get_symbol_returns_from_yahoo` as the
    `get_returns_cached` update callback for cached SPY data.

### Level 3 — composed and conditional metrics

1. `calmar_ratio` → `annual_return`, `max_drawdown`.
2. `alpha_beta_aligned` → `alpha_aligned`, `beta_aligned`.
3. `alpha` → `alpha_aligned`; for non-NumPy inputs it also aligns inputs
   through utility `_aligned_series`.
4. `gpd_loglikelihood_minimizer_aligned` → `gpd_loglikelihood_factory`.
5. Conditional capture and alpha/beta functions delegate to `utils.up` or
   `utils.down`, which filter observations and then invoke the supplied
   statistic:
   - `up_capture` → `utils.up` → `capture`
   - `down_capture` → `utils.down` → `capture`
   - `up_alpha_beta` → `utils.up` → `alpha_beta_aligned`
   - `down_alpha_beta` → `utils.down` → `alpha_beta_aligned`
6. `roll_downsize_risk` → `roll_downside_risk` (deprecated alias).

### Level 4 — multi-stage aggregates

1. `alpha_beta` → utility `_aligned_series`, `alpha_beta_aligned`.
2. `gpd_risk_estimates_aligned` → `gpd_loglikelihood_minimizer_aligned`,
   `gpd_var_calculator`, `gpd_es_calculator`.
3. `gpd_risk_estimates` → `gpd_risk_estimates_aligned` (since `bc01011`,
   `var_p` is treated as a scalar tail probability and passed straight
   through; the earlier `_aligned_series(returns, var_p)` call was dropped
   because `var_p` is not a return series).
4. `up_down_capture` → `up_capture`, `down_capture`.

[⬆ 回到目录](#table-of-contents)

## Rolling-statistic dependencies
Most `roll_*` statistics in `stats.py` are generated by the utility factories
at module import time. The generated unary wrappers apply the base statistic
to windows created by `utils.rolling_window` (after `_flatten` for Series);
the generated binary wrappers window both inputs before invoking the base
statistic.

| Rolling function | Base function / implementation |
| --- | --- |
| `roll_max_drawdown` | `max_drawdown` via unary factory |
| `roll_cagr` | `cagr` via unary factory |
| `roll_annual_volatility` | `annual_volatility` via unary factory |
| `roll_sharpe_ratio` | `sharpe_ratio` via unary factory |
| `roll_sortino_ratio` | `sortino_ratio` via unary factory |
| `roll_downside_risk` | `downside_risk` via unary factory |
| `roll_excess_sharpe` | `excess_sharpe` via binary factory |
| `roll_alpha_beta_aligned` | `alpha_beta_aligned` via binary factory |
| `roll_alpha`, `roll_alpha_aligned` | `alpha`, `alpha_aligned` via binary factory |
| `roll_beta`, `roll_beta_aligned` | `beta`, `beta_aligned` via binary factory |

`roll_alpha_beta` is a handwritten rolling wrapper rather than a generated
factory alias; it aligns its inputs and delegates to `roll_alpha_beta_aligned`.

The additional rolling entry points layer on top of those generated functions:

- `roll_alpha_beta` aligns inputs with `_aligned_series`, then calls
  `roll_alpha_beta_aligned`.
- `roll_up_capture`, `roll_down_capture`, and `roll_up_down_capture` call
  `utils.roll` with `up_capture`, `down_capture`, or `up_down_capture` as the
  callback.
- `roll_downsize_risk` is a deprecated compatibility wrapper around
  `roll_downside_risk`.

[⬆ 回到目录](#table-of-contents)

## Module dependency overview
```text
empyrical.periods
    └── constants used by empyrical.stats

empyrical.utils
    ├── alignment, return adjustment, rolling, and NaN-reduction helpers
    ├── cache and date helpers
    └── optional pandas-datareader / yfinance data retrieval

empyrical.stats
    ├── uses periods and utils
    └── composes return, risk, factor, rolling, and tail-risk metrics

empyrical.perf_attrib
    └── computes factor exposures and portfolio return attribution

empyrical.deprecate
    └── generic deprecation decorator; independent of other package functions
```

[⬆ 回到目录](#table-of-contents)

## Key observations
- `utils` contains shared primitives used throughout `stats`; changes to
  `_aligned_series`, `_adjust_returns`, `rolling_window`, or a NaN reduction
  can affect many metrics.
- `stats` is the main composition layer. Drawdown, annualization, factor
  regression, rolling, and generalized Pareto tail-risk calculations have
  distinct helper chains.
- Rolling statistics are mostly generated by factories, so their function
  bodies are not explicit `def roll_*` definitions. Their base-statistic and
  utility dependencies are listed above.
- `perf_attrib` and `deprecate` form separate utility surfaces: attribution
  uses its own exposure aggregation, while the deprecation decorator invokes
  the wrapped function dynamically.
- Since `bc01011`, several metrics are hardened against degenerate input and
  now return NaN instead of a spurious or infinite number: `sharpe_ratio` /
  `excess_sharpe` (constant returns → 0 denominator → NaN),
  `conditional_value_at_risk` / `value_at_risk` (empty or all-NaN → NaN),
  `batting_average` (non-finite obs dropped; empty subset → NaN),
  `beta_fragility_heuristic_aligned` (< 3 pairs → NaN),
  `gpd_es_calculator` (shape ≥ 1 → `np.inf`). `aggregate_returns` WEEKLY
  grouping now keys on ISO year + ISO week, and `drawdown_series` ndarray
  output no longer includes the anchor row.

[⬆ 回到目录](#table-of-contents)
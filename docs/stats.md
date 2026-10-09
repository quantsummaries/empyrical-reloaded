# Performance and Risk Statistics

`empyrical.stats` provides calculations for converting prices to returns,
summarizing return streams, measuring risk, and comparing a strategy with a
benchmark or other factor.

## Input conventions

- Return inputs are **simple, non-cumulative decimal returns**: `0.01`
  represents a 1% return. Price inputs are used only by `simple_returns`.
- A `pandas.Series` represents one time series. A `pandas.DataFrame` generally
  represents multiple series, one per column. Many functions also accept
  NumPy arrays.
- For functions that take strategy and factor/benchmark returns, pass
  observations for the same dates. The regular functions align pandas Series
  by their index labels. Functions with an `_aligned` suffix expect inputs to
  already be aligned; array inputs to those functions must have matching
  shapes.
- Missing return observations are generally skipped by statistical
  calculations or treated as zero by cumulative-return calculations, as
  described below. Individual metrics may have additional minimum-data
  requirements.

## Annualization

`annualization_factor(period, annualization)` resolves the number of
observations per year. The default period factors are:

| Period | Factor |
| --- | ---: |
| `DAILY` | 252 |
| `WEEKLY` | 52 |
| `MONTHLY` | 12 |
| `QUARTERLY` | 4 |
| `YEARLY` | 1 |

These period constants are available from `empyrical` (for example,
`from empyrical import DAILY`). A custom `annualization` value overrides the
period's default. For details, see [Return Periods and Annualization
Factors](periods.md).

## Returns and compounding

| Function | Description |
| --- | --- |
| `simple_returns(prices)` | Computes period-over-period percentage returns from a Series, DataFrame, or array of prices. For pandas inputs, the first observation is omitted because it has no preceding price. |
| `cum_returns(returns, starting_value=0, out=None)` | Computes cumulative compounded returns for one or more series. A starting value of `0` returns cumulative gain/loss (for example, `0.10` means +10%); a nonzero starting value scales the compounded growth by that value. NaN returns are treated as zero. |
| `cum_returns_final(returns, starting_value=0)` | Computes only the ending compounded return, returning a scalar for a one-dimensional input and one result per column for a two-dimensional input. |
| `aggregate_returns(returns, convert_to)` | Compounds observations into `"weekly"`, `"monthly"`, `"quarterly"`, or `"yearly"` returns. |

```python
import pandas as pd
from empyrical import simple_returns, cum_returns, aggregate_returns

prices = pd.Series(
    [100.0, 102.0, 101.0],
    index=pd.date_range("2024-01-01", periods=3),
)
returns = simple_returns(prices)
growth = cum_returns(returns)
monthly = aggregate_returns(returns, convert_to="monthly")
```

## Drawdowns and growth

| Function | Description |
| --- | --- |
| `drawdown_series(returns, out=None)` | Returns each observation's percentage decline from the running cumulative peak. |
| `max_drawdown(returns, out=None)` | Returns the most negative drawdown over the period. |
| `roll_max_drawdown(returns, window=...)` | Computes maximum drawdown over rolling windows. |
| `annual_return(returns, period=DAILY, annualization=None)` | Computes the compound annual growth rate (CAGR) from the cumulative return and observation count. |
| `cagr(returns, period=DAILY, annualization=None)` | Alias for `annual_return`. |
| `roll_cagr(...)` | Rolling-window CAGR. |
| `calmar_ratio(returns, period=DAILY, annualization=None)` | Annual return divided by the absolute maximum drawdown; returns NaN when there is no negative maximum drawdown. |

Drawdowns are non-positive fractions: a drawdown of `-0.20` represents a 20%
decline from the preceding peak. Annualized calculations use the period factor
or custom `annualization` value described above.

## Volatility and risk-adjusted returns

| Function | Description |
| --- | --- |
| `annual_volatility(returns, period=DAILY, alpha=2.0, annualization=None, out=None)` | Sample standard deviation scaled by the annualization factor raised to `1 / alpha`. The usual standard-deviation scaling uses the default `alpha=2`. |
| `roll_annual_volatility(...)` | Rolling annualized volatility. |
| `sharpe_ratio(returns, risk_free=0, period=DAILY, annualization=None, out=None)` | Annualized mean excess return divided by sample standard deviation of excess returns. `risk_free` is a constant per-period return. |
| `roll_sharpe_ratio(...)` | Rolling Sharpe ratio. |
| `sortino_ratio(returns, required_return=0, period=DAILY, annualization=None, out=None)` | Annualized average return above the minimum acceptable return divided by downside risk. |
| `roll_sortino_ratio(...)` | Rolling Sortino ratio. |
| `downside_risk(returns, required_return=0, period=DAILY, annualization=None, out=None)` | Annualized downside deviation below the required-return threshold. |
| `roll_downside_risk(...)` | Rolling downside risk. The legacy misspelling `roll_downsize_risk` emits a deprecation warning; use `roll_downside_risk`. |
| `omega_ratio(returns, risk_free=0.0, required_return=0.0, annualization=252)` | Sum of gains above the per-period threshold divided by the absolute sum of losses below it. The required return is annualized unless `annualization=1`. |
| `excess_sharpe(returns, factor_returns, out=None)` | Mean active return divided by tracking error, a simplified information ratio. |
| `roll_excess_sharpe(...)` | Rolling excess Sharpe ratio. |

## Benchmark and factor statistics

`factor_returns` is a non-cumulative return series for a benchmark or factor.
For pandas Series, the regular functions align the two series by index;
`_aligned` variants avoid that alignment step and require already-matched
inputs.

| Function | Description |
| --- | --- |
| `alpha(returns, factor_returns, risk_free=0.0, period=DAILY, annualization=None)` | Annualized alpha relative to a factor, using the factor beta and risk-free adjustment. |
| `beta(returns, factor_returns, risk_free=0.0)` | Sensitivity of strategy returns to factor returns. |
| `alpha_beta(...)` | Returns annualized alpha and beta together. |
| `roll_alpha(...)`, `roll_beta(...)`, `roll_alpha_beta(...)` | Rolling alpha, beta, or paired alpha and beta. These functions accept a window length and forward supported metric options. |
| `alpha_aligned(...)`, `beta_aligned(...)`, `alpha_beta_aligned(...)` | Variants for inputs already aligned by index (or matching array shape). |
| `roll_alpha_aligned(...)`, `roll_beta_aligned(...)`, `roll_alpha_beta_aligned(...)` | Rolling aligned variants. |
| `capture(returns, factor_returns, period=DAILY)` | Strategy annual return divided by factor annual return. |
| `up_capture(returns, factor_returns, **kwargs)` | Capture ratio using observations where factor returns are nonnegative. |
| `down_capture(returns, factor_returns, **kwargs)` | Capture ratio using observations where factor returns are negative. |
| `up_down_capture(returns, factor_returns, **kwargs)` | Up-capture divided by down-capture. |
| `roll_up_capture(...)`, `roll_down_capture(...)`, `roll_up_down_capture(...)` | Rolling up-, down-, and up/down-capture calculations. |
| `up_alpha_beta(...)`, `down_alpha_beta(...)` | Alpha and beta on nonnegative- or negative-factor observations, respectively. |
| `batting_average(returns, factor_returns)` | A Series containing the fraction of all observations, nonnegative-factor observations, and negative-factor observations on which strategy returns exceed factor returns. |
| `beta_fragility_heuristic(returns, factor_returns)` | Heuristic estimate of return fragility associated with changes across low, middle, and high factor-return observations. |
| `beta_fragility_heuristic_aligned(...)` | Aligned-input variant of the beta fragility heuristic. |

The rolling functions use a rolling observation window. The paired alpha/beta
functions return both statistics; for array inputs, the last dimension
contains alpha followed by beta.

## Distribution and tail-risk statistics

| Function | Description |
| --- | --- |
| `value_at_risk(returns, cutoff=0.05)` | Historical return quantile at the specified lower-tail cutoff. The result is typically negative for a loss threshold. |
| `conditional_value_at_risk(returns, cutoff=0.05)` | Mean of the lowest returns selected at the requested lower-tail cutoff. |
| `tail_ratio(returns)` | Absolute 95th-percentile return divided by the absolute 5th-percentile return. Values below one indicate a larger-magnitude left tail than right tail. |
| `gpd_risk_estimates(returns, var_p=0.01)` | Fits a Generalized Pareto Distribution to losses and returns five values: threshold, scale, shape, VaR estimate, and expected shortfall (ES) estimate. |
| `gpd_risk_estimates_aligned(returns, var_p=0.01)` | Aligned-input variant of the GPD risk estimate. |
| `stability_of_timeseries(returns)` | R-squared from a linear fit to cumulative log returns over time. |

The GPD calculation is an extreme-value model estimate, not the historical
quantile used by `value_at_risk`. Interpret it with the assumptions and
limitations of tail fitting in mind.

The lower-level `gpd_var_calculator`, `gpd_es_calculator`, and GPD
log-likelihood helpers support the fitting process; most callers should use
`gpd_risk_estimates` instead.

## Metric collections

`SIMPLE_STAT_FUNCS` and `FACTOR_STAT_FUNCS` are lists of commonly used
statistics. The former includes return-only measures such as cumulative
return, annualized return and volatility, Sharpe ratio, maximum drawdown, and
tail ratio. The latter includes factor-relative measures such as excess
Sharpe, alpha, beta, capture, beta fragility, and GPD risk estimates. These
lists are provided for programmatic use; their membership is defined in the
module.

## Shape and return consistency

Many statistics accept one- or two-dimensional inputs. For two-dimensional
inputs, calculations are generally performed independently by column. Scalar
inputs return a scalar result; DataFrame inputs commonly return a Series
indexed by columns. Functions that accept `out` use it as a NumPy output
buffer.

Several metrics return NaN when the input is empty, too short, has no usable
variation, or makes a ratio undefined. In particular, many volatility,
Sharpe, Sortino, and regression calculations require at least two observations.
Review individual function docstrings for exact edge-case behavior and
parameter details.

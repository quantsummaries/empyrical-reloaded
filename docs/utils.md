# Utilities

`empyrical.utils` contains helpers for rolling calculations, aligning and
adjusting return data, caching downloaded data, and retrieving market data.
Several helpers are used internally by the statistics functions; underscore-
prefixed helpers are implementation utilities rather than general-purpose
public APIs.

## Rolling and conditional calculations

### `roll`

```python
roll(*returns, window, function, **kwargs)
```

Applies `function` to successive windows of one or two return series. The
`window` argument is the number of observations per window, and remaining
keyword arguments are forwarded to `function`.

```python
import pandas as pd
from empyrical.stats import alpha_aligned
from empyrical.utils import roll

rolling_alpha = roll(
    strategy_returns,
    benchmark_returns,
    window=60,
    function=alpha_aligned,
)
```

For pandas inputs, the result is a Series indexed by the last date of each
window. For NumPy arrays, it is a NumPy array. Two inputs must be the same
Python type; at most two return series may be passed. Rolling functions
created by Empyrical generally provide a more direct interface for specific
statistics; see [Performance and Risk Statistics](stats.md).

### `up` and `down`

```python
up(returns, factor_returns, function, **kwargs)
down(returns, factor_returns, function, **kwargs)
```

Filter strategy and factor returns to observations where factor returns are
strictly positive (`up`) or strictly negative (`down`), then call `function`
with the filtered series and forwarded keyword arguments. Observations where
the factor return is exactly zero are excluded from both groups. Inputs should
be aligned and have matching shapes.

These helpers underpin conditional measures such as up- and down-capture.

## Rolling-window array helpers

### `rolling_window`

```python
rolling_window(array, length, mutable=False)
```

Creates overlapping windows along the first axis of a NumPy array. For an
input with shape `(n, ...)`, the output has shape
`(n - length + 1, length, ...)`. The returned view shares memory with the
input. By default it is read-only; `mutable=True` enables writes, which also
modify the original array and may affect multiple overlapping windows.

The window length must be nonzero and cannot exceed the first-axis length. A
scalar input is not supported.

### Rolling-function factories

`_create_unary_vectorized_roll_function(function)` and
`_create_binary_vectorized_roll_function(function)` create rolling variants
of one-input and two-input statistics. Generated functions accept a `window`,
optional output buffer, and statistic-specific keyword arguments. These
underscore-prefixed helpers are primarily for implementing Empyrical's
rolling statistics.

## Cache paths and cached data

| Helper | Purpose |
| --- | --- |
| `cache_dir(environ=os.environ)` | Returns the cache directory from `EMPYRICAL_CACHE_DIR`, or defaults to `$XDG_CACHE_HOME/empyrical` (with `~/.cache/` as the XDG default). |
| `data_path(name)` | Joins `name` to the cache directory. |
| `ensure_directory(path)` | Creates a directory and does nothing if it already exists as a directory; propagates other filesystem errors. |
| `get_returns_cached(filepath, update_func, latest_dt, **kwargs)` | Reads cached CSV data when the file modification time is recent enough; otherwise calls `update_func(**kwargs)`, attempts to save its DataFrame result, and returns the result. |

When a cache directory cannot be created or a result cannot be written, the
cache helper emits a `UserWarning`; it still returns the data fetched by the
update function. The cache's freshness decision is based on file modification
time compared with `latest_dt`.

## Market and reference data

These functions retrieve data from external services and may require optional
dependencies and network access.

| Function | Description |
| --- | --- |
| `get_fama_french(start="1-1-1970", end=None, datasets=(...))` | Fetches one or more Fama-French datasets using `pandas-datareader`, concatenates their columns, removes rows with missing values, converts percentage values to decimal returns, trims column names, and localizes the date index to UTC. |
| `load_portfolio_risk_factors(filepath_prefix=None, start=None, end=None)` | Loads cached Fama-French market, size, value, risk-free, and momentum factor data, refreshing the cache as needed, then returns the requested date range. The default cache file is `factors.csv`. |
| `get_treasury_yield(start=None, end=None, period="3MO")` | Fetches a Treasury yield series from FRED for the selected maturity and forward-fills missing observations. |
| `get_symbol_returns_from_yahoo(symbol, start=None, end=None)` | Downloads Yahoo Finance adjusted-close prices for a symbol and calculates simple returns. |
| `default_returns_func(symbol, start=None, end=None)` | Retrieves daily returns for a symbol. SPY results use the local `spy.csv` cache; other symbols are fetched directly. |

`pandas-datareader` is needed for Fama-French and FRED requests; `yfinance` is
needed for Yahoo Finance data. These dependencies are optional. Fama-French
retrieval raises `ImportError` if `pandas-datareader` is unavailable.

## Date and data alignment helpers

| Helper | Purpose |
| --- | --- |
| `get_utc_timestamp(dt)` | Converts a date or datetime-like value to a pandas timestamp/index localized to UTC if naive, or converted to UTC if already timezone-aware. |
| `_1_bday_ago()` | Returns the prior business day based on the current local date. Used as the default end date for data retrieval. |
| `_aligned_series(*many_series)` | Aligns multiple Series-like inputs by their pandas index, filling missing positions with NaN. Equal-length NumPy arrays are returned unchanged when possible. |
| `_to_pandas(ob)` | Converts one- or two-dimensional array-like data to a Series or DataFrame; dimensions greater than two raise `ValueError`. |
| `_flatten(arr)` | Returns a Series' underlying values; other inputs are returned unchanged. |
| `_adjust_returns(returns, adjustment_factor)` | Subtracts a scalar or series adjustment from returns. A zero scalar is optimized by returning the original input. |

## NaN-aware reductions

`nanmean`, `nanstd`, `nansum`, `nanmax`, `nanmin`, `nanargmax`, and
`nanargmin` are NaN-aware reduction functions. Empyrical uses Bottleneck's
implementations when Bottleneck is installed and otherwise falls back to the
corresponding NumPy `nan*` functions. When Bottleneck is used, the wrappers
also support writing the reduction result into an optional `out` buffer.

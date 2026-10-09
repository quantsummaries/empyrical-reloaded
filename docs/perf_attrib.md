# Performance Attribution

`empyrical.perf_attrib` attributes a portfolio's returns to a set of risk
factors. It calculates the portfolio's daily exposure to each factor, the
return contribution from each factor, and the returns not explained by the
factors.

## Inputs and alignment

| Argument | Type | Expected index and contents |
| --- | --- | --- |
| `returns` | `pandas.Series` | Datetime index; portfolio return for each date. |
| `positions` | `pandas.Series` | MultiIndex with date (`dt`) and asset (`ticker`) levels; holdings or weights for each asset and date. |
| `factor_returns` | `pandas.DataFrame` | Datetime index and one column per factor; return of each factor on each date. |
| `factor_loadings` | `pandas.DataFrame` | MultiIndex with date (`dt`) and asset (`ticker`) levels, and one column per factor; each asset's loading on each factor and date. |

Use decimal returns and weights (for example, `0.02` for 2%). The factor
columns in `factor_returns` and `factor_loadings` should correspond. Positions
and loadings should use matching date/asset index values. The implementation
aligns data using pandas index and column labels; input dates are restricted to
the first and last dates in `returns`.

## Calculation

For date \(t\), asset \(i\), and factor \(k\), portfolio exposure is the
weighted sum of asset factor loadings:

\[
E_{t,k} = \sum_i w_{t,i} L_{t,i,k}
\]

where \(w_{t,i}\) is the position and \(L_{t,i,k}\) is the factor loading.
Daily factor contribution is exposure multiplied by that date's factor return
\(F_{t,k}\):

\[
A_{t,k} = E_{t,k} F_{t,k}
\]

The function then calculates:

- **Common returns**: the sum of factor contributions for each date.
- **Specific returns**: total portfolio returns minus common returns.
- **Tilt returns**: factor returns multiplied by the portfolio's average
  exposure to each factor over the period, summed across factors.
- **Timing returns**: common returns minus tilt returns.

Thus, common and specific returns sum to total returns. Tilt and timing returns
decompose common returns.

## `perf_attrib`

```python
empyrical.perf_attrib.perf_attrib(
    returns, positions, factor_returns, factor_loadings
)
```

Returns a two-item tuple `(risk_exposures_portfolio, attribution)`.

`risk_exposures_portfolio` is a DataFrame indexed by date with one column per
factor. `attribution` is a DataFrame indexed by date with one column per
factor contribution, plus `total_returns`, `common_returns`,
`specific_returns`, `tilt_returns`, and `timing_returns`.

### Example

```python
import pandas as pd
from empyrical.perf_attrib import perf_attrib

dates = pd.date_range("2024-01-02", periods=2, name="dt")
assets = ["AAA", "BBB"]
asset_dates = pd.MultiIndex.from_product(
    [dates, assets], names=["dt", "ticker"]
)

returns = pd.Series([0.03, 0.01], index=dates, name="returns")
positions = pd.Series([0.6, 0.4, 0.6, 0.4], index=asset_dates)
factor_returns = pd.DataFrame(
    {"market": [0.02, -0.01]}, index=dates
)
factor_loadings = pd.DataFrame(
    {"market": [1.2, 0.5, 0.8, 0.2]}, index=asset_dates
)

exposures, attribution = perf_attrib(
    returns, positions, factor_returns, factor_loadings
)
```

For this example, the portfolio's market exposures are `0.92` and `0.56`;
the market contributions are `0.0184` and `-0.0056`. The attribution DataFrame
also contains the total, common, specific, tilt, and timing returns.

## `compute_exposures`

```python
empyrical.perf_attrib.compute_exposures(positions, factor_loadings)
```

Computes daily portfolio factor exposures without calculating returns. It
multiplies each asset's factor loadings by its position, then sums the
weighted loadings by date. It returns a DataFrame indexed by date with factor
columns.

```python
from empyrical.perf_attrib import compute_exposures

exposures = compute_exposures(positions, factor_loadings)
```

## Notes

- Positions are used as supplied; they are not normalized. They may represent
  long and short holdings.
- If the returns index has a pandas frequency, the calculated exposures are
  reindexed to that frequency.
- The attribution is a factor model decomposition of the supplied data; the
  specific return is the residual after subtracting modeled factor
  contributions.

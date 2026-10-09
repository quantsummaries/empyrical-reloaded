# Return Periods and Annualization Factors

`empyrical.periods` defines the standard period labels and annualization
constants used by Empyrical's return and risk statistics. The values map a
return observation frequency to the approximate number of observations in one
year.

## Period labels

| Constant | Value | Meaning |
| --- | --- | --- |
| `DAILY` | `"daily"` | Daily observations. |
| `WEEKLY` | `"weekly"` | Weekly observations. |
| `MONTHLY` | `"monthly"` | Monthly observations. |
| `QUARTERLY` | `"quarterly"` | Quarterly observations. |
| `YEARLY` | `"yearly"` | Annual observations. |

These constants are also re-exported from the top-level `empyrical` package:

```python
from empyrical import DAILY, MONTHLY, WEEKLY
```

## Annualization constants

| Constant | Value | Description |
| --- | ---: | --- |
| `APPROX_BDAYS_PER_MONTH` | `21` | Approximate number of business days in a month. |
| `APPROX_BDAYS_PER_YEAR` | `252` | Approximate number of business days in a year; used for daily data. |
| `MONTHS_PER_YEAR` | `12` | Months in a year. |
| `WEEKS_PER_YEAR` | `52` | Weeks in a year. |
| `QTRS_PER_YEAR` | `4` | Quarters in a year. |

`ANNUALIZATION_FACTORS` maps each period label to the corresponding factor:

| Period label | Annualization factor |
| --- | ---: |
| `DAILY` | `252` |
| `WEEKLY` | `52` |
| `MONTHLY` | `12` |
| `QUARTERLY` | `4` |
| `YEARLY` | `1` |

## Using period labels

Statistics that annualize periodic returns accept a period label to select a
default factor. For example:

```python
from empyrical import annual_return, DAILY

annual_return(daily_returns, period=DAILY)
```

The annualization factor can also be supplied directly where the statistic
supports an `annualization` argument. A custom factor takes precedence over
the period label. For example, a series with 260 observations per year can use
`annualization=260`.

The period values are conventions for annualizing returns and volatility;
they do not infer or validate the actual frequency of a data series. Choose
the period or custom factor to match the observations in the input data.

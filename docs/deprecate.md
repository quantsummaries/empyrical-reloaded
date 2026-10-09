# Deprecation Utilities

`empyrical.deprecate` provides a decorator for marking functions as deprecated.
When a decorated function is called, it emits a Python `DeprecationWarning`
and then calls the original function with the supplied arguments.

## `deprecated`

```python
empyrical.deprecate.deprecated(msg=None, stacklevel=2)
```

Use `deprecated` to decorate a function that remains available for
compatibility but should no longer be used.

| Parameter | Description |
| --- | --- |
| `msg` | Optional warning text. If omitted, the warning says `Function <name> is deprecated.` |
| `stacklevel` | Warning stack level passed to `warnings.warn`. Defaults to `2`, which normally points to the deprecated function's caller. |

The decorator preserves the wrapped function's metadata and signature through
`functools.wraps`. It does not change the return value or suppress exceptions
from the original function.

### Example

```python
from empyrical.deprecate import deprecated

@deprecated(msg="old_metric is deprecated; use new_metric instead.")
def old_metric(values):
    return new_metric(values)
```

Calling `old_metric(values)` emits a `DeprecationWarning` with the supplied
message, then returns the result of `new_metric(values)`. If no message is
provided:

```python
@deprecated()
def old_metric(values):
    return new_metric(values)
```

the warning message is `Function old_metric is deprecated.`.

`DeprecationWarning` is commonly filtered out by default in ordinary Python
applications. Tests or applications can control its visibility using the
standard `warnings` module, for example with `warnings.simplefilter("always")`.

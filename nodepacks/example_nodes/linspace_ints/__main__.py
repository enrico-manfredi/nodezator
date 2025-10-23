def linspace(
    start: float = 0.0,
    end:   float = 1.0,
    count: int   = 10
) -> list:
    """
    Generate a list of `count` evenly spaced values from `start` to `end`, inclusive.
    If count == 1: returns [start].
    If count <= 0: returns [] or raises ValueError.
    """
    # Validate count
    if not isinstance(count, int):
        try:
            count = int(count)
        except Exception:
            raise ValueError(f"linspace: count must be an integer, got {count!r}")
    if count < 1:
        raise ValueError(f"linspace: count must be >=1, got {count!r}")
    if count == 1:
        return [float(start)]
    # compute step
    start_f = float(start)
    end_f   = float(end)
    step = (end_f - start_f) / (count - 1)
    result = [start_f + i * step for i in range(count)]
    # enforce last value exactly end_f (to avoid fp error)
    result[-1] = end_f
    return result

main_callable = linspace

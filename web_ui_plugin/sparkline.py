"""
Drawing a trend line without a charting library.

The page is served from a machine that may have no internet access, and a
chart of at most a few dozen points does not justify pulling a library over a
CDN. The polyline is computed here and rendered as inline SVG.
"""


def sparkline(points, width=160, height=36, padding=3):
    """
    Turn a series of values into SVG polyline coordinates.

    Args:
        points (list): (label, value) pairs, oldest first.
        width (int): Drawing width in pixels.
        height (int): Drawing height in pixels.
        padding (int): Margin kept above and below the line.

    Returns:
        dict | None: {"points", "first", "last", "min", "max", "direction"},
            or None when there is nothing to draw.
    """
    values = [float(value) for _, value in points if value is not None]
    if len(values) < 2:
        return None

    lowest, highest = min(values), max(values)
    span = highest - lowest
    usable = height - 2 * padding
    step = width / (len(values) - 1)

    coordinates = []
    for index, value in enumerate(values):
        # A flat series would divide by zero; draw it down the middle instead.
        ratio = 0.5 if span == 0 else (value - lowest) / span
        y = height - padding - ratio * usable
        coordinates.append(f"{index * step:.1f},{y:.1f}")

    return {
        "points": " ".join(coordinates),
        "first": values[0],
        "last": values[-1],
        "min": lowest,
        "max": highest,
        "direction": (
            "up"
            if values[-1] > values[0]
            else "down" if values[-1] < values[0] else "flat"
        ),
    }

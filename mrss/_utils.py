def human_duration(secs: float, /):
    negative = secs < 0
    secs = abs(secs)

    # As of Python 3.7 dict items guarantee to be in insertion order.
    t = {}
    t["w"], secs = divmod(secs, 60 * 60 * 24 * 7)
    t["d"], secs = divmod(secs, 60 * 60 * 24)
    t["h"], secs = divmod(secs, 60 * 60)
    t["m"], secs = divmod(secs, 60)
    t["s"], secs = divmod(secs, 1)

    parts = [f"{int(value)}{unit}" for unit, value in t.items() if value > 0]
    if parts:
        return ("-" if negative else "") + " ".join(parts)
    elif secs:
        return "<1s"
    else:
        return "0s"

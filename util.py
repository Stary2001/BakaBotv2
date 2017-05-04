def pretty_time(t):
    if t == None:
        return None

    hours, min_sec = divmod(t, 3600)
    minutes, seconds = divmod(min_sec, 60)

    if hours != 0:
        duration = "{:02d}h{:02d}m{:02d}s".format(hours, minutes, seconds)
    elif minutes != 0:
        duration = "{:02d}m{:02d}s".format(minutes, seconds)
    else:
        duration = "{:02d}s".format(seconds)

    return duration
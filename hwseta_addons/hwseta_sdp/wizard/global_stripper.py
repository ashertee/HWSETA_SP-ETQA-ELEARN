def global_stripper(val):
    if isinstance(val, str):
        return val.strip()
    else:
        return val

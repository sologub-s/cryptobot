def find_first_key_by_value(d: dict, value, default = None):
    return next((k for k, v in d.items() if v == value), default)
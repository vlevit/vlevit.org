

def unquote_string(quoted):
    """
    Remove one pair of single or double quotes from quoted string.

    """
    if (quoted.startswith('"') and quoted.endswith('"') or
            quoted.startswith("'") and quoted.endswith("'")):
        return quoted[1:-1]
    return quoted

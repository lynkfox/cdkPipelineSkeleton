class BashColor:
    HEADER = "\033[95m"
    OK_BLUE = "\033[94m"
    OK_CYAN = "\033[96m"
    OK_GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    CLEAR_COLOR = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def as_warning(s: str) -> str:
    """
    Returns the string except yellow.

    Params:
        s (string) : string to make yellow

    Returns:
        (str) : the string except yellow.
    """
    return f"{BashColor.WARNING}{s}{BashColor.CLEAR_COLOR}"


def as_ok(s: str) -> str:
    """
    Returns the string except green.

    Params:
        s (string) : string to make green

    Returns:
        (str) : the string except green.
    """
    return f"{BashColor.OK_GREEN}{s}{BashColor.CLEAR_COLOR}"


def as_fail(s: str) -> str:
    """
    Returns the string except red.

    Params:
        s (string) : string to make red

    Returns:
        (str) : the string except red.
    """
    return f"{BashColor.FAIL}{s}{BashColor.CLEAR_COLOR}"


def as_color(s: str, color: BashColor) -> str:
    """
    Returns the string except the color from the BashColor constant class

    Params:
        s (string) : string to color

    Returns:
        (str) : the string colored.
    """
    return f"{color}{s}{BashColor.CLEAR_COLOR}"

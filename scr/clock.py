_cycle = 0

def tick(steps: int = 1) -> int:
    """Advance global cycle counter and return new value."""
    global _cycle
    _cycle += int(steps)
    return _cycle

def get_cycle() -> int:
    """Return current global cycle."""
    return _cycle

def set_cycle(value: int) -> None:
    global _cycle
    _cycle = int(value)

def reset() -> None:
    set_cycle(0)
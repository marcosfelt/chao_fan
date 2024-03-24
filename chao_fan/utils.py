import signal
from types import FrameType, TracebackType
from typing import Any, Optional, Type, Union


class Timeout:
    """Execute a code block raising a timeout.

    Notes
    -----
    Taken from https://www.debuggingbook.org/html/Timeout.html#

    Examples
    --------
    >>> long_running_function = lambda: time.sleep(10)
    >>> with SignalTimeout(5):
    >>> try:
    >>>     with SignalTimeout(0.2):
    >>>        some_long_running_function()
    >>>        print("Complete!")
    >>> except TimeoutError:
    >>>    print("Timeout!")

    """

    def __init__(self, timeout: Union[int, float]) -> None:
        """
        Constructor. Interrupt execution after `timeout` seconds.
        """
        self.timeout = timeout
        self.old_handler: Any = signal.SIG_DFL
        self.old_timeout = 0.0

    def __enter__(self) -> Any:
        """Begin of `with` block"""
        # Register timeout() as handler for signal 'SIGALRM'"
        self.old_handler = signal.signal(signal.SIGALRM, self.timeout_handler)
        self.old_timeout, _ = signal.setitimer(signal.ITIMER_REAL, self.timeout)
        return self

    def __exit__(
        self, exc_type: Type, exc_value: BaseException, tb: TracebackType
    ) -> None:
        """End of `with` block"""
        self.cancel()
        return  # re-raise exception, if any

    def cancel(self) -> None:
        """Cancel timeout"""
        signal.signal(signal.SIGALRM, self.old_handler)
        signal.setitimer(signal.ITIMER_REAL, self.old_timeout)

    def timeout_handler(self, signum: int, frame: Optional[FrameType]) -> None:
        """Handle timeout (SIGALRM) signal"""
        raise TimeoutError()

from typing import Callable
from typing import List

from typeguard import typechecked


@typechecked
class Timer:
    """
    A countup timer.

    Parameters:
    - counter: current count.
    - duration: how long I count.
    - is_done: true when counter is past duration.

    Update:
    - counter
    - is_done
    - Fire END event.
    """

    # Events.
    END: int = 0

    def __init__(self, duration: float):
        # Track counter.
        self.counter: int = 0

        # How long I count.
        self.duration: float = duration

        # Event subscribers list.
        self.listener_end: List[Callable] = []

        # True when I have counted past duration.
        self.is_done: bool = False

    def add_event_listener(self, value: Callable, event: int) -> None:
        """
        Use this to subscribe to my events:
        - END.
        """

        if event == self.END:
            self.listener_end.append(value)

    def reset(self) -> None:
        """
        Resets:
        - counter = 0.
        - is_done = false.
        """

        self.counter = 0

        self.is_done = False

    def update(self, dt: int) -> None:
        """
        Update:
        - counter
        - is_done
        - Fire END event.
        """

        # No need to count when is done true.
        if self.is_done:
            return

        # Count up.
        self.counter += dt

        # Counted past duration?
        if self.counter > self.duration:
            # Set is done true.
            self.is_done = True

            # Fire END event.
            for callback in self.listener_end:
                callback()

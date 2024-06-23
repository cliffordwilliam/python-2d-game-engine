from typing import Callable
from typing import List

from typeguard import typechecked


@typechecked
class Timer:
    """
    A countup timer.
    Counts up and fire END event on passing duration.

    Set duration in float.
    Call the update method to start counting up.
    Remember to call reset() before counting up again.

    TODO: Timers are affected by Game.time_scale.
    TODO: A higher scale means quicker timeouts, and vice versa.
    """

    # Events.

    # Fired when count reaches duration.
    END: int = 0

    def __init__(self, duration: float):
        # Holds my counting.
        self.count: int = 0

        # Determine how long I count.
        self.duration: float = duration

        # END event subscribers list.
        self.listener_end: List[Callable] = []

        # True when I have counted past duration.
        self.is_done: bool = False

    def add_event_listener(self, value: Callable, event: int) -> None:
        """
        Use this to subscribe to my events.
        """

        if event == self.END:
            self.listener_end.append(value)

    def reset(self) -> None:
        """
        Resets my count.
        Is done False.
        """

        self.count = 0

        self.is_done = False

    def update(self, dt: int) -> None:
        """
        Update my counting until duration.
        """

        # No need to count when is done true.
        if self.is_done:
            return

        # Count.
        self.count += dt

        # Counted past duration?
        if self.count > self.duration:
            # Is done true.
            self.is_done = True

            # Fire END event.
            for callback in self.listener_end:
                callback()

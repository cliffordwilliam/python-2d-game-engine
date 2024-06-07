# from constants import
from typing import Callable
from typing import List

from typeguard import typechecked


@typechecked
class Timer:
    """
    Set duration in float.
    Call the draw and update method to start counting.
    Call the reset before counting again.
    """

    END: int = 0

    def __init__(self, duration: float):
        self.timer: int = 0

        self.duration: float = duration

        self.listener_end: List[Callable] = []

        self.is_done: bool = False

    def add_event_listener(self, value: Callable, event: int) -> None:
        if event == self.END:
            self.listener_end.append(value)

    def reset(self) -> None:
        self.timer = 0

        self.is_done = False

    def update(self, dt: int) -> None:
        """
        Update my counting until duration.
        """
        if self.is_done:
            return

        self.timer += dt

        if self.timer > self.duration:
            self.is_done = True

            for callback in self.listener_end:
                callback()

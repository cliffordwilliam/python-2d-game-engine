from typing import Callable

from typeguard import typechecked


@typechecked
class Timer:
    # Events
    END: int = 0

    def __init__(self, duration: float):
        self.counter: int = 0
        self.duration: float = duration
        self.listener_end: list[Callable] = []
        self.is_done: bool = False

    def add_event_listener(self, value: Callable, event: int) -> None:
        if event == self.END:
            self.listener_end.append(value)

    def reset(self) -> None:
        self.counter = 0
        self.is_done = False

    def update(self, dt: int) -> None:
        if self.is_done:
            return

        self.counter += dt

        # Counted past duration?
        if self.counter > self.duration:
            # Set is done true.
            self.is_done = True
            # Fire END event.
            for callback in self.listener_end:
                callback()

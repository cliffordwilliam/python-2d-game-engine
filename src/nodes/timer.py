from typing import Callable

from typeguard import typechecked


@typechecked
class Timer:
    # Event names
    END: int = 0

    def __init__(self, duration: float):
        # Keep track how much I have counted this frame
        self.counter: int = 0

        # How long I have to count
        self.duration: float = duration

        # Set to true when done counting
        self.is_done: bool = False

        # Key is event name, value is a list of listeners
        self.event_listeners: dict[int, list[Callable]] = {
            self.END: [],
        }

    def add_event_listener(self, callback: Callable, event: int) -> None:
        """
        Subscribe to my events.
        """

        # The event user is supported?
        if event in self.event_listeners:
            # Collect it
            self.event_listeners[event].append(callback)
        else:
            # Throw error
            raise ValueError(f"Unsupported event type: {event}")

    def reset(self) -> None:
        """
        Reset my props.
        """

        self.counter = 0
        self.is_done = False

    def update(self, dt: int) -> None:
        """
        Count.
        """

        # Prev frame counted past duration?
        if self.is_done:
            # Return
            return

        # Count
        self.counter += dt

        # Counted past duration?
        if self.counter > self.duration:
            # Set is done true
            self.is_done = True
            # Fire END event
            for callback in self.event_listeners[self.END]:
                callback()

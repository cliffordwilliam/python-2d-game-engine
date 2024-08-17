from typing import Callable

from constants import pg
from pygame.math import clamp
from pygame.math import lerp
from typeguard import typechecked


@typechecked
class Curtain:
    # Event names
    INVISIBLE_END: int = 0
    OPAQUE_END: int = 1

    # Start settings enum
    INVISIBLE: int = 2
    OPAQUE: int = 3

    def __init__(
        self,
        duration: float,
        start_state: int,
        max_alpha: int,
        surf_size_tuple: tuple[int, int],
        is_invisible: bool,
        color: str,
    ):
        # Set surf
        self.surf: pg.Surface = pg.Surface(surf_size_tuple)

        # Is invisible True?
        if is_invisible:
            # Turn surf invisible
            self.surf.set_colorkey(color)

        # Fill surf with given color
        self.surf.fill(color)

        # Get surf rect
        self.rect: pg.Rect = self.surf.get_rect()

        # Fade in / out duration
        self.fade_duration: float = duration

        # Set max alpha
        self.max_alpha: int = max_alpha

        # Set initial alpha and fade counter
        self.alpha: int = 0
        self.fade_counter: float = 0

        # Start INVISIBLE / OPAQUE
        # Update alpha and fade counter
        self.start_state: int = start_state
        # Start INVISIBLE?
        if self.start_state == self.INVISIBLE:
            self.alpha = 0
            self.fade_counter = 0
        # Start OPAQUE?
        elif self.start_state == self.OPAQUE:
            self.alpha = self.max_alpha
            self.fade_counter = self.fade_duration

        # Set surf alpha
        self.surf.set_alpha(self.alpha)

        # Store truncated float
        self.remainder: float = 0

        # Fade direction
        self.direction: int = 0

        # Key is event name, value is a list of listeners
        self.event_listeners: dict[int, list[Callable]] = {
            self.INVISIBLE_END: [],
            self.OPAQUE_END: [],
        }

        # True when reached INVISIBLE_END / OPAQUE_END
        self.is_done: bool = True

    def go_to_opaque(self) -> None:
        """
        Set dir to opaque.
        Set is done false.
        """

        # Go right opaque
        self.direction = 1

        # Set is done false
        self.is_done = False

    def go_to_invisible(self) -> None:
        """
        Set dir to invisible.
        Set is done false.
        """

        # Go left invisible
        self.direction = -1

        # Set is done true
        self.is_done = False

    def add_event_listener(self, value: Callable, event: int) -> None:
        """
        Subscribe to my events.
        """

        # The event user is supported?
        if event in self.event_listeners:
            # Collect it
            self.event_listeners[event].append(value)
        else:
            # Throw error
            raise ValueError(f"Unsupported event type: {event}")

    def jump_to_opaque(self) -> None:
        """
        Forces the alpha to jump to opaque.
        """

        self.is_done = True
        self.fade_counter = self.fade_duration
        self.remainder = 0
        self.alpha = self.max_alpha
        self.surf.set_alpha(self.alpha)
        self.direction = 1
        for callback in self.event_listeners[self.OPAQUE_END]:
            callback()

    def jump_to_invisible(self) -> None:
        """
        Forces the alpha to jump to opaque.
        """

        self.is_done = True
        self.fade_counter = 0
        self.remainder = 0
        self.alpha = 0
        self.surf.set_alpha(self.alpha)
        self.direction = -1
        for callback in self.event_listeners[self.INVISIBLE_END]:
            callback()

    def set_max_alpha(self, value: int) -> None:
        """
        Sets the max_alpha of the surf.
        """

        self.max_alpha = value

    def draw(self, surf: pg.Surface, y_offset: int) -> None:
        """
        Draw:
        - surf.
        """

        # No need to draw if my alpha is 0, I am invisible
        if self.alpha == 0:
            return

        surf.blit(self.surf, (self.rect.x, self.rect.y + y_offset))

    def update(self, dt: int) -> None:
        """
        Update:
        - fade_counter.
        - alpha.
        - remainder.
        - surf alpha.
        - Fire INVISIBLE_END event.
        - Fire OPAQUE_END event.
        """

        # Prev frame counted past duration?
        if self.is_done:
            # Return
            return

        # Count
        self.fade_counter += dt * self.direction

        # Clamp counter
        self.fade_counter = clamp(self.fade_counter, 0.0, self.fade_duration)

        # Get counter over duration fraction
        fraction: float = self.fade_counter / self.fade_duration

        # Use fraction to map duration position to alpha position
        lerp_alpha: float = lerp(0, self.max_alpha, fraction)

        # Add lost truncated alpha from prev frame
        lerp_alpha += self.remainder

        # Truncate alpha
        self.alpha = int(clamp(lerp_alpha, 0.0, float(self.max_alpha)))

        # Store truncated floats for next frame
        self.remainder = lerp_alpha - float(self.alpha)

        # Set surf alpha
        self.surf.set_alpha(self.alpha)

        # Counter is 0?
        if self.fade_counter == 0:
            # Set is done true
            self.is_done = True

            # Fire INVISIBLE_END event
            for callback in self.event_listeners[self.INVISIBLE_END]:
                callback()

            # Make sure it is zero
            self.alpha = 0
            self.surf.set_alpha(self.alpha)

        # Counter reached duration?
        elif self.fade_counter == self.fade_duration:
            # Set is done true
            self.is_done = True

            # Fire OPAQUE_END event
            for callback in self.event_listeners[self.OPAQUE_END]:
                callback()

            # Make sure it is max
            self.alpha = self.max_alpha
            self.surf.set_alpha(self.alpha)

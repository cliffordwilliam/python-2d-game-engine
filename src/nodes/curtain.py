from typing import Callable

from constants import pg
from pygame.math import clamp
from pygame.math import lerp
from typeguard import typechecked


@typechecked
class Curtain:
    """
    A surf that can fades its alpha.

    Parameters:
    - surf_size_tuple: button surf.
    - topleft: button rect topleft.
    - text: button text.
    - text_topleft: relative to button rect.
    - description_text: text near screen bottom.

    Update:
    - Active curtain.

    Draw:
    - description.
    - surf.
    - active curtain.

    States:
    - INACTIVE.
    - ACTIVE.
    """

    # Events.
    INVISIBLE_END: int = 0
    OPAQUE_END: int = 1

    # Start settings enum.
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
        # Set surf.
        self.surf: pg.Surface = pg.Surface(surf_size_tuple)

        # Is invisible True?
        if is_invisible:
            # Turn surf invisible.
            self.surf.set_colorkey(color)

        # Fill surf with given color.
        self.surf.fill(color)

        # Get surf rect.
        self.rect: pg.Rect = self.surf.get_rect()

        # Fade in / out duration.
        self.fade_duration: float = duration

        # Set max alpha.
        self.max_alpha: int = max_alpha

        # Set initial alpha and fade counter.
        self.alpha: int = 0
        self.fade_counter: float = 0

        # Start INVISIBLE / OPAQUE.
        # Update alpha and fade counter.
        self.start_state: int = start_state
        # Start INVISIBLE?
        if self.start_state == self.INVISIBLE:
            self.alpha = 0
            self.fade_counter = 0
        # Start OPAQUE?
        elif self.start_state == self.OPAQUE:
            self.alpha = self.max_alpha
            self.fade_counter = self.fade_duration

        # Set surf alpha.
        self.surf.set_alpha(self.alpha)

        # Store truncated float.
        self.remainder: float = 0

        # Fade direction.
        self.direction: int = 0

        # Event subscribers list.
        self.listener_invisible_ends: list[Callable] = []
        self.listener_opaque_ends: list[Callable] = []

        # True when reached INVISIBLE_END / OPAQUE_END.
        self.is_done: bool = True

    def go_to_opaque(self) -> None:
        """
        Lerp the curtain to my max alpha.
        """

        # Go right opaque.
        self.direction = 1

        # Set is done false.
        self.is_done = False

    def go_to_invisible(self) -> None:
        """
        Lerp the curtain to alpha 0.
        """

        # Go left invisible.
        self.direction = -1

        # Set is done true.
        self.is_done = False

    def add_event_listener(self, value: Callable, event: int) -> None:
        """
        Use this to subscribe to my events:
        - INVISIBLE_END
        - OPAQUE_END
        """

        if event == self.INVISIBLE_END:
            self.listener_invisible_ends.append(value)
        elif event == self.OPAQUE_END:
            self.listener_opaque_ends.append(value)

    def jump_to_opaque(self) -> None:
        """
        Forces the alpha to jump to opaque, mutates:
        - alpha.
        - remainder.
        - fade_counter.
        """

        self.alpha = self.max_alpha
        self.remainder = 0
        self.fade_counter = self.fade_duration

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

        # No need to draw if my alpha is 0, I am invisible.
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

        # No need to count when is done true.
        if self.is_done:
            return

        # Count up or down.
        self.fade_counter += dt * self.direction

        # Clamp counter.
        self.fade_counter = clamp(self.fade_counter, 0, self.fade_duration)

        # Get fraction with counter and duration.
        fraction: float = self.fade_counter / self.fade_duration

        # Get alpha with fraction.
        lerp_alpha: float = lerp(0, self.max_alpha, fraction)

        # Add lost truncated alpha.
        lerp_alpha += self.remainder

        # Truncate alpha.
        self.alpha = int(clamp(round(lerp_alpha), 0, self.max_alpha))

        # Store truncated floats.
        self.remainder = lerp_alpha - self.alpha

        # Set surf alpha.
        self.surf.set_alpha(self.alpha)

        # Counter is 0?
        if self.fade_counter == 0:
            # Set is done true.
            self.is_done = True

            # Fire INVISIBLE_END event.
            for callback in self.listener_invisible_ends:
                callback()

            # Make sure it is zero.
            self.alpha = 0

        # Counter reached duration?
        elif self.fade_counter == self.fade_duration:
            # Set is done true.
            self.is_done = True

            # Fire OPAQUE_END event.
            for callback in self.listener_opaque_ends:
                callback()

            # Make sure it is max.
            self.alpha = self.max_alpha

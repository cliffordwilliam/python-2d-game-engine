from typing import Callable
from typing import List

from constants import pg
from pygame.math import clamp
from pygame.math import lerp
from typeguard import typechecked


@typechecked
class Curtain:
    """
    A surface alpha fader.

    Events:
    - INVISIBLE_END
    - OPAQUE_END

    Give me a surface.
    if is_invisible is set to True:
    - Curtain is always invisible.
    - But when you stick things to it, it fades.
    Set duration in float.
    Set start_state in invisible or opaque (enum).
    Set the max alpha of the opaque state in int.
    Add event listeners (optional).
    FIRST, Call go_to_invisible() or opaque to start_state fading.
    THEN, Call draw() (draw me).
    THEN, Call update() (update alpha value).
    """

    # Events.

    # Reached invisible.
    INVISIBLE_END: int = 0

    # Reached opaque.
    OPAQUE_END: int = 1

    # Enums.

    # Start invisible.
    INVISIBLE: int = 2

    # Start opaque.
    OPAQUE: int = 3

    def __init__(
        self,
        duration: float,
        start_state: int,
        max_alpha: int,
        surf: pg.Surface,
        is_invisible: bool,
    ):
        # The surf that alpha I manipulate.
        self.surf: pg.Surface = surf

        # is_invisible True?
        if is_invisible:
            # Set my surf to be always invisible.
            self.surf.set_colorkey("black")
            self.surf.fill("black")

        # Define surf OPAQUE's alpha.
        self.max_alpha: int = max_alpha

        # Use this to position me relative to topleft native.
        self.rect: pg.Rect = self.surf.get_rect()

        # Determine to count up or down. Default 0.
        self.direction: int = 0

        # Determine how long I fade in or out.
        self.fade_duration: float = duration

        # Either start INVISIBLE or OPAQUE.
        self.start_state: int = start_state

        # Set initial surf alpha and fade counter.
        self.alpha: int = 0
        self.fade_counter: float = 0

        # Start INVISIBLE?
        if self.start_state == self.INVISIBLE:
            # Surf alpha 0.
            # Fade counter 0.
            self.alpha = 0
            self.fade_counter = 0

        # Start OPAQUE?
        elif self.start_state == self.OPAQUE:
            # Surf alpha max_alpha.
            # Fade counter fade_duration.
            self.alpha = self.max_alpha
            self.fade_counter = self.fade_duration

        # Update actual surf alpha.
        self.surf.set_alpha(self.alpha)

        # Store lost float to int rounding.
        self.remainder: float = 0

        # INVISIBLE_END event subscribers list.
        self.listener_invisible_ends: List[Callable] = []
        # OPAQUE_END event subscribers list.
        self.listener_opaque_ends: List[Callable] = []

        # True when I have reached INVISIBLE_END or OPAQUE_END.
        self.is_done: bool = True

    def go_to_opaque(self) -> None:
        """
        Lerp the curtain to my max alpha.
        """

        # Go right (opaque).
        self.direction = 1

        # Is done False.
        self.is_done = False

    def go_to_invisible(self) -> None:
        """
        Lerp the curtain to alpha 0.
        """

        # Go left (invisible).
        self.direction = -1

        # Is done False.
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
        Call this to force the lerp to jump to opaque.
        """

        self.alpha = self.max_alpha
        self.remainder = 0
        self.fade_counter = self.fade_duration

    def set_max_alpha(self, value: int) -> None:
        """
        Sets the max_alpha of the surface.
        """

        self.max_alpha = value

    def draw(self, surf: pg.Surface, y_offset: int) -> None:
        """
        Blit myself to the given surface.
        Need to pass offset, useful for camera tricks:
            - Draw my surf somewhere else, not on my rect pos.
        """

        # No need to draw if my alpha is 0, I am invisible.
        if self.alpha == 0:
            return

        surf.blit(self.surf, (self.rect.x, self.rect.y + y_offset))

    def update(self, dt: int) -> None:
        """
        Update to lerp my curtain.
        """

        # No need to count when is done true.
        if self.is_done:
            return

        # Count up or down.
        self.fade_counter += dt * self.direction

        # Clamp counter to 0 and fade duration.
        self.fade_counter = clamp(self.fade_counter, 0, self.fade_duration)

        # Use counter and duration to get: fraction.
        fraction: float = self.fade_counter / self.fade_duration

        # Use fraction to get alpha.
        lerp_alpha: float = lerp(0, self.max_alpha, fraction)

        # Add lost alpha from remainder.
        lerp_alpha += self.remainder

        # Int, clamp and round this alpha.
        self.alpha = int(clamp(round(lerp_alpha), 0, self.max_alpha))

        # Store lost floats from truncation in previous line.
        self.remainder = lerp_alpha - self.alpha

        # Set actual surface alpha.
        self.surf.set_alpha(self.alpha)

        # Counter is 0?
        if self.fade_counter == 0:
            # Is done true.
            self.is_done = True

            # Fire INVISIBLE_END event.
            for callback in self.listener_invisible_ends:
                callback()

        # Counter reached duration?
        elif self.fade_counter == self.fade_duration:
            # Is done true.
            self.is_done = True

            # Fire OPAQUE_END event.
            for callback in self.listener_opaque_ends:
                callback()

from typing import Callable
from typing import List

from constants import NATIVE_H
from constants import NATIVE_SURF
from constants import NATIVE_W
from constants import pg
from pygame.math import clamp
from pygame.math import lerp
from typeguard import typechecked


@typechecked
class Curtain:
    """
    Set duration in float.
    Set start in invisible or opaque.
    Set the max alpha of the opaque state.
    Add event listeners to either invisible_end or opaque_end.
    Call the draw and update method.
    Call the go_to_invisible() or opaque to control where it fades into.
    """

    INVISIBLE_END = 0
    OPAQUE_END = 1
    INVISIBLE = 2
    OPAQUE = 3

    def __init__(self, duration: float, start: int = 2, max_alpha: int = 255):
        self.start: int = start

        self.max_alpha: int = max_alpha

        self.surface: pg.Surface = pg.Surface((NATIVE_W, NATIVE_H))
        self.surface.fill("black")

        self.direction: int = 0

        self.surface.set_alpha(0)
        self.alpha: int = 0
        self.fade_duration: float = duration
        self.fade_timer: float = 0

        if self.start == self.OPAQUE:
            self.surface.set_alpha(self.max_alpha)
            self.alpha = self.max_alpha
            self.fade_duration = duration
            self.fade_timer = self.fade_duration

        self.remainder: float = 0

        self.listener_invisible_ends: List[Callable] = []
        self.listener_opaque_ends: List[Callable] = []

        self.is_done_lerping: bool = True

    def go_to_opaque(self):
        """
        Lerp the curtain to my max alpha.
        """
        self.direction = 1

        self.is_done_lerping = False

    def go_to_invisible(self):
        """
        Lerp the curtain to alpha 0.
        """
        self.direction = -1

        self.is_done_lerping = False

    def add_event_listener(self, value: Callable, event: int):
        """
        Subscribe to my events.
        """
        if event == self.INVISIBLE_END:
            self.listener_invisible_ends.append(value)

        elif event == self.OPAQUE_END:
            self.listener_opaque_ends.append(value)

    def draw(self):
        """
        Blit myself to native surface.
        """
        if self.alpha == 0:
            return

        NATIVE_SURF.blit(self.surface, (0, 0))

    def update(self, dt: int):
        """
        Update to lerp my curtain.
        """
        if self.is_done_lerping:
            return

        self.fade_timer += dt * self.direction

        self.fade_timer = clamp(self.fade_timer, 0, self.fade_duration)

        fraction = self.fade_timer / self.fade_duration

        lerp_alpha = lerp(0, self.max_alpha, fraction)

        lerp_alpha += self.remainder

        self.alpha = int(clamp(round(lerp_alpha), 0, self.max_alpha))

        self.remainder = lerp_alpha - self.alpha

        self.surface.set_alpha(self.alpha)

        if self.fade_timer == 0:
            self.is_done_lerping = True

            for callback in self.listener_invisible_ends:
                callback()

        elif self.fade_timer == self.fade_duration:
            self.is_done_lerping = True

            for callback in self.listener_opaque_ends:
                callback()

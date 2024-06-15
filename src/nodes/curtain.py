from typing import Callable
from typing import List

from constants import NATIVE_SURF
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

    INVISIBLE_END: int = 0
    OPAQUE_END: int = 1
    INVISIBLE: int = 2
    OPAQUE: int = 3

    def __init__(
        self,
        duration: float,
        start: int,
        max_alpha: int,
        surf: pg.Surface,
        is_invisible: bool,
    ):
        self.start: int = start

        self.max_alpha: int = max_alpha

        self.surf: pg.Surface = surf

        if is_invisible:
            self.surf.set_colorkey("black")

        self.surf.fill("black")

        self.rect: pg.Rect = self.surf.get_rect()

        self.direction: int = 0

        self.surf.set_alpha(0)
        self.alpha: int = 0
        self.fade_duration: float = duration
        self.fade_timer: float = 0

        if self.start == self.OPAQUE:
            self.surf.set_alpha(self.max_alpha)
            self.alpha = self.max_alpha
            self.fade_duration = duration
            self.fade_timer = self.fade_duration

        self.remainder: float = 0

        self.listener_invisible_ends: List[Callable] = []
        self.listener_opaque_ends: List[Callable] = []

        self.is_done_lerping: bool = True

    def go_to_opaque(self) -> None:
        """
        Lerp the curtain to my max alpha.
        """
        self.direction = 1

        self.is_done_lerping = False

    def go_to_invisible(self) -> None:
        """
        Lerp the curtain to alpha 0.
        """
        self.direction = -1

        self.is_done_lerping = False

    def add_event_listener(self, value: Callable, event: int) -> None:
        """
        Subscribe to my events.
        """
        if event == self.INVISIBLE_END:
            self.listener_invisible_ends.append(value)

        elif event == self.OPAQUE_END:
            self.listener_opaque_ends.append(value)

    def jump_to_opaque(self) -> None:
        self.alpha = self.max_alpha
        self.remainder = 0
        self.fade_timer = self.fade_duration

    def set_max_alpha(self, value: int) -> None:
        self.max_alpha = value

    def draw(self) -> None:
        """
        Blit myself to native surf.
        """
        if self.alpha == 0:
            return

        NATIVE_SURF.blit(self.surf, self.rect)

    def update(self, dt: int) -> None:
        """
        Update to lerp my curtain.
        """
        if self.is_done_lerping:
            return

        self.fade_timer += dt * self.direction

        self.fade_timer = clamp(self.fade_timer, 0, self.fade_duration)

        fraction: float = self.fade_timer / self.fade_duration

        lerp_alpha: float = lerp(0, self.max_alpha, fraction)

        lerp_alpha += self.remainder

        self.alpha = int(clamp(round(lerp_alpha), 0, self.max_alpha))

        self.remainder = lerp_alpha - self.alpha

        self.surf.set_alpha(self.alpha)

        if self.fade_timer == 0:
            self.is_done_lerping = True

            for callback in self.listener_invisible_ends:
                callback()

        elif self.fade_timer == self.fade_duration:
            self.is_done_lerping = True

            for callback in self.listener_opaque_ends:
                callback()

from typing import TYPE_CHECKING

from constants import NATIVE_SURF
from nodes.curtain import Curtain
from nodes.timer import Timer


if TYPE_CHECKING:
    from nodes.game import Game


class CreatedBySplashScreen:
    def __init__(self, game: "Game"):
        self.game = game

        self.curtain_duration: float = 1000.0
        self.curtain_max_alpha: int = 255
        self.curtain = Curtain(
            self.curtain_duration,
            Curtain.OPAQUE, self.curtain_max_alpha
        )
        self.curtain.add_event_listener(
            self.on_curtain_invisible, Curtain.INVISIBLE_END
        )
        self.curtain.add_event_listener(
            self.on_curtain_opaque, Curtain.OPAQUE_END)

        self.fadeout_delay_timer = Timer(1000)
        self.fadeout_delay_timer.add_event_listener(
            self.on_timer_end, Timer.END
        )

    def on_timer_end(self):
        self.curtain.go_to_invisible()

    def on_curtain_invisible(self):
        return

    def on_curtain_opaque(self):
        return

    def draw(self):
        NATIVE_SURF.fill("pink")
        self.curtain.draw()

    def update(self, dt: int):
        self.curtain.update(dt)
        self.fadeout_delay_timer.update(dt)

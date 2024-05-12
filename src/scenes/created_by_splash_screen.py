from constants import NATIVE_SURF
from constants import TYPE_CHECKING


if TYPE_CHECKING:
    from nodes.game import Game


class CreatedBySplashScreen:
    def __init__(self, game: "Game"):
        self.game = game

    def draw(self):
        NATIVE_SURF.fill("pink")

    def update(self, dt):
        return

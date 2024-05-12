from typing import TYPE_CHECKING

from constants import NATIVE_SURF


if TYPE_CHECKING:
    from nodes.game import Game


class CreatedBySplashScreen:
    def __init__(self, game: "Game"):
        self.game = game

    def draw(self):
        NATIVE_SURF.fill("pink")

    def update(self, dt):
        return

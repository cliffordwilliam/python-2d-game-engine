from constants import CLOCK
from constants import EVENTS
from constants import FPS
from constants import NATIVE_SURF
from constants import pg
from nodes.game import Game

game: Game = Game("CreatedBySplashScreen")

while 1:
    dt: int = CLOCK.tick(FPS)

    for event in pg.event.get(EVENTS):
        game.event(event)

    game.current_scene.draw()

    game.current_scene.update(dt)

    # REMOVE IN BUILD
    game.debug_draw.add(
        {
            "type": "text",
            "layer": 6,
            "x": 0,
            "y": 0,
            "text": f"fps: {int(CLOCK.get_fps())}",
        }
    )

    if game.is_debug:
        game.debug_draw.draw()

    scaled_native_surf: pg.Surface = pg.transform.scale_by(
        NATIVE_SURF, game.resolution
    )
    game.window_surf.blit(scaled_native_surf, (0, game.y_offset))
    pg.display.update()

    game.reset_just_events()

from constants import CLOCK
from constants import EVENTS
from constants import FPS
from constants import NATIVE_SURF
from constants import NEXT_FRAME
from constants import pg
from nodes.game import Game
from nodes.options_menu import OptionsMenu

# Has the following instances:
# - Game.
# - OptionsMenu.

# Responsible for managing current scenes.
# Scenes can be: splash screens, load data screen, gameplay scene.
game: Game = Game("CreatedBySplashScreen")

# Options menu is present all the time in any scenes.
# Current scene and options menu cannot be updated at the same time.
# Responsible for being the front-end to the json setting data base.
options_menu: OptionsMenu = OptionsMenu(game)

# The main game loop.
while 1:
    # REMOVE IN BUILD
    if game.is_per_frame:
        for event in pg.event.get(EVENTS):
            game.event(event)

        if pg.key.get_just_pressed()[NEXT_FRAME]:
            game.current_scene.draw()

            if game.is_options_menu_active:
                options_menu.draw()
                options_menu.update(16)  # Hardcoded 16 dt.
            else:
                game.current_scene.update(16)  # Hardcoded 16 dt.

            # REMOVE IN BUILD
            game.debug_draw.add(
                {
                    "type": "text",
                    "layer": 6,
                    "x": 0,
                    "y": 0,
                    "text": f"fps: {CLOCK.get_fps()}",
                }
            )

            # REMOVE IN BUILD
            if game.is_debug:
                game.debug_draw.draw()

            game.window_surf.blit(
                pg.transform.scale_by(NATIVE_SURF, game.resolution_scale),
                (0, game.native_y_offset),
            )

            pg.display.update()

            game.reset_just_events()

    else:
        dt: int = CLOCK.tick(FPS)

        # REMOVE IN BUILD
        # Quick hacky solution to prevent dt build up in frame by frame debug.
        # In frame by frame mode, must spend at least 1 s in there.
        if dt > 1000:
            dt = 16

        for event in pg.event.get(EVENTS):
            game.event(event)

        game.current_scene.draw()

        if game.is_options_menu_active:
            options_menu.draw()
            options_menu.update(dt)
        else:
            game.current_scene.update(dt)

        # REMOVE IN BUILD
        game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 0,
                "text": f"fps: {CLOCK.get_fps()}",
            }
        )

        # REMOVE IN BUILD
        if game.is_debug:
            game.debug_draw.draw()

        game.window_surf.blit(
            pg.transform.scale_by(NATIVE_SURF, game.resolution_scale),
            (0, game.native_y_offset),
        )

        pg.display.update()

        game.reset_just_events()

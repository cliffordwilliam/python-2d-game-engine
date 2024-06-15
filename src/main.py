from constants import CLOCK
from constants import EVENTS
from constants import FPS
from constants import NATIVE_SURF
from constants import NEXT_FRAME
from constants import pg
from nodes.game import Game
from nodes.options_menu import OptionsMenu

game: Game = Game("CreatedBySplashScreen")

# Treat this like a global debug mode
options_menu: OptionsMenu = OptionsMenu(game)


while 1:
    # REMOVE IN BUILD
    if game.is_per_frame:
        for event in pg.event.get(EVENTS):
            game.event(event)
        if pg.key.get_just_pressed()[NEXT_FRAME]:
            game.current_scene.draw()

            game.current_scene.update(16)

            if game.is_options_menu_active:
                options_menu.draw()
                options_menu.update(16)
            else:
                game.current_scene.update(16)

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
                pg.transform.scale_by(NATIVE_SURF, game.resolution),
                (0, game.y_offset),
            )
            pg.display.update()

            game.reset_just_events()

    else:
        dt: int = CLOCK.tick(FPS)

        # REMOVE IN BUILD
        # Quick hacky solution to prevent dt build up in frame by frame debug
        # Most def I will debug more than 1s anyways
        if dt > 1000:
            dt = 16

        for event in pg.event.get(EVENTS):
            game.event(event)

        game.current_scene.draw()

        # game.current_scene.update(dt)

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

        scaled_native_surf: pg.Surface = pg.transform.scale_by(
            NATIVE_SURF, game.resolution
        )
        game.window_surf.blit(scaled_native_surf, (0, game.y_offset))
        pg.display.update()

        game.reset_just_events()

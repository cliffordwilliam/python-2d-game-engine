from constants import CLOCK
from constants import EVENTS
from constants import FPS
from constants import NATIVE_SURF
from constants import NEXT_FRAME
from constants import pg
from nodes.game import Game
from nodes.options_menu import OptionsMenu

game: Game = Game("CreatedBySplashScreen")
options_menu: OptionsMenu = OptionsMenu(game)

while 1:
    # REMOVE IN BUILD
    if game.is_per_frame:
        for event in pg.event.get(EVENTS):
            game.event_handler.event(event)

            if game.event_handler.is_0_just_pressed:
                game.is_debug = not game.is_debug
            if game.event_handler.is_9_just_pressed:
                game.is_per_frame = not game.is_per_frame

        if pg.key.get_just_pressed()[NEXT_FRAME]:
            game.current_scene.draw()

            if game.is_options_menu_active:
                options_menu.draw()
                options_menu.update(16)  # Hardcoded 16 dt
            else:
                game.current_scene.update(16)  # Hardcoded 16 dt

            if game.is_debug:
                game.debug_draw.draw()

            pg.display.set_caption("FPS: NAN")

            pg.transform.scale(NATIVE_SURF, (game.window_width, game.window_height), game.window_surf)

            pg.display.update()

            game.event_handler.reset_just_events()

    else:
        # Limit to fps, gets dt
        dt: int = CLOCK.tick(FPS)

        # REMOVE IN BUILD
        if dt > 1000:
            dt = 16

        # Update event handler flags
        for event in pg.event.get(EVENTS):
            game.event_handler.event(event)

            # REMOVE IN BUILD
            if game.event_handler.is_0_just_pressed:
                game.is_debug = not game.is_debug
            if game.event_handler.is_9_just_pressed:
                game.is_per_frame = not game.is_per_frame

        # Current scene draw
        game.current_scene.draw()

        # Current scene or option menu draw?
        if game.is_options_menu_active:
            options_menu.draw()
            options_menu.update(dt)
        else:
            game.current_scene.update(dt)

        # REMOVE IN BUILD
        if game.is_debug:
            game.debug_draw.draw()

        # REMOVE IN BUILD
        pg.display.set_caption(f"FPS: {CLOCK.get_fps():.0f}")

        # Scale native surf to window surf
        pg.transform.scale(NATIVE_SURF, (game.window_width, game.window_height), game.window_surf)

        # Update whole window
        pg.display.update()

        # Reset the just pressed event handler flags
        game.event_handler.reset_just_events()

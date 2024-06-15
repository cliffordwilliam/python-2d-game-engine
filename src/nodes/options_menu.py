from typing import List
from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_H
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_W
from constants import pg
from nodes.button import Button
from nodes.button_container import ButtonContainer
from nodes.curtain import Curtain
from nodes.timer import Timer
from typeguard import typechecked

# TODO: Find hotkey to remove unused imports


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class OptionsMenu:
    """
    Since most things can access pause menu, it is autoload
    """

    JUST_ENTERED: int = 0
    GOING_TO_OPAQUE: int = 1
    REACHED_OPAQUE: int = 2
    GOING_TO_INVISIBLE: int = 3
    REACHED_INVISIBLE: int = 4

    # REMOVE IN BUILD
    state_names: List = [
        "JUST_ENTERED",
        "GOING_TO_OPAQUE",
        "REACHED_OPAQUE",
        "GOING_TO_INVISIBLE",
        "REACHED_INVISIBLE",
    ]

    def __init__(self, game: "Game"):
        self.game = game

        self.initial_state: int = self.JUST_ENTERED

        self.native_clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        self.curtain_surf: pg.Surface = pg.Surface((NATIVE_W, NATIVE_H))
        self.curtain_surf.fill(self.native_clear_color)
        self.curtain_duration: float = 1000.0
        self.curtain_start: int = Curtain.INVISIBLE
        self.curtain_max_alpha: int = 255
        self.curtain_is_invisible: int = False
        self.curtain: Curtain = Curtain(
            self.curtain_duration,
            self.curtain_start,
            self.curtain_max_alpha,
            self.curtain_surf,
            self.curtain_is_invisible,
        )
        self.curtain.add_event_listener(
            self.on_curtain_invisible, Curtain.INVISIBLE_END
        )
        self.curtain.add_event_listener(
            self.on_curtain_opaque, Curtain.OPAQUE_END
        )

        self.entry_delay_timer_duration: float = 0
        # Move magic delay value as prop in all timer uses
        self.entry_delay_timer: Timer = Timer(self.entry_delay_timer_duration)
        self.entry_delay_timer.add_event_listener(
            self.on_entry_delay_timer_end, Timer.END
        )

        self.exit_delay_timer_duration: float = 0
        self.exit_delay_timer: Timer = Timer(self.exit_delay_timer_duration)
        self.exit_delay_timer.add_event_listener(
            self.on_exit_delay_timer_end, Timer.END
        )

        self.title_text: str = "options"
        self.title_rect: pg.Rect = FONT.get_rect(self.title_text)
        self.title_rect.center = NATIVE_RECT.center
        self.title_rect.y = 11

        self.resolution_button: Button = Button(
            149, 9, (87, 18), "resolutions", (4, 2), "set resolutions"
        )
        self.exit_button: Button = Button(
            149, 9, (87, 28), "exit", (4, 2), "exit options menu"
        )
        self.button_container: ButtonContainer = ButtonContainer(
            [
                self.resolution_button,
                self.exit_button,
            ]
        )

        self.button_container.add_event_listener(
            self.on_button_selected, ButtonContainer.BUTTON_SELECTED
        )

        self.button_container.add_event_listener(
            self.on_button_index_changed, ButtonContainer.INDEX_CHANGED
        )

        self.selected_button: Button = self.resolution_button
        self.focused_button: Button = self.resolution_button

        self.resolution_texts: List = [
            "320 x 160",
            "640 x 320",
        ]
        self.resolution_texts_len: int = len(self.resolution_texts)
        self.resolution_index: int = 0
        self.resolution_text: str = self.resolution_texts[
            self.resolution_index
        ]
        self.resolution_text_rect: pg.Rect = FONT.get_rect(
            self.resolution_text
        )
        self.resolution_text_rect.topright = (
            self.resolution_button.rect.topright
        )
        self.resolution_text_rect.x -= 3
        self.resolution_text_rect.y += 2

        self.state: int = self.initial_state

        self.init_state()

    def init_state(self) -> None:
        """
        This is set state for none to initial state.
        """
        pass

    def set_resolution_index(self, value: int) -> None:
        self.resolution_index = value
        self.resolution_index = (
            self.resolution_index % self.resolution_texts_len
        )
        self.resolution_text = self.resolution_texts[self.resolution_index]
        self.resolution_text_rect = FONT.get_rect(self.resolution_text)
        self.resolution_text_rect.topright = (
            self.resolution_button.rect.topright
        )
        self.resolution_text_rect.x -= 3
        self.resolution_text_rect.y += 2

    def on_entry_delay_timer_end(self) -> None:
        self.set_state(self.GOING_TO_OPAQUE)

    def on_exit_delay_timer_end(self) -> None:
        # Exit options here
        # Set my state back to JUST_ENTERED for next entry here
        # No need for setter, bypass setter
        self.exit_delay_timer.reset()
        self.entry_delay_timer.reset()
        self.state = self.JUST_ENTERED
        self.game.set_is_options_menu_active(False)

    def on_curtain_invisible(self) -> None:
        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        self.set_state(self.REACHED_OPAQUE)

    def on_button_index_changed(self, focused_button: Button) -> None:
        """
        Called and pass the newly focused button
        """
        self.focused_button = focused_button

    def on_button_selected(self, selected_button: Button) -> None:
        """
        Remember selected
        Need to wait for curtain to go to opaque
        Then use remembered button to switch statement to go somewhere
        """
        self.selected_button = selected_button

        if self.resolution_button == self.selected_button:
            pass

        elif self.exit_button == self.selected_button:
            self.set_state(self.GOING_TO_INVISIBLE)

    def draw(self) -> None:
        self.curtain.surf.fill(self.native_clear_color)
        FONT.render_to(
            self.curtain.surf,
            self.title_rect,
            self.title_text,
            self.font_color,
        )
        self.button_container.draw(self.curtain.surf)
        FONT.render_to(
            self.curtain.surf,
            self.resolution_text_rect,
            self.resolution_text,
            self.font_color,
        )
        pg.draw.line(self.curtain.surf, "#0193bc", (87, 79), (232, 79), 1)
        pg.draw.line(self.curtain.surf, "#0193bc", (160, 18), (160, 78), 1)
        self.curtain.draw(NATIVE_SURF)

    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 6,
                "text": (
                    f"options menu state "
                    f"state: {self.state_names[self.state]}"
                ),
            }
        )

        if self.state == self.JUST_ENTERED:
            self.entry_delay_timer.update(dt)

        elif self.state == self.GOING_TO_OPAQUE:
            self.curtain.update(dt)

        elif self.state == self.REACHED_OPAQUE:
            self.button_container.event(self.game)
            self.button_container.update(dt)

            if self.resolution_button == self.focused_button:
                if self.game.is_left_just_pressed:
                    new_value = self.resolution_index - 1
                    self.set_resolution_index(new_value)
                if self.game.is_right_just_pressed:
                    new_value = self.resolution_index + 1
                    self.set_resolution_index(new_value)

            elif self.exit_button == self.focused_button:
                pass

        elif self.state == self.GOING_TO_INVISIBLE:
            self.curtain.update(dt)
            self.button_container.update(dt)

        elif self.state == self.REACHED_INVISIBLE:
            self.exit_delay_timer.update(dt)

    def set_state(self, value: int) -> None:
        old_state: int = self.state
        self.state = value

        if old_state == self.JUST_ENTERED:
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()

        elif old_state == self.GOING_TO_OPAQUE:
            if self.state == self.REACHED_OPAQUE:
                self.button_container.set_is_input_allowed(True)

        elif old_state == self.REACHED_OPAQUE:
            if self.state == self.GOING_TO_INVISIBLE:
                self.button_container.set_is_input_allowed(False)
                self.curtain.go_to_invisible()

        elif old_state == self.GOING_TO_INVISIBLE:
            if self.state == self.REACHED_INVISIBLE:
                pass

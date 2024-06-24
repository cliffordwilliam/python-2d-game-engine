from typing import List
from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import pg
from nodes.button import Button
from nodes.button_container import ButtonContainer
from nodes.curtain import Curtain
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class OptionsMenu:
    """
    Since most things can access pause menu, it is autoloaded.
    """

    # States.
    JUST_ENTERED: int = 0
    GOING_TO_OPAQUE: int = 1
    REACHED_OPAQUE: int = 2
    GOING_TO_INVISIBLE: int = 3
    REACHED_INVISIBLE: int = 4

    # REMOVE IN BUILD
    # For debug drwa.
    state_names: List[str] = [
        "JUST_ENTERED",
        "GOING_TO_OPAQUE",
        "REACHED_OPAQUE",
        "GOING_TO_INVISIBLE",
        "REACHED_INVISIBLE",
    ]

    def __init__(self, game: "Game"):
        # For input and toggle options menu mode.
        self.game = game

        # Set initial state.
        self.initial_state: int = self.JUST_ENTERED

        # Background color and font color.
        self.native_clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        # Curtain here is my surface.
        self.curtain_surf: pg.Surface = pg.Surface(
            (NATIVE_WIDTH, NATIVE_HEIGHT)
        )
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

        # Delay timers
        self.entry_delay_timer_duration: float = 0
        self.entry_delay_timer: Timer = Timer(self.entry_delay_timer_duration)
        self.entry_delay_timer.add_event_listener(
            self.on_entry_delay_timer_end, Timer.END
        )
        self.exit_delay_timer_duration: float = 0
        self.exit_delay_timer: Timer = Timer(self.exit_delay_timer_duration)
        self.exit_delay_timer.add_event_listener(
            self.on_exit_delay_timer_end, Timer.END
        )

        # Options title text.
        self.title_text: str = "options"
        self.title_rect: pg.Rect = FONT.get_rect(self.title_text)
        self.title_rect.center = NATIVE_RECT.center
        self.title_rect.y = 11

        # Buttons and button container.
        self.button_height: int = 9
        self.resolution_button: Button = Button(
            149,
            self.button_height,
            (87, 18),
            "resolutions",
            (4, 2),
            "set resolutions",
        )
        self.exit_button: Button = Button(
            73,
            self.button_height,
            (87, 18),
            "exit",
            (4, 2),
            "exit options menu",
        )
        self.button_container: ButtonContainer = ButtonContainer(
            [
                self.resolution_button,
                self.exit_button,
            ],
            0,
            2,
            False,
        )
        self.button_container.add_event_listener(
            self.on_button_selected, ButtonContainer.BUTTON_SELECTED
        )
        self.button_container.add_event_listener(
            self.on_button_index_changed, ButtonContainer.INDEX_CHANGED
        )

        # Keep track of who is selected and focused.
        self.selected_button: Button = self.resolution_button
        self.focused_button: Button = self.resolution_button

        # Resolution texts.
        self.resolution_texts: List[str] = [
            "< 320  x 160 >",
            "< 640  x 320 >",
            "< 960  x 480 >",
            "< 1280 x 640 >",
            "< 1600 x 800 >",
            "< 1920 x 960 >",
            "< fullscreen >",
        ]
        self.resolution_texts_len: int = len(self.resolution_texts)
        self.resolution_index: int = int(
            self.game.local_settings_dict["resolution_scale"]
        )
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

        # Decoration lines.
        self.decoration_vertical_start = (160, 18)
        self.decoration_vertical_x: int = 160
        self.decoration_vertical_top: int = 18
        self.decoration_vetical_height: int = (
            self.button_container.buttons_len * (self.button_height + 1)
        )
        self.decoration_vertical_bottom: int = (
            self.decoration_vertical_top + self.decoration_vetical_height
        )
        self.decoration_horizontal_y: int = self.decoration_vertical_bottom
        self.decoration_horizontal_left: int = 87
        self.decoration_horizontal_right: int = 232

        # Initial state.
        self.state: int = self.initial_state

    def set_resolution_index(self, value: int) -> None:
        """
        Left and right input while resolution button is focused.
        """

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
        """
        Delay ends, starts going to opaque.
        """

        self.set_state(self.GOING_TO_OPAQUE)

    def on_exit_delay_timer_end(self) -> None:
        """
        Exit options here.
        Set my state back to JUST_ENTERED for next entry here.
        No need for setter, bypass setter.
        """

        self.exit_delay_timer.reset()
        self.entry_delay_timer.reset()
        self.state = self.JUST_ENTERED
        self.game.set_is_options_menu_active(False)

    def on_curtain_invisible(self) -> None:
        """
        Set REACHED_INVISIBLE state.
        """

        self.set_state(self.REACHED_INVISIBLE)

    def on_curtain_opaque(self) -> None:
        """
        Set REACHED_OPAQUE state.
        """

        self.set_state(self.REACHED_OPAQUE)

    def on_button_index_changed(self, focused_button: Button) -> None:
        """
        When index changes, update focused_button.
        """
        self.focused_button = focused_button

    def on_button_selected(self, selected_button: Button) -> None:
        """
        Remember selected.
        Need to wait for curtain to go to opaque.
        Then use remembered button to go somewhere.
        """

        self.selected_button = selected_button

        # Resolution button selected?
        if self.resolution_button == self.selected_button:
            pass

        # Exit button selected?
        elif self.exit_button == self.selected_button:
            # Set my state to GOING_TO_INVISIBLE.
            self.set_state(self.GOING_TO_INVISIBLE)

            # TODO: Move this to apply button, also add another called revert.
            # TODO: For now apply change is here + save to disk.
            self.game.set_resolution(self.resolution_index)
            self.game.sync_local_saves_with_disk_saves()

    def draw(self) -> None:
        """
        - Clear curtain.
        - Draw title.
        - Button container.
        - Resolution texts.
        - Decorations.
        - Draw curtain on native.
        """

        # Clear curtain.
        self.curtain.surf.fill(self.native_clear_color)

        # Draw title.
        FONT.render_to(
            self.curtain.surf,
            self.title_rect,
            self.title_text,
            self.font_color,
        )

        # Button container.
        self.button_container.draw(self.curtain.surf)

        # Resolution texts.
        FONT.render_to(
            self.curtain.surf,
            self.resolution_text_rect,
            self.resolution_text,
            self.font_color,
        )

        # Decorations.
        pg.draw.line(
            self.curtain.surf,
            "#0193bc",
            (self.decoration_horizontal_left, self.decoration_horizontal_y),
            (self.decoration_horizontal_right, self.decoration_horizontal_y),
            1,
        )
        pg.draw.line(
            self.curtain.surf,
            "#0193bc",
            (self.decoration_vertical_x, self.decoration_vertical_top),
            (self.decoration_vertical_x, self.decoration_vertical_bottom),
            1,
        )

        # Draw curtain on native.
        self.curtain.draw(NATIVE_SURF, 0)

    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        # Draw my state.
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

        # JUST_ENTERED state.
        if self.state == self.JUST_ENTERED:
            self.entry_delay_timer.update(dt)

        # GOING_TO_OPAQUE state.
        elif self.state == self.GOING_TO_OPAQUE:
            self.curtain.update(dt)

        # REACHED_OPAQUE state.
        elif self.state == self.REACHED_OPAQUE:
            # Update button index.
            self.button_container.event(self.game)

            # Update button active alpha.
            self.button_container.update(dt)

            # Focusing on resolution button?
            if self.resolution_button == self.focused_button:
                # Initialize new value.
                new_value = self.resolution_index
                is_pressed_left_or_right: bool = False

                # Left?
                if self.game.is_left_just_pressed:
                    new_value -= 1
                    is_pressed_left_or_right = True
                # Right?
                if self.game.is_right_just_pressed:
                    new_value += 1
                    is_pressed_left_or_right = True

                if is_pressed_left_or_right:
                    # Frame perfect press both, no index change, return.
                    if self.resolution_index != new_value:
                        self.set_resolution_index(new_value)

            # Focusing on exit button?
            elif self.exit_button == self.focused_button:
                pass

        # GOING_TO_INVISIBLE state.
        elif self.state == self.GOING_TO_INVISIBLE:
            self.curtain.update(dt)
            self.button_container.update(dt)

        # REACHED_INVISIBLE state.
        elif self.state == self.REACHED_INVISIBLE:
            self.exit_delay_timer.update(dt)

    def set_state(self, value: int) -> None:
        old_state: int = self.state
        self.state = value

        # From JUST_ENTERED
        if old_state == self.JUST_ENTERED:
            # To GOING_TO_OPAQUE
            if self.state == self.GOING_TO_OPAQUE:
                self.curtain.go_to_opaque()

        # From GOING_TO_OPAQUE
        elif old_state == self.GOING_TO_OPAQUE:
            # To REACHED_OPAQUE
            if self.state == self.REACHED_OPAQUE:
                self.button_container.set_is_input_allowed(True)

        # From REACHED_OPAQUE
        elif old_state == self.REACHED_OPAQUE:
            # To GOING_TO_INVISIBLE
            if self.state == self.GOING_TO_INVISIBLE:
                self.button_container.set_is_input_allowed(False)
                self.curtain.go_to_invisible()

        # From GOING_TO_INVISIBLE
        elif old_state == self.GOING_TO_INVISIBLE:
            # To REACHED_INVISIBLE
            if self.state == self.REACHED_INVISIBLE:
                pass

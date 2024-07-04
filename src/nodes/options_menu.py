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
    Autoload scene.
    Activate this to update this instead of current scene.

    States:
    - JUST_ENTERED.
    - GOING_TO_OPAQUE.
    - REACHED_OPAQUE.
    - GOING_TO_INVISIBLE.
    - REACHED_INVISIBLE.

    Parameters:
    - game:
        - read / update local save.
        - activates / deactivates options menu.
        - sync disk to local save.
        - debug draw.
        - input flags.

    Update:
    - state machine.

    Draw:
    - clear curtain.
    - draw title.
    - button container.
    - resolution texts.
    - decorations.
    - draw curtain on native.
    """

    # States.
    JUST_ENTERED: int = 0
    GOING_TO_OPAQUE: int = 1
    REACHED_OPAQUE: int = 2
    GOING_TO_INVISIBLE: int = 3
    REACHED_INVISIBLE: int = 4
    REBIND: int = 5

    # REMOVE IN BUILD
    # For debug draw.
    state_names: list[str] = [
        "JUST_ENTERED",
        "GOING_TO_OPAQUE",
        "REACHED_OPAQUE",
        "GOING_TO_INVISIBLE",
        "REACHED_INVISIBLE",
        "REBIND",
    ]

    def __init__(self, game: "Game"):
        # For input and toggle options menu mode.
        self.game = game

        # Set initial state.
        self.initial_state: int = self.JUST_ENTERED

        # Background color and font color.
        self.curtain_clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        # Curtain here is my surf.
        self.curtain_duration: float = 1000.0
        self.curtain_start: int = Curtain.INVISIBLE
        self.curtain_max_alpha: int = 255
        self.curtain_is_invisible: int = False
        self.curtain: Curtain = Curtain(
            self.curtain_duration,
            self.curtain_start,
            self.curtain_max_alpha,
            (NATIVE_WIDTH, NATIVE_HEIGHT),
            self.curtain_is_invisible,
            self.curtain_clear_color,
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
        self.wide_button_width: int = 146
        self.narrow_button_width: int = 73
        self.button_flex_col_topleft: tuple[int, int] = (87, 18)
        self.buttton_text_topleft_offset: tuple[int, int] = (4, 2)
        self.resolution_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "resolutions",
            self.buttton_text_topleft_offset,
            "set resolutions with left and right input",
        )
        self.up_input_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "up input",
            self.buttton_text_topleft_offset,
            "press enter to rebind up input",
        )
        self.down_input_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "down input",
            self.buttton_text_topleft_offset,
            "press enter to rebind down input",
        )
        self.left_input_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "left input",
            self.buttton_text_topleft_offset,
            "press enter to rebind left input",
        )
        self.right_input_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "right input",
            self.buttton_text_topleft_offset,
            "press enter to rebind right input",
        )
        self.enter_input_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "enter input",
            self.buttton_text_topleft_offset,
            "press enter to rebind enter input",
        )
        self.pause_input_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "pause input",
            self.buttton_text_topleft_offset,
            "press pause to rebind pause input",
        )
        self.jump_input_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "jump input",
            self.buttton_text_topleft_offset,
            "press jump to rebind jump input",
        )
        self.attack_input_button: Button = Button(
            (self.wide_button_width, self.button_height),
            self.button_flex_col_topleft,
            "attack input",
            self.buttton_text_topleft_offset,
            "press attack to rebind attack input",
        )
        self.apply_button: Button = Button(
            (self.narrow_button_width, self.button_height),
            self.button_flex_col_topleft,
            "apply",
            self.buttton_text_topleft_offset,
            "apply and save changes",
        )
        self.reset_button: Button = Button(
            (self.narrow_button_width, self.button_height),
            self.button_flex_col_topleft,
            "reset",
            self.buttton_text_topleft_offset,
            "discard changes",
        )
        self.exit_button: Button = Button(
            (self.narrow_button_width, self.button_height),
            self.button_flex_col_topleft,
            "exit",
            self.buttton_text_topleft_offset,
            "exit options menu",
        )
        self.button_container_offset: int = 0
        self.button_container_limit: int = 6
        self.button_container_pagination: bool = True
        self.button_container: ButtonContainer = ButtonContainer(
            [
                self.resolution_button,
                self.up_input_button,
                self.down_input_button,
                self.left_input_button,
                self.right_input_button,
                self.enter_input_button,
                self.pause_input_button,
                self.jump_input_button,
                self.attack_input_button,
                self.apply_button,
                self.reset_button,
                self.exit_button,
            ],
            self.button_container_offset,
            self.button_container_limit,
            self.button_container_pagination,
            self.game,
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
        self.resolution_texts: list[str] = [
            "<  320 x 160 >",
            "<  640 x 320 >",
            "<  960 x 480 >",
            "< 1280 x 640 >",
            "< 1600 x 800 >",
            "< 1920 x 960 >",
            "< fullscreen >",
        ]
        self.resolution_texts_len: int = len(self.resolution_texts)
        self.resolution_index: int = (
            self.game.local_settings_dict["resolution_scale"] - 1
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
        # Compute to relative position to button topleft rect.
        self.resolution_text_rect.x -= self.resolution_button.rect.x
        self.resolution_text_rect.y -= self.resolution_button.rect.y
        # Draw it on button.
        self.resolution_button.draw_text_on_surface(
            self.resolution_text,
            self.resolution_text_rect.topleft,
        )

        # Up input text.
        self.up_input_text: str = pg.key.name(
            self.game.local_settings_dict["up"]
        )
        self.up_input_text_rect: pg.Rect = FONT.get_rect(self.up_input_text)
        self.up_input_text_rect.topright = self.up_input_button.rect.topright
        self.up_input_text_rect.x -= 3
        self.up_input_text_rect.y += 2
        # Compute to relative position to button topleft rect.
        self.up_input_text_rect.x -= self.up_input_button.rect.x
        self.up_input_text_rect.y -= self.up_input_button.rect.y
        # Draw it on button.
        self.up_input_button.draw_text_on_surface(
            self.up_input_text,
            self.up_input_text_rect.topleft,
        )

        # Down input text.
        self.down_input_text: str = pg.key.name(
            self.game.local_settings_dict["down"]
        )
        self.down_input_text_rect: pg.Rect = FONT.get_rect(
            self.down_input_text
        )
        self.down_input_text_rect.topright = (
            self.down_input_button.rect.topright
        )
        self.down_input_text_rect.x -= 3
        self.down_input_text_rect.y += 2
        # Compute to relative position to button topleft rect.
        self.down_input_text_rect.x -= self.down_input_button.rect.x
        self.down_input_text_rect.y -= self.down_input_button.rect.y
        # Draw it on button.
        self.down_input_button.draw_text_on_surface(
            self.down_input_text,
            self.down_input_text_rect.topleft,
        )

        # Left input text.
        self.left_input_text: str = pg.key.name(
            self.game.local_settings_dict["left"]
        )
        self.left_input_text_rect: pg.Rect = FONT.get_rect(
            self.left_input_text
        )
        self.left_input_text_rect.topright = (
            self.left_input_button.rect.topright
        )
        self.left_input_text_rect.x -= 3
        self.left_input_text_rect.y += 2
        # Compute to relative position to button topleft rect.
        self.left_input_text_rect.x -= self.left_input_button.rect.x
        self.left_input_text_rect.y -= self.left_input_button.rect.y
        # Draw it on button.
        self.left_input_button.draw_text_on_surface(
            self.left_input_text,
            self.left_input_text_rect.topleft,
        )

        # Right input text.
        self.right_input_text: str = pg.key.name(
            self.game.local_settings_dict["right"]
        )
        self.right_input_text_rect: pg.Rect = FONT.get_rect(
            self.right_input_text
        )
        self.right_input_text_rect.topright = (
            self.right_input_button.rect.topright
        )
        self.right_input_text_rect.x -= 3
        self.right_input_text_rect.y += 2
        # Compute to relative position to button topleft rect.
        self.right_input_text_rect.x -= self.right_input_button.rect.x
        self.right_input_text_rect.y -= self.right_input_button.rect.y
        # Draw it on button.
        self.right_input_button.draw_text_on_surface(
            self.right_input_text,
            self.right_input_text_rect.topleft,
        )

        # Enter input text.
        self.enter_input_text: str = pg.key.name(
            self.game.local_settings_dict["enter"]
        )
        self.enter_input_text_rect: pg.Rect = FONT.get_rect(
            self.enter_input_text
        )
        self.enter_input_text_rect.topright = (
            self.enter_input_button.rect.topright
        )
        self.enter_input_text_rect.x -= 3
        self.enter_input_text_rect.y += 2
        # Compute to relative position to button topleft rect.
        self.enter_input_text_rect.x -= self.enter_input_button.rect.x
        self.enter_input_text_rect.y -= self.enter_input_button.rect.y
        # Draw it on button.
        self.enter_input_button.draw_text_on_surface(
            self.enter_input_text,
            self.enter_input_text_rect.topleft,
        )

        # Pause input text.
        self.pause_input_text: str = pg.key.name(
            self.game.local_settings_dict["pause"]
        )
        self.pause_input_text_rect: pg.Rect = FONT.get_rect(
            self.pause_input_text
        )
        self.pause_input_text_rect.topright = (
            self.pause_input_button.rect.topright
        )
        self.pause_input_text_rect.x -= 3
        self.pause_input_text_rect.y += 2
        # Compute to relative position to button topleft rect.
        self.pause_input_text_rect.x -= self.pause_input_button.rect.x
        self.pause_input_text_rect.y -= self.pause_input_button.rect.y
        # Draw it on button.
        self.pause_input_button.draw_text_on_surface(
            self.pause_input_text,
            self.pause_input_text_rect.topleft,
        )

        # Jump input text.
        self.jump_input_text: str = pg.key.name(
            self.game.local_settings_dict["jump"]
        )
        self.jump_input_text_rect: pg.Rect = FONT.get_rect(
            self.jump_input_text
        )
        self.jump_input_text_rect.topright = (
            self.jump_input_button.rect.topright
        )
        self.jump_input_text_rect.x -= 3
        self.jump_input_text_rect.y += 2
        # Compute to relative position to button topleft rect.
        self.jump_input_text_rect.x -= self.jump_input_button.rect.x
        self.jump_input_text_rect.y -= self.jump_input_button.rect.y
        # Draw it on button.
        self.jump_input_button.draw_text_on_surface(
            self.jump_input_text,
            self.jump_input_text_rect.topleft,
        )

        # Attack input text.
        self.attack_input_text: str = pg.key.name(
            self.game.local_settings_dict["attack"]
        )
        self.attack_input_text_rect: pg.Rect = FONT.get_rect(
            self.attack_input_text
        )
        self.attack_input_text_rect.topright = (
            self.attack_input_button.rect.topright
        )
        self.attack_input_text_rect.x -= 3
        self.attack_input_text_rect.y += 2
        # Compute to relative position to button topleft rect.
        self.attack_input_text_rect.x -= self.attack_input_button.rect.x
        self.attack_input_text_rect.y -= self.attack_input_button.rect.y
        # Draw it on button.
        self.attack_input_button.draw_text_on_surface(
            self.attack_input_text,
            self.attack_input_text_rect.topleft,
        )

        # Decoration lines.
        self.decoration_vertical_start = (160, 18)
        self.decoration_vertical_x: int = 160
        self.decoration_vertical_top: int = 18
        self.decoration_vetical_height: int = 60
        self.decoration_vertical_bottom: int = (
            self.decoration_vertical_top + self.decoration_vetical_height
        )
        self.decoration_horizontal_y: int = self.decoration_vertical_bottom
        self.decoration_horizontal_left: int = 87
        self.decoration_horizontal_right: int = 232

        # Initial state.
        self.state: int = self.initial_state

    def load_settings_and_update_ui(self) -> None:
        """
        Left and right input while resolution button is focused.
        """

        # Try loading to local, if not dump local to disk.
        self.game.load_or_create_settings()

        # Update input texts with local.

        # Resolution input text.
        old_resolution_index = self.resolution_index
        self.set_resolution_index(
            self.game.local_settings_dict["resolution_scale"] - 1
        )
        if self.game.local_settings_dict["resolution_scale"] != (
            old_resolution_index + 1
        ):
            # Update game.local_settings_dict resolution.
            new_value = self.resolution_index + 1
            self.game.set_resolution(new_value)

        # Up input text.
        self.update_input_text(
            self.up_input_button,
            pg.key.name(self.game.local_settings_dict["up"]),
        )

        # Down input text.
        self.update_input_text(
            self.down_input_button,
            pg.key.name(self.game.local_settings_dict["down"]),
        )

        # Left input text.
        self.update_input_text(
            self.left_input_button,
            pg.key.name(self.game.local_settings_dict["left"]),
        )

        # Right input text.
        self.update_input_text(
            self.right_input_button,
            pg.key.name(self.game.local_settings_dict["right"]),
        )

        # Enter input text.
        self.update_input_text(
            self.enter_input_button,
            pg.key.name(self.game.local_settings_dict["enter"]),
        )

        # Pause input text.
        self.update_input_text(
            self.pause_input_button,
            pg.key.name(self.game.local_settings_dict["pause"]),
        )

        # Jump input text.
        self.update_input_text(
            self.jump_input_button,
            pg.key.name(self.game.local_settings_dict["jump"]),
        )

        # Attack input text.
        self.update_input_text(
            self.attack_input_button,
            pg.key.name(self.game.local_settings_dict["attack"]),
        )

    def update_input_text(self, button: Button, text: str) -> None:
        """
        This combines all input button text setter.
        Handle each button input text.
        - input_text
        - input_text_rect
        """

        if button == self.up_input_button:
            self.up_input_text = text
            self.up_input_text_rect = FONT.get_rect(self.up_input_text)
            self.up_input_text_rect.topright = (
                self.up_input_button.rect.topright
            )
            self.up_input_text_rect.x -= 3
            self.up_input_text_rect.y += 2
            # Compute to relative position to button topleft rect.
            self.up_input_text_rect.x -= self.up_input_button.rect.x
            self.up_input_text_rect.y -= self.up_input_button.rect.y
            # Draw it on button.
            self.up_input_button.draw_text_on_surface(
                self.up_input_text,
                self.up_input_text_rect.topleft,
            )

        elif button == self.down_input_button:
            self.down_input_text = text
            self.down_input_text_rect = FONT.get_rect(self.down_input_text)
            self.down_input_text_rect.topright = (
                self.down_input_button.rect.topright
            )
            self.down_input_text_rect.x -= 3
            self.down_input_text_rect.y += 2
            # Compute to relative position to button topleft rect.
            self.down_input_text_rect.x -= self.down_input_button.rect.x
            self.down_input_text_rect.y -= self.down_input_button.rect.y
            # Draw it on button.
            self.down_input_button.draw_text_on_surface(
                self.down_input_text,
                self.down_input_text_rect.topleft,
            )

        elif button == self.left_input_button:
            self.left_input_text = text
            self.left_input_text_rect = FONT.get_rect(self.left_input_text)
            self.left_input_text_rect.topright = (
                self.left_input_button.rect.topright
            )
            self.left_input_text_rect.x -= 3
            self.left_input_text_rect.y += 2
            # Compute to relative position to button topleft rect.
            self.left_input_text_rect.x -= self.left_input_button.rect.x
            self.left_input_text_rect.y -= self.left_input_button.rect.y
            # Draw it on button.
            self.left_input_button.draw_text_on_surface(
                self.left_input_text,
                self.left_input_text_rect.topleft,
            )

        elif button == self.right_input_button:
            self.right_input_text = text
            self.right_input_text_rect = FONT.get_rect(self.right_input_text)
            self.right_input_text_rect.topright = (
                self.right_input_button.rect.topright
            )
            self.right_input_text_rect.x -= 3
            self.right_input_text_rect.y += 2
            # Compute to relative position to button topleft rect.
            self.right_input_text_rect.x -= self.right_input_button.rect.x
            self.right_input_text_rect.y -= self.right_input_button.rect.y
            # Draw it on button.
            self.right_input_button.draw_text_on_surface(
                self.right_input_text,
                self.right_input_text_rect.topleft,
            )

        elif button == self.enter_input_button:
            self.enter_input_text = text
            self.enter_input_text_rect = FONT.get_rect(self.enter_input_text)
            self.enter_input_text_rect.topright = (
                self.enter_input_button.rect.topright
            )
            self.enter_input_text_rect.x -= 3
            self.enter_input_text_rect.y += 2
            # Compute to relative position to button topleft rect.
            self.enter_input_text_rect.x -= self.enter_input_button.rect.x
            self.enter_input_text_rect.y -= self.enter_input_button.rect.y
            # Draw it on button.
            self.enter_input_button.draw_text_on_surface(
                self.enter_input_text,
                self.enter_input_text_rect.topleft,
            )

        elif button == self.pause_input_button:
            self.pause_input_text = text
            self.pause_input_text_rect = FONT.get_rect(self.pause_input_text)
            self.pause_input_text_rect.topright = (
                self.pause_input_button.rect.topright
            )
            self.pause_input_text_rect.x -= 3
            self.pause_input_text_rect.y += 2
            # Compute to relative position to button topleft rect.
            self.pause_input_text_rect.x -= self.pause_input_button.rect.x
            self.pause_input_text_rect.y -= self.pause_input_button.rect.y
            # Draw it on button.
            self.pause_input_button.draw_text_on_surface(
                self.pause_input_text,
                self.pause_input_text_rect.topleft,
            )

        elif button == self.jump_input_button:
            self.jump_input_text = text
            self.jump_input_text_rect = FONT.get_rect(self.jump_input_text)
            self.jump_input_text_rect.topright = (
                self.jump_input_button.rect.topright
            )
            self.jump_input_text_rect.x -= 3
            self.jump_input_text_rect.y += 2
            # Compute to relative position to button topleft rect.
            self.jump_input_text_rect.x -= self.jump_input_button.rect.x
            self.jump_input_text_rect.y -= self.jump_input_button.rect.y
            # Draw it on button.
            self.jump_input_button.draw_text_on_surface(
                self.jump_input_text,
                self.jump_input_text_rect.topleft,
            )

        elif button == self.attack_input_button:
            self.attack_input_text = text
            self.attack_input_text_rect = FONT.get_rect(self.attack_input_text)
            self.attack_input_text_rect.topright = (
                self.attack_input_button.rect.topright
            )
            self.attack_input_text_rect.x -= 3
            self.attack_input_text_rect.y += 2
            # Compute to relative position to button topleft rect.
            self.attack_input_text_rect.x -= self.attack_input_button.rect.x
            self.attack_input_text_rect.y -= self.attack_input_button.rect.y
            # Draw it on button.
            self.attack_input_button.draw_text_on_surface(
                self.attack_input_text,
                self.attack_input_text_rect.topleft,
            )

    def set_resolution_index(self, value: int) -> None:
        """
        Left and right input while resolution button is focused:
        - resolution_index (modulo wrap)
        - resolution_text
        - resolution_text_rect
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
        # Compute to relative position to button topleft rect.
        self.resolution_text_rect.x -= self.resolution_button.rect.x
        self.resolution_text_rect.y -= self.resolution_button.rect.y
        # Draw it on button.
        self.resolution_button.draw_text_on_surface(
            self.resolution_text,
            self.resolution_text_rect.topleft,
        )

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

        # Apply button selected?
        if self.apply_button == self.selected_button:
            self.game.save_settings()

        # Reset button selected?
        elif self.reset_button == self.selected_button:
            self.load_settings_and_update_ui()

        # Exit button selected?
        elif self.exit_button == self.selected_button:
            # Exit state to GOING_TO_INVISIBLE.
            self.load_settings_and_update_ui()
            self.set_state(self.GOING_TO_INVISIBLE)

        # Any input button selected?
        elif self.selected_button in [
            self.up_input_button,
            self.down_input_button,
            self.left_input_button,
            self.right_input_button,
            self.enter_input_button,
            self.pause_input_button,
            self.jump_input_button,
            self.attack_input_button,
        ]:
            # Exit state to REBIND.
            self.set_state(self.REBIND)

    def draw(self) -> None:
        """
        Draw:
        - clear curtain.
        - draw title.
        - button container.
        - resolution texts.
        - decorations.
        - draw curtain on native.
        """

        # Clear curtain.
        self.curtain.surf.fill(self.curtain_clear_color)

        # Draw title.
        FONT.render_to(
            self.curtain.surf,
            self.title_rect,
            self.title_text,
            self.font_color,
        )

        # Button container.
        self.button_container.draw(self.curtain.surf)

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
        """
        Update:
        - state machine.
        """

        # REMOVE IN BUILD
        # Draw my state name.
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
                # Get left right direction.
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
                # Update resolution index.
                if is_pressed_left_or_right:
                    if self.resolution_index != new_value:
                        self.set_resolution_index(new_value)
                        if self.game.local_settings_dict[
                            "resolution_scale"
                        ] != (self.resolution_index + 1):
                            # Update game.local_settings_dict resolution.
                            new_value = self.resolution_index + 1
                            self.game.set_resolution(new_value)

        # REBIND state.
        elif self.state == self.REBIND:
            # Pressed any key?
            if self.game.is_any_key_just_pressed:
                # Find if pressed key is used already?
                for key_name, key_int in self.game.local_settings_dict.items():
                    # Update text to alert message. Return.
                    if self.game.this_frame_event.key == key_int:
                        self.update_input_text(
                            self.focused_button, f"used by '{key_name}'"
                        )
                        return

                # Rebind. Update game.local_settings_dict input.
                if self.focused_button == self.up_input_button:
                    self.game.local_settings_dict[
                        "up"
                    ] = self.game.this_frame_event.key
                elif self.focused_button == self.down_input_button:
                    self.game.local_settings_dict[
                        "down"
                    ] = self.game.this_frame_event.key
                elif self.focused_button == self.left_input_button:
                    self.game.local_settings_dict[
                        "left"
                    ] = self.game.this_frame_event.key
                elif self.focused_button == self.right_input_button:
                    self.game.local_settings_dict[
                        "right"
                    ] = self.game.this_frame_event.key
                elif self.focused_button == self.enter_input_button:
                    self.game.local_settings_dict[
                        "enter"
                    ] = self.game.this_frame_event.key
                elif self.focused_button == self.pause_input_button:
                    self.game.local_settings_dict[
                        "pause"
                    ] = self.game.this_frame_event.key
                elif self.focused_button == self.jump_input_button:
                    self.game.local_settings_dict[
                        "jump"
                    ] = self.game.this_frame_event.key
                elif self.focused_button == self.attack_input_button:
                    self.game.local_settings_dict[
                        "attack"
                    ] = self.game.this_frame_event.key

                # Update input text.
                self.update_input_text(
                    self.focused_button,
                    pg.key.name(self.game.this_frame_event.key),
                )

                # Exit to normal state after rebind ok.
                self.set_state(self.REACHED_OPAQUE)

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
            # To REBIND
            elif self.state == self.REBIND:
                # Update input text to "press any key".
                self.update_input_text(self.focused_button, "press any key")

        # From REBIND
        elif old_state == self.REBIND:
            # To REACHED_OPAQUE
            if self.state == self.REACHED_OPAQUE:
                # Make the press any button stop fade in out.
                pass

        # From GOING_TO_INVISIBLE
        elif old_state == self.GOING_TO_INVISIBLE:
            # To REACHED_INVISIBLE
            if self.state == self.REACHED_INVISIBLE:
                pass

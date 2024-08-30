from enum import auto
from enum import Enum
from typing import TYPE_CHECKING

from constants import FONT
from constants import NATIVE_HEIGHT
from constants import NATIVE_RECT
from constants import NATIVE_SURF
from constants import NATIVE_WIDTH
from constants import pg
from constants import SETTINGS_FILE_NAME
from nodes.button import Button
from nodes.button_container import ButtonContainer
from nodes.curtain import Curtain
from nodes.state_machine import StateMachine
from nodes.timer import Timer
from typeguard import typechecked


if TYPE_CHECKING:
    from nodes.game import Game


@typechecked
class OptionsMenu:
    class State(Enum):
        JUST_ENTERED_SCENE = auto()
        CLOSING_SCENE_CURTAIN = auto()
        CLOSED_SCENE_CURTAIN = auto()
        OPENING_SCENE_CURTAIN = auto()
        OPENED_SCENE_CURTAIN = auto()
        REBIND = auto()

    def __init__(self, game: "Game"):
        # Initialize game
        self.game = game
        self.game_debug_draw = self.game.debug_draw
        self.game_event_handler = self.game.event_handler

        # Colors
        self.curtain_clear_color: str = "#000000"
        self.font_color: str = "#ffffff"

        # Curtain setup
        self._setup_curtain()
        self._setup_timers()
        self._setup_texts()
        self._setup_buttons()
        self._setup_decoration_lines()

        # State machines setup
        self._setup_state_machine_update()
        self._setup_state_machine_draw()

    # Setups
    def _setup_curtain(self) -> None:
        """
        Setup curtain with event listeners. Curtain here is my surf.
        """

        self.curtain: Curtain = Curtain(
            duration=1000.0,
            start_state=Curtain.INVISIBLE,
            max_alpha=255,
            surf_size_tuple=(NATIVE_WIDTH, NATIVE_HEIGHT),
            is_invisible=False,
            color=self.curtain_clear_color,
        )
        self.curtain.add_event_listener(self._on_curtain_invisible, Curtain.INVISIBLE_END)
        self.curtain.add_event_listener(self._on_curtain_opaque, Curtain.OPAQUE_END)

    def _setup_timers(self) -> None:
        """
        Setup timers with event listeners.
        """

        self.entry_delay_timer: Timer = Timer(0.0)
        self.entry_delay_timer.add_event_listener(self._on_entry_delay_timer_end, Timer.END)

        self.exit_delay_timer: Timer = Timer(0.0)
        self.exit_delay_timer.add_event_listener(self._on_exit_delay_timer_end, Timer.END)

    def _setup_texts(self) -> None:
        """
        Setup title text.
        """

        self.title_text: str = "options"
        self.title_rect: pg.Rect = FONT.get_rect(self.title_text)
        self.title_rect.center = NATIVE_RECT.center
        self.title_rect.y = 14

    def _setup_buttons(self) -> None:
        """
        Setup button container.
        """

        self.button_height: int = 9
        self.wide_button_width: int = 146
        self.narrow_button_width: int = 73
        self.button_flex_col_topleft: tuple[int, int] = (88, 22)
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
        self.button_container: ButtonContainer = ButtonContainer(
            buttons=[
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
            offset=0,
            limit=6,
            is_pagination=True,
            game_event_handler=self.game.event_handler,
            game_sound_manager=self.game.sound_manager,
        )
        self.button_container.add_event_listener(self._on_button_selected, ButtonContainer.BUTTON_SELECTED)
        self.button_container.add_event_listener(self._on_button_index_changed, ButtonContainer.INDEX_CHANGED)

        # Keep track of who is selected and focused
        self.selected_button: Button = self.resolution_button
        self.focused_button: Button = self.resolution_button

        # Extra texts offset
        self.extra_text_x_offset = 3
        self.extra_text_y_offset = 2

        # Resolution text
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
        local_settings_dict_resolution_index = self.game.get_one_local_settings_dict_value("resolution_index")
        self.resolution_text: str = self.resolution_texts[local_settings_dict_resolution_index]
        self.resolution_text_rect: pg.Rect = FONT.get_rect(self.resolution_text)
        self.resolution_text_rect.topright = self.resolution_button.rect.topright
        self.resolution_text_rect.x -= self.extra_text_x_offset
        self.resolution_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.resolution_text_rect.x -= self.resolution_button.rect.x
        self.resolution_text_rect.y -= self.resolution_button.rect.y
        # Draw it on button
        self.resolution_button.draw_extra_text_on_surf(
            self.resolution_text,
            self.resolution_text_rect.topleft,
        )

        # Up input text
        local_settings_dict_up = self.game.get_one_local_settings_dict_value("up")
        self.up_input_text: str = pg.key.name(local_settings_dict_up)
        self.up_input_text_rect: pg.Rect = FONT.get_rect(self.up_input_text)
        self.up_input_text_rect.topright = self.up_input_button.rect.topright
        self.up_input_text_rect.x -= self.extra_text_x_offset
        self.up_input_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.up_input_text_rect.x -= self.up_input_button.rect.x
        self.up_input_text_rect.y -= self.up_input_button.rect.y
        # Draw it on button
        self.up_input_button.draw_extra_text_on_surf(
            self.up_input_text,
            self.up_input_text_rect.topleft,
        )

        # Down input text
        local_settings_dict_down = self.game.get_one_local_settings_dict_value("down")
        self.down_input_text: str = pg.key.name(local_settings_dict_down)
        self.down_input_text_rect: pg.Rect = FONT.get_rect(self.down_input_text)
        self.down_input_text_rect.topright = self.down_input_button.rect.topright
        self.down_input_text_rect.x -= self.extra_text_x_offset
        self.down_input_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.down_input_text_rect.x -= self.down_input_button.rect.x
        self.down_input_text_rect.y -= self.down_input_button.rect.y
        # Draw it on button
        self.down_input_button.draw_extra_text_on_surf(
            self.down_input_text,
            self.down_input_text_rect.topleft,
        )

        # Left input text
        local_settings_dict_left = self.game.get_one_local_settings_dict_value("left")
        self.left_input_text: str = pg.key.name(local_settings_dict_left)
        self.left_input_text_rect: pg.Rect = FONT.get_rect(self.left_input_text)
        self.left_input_text_rect.topright = self.left_input_button.rect.topright
        self.left_input_text_rect.x -= self.extra_text_x_offset
        self.left_input_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.left_input_text_rect.x -= self.left_input_button.rect.x
        self.left_input_text_rect.y -= self.left_input_button.rect.y
        # Draw it on button
        self.left_input_button.draw_extra_text_on_surf(
            self.left_input_text,
            self.left_input_text_rect.topleft,
        )

        # Right input text
        local_settings_dict_right = self.game.get_one_local_settings_dict_value("right")
        self.right_input_text: str = pg.key.name(local_settings_dict_right)
        self.right_input_text_rect: pg.Rect = FONT.get_rect(self.right_input_text)
        self.right_input_text_rect.topright = self.right_input_button.rect.topright
        self.right_input_text_rect.x -= self.extra_text_x_offset
        self.right_input_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.right_input_text_rect.x -= self.right_input_button.rect.x
        self.right_input_text_rect.y -= self.right_input_button.rect.y
        # Draw it on button
        self.right_input_button.draw_extra_text_on_surf(
            self.right_input_text,
            self.right_input_text_rect.topleft,
        )

        # Enter input text
        local_settings_dict_enter = self.game.get_one_local_settings_dict_value("enter")
        self.enter_input_text: str = pg.key.name(local_settings_dict_enter)
        self.enter_input_text_rect: pg.Rect = FONT.get_rect(self.enter_input_text)
        self.enter_input_text_rect.topright = self.enter_input_button.rect.topright
        self.enter_input_text_rect.x -= self.extra_text_x_offset
        self.enter_input_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.enter_input_text_rect.x -= self.enter_input_button.rect.x
        self.enter_input_text_rect.y -= self.enter_input_button.rect.y
        # Draw it on button
        self.enter_input_button.draw_extra_text_on_surf(
            self.enter_input_text,
            self.enter_input_text_rect.topleft,
        )

        # Pause input text
        local_settings_dict_pause = self.game.get_one_local_settings_dict_value("pause")
        self.pause_input_text: str = pg.key.name(local_settings_dict_pause)
        self.pause_input_text_rect: pg.Rect = FONT.get_rect(self.pause_input_text)
        self.pause_input_text_rect.topright = self.pause_input_button.rect.topright
        self.pause_input_text_rect.x -= self.extra_text_x_offset
        self.pause_input_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.pause_input_text_rect.x -= self.pause_input_button.rect.x
        self.pause_input_text_rect.y -= self.pause_input_button.rect.y
        # Draw it on button
        self.pause_input_button.draw_extra_text_on_surf(
            self.pause_input_text,
            self.pause_input_text_rect.topleft,
        )

        # Jump input text
        local_settings_dict_jump = self.game.get_one_local_settings_dict_value("jump")
        self.jump_input_text: str = pg.key.name(local_settings_dict_jump)
        self.jump_input_text_rect: pg.Rect = FONT.get_rect(self.jump_input_text)
        self.jump_input_text_rect.topright = self.jump_input_button.rect.topright
        self.jump_input_text_rect.x -= self.extra_text_x_offset
        self.jump_input_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.jump_input_text_rect.x -= self.jump_input_button.rect.x
        self.jump_input_text_rect.y -= self.jump_input_button.rect.y
        # Draw it on button
        self.jump_input_button.draw_extra_text_on_surf(
            self.jump_input_text,
            self.jump_input_text_rect.topleft,
        )

        # Attack input text
        local_settings_dict_attack = self.game.get_one_local_settings_dict_value("attack")
        self.attack_input_text: str = pg.key.name(local_settings_dict_attack)
        self.attack_input_text_rect: pg.Rect = FONT.get_rect(self.attack_input_text)
        self.attack_input_text_rect.topright = self.attack_input_button.rect.topright
        self.attack_input_text_rect.x -= self.extra_text_x_offset
        self.attack_input_text_rect.y += self.extra_text_y_offset
        # Compute to relative position to button topleft rect
        self.attack_input_text_rect.x -= self.attack_input_button.rect.x
        self.attack_input_text_rect.y -= self.attack_input_button.rect.y
        # Draw it on button
        self.attack_input_button.draw_extra_text_on_surf(
            self.attack_input_text,
            self.attack_input_text_rect.topleft,
        )

    def _setup_decoration_lines(self) -> None:
        """
        Setup decoration lines.
        """

        # Metadata constant
        self.decoration_line_width: int = 1
        self.decoration_line_color: str = "#0193bc"
        self.decoration_vertical_start = (NATIVE_RECT.center[0], self.button_flex_col_topleft[1])
        self.decoration_vertical_x: int = self.decoration_vertical_start[0]
        self.decoration_vertical_top: int = self.decoration_vertical_start[1]
        self.decoration_vetical_height: int = self.button_container.button_height_with_margin * self.button_container.limit
        self.decoration_vertical_bottom: int = self.decoration_vertical_top + self.decoration_vetical_height
        self.decoration_horizontal_y: int = self.decoration_vertical_bottom
        self.decoration_horizontal_left: int = self.button_flex_col_topleft[0]
        self.decoration_horizontal_right: int = self.button_flex_col_topleft[0] + self.wide_button_width
        # Horizontal surf init
        self.decoration_line_surf_horizontal: pg.Surface = pg.Surface(
            (self.decoration_horizontal_right - self.decoration_horizontal_left, self.decoration_line_width)
        )
        self.decoration_line_surf_horizontal.fill(self.decoration_line_color)
        # Vertical surf init
        self.decoration_line_surf_vertical: pg.Surface = pg.Surface(
            (self.decoration_line_width, self.decoration_vertical_bottom - self.decoration_vertical_top)
        )
        self.decoration_line_surf_vertical.fill(self.decoration_line_color)

    def _setup_state_machine_update(self) -> None:
        """
        Create state machine for update.
        """

        self.state_machine_update = StateMachine(
            initial_state=OptionsMenu.State.JUST_ENTERED_SCENE,
            state_handlers={
                OptionsMenu.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE,
                OptionsMenu.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN,
                OptionsMenu.State.CLOSED_SCENE_CURTAIN: self._CLOSED_SCENE_CURTAIN,
                OptionsMenu.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN,
                OptionsMenu.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN,
                OptionsMenu.State.REBIND: self._REBIND,
            },
            transition_actions={
                (
                    OptionsMenu.State.JUST_ENTERED_SCENE,
                    OptionsMenu.State.CLOSING_SCENE_CURTAIN,
                ): self._JUST_ENTERED_SCENE_to_CLOSING_SCENE_CURTAIN,
                (
                    OptionsMenu.State.CLOSING_SCENE_CURTAIN,
                    OptionsMenu.State.CLOSED_SCENE_CURTAIN,
                ): self._CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN,
                (
                    OptionsMenu.State.CLOSED_SCENE_CURTAIN,
                    OptionsMenu.State.OPENING_SCENE_CURTAIN,
                ): self._CLOSED_SCENE_CURTAIN_to_OPENING_SCENE_CURTAIN,
                (
                    OptionsMenu.State.CLOSED_SCENE_CURTAIN,
                    OptionsMenu.State.REBIND,
                ): self._CLOSED_SCENE_CURTAIN_to_REBIND,
                (
                    OptionsMenu.State.REBIND,
                    OptionsMenu.State.CLOSED_SCENE_CURTAIN,
                ): self._REBIND_to_CLOSED_SCENE_CURTAIN,
                (
                    OptionsMenu.State.OPENING_SCENE_CURTAIN,
                    OptionsMenu.State.OPENED_SCENE_CURTAIN,
                ): self._OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN,
            },
        )

    def _setup_state_machine_draw(self) -> None:
        """
        Create state machine for draw.
        """

        self.state_machine_draw = StateMachine(
            initial_state=OptionsMenu.State.JUST_ENTERED_SCENE,
            state_handlers={
                OptionsMenu.State.JUST_ENTERED_SCENE: self._OPENED_CURTAIN_DRAW,
                OptionsMenu.State.CLOSING_SCENE_CURTAIN: self._FADING_CURTAIN_DRAW,
                OptionsMenu.State.CLOSED_SCENE_CURTAIN: self._CLOSED_SCENE_CURTAIN_DRAW,
                OptionsMenu.State.OPENING_SCENE_CURTAIN: self._FADING_CURTAIN_DRAW,
                OptionsMenu.State.OPENED_SCENE_CURTAIN: self._OPENED_CURTAIN_DRAW,
                OptionsMenu.State.REBIND: self._CLOSED_SCENE_CURTAIN_DRAW,
            },
            transition_actions={},
        )

    # State draw logics
    def _FADING_CURTAIN_DRAW(self, _dt: int) -> None:
        # Clear curtain
        self.curtain.surf.fill(self.curtain_clear_color)

        # Draw title
        FONT.render_to(
            self.curtain.surf,
            self.title_rect,
            self.title_text,
            self.font_color,
        )

        # Button container
        self.button_container.draw(self.curtain.surf)

        # Decorations
        self.curtain.surf.blit(
            self.decoration_line_surf_horizontal, (self.decoration_horizontal_left, self.decoration_horizontal_y)
        )
        self.curtain.surf.blit(self.decoration_line_surf_vertical, (self.decoration_vertical_x, self.decoration_vertical_top))

        # Draw curtain on native
        self.curtain.draw(NATIVE_SURF, 0)

    def _CLOSED_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        # Clear curtain
        self.curtain.surf.fill(self.curtain_clear_color)

        # Draw title
        FONT.render_to(
            self.curtain.surf,
            self.title_rect,
            self.title_text,
            self.font_color,
        )

        # Button container
        self.button_container.draw(self.curtain.surf)

        # Decorations
        self.curtain.surf.blit(
            self.decoration_line_surf_horizontal, (self.decoration_horizontal_left, self.decoration_horizontal_y)
        )
        self.curtain.surf.blit(self.decoration_line_surf_vertical, (self.decoration_vertical_x, self.decoration_vertical_top))

        # Draw curtain on native
        self.curtain.draw(NATIVE_SURF, 0)

    def _OPENED_CURTAIN_DRAW(self, _dt: int) -> None:
        pass

    # State update logics
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        self.entry_delay_timer.update(dt)

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _CLOSED_SCENE_CURTAIN(self, dt: int) -> None:
        self.button_container.update(dt)

        # Focusing on resolution button?
        if self.resolution_button == self.focused_button:
            # Get left right dir
            dir: int = self.game_event_handler.is_right_just_pressed - self.game_event_handler.is_left_just_pressed
            # Return if dir is zero
            if dir == 0:
                return
            # Get new resolution index value with dir
            local_settings_dict_resolution_index = self.game.get_one_local_settings_dict_value("resolution_index")
            new_resolution_index_value = local_settings_dict_resolution_index + dir
            # Module wrap it
            new_resolution_index_value = new_resolution_index_value % self.resolution_texts_len
            # Update game real window, window prop and local settings with new resolution value
            self.game.set_resolution_index(new_resolution_index_value)
            # Update my front end ui with new game resolution
            local_settings_dict_resolution_index = self.game.get_one_local_settings_dict_value("resolution_index")
            self._update_input_text_front_end_ui(
                self.resolution_button,
                self.resolution_texts[local_settings_dict_resolution_index],
            )

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)
        self.button_container.update(dt)

    def _OPENED_SCENE_CURTAIN(self, dt: int) -> None:
        self.exit_delay_timer.update(dt)

    def _REBIND(self, dt: int) -> None:
        # Pressed any key?
        if self.game_event_handler.is_any_key_just_pressed:
            # The key pressed this frame is not none?
            if self.game_event_handler.this_frame_event is not None:
                # Loop over each key val in game local settings dict
                game_local_settings_dict = self.game.get_local_settings_dict()
                for key_name, key_int in game_local_settings_dict.items():
                    # This frame key pressed code exists in game local dict?
                    if self.game_event_handler.this_frame_event.key == key_int:
                        # Update alert and return
                        self._update_input_text_front_end_ui(self.focused_button, f"used by '{key_name}'")
                        return

                # Rebind
                # The only way to get here is to press Button are named like "${key_name} input"
                key_name = self.focused_button.text.split()[0]

                # Update game local settings input
                self.game.set_one_local_settings_dict_value(key_name, self.game_event_handler.this_frame_event.key)

                # Update input text front-end ui
                self._update_input_text_front_end_ui(
                    self.focused_button,
                    pg.key.name(self.game_event_handler.this_frame_event.key),
                )

                # Exit to normal state after rebind ok
                self.state_machine_draw.change_state(OptionsMenu.State.CLOSED_SCENE_CURTAIN)
                self.state_machine_update.change_state(OptionsMenu.State.CLOSED_SCENE_CURTAIN)

    # State transitions
    def _JUST_ENTERED_SCENE_to_CLOSING_SCENE_CURTAIN(self) -> None:
        self.curtain.go_to_opaque()

    def _CLOSING_SCENE_CURTAIN_to_CLOSED_SCENE_CURTAIN(self) -> None:
        self.button_container.set_is_input_allowed(True)

    def _CLOSED_SCENE_CURTAIN_to_OPENING_SCENE_CURTAIN(self) -> None:
        self.button_container.set_is_input_allowed(False)
        self.curtain.go_to_invisible()

    def _CLOSED_SCENE_CURTAIN_to_REBIND(self) -> None:
        # This can only happen when you press button input
        # Update input text to "press any key"
        self._update_input_text_front_end_ui(self.focused_button, "press any key")

    def _REBIND_to_CLOSED_SCENE_CURTAIN(self) -> None:
        pass

    def _OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN(self) -> None:
        pass

    # Callbacks
    def _on_entry_delay_timer_end(self) -> None:
        """
        Delay ends, starts going to opaque.
        """

        self.state_machine_update.change_state(OptionsMenu.State.CLOSING_SCENE_CURTAIN)
        self.state_machine_draw.change_state(OptionsMenu.State.CLOSING_SCENE_CURTAIN)

    def _on_exit_delay_timer_end(self) -> None:
        """
        Exit options here.
        Set my state back to JUST_ENTERED_SCENE for next entry here.
        No need for setter, bypass setter.
        """

        self.exit_delay_timer.reset()
        self.entry_delay_timer.reset()
        self.state_machine_update.change_state(OptionsMenu.State.JUST_ENTERED_SCENE)
        self.state_machine_draw.change_state(OptionsMenu.State.JUST_ENTERED_SCENE)
        self.game.set_is_options_menu_active(False)

    def _on_curtain_invisible(self) -> None:
        """
        Set OPENED_SCENE_CURTAIN state.
        """

        self.state_machine_update.change_state(OptionsMenu.State.OPENED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(OptionsMenu.State.OPENED_SCENE_CURTAIN)

    def _on_curtain_opaque(self) -> None:
        """
        Set CLOSED_SCENE_CURTAIN state.
        """

        self.state_machine_update.change_state(OptionsMenu.State.CLOSED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(OptionsMenu.State.CLOSED_SCENE_CURTAIN)

    def _on_button_index_changed(self, focused_button: Button) -> None:
        """
        When index changes, update focused_button.
        """
        self.focused_button = focused_button

    def _on_button_selected(self, selected_button: Button) -> None:
        """
        Remember selected.
        Need to wait for curtain to go to opaque.
        Then use remembered button to go somewhere.
        """

        self.selected_button = selected_button

        # Apply button selected?
        if self.apply_button == self.selected_button:
            # Overwrite disk with game local settings
            self.game.PATCH_file_to_disk_dynamic_path(
                self.game.jsons_user_pahts_dict[SETTINGS_FILE_NAME],
                self.game.get_local_settings_dict(),
            )

        # Reset button selected?
        elif self.reset_button == self.selected_button:
            # Overwrite game local settings with disk
            self._load_settings_and_update_ui()

        # Exit button selected?
        elif self.exit_button == self.selected_button:
            # Overwrite game local settings with disk
            self._load_settings_and_update_ui()
            self.state_machine_update.change_state(OptionsMenu.State.OPENING_SCENE_CURTAIN)
            self.state_machine_draw.change_state(OptionsMenu.State.OPENING_SCENE_CURTAIN)

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
            # Exit state to REBIND
            self.state_machine_update.change_state(OptionsMenu.State.REBIND)
            self.state_machine_draw.change_state(OptionsMenu.State.REBIND)

    # Draw
    def draw(self) -> None:
        self.state_machine_draw.handle(0)

    # Update
    def update(self, dt: int) -> None:
        # REMOVE IN BUILD
        self.game_debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 0,
                "text": (f"options menu state " f"state: {self.state_machine_update.state.name}"),
            }
        )

        self.state_machine_update.handle(dt)

    # Helpers
    def _load_settings_and_update_ui(self) -> None:
        """
        Overwrite local with disk.
        Update front-end ui.
        """

        # Remember the old, no need to update window and local settings if the same
        old_local_settings_dict_resolution_index = self.game.get_one_local_settings_dict_value("resolution_index")

        # Read disk and update game local settings
        self.game.GET_or_POST_settings_json_from_disk()

        # Get resolution index
        local_settings_dict_resolution_index = self.game.get_one_local_settings_dict_value("resolution_index")

        # Old and new was different? Then resolution was updated by player in settings
        if old_local_settings_dict_resolution_index != local_settings_dict_resolution_index:
            # Update the window and local settings dict
            self.game.set_resolution_index(local_settings_dict_resolution_index)

        # Update ui text
        button_settings = {
            self.resolution_button: self.resolution_texts[local_settings_dict_resolution_index],
            self.up_input_button: pg.key.name(self.game.get_one_local_settings_dict_value("up")),
            self.down_input_button: pg.key.name(self.game.get_one_local_settings_dict_value("down")),
            self.left_input_button: pg.key.name(self.game.get_one_local_settings_dict_value("left")),
            self.right_input_button: pg.key.name(self.game.get_one_local_settings_dict_value("right")),
            self.enter_input_button: pg.key.name(self.game.get_one_local_settings_dict_value("enter")),
            self.pause_input_button: pg.key.name(self.game.get_one_local_settings_dict_value("pause")),
            self.jump_input_button: pg.key.name(self.game.get_one_local_settings_dict_value("jump")),
            self.attack_input_button: pg.key.name(self.game.get_one_local_settings_dict_value("attack")),
        }
        for button_instance, button_text in button_settings.items():
            self._update_input_text_front_end_ui(
                button_instance,
                button_text,
            )

    def _update_input_text_front_end_ui(self, button: Button, text: str) -> None:
        """
        This combines all input button text setter.
        Handle each button input text.
        - input_text
        - input_text_rect
        """

        # Map buttons to their props
        button_map = {
            self.up_input_button: ("up_input_text", "up_input_text_rect"),
            self.down_input_button: ("down_input_text", "down_input_text_rect"),
            self.left_input_button: ("left_input_text", "left_input_text_rect"),
            self.right_input_button: ("right_input_text", "right_input_text_rect"),
            self.enter_input_button: ("enter_input_text", "enter_input_text_rect"),
            self.pause_input_button: ("pause_input_text", "pause_input_text_rect"),
            self.jump_input_button: ("jump_input_text", "jump_input_text_rect"),
            self.attack_input_button: ("attack_input_text", "attack_input_text_rect"),
            self.resolution_button: ("resolution_text", "resolution_text_rect"),
        }

        # Return if given button is not in map
        if button not in button_map:
            return

        # Get the associated attributes dynamically
        text_attr, rect_attr = button_map[button]

        # Set the text
        setattr(self, text_attr, text)

        # Update the rect
        rect = FONT.get_rect(text)
        rect.topright = button.rect.topright
        rect.x -= self.extra_text_x_offset
        rect.y += self.extra_text_y_offset
        rect.x -= button.rect.x  # Relative to button
        rect.y -= button.rect.y  # Relative to button
        setattr(self, rect_attr, rect)

        # Draw the text on the button
        button.draw_extra_text_on_surf(getattr(self, text_attr), getattr(self, rect_attr).topleft)

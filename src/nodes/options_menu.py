from enum import auto
from enum import Enum
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

        # State machines init
        self.state_machine_update = self._create_state_machine_update()
        self.state_machine_draw = self._create_state_machine_draw()

    # Setups
    def _setup_curtain(self) -> None:
        """Setup curtain with event listeners. Curtain here is my surf."""
        self.curtain: Curtain = Curtain(
            duration=1000.0,
            start_state=Curtain.INVISIBLE,
            max_alpha=255,
            surf_size_tuple=(NATIVE_WIDTH, NATIVE_HEIGHT),
            is_invisible=False,
            color=self.curtain_clear_color,
        )
        self.curtain.add_event_listener(self.on_curtain_invisible, Curtain.INVISIBLE_END)
        self.curtain.add_event_listener(self.on_curtain_opaque, Curtain.OPAQUE_END)

    def _setup_timers(self) -> None:
        """Setup timers with event listeners."""
        self.entry_delay_timer: Timer = Timer(0.0)
        self.entry_delay_timer.add_event_listener(self.on_entry_delay_timer_end, Timer.END)

        self.exit_delay_timer: Timer = Timer(0.0)
        self.exit_delay_timer.add_event_listener(self.on_exit_delay_timer_end, Timer.END)

    def _setup_texts(self) -> None:
        """Setup title text."""
        self.title_text: str = "options"
        self.title_rect: pg.Rect = FONT.get_rect(self.title_text)
        self.title_rect.center = NATIVE_RECT.center
        self.title_rect.y = 14

    def _setup_buttons(self) -> None:
        """Setup button container."""
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
        self.button_container.add_event_listener(self.on_button_selected, ButtonContainer.BUTTON_SELECTED)
        self.button_container.add_event_listener(self.on_button_index_changed, ButtonContainer.INDEX_CHANGED)

        # Keep track of who is selected and focused
        self.selected_button: Button = self.resolution_button
        self.focused_button: Button = self.resolution_button

        # Resolution texts
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
        self.resolution_text: str = self.resolution_texts[self.game.local_settings_dict["resolution_index"]]
        self.resolution_text_rect: pg.Rect = FONT.get_rect(self.resolution_text)
        self.resolution_text_rect.topright = self.resolution_button.rect.topright
        self.resolution_text_rect.x -= 3
        self.resolution_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.resolution_text_rect.x -= self.resolution_button.rect.x
        self.resolution_text_rect.y -= self.resolution_button.rect.y
        # Draw it on button
        self.resolution_button.draw_extra_text_on_surf(
            self.resolution_text,
            self.resolution_text_rect.topleft,
        )

        # Up input text
        self.up_input_text: str = pg.key.name(self.game.local_settings_dict["up"])
        self.up_input_text_rect: pg.Rect = FONT.get_rect(self.up_input_text)
        self.up_input_text_rect.topright = self.up_input_button.rect.topright
        self.up_input_text_rect.x -= 3
        self.up_input_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.up_input_text_rect.x -= self.up_input_button.rect.x
        self.up_input_text_rect.y -= self.up_input_button.rect.y
        # Draw it on button
        self.up_input_button.draw_extra_text_on_surf(
            self.up_input_text,
            self.up_input_text_rect.topleft,
        )

        # Down input text
        self.down_input_text: str = pg.key.name(self.game.local_settings_dict["down"])
        self.down_input_text_rect: pg.Rect = FONT.get_rect(self.down_input_text)
        self.down_input_text_rect.topright = self.down_input_button.rect.topright
        self.down_input_text_rect.x -= 3
        self.down_input_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.down_input_text_rect.x -= self.down_input_button.rect.x
        self.down_input_text_rect.y -= self.down_input_button.rect.y
        # Draw it on button
        self.down_input_button.draw_extra_text_on_surf(
            self.down_input_text,
            self.down_input_text_rect.topleft,
        )

        # Left input text
        self.left_input_text: str = pg.key.name(self.game.local_settings_dict["left"])
        self.left_input_text_rect: pg.Rect = FONT.get_rect(self.left_input_text)
        self.left_input_text_rect.topright = self.left_input_button.rect.topright
        self.left_input_text_rect.x -= 3
        self.left_input_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.left_input_text_rect.x -= self.left_input_button.rect.x
        self.left_input_text_rect.y -= self.left_input_button.rect.y
        # Draw it on button
        self.left_input_button.draw_extra_text_on_surf(
            self.left_input_text,
            self.left_input_text_rect.topleft,
        )

        # Right input text
        self.right_input_text: str = pg.key.name(self.game.local_settings_dict["right"])
        self.right_input_text_rect: pg.Rect = FONT.get_rect(self.right_input_text)
        self.right_input_text_rect.topright = self.right_input_button.rect.topright
        self.right_input_text_rect.x -= 3
        self.right_input_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.right_input_text_rect.x -= self.right_input_button.rect.x
        self.right_input_text_rect.y -= self.right_input_button.rect.y
        # Draw it on button
        self.right_input_button.draw_extra_text_on_surf(
            self.right_input_text,
            self.right_input_text_rect.topleft,
        )

        # Enter input text
        self.enter_input_text: str = pg.key.name(self.game.local_settings_dict["enter"])
        self.enter_input_text_rect: pg.Rect = FONT.get_rect(self.enter_input_text)
        self.enter_input_text_rect.topright = self.enter_input_button.rect.topright
        self.enter_input_text_rect.x -= 3
        self.enter_input_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.enter_input_text_rect.x -= self.enter_input_button.rect.x
        self.enter_input_text_rect.y -= self.enter_input_button.rect.y
        # Draw it on button
        self.enter_input_button.draw_extra_text_on_surf(
            self.enter_input_text,
            self.enter_input_text_rect.topleft,
        )

        # Pause input text
        self.pause_input_text: str = pg.key.name(self.game.local_settings_dict["pause"])
        self.pause_input_text_rect: pg.Rect = FONT.get_rect(self.pause_input_text)
        self.pause_input_text_rect.topright = self.pause_input_button.rect.topright
        self.pause_input_text_rect.x -= 3
        self.pause_input_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.pause_input_text_rect.x -= self.pause_input_button.rect.x
        self.pause_input_text_rect.y -= self.pause_input_button.rect.y
        # Draw it on button
        self.pause_input_button.draw_extra_text_on_surf(
            self.pause_input_text,
            self.pause_input_text_rect.topleft,
        )

        # Jump input text
        self.jump_input_text: str = pg.key.name(self.game.local_settings_dict["jump"])
        self.jump_input_text_rect: pg.Rect = FONT.get_rect(self.jump_input_text)
        self.jump_input_text_rect.topright = self.jump_input_button.rect.topright
        self.jump_input_text_rect.x -= 3
        self.jump_input_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.jump_input_text_rect.x -= self.jump_input_button.rect.x
        self.jump_input_text_rect.y -= self.jump_input_button.rect.y
        # Draw it on button
        self.jump_input_button.draw_extra_text_on_surf(
            self.jump_input_text,
            self.jump_input_text_rect.topleft,
        )

        # Attack input text
        self.attack_input_text: str = pg.key.name(self.game.local_settings_dict["attack"])
        self.attack_input_text_rect: pg.Rect = FONT.get_rect(self.attack_input_text)
        self.attack_input_text_rect.topright = self.attack_input_button.rect.topright
        self.attack_input_text_rect.x -= 3
        self.attack_input_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.attack_input_text_rect.x -= self.attack_input_button.rect.x
        self.attack_input_text_rect.y -= self.attack_input_button.rect.y
        # Draw it on button
        self.attack_input_button.draw_extra_text_on_surf(
            self.attack_input_text,
            self.attack_input_text_rect.topleft,
        )

    def _setup_decoration_lines(self) -> None:
        """Setup decoration lines."""
        self.decoration_vertical_start = (NATIVE_RECT.center[0], self.button_flex_col_topleft[1])
        self.decoration_vertical_x: int = self.decoration_vertical_start[0]
        self.decoration_vertical_top: int = self.decoration_vertical_start[1]
        self.decoration_vetical_height: int = self.button_container.button_height_with_margin * self.button_container.limit
        self.decoration_vertical_bottom: int = self.decoration_vertical_top + self.decoration_vetical_height
        self.decoration_horizontal_y: int = self.decoration_vertical_bottom
        self.decoration_horizontal_left: int = self.button_flex_col_topleft[0]
        self.decoration_horizontal_right: int = self.button_flex_col_topleft[0] + self.wide_button_width

        self.decoration_line_surf_horizontal: pg.Surface = pg.Surface(
            (self.decoration_horizontal_right - self.decoration_horizontal_left, 1)
        )
        self.decoration_line_surf_horizontal.fill("#0193bc")

        self.decoration_line_surf_vertical: pg.Surface = pg.Surface(
            (1, self.decoration_vertical_bottom - self.decoration_vertical_top)
        )
        self.decoration_line_surf_vertical.fill("#0193bc")

    def _create_state_machine_update(self) -> StateMachine:
        """Create state machine for update."""
        return StateMachine(
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

    def _create_state_machine_draw(self) -> StateMachine:
        """Create state machine for draw."""
        return StateMachine(
            initial_state=OptionsMenu.State.JUST_ENTERED_SCENE,
            state_handlers={
                OptionsMenu.State.JUST_ENTERED_SCENE: self._JUST_ENTERED_SCENE_DRAW,
                OptionsMenu.State.CLOSING_SCENE_CURTAIN: self._CLOSING_SCENE_CURTAIN_DRAW,
                OptionsMenu.State.CLOSED_SCENE_CURTAIN: self._CLOSED_SCENE_CURTAIN_DRAW,
                OptionsMenu.State.OPENING_SCENE_CURTAIN: self._OPENING_SCENE_CURTAIN_DRAW,
                OptionsMenu.State.OPENED_SCENE_CURTAIN: self._OPENED_SCENE_CURTAIN_DRAW,
                OptionsMenu.State.REBIND: self._REBIND_DRAW,
            },
            transition_actions={},
        )

    # State draw logics
    def _JUST_ENTERED_SCENE_DRAW(self, _dt: int) -> None:
        pass

    def _CLOSING_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
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

    def _OPENING_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        # Clear curtain
        self.curtain.surf.fill(self.curtain_clear_color)

        # Draw title.
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

    def _OPENED_SCENE_CURTAIN_DRAW(self, _dt: int) -> None:
        pass

    def _REBIND_DRAW(self, _dt: int) -> None:
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

    # State update logics
    def _JUST_ENTERED_SCENE(self, dt: int) -> None:
        self.entry_delay_timer.update(dt)

    def _CLOSING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)

    def _CLOSED_SCENE_CURTAIN(self, dt: int) -> None:
        # Update button index
        # Update button active alpha
        self.button_container.update(dt)

        # Focusing on resolution button?
        if self.resolution_button == self.focused_button:
            # Get left right direction
            new_value = self.game.local_settings_dict["resolution_index"]
            is_pressed_left_or_right: bool = False
            # Left?
            if self.game_event_handler.is_left_just_pressed:
                new_value -= 1
                is_pressed_left_or_right = True
            # Right?
            if self.game_event_handler.is_right_just_pressed:
                new_value += 1
                is_pressed_left_or_right = True
            # Update resolution index
            if is_pressed_left_or_right:
                if self.game.local_settings_dict["resolution_index"] != new_value:
                    self.set_resolution_index(new_value)
                    # Update game.local_settings_dict resolution
                    self.game.set_resolution_index(self.game.local_settings_dict["resolution_index"])

    def _OPENING_SCENE_CURTAIN(self, dt: int) -> None:
        self.curtain.update(dt)
        self.button_container.update(dt)

    def _OPENED_SCENE_CURTAIN(self, dt: int) -> None:
        self.exit_delay_timer.update(dt)

    def _REBIND(self, dt: int) -> None:
        # Pressed any key?
        if self.game_event_handler.is_any_key_just_pressed:
            # Find if pressed key is used already?
            for key_name, key_int in self.game.local_settings_dict.items():
                # Update text to alert message, return
                if self.game_event_handler.this_frame_event is not None:
                    if self.game_event_handler.this_frame_event.key == key_int:
                        self.update_input_text(self.focused_button, f"used by '{key_name}'")
                        return

            # Rebind, update game.local_settings_dict input
            # TODO: Create key val for this
            if self.game_event_handler.this_frame_event is not None:
                if self.focused_button == self.up_input_button:
                    self.game.local_settings_dict["up"] = self.game_event_handler.this_frame_event.key
                elif self.focused_button == self.down_input_button:
                    self.game.local_settings_dict["down"] = self.game_event_handler.this_frame_event.key
                elif self.focused_button == self.left_input_button:
                    self.game.local_settings_dict["left"] = self.game_event_handler.this_frame_event.key
                elif self.focused_button == self.right_input_button:
                    self.game.local_settings_dict["right"] = self.game_event_handler.this_frame_event.key
                elif self.focused_button == self.enter_input_button:
                    self.game.local_settings_dict["enter"] = self.game_event_handler.this_frame_event.key
                elif self.focused_button == self.pause_input_button:
                    self.game.local_settings_dict["pause"] = self.game_event_handler.this_frame_event.key
                elif self.focused_button == self.jump_input_button:
                    self.game.local_settings_dict["jump"] = self.game_event_handler.this_frame_event.key
                elif self.focused_button == self.attack_input_button:
                    self.game.local_settings_dict["attack"] = self.game_event_handler.this_frame_event.key

                # Update input text
                self.update_input_text(
                    self.focused_button,
                    pg.key.name(self.game_event_handler.this_frame_event.key),
                )

                # Update event handler function binds
                self.game_event_handler.init_keybind()

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
        # Update input text to "press any key"
        self.update_input_text(self.focused_button, "press any key")

    def _REBIND_to_CLOSED_SCENE_CURTAIN(self) -> None:
        pass

    def _OPENING_SCENE_CURTAIN_to_OPENED_SCENE_CURTAIN(self) -> None:
        pass

    # Callbacks
    def on_entry_delay_timer_end(self) -> None:
        """
        Delay ends, starts going to opaque.
        """
        self.state_machine_update.change_state(OptionsMenu.State.CLOSING_SCENE_CURTAIN)
        self.state_machine_draw.change_state(OptionsMenu.State.CLOSING_SCENE_CURTAIN)

    def on_exit_delay_timer_end(self) -> None:
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

    def on_curtain_invisible(self) -> None:
        """
        Set OPENED_SCENE_CURTAIN state.
        """

        self.state_machine_update.change_state(OptionsMenu.State.OPENED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(OptionsMenu.State.OPENED_SCENE_CURTAIN)

    def on_curtain_opaque(self) -> None:
        """
        Set CLOSED_SCENE_CURTAIN state.
        """

        self.state_machine_update.change_state(OptionsMenu.State.CLOSED_SCENE_CURTAIN)
        self.state_machine_draw.change_state(OptionsMenu.State.CLOSED_SCENE_CURTAIN)

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
            # Exit state to OPENING_SCENE_CURTAIN
            self.load_settings_and_update_ui()
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
        self.game.debug_draw.add(
            {
                "type": "text",
                "layer": 6,
                "x": 0,
                "y": 6,
                "text": (f"options menu state " f"state: {self.state_machine_update.state.name}"),
            }
        )

        self.state_machine_update.handle(dt)

    # Helpers
    def load_settings_and_update_ui(self) -> None:
        """
        Left and right input while resolution button is focused.
        """

        old_local_settings_dict_resolution_index = self.game.local_settings_dict["resolution_index"]

        # Try loading to local, if not dump local to disk
        self.game.load_or_create_settings()

        # Update input texts with local

        # Resolution input text
        self.set_resolution_index(self.game.local_settings_dict["resolution_index"])
        if old_local_settings_dict_resolution_index != (self.game.local_settings_dict["resolution_index"]):
            # Update game.local_settings_dict resolution
            self.game.set_resolution_index(self.game.local_settings_dict["resolution_index"])

        # Up input text
        self.update_input_text(
            self.up_input_button,
            pg.key.name(self.game.local_settings_dict["up"]),
        )
        # Down input text
        self.update_input_text(
            self.down_input_button,
            pg.key.name(self.game.local_settings_dict["down"]),
        )
        # Left input text
        self.update_input_text(
            self.left_input_button,
            pg.key.name(self.game.local_settings_dict["left"]),
        )
        # Right input text
        self.update_input_text(
            self.right_input_button,
            pg.key.name(self.game.local_settings_dict["right"]),
        )
        # Enter input text
        self.update_input_text(
            self.enter_input_button,
            pg.key.name(self.game.local_settings_dict["enter"]),
        )
        # Pause input text
        self.update_input_text(
            self.pause_input_button,
            pg.key.name(self.game.local_settings_dict["pause"]),
        )
        # Jump input text
        self.update_input_text(
            self.jump_input_button,
            pg.key.name(self.game.local_settings_dict["jump"]),
        )
        # Attack input text
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

        # TODO: Move this to key val pair

        if button == self.up_input_button:
            self.up_input_text = text
            self.up_input_text_rect = FONT.get_rect(self.up_input_text)
            self.up_input_text_rect.topright = self.up_input_button.rect.topright
            self.up_input_text_rect.x -= 3
            self.up_input_text_rect.y += 2
            # Compute to relative position to button topleft rect
            self.up_input_text_rect.x -= self.up_input_button.rect.x
            self.up_input_text_rect.y -= self.up_input_button.rect.y
            # Draw it on button
            self.up_input_button.draw_extra_text_on_surf(
                self.up_input_text,
                self.up_input_text_rect.topleft,
            )

        elif button == self.down_input_button:
            self.down_input_text = text
            self.down_input_text_rect = FONT.get_rect(self.down_input_text)
            self.down_input_text_rect.topright = self.down_input_button.rect.topright
            self.down_input_text_rect.x -= 3
            self.down_input_text_rect.y += 2
            # Compute to relative position to button topleft rect
            self.down_input_text_rect.x -= self.down_input_button.rect.x
            self.down_input_text_rect.y -= self.down_input_button.rect.y
            # Draw it on button
            self.down_input_button.draw_extra_text_on_surf(
                self.down_input_text,
                self.down_input_text_rect.topleft,
            )

        elif button == self.left_input_button:
            self.left_input_text = text
            self.left_input_text_rect = FONT.get_rect(self.left_input_text)
            self.left_input_text_rect.topright = self.left_input_button.rect.topright
            self.left_input_text_rect.x -= 3
            self.left_input_text_rect.y += 2
            # Compute to relative position to button topleft rect
            self.left_input_text_rect.x -= self.left_input_button.rect.x
            self.left_input_text_rect.y -= self.left_input_button.rect.y
            # Draw it on button
            self.left_input_button.draw_extra_text_on_surf(
                self.left_input_text,
                self.left_input_text_rect.topleft,
            )

        elif button == self.right_input_button:
            self.right_input_text = text
            self.right_input_text_rect = FONT.get_rect(self.right_input_text)
            self.right_input_text_rect.topright = self.right_input_button.rect.topright
            self.right_input_text_rect.x -= 3
            self.right_input_text_rect.y += 2
            # Compute to relative position to button topleft rect
            self.right_input_text_rect.x -= self.right_input_button.rect.x
            self.right_input_text_rect.y -= self.right_input_button.rect.y
            # Draw it on button
            self.right_input_button.draw_extra_text_on_surf(
                self.right_input_text,
                self.right_input_text_rect.topleft,
            )

        elif button == self.enter_input_button:
            self.enter_input_text = text
            self.enter_input_text_rect = FONT.get_rect(self.enter_input_text)
            self.enter_input_text_rect.topright = self.enter_input_button.rect.topright
            self.enter_input_text_rect.x -= 3
            self.enter_input_text_rect.y += 2
            # Compute to relative position to button topleft rect
            self.enter_input_text_rect.x -= self.enter_input_button.rect.x
            self.enter_input_text_rect.y -= self.enter_input_button.rect.y
            # Draw it on button
            self.enter_input_button.draw_extra_text_on_surf(
                self.enter_input_text,
                self.enter_input_text_rect.topleft,
            )

        elif button == self.pause_input_button:
            self.pause_input_text = text
            self.pause_input_text_rect = FONT.get_rect(self.pause_input_text)
            self.pause_input_text_rect.topright = self.pause_input_button.rect.topright
            self.pause_input_text_rect.x -= 3
            self.pause_input_text_rect.y += 2
            # Compute to relative position to button topleft rect
            self.pause_input_text_rect.x -= self.pause_input_button.rect.x
            self.pause_input_text_rect.y -= self.pause_input_button.rect.y
            # Draw it on button
            self.pause_input_button.draw_extra_text_on_surf(
                self.pause_input_text,
                self.pause_input_text_rect.topleft,
            )

        elif button == self.jump_input_button:
            self.jump_input_text = text
            self.jump_input_text_rect = FONT.get_rect(self.jump_input_text)
            self.jump_input_text_rect.topright = self.jump_input_button.rect.topright
            self.jump_input_text_rect.x -= 3
            self.jump_input_text_rect.y += 2
            # Compute to relative position to button topleft rect
            self.jump_input_text_rect.x -= self.jump_input_button.rect.x
            self.jump_input_text_rect.y -= self.jump_input_button.rect.y
            # Draw it on button
            self.jump_input_button.draw_extra_text_on_surf(
                self.jump_input_text,
                self.jump_input_text_rect.topleft,
            )

        elif button == self.attack_input_button:
            self.attack_input_text = text
            self.attack_input_text_rect = FONT.get_rect(self.attack_input_text)
            self.attack_input_text_rect.topright = self.attack_input_button.rect.topright
            self.attack_input_text_rect.x -= 3
            self.attack_input_text_rect.y += 2
            # Compute to relative position to button topleft rect
            self.attack_input_text_rect.x -= self.attack_input_button.rect.x
            self.attack_input_text_rect.y -= self.attack_input_button.rect.y
            # Draw it on button
            self.attack_input_button.draw_extra_text_on_surf(
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

        self.game.local_settings_dict["resolution_index"] = value
        self.game.local_settings_dict["resolution_index"] = (
            self.game.local_settings_dict["resolution_index"] % self.resolution_texts_len
        )
        self.resolution_text = self.resolution_texts[self.game.local_settings_dict["resolution_index"]]
        self.resolution_text_rect = FONT.get_rect(self.resolution_text)
        self.resolution_text_rect.topright = self.resolution_button.rect.topright
        self.resolution_text_rect.x -= 3
        self.resolution_text_rect.y += 2
        # Compute to relative position to button topleft rect
        self.resolution_text_rect.x -= self.resolution_button.rect.x
        self.resolution_text_rect.y -= self.resolution_button.rect.y
        # Draw it on button
        self.resolution_button.draw_extra_text_on_surf(
            self.resolution_text,
            self.resolution_text_rect.topleft,
        )

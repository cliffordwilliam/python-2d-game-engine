from constants import FONT
from constants import NATIVE_RECT
from constants import pg
from nodes.curtain import Curtain
from typeguard import typechecked


@typechecked
class Button:
    # Inactive colors
    BUTTON_INACTIVE_BODY_COLOR: str = "#000f28"
    BUTTON_INACTIVE_LINE_COLOR: str = "#004a89"
    BUTTON_INACTIVE_TEXT_COLOR: str = "#bac3d2"

    # Active colors
    BUTTON_ACTIVE_BODY_COLOR: str = "#126a9c"
    BUTTON_ACTIVE_LINE_COLOR: str = "#1896ea"
    BUTTON_ACTIVE_TEXT_COLOR: str = "#feffff"

    # Hover colors
    BUTTON_HOVER_BODY_COLOR: str = "#6aa1c0"
    BUTTON_HOVER_LINE_COLOR: str = "#52b0ef"
    BUTTON_HOVER_TEXT_COLOR: str = "#feffff"

    # Desc padding
    DESCRIPTION_TEXT_BOTTOM_PADDING: int = 2

    # States
    INACTIVE: int = 0
    ACTIVE: int = 1

    def __init__(
        self,
        surf_size_tuple: tuple[int, int],
        topleft: tuple[int, int],
        text: str,
        text_topleft: tuple[int, int],
        description_text: str,
    ):
        # Create surf and fill it
        self.surf: pg.Surface = pg.Surface(surf_size_tuple)
        self.surf.fill(self.BUTTON_INACTIVE_BODY_COLOR)

        # Get surf rect and position it with given topleft
        self.rect: pg.Rect = self.surf.get_rect()
        self.rect.topleft = topleft

        # Draw decor on surf, need rect dimension for this
        pg.draw.line(
            self.surf,
            self.BUTTON_INACTIVE_LINE_COLOR,
            (0, 0),
            (0, self.rect.height),
        )

        # Get text
        self.text: str = text
        # Position text topleft relative to my rect
        self.text_top_left: tuple[int, int] = text_topleft
        # Draw text on surf
        FONT.render_to(
            self.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_INACTIVE_TEXT_COLOR,
        )

        # Create active curtain
        self.active_curtain: Curtain = Curtain(
            duration=300.0,
            start_state=Curtain.INVISIBLE,
            max_alpha=225,
            surf_size_tuple=(self.rect.width + 1, self.rect.height),
            is_invisible=False,
            color=self.BUTTON_ACTIVE_BODY_COLOR,
        )
        # Position active curtain rect to my rect
        self.active_curtain.rect.topright = self.rect.topright
        # Draw decor on active curtain surf
        pg.draw.line(
            self.active_curtain.surf,
            self.BUTTON_ACTIVE_TEXT_COLOR,
            (0, 0),
            (0, self.rect.height),
        )
        pg.draw.line(
            self.active_curtain.surf,
            self.BUTTON_ACTIVE_LINE_COLOR,
            (1, 0),
            (1, self.rect.height),
        )
        # Draw text on active curtain surf
        FONT.render_to(
            self.active_curtain.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_ACTIVE_TEXT_COLOR,
        )

        # Create hover curtain
        self.hover_curtain: Curtain = Curtain(
            duration=1500.0,
            start_state=Curtain.INVISIBLE,
            max_alpha=225,
            surf_size_tuple=(self.rect.width + 1, self.rect.height),
            is_invisible=False,
            color=self.BUTTON_HOVER_BODY_COLOR,
        )
        self.hover_curtain.add_event_listener(self._on_hover_curtain_invisible, Curtain.INVISIBLE_END)
        self.hover_curtain.add_event_listener(self._on_hover_curtain_opaque, Curtain.OPAQUE_END)
        # Set hover curtain rect to my rect
        self.hover_curtain.rect.topright = self.rect.topright
        # Draw decor on hover curtain surf
        pg.draw.line(
            self.hover_curtain.surf,
            self.BUTTON_HOVER_TEXT_COLOR,
            (0, 0),
            (0, self.rect.height),
        )
        pg.draw.line(
            self.hover_curtain.surf,
            self.BUTTON_HOVER_LINE_COLOR,
            (1, 0),
            (1, self.rect.height),
        )
        # Draw text on hover curtain surf
        FONT.render_to(
            self.hover_curtain.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_HOVER_TEXT_COLOR,
        )

        # Get description text
        self.description_text: str = description_text
        # Get description rect
        self.description_text_rect: pg.Rect = FONT.get_rect(self.description_text)
        # Position description rect
        self.description_text_rect.center = NATIVE_RECT.center
        self.description_text_rect.bottom = NATIVE_RECT.bottom
        self.description_text_rect.y -= self.DESCRIPTION_TEXT_BOTTOM_PADDING

        # Set initial state to INACTIVE
        self.state: int = self.INACTIVE

    # Callbacks
    def _on_hover_curtain_invisible(self) -> None:
        # Only hover bounce curtain fade in ACTIVE STATE
        if self.state == self.ACTIVE:
            self.hover_curtain.go_to_opaque()

    def _on_hover_curtain_opaque(self) -> None:
        # Only hover bounce curtain fade in ACTIVE STATE
        if self.state == self.ACTIVE:
            self.hover_curtain.go_to_invisible()

    # Draw
    def draw(self, surf: pg.Surface, y_offset: int) -> None:
        """
        Draw:
        - description text.
        - surf.
        - active curtain.
        """

        # Draw my description text if I am active
        if self.state == self.ACTIVE:
            FONT.render_to(
                surf,
                self.description_text_rect,
                self.description_text,
                self.BUTTON_ACTIVE_TEXT_COLOR,
            )

        # Draw my surf
        surf.blit(self.surf, (self.rect.x, self.rect.y + y_offset))

        # Draw my active surf
        self.active_curtain.draw(surf, y_offset)

        # Draw my hover surf
        self.hover_curtain.draw(surf, y_offset)

    # Update
    def update(self, dt: int) -> None:
        """
        Update:
        - active_curtain
        - hover_curtain
        """

        # Update my active surf
        self.active_curtain.update(dt)

        # Update my hover surf
        self.hover_curtain.update(dt)

    def set_state(self, value: int) -> None:
        """
        State setter and cleanup.
        """

        old_state: int = self.state
        self.state = value

        # From INACTIVE?
        if old_state == self.INACTIVE:
            # To ACTIVE?
            if self.state == self.ACTIVE:
                # Active surf go to opaque
                self.active_curtain.go_to_opaque()
                # Hover surf go to opaque
                self.hover_curtain.go_to_opaque()

        # From ACTIVE?
        elif old_state == self.ACTIVE:
            # To INACTIVE?
            if self.state == self.INACTIVE:
                # Active surf go to invisible
                self.active_curtain.go_to_invisible()
                # Hover surf go to invisible
                self.hover_curtain.jump_to_invisible()

    # Abilities
    def apply_y_offset_to_rect_and_curtain_rects(
        self,
        value: int,
    ) -> None:
        """
        Used by button container.
        Value is added.
        """

        self.rect.y += value
        self.active_curtain.rect.y += value
        self.hover_curtain.rect.y += value

    def draw_extra_text_on_surf(
        self,
        text: str,
        position_tuple_relative_to_button_surf_topleft: tuple[int, int],
    ) -> None:
        """
        Use this to draw extra text on the button.
        Clear both active and inactive surf.
        Draw old texts on them.
        Draw given texts on them.
        """

        # Clear all surfs
        self.surf.fill(self.BUTTON_INACTIVE_BODY_COLOR)
        self.active_curtain.surf.fill(self.BUTTON_ACTIVE_BODY_COLOR)
        self.hover_curtain.surf.fill(self.BUTTON_HOVER_BODY_COLOR)

        # Draw decor on surf
        pg.draw.line(
            self.surf,
            self.BUTTON_INACTIVE_LINE_COLOR,
            (0, 0),
            (0, self.rect.height),
        )

        # Draw original text on surf
        FONT.render_to(
            self.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_INACTIVE_TEXT_COLOR,
        )

        # Draw given text on surf
        FONT.render_to(
            self.surf,
            position_tuple_relative_to_button_surf_topleft,
            text,
            self.BUTTON_INACTIVE_TEXT_COLOR,
        )

        # Draw decor on active curtain surf
        pg.draw.line(
            self.active_curtain.surf,
            self.BUTTON_ACTIVE_TEXT_COLOR,
            (0, 0),
            (0, self.rect.height),
        )
        pg.draw.line(
            self.active_curtain.surf,
            self.BUTTON_ACTIVE_LINE_COLOR,
            (1, 0),
            (1, self.rect.height),
        )
        # Draw original text on active curtain surf
        FONT.render_to(
            self.active_curtain.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_ACTIVE_TEXT_COLOR,
        )
        # Draw given text on active curtain surf
        FONT.render_to(
            self.active_curtain.surf,
            position_tuple_relative_to_button_surf_topleft,
            text,
            self.BUTTON_ACTIVE_TEXT_COLOR,
        )

        # Draw decor on hover curtain surf
        pg.draw.line(
            self.hover_curtain.surf,
            self.BUTTON_HOVER_TEXT_COLOR,
            (0, 0),
            (0, self.rect.height),
        )
        pg.draw.line(
            self.hover_curtain.surf,
            self.BUTTON_HOVER_LINE_COLOR,
            (1, 0),
            (1, self.rect.height),
        )
        # Draw original text on hover curtain surf
        FONT.render_to(
            self.hover_curtain.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_HOVER_TEXT_COLOR,
        )
        # Draw given text on active curtain surf
        FONT.render_to(
            self.hover_curtain.surf,
            position_tuple_relative_to_button_surf_topleft,
            text,
            self.BUTTON_HOVER_TEXT_COLOR,
        )

    def draw_extra_surf_on_surf(
        self,
        surf: pg.Surface,
        position_tuple_relative_to_button_surf_topleft: tuple[int, int],
    ) -> None:
        """
        Use this to draw extra surf on the button.
        Clear both active and inactive surf.
        Draw old texts on them.
        Draw given surf on them.
        """

        # Clear all surfs
        self.surf.fill(self.BUTTON_INACTIVE_BODY_COLOR)
        self.active_curtain.surf.fill(self.BUTTON_ACTIVE_BODY_COLOR)
        self.hover_curtain.surf.fill(self.BUTTON_HOVER_BODY_COLOR)

        # Draw decor on surf
        pg.draw.line(
            self.surf,
            self.BUTTON_INACTIVE_LINE_COLOR,
            (0, 0),
            (0, self.rect.height),
        )

        # Draw original text on surf
        FONT.render_to(
            self.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_INACTIVE_TEXT_COLOR,
        )

        # Draw given surf on surf
        self.surf.blit(
            surf,
            position_tuple_relative_to_button_surf_topleft,
        )

        # Draw decor on active curtain surf
        pg.draw.line(
            self.active_curtain.surf,
            self.BUTTON_ACTIVE_TEXT_COLOR,
            (0, 0),
            (0, self.rect.height),
        )
        pg.draw.line(
            self.active_curtain.surf,
            self.BUTTON_ACTIVE_LINE_COLOR,
            (1, 0),
            (1, self.rect.height),
        )
        # Draw original text on active curtain surf
        FONT.render_to(
            self.active_curtain.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_ACTIVE_TEXT_COLOR,
        )
        # Draw given surf on active curtain surf
        self.active_curtain.surf.blit(
            surf,
            position_tuple_relative_to_button_surf_topleft,
        )
        # Draw decor on hover curtain surf
        pg.draw.line(
            self.hover_curtain.surf,
            self.BUTTON_HOVER_TEXT_COLOR,
            (0, 0),
            (0, self.rect.height),
        )
        pg.draw.line(
            self.hover_curtain.surf,
            self.BUTTON_HOVER_LINE_COLOR,
            (1, 0),
            (1, self.rect.height),
        )
        # Draw original text on hover curtain surf
        FONT.render_to(
            self.hover_curtain.surf,
            self.text_top_left,
            self.text,
            self.BUTTON_HOVER_TEXT_COLOR,
        )
        # Draw given surf on hover curtain surf
        self.hover_curtain.surf.blit(
            surf,
            position_tuple_relative_to_button_surf_topleft,
        )

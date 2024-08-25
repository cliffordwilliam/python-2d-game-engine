from typing import Any
from typing import TYPE_CHECKING

from constants import FONT
from constants import MAX_QUADTREE_DEPTH
from constants import pg
from typeguard import typechecked

# REMOVE IN BUILD

if TYPE_CHECKING:
    # REMOVE IN BUILD
    from nodes.debug_draw import DebugDraw
    from nodes.camera import Camera

# Global dictionary to map actor IDs to quadtree instances
actor_to_quad: dict[int, "Quadtree"] = {}


@typechecked
class Quadtree:
    """
    Given a finite space.
    Populated with rects.
    Use a rect to find the rects that overlaps with it.

    Found actors inside the camera rect = quadtree.search(camera.rect)
    Then iterate and call each of their draw and update.

    On first actors init, add it to quadtree with its insert method.

    When room changed, use the resize and re add the actors again.

    If you used search and found actors, then you want to delete them? Use the remove actor method.

    If actors move, call the relocate and pass the moved actor right after you have updated its position.

    Use this to group a set of moving rect things you want to look for with a rect.
    """

    def __init__(self, rect: pg.FRect, depth: int):
        """
        Here we refer to current rect, might be root, or a kid.
        """

        # Limit with max constant, keeps track of depth level
        self.depth: int = depth

        # My rect, to check if actor is inside or not
        self.rect: pg.FRect = rect

        # To hold my potential 4 kids
        self.potential_kid_number: int = 4
        self.kids: list[(None | Quadtree)] = [None] * self.potential_kid_number

        # Actors that I own
        self.actors: list[Any] = []

        # Prepare rects for my potential kids
        child_width: float = self.rect.width / 2.0
        child_height: float = self.rect.height / 2.0
        self.kids_rects: list[pg.FRect] = [
            # Topleft
            pg.FRect(
                (
                    self.rect.x,
                    self.rect.y,
                ),
                (
                    child_width,
                    child_height,
                ),
            ),
            # Topright
            pg.FRect(
                (
                    self.rect.x + child_width,
                    self.rect.y,
                ),
                (
                    child_width,
                    child_height,
                ),
            ),
            # Leftbottom
            pg.FRect(
                (
                    self.rect.x,
                    self.rect.y + child_height,
                ),
                (
                    child_width,
                    child_height,
                ),
            ),
            # Bottomright
            pg.FRect(
                (
                    self.rect.x + child_width,
                    self.rect.y + child_height,
                ),
                (
                    child_width,
                    child_height,
                ),
            ),
        ]

    #############
    # ABILITIES #
    #############
    def set_rect(self, rect: pg.FRect) -> None:
        """
        Called when room changed, set my root rect to be as big as room.
        """

        # Clear first, removes all existing kids
        self._clear()

        # Update my root rect
        self.rect = rect

        # Prepare rects for my potential kids
        child_width: float = self.rect.width / 2.0
        child_height: float = self.rect.height / 2.0
        self.kids_rects = [
            # Topleft
            pg.FRect(
                (
                    self.rect.x,
                    self.rect.y,
                ),
                (
                    child_width,
                    child_height,
                ),
            ),
            # Topright
            pg.FRect(
                (
                    self.rect.x + child_width,
                    self.rect.y,
                ),
                (
                    child_width,
                    child_height,
                ),
            ),
            # Leftbottom
            pg.FRect(
                (
                    self.rect.x,
                    self.rect.y + child_height,
                ),
                (
                    child_width,
                    child_height,
                ),
            ),
            # Bottomright
            pg.FRect(
                (
                    self.rect.x + child_width,
                    self.rect.y + child_height,
                ),
                (
                    child_width,
                    child_height,
                ),
            ),
        ]

    def get_size(self) -> int:
        """
        In case I need to know how many actors are in this quad.
        """

        # Get my total
        total_actors = len(self.actors)
        # Accumulate with kids total
        for kid in self.kids:
            if kid:
                total_actors += kid.get_size()
        return total_actors

    def insert(self, given_actor: Any) -> None:
        """
        Called when root first created or when actors position changed / relocated.
        """

        # To find actor that is completely inside one of my kid
        for i in range(self.potential_kid_number):
            # Get current iteration metadata
            kid_rect = self.kids_rects[i]
            kid = self.kids[i]

            # Given actor is completely inside one of my kid?
            if kid_rect.contains(given_actor.rect):
                # Still inside limit?
                if self.depth + 1 < MAX_QUADTREE_DEPTH:
                    # No child?
                    if not kid:
                        # Create child
                        kid = Quadtree(kid_rect, self.depth + 1)

                    # Got child? Or from creation above? Add given_actor to it
                    kid.insert(given_actor)
                    # At this point an actor was found inside one of my kid
                    # That actor was added to that kid, not mine
                    return

        # Actors is not completely inside any of my kids? Then its mine
        self.actors.append(given_actor)

        # Fill global book, store the mapping of actor id to me (me quadtree)
        actor_to_quad[given_actor.id] = self

    def search(self, given_rect: pg.FRect) -> list[Any]:
        """
        Return actors list that overlap with given rect.
        """
        # Prepare output
        found_actors: list[Any] = []

        # Recurssion search, this is expensive
        self._search_helper(given_rect, found_actors)

        # Return output
        return found_actors

    def relocate(self, given_actor: Any) -> None:
        """
        Call this and pass the actor right after they have moved / updated their position.
        """
        if self._remove_actor(given_actor):
            self.insert(given_actor)

    def get_all_actors(self) -> list[Any]:
        """
        In case I need to get all of the actors instance from this quad.
        """
        # Prepare output
        all_actors: list[Any] = []

        # Iterate over all quads in actor_to_quad
        for quadtree in actor_to_quad.values():
            # Add actors from each quad to the list
            all_actors.extend(quadtree.actors)

        # Return output
        return all_actors

    # REMOVE IN BUILD
    def draw(self, game_debug_draw: "DebugDraw", camera: "Camera") -> None:
        """
        Debugging purposes to show all of the quads (sections / kids).
        """
        # Draw the current quad
        x: float = self.rect.x - camera.rect.x
        y: float = self.rect.y - camera.rect.y

        # My rect
        game_debug_draw.add(
            {"type": "rect", "layer": 2, "rect": [x, y, self.rect.width, self.rect.height], "color": "cyan", "width": 1}
        )

        # Draw how many actors I have
        text_rect: pg.Rect = FONT.get_rect(f"actors: {len(self.actors)}")
        text_rect.center = (int(self.rect.centerx), int(self.rect.centery))
        text_x: float = float(text_rect.x) - camera.rect.x
        text_y: float = float(text_rect.y) - camera.rect.y
        game_debug_draw.add({"type": "text", "layer": 4, "x": text_x, "y": text_y, "text": f"actors: {len(self.actors)}"})

        # Recursively draw kids
        for kid in self.kids:
            if kid:
                kid.draw(game_debug_draw, camera)

    ##########
    # HELPER #
    ##########
    def _clear(self) -> None:
        """
        Purge all, until only root is left.
        """

        # Clear actor
        self.actors.clear()

        # Tell children to clear and empty themselves to None
        for kid in self.kids:
            if kid:
                kid._clear()
                kid = None

    def _search_helper(self, given_rect: pg.FRect, found_actors: list[Any]) -> None:
        """
        Search helper for the search ability.
        """
        # Check my actors, collect actors in me that overlap with given rect
        for actor in self.actors:
            if given_rect.colliderect(actor.rect):
                found_actors.append(actor)

        # Check my kids see if they can add actor

        # To find actor that is completely inside one of my kid
        for i in range(self.potential_kid_number):
            # Get current iteration metadata
            kid_rect = self.kids_rects[i]
            kid = self.kids[i]
            # I have kids?
            if kid:
                # This kid is completely inside the given rect, dump all of its actors to collection
                if given_rect.contains(kid_rect):
                    kid._add_actors(found_actors)

                # This kid only overlap given rect? Tell them to search again, recurssion
                elif kid_rect.colliderect(given_rect):
                    kid._search_helper(given_rect, found_actors)

    def _add_actors(self, found_actors: list[Any]) -> None:
        """
        Search helper helper. for kids to dump all of their actors and their subsequent kids actors to search output.
        """
        # Dump all of my actors into collection
        for actor in self.actors:
            found_actors.append(actor)

        # Dump all my children actors into collection
        for kid in self.kids:
            if kid:
                kid._add_actors(found_actors)

    def _remove_actor(self, given_actor: Any) -> bool:
        """
        Remove a certain actor from a certain quad (section / kid).
        """
        # Make sure that id is valid, it is in the book
        if given_actor.id in actor_to_quad:
            # Use the actor id to immediately get the quad it is in
            quadtree = actor_to_quad[given_actor.id]

            # Make sure that the given actor is in the quad from book
            if given_actor in quadtree.actors:
                # Remove actor from that quad
                quadtree.actors.remove(given_actor)

            # Delete that book row
            del actor_to_quad[given_actor.id]

            # 200 deleted ok
            return True

        # 400 not found
        return False

from dataclasses import dataclass
from typing import Any

from jsonschema import validate
from jsonschema import ValidationError

# How schema works
# This is the same like how you get json res, then you instance a class to represent it
# But here json res is either from reading a file or from hardcoded dict

# You want this because
# After validating dict against schema
# You get autocompletion with its prop, no more guessing what keys it has

# Protocol
# 1. Validate dict with SCHEMA
# 2. Instance dataclass
# 3. Use instance just like any other dict but has prop autocompletion

######################
# ANIMATION METADATA #
######################

# Animation metadata is json in project dir dynamic
# Generated from animation json generator
# It has
# Animation name
# Animation duration
# Animation sprite size
# And more...

# Todo:
# Validate on saving
# Update the dynamic path dict
# Validate on loading

# Example, "thin_fire_animation.json"

# {
#     "burn": {
#         "animation_is_loop": 1,
#         "next_animation_name": "none",
#         "animation_duration": 50,
#         "animation_sprite_height": 16,
#         "animation_sprite_width": 16,
#         "sprite_sheet_png_name": "thin_fire_sprite_sheet.png",
#         "animation_sprites_list": [
#             {
#                 "x": 0,
#                 "y": 0
#             },
#             {
#                 "x": 16,
#                 "y": 0
#             },
#         ]
#     },
#     "another_animation": {
#         "animation_is_loop": 1,
#         "next_animation_name": "none",
#         "animation_duration": 50,
#         "animation_sprite_height": 16,
#         "animation_sprite_width": 16,
#         "sprite_sheet_png_name": "thin_fire_sprite_sheet.png",
#         "animation_sprites_list": [
#             {
#                 "x": 0,
#                 "y": 0
#             },
#             {
#                 "x": 16,
#                 "y": 0
#             },
#         ]
#     }
# }

ANIMATION_SCHEMA: dict = {
    "type": "object",
    "patternProperties": {
        "^[a-zA-Z0-9_]+$": {
            "type": "object",
            "properties": {
                "animation_is_loop": {"type": "integer", "enum": [0, 1]},
                "next_animation_name": {"type": "string"},
                "animation_duration": {"type": "integer", "minimum": 0},
                "animation_sprite_height": {"type": "integer", "minimum": 1},
                "animation_sprite_width": {"type": "integer", "minimum": 1},
                "sprite_sheet_png_name": {"type": "string"},
                "animation_sprites_list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0}},
                        "required": ["x", "y"],
                    },
                    "minItems": 1,
                },
            },
            "required": [
                "animation_is_loop",
                "next_animation_name",
                "animation_duration",
                "animation_sprite_height",
                "animation_sprite_width",
                "sprite_sheet_png_name",
                "animation_sprites_list",
            ],
        }
    },
    "additionalProperties": False,
}

# TODO: Use this for validation in saving later
ANIMATION_SPRITE_METADATA_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "x": {"type": "integer", "minimum": 0},
        "y": {"type": "integer", "minimum": 0},
    },
    "required": [
        "x",
        "y",
    ],
}


# Dataclass for ANIMATION_SCHEMA's animation_sprites_list dict members
#             {
#                 "x": 0,
#                 "y": 0
#             },
@dataclass
class AnimationSpriteMetadata:
    x: int
    y: int


# Dataclass for ANIMATION_SCHEMA
@dataclass
class AnimationMetadata:
    animation_is_loop: int
    next_animation_name: str
    animation_duration: int
    animation_sprite_height: int
    animation_sprite_width: int
    sprite_sheet_png_name: str
    animation_sprites_list: list[AnimationSpriteMetadata]


# So the dataclass should look like this
# Dict
# Keys = animation name strings
# Values = AnimationMetadata with list[AnimationSpriteMetadata]


# Factory method to instance the dataclass
def instance_animation_metadata(input_dict: dict) -> dict[str, AnimationMetadata]:
    """
    Factory method, validates dict and returns instance dataclass version of it.

    Input = animation metadata json.

    Output = dict = {
        "animation_string_name_1": {
            AnimationMetadata: {
                "animation_is_loop": 1
                ...: ...
                "animation_sprites_list": list[AnimationSpriteMetadata]
            }
        },
        "animation_string_name_2": {
            AnimationMetadata: {
                "animation_is_loop": 0
                ...: ...
                "animation_sprites_list": list[AnimationSpriteMetadata]
            }
        }
        "animation_string_name_3": ...
    }

    I Raise invalid given animation dict against schema exception.
    """

    # Validate the given dict against the schema
    if not validate_json(input_dict, ANIMATION_SCHEMA):
        raise ValueError("Invalid given animation dict against schema")

    # Prepare output var
    out: dict[
        str,  # Animation name string (burn, another_animation)
        AnimationMetadata,
    ] = {}

    # Given dict is valid here, iter over each animation in it (burn, another_animation, ...)
    for animation_name, animation_metadata in input_dict.items():
        # Instance and populate each animation_sprites_list member first
        sprites_list = [
            AnimationSpriteMetadata(x=sprite["x"], y=sprite["y"]) for sprite in animation_metadata["animation_sprites_list"]
        ]

        # Then construct the whole AnimationMetadata instance
        out[animation_name] = AnimationMetadata(
            animation_is_loop=animation_metadata["animation_is_loop"],
            next_animation_name=animation_metadata["next_animation_name"],
            animation_duration=animation_metadata["animation_duration"],
            animation_sprite_height=animation_metadata["animation_sprite_height"],
            animation_sprite_width=animation_metadata["animation_sprite_width"],
            sprite_sheet_png_name=animation_metadata["sprite_sheet_png_name"],
            animation_sprites_list=sprites_list,
        )

    # Output is complete here, return it
    return out


#########################
# SPRITE SHEET METADATA #
#########################

# Sprite sheet metadata is json in project dir dynamic
# Generated from sprite sheet json generator
# It has
# Sprite sheet png name
# Sprite room map body color (for minimap)
# Sprites list (sprite name, layer, width, topleft, and more...)
# And more

# Todo:
# Validate on saving
# Update the dynamic path dict
# Validate on loading

# Example, this is "stage_1_sprite_sheet_metadata.json"

# {
#     "sprite_sheet_png_name": "stage_1_sprite_sheet.png",
#     "sprite_room_map_body_color": "#492a1e",
#     "sprite_room_map_sub_division_color": "#5a3729",
#     "sprite_room_map_border_color": "#e5e3bc",
#     "sprites_list": [
#         {
#             "sprite_name": "sky",
#             "sprite_layer": 1,
#             "sprite_tile_type": "none",
#             "sprite_type": "parallax_background",
#             "sprite_is_tile_mix": 0,
#             "width": 320,
#             "height": 128,
#             "x": 0,
#             "y": 0
#         },
#         {
#             "sprite_name": "clouds",
#             "sprite_layer": 2,
#             "sprite_tile_type": "none",
#             "sprite_type": "parallax_background",
#             "sprite_is_tile_mix": 0,
#             "width": 320,
#             "height": 160,
#             "x": 0,
#             "y": 128
#         },

SPRITE_SHEET_METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "sprite_sheet_png_name": {"type": "string"},
        "sprite_room_map_body_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "sprite_room_map_sub_division_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "sprite_room_map_border_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "sprites_list": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sprite_name": {"type": "string"},
                    "sprite_layer": {"type": "integer", "minimum": 1},
                    "sprite_tile_type": {"type": "string"},
                    "sprite_type": {"type": "string"},
                    "sprite_is_tile_mix": {"type": "integer", "enum": [0, 1]},
                    "width": {"type": "integer", "minimum": 1},
                    "height": {"type": "integer", "minimum": 1},
                    "x": {"type": "integer", "minimum": 0},
                    "y": {"type": "integer", "minimum": 0},
                },
                "required": [
                    "sprite_name",
                    "sprite_layer",
                    "sprite_tile_type",
                    "sprite_type",
                    "sprite_is_tile_mix",
                    "width",
                    "height",
                    "x",
                    "y",
                ],
            },
            "minItems": 1,
        },
    },
    "required": [
        "sprite_sheet_png_name",
        "sprite_room_map_body_color",
        "sprite_room_map_sub_division_color",
        "sprite_room_map_border_color",
        "sprites_list",
    ],
    "additionalProperties": False,
}

SPRITE_METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "sprite_name": {"type": "string"},
        "sprite_layer": {"type": "integer", "minimum": 1},
        "sprite_tile_type": {"type": "string"},
        "sprite_type": {"type": "string"},
        "sprite_is_tile_mix": {"type": "integer", "enum": [0, 1]},
        "width": {"type": "integer", "minimum": 1},
        "height": {"type": "integer", "minimum": 1},
        "x": {"type": "integer", "minimum": 0},
        "y": {"type": "integer", "minimum": 0},
    },
    "required": [
        "sprite_name",
        "sprite_layer",
        "sprite_tile_type",
        "sprite_type",
        "sprite_is_tile_mix",
        "width",
        "height",
        "x",
        "y",
    ],
}


# Dataclass for SPRITE_SHEET_METADATA_SCHEMA's sprites_list dict memebers
#         {
#             "sprite_name": "sky",
#             "sprite_layer": 1,
#             "sprite_tile_type": "none",
#             "sprite_type": "parallax_background",
#             "sprite_is_tile_mix": 0,
#             "width": 320,
#             "height": 128,
#             "x": 0,
#             "y": 0
#         },
@dataclass
class SpriteMetadata:
    sprite_name: str
    sprite_layer: int
    sprite_tile_type: str
    sprite_type: str
    sprite_is_tile_mix: int
    width: int
    height: int
    x: int
    y: int


# Dataclass for SPRITE_SHEET_METADATA_SCHEMA
@dataclass
class SpriteSheetMetadata:
    sprite_sheet_png_name: str
    sprite_room_map_body_color: str
    sprite_room_map_sub_division_color: str
    sprite_room_map_border_color: str
    sprites_list: list[SpriteMetadata]


# So the dataclass should look like this
# Dataclass instance
# SpriteSheetMetadata with list[SpriteMetadata]


# Factory method to instance the dataclass
def instance_sprite_sheet_metadata(input_dict: dict) -> SpriteSheetMetadata:
    """
    Factory method, validates dict and returns instance dataclass version of it.

    Input = sprite sheet metadata json.

    Output = SpriteSheetMetadata with list[SpriteMetadata].

    I Raise invalid sprite sheet dict against schema exception.
    """

    # Validate the given dict against the schema
    if not validate_json(input_dict, SPRITE_SHEET_METADATA_SCHEMA):
        raise ValueError("Invalid sprite sheet dict against schema")

    # Given dict is valid here, construct the whole instance
    return SpriteSheetMetadata(
        sprite_sheet_png_name=input_dict["sprite_sheet_png_name"],
        sprite_room_map_body_color=input_dict["sprite_room_map_body_color"],
        sprite_room_map_sub_division_color=input_dict["sprite_room_map_sub_division_color"],
        sprite_room_map_border_color=input_dict["sprite_room_map_border_color"],
        sprites_list=[
            SpriteMetadata(
                sprite_name=sprite["sprite_name"],
                sprite_layer=sprite["sprite_layer"],
                sprite_tile_type=sprite["sprite_tile_type"],
                sprite_type=sprite["sprite_type"],
                sprite_is_tile_mix=sprite["sprite_is_tile_mix"],
                width=sprite["width"],
                height=sprite["height"],
                x=sprite["x"],
                y=sprite["y"],
            )
            for sprite in input_dict["sprites_list"]
        ],
    )


def instance_sprite_metadata(input_dict: dict) -> SpriteMetadata:
    """
    Factory method, validates dict and returns instance dataclass version of it.

    Input = sprite sheet's sprite metadata json.

    Output = SpriteMetadata.

    I Raise invalid sprite dict against schema exception.
    """

    # Validate the given dict against the schema
    if not validate_json(input_dict, SPRITE_METADATA_SCHEMA):
        raise ValueError("Invalid sprite dict against schema")

    # Given dict is valid here, construct the whole instance
    return SpriteMetadata(
        sprite_name=input_dict["sprite_name"],
        sprite_layer=input_dict["sprite_layer"],
        sprite_tile_type=input_dict["sprite_tile_type"],
        sprite_type=input_dict["sprite_type"],
        sprite_is_tile_mix=input_dict["sprite_is_tile_mix"],
        width=input_dict["width"],
        height=input_dict["height"],
        x=input_dict["x"],
        y=input_dict["y"],
    )


#################
# USER SETTINGS #
#################

# Settings is json in user OS dir dynamic
# Generated from game
# It has
# Resolution index
# Resolution scale
# Up (input mapping)
# Down (input mapping)
# And more...

# Todo:
# Validate on saving
# Update the dynamic path dict
# Validate on loading

# Example, there can be only 1 of this stored in OS context sensitive dir
# Linux: /home/.config/python_2d_game_engine/settings.json

# {
#     "resolution_index": 2,
#     "resolution_scale": 3,
#     "up": 1073741906,
#     "down": 1073741905,
#     "left": 1073741904,
#     "right": 1073741903,
#     "enter": 13,
#     "pause": 27,
#     "jump": 99,
#     "attack": 120,
#     "lmb": 1,
#     "mmb": 2,
#     "rmb": 3
# }

SETTINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "resolution_index": {"type": "integer", "minimum": 0},
        "resolution_scale": {"type": "integer", "minimum": 1},
        "up": {"type": "integer", "minimum": 0},
        "down": {"type": "integer", "minimum": 0},
        "left": {"type": "integer", "minimum": 0},
        "right": {"type": "integer", "minimum": 0},
        "enter": {"type": "integer", "minimum": 0},
        "pause": {"type": "integer", "minimum": 0},
        "jump": {"type": "integer", "minimum": 0},
        "attack": {"type": "integer", "minimum": 0},
        # REMOVE IN BUILD
        "lmb": {"type": "integer", "minimum": 0},
        "mmb": {"type": "integer", "minimum": 0},
        "rmb": {"type": "integer", "minimum": 0},
    },
    "required": [
        "resolution_index",
        "resolution_scale",
        "up",
        "down",
        "left",
        "right",
        "enter",
        "pause",
        "jump",
        "attack",
        # REMOVE IN BUILD
        "lmb",
        "mmb",
        "rmb",
    ],
    "additionalProperties": False,
}


# TODO: Use this in place of dict after settings dict validation
@dataclass
class Settings:
    resolution_index: int
    resolution_scale: int
    up: int
    down: int
    left: int
    right: int
    enter: int
    pause: int
    jump: int
    attack: int
    # REMOVE IN BUILD
    lmb: int
    mmb: int
    rmb: int


################################
# NONE OR BLOB SPRITE METADATA #
################################

# None or blob sprite metadata is dict in room editor
# Created and stored in collision map list
# It has
# Sprite name
# Sprite x and y world coord
# Sprirte x and y sprite sheet region coord

# Todo:
# Validate on reading collision data
# Validate on storing collision data

# Example, on lmb pressed blob tile type

# new_none_or_blob_sprite_metadata_dict: dict = {
#     "name": selected_sprite_name,
#     "type": self.sprite_name_to_sprite_metadata[self.selected_sprite_name].sprite_type,
#     "x": world_snapped_x,
#     "y": world_snapped_y,
#     "region_x": selected_sprite_x,
#     "region_y": selected_sprite_y,
# }

# TODO: Rename this? I think this is for blob only

NONE_OR_BLOB_SPRITE_METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "x": {"type": "integer", "minimum": 0},
        "y": {"type": "integer", "minimum": 0},
        "region_x": {"type": "integer", "minimum": 0},
        "region_y": {"type": "integer", "minimum": 0},
    },
    "required": [
        "name",
        "x",
        "y",
        "region_x",
        "region_y",
    ],
}


# Dataclass for NONE_OR_BLOB_SPRITE_METADATA_SCHEMA, collision map item
@dataclass
class NoneOrBlobSpriteMetadata:
    name: str
    type: str
    x: int
    y: int
    region_x: int
    region_y: int


def instance_none_or_blob_sprite_metadata(input_dict: dict) -> NoneOrBlobSpriteMetadata:
    """
    Factory method, validates dict and returns instance dataclass version of it.

    Input = dict for collision map item.

    Output = NoneOrBlobSpriteMetadata.

    I Raise invalid sprite dict against schema exception.
    """

    # Validate first
    if not validate_json(input_dict, NONE_OR_BLOB_SPRITE_METADATA_SCHEMA):
        raise ValueError("Invalid sprite dict against schema")

    # If safe then create instance
    return NoneOrBlobSpriteMetadata(
        name=input_dict["name"],
        type=input_dict["type"],
        x=input_dict["x"],
        y=input_dict["y"],
        region_x=input_dict["region_x"],
        region_y=input_dict["region_y"],
    )


##########################
# ADJACENT TILE METADATA #
##########################

# Adjacent tile metadata is dict in room editor
# Created in the get adjacent tile helper private func
# It has
# Tile
# World coord x and y

# Todo:
# Validate on making in func
# Validate on receiving from func

# Example, inside the func _get_adjacent_tiles

# adjacent_tile_dict: dict = {
#     "tile": tile.name,
#     "world_tu_x": adjacent_x,
#     "world_tu_y": adjacent_y,
# }

ADJACENT_TILE_METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "tile": {"type": "string"},
        "world_tu_x": {"type": "integer", "minimum": 0},
        "world_tu_y": {"type": "integer", "minimum": 0},
    },
    "required": [
        "tile",
        "world_tu_x",
        "world_tu_y",
    ],
}


# Dataclass for ADJACENT_TILE_METADATA_SCHEMA, _get_adjacent_tiles func output
@dataclass
class AdjacentTileMetadata:
    tile: str
    world_tu_x: int
    world_tu_y: int


def instance_adjacent_tile_metadata(input_dict: dict) -> AdjacentTileMetadata:
    """
    Factory method, validates dict and returns instance dataclass version of it.

    Input = dict for _get_adjacent_tiles helper func output.

    Output = NoneOrBlobSpriteMetadata.

    I Raise invalid sprite dict against schema exception.
    """

    # Validate first
    if not validate_json(input_dict, ADJACENT_TILE_METADATA_SCHEMA):
        raise ValueError("Invalid sprite dict against schema")

    # If safe then create instance
    return AdjacentTileMetadata(
        tile=input_dict["tile"],
        world_tu_x=input_dict["world_tu_x"],
        world_tu_y=input_dict["world_tu_y"],
    )


def validate_json(input_dict: dict, schema: Any) -> bool:
    """
    Check if a dict is valid against a schema.

    Input: dict and schema.

    Output: boolean.
    """

    try:
        validate(instance=input_dict, schema=schema)
        return True
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        return False

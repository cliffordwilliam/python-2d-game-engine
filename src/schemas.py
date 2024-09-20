from dataclasses import dataclass
from typing import Any

from jsonschema import validate
from jsonschema import ValidationError

# Algo determine how dict access is either
# - some_dict.name
# - some_dict[self.name]

# Point is to stop doing some_dict["some_key"]
# And do some_dict.key with auto completion
# If you need some_dict["some_key"], then make a schema for it

# If no choice need to do some_dict[self.name]
# Use util set get

# Example
# PNGS_PATHS_DICT[self.sprite_sheet_png_name]
# Technically can do PNGS_PATHS_DICT.some_key
# But usage algo is not like that so use utils

# How schema works

# Protocol like how you get JSON response, then you instance a class to represent it
# So schema here to validate, then use their instance after successful validation
# Schema instance gives you autocompletion with its keys

######################
# ANIMATION METADATA #
######################

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
                    "items": ANIMATION_SPRITE_METADATA_SCHEMA,
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


@dataclass
class AnimationSpriteMetadata:
    x: int
    y: int


@dataclass
class AnimationMetadata:
    animation_is_loop: int
    next_animation_name: str
    animation_duration: int
    animation_sprite_height: int
    animation_sprite_width: int
    sprite_sheet_png_name: str
    animation_sprites_list: list[AnimationSpriteMetadata]


def instance_animation_metadata(input_dict: dict) -> dict[str, AnimationMetadata]:
    """
    | Input = animation JSON dict from disk.
    |
    | Validate input against schema.
    | I raise exception on invalid.
    |
    | Output = {animation name : AnimationMetadata dataclass instance}
    """

    # Validate against the schema
    if not validate_json(input_dict, ANIMATION_SCHEMA):
        raise ValueError("Invalid given animation dict against schema")

    # Prepare output {animation name : AnimationMetadata dataclass instance}
    out: dict[
        str,
        AnimationMetadata,
    ] = {}

    # Iter over each animation name and its metadata
    for animation_name, animation_metadata in input_dict.items():
        # Instance and populate each animation sprite members first
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

    # Return output
    return out


#########################
# SPRITE SHEET METADATA #
#########################

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

SPRITE_SHEET_METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "sprite_sheet_png_name": {"type": "string"},
        "sprite_room_map_body_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "sprite_room_map_sub_division_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "sprite_room_map_border_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
        "sprites_list": {
            "type": "array",
            "items": SPRITE_METADATA_SCHEMA,
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


@dataclass
class SpriteSheetMetadata:
    sprite_sheet_png_name: str
    sprite_room_map_body_color: str
    sprite_room_map_sub_division_color: str
    sprite_room_map_border_color: str
    sprites_list: list[SpriteMetadata]


def instance_sprite_sheet_metadata(input_dict: dict) -> SpriteSheetMetadata:
    """
    | Input = sprite sheet JSON dict from disk.
    |
    | Validate input against schema.
    | I raise exception on invalid.
    |
    | Output = SpriteSheetMetadata dataclass instance
    """

    # Validate against the schema
    if not validate_json(input_dict, SPRITE_SHEET_METADATA_SCHEMA):
        raise ValueError("Invalid sprite sheet dict against schema")
        # TODO: Do this later
        # raise ValueError("An exception has occured.")
        # File "path/to/file.extension", line number
        # See traceback.txt for details.

    # Construct the whole instance and return it
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
    | Input = sprite JSON dict from disk.
    |
    | Validate input against schema.
    | I raise exception on invalid.
    |
    | Output = SpriteMetadata dataclass instance
    """

    # Validate against the schema
    if not validate_json(input_dict, SPRITE_METADATA_SCHEMA):
        raise ValueError("Invalid sprite dict against schema")

    # Construct the whole instance and return it
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
# TODO: Update with set get, then re create dataclass instance
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
    | Input = object like dict item member in collision map list.
    |
    | Validate input against schema.
    | I raise exception on invalid.
    |
    | Output = NoneOrBlobSpriteMetadata dataclass instance
    """

    # Validate against the schema
    if not validate_json(input_dict, NONE_OR_BLOB_SPRITE_METADATA_SCHEMA):
        raise ValueError("Invalid sprite dict against schema")

    # Construct the whole instance and return it
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


@dataclass
class AdjacentTileMetadata:
    tile: str
    world_tu_x: int
    world_tu_y: int


def instance_adjacent_tile_metadata(input_dict: dict) -> AdjacentTileMetadata:
    """
    | Input = object like dict from _get_adjacent_tiles helper func output.
    |
    | Validate input against schema.
    | I raise exception on invalid.
    |
    | Output = AdjacentTileMetadata dataclass instance
    """

    # Validate against the schema
    if not validate_json(input_dict, ADJACENT_TILE_METADATA_SCHEMA):
        raise ValueError("Invalid sprite dict against schema")

    # Construct the whole instance and return it
    return AdjacentTileMetadata(
        tile=input_dict["tile"],
        world_tu_x=input_dict["world_tu_x"],
        world_tu_y=input_dict["world_tu_y"],
    )


def validate_json(input_dict: dict, schema: Any) -> bool:
    """
    | Validate input dict against schema.
    | Returns boolean.
    """

    try:
        validate(instance=input_dict, schema=schema)
        return True
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        return False

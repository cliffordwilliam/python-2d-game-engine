from dataclasses import dataclass
from typing import Any

from jsonschema import validate
from jsonschema import ValidationError

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


def instance_animation_metadata(data: dict) -> dict[str, AnimationMetadata]:
    # Validate the JSON data against the schema
    if not validate_json(data, ANIMATION_SCHEMA):
        raise ValueError("Invalid animation JSON data against schema")
    out: dict[str, AnimationMetadata] = {}
    # Animation name, animation metadata
    for animation_name, animation_metadata in data.items():
        # Extract and convert the sprite list
        sprites_list = [
            AnimationSpriteMetadata(x=sprite["x"], y=sprite["y"]) for sprite in animation_metadata["animation_sprites_list"]
        ]

        # Create and return an AnimationMetadata instance
        out[animation_name] = AnimationMetadata(
            animation_is_loop=animation_metadata["animation_is_loop"],
            next_animation_name=animation_metadata["next_animation_name"],
            animation_duration=animation_metadata["animation_duration"],
            animation_sprite_height=animation_metadata["animation_sprite_height"],
            animation_sprite_width=animation_metadata["animation_sprite_width"],
            sprite_sheet_png_name=animation_metadata["sprite_sheet_png_name"],
            animation_sprites_list=sprites_list,
        )
    return out


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

SPRITE_SHEET_SPRITES_LIST = {
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


def instance_sprite_sheet_metadata(data: dict) -> SpriteSheetMetadata:
    # Validate first
    if not validate_json(data, SPRITE_SHEET_METADATA_SCHEMA):
        raise ValueError("Invalid sprite sheet JSON against schema")

    # If safe then create instance
    return SpriteSheetMetadata(
        sprite_sheet_png_name=data["sprite_sheet_png_name"],
        sprite_room_map_body_color=data["sprite_room_map_body_color"],
        sprite_room_map_sub_division_color=data["sprite_room_map_sub_division_color"],
        sprite_room_map_border_color=data["sprite_room_map_border_color"],
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
            for sprite in data["sprites_list"]
        ],
    )


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


def validate_json(data: dict, schema: Any) -> bool:
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        return False

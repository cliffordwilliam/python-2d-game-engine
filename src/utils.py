from math import exp
from os import getenv
from os import listdir
from os import makedirs
from os.path import exists
from os.path import expanduser
from os.path import isfile
from os.path import join
from platform import system
from typing import Any

import pygame as pg
from schemas import NoneOrBlobSpriteMetadata
from schemas import validate_json


def create_paths_dict(directory: str) -> dict[str, str]:
    """
    Reads a dir.

    Loop over its content, get files only.
    Create a dict.

    Key is file name.

    Value is file path.
    """

    paths_dict = {}
    for filename in listdir(directory):
        if isfile(join(directory, filename)):
            paths_dict[filename] = join(directory, filename)
    return paths_dict


def get_os_specific_directory(app_name: Any) -> str:
    """
    Pass a dir name.

    Returns the dir full path to APPDATA or config and so on
    """

    user_home = expanduser("~")
    sys = system()

    # Set dir
    if sys == "Windows":
        appdata_path = getenv("APPDATA", user_home)
        directory = join(appdata_path, app_name)
    elif sys == "Darwin":  # macOS
        directory = join(user_home, "Library", "Application Support", app_name)
    else:  # Assume Linux or other Unix-like OS
        directory = join(user_home, ".config", app_name)

    # Dir does not exists?
    if not exists(directory):
        # Make dir
        makedirs(directory)

    # Return dir
    return directory


def overwriting_target_dict(new_dict: dict, target_dict: dict, target_dict_schema: Any) -> None:
    """
    Overwrite dict, need exact same shape.

    Do not use this on local settings dict.

    Use the game setter and getter method.
    """

    if not validate_json(new_dict, target_dict_schema):
        raise ValueError("Invalid new dict JSON against target dict schema")

    target_dict.update(new_dict)


def set_one_target_dict_value(key: Any, key_type: Any, val: Any, val_type: Any, target_dict: dict, target_dict_name: str) -> None:
    """
    | Set a value to non constant dict.
    |
    | Makes sure key type is correct.
    | Makes sure value type is correct.
    |
    | Raises exception on invalid key or values.
    """

    is_key_valid: bool = isinstance(key, key_type)
    is_val_valid: bool = isinstance(val, val_type)

    # Invalid key type?
    if not is_key_valid:
        # Raise exception
        raise KeyError(f"{key} type invalid for {target_dict_name}")

    # Invalid val type?
    if not is_val_valid:
        # Raise exception
        raise KeyError(f"{val} type invalid for {target_dict_name}")

    # Set the new value, no need to return mutable
    target_dict[key] = val


def get_one_target_dict_value(key: str, target_dict: dict, target_dict_name: str) -> Any:
    """
    | Get a value from non constant dict.
    |
    | Makes sure key exists.
    | No need to check if value type is correct.
    | Since it was validated before insertion.
    |
    | Raises exception on invalid key.
    """

    # Key not in target dict?
    if key not in target_dict:
        # Raise exception
        raise KeyError(f"{key} is not in {target_dict_name}")

    # Return value
    return target_dict[key]


def ray_vs_rect(
    ray_origin: pg.Vector2,
    ray_dir: pg.Vector2,
    target_rect: pg.FRect,
    contact_point: list[pg.Vector2],
    contact_normal: list[pg.Vector2],
    t_hit_near: list,
) -> bool:
    """
    True if light ray hits rect.

    Parameter needs ray origin, ray dir, target_rect.

    Need immutable list for extra info after computation.

    contact_point, contact_normal, t_hit_near.
    """

    # Cache division
    one_over_ray_dir_x: float = 0.0
    one_over_ray_dir_y: float = 0.0
    sign: float = -1.0

    # Handle infinity
    if abs(ray_dir.x) < 0.1:
        if ray_dir.x > 0:
            sign = 1.0
        one_over_ray_dir_x = float("inf") * sign
    else:
        one_over_ray_dir_x = 1 / ray_dir.x

    # Handle infinity
    if abs(ray_dir.y) < 0.1:
        if ray_dir.y > 0:
            sign = 1.0
        one_over_ray_dir_y = float("inf") * sign
    else:
        one_over_ray_dir_y = 1 / ray_dir.y

    # Get near far time
    t_near = pg.Vector2(
        (target_rect.x - ray_origin.x) * one_over_ray_dir_x,
        (target_rect.y - ray_origin.y) * one_over_ray_dir_y,
    )
    t_far = pg.Vector2(
        (target_rect.x + target_rect.width - ray_origin.x) * one_over_ray_dir_x,
        (target_rect.y + target_rect.height - ray_origin.y) * one_over_ray_dir_y,
    )

    # Sort near far time
    if t_near.x > t_far.x:
        t_near.x, t_far.x = t_far.x, t_near.x
    if t_near.y > t_far.y:
        t_near.y, t_far.y = t_far.y, t_near.y

    # COLLISION RULE
    if t_near.x > t_far.y or t_near.y > t_far.x:
        return False

    # Get near far time
    t_hit_near[0] = max(t_near.x, t_near.y)
    t_hit_far: float = min(t_far.x, t_far.y)

    if t_hit_far < 0:
        return False

    # Compute contact point
    contact_point[0] = ray_origin + t_hit_near[0] * ray_dir

    # Compute contact normal
    if t_near.x > t_near.y:
        contact_normal[0].x, contact_normal[0].y = (1, 0) if ray_dir.x < 0 else (-1, 0)
    elif t_near.x < t_near.y:
        contact_normal[0].x, contact_normal[0].y = (0, 1) if ray_dir.y < 0 else (0, -1)

    return True


def dynamic_rect_vs_rect(
    input_velocity: pg.Vector2,
    collider_rect: pg.FRect,
    target_rect: pg.FRect,
    contact_point: list[pg.Vector2],
    contact_normal: list[pg.Vector2],
    t_hit_near: list[float],
    dt: int,
) -> bool:
    """
    If dynamic actor is not moving, returns False.
    """
    if input_velocity.x == 0 and input_velocity.y == 0:
        return False
    expanded_target: pg.FRect = pg.FRect(
        target_rect.x - collider_rect.width / 2,
        target_rect.y - collider_rect.height / 2,
        target_rect.width + collider_rect.width,
        target_rect.height + collider_rect.height,
    )
    hit = ray_vs_rect(
        pg.Vector2(
            collider_rect.x + collider_rect.width / 2,
            collider_rect.y + collider_rect.height / 2,
        ),
        input_velocity * dt,
        expanded_target,
        contact_point,
        contact_normal,
        t_hit_near,
    )
    if hit:
        return t_hit_near[0] >= 0.0 and t_hit_near[0] < 1.0
    else:
        return False


def exp_decay(a: float, b: float, decay: float, dt: int) -> float:
    return b + (a - b) * exp(-decay * dt)


def get_tile_from_collision_map_list(
    world_tu_x: int,
    world_tu_y: int,
    room_width_tu: int,
    room_height_tu: int,
    collision_map_list: list,
) -> Any | int | NoneOrBlobSpriteMetadata:
    """
    Returns -1 if out of bounds.

    Because camera needs extra 1 and thus may get out of bound.
    """
    if 0 <= world_tu_x < room_width_tu and 0 <= world_tu_y < room_height_tu:
        return collision_map_list[world_tu_y * room_width_tu + world_tu_x]
    else:
        return -1

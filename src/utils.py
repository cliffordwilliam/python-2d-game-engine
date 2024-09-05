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

from constants import pg
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


def set_one_target_dict_value(key: str, value: Any, target_dict: dict, target_dict_schema: Any) -> None:
    """
    Set a value to local settings dict. Need to be same type. For POST and PATCH.
    Do not use this on local settings dict.
    Use the game setter and getter method.
    """

    # Set the new value
    target_dict[key] = value

    if not validate_json(target_dict, target_dict_schema):
        raise ValueError("Invalid new dict JSON against target dict schema")


def get_one_target_dict_value(key: str, target_dict: dict) -> Any:
    """
    Get a value from local settings dict.
    Do not use this on local settings dict.
    Use the game setter and getter method.
    """

    # Check if the key exists in the target_dict
    if key not in target_dict:
        raise KeyError(f"Invalid key: '{key}'")

    # Return the value for the key
    return target_dict.get(key, None)


def point_vs_rect(p: pg.Vector2, r: pg.FRect) -> bool:
    """
    True if point in a rect.
    Parameter needs a point and a rect.
    """
    return p.x >= r.x and p.y >= r.y and p.x < r.x + r.width and p.y < r.y + r.height


def rect_vs_rect(r1: pg.FRect, r2: pg.FRect) -> bool:
    """
    True if rect in a rect. Needs to overlap.
    Parameter needs a rect and a rect.
    """
    return r1.x < r2.x + r2.width and r1.x + r1.width > r2.x and r1.y < r2.y + r2.height and r1.y + r1.height > r2.y


def ray_vs_rect(
    ray_origin: pg.Vector2,
    ray_dir: pg.Vector2,
    target: pg.FRect,
    contact_point: list[pg.Vector2],
    contact_normal: list[pg.Vector2],
    t_hit_near: list,
) -> bool:
    """
    True if light ray hits rect.
    Parameter needs ray origin, ray dir, target rect
    Need immutable list for extra info after computation.
    contact_point, contact_normal, t_hit_near
    """
    if ray_dir.y == 0 or ray_dir.x == 0:
        return False
    # TODO: Cache division?
    t_near = pg.Vector2((target.x - ray_origin.x) / ray_dir.x, (target.y - ray_origin.y) / ray_dir.y)
    t_far = pg.Vector2(
        (target.x + target.width - ray_origin.x) / ray_dir.x, (target.y + target.height - ray_origin.y) / ray_dir.y
    )

    if t_near.x > t_far.x:
        t_near.x, t_far.x = t_far.x, t_near.x
    if t_near.y > t_far.y:
        t_near.y, t_far.y = t_far.y, t_near.y

    if t_near.x > t_far.y or t_near.y > t_far.x:
        return False

    t_hit_near[0] = max(t_near.x, t_near.y)
    t_hit_far: float = min(t_far.x, t_far.y)

    if t_hit_far < 0:
        return False

    contact_point[0] = ray_origin + t_hit_near[0] * ray_dir

    if t_near.x > t_near.y:
        contact_normal[0].x, contact_normal[0].y = (1, 0) if ray_dir.x < 0 else (-1, 0)
    elif t_near.x < t_near.y:
        contact_normal[0].x, contact_normal[0].y = (0, 1) if ray_dir.y < 0 else (0, -1)

    return True


def dynamic_rect_vs_rect(
    dynamic_actor: Any,
    target: pg.FRect,
    contact_point: list[pg.Vector2],
    contact_normal: list[pg.Vector2],
    t_hit_near: list[float],
    dt: int,
) -> bool:
    if dynamic_actor.velocity.x == 0 and dynamic_actor.velocity.y == 0:
        return False
    expanded_target: pg.FRect = pg.FRect(
        target.x - dynamic_actor.rect.width / 2,
        target.y - dynamic_actor.rect.height / 2,
        target.width + dynamic_actor.rect.width,
        target.height + dynamic_actor.rect.height,
    )
    hit = ray_vs_rect(
        pg.Vector2(
            dynamic_actor.rect.x + dynamic_actor.rect.width / 2,
            dynamic_actor.rect.y + dynamic_actor.rect.height / 2,
        ),
        dynamic_actor.velocity * dt,
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

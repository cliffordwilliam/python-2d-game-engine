from os import getenv
from os import listdir
from os import makedirs
from os.path import exists
from os.path import expanduser
from os.path import isfile
from os.path import join
from platform import system
from typing import Any


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


# TODO: Use this in other json other than the settings dict, like editors
# TODO: Make a post too
# TODO: Do not check type, check the shape, cuz dict val can be another dict
def overwriting_target_dict(new_dict: dict, target_dict: dict) -> None:
    """
    Overwrite dict, need exact same shape.
    Do not use this on local settings dict.
    Use the game setter and getter method.
    """

    # Ensure that all required keys are present
    for key in target_dict:
        if key not in new_dict:
            raise KeyError(f"Missing required key: '{key}'")

    # Ensure that no extra keys are present
    for key in new_dict:
        if key not in target_dict:
            raise KeyError(f"Invalid key: '{key}'")

    # Ensure that the new dictionary has valid values
    for key, value in new_dict.items():
        # Get the expected type from target_dict
        expected_type = type(target_dict[key])

        # Check if the value matches the expected type
        if not isinstance(value, expected_type):
            raise TypeError(f"Key '{key}' expects a value of type {expected_type.__name__}, but got {type(value).__name__}.")

    # If all checks pass, overwrite the current settings
    target_dict.update(new_dict)


def set_one_target_dict_value(key: str, value: Any, target_dict: dict) -> None:
    """
    Set a value to local settings dict. Need to be same type.
    Do not use this on local settings dict.
    Use the game setter and getter method.
    """

    # Check if the key exists in the target_dict
    if key not in target_dict:
        raise KeyError(f"Invalid key: '{key}'")

    # Get the expected type from target_dict
    expected_type = type(target_dict[key])

    # Check if the value matches the expected type
    if not isinstance(value, expected_type):
        raise TypeError(f"Key '{key}' expects a value of type {expected_type.__name__}, but got {type(value).__name__}.")

    # Set the new value
    target_dict[key] = value


def get_one_target_dict_value(key: str, target_dict: dict) -> Any:
    """
    Get a value from local settings dict.
    Do not use this on local settings dict.
    Use the game setter and getter method.
    """

    # Check if the key exists in the target_dict
    if key not in target_dict:
        # TODO: Do not crash the app, return None
        raise KeyError(f"Invalid key: '{key}'")

    # Return the value for the key
    return target_dict.get(key, None)

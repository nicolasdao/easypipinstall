import sys
import re
import os
import subprocess

SETUP_FILE = "setup.cfg"
SUPPORTED_COMMANDS = ["show", "bump"]
SUPPORTED_VERSION_BITS = ["patch", "minor", "major"]


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"  # yellow
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def version(*args):
    if not (len(args)):
        # Gets the terminal inputs
        _, *args = sys.argv

    command, param, *_ = list(args) + [None, None]
    command = "show" if command is None else command

    if command not in SUPPORTED_COMMANDS:
        print(f"{bcolors.WARNING}Command '{command}' is not supported.{bcolors.ENDC}")
        exit()

    if command == "show":
        show()
    else:
        bump(param if param else "patch")


def show():
    v = _get_version()
    if v is not None:
        print(v)
    return v


def bump(version="patch"):
    version = f"{version}".strip()
    new_version = None
    v = _get_version()
    major, minor, patch = _parse_version(v)
    if major is None:
        print(
            f"{bcolors.FAIL}Error: Incorrect or missing 'version' property in file '{SETUP_FILE}'.{bcolors.ENDC}"
        )
        exit()

    if version == "patch":
        new_version = f"{major}.{minor}.{patch+1}"
    elif version == "minor":
        new_version = f"{major}.{minor+1}.0"
    elif version == "major":
        new_version = f"{major+1}.0.0"
    else:
        new_major, new_minor, new_patch = _parse_version(version)
        if new_major is None:
            print(
                f"{bcolors.FAIL}Error: Invalid 'version' input. When 'version' is not one of the allowed shortcut (i.e., 'patch', 'minor' or 'major'), it must be an explicit semver version number. Found '{version}' instead.{bcolors.ENDC}"
            )
            exit()
        if new_major < major or (
            new_major == major
            and (new_minor < minor or (new_minor == minor and new_patch < patch))
        ):
            print(
                f"{bcolors.FAIL}Error: Invalid 'version' input. The new version ({version}) cannot be smaller than the current version ({v}).{bcolors.ENDC}"
            )
            exit()
        new_version = f"{new_major}.{new_minor}.{new_patch}"

    # _update_setup_file_version(new_version)
    if _is_git():
        _update_changelog(old_version=v, new_version=new_version)


def _update_changelog(old_version, new_version):
    git_status_out = subprocess.check_output(("git", "log", f"v{old_version}..head")).decode("UTF-8")


def _is_git():
    try:
        # Check if git is installed
        exist_command, not_found_text = (
            ["where", r"ould not find"]
            if os.name == "Windows"
            else ["which", r"not found"]
        )
        which_out = subprocess.check_output((exist_command, "git")).decode("UTF-8")
        if re.search(not_found_text, f"{which_out}"):
            return False

        # Check if this project if under source control
        git_status_out = subprocess.check_output(("git", "status")).decode("UTF-8")
        if re.search(r"not a git repository", f"{git_status_out}"):
            return False

        return True
    except:
        return False


def _update_setup_file_version(version):
    try:
        major, *_ = _parse_version(version)
        if major is None:
            raise Exception(f"Invalid version value ({version}).")

        updated_content = ""
        with open(SETUP_FILE, "r") as setup_file:
            updated_content = setup_file.read()
            updated_content = re.sub(
                r"version\s*=(.*?)\n", f"version = {version}\n", updated_content, 1
            )
        with open(SETUP_FILE, "w") as setup_file:
            setup_file.write(updated_content)
    except Exception as e:
        print(
            f"{bcolors.FAIL}Error: Failed to update the version in {SETUP_FILE}. Details:{bcolors.ENDC}"
        )
        print(f"{bcolors.FAIL}{e}{bcolors.ENDC}")
        exit()


def _get_version():
    v = None
    if os.path.exists(SETUP_FILE):
        with open(SETUP_FILE, "r") as setup_file:
            content = setup_file.read()
            version, *_ = re.findall(r"version\s*=\s*(.*?)\n", content) + [None]
            v = version.strip() if version is not None else None
    else:
        print(
            f"{bcolors.FAIL}'version' not found. Missing required file '{SETUP_FILE}'.{bcolors.ENDC}"
        )
        exit()

    return v


def _parse_version(version):
    if version is None or version == "":
        return None

    v = f"{version}"
    v, *_ = re.findall(r"[0-9]+\.[0-9]+\.[0-9]+", v) + [""]
    parts = v.split(".")
    if len(parts) != 3:
        return [None, None, None]
    else:
        major, minor, patch = parts
        return [int(major), int(minor), int(patch)]

import sys
import re
import os
import subprocess
from datetime import datetime

SETUP_FILE = "setup.cfg"
CHANGELOG = "CHANGELOG.md"
SUPPORTED_COMMANDS = ["show", "bump"]
SUPPORTED_VERSION_BITS = ["patch", "minor", "major"]
CHANGELOG_HEADER = """# Changelog

All notable changes to this project will be documented in this file. 

"""
DEFAULT_CHANGELOG_START_LINE = 4


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
    command = "show" if (not command) or (command is None) else command

    if command not in SUPPORTED_COMMANDS:
        print(f"{bcolors.WARNING}Command '{command}' is not supported.{bcolors.ENDC}")
        exit()

    if command == "show":
        show()
    else:
        bump(param if param else "patch")


def show():
    v = _get_setup_cfg_version()
    if v is not None:
        print(v)
    return v


def bump(version="patch"):
    version = f"{version}".strip()
    new_version = None
    v = _get_setup_cfg_version()
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
        if not _is_new_version_strictly_greater(
            f"{major}.{minor}.{patch}", f"{new_major}.{new_minor}.{new_patch}"
        ):
            print(
                f"{bcolors.FAIL}Error: Invalid 'version' input. The new version ({version}) cannot be smaller than the current version ({v}).{bcolors.ENDC}"
            )
            exit()
        new_version = f"{new_major}.{new_minor}.{new_patch}"

    _update_setup_file_version(new_version)
    if _is_git():
        _update_changelog(old_version=v, new_version=new_version)
        _tag_project(new_version)

    print(
        f"{bcolors.OKGREEN}Project successfully versionned, tagged and documented in {CHANGELOG}.{bcolors.ENDC}"
    )


def _tag_project(version):
    msg = f"v{version}"
    subprocess.check_output(("git", "add", "--all")).decode("UTF-8")
    subprocess.check_output(("git", "commit", "-am", msg)).decode("UTF-8")
    subprocess.check_output(("git", "tag", "-a", msg, "-m", msg)).decode("UTF-8")


def _is_new_version_strictly_greater(old_version, new_version):
    major, minor, patch = _parse_version(old_version)
    new_major, new_minor, new_patch = _parse_version(new_version)
    if major is None or new_major is None:
        return False
    elif new_major < major or (
        new_major == major
        and (new_minor < minor or (new_minor == minor and new_patch <= patch))
    ):
        return False
    else:
        return True


def _update_changelog(old_version, new_version):
    """
    Mutates the CHANGELOG.md file as follow:
      - Create a new title using the `new_version` and linking it to its diff with the previous tag (which should be 'v{old_version}').
      - Under that new title, document all the feature, bug fixes and documentation changes (ignore the other types such as chore). For each change, add a link to their commit using the commit hash.

    Args:
        - old_version (str): version maintained in the setup.cfg (e.g., '0.1.6').
        - new_version (str): New version entered via the CLI (e.g., '2.0.0').

    Returns:
        void
    """
    commits = _get_latest_commits(old_version)
    _update_changelog_file(
        old_version=old_version, new_version=new_version, commits=commits
    )


def _check_tag_exists(tag):
    try:
        out = subprocess.check_output(("git", "tag", "-l", tag)).decode("UTF-8")
        i = re.split(os.linesep, f"{out}").index(tag)
        return i >= 0
    except:
        return False


def _update_changelog_file(old_version, new_version, commits):
    """
    Returns a dictionary containing information about a user.

    Args:
        - old_version (str): version maintained in the setup.cfg (e.g., '0.1.6').
        - new_version (str): New version entered via the CLI (e.g., '2.0.0').
        - commits (list<dict>):
          - 'commit' (str): Commit message
          - 'type' (str): Valid values: 'feat', 'doc', 'fix', 'chore', 'refactor', 'test', 'config', 'style'
          - 'hash' (str): Short commit hash.

    Returns:
        dict: A dictionary containing the following keys:
            - 'name' (str): The user's name.
            - 'age' (int): The user's age.
            - 'email' (str): The user's email address.
            - 'address' (dict): A dictionary containing the user's address, with the following keys:
                - 'street' (str): The user's street address.
                - 'city' (str): The user's city.
                - 'state' (str): The user's state.
                - 'zip' (str): The user's zip code.
    """

    # If CHANGELOG.md does not exist yet, create it.
    if not os.path.exists(CHANGELOG):
        with open(CHANGELOG, "a+") as file:
            file.write(CHANGELOG_HEADER)

    with open(CHANGELOG, "r+") as file:
        content = file.read()
        file.seek(0, 0)
        lines = re.split(os.linesep, content)
        last_version = None
        last_version_idx = None
        for idx, line in enumerate(lines):
            last_version, *_ = re.findall(r"^#+\s\[[0-9]+.[0-9]+.[0-9]+\]", line) + [
                None
            ]
            if last_version is not None:
                last_version = re.sub(r"[^0-9.]", "", last_version)
                last_version_idx = idx
                break

        skip = (last_version is not None) and (
            not _is_new_version_strictly_greater(last_version, new_version)
        )
        if skip:
            file.write(content)
        else:
            previously_tagged_version = (
                old_version if last_version is None else last_version
            )
            previously_tagged_version_exists = _check_tag_exists(
                f"v{previously_tagged_version}"
            )
            if (not previously_tagged_version_exists) and old_version:
                previously_tagged_version_exists = _check_tag_exists(f"v{old_version}")
                if previously_tagged_version_exists:
                    previously_tagged_version = old_version

            if not previously_tagged_version_exists:
                previously_tagged_version = None

            new_content = _create_changelog_section(
                previously_tagged_version=previously_tagged_version,
                version=new_version,
                commits=commits,
            )
            if (not new_content) or (new_content is None):
                file.write(content)
            else:
                lines.insert(
                    DEFAULT_CHANGELOG_START_LINE
                    if last_version_idx is None
                    else last_version_idx,
                    new_content,
                )
                file.write(os.linesep.join(lines))


def _create_changelog_section(previously_tagged_version, version, commits):
    git_remote_url = subprocess.check_output(
        ("git", "remote", "get-url", "origin")
    ).decode("UTF-8")
    git_remote_url = re.sub(r"\.git$", "", f"{git_remote_url}".strip())
    if re.search(r"o such remote", git_remote_url):
        return None
    else:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        pathname, diff_range = (
            ["tree", f"v{version}"]
            if (not previously_tagged_version) or (previously_tagged_version is None)
            else ["compare", f"v{previously_tagged_version}...v{version}"]
        )
        version_title = (
            f"## [{version}]({git_remote_url}/{pathname}/{diff_range}) ({date_str})"
        )

        lines = [
            version_title,
            "",
        ]

        feat_lines = [
            f"- {x['commit']} ([{x['hash']}]({git_remote_url}/commit/{x['hash']}))"
            for x in commits
            if x and x["type"] == "feat"
        ]
        fix_lines = [
            f"- {x['commit']} ([{x['hash']}]({git_remote_url}/commit/{x['hash']}))"
            for x in commits
            if x and x["type"] == "fix"
        ]
        doc_lines = [
            f"- {x['commit']} ([{x['hash']}]({git_remote_url}/commit/{x['hash']}))"
            for x in commits
            if x and x["type"] == "doc"
        ]

        if len(feat_lines) > 0:
            lines.extend(["### Features", ""])
            lines.extend(feat_lines)
            lines.append("")
        if len(fix_lines) > 0:
            lines.extend(["### Bug fixes", ""])
            lines.extend(fix_lines)
            lines.append("")
        if len(doc_lines) > 0:
            lines.extend(["### Documentation", ""])
            lines.extend(doc_lines)
            lines.append("")

        lines.append("")

        return os.linesep.join(lines)


def _get_latest_commits(old_version):
    commits_str = subprocess.check_output(
        ("git", "log", f"v{old_version}..head", "--oneline")
    ).decode("UTF-8")
    old_version_not_tagged = re.search("unknown revision or path", f"{commits_str}")

    if old_version_not_tagged:
        commits_str = subprocess.check_output(
            ("git", "log", "-20", "--oneline")
        ).decode("UTF-8")
        no_commits_str_yet = re.search(
            "does not have any commits_str yet", f"{commits_str}"
        )
        if no_commits_str_yet:
            commits_str = ""

    commits = []
    for x in re.split(os.linesep, commits_str):
        if x:
            hash_key, *_ = re.findall(r"^.{7}", x.strip()) + [""]
            commit = re.sub(r"^.{8}(\((.*?)\)\s){0,1}", "", x).strip()
            _type = None
            if re.search(r"^feat", commit):
                _type = "feat"
                commit = re.sub(r"^feat:\s*", "", commit)
            elif re.search(r"^doc", commit):
                _type = "doc"
                commit = re.sub(r"^doc:\s*", "", commit)
                commit = re.sub(r"^docs:\s*", "", commit)
            elif re.search(r"^fix", commit):
                _type = "fix"
                commit = re.sub(r"^fix", "", commit)
                commit = re.sub(r"^:", "", commit)
                commit = commit.strip()
            elif re.search(r"^refactor", commit):
                _type = "refactor"
                commit = re.sub(r"^refactor:\s*", "", commit)
            elif re.search(r"^test", commit):
                _type = "test"
                commit = re.sub(r"^test:\s*", "", commit)
            elif re.search(r"^chore", commit):
                _type = "chore"
                commit = re.sub(r"^chore:\s*", "", commit)
            elif re.search(r"^config", commit):
                _type = "config"
                commit = re.sub(r"^config:\s*", "", commit)
            elif re.search(r"^style", commit):
                _type = "style"
                commit = re.sub(r"^style:\s*", "", commit)

            if _type is not None:
                commits.append({"commit": commit, "type": _type, "hash": hash_key})

    return commits


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
                rf"version\s*=(.*?){os.linesep}",
                f"version = {version}{os.linesep}",
                updated_content,
                1,
            )
        with open(SETUP_FILE, "w") as setup_file:
            setup_file.write(updated_content)
    except Exception as e:
        print(
            f"{bcolors.FAIL}Error: Failed to update the version in {SETUP_FILE}. Details:{bcolors.ENDC}"
        )
        print(f"{bcolors.FAIL}{e}{bcolors.ENDC}")
        exit()


def _get_setup_cfg_version():
    v = None
    if os.path.exists(SETUP_FILE):
        with open(SETUP_FILE, "r") as setup_file:
            content = setup_file.read()
            version, *_ = re.findall(rf"version\s*=\s*(.*?){os.linesep}", content) + [
                None
            ]
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

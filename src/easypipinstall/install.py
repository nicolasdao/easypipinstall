import configparser
import sys
import subprocess
import re
import os
from functools import partial
import importlib

# Defines constants
SETUP_FILE = "setup.cfg"
LIB_COMPARATOR_REGEX = r"[>=<\n\s,]"
GLOBAL_REQUIREMENTS = "requirements.txt"
PROD_REQUIREMENTS = "prod-requirements.txt"
PROD_SECTION = "options"
PROD_SECTION_REQUIRE = "install_requires"
DEV_SECTION = "options.extras_require"
DEV_SECTION_REQUIRE = "dev"


def getItems(s=""):
    """Gets the unique items in a list where the separator is a new line"""
    if not s:
        return ([], [])
    items = list(set(x for x in re.split("\n", s) if x))
    names = [getLibNameOnly(x) for x in items]
    return (items, names)


def freeze():
    with open(GLOBAL_REQUIREMENTS, "w") as f:
        f.write(subprocess.check_output(("pip", "freeze")).decode("UTF-8"))


def getConfig(config, section, property):
    val = (
        ""
        if section not in config or property not in config[section]
        else config[section][property]
    )
    val = val if val else ""
    return val


def initConfig(config, section, property):
    """Makes sure that config[section][property] exists."""
    if section not in config:
        config[section] = {}
    if property not in config[section]:
        config[section][property] = ""


def find(val, items):
    return next((x for x in items if val in x), None)


def getLibNameOnly(lib=""):
    return [x for x in re.split(LIB_COMPARATOR_REGEX, lib) if x][0].strip()


def getPackageDeps(lib):
    """Gets a package's dependencies withouth their versions"""
    try:
        pkg_resources = importlib.import_module("pip._vendor.pkg_resources")
        _package = pkg_resources.working_set.by_key[lib]
        return [getLibNameOnly(str(r)) for r in _package.requires()]
    except BaseException as error:
        print(
            f"\033[93mWARNING: Failed to extract dependencies for lib {lib}. Details: {type(error).__name__}: {str(error)}\033[0m"
        )
        return []


def pip_install(lib, dev=False):
    """
    Installs library 'lib' and freeze the dependencies into requirements.txt
    and prod-requirements.txt (if the dev mode is not on). The strategy used to
    install the new dependencies in prod mode is as follow:
    1.	Gets all the dependencies (incl. the lib itself).
    2.	Add or update those dependencies in prod-requirements.txt.

            Parameters:
                    lib (string):	e.g., 'numpy' or 'flake8==6.0.0'.
                    dev (boolean):	Default False. When False, the prod-requirements.txt is also updated.
    """
    subprocess.check_call(["pip", "install", lib])
    freeze()
    if not dev:
        requirements = getFileContent(GLOBAL_REQUIREMENTS)
        print(requirements)
        deps = getExactDeps(requirements, lib)
        if len(deps):
            with open(PROD_REQUIREMENTS, "w") as pfile:
                prodRequirements = getFileContent(PROD_REQUIREMENTS)
                prodDeps, prodNames = getItems(prodRequirements)
                for dependency in deps:
                    libName = getLibNameOnly(dependency)
                    if libName not in prodNames:
                        prodDeps.append(dependency)
                    else:
                        prodDeps[prodNames.index(libName)] = dependency
                prodDeps = list(set(prodDeps))
                prodDeps.sort()
                pfile.write("\n".join(prodDeps))


def pip_uninstall(lib):
    """
    Uninstalls library 'lib' and freeze the dependencies in both requirements.txt and prod-requirements.txt.
    The strategy used to uninstall the dependencies in prod mode is as follow:
    1.	Check which dependencies were removed from requirements.txt. It's safer to do that rather than
            checking the lib's dependencies explicitly, as some shared dependencies may not have been removed.
    2.	Remove the dependencies from prod-requirements.txt.

            Parameters:
                    lib (string):	e.g., 'numpy' or 'flake8==6.0.0'.
    """
    oldRequirements = getFileContent(GLOBAL_REQUIREMENTS)
    uninstallDeps = getIsolatedDeps(lib)
    if not len(uninstallDeps):
        return

    for dep in uninstallDeps:
        subprocess.check_call(["pip", "uninstall", dep, "-y"])

    freeze()
    newRequirements = getFileContent(GLOBAL_REQUIREMENTS)
    deletedLines = getDeletedLines(oldRequirements, newRequirements)
    if len(deletedLines):
        with open(PROD_REQUIREMENTS, "w") as pfile:
            oldProdRequirements = getFileContent(PROD_REQUIREMENTS)
            prodLines = oldProdRequirements.split("\n")
            newProdLines = []
            for line in prodLines:
                if line not in deletedLines:
                    newProdLines.append(line)
            newProdLines = list(set(newProdLines))
            newProdLines.sort()
            pfile.write("\n".join(newProdLines))


def getIsolatedDeps(lib):
    """Gets lib's dependencies that are only used by lib any nobody else in the requirements.txt"""
    libName = getLibNameOnly(lib)
    requirements = getFileContent(GLOBAL_REQUIREMENTS)
    # Gets lib's dependencies
    depNames = [
        getLibNameOnly(x) for x in getExactDeps(requirements, libName, recursive=True)
    ]
    # Gets all the dependencies listed in requirements.txt
    _, prodNames = getItems(requirements)
    # Loops through all the dependencies listed in requirements.txt to get all their dependencies
    for prodName in prodNames:
        if libName != prodName:
            prodDepNames = [
                getLibNameOnly(x)
                for x in getExactDeps(requirements, prodName, recursive=True)
            ]
            for n in prodDepNames:
                if n in depNames and n != libName and n != prodName:
                    depNames.remove(n)
    return depNames


def getFileContent(file):
    content = ""
    if not file:
        return content

    if os.path.exists(file):
        with open(file) as f:
            content = f.read()

    return content


def getDiffLines(oldContent="", newContent="", mode="new"):
    oldLines = oldContent.split("\n")
    newLines = newContent.split("\n")
    lines = []
    ls1, ls2 = (newLines, oldLines) if mode == "new" else (oldLines, newLines)
    for line in ls1:
        if line not in ls2:
            lines.append(line)
    return lines


def getExactDeps(requirementsContent, lib, recursive=False, skipDeps=[]):
    requirements = requirementsContent.split("\n")
    deps = getPackageDeps(lib)
    libName = getLibNameOnly(lib)
    deps.append(libName)
    exactDeps = []
    findDeps = partial(find, items=requirements)
    for dep in deps:
        if dep not in skipDeps:
            fullName = findDeps(dep)
            if fullName:
                exactDeps.append(fullName)

    if recursive:
        nested = [*exactDeps]
        nestedNames = [getLibNameOnly(x) for x in exactDeps]
        for dep in nestedNames:
            if dep not in skipDeps and dep != libName:
                nested.extend(
                    getExactDeps(requirementsContent, dep, recursive, nestedNames)
                )
        exactDeps = nested

    exactDeps = list(set(exactDeps))
    exactDeps.sort()
    return exactDeps


getNewLines = partial(getDiffLines, mode="new")
getDeletedLines = partial(getDiffLines, mode="deleted")


def main(mode="install"):
    """Main program"""
    # Reads the 'setup.cfg' file

    # Gets the terminal inputs
    _, *libs = sys.argv

    # Exists if no inputs were provided
    if not (len(libs)):
        exit()

    # Filters the inputs between libraries and options (e.g., -D for dev dependencies)
    libDefs = []
    options = []
    for lib in libs:
        tar = options if re.search(r"^-", lib) else libDefs
        tar.append(lib)

    config = configparser.ConfigParser()
    config.read(SETUP_FILE)
    dev = "-D" in options
    prodDeps, prodNames = getItems(
        getConfig(config, PROD_SECTION, PROD_SECTION_REQUIRE)
    )
    devDeps, devNames = getItems(getConfig(config, DEV_SECTION, DEV_SECTION_REQUIRE))

    prodChanged = False
    devChanged = False
    for lib in libDefs:
        # Gets the library that must be installed without its version
        name = getLibNameOnly(lib)
        cleanName = re.sub(r",\s*$", "", lib)
        if not name:
            continue

        existingProdName = find(name, prodDeps)
        existingDevName = find(name, devDeps)

        if mode != "install":
            if existingProdName:
                prodChanged = True
                prodDeps.remove(existingProdName)
            if existingDevName:
                devChanged = True
                devDeps.remove(existingDevName)
            pip_uninstall(name)
        else:
            if existingProdName or existingDevName:
                pass
            if dev:
                if existingDevName or existingProdName:
                    pass
                else:
                    devChanged = True
                    devDeps.append(cleanName)
            else:
                if existingProdName:
                    pass
                else:
                    if existingDevName:
                        # If the dep is already in dev, remove it from there and add it to prod
                        devChanged = True
                        devDeps.remove(existingDevName)
                        pip_uninstall(name)

                    prodChanged = True
                    prodDeps.append(cleanName)
            pip_install(lib, dev)

    if prodChanged:
        initConfig(config, PROD_SECTION, PROD_SECTION_REQUIRE)
        if len(prodDeps):
            prodDeps.sort()
            config[PROD_SECTION][PROD_SECTION_REQUIRE] = "\n" + "\n".join(prodDeps)
        else:
            del config[PROD_SECTION][PROD_SECTION_REQUIRE]
    if devChanged:
        initConfig(config, DEV_SECTION, DEV_SECTION_REQUIRE)
        if len(devDeps):
            devDeps.sort()
            config[DEV_SECTION][DEV_SECTION_REQUIRE] = "\n" + "\n".join(devDeps)
        else:
            del config[DEV_SECTION][DEV_SECTION_REQUIRE]

    with open(SETUP_FILE, "w") as configfile:
        config.write(configfile)


install = partial(main, mode="install")
uninstall = partial(main, mode="uninstall")

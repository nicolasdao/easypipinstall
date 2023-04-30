# EASY PIP INSTALL

`easypipinstall` is a dev utility that helps installing Python packages similarly to NPM in NodeJS. It automatically maintains the `requirements.txt`, `prod-requirements.txt` and `setup.cfg` files. It also easily uninstalls all the dependencies from those files. It uses an opinionated pattern where:
- Only two types of dependencies exist: `dev` (via requirements.txt) and `prod` (via prod-requirements.txt, which is a subset of requirements.txt).
- All dependencies are listed under `requirements.txt`.
- By default, dependencies are listed in both `requirements.txt` and `prod-requirements.txt`.
- Dependencies are not listed under `prod-requirements.txt` when the `-D` option (development mode) is used. 
- The `setup.cfg` file is updated as follows:
	- By default, the dependency is listed without its version under the `install_requires` property of the `[options]` section.
	- When the `-D` option is used, the dependency is listed without its version under the `dev` property of the `[options.extras_require]` section.

To install:
```
pip install easypipinstall
```

This will add three new CLI utilities: 
1. [`easyi` (install)](#easyi-to-install)
2. [`easyu` (uninstall)](#easyu-to-uninstall)
3. [`easyv` (version)](#easyv-to-version)

Examples:
```shell
easyi numpy
```

This installs `numpy` (via `pip install`) then automatically updates the following files:
- `setup.cfg` (WARNING: this file must already exists):
	```
	[options]
	install_requires = 
		numpy
	```
- `requirements.txt` and `prod-requirements.txt`

```shell
easyi flake8 black -D
```

This installs `flake8` and `black` (via `pip install`) and then automatically updates the following files:
- `setup.cfg` (WARNING: this file must already exist):
	```
	[options.extras_require]
	dev = 
		black
		flake8
	```
- `requirements.txt` only, as those dependencies are installed for development purposes only.

```shell
easyu flake8
```

This uninstalls `flake8` as well as all its dependencies. Those dependencies are uninstalled only if other project dependencies do not use them. The `setup.cfg` and `requirements.txt` are automatically updated.


# Table of contents

> * [APIs](#apis)
>	- [`easyi` to install](#easyi-to-install)
>	- [`easyu` to uninstall](#easyu-to-uninstall)
>	- [`easyv` to version](#easyv-to-version)
> * [Dev](#dev)
>	- [Getting started](#dev---getting-started)
>	- [CLI commands](#cli-commands)
>	- [Linting, formatting and testing](#linting-formatting-and-testing)
>		- [Ignoring `flake8` errors](#ignoring-flake8-errors)
>		- [Skipping tests](#skipping-tests)
>		- [Executing a specific test only](#executing-a-specific-test-only)
>	- [Building and distributing this package](#building-and-distributing-this-package)
> * [FAQ](#faq)
> * [References](#references)
> * [License](#license)

# APIs
## `easyi` to install

```shell
easyi numpy
```

This installs `numpy` (via `pip install`) then automatically updates the following files:
- `setup.cfg` (WARNING: this file must already exists):
	```
	[options]
	install_requires = 
		numpy
	```
- `requirements.txt` and `prod-requirements.txt`

```shell
easyi flake8 black -D
```

This installs `flake8` and `black` (via `pip install`) and then automatically updates the following files:
- `setup.cfg` (WARNING: this file must already exist):
	```
	[options.extras_require]
	dev = 
		black
		flake8
	```
- `requirements.txt` only, as those dependencies are installed for development purposes only.

## `easyu` to uninstall

```shell
easyu flake8
```

This uninstalls `flake8` as well as all its dependencies. Those dependencies are uninstalled only if other project dependencies do not use them. The `setup.cfg` and `requirements.txt` are automatically updated.

## `easyv` to version

```shell
easyv
```

This returns the current package's version as defined in the `setup.cfg` file.

```shell
easyv bump
```

Bumps the patch bit of the version (e.g., before `2.0.0` after `2.0.1`). Up to three updates are applied:
1. Updates the version property in the `setup.cfg` file.
2. If the project is under source control with git and git is installed:
	1. Updates the `CHANGELOG.md` file using the commit messages between the current branch and the last version tag. If the `CHANGELOG.md` file does not exist, it is automatically created.
	2. git commit and tag (using the version number prefixed with `v`) the project.

```shell
easyv bump patch
```

Same as above.

```shell
easyv bump minor
```

Update the minor bit of the version.

```shell
easyv bump major
```

Update the major bit of the version.

```shell
easyv bump 2.0.0
```

Explicitly sets the version to `2.0.0`.

# Dev
## Dev - Getting started

1. Clone this project:
```shell
git clone https://github.com/nicolasdao/easypipinstall.git
```
2. Browse to the root folder:
```shell
cd easypipinstall
```
3. Create a new virtual environment:
```shell
python3 -m venv .venv
```
4. Activate this virtual environment:
```shell
source .venv/bin/activate
```

To deactivate that virtual environment:
```shell
deactivate
```

## CLI commands

`make` commands:

| Command | Description |
|:--------|:------------|
| `python3 -m venv .venv` | Create a new virtual environment. |
| `source .venv/bin/activate` | Activate the virtual environment |
| `deactivate` | Deactivate the virtual environment |
| `make b` | Builds the package. |
| `make p` | Publish the package to https://pypi.org. |
| `make bp` | Builds the package and then publish it to https://pypi.org. |
| `make bi` | Builds the package and install it locally (`pip install -e .`). |
| `make install` | Install the dependencies defined in the `requirements.txt`. This file contains all the dependencies (i.e., both prod and dev). |
| `make install-prod` | Install the dependencies defined in the `prod-requirements.txt`. This file only contains the production dependencies. |
| `make n` | Starts a Jupyter notebook for this project. |
| `make t` | Formats, lints and then unit tests the project. |
| `make t testpath=<FULLY QUALIFIED TEST PATH>` | Foccuses the unit test on a specific test. For a concrete example, please refer to the [Executing a specific test only](#executing-a-specific-test-only) section. |

## Linting, formatting and testing

```
make t
```

This command runs the following three python executables:

```shell
black ./
flake8 ./
pytest --capture=no --verbose $(testpath)
```

- `black` formats all the `.py` files, while `flake8` lints them. 
- `black` is configured in the `pyproject.toml` file under the `[tool.black]` section.
- `flake8` is configured in the `setup.cfg` file under the `[flake8]` section.
- `pytest` runs all the `.py` files located under the `tests` folder. The meaning of each option is as follow:
	- `--capture=no` allows the `print` function to send outputs to the terminal. 
	- `--verbose` displays each test. Without it, the terminal would only display the count of how many passed and failed.
	- `$(testpath)` references the `testpath` variable. This variable is set to `tests` (i.e., the `tests` folder) by default. This allows to override this default variable with something else (e.g., a specific test to only run that one).

### Ignoring `flake8` errors

This project is pre-configured to ignore certain `flake8` errors. To add or remove `flake8` errors, update the `extend-ignore` property under the `[flake8]` section in the `setup.cfg` file.

### Skipping tests

In your test file, add the `@pytest.mark.skip()` decorator. For example:

```python
import pytest

@pytest.mark.skip()
def test_self_describing_another_test_name():
	# ... your test here
```

### Executing a specific test only

One of the output of the `make t` command is list of all the test that were run (PASSED and FAILED). For example:

```
tests/error/test_catch_errors.py::test_catch_errors_basic PASSED
tests/error/test_catch_errors.py::test_catch_errors_wrapped PASSED
tests/error/test_catch_errors.py::test_catch_errors_nested_errors PASSED
tests/error/test_catch_errors.py::test_catch_errors_StackedException_arbitrary_inputs FAILED
```

To execute a specific test only, add the `testpath` option with the test path. For example, to execute the only FAILED test in the example above, run this command:

```shell
make t testpath=tests/error/test_catch_errors.py::test_catch_errors_StackedException_arbitrary_inputs
```

## Building and distributing this package

1. Make sure the test and lint operations have not produced errors:
```shell
make t
```
2. Build this package:
```shell
make b
```
> This command is a wrapper around `python3 -m build`.
3. Version and tag this package using one of the following command (1):
	- `make v cmd=bump`: Use this to bump the patch version.
	- `make v cmd=bump ver=minor`: Use this to bump the minor version.
	- `make v cmd=bump ver=major`: Use this to bump the major version.
	- `make v cmd=bump ver=x.x.x`: Use this to bump the version to a specific value.
4 . Publish this package to https://pypi.org:
```shell
make p
```
> This command is a wrapper around the following commands: `python3 -m build; twine upload dist/*`


To test your package locally before deploying it to https://pypi.org, you can run build and install it locally with this command:

```shell
make bi
```

This command buils the package and follows with `pip install -e .`.

> (1): This step applies three updates:
> 1. Updates the version property in the `setup.cfg` file.
> 2. Updates the `CHANGELOG.md` file using the commit messages between the current branch and the last version tag.
> 3. git commit and tag (using the version number prefixed with `v`) the project.

# FAQ

# References

# License

BSD 3-Clause License

```
Copyright (c) 2019-2023, Cloudless Consulting Pty Ltd
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

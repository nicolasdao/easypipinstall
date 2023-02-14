# EASY PIP INSTALL

easypipinstall installs Python packages with automatic `requirements.txt`, `prod-requirements.txt` and `setup.cfg` files updates. It also easily uninstall all the dependencies from those files. It uses an opiniated pattern where:
- Only two type of dependencies exist: `prod` and `dev`.
- All dependencies are listed under `requirements.txt`.
- By default, dependencies are listed in both `requirements.txt` and `prod-requirements.txt`.
- Dependencies are not listed under `prod-requirements.txt` when the `-D` option (development mode) is used. 
- The `setup.cfg` file is updated as follow:
	- By default the dependency is listed without its version under the `install_requires` property of the `[options]` section.
	- When the `-D` option is used, the dependency is listed without its version under the `dev` property of the `[options.extras_require]` section.

To install:
```
pip install easypipinstall
```

This will add two new CLI utilities: `easyi` (install) and `easyu` (uninstall).

Examples:
```
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

```
easyi flake8 black -D
```

This installs `flake8` and `black` (via `pip install`) then automatically updates the following files:
- `setup.cfg` (WARNING: this file must already exists):
	```
	[options.extras_require]
	dev = 
		black
		flake8
	```
- `requirements.txt` only, as those dependencies are installed for development purposes only.

```
easyu flake8
```

This uninstalls `flake8` as well as all its dependencies. Those dependencies are uninstalled only if they are not used by other project dependencies. The `setup.cfg` and `requirements.txt` are automatically updated accordingly.





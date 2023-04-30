b:
	rm -rf dist; \
	rm -rf src/*.egg-info; \
	python3 -m build
bp:
	rm -rf dist; \
	rm -rf src/*.egg-info; \
	python3 -m build; \
	twine upload dist/* $(options)
install:
	pip install -r requirements.txt
ie:
	pip install -e .
p:
	twine upload dist/* $(options)
t:
	black ./
	flake8 ./
v:
	python3 -c 'from src.easypipinstall.version import version; version("$(cmd)", "$(ver)")'
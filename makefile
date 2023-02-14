b:
	rm -rf dist; \
	python3 -m build
bp:
	rm -rf dist; \
	python3 -m build; \
	twine upload dist/*
install:
	pip install -r requirements.txt
ie:
	pip install -e .
p:
	twine upload dist/*
t:
	black ./
	flake8 ./
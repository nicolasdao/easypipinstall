b:
	python -m build
install:
	pip install -r requirements.txt
ie:
	pip install -e .
t:
	black ./
	flake8 ./
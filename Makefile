include defaults.mk

CODE_LOCATIONS = proj tests

COVERAGE_LIMIT = 98

#.PHONY: clean-pyc clean-build docs clean

#help:
	#@echo "clean - remove all build, test, coverage and Python artifacts"
	#@echo "clean-build - remove build artifacts"
	#@echo "clean-pyc - remove Python file artifacts"
	#@echo "clean-test - remove test and coverage artifacts"
	#@echo "lint - check style with flake8"
	#@echo "test - run tests quickly with the default Python"
	#@echo "test-all - run tests on every Python version with tox"
	#@echo "coverage - check code coverage quickly with the default Python"
	#@echo "docs - generate Sphinx HTML documentation, including API docs"
	#@echo "release - package and upload a release"
	#@echo "dist - package"

clean: clean-default clean-pyc clean-test
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

docs:
	rm -f docs/proj.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ proj
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: dist
	twine upload dist/*

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

watch: .venv
	@clear
	@make test || true
	@.venv/bin/watchmedo shell-command --drop -c 'clear && make test'

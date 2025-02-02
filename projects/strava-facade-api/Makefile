PYTHON_VERSION:="3.13.1"
SRC_DIR:="strava_facade_api"

.PHONY: default
default: test ;


# Example: `$ make version-bump/1.0.0`.
# Do not edit the `version` in pyproject.toml directly or with `poetry version`, but
#  instead run this.
# This is so we can write the version in __version__.py which is always included in
#  the wheel after a poetry build (unlike pyproject.toml).
.PHONY : version-bump
version-bump/%:
	@echo '# Do not edit __version__ directly, instead run: `$$ make version-bump/1.0.0`.\n__version__ = "$*"' > $(SRC_DIR)/__version__.py
	@poetry version $*


.PHONY : poetry-create-env
poetry-create-env:
	pyenv local $(PYTHON_VERSION) # It creates `.python-version`, to be git-ignored.
	poetry env use $$(pyenv which python) # It creates the env via pyenv.
	poetry install


.PHONY : poetry-destroy-env
poetry-destroy-env:
	rm -f poetry.lock
	@echo "Removing: $$(poetry run which python | tail -n 1)"
	poetry env remove $$(poetry run which python | tail -n 1)


.PHONY : poetry-destroy-and-recreate-env
poetry-destroy-and-recreate-env: poetry-destroy-env poetry-create-env


.PHONY : pyclean
pyclean:
	find . -name *.pyc -delete
	rm -rf *.egg-info build
	rm -rf coverage.xml .coverage
	find . -name .pytest_cache -type d -exec rm -rf "{}" +
	find . -name __pycache__ -type d -exec rm -rf "{}" +	


.PHONY : clean
clean: pyclean
	rm -rf build
	rm -rf dist


.PHONY : pip-clean
pip-clean:
	#rm -rf ~/Library/Caches/pip  # macOS.
	#rm -rf ~/.cache/pip  # linux.
	rm -rf $$(pip cache dir)  # Cross platform.


.PHONY : pip-uninstall-all
pip-uninstall-all:
	pip freeze | pip uninstall -y -r /dev/stdin


.PHONY : deploy
deploy:
	sls deploy


.PHONY : test
test:
	poetry run pytest -s tests/ -v -n auto --durations=25


.PHONY : format
format:
	isort .
	black .


.PHONY : format-check
format-check:
	isort --check-only .
	black --check .

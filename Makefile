.PHONY: format lint all

format:
	isort JVG
	black JVG
	isort tests
	black tests

lint:
	pylint --exit-zero --disable=import-error,no-member JVG

	

all: format lint

bootstrap:
	pip install -r requirements.txt

test:
	isort --check-only .
	flake8 .
	pytest

upload:
	python -m pip install --upgrade build twine
	python -m build
	python -m twine upload --skip-existing dist/*

tag:
	$(eval \
		VERSION = $(shell cat setup.py | grep 'version=' | cut -d '"' -f 2) \
	)

	if ! git ls-remote --tags --exit-code origin v$(VERSION); then \
		git tag v$(VERSION); \
		git push --tags; \
	fi

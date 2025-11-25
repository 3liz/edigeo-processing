SHELL:=bash


-include .localconfig.mk

REQUIREMENTS_GROUPS= \
	dev \
	tests \
	lint \
	packaging \
	$(NULL)

.PHONY: update-requirements 

REQUIREMENTS=$(patsubst %, requirements/%.txt, $(REQUIREMENTS_GROUPS))

update-requirements: $(REQUIREMENTS)

requirements/%.txt: pyproject.toml
	@echo "Updating requirements for '$*'"; \
	uv export --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		--only-group $* \
		-q -o $@

test:
	pytest tests

lint::
	ruff check --output-format=concise

lint:: typecheck

lint-fix:
	ruff check --fix

lint-preview:
	ruff check --preview

lint-fix-preview:
	ruff check --preview --fix

format:
	ruff format

format-diff:
	ruff format --diff

typecheck:
	mypy  .


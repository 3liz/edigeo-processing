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

requirements/%.txt: uv.lock
	@echo "Updating requirements for '$*'"; \
	uv export --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		--only-group $* \
		-q -o $@


test:
	rm -rf tests/__output__/*
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
	mypy .

version-%:
	@echo `uv version --short`+$*

version-prerelease-%:
	@echo `uv version --short`-$*

version-release:
	@uv version --short

STATUS:=unstable

ifeq ($(shell echo $(CI_COMMIT_TAG) | head -c 8), release-)
VERSION_BUMP=release
STATUS:=stable
else
VERSION_BUMP=alpha
endif

version: version-$(VERSION_BUMP)

status:
	@echo $(STATUS)

echo-var-%:
	@echo $($*)




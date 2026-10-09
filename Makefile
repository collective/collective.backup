# Run the same checks as the GitHub workflows, before you commit.
#
#   make check      everything: lint, dependencies, release, circular,
#                   tests on all Python versions and the Docker build
#   make quick      lint and tests on one Python version
#
# Needs uv; tox-uv fetches missing Python versions.  Docker is optional.

TOX ?= uvx --with tox-uv tox
PYTHONS ?= py310,py311,py312,py313,py314

.PHONY: help check quick lint format dependencies release-check circular \
	test test-all docker clean

help:
	@sed -n '1,8s/^# \{0,1\}//p' Makefile

check: lint dependencies release-check circular test-all docker

quick: lint test

# Meta workflow, qa job.
lint:
	$(TOX) -e lint

format:
	$(TOX) -e format

# Meta workflow, dependencies job.
dependencies:
	$(TOX) -e dependencies

# Meta workflow, release_ready job.  The tox env runs towncrier, which
# consumes the news fragments and rewrites CHANGES.rst, so run it in a
# throwaway copy of the working tree.
release-check:
	@tmp=$$(mktemp -d) && \
	git ls-files -co --exclude-standard | rsync -a --files-from=- . "$$tmp" && \
	(cd "$$tmp" && $(TOX) -e release-check); \
	status=$$?; rm -rf "$$tmp"; exit $$status

# Meta workflow, circular job.
circular:
	$(TOX) -e circular

test:
	$(TOX) -e test

# tests workflow.
test-all:
	$(TOX) run-parallel -e $(PYTHONS)

# docker workflow (local platform only, no push).
docker:
	@if command -v docker >/dev/null && docker info >/dev/null 2>&1; then \
		docker build -t collective-backup:check . ; \
	else \
		echo "Docker is not running, skipping the image build."; \
	fi

clean:
	rm -rf build dist .tox forest.dot forest.json

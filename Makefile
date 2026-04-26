.PHONY: release-major release-features release-fixes

release-major: SHELL := bash
release-major: ## Bump major version and release to main
	./bin/release.sh major

release-features: SHELL := bash
release-features: ## Bump minor version and release to main
	./bin/release.sh features

release-fixes: SHELL := bash
release-fixes: ## Bump patch version and release to main
	./bin/release.sh fixes

version = `cat ./VERSION`
package-name = generic-api


test:
	echo "no tests"
	# python -m green -ar tests/*.py

upload: test vpatch
	devpi upload

install-locally:
	pip install -U .

publish:
	devpi push "$(package-name)==$(version)" "ai-unit/prod"

vpatch:
	bumpversion patch

vminor:
	bumpversion minor

vmajor:
	bumpversion major

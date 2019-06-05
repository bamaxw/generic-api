version = `cat ./VERSION`
package-name = genericapi


test:
	echo "no tests"
	# python -m green -ar tests/*.py

upload: test vpatch
	devpi upload

install-locally:
	pip install -U .

publish:
	devpi push "$(package-name)==$(version)" "inyourarea/prod"

vpatch:
	bumpversion patch

vminor:
	bumpversion minor

vmajor:
	bumpversion major

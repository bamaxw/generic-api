version = `cat ./VERSION`
package-name = genericapi


test:
	echo "no tests"
	# python -m green -ar tests/*.py

upload: vpatch
	pipenv run python setup.py bdist_wheel
	twine upload --repository-url https://pypi.inyourarea.co.uk/inyourarea/staging dist/*

publish:
	twine upload --repository-url https://pypi.inyourarea.co.uk/inyourarea/prod dist/*
	rm -r dist
	rm -r build
	rm -r jigsawdb.egg-info

vpatch:
	bumpversion patch

vminor:
	bumpversion minor

vmajor:
	bumpversion major

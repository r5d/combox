#    Copyright (C) 2015 Combox contributor(s). See CONTRIBUTORS.rst.
#
#    This file is part of Combox.
#
#   Combox is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Combox is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Combox (see COPYING).  If not, see
#   <http://www.gnu.org/licenses/>.
all:
	@echo "Give me something to make."

test:
	@nosetests

egg:
	@python setup.py egg_info

build-dist:
	@python setup.py sdist bdist_wheel

docs:
	@$(MAKE) -C docs html

upload-pypi:
	@twine upload -r bgpypi -s -i sravik@bgsu.edu dist/*.tar.gz
	@twine upload -r bgpypi -s -i sravik@bgsu.edu  dist/*.whl

upload-docs:
	@rsync -avz --delete --exclude-from=docs/rsync-exclude.filter docs/_build/html/  $(COMBOX_DOCS_HOST)

clean-docs:
	@$(MAKE) -C docs clean

clean-dist:
	@rm -rf dist/

clean-build:
	@rm -rf build/
	@rm -rf *.egg-info

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +

.PHONY: dist clean-build clean-dist clean-pyc upload-pypi upload-docs build-dist docs all

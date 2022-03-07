
.PHONY: default setup build buildext force forceext install installext test testext dist clean

PYTHON=python
PYTHON2=python2
PYTHON3=python3
TEST=
PARAMETERS=

setup:
	pip install tox tox-pyenv Cython
	pyenv install --skip-existing 2.7.18
	pyenv install --skip-existing 3.7.12
	pyenv install --skip-existing 3.8.12
	pyenv install --skip-existing 3.9.10
	pyenv install --skip-existing 3.10.2
	pyenv install --skip-existing pypy3.8-7.3.7
	pyenv local 2.7.18 3.7.12 3.8.12 3.9.10 3.10.2 pypy3.8-7.3.7
	pyenv global 2.7.18 3.7.12 3.8.12 3.9.10 3.10.2 pypy3.8-7.3.7
	python --version
	python -m pip install tox tox-pyenv Cython

build:
	${PYTHON} setup.py build ${PARAMETERS}

buildext:
	${PYTHON} setup.py --with-libyaml build ${PARAMETERS}

force:
	${PYTHON} setup.py build -f ${PARAMETERS}

forceext:
	${PYTHON} setup.py --with-libyaml build -f ${PARAMETERS}

install:
	${PYTHON} setup.py install ${PARAMETERS}

installext:
	${PYTHON} setup.py --with-libyaml install ${PARAMETERS}

test: build
	${PYTHON} tests/lib/test_build.py ${TEST}

testext: buildext
	${PYTHON} tests/lib/test_build_ext.py ${TEST}

testall:
	${PYTHON} setup.py test

dist:
	@# No longer uploading a zip file to pypi
	@# ${PYTHON} setup.py --with-libyaml sdist --formats=zip,gztar
	${PYTHON} setup.py --with-libyaml sdist --formats=gztar

windist:
	${PYTHON} setup.py --with-libyaml bdist_wininst

clean:
	${PYTHON} setup.py --with-libyaml clean -a
	rm -rf .tox/ build/ lib/PyYAML*/ yaml/*.c .pytest_cache/ wheelhouse/
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

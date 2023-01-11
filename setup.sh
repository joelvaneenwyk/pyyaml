#!/usr/bin/sh

clean() {
    rm -rf "./.tox"
    rm -rf "./libyaml"
    rm -rf "./build"
    rm -rf "./lib/PyYAML.egg-info"
}

install() {
    echo "Installing Python versions through 'pyenv' install..."
    pyenv install --skip-existing 2.6.9
    pyenv install --skip-existing 2.7.18
    pyenv install --skip-existing 3.6.15
    pyenv install --skip-existing 3.7.16
    pyenv install --skip-existing 3.8.16
    pyenv install --skip-existing 3.9.16
    pyenv install --skip-existing 3.10.9
    pyenv install --skip-existing 3.11.1
    pyenv install --skip-existing 3.12-dev
    pyenv install --skip-existing ironpython-2.7.7
    pyenv install --skip-existing jython-2.7.2
    pyenv install --skip-existing pypy2.7-7.3.11
    pyenv install --skip-existing pypy3.9-7.3.11
    pyenv install --skip-existing pyston-2.3.5
    pyenv install --skip-existing stackless-3.7.5
}

if [ -d "${HOME:-}/.pyenv" ]; then
    export PYENV_ROOT="${HOME:-}/.pyenv"

    if ! pyenv --version >/dev/null 2>&1; then
        export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/versions:$PATH"
        eval "$(pyenv init -)"
    fi
fi

pyenv local \
    3.9.16 3.10.9 3.11.1 3.12-dev \
    3.6.15 3.7.16 \
    2.6.9 2.7.18 \
    ironpython-2.7.7 jython-2.7.2 pypy2.7-7.3.11 pypy3.9-7.3.11 pyston-2.3.5 stackless-3.7.5

if [ "${1:-}" = "install" ]; then
    install
fi

python3 --version

if ! python3 -m pip --version; then
    python3 -m ensurepip
fi

python3 -m pip install --upgrade pip
python3 -m pip install tox pytest pyright mypy black flake8

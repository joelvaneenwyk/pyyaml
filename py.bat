@echo off
setlocal EnableDelayedExpansion

set PYRIGHT_PYTHON_FORCE_VERSION=latest
set PYRIGHT_PYTHON_IGNORE_WARNINGS=1

call pyenv --version >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    call pyenv exec python %*
    exit /b
)

call python3 --version >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    call python3 %*
    exit /b
)

python %*

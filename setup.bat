@echo off
setlocal EnableDelayedExpansion

if "%~1"=="clean" (
    call :Clean
    exit /b
)

if "%~1"=="install" (
    shift
    call :Install
)

call "%~dp0py.bat" --version
call "%~dp0py.bat" -m ensurepip
call "%~dp0py.bat" -m pip install --upgrade pip
call "%~dp0py.bat" -m pip install tox pytest pyright mypy black flake8
if not "%~1"=="" call "%~dp0py.bat" %*
exit /b

:Clean
    rmdir /q /s "%~dp0.tox"
    rmdir /q /s "%~dp0libyaml"
    rmdir /q /s "%~dp0build"
    rmdir /q /s "%~dp0lib\PyYAML.egg-info"
exit /b 0

:Install
    echo Installing Python versions through 'pyenv' install...
    pyenv --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        call pyenv install 2.6.6
        call pyenv install 2.7.18
        call pyenv install 3.10.9
        call pyenv install 3.11.1
        call pyenv install 3.12.0a3
        call pyenv install 3.6.8
        call pyenv install 3.7.0-win32
        call pyenv install 3.8.10
        call pyenv install 3.9.9
    )

    scoop --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        echo Installing Python versions through 'scoop' install...
        scoop bucket add versions
        scoop install python27
        scoop install python36
        scoop install python37
        scoop install python311
        scoop install pypy2
        scoop install pypy3
    )
exit /b

pyenv local ^
    3.9.9 3.10.9 3.11.1 ^
    2.6.6 2.7.18 ^
    3.12.0a3 3.6.8 3.7.0-win32 3.8.10

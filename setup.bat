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

    call pyenv --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        call pyenv local ^
            3.9.9 3.10.9 3.11.1 ^
            2.6.6 2.7.18 ^
            3.12.0a3 3.6.8 3.7.0-win32 3.8.10

        call pyenv versions
    )

    set _jython=C:\Tools\jython2.7.3
    if not exist "%_jython%" goto:$SkipJython
        jython --version >nul 2>&1
        if not "!ERRORLEVEL!"=="0" (
            set "PATH=%PATH%;C:\Tools\jython2.7.3\bin"
        )
    :$SkipJython

    call :Run call "%~dp0py.bat" --version
    call :Run call "%~dp0py.bat" -m ensurepip
    call :Run call "%~dp0py.bat" -m pip install --upgrade pip
    call :Run call "%~dp0py.bat" -m pip install --upgrade tox pytest pyright mypy black flake8 pylint
endlocal & (
    set "PATH=%PATH%"
)

if not "%~1"=="" call "%~dp0py.bat" %*
exit /b

:Clean
    rmdir /q /s "%~dp0.tox"
    rmdir /q /s "%~dp0libyaml"
    rmdir /q /s "%~dp0build"
    rmdir /q /s "%~dp0lib\PyYAML.egg-info"
exit /b 0

:Install
    call pyenv --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        echo Installing Python versions through 'pyenv' install...
        call :Run call pyenv install --skip-existing 3.9.9
        call :Run call pyenv install --skip-existing 3.10.9
        call :Run call pyenv install --skip-existing 3.11.1
        call :Run call pyenv install --skip-existing 3.12.0a3

        call :Run call pyenv install --skip-existing 2.7.18
        call :Run call pyenv install --skip-existing 2.6.6

        call :Run call pyenv install --skip-existing 3.8.10
        call :Run call pyenv install --skip-existing 3.7.0-win32
        call :Run call pyenv install --skip-existing 3.6.8
    )

    scoop --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        echo Installing Python versions through 'scoop' install...
        call :Run scoop bucket add versions
        call :Run scoop install --no-update-scoop python39
        call :Run scoop install --no-update-scoop python311
        call :Run scoop install --no-update-scoop python27
        call :Run scoop install --no-update-scoop pypy3

        call :Run scoop install --no-update-scoop python37
        call :Run scoop install --no-update-scoop python36
        call :Run scoop install --no-update-scoop pypy2
    )
exit /b

:Run
    echo ##[cmd] %*
    %*
exit /b

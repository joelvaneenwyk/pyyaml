@echo off
setlocal EnableDelayedExpansion

set _root=%~dp0
if "!_root:~-1!"=="\" set _root=!_root:~0,-1!

set DISTUTILS_USE_SDK=1
set MSSdk=1
set PYYAML_FORCE_CYTHON=1
set PYYAML_FORCE_LIBYAML=1
set INCLUDE=%_root%\yaml;%_root%\libyaml\include;%INCLUDE%
set LIBPATH=%_root%\yaml;%_root%\libyaml\build\Release;%LIBPATH%
set GIT_ASK_YESNO=false
set AGENT_TOOLSDIRECTORY=%_root%\build\cache

python -V

set _libyaml_source=%_root%\libyaml
set _libyaml_build=%_root%\build\libyaml
if exist "%_libyaml_build%" rmdir /s /q "%_libyaml_build%"
mkdir "%_libyaml_build%"

if not exist "%_libyaml_source%" (
    git clone https://github.com/yaml/libyaml "%_libyaml_source%"
) else (
    git -C "%_libyaml_source%" clean -fdx
    git pull
)
cmake.exe -A x64 -DYAML_STATIC_LIB_NAME=yaml -S "%_libyaml_source%" -B "%_libyaml_build%"
cmake.exe --build "%_libyaml_build%" --config Release
if errorlevel 1 exit /b

python -W "ignore:DEPRECATION" -m pip install --upgrade cython wheel setuptools --no-warn-script-location

python "%_root%\setup.py" --with-libyaml build_ext -I "%_root%\libyaml\include" -L "%_root%\libyaml\build\Release" -D YAML_DECLARE_STATIC build bdist_wheel

set PYTHONPATH=%_root%\lib;%_root%\tests\lib;%_root%\build\lib.win-amd64-2.7
python "%_root%\tests\lib\test_all.py"

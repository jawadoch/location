@echo off
setlocal
cd /d "%~dp0"
title Installation - Gestion location de voitures
echo ============================================================
echo   Installation de l'application de gestion de location
echo ============================================================
echo.

rem ---------- 1. Recherche de Python 3.10 ou plus recent
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if defined PY goto python_ok
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
if defined PY goto python_ok
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
if defined PY goto python_ok

echo Python n'est pas installe. Tentative d'installation automatique...
where winget >nul 2>nul
if errorlevel 1 goto no_python
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
if defined PY goto python_ok

:no_python
echo.
echo [ERREUR] Python est introuvable.
echo Installez Python 3.12 depuis https://www.python.org/downloads/
echo en cochant la case "Add python.exe to PATH", puis relancez INSTALLER.bat
echo.
pause
exit /b 1

:python_ok
echo [1/4] Python trouve :
%PY% --version
echo.

rem ---------- 2. Environnement virtuel
if exist ".venv\Scripts\python.exe" goto venv_ok
echo [2/4] Creation de l'environnement de l'application...
%PY% -m venv .venv
if errorlevel 1 goto error
:venv_ok

rem ---------- 3. Dependances
echo [3/4] Installation des composants, patientez quelques minutes...
".venv\Scripts\python.exe" -m pip install --upgrade pip --disable-pip-version-check -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt --disable-pip-version-check -q
if errorlevel 1 goto error
".venv\Scripts\python.exe" -c "from app import create_app; create_app()"
if errorlevel 1 goto error

rem ---------- 4. Raccourcis Bureau et menu Demarrer
echo [4/4] Creation des raccourcis sur le Bureau...
powershell -NoProfile -ExecutionPolicy Bypass -File "windows\creer_raccourcis.ps1"
if errorlevel 1 goto error

echo.
echo ============================================================
echo   Installation terminee.
echo   Double-cliquez sur l'icone "Apollo Car" du Bureau
echo   pour ouvrir l'application.
echo ============================================================
echo.
start "" wscript.exe "%~dp0windows\lancer.vbs"
pause
exit /b 0

:error
echo.
echo [ERREUR] L'installation a echoue. Verifiez la connexion Internet et relancez INSTALLER.bat
pause
exit /b 1

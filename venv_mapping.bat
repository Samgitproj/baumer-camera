@echo off
REM ——————————————
REM piplist.bat
REM Project: AI camera virtuele omgeving
REM Toont alle geïnstalleerde pip-packages in de venv
REM ——————————————

REM 1) Navigeer naar de map van dit script
cd /d "%~dp0"

REM 2) Voer het pip-list commando uit via de Python in de virtuele omgeving
powershell -NoProfile -ExecutionPolicy Bypass -Command "& 'C:\virt omgeving\AI camera\Scripts\python.exe' -m pip list"

REM 3) Houd het venster open om de lijst te bekijken
pause

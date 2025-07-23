@echo off
REM ——————————————
REM start_project.bat
REM Project: Baumer Camera GUI
REM Plaats dit bestand in de project-root (waar main.py staat)
REM ——————————————

REM 1) Activeer de virtuele omgeving
CALL "C:\virt omgeving\AI camera\Scripts\activate.bat"

REM 2) Navigeer naar de map van dit script (project-root)
cd /d "%~dp0"

REM 3) Start de hoofd-applicatie
python main.py

REM 4) Houd het venster open om eventuele foutmeldingen te zien
pause

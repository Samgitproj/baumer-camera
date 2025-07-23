@echo off
REM ——————————————
REM projectmapping.bat
REM Project: Baumer Camera GUI
REM Voer recursieve mappenlijst uit voor het baumer_project
REM ——————————————

REM 1) Navigeer naar de map van dit script (project-root)
cd /d "%~dp0"

REM 2) Voer PowerShell-commando uit om mapinhoud recursief weer te geven
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -Path 'C:\OneDrive\Vioprint\OneDrive - Vioprint\Sam\AI camera\baumer project\baumer_project' -Recurse"

REM 3) Houd het venster open om eventuele foutmeldingen te zien
pause
@echo off
REM — Generate folder name in DDMMYYHHMM format
for /f "skip=1 tokens=1" %%x in ('wmic os get localdatetime') do if not defined ldt set ldt=%%x
set dd=%ldt:~6,2%
set mm=%ldt:~4,2%
set yy=%ldt:~2,2%
set hh=%ldt:~8,2%
set min=%ldt:~10,2%
set folder=%dd%%mm%%yy%%hh%%min%

REM — Paths
set scriptDir=%~dp0
set sourceDir=%scriptDir:~0,-1%
set backupRoot=C:\OneDrive\Vioprint\OneDrive - Vioprint\Sam\AI camera\baumer project\backup
set dest=%backupRoot%\%folder%

REM — Create the time-stamped backup folder
mkdir "%dest%"

REM — Copy everything under project folder to the new backup folder, excluding the backup folder itself
robocopy "%sourceDir%" "%dest%" /E /COPY:DAT /R:0 /W:0 /XD "%backupRoot%"

pause

@echo off
cd /d %~dp0
echo [%date% %time%] Running Daily Check... >> run_log.txt
python daily_check.py >> run_log.txt 2>&1
echo Done. >> run_log.txt

@echo off
title EMS Expense Portal Mobile App
echo ========================================================
echo    STARTING EMS EXPENSE PORTAL MOBILE APP SERVER
echo ========================================================
echo.
echo Desktop Access : http://localhost:5000
echo Mobile Access  : Check QR code or IP displayed on screen
echo ========================================================
echo.
cd /d "C:\Users\SSBD-202506-02\Downloads\Expense-Portal-App"
start http://localhost:5000
"C:\Users\SSBD-202506-02\AppData\Local\Python\bin\python.exe" app.py
pause

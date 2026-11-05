@echo off
title Push EMS Expense App to GitHub
echo ============================================================
echo PUSHING EMS EXPENSE PORTAL APP TO GITHUB
echo ============================================================
echo.
git status
echo.
echo Adding files...
git add .
echo.
echo Committing changes...
git commit -m "Update EMS Expense Mobile App with Cloudflare Tunnel & Cloud deployment"
echo.
echo Pushing to GitHub...
git push -u origin main
echo.
echo ============================================================
echo Done!
pause

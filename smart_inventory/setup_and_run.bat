@echo off
echo ============================================
echo   Smart Inventory Management System Setup
echo ============================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo [2/4] Installing dependencies...
pip install -r requirements.txt

echo [3/4] Setting up database...
python manage.py migrate

echo [4/4] Loading sample data...
python manage.py populate_sample_data

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo   Login credentials:
echo     Admin:  admin / admin123
echo     Demo:   demo  / demo123
echo.
echo   Starting server...
echo   Open: http://127.0.0.1:8000/
echo.
python manage.py runserver

pause

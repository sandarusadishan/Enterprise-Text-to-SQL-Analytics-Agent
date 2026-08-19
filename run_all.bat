@echo off
echo ===================================================
echo   OmniQuery - Starting Autonomous BI Analytics Agent
echo ===================================================
echo.

echo [1/3] Launching FastAPI Backend Server (Port 8000)...
cd backend
start "OmniQuery API" cmd /k ".\venv\Scripts\python.exe main.py"

echo [2/3] Launching Backup Streamlit App (Port 8501)...
start "OmniQuery Streamlit" cmd /k ".\venv\Scripts\streamlit.exe run app.py"

echo [3/3] Launching React Frontend Dev Server (Port 5173)...
cd ../frontend
start "OmniQuery Frontend" cmd /k "npm run dev"

echo.
echo ===================================================
echo   All servers started successfully!
echo   Open: http://localhost:5173 (React UI)
echo         http://localhost:8501 (Streamlit UI)
echo ===================================================
pause

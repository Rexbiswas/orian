# OrionAI Full-Stack Startup Script

Write-Host "Starting OrionAI Full-Stack System..." -ForegroundColor Cyan

# 1. Start Python Backend (FastAPI)
Write-Host "[1/3] Launching Python Intelligence Core (Port 8000) [WATCH_MODE]..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass", "-NoExit", "-Command", "cd backend; python main.py"

# 2. Start Node.js Proxy Server
Write-Host "[2/3] Launching Node.js Proxy Server (Port 5000) [WATCH_MODE]..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass", "-NoExit", "-Command", "npm run dev --prefix server"

# 3. Launch HackerAI Local Bridge (Pro Security Context)
Write-Host "[3/4] Initializing HackerAI Local Bridge..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass", "-NoExit", "-Command", "npx -y @hackerai/local@latest --token hsb_b14367f6b37d02aff7c5c964f4eb9799e2497de2de49f1daa88fcfde6f130465 --name 'My Machine'"

# 4. Start Frontend (Vite)
Write-Host "[4/4] Launching Frontend Dashboard..." -ForegroundColor Green
npm run dev

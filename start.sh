#!/bin/bash
# Naledi Intelligence Platform — Studex Meat
# Start both backend (FastAPI) and frontend (Vite)

set -e

CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   NALEDI INTELLIGENCE PLATFORM v1.0      ║${NC}"
echo -e "${CYAN}║   Studex Meat · Rulofo + GSD + RALF-GIUM ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# Backend
echo -e "${CYAN}[1/2] Starting backend (FastAPI) on :8000...${NC}"
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Frontend
echo -e "${CYAN}[2/2] Starting frontend (Vite) on :5173...${NC}"
cd frontend
npm install --silent 2>/dev/null
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "${CYAN}  Backend API:  http://localhost:8000${NC}"
echo -e "${CYAN}  Frontend UI:  http://localhost:5173${NC}"
echo -e "${CYAN}  API docs:     http://localhost:8000/docs${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo ""
echo "Press Ctrl+C to stop both services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait

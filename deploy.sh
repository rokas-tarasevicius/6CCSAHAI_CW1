#!/bin/bash

# Deployment script for Adaptive Learning Platform
# Starts both backend (FastAPI) and frontend (React) servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Cleanup function to kill background processes
cleanup() {
    print_info "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

print_info "Starting Adaptive Learning Platform..."
echo ""

# Check Python dependencies
print_info "Checking Python dependencies..."
if ! command -v uv &> /dev/null; then
    print_error "UV package manager not found. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check Node.js dependencies
print_info "Checking Node.js dependencies..."
if ! command -v npm &> /dev/null; then
    print_error "npm not found. Please install Node.js first"
    exit 1
fi

# Start backend
print_info "Starting backend server (FastAPI) on http://localhost:8000"
cd backend
uv run uvicorn api.main:app --reload --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    print_error "Backend failed to start. Check backend.log for details"
    exit 1
fi

print_info "Backend started (PID: $BACKEND_PID)"

# Start frontend
print_info "Starting frontend server (React) on http://localhost:5173"
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    print_info "Installing frontend dependencies..."
    npm install
fi

npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    print_error "Frontend failed to start. Check frontend.log for details"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

print_info "Frontend started (PID: $FRONTEND_PID)"
echo ""
print_info "=========================================="
print_info "🚀 Platform is running!"
print_info "=========================================="
echo ""
print_info "Backend API:  http://localhost:8000"
print_info "Frontend App: http://localhost:5173"
print_info "API Docs:     http://localhost:8000/docs"
echo ""
print_warn "Press Ctrl+C to stop both servers"
echo ""

# Wait for user interrupt
wait


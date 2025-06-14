#!/bin/bash
# FinSight Demo Startup Script
# Starts both API server and frontend for PM demo

echo "🎯 Starting FinSight Demo Environment"
echo "=================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "llm_api_server.py" ]; then
    echo "❌ Please run this script from the FinSight/demo directory"
    exit 1
fi

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
        echo "🔧 Attempting to free port $port..."
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        sleep 2
        if lsof -i :$port > /dev/null 2>&1; then
            echo "❌ Could not free port $port. Please manually kill the process using: lsof -ti :$port | xargs kill -9"
            exit 1
        fi
    fi
    echo "✅ Port $port is available"
}

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q fastapi uvicorn yfinance pandas requests || {
    echo "❌ Failed to install dependencies"
    exit 1
}

echo "✅ Dependencies ready"

# Check and free ports if needed
echo "🔍 Checking port availability..."
check_port 8000
check_port 8080

# Start API server in background
echo "🚀 Starting FinSight LLM-Enhanced API server..."
python llm_api_server.py &
API_PID=$!

# Wait for API to start
echo "⏳ Waiting for API server to start..."
sleep 3

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API server running on http://localhost:8000"
else
    echo "❌ API server failed to start"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Start frontend server
echo "🌐 Starting frontend server..."
cd ../frontend
python -m http.server 8080 &
FRONTEND_PID=$!
cd ../demo

# Wait for frontend to start
sleep 2

echo ""
echo "🎉 FinSight Demo Ready!"
echo "======================="
echo ""
echo "🌐 Frontend Demo: http://localhost:8080/demo-fixed.html"
echo "🔧 API Server:    http://localhost:8000"
echo "📚 API Docs:      http://localhost:8000/docs"
echo ""
echo "🎭 Demo Instructions:"
echo "1. Open http://localhost:8080/demo-fixed.html in your browser"
echo "2. Try the sample scenarios (Risky Investment Advice recommended)"
echo "3. Click 'Enhance Content with FinSight' to see magic happen"
echo ""
echo "📋 For PM Demo:"
echo "• Start with the problem (raw AI content)"
echo "• Show the solution (enhanced content)"
echo "• Highlight business value and technical readiness"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping demo servers..."
    
    # Kill specific PIDs if they exist
    if [[ -n "$API_PID" ]]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [[ -n "$FRONTEND_PID" ]]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Also kill any processes still using our ports
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    lsof -ti :8080 | xargs kill -9 2>/dev/null || true
    
    echo "✅ Demo environment stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running and show logs
echo ""
echo "📊 Server Logs (Ctrl+C to stop):"
echo "================================"

# Wait for user to stop
wait

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
if [ ! -f "api_server.py" ]; then
    echo "❌ Please run this script from the FinSight/demo directory"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q fastapi uvicorn yfinance pandas requests || {
    echo "❌ Failed to install dependencies"
    exit 1
}

echo "✅ Dependencies ready"

# Start API server in background
echo "🚀 Starting FinSight API server..."
python api_server.py &
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
cd frontend
python -m http.server 8080 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 2

echo ""
echo "🎉 FinSight Demo Ready!"
echo "======================="
echo ""
echo "🌐 Frontend Demo: http://localhost:8080/enhanced-demo.html"
echo "🔧 API Server:    http://localhost:8000"
echo "📚 API Docs:      http://localhost:8000/docs"
echo ""
echo "🎭 Demo Instructions:"
echo "1. Open http://localhost:8080/enhanced-demo.html in your browser"
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
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
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

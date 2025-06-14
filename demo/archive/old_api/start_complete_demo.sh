#!/bin/bash

# FinSight Complete Demo Startup Script
# Starts both API server and frontend server for full demo

echo "🚀 Starting FinSight Complete Demo Environment"
echo "=============================================="

# Kill any existing servers
echo "🧹 Cleaning up existing servers..."
pkill -f api_server.py 2>/dev/null || true
pkill -f "http.server 8082" 2>/dev/null || true
sleep 2

# Start API server in background
echo "🔧 Starting API server on port 8000..."
cd "$(dirname "$0")/.."
python demo/api_server.py &
API_PID=$!

# Wait for API to start
sleep 3

# Start frontend server in background  
echo "🌐 Starting frontend server on port 8082..."
cd demo && python -m http.server 8082 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 2

echo ""
echo "✅ Demo Environment Ready!"
echo "=========================="
echo "📡 API Server:      http://localhost:8000"
echo "🌐 Frontend Demo:   http://localhost:8082/frontend/enhanced-demo.html"
echo "💊 API Health:      http://localhost:8000/health"
echo ""
echo "🎯 Ready for PM Demo! Use these URLs:"
echo "   • Main Demo: http://localhost:8082/frontend/enhanced-demo.html"
echo "   • API Docs:  http://localhost:8000/docs"
echo ""
echo "🛑 To stop servers: pkill -f api_server.py && pkill -f 'http.server 8082'"
echo ""

# Test that both servers are working
echo "🧪 Testing servers..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API Server: OK"
else
    echo "❌ API Server: FAILED"
fi

if curl -s -I http://localhost:8082/frontend/enhanced-demo.html > /dev/null; then
    echo "✅ Frontend Server: OK"
else
    echo "❌ Frontend Server: FAILED"
fi

echo ""
echo "🎉 FinSight Demo is LIVE and ready for presentation!"
echo "Press Ctrl+C to stop all servers"

# Keep script running and handle cleanup on exit
trap 'echo ""; echo "🛑 Stopping demo servers..."; kill $API_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Wait for user interrupt
wait

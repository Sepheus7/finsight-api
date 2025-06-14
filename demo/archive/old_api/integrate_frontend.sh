#!/bin/bash
# Script to help integrate external frontend with FinSight backend

echo "🎯 FinSight Frontend Integration Helper"
echo "======================================"

echo ""
echo "This script will help you integrate your external frontend with FinSight."
echo ""

# Check if frontend directory exists
if [ -d "frontend" ]; then
    echo "📁 Current frontend directory exists: $(ls frontend/)"
    echo ""
    echo "Options:"
    echo "1. Backup existing frontend and copy your frontend here"
    echo "2. Add your frontend files alongside existing ones"
    echo "3. Exit and manually manage"
    echo ""
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo "📦 Backing up existing frontend to frontend_backup..."
            mv frontend frontend_backup
            mkdir frontend
            echo "✅ Ready to copy your frontend files to: $(pwd)/frontend/"
            ;;
        2)
            echo "✅ Ready to add your files to existing: $(pwd)/frontend/"
            ;;
        3)
            echo "👋 Exiting. You can manually copy files to: $(pwd)/frontend/"
            exit 0
            ;;
        *)
            echo "❌ Invalid option"
            exit 1
            ;;
    esac
else
    mkdir -p frontend
    echo "📁 Created frontend directory: $(pwd)/frontend/"
fi

echo ""
echo "📋 INTEGRATION STEPS:"
echo "1. Copy your frontend files to: $(pwd)/frontend/"
echo "2. Update API endpoints in your frontend to: http://localhost:8000"
echo "3. Update the demo/INSTRUCTIONS.md frontend path if needed"
echo "4. Test with: cd demo && python -m http.server 8080"
echo ""

echo "🔧 BACKEND SETUP:"
echo "Make sure to use the LLM-enhanced API server:"
echo "  python demo/llm_api_server.py"
echo ""

echo "🌐 CORS CONFIGURATION:"
echo "Both API servers are already configured to accept requests from any origin."
echo "Your frontend should be able to make requests to http://localhost:8000"
echo ""

echo "📱 SUGGESTED FRONTEND STRUCTURE:"
echo "frontend/"
echo "├── index.html (your main page)"
echo "├── css/"
echo "├── js/"
echo "├── assets/"
echo "└── enhanced-demo.html (existing demo page)"
echo ""

echo "🚀 After copying your files, you can:"
echo "1. Update start_demo.sh to serve your specific frontend page"
echo "2. Test the integration with: ./start_demo.sh"
echo "3. Access your frontend at: http://localhost:8080/[your-page].html"
echo ""

read -p "Press Enter to continue..."

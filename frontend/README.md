# FinSight Frontend - Unified Interface

This directory contains the unified FinSight frontend interface that consolidates all the different components into a single, cohesive application.

## New Unified Structure

### Main Interface (`main.html`)

The new unified interface provides seamless navigation between all FinSight features:

- **Home Page**: Overview and feature navigation
- **AI Chat**: Intelligent financial assistant powered by Bedrock Router Agent
- **RAG Platform**: Retrieval-Augmented Generation for financial research
- **Analysis Tools**: Financial enrichment, fact-checking, and compliance tools

### Key Features

1. **Bedrock Router Agent Integration**: The chat interface now uses the new Bedrock function calling system for more intelligent and accurate responses.

2. **Unified Navigation**: Single-page application with smooth transitions between different tools.

3. **Real-time API Status**: Live monitoring of backend service health.

4. **Responsive Design**: Works seamlessly on desktop and mobile devices.

## Files Overview

### Core Files

- `main.html` - New unified interface (main entry point)
- `api.js` - Updated API client with router agent support
- `styles.css` - Enhanced styles with router agent message styling

### Legacy Files (Still Used)

- `chat.html` - Chat interface (embedded in main.html)
- `index-rag.html` - RAG platform (embedded in main.html)
- `index.html` - Analysis tools (embedded in main.html)
- `chat-app.js` - Chat functionality with router agent integration
- `rag-app.js` - RAG platform functionality
- `app.js` - Analysis tools functionality

### Removed/Deprecated

- `performance-demo.html` - No longer needed (functionality integrated)
- `demo-fixed.html` - Replaced by unified interface

## Usage

1. **Start the Backend Server**:

   ```bash
   cd /path/to/FinSight
   python src/api_server.py
   ```

2. **Access the Interface**:
   Open <http://localhost:8000> in your browser

3. **Navigate Between Features**:
   - Use the top navigation bar to switch between different tools
   - Click on feature cards on the home page for quick access
   - All features are now integrated in a single interface

## API Integration

The frontend now integrates with the new Bedrock Router Agent through the `/route-query` endpoint:

```javascript
// Example usage
const api = new FinSightAPI();
const response = await api.routeQuery("What is Apple's stock price?", {
    use_function_calling: true
});
```

## Router Agent Features

The new chat interface includes:

- **Function Calling**: Automatic tool selection and execution
- **Real-time Data**: Live stock prices, company information, and economic indicators
- **Web Search**: Intelligent web search for additional context
- **Metadata Display**: Detailed information about AI processing and tool usage
- **Error Handling**: Graceful fallbacks and error reporting

## Development

To modify the interface:

1. **Main Layout**: Edit `main.html` for navigation and overall structure
2. **Chat Features**: Modify `chat-app.js` for chat functionality
3. **Styling**: Update `styles.css` for visual changes
4. **API Integration**: Modify `api.js` for backend communication

The interface automatically loads and initializes the appropriate JavaScript modules when navigating between different sections.

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License - See LICENSE file for details

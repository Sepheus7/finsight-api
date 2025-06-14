# FinSight Frontend

A modern, responsive web interface for testing and interacting with the FinSight Financial Data Enrichment API.

## Features

- 🎯 **API Testing Interface** - Test API endpoints with real-time feedback
- 🔄 **Environment Switching** - Easily switch between local, dev, and prod environments
- 📊 **Response Visualization** - Clear display of API responses and performance metrics
- ⚡ **Real-time Updates** - Instant feedback on API calls and response times

## Quick Start

1. **Start the API Server**
   ```bash
   # From the project root
   python api_server.py
   ```

2. **Open the Frontend**
   - Open `frontend/src/index.html` in your browser
   - Or serve it using a local web server:
     ```bash
     # Using Python's built-in server
     cd frontend/src
     python -m http.server 8080
     ```
     Then visit `http://localhost:8080`

## Configuration

The frontend automatically configures itself based on the selected environment:

- **Local**: `http://localhost:8000`
- **Development**: `https://dev-api.finsight.example.com`
- **Production**: `https://api.finsight.example.com`

To update these endpoints, modify the environment configuration in `app.js`.

## Development

### Project Structure

```
frontend/
├── src/
│   ├── index.html    # Main HTML file
│   ├── app.js        # Application logic
│   └── styles.css    # Custom styles
└── README.md         # This file
```

### Customization

- **Styling**: Modify `styles.css` to change the appearance
- **Behavior**: Update `app.js` to modify functionality
- **Layout**: Edit `index.html` to change the structure

## API Testing

The frontend supports testing the following API endpoints:

1. **Enrichment Endpoint**
   ```json
   POST /enrich
   {
     "content": "Apple (AAPL) stock is trading at $195",
     "enrichment_types": ["stock_data", "market_context"],
     "format_style": "enhanced"
   }
   ```

2. **Health Check**
   ```
   GET /health
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details 
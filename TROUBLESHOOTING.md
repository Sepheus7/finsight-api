# FinSight UI Troubleshooting Guide

## Issue: UI Buttons Not Responding

### Quick Diagnosis Steps

1. **Open Browser Developer Tools**
   - Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - Go to the **Console** tab
   - Look for any JavaScript errors (red text)

2. **Check Network Tab**
   - Go to the **Network** tab in Developer Tools
   - Refresh the page
   - Verify these files are loading successfully (status 200):
     - `/static/styles.css`
     - `/static/app-simple.js` (or `/static/app.js`)
     - `/static/api.js` (if using full version)

3. **Test JavaScript Execution**
   - In the Console tab, type: `console.log('Test')`
   - Press Enter - you should see "Test" printed
   - If this doesn't work, JavaScript is disabled

### Current Setup

The UI has been temporarily switched to a **simplified version** for debugging:

- Using `/static/app-simple.js` instead of the full app
- Simplified API client built-in
- Enhanced console logging for debugging

### Test URLs

1. **Main Interface**: <http://localhost:8000/>
2. **Debug Interface**: <http://localhost:8000/static/debug.html>
3. **Simple Test**: <http://localhost:8000/static/test.html>
4. **API Health**: <http://localhost:8000/health>

### Expected Console Output

When the page loads, you should see:

```text
FinSight Simple App Loading...
DOM loaded, initializing simple app...
Element check:
  testEnrichment: FOUND
  testFactCheck: FOUND
  testCompliance: FOUND
  ...
Enrichment listener added
Fact check listener added
Compliance listener added
Simple app initialized successfully
Checking API health...
API health check successful: {...}
```

### Common Issues & Solutions

#### 1. JavaScript Not Loading

**Symptoms**: No console output, buttons don't respond
**Solutions**:

- Check if JavaScript is enabled in browser
- Verify server is serving static files correctly
- Check for CORS issues

#### 2. API Requests Failing

**Symptoms**: Console shows "API request failed" errors
**Solutions**:

- Verify server is running: `curl http://localhost:8000/health`
- Check for CORS headers in server response
- Verify API endpoints are working

#### 3. DOM Elements Not Found

**Symptoms**: Console shows "MISSING" for elements
**Solutions**:

- Verify HTML structure is correct
- Check for typos in element IDs
- Ensure scripts load after DOM is ready

#### 4. CORS Issues

**Symptoms**: "Access to fetch at ... has been blocked by CORS policy"
**Solutions**:

- Server should include CORS headers
- For local testing, try disabling CORS in browser (not recommended for production)

### Manual Testing Commands

Test API endpoints directly:

```bash
# Health check
curl http://localhost:8000/health

# Enrichment test
curl -X POST http://localhost:8000/enrich \
  -H "Content-Type: application/json" \
  -d '{"content": "Apple stock is trading at $195"}'

# Compliance test
curl -X POST http://localhost:8000/compliance \
  -H "Content-Type: application/json" \
  -d '{"content": "Buy Apple stock now! Guaranteed profits!"}'

# Fact check test
curl -X POST http://localhost:8000/fact-check \
  -H "Content-Type: application/json" \
  -d '{"content": "Apple stock is trading at $150"}'
```

### Browser-Specific Issues

#### Safari

- May have stricter CORS policies
- Check if "Develop" menu is enabled
- Try in private browsing mode

#### Chrome

- Check for ad blockers interfering
- Try incognito mode
- Check console for security warnings

#### Firefox

- Similar to Chrome
- Check for tracking protection interference

### Debugging Steps

1. **Open <http://localhost:8000/static/test.html>**
   - This is the simplest test page
   - Should show "Click Me!" button that works
   - If this doesn't work, JavaScript is completely broken

2. **Open <http://localhost:8000/static/debug.html>**
   - More comprehensive test interface
   - Tests API connectivity
   - Shows detailed error messages

3. **Open <http://localhost:8000/>**
   - Main interface with simplified JavaScript
   - Check console for detailed logging
   - All buttons should work and show console messages

### Restoring Full Functionality

Once basic functionality is confirmed working, restore the full app:

```bash
# Edit frontend/src/index.html and change:
<script src="/static/app-simple.js"></script>

# Back to:
<script src="/static/api.js"></script>
<script src="/static/app.js"></script>
```

### Server Status

Verify the server is running correctly:

- Server should be on port 8000
- Health endpoint should return JSON with status "healthy"
- All three main endpoints should be available: `/enrich`, `/fact-check`, `/compliance`

### Next Steps

1. Try the test pages first
2. Check browser console for errors
3. Verify API endpoints work with curl
4. If simplified version works, gradually restore full functionality
5. Report specific error messages for further debugging

### Contact Information

If issues persist, provide:

1. Browser type and version
2. Console error messages (screenshots)
3. Network tab showing failed requests
4. Operating system
5. Which test pages work/don't work

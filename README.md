# App Store Webhook Proxy

A robust Azure Functions-based proxy service that receives App Store Connect Server-to-Server notifications and fans them out to multiple backend services with error handling and monitoring capabilities.

## 🚀 Features

- **Multi-Backend Support**: Dynamically discovers and forwards webhooks to multiple backend services
- **Error Handling**: Graceful failure handling with detailed error reporting
- **Backend Filtering**: Enable/disable individual backends without code changes
- **Header Preservation**: Maintains all Apple-specific headers for signature validation
- **Scalable Architecture**: Easy to add new backends via environment variables
- **Production Ready**: Comprehensive logging and monitoring support

## 🏗️ Architecture

The proxy receives App Store Connect notifications and forwards them to all active backend services configured via environment variables. It preserves all headers (especially `X-Apple-Signature` and `X-Apple-Notification-Type`) and the original JSON payload.

```
App Store Connect → Azure Functions Proxy → Backend 1
                                         → Backend 2
                                         → Backend N
```

## 📋 Requirements

- Python 3.11 (required for Azure Functions deployment)
- Azure Functions Core Tools v4
- Azure Functions Python Worker Runtime v2
- VS Code with Azure Functions extension (recommended for deployment)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd appstore-webhook-proxy
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (see Configuration section)

4. **Run locally:**
   ```bash
   func host start
   ```

## ⚙️ Configuration

Configure your backends using environment variables in `local.settings.json` (local development) or Application Settings (Azure deployment):

```json
{
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "BACKEND_1_URL": "https://your-backend-1.com/webhook",
    "BACKEND_1_ACTIVE": "true",
    "BACKEND_2_URL": "https://your-backend-2.com/webhook", 
    "BACKEND_2_ACTIVE": "true",
    "BACKEND_3_URL": "https://your-backend-3.com/webhook",
    "BACKEND_3_ACTIVE": "false"
  }
}
```

### Environment Variables

- `BACKEND_N_URL`: The webhook endpoint URL for backend N
- `BACKEND_N_ACTIVE`: Set to `"true"` to enable, `"false"` to disable (default: `"true"`)

The proxy automatically discovers all `BACKEND_*_URL` variables and processes them sequentially.

## 🔗 API Endpoints

### GET /api/health

**Description:** Health check endpoint for monitoring the proxy status and backend configuration.

**Authentication:** Requires function key (`?code=YOUR_FUNCTION_KEY`)

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "Fri, 18 Jul 2025 07:00:00 GMT", 
  "total_backends": 2,
  "active_backends": 1,
  "backend_urls": ["https://your-backend-1.com/webhook"]
}
```

### POST /api/webhook

**Description:** Receives App Store Connect notifications and forwards them to configured backends.

**Authentication:** Anonymous (no authentication required for webhook endpoint)

**Headers:**
- `Content-Type: application/json`
- `X-Apple-Signature`: Apple's signature for webhook validation
- `X-Apple-Notification-Type`: Type of notification (e.g., `SUBSCRIBED`, `DID_CHANGE_RENEWAL_STATUS`)

**Response:**
- `200 OK`: All active backends received the webhook successfully
- `500 Internal Server Error`: One or more backends failed to receive the webhook

**Error Response Body:**
```
Failed to deliver to: https://backend1.com/webhook, https://backend2.com/webhook
```

## 🧪 Testing

We've thoroughly tested the webhook proxy with various scenarios:

### Local Testing Setup

1. **Start the test servers:**
   ```bash
   # Terminal 1 - Backend 1
   python3 test_server.py 8001
   
   # Terminal 2 - Backend 2  
   python3 test_server.py 8002
   ```

2. **Update local.settings.json:**
   ```json
   {
     "Values": {
       "BACKEND_1_URL": "http://localhost:8001/webhook",
       "BACKEND_1_ACTIVE": "true",
       "BACKEND_2_URL": "http://localhost:8002/webhook",
       "BACKEND_2_ACTIVE": "true"
     }
   }
   ```

3. **Start the Azure Functions:**
   ```bash
   func host start
   ```

### Test Scenarios

#### ✅ Test 1: Basic Functionality
```bash
curl -X POST http://localhost:7071/api/webhook \
  -H "Content-Type: application/json" \
  -H "X-Apple-Signature: sha256=test-signature" \
  -H "X-Apple-Notification-Type: DID_CHANGE_RENEWAL_STATUS" \
  -d '{
    "notificationType": "DID_CHANGE_RENEWAL_STATUS",
    "subtype": "AUTO_RENEW_ENABLED",
    "notificationUUID": "test-uuid-123",
    "data": {
      "bundleId": "com.example.app",
      "environment": "Sandbox"
    }
  }'
```

**Expected:** Returns `200 OK`, both backends receive the webhook with preserved headers.

#### ✅ Test 2: Error Handling (Backend Failure)
```bash
# Stop one backend server
kill $(lsof -ti:8002)

# Send webhook
curl -X POST http://localhost:7071/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

**Expected:** Returns `500 Internal Server Error` with failure details, working backend still receives webhook.

#### ✅ Test 3: Different Notification Types
```bash
curl -X POST http://localhost:7071/api/webhook \
  -H "Content-Type: application/json" \
  -H "X-Apple-Notification-Type: SUBSCRIBED" \
  -d '{
    "notificationType": "SUBSCRIBED",
    "subtype": "INITIAL_BUY",
    "data": {
      "bundleId": "com.example.app",
      "productId": "premium_subscription"
    }
  }'
```

**Expected:** Returns `200 OK`, handles different notification types correctly.

### Testing Deployed Endpoints

Once deployed to Azure, test your endpoints:

#### Health Check Test
```bash
curl "https://your-function-app.azurewebsites.net/api/health?code=YOUR_FUNCTION_KEY"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "Fri, 18 Jul 2025 07:00:00 GMT",
  "total_backends": 2,
  "active_backends": 1, 
  "backend_urls": ["https://your-backend-1.com/webhook"]
}
```

#### Webhook Test
```bash
curl -X POST "https://your-function-app.azurewebsites.net/api/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Apple-Signature: test-signature" \
  -H "X-Apple-Notification-Type: DID_CHANGE_RENEWAL_STATUS" \
  -d '{
    "notificationType": "DID_CHANGE_RENEWAL_STATUS",
    "data": {"bundleId": "com.example.app"}
  }'
```

**Expected:** Returns `200 OK` if backends configured, or `500` with "No active backends configured" if not yet configured.

#### ✅ Test 4: Backend Filtering
```bash
# Set BACKEND_2_ACTIVE to "false" in local.settings.json
# Restart functions and send webhook
```

**Expected:** Returns `200 OK`, only active backends receive the webhook.

### Test Results Summary

- ✅ **Basic Functionality**: Successfully forwards webhooks to all active backends
- ✅ **Error Handling**: Returns 500 status with specific failure details
- ✅ **Partial Failure Resilience**: Working backends continue to receive webhooks
- ✅ **Header Preservation**: All Apple headers correctly forwarded
- ✅ **JSON Payload Integrity**: Webhook data preserved exactly as received
- ✅ **Multiple Notification Types**: Supports all App Store notification types
- ✅ **Backend Filtering**: Inactive backends correctly skipped
- ✅ **Dynamic Backend Discovery**: Automatically finds all configured backends

## 🚀 Deployment

### Option 1: VS Code Deployment (Recommended)

1. **Install VS Code Azure Functions Extension:**
   - Install the Azure Functions extension in VS Code
   - Sign in to your Azure account

2. **Setup Python 3.11 Environment:**
   ```bash
   # Install Python 3.11 using pyenv (macOS)
   pyenv install 3.11.9
   pyenv local 3.11.9
   
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Deploy from VS Code:**
   - Press `Cmd+Shift+P` (or `Ctrl+Shift+P` on Windows)
   - Type "Azure Functions: Deploy to Function App"
   - Select your Azure subscription
   - Choose "Create new Function App" or select existing one
   - Select Python 3.11 runtime
   - Wait for deployment to complete

4. **Configure Environment Variables:**
   - In VS Code Azure extension, navigate to your Function App
   - Right-click → "Edit Settings"
   - Add your backend configuration variables

### Option 2: Azure CLI Deployment

1. **Create an Azure Functions App:**
   ```bash
   az functionapp create \
     --resource-group myResourceGroup \
     --consumption-plan-location westus \
     --runtime python \
     --runtime-version 3.11 \
     --functions-version 4 \
     --name myAppStoreWebhookProxy \
     --storage-account mystorageaccount
   ```

2. **Configure Application Settings:**
   ```bash
   az functionapp config appsettings set \
     --name myAppStoreWebhookProxy \
     --resource-group myResourceGroup \
     --settings \
     "BACKEND_1_URL=https://your-backend-1.com/webhook" \
     "BACKEND_1_ACTIVE=true" \
     "BACKEND_2_URL=https://your-backend-2.com/webhook" \
     "BACKEND_2_ACTIVE=true"
   ```

3. **Deploy the function:**
   ```bash
   func azure functionapp publish myAppStoreWebhookProxy
   ```

### Production Deployment Example

**Deployed Function App:** `wizad-webhook-proxy`
- **Health Endpoint:** `https://wizad-webhook-proxy.azurewebsites.net/api/health?code=YOUR_FUNCTION_KEY`
- **Webhook Endpoint:** `https://wizad-webhook-proxy.azurewebsites.net/api/webhook`

### App Store Connect Configuration

Use the clean webhook URL in App Store Connect (no authentication parameters needed):
```
https://your-function-app.azurewebsites.net/api/webhook
```

### Environment Variables for Production

Set these in your Azure Function App settings:

```
BACKEND_1_URL=https://your-primary-backend.com/webhook
BACKEND_1_ACTIVE=true
BACKEND_2_URL=https://your-secondary-backend.com/webhook  
BACKEND_2_ACTIVE=true
BACKEND_3_URL=https://your-analytics-backend.com/webhook
BACKEND_3_ACTIVE=true
```

## 📊 Monitoring

The proxy includes comprehensive logging for monitoring:

- **Success:** Logs successful delivery to all backends
- **Failures:** Logs specific backend failures with URLs and error details
- **Configuration:** Logs discovered backends and their status at startup

View logs in Azure Portal under your Function App → Monitor → Logs.

## 🔒 Security

- **Anonymous Webhook Access**: The webhook endpoint (`/api/webhook`) allows anonymous access for App Store Connect
- **Secured Health Check**: The health endpoint (`/api/health`) requires function key authentication
- **Signature Validation**: The proxy forwards Apple's `X-Apple-Signature` header to backends for validation
- **HTTPS Only**: Ensure all backend URLs use HTTPS in production
- **Backend Validation**: Each backend should validate the Apple signature independently

### Function Keys

- **Health Check**: Requires function key for monitoring access
  ```bash
  curl "https://your-app.azurewebsites.net/api/health?code=YOUR_FUNCTION_KEY"
  ```
- **Webhook**: No authentication required (anonymous access for App Store Connect)
  ```bash
  curl -X POST "https://your-app.azurewebsites.net/api/webhook" -d "{...}"
  ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the Azure Functions logs for debugging information
- Verify backend endpoints are accessible and responding correctly

---

**Note:** This proxy is designed for production use with proper error handling, logging, and monitoring. Always test thoroughly in a staging environment before deploying to production.
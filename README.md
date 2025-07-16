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

- Python 3.8+
- Azure Functions Core Tools
- Azure Functions Python Worker Runtime

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

### POST /api/webhook

**Description:** Receives App Store Connect notifications and forwards them to configured backends.

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

### Azure Functions Deployment

1. **Create an Azure Functions App:**
   ```bash
   az functionapp create \
     --resource-group myResourceGroup \
     --consumption-plan-location westus \
     --runtime python \
     --runtime-version 3.9 \
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

4. **Configure App Store Connect:**
   - Use the Azure Functions URL: `https://myAppStoreWebhookProxy.azurewebsites.net/api/webhook`
   - Set up your webhook endpoint in App Store Connect

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

- **Signature Validation**: The proxy forwards Apple's `X-Apple-Signature` header to backends for validation
- **Function-Level Authentication**: Uses Azure Functions' built-in authentication (`AuthLevel.FUNCTION`)
- **HTTPS Only**: Ensure all backend URLs use HTTPS in production
- **Backend Validation**: Each backend should validate the Apple signature independently

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
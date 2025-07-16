#!/bin/bash
# Azure Functions Deployment Script

set -e

# Configuration
RESOURCE_GROUP="your-resource-group"
FUNCTION_APP_NAME="your-function-app-name"
STORAGE_ACCOUNT="your-storage-account"
LOCATION="eastus"

# TODO: Update these with your actual backend URLs before deployment
BACKEND_1_URL="https://your-backend-1.com/webhook"
BACKEND_2_URL="https://your-backend-2.com/webhook"

echo "🚀 Starting Azure Functions deployment..."

# Create resource group
echo "📁 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
echo "💾 Creating storage account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create function app
echo "⚡ Creating function app..."
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name $FUNCTION_APP_NAME \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux

# Configure app settings (add your backend URLs here)
echo "⚙️ Configuring app settings..."
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
  "BACKEND_1_URL=$BACKEND_1_URL" \
  "BACKEND_1_ACTIVE=true" \
  "BACKEND_2_URL=$BACKEND_2_URL" \
  "BACKEND_2_ACTIVE=true"

# Deploy function
echo "🚢 Deploying function code..."
func azure functionapp publish $FUNCTION_APP_NAME

echo "✅ Deployment complete!"
echo "📋 Function App URL: https://$FUNCTION_APP_NAME.azurewebsites.net"
echo "🔗 Webhook URL: https://$FUNCTION_APP_NAME.azurewebsites.net/api/webhook"
echo "❤️ Health Check: https://$FUNCTION_APP_NAME.azurewebsites.net/api/health"

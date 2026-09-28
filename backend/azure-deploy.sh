#!/bin/bash
# ==============================================================================
# JEEVAN-MITRA 2.0 - AZURE DEPLOYMENT SCRIPT (Bash / Azure Cloud Shell)
# ==============================================================================
set -e

RESOURCE_GROUP="rg-jeevanmitra"
LOCATION="centralindia"
ACR_NAME="acrjeevanmitra$RANDOM"
APP_NAME="jeevanmitra-backend"
ENV_NAME="env-jeevanmitra"

echo "================================================================"
echo "  JeevanMitra 2.0 - Microsoft Azure Deployment (Bash)"
echo "================================================================"

# 1. Login check
if ! az account show > /dev/null 2>&1; then
    echo "Logging into Azure..."
    az login
fi

# 2. Resource Group
echo "[1/5] Creating Resource Group: $RESOURCE_GROUP ($LOCATION)..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o table

# 3. Azure Container Registry (ACR)
echo "[2/5] Creating ACR: $ACR_NAME..."
az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic --admin-enabled true -o table

# 4. Cloud Build in ACR
echo "[3/5] Building Docker image in ACR (Cloud Build)..."
az acr build --registry "$ACR_NAME" --image "${APP_NAME}:latest" .

# 5. Container Apps Environment
echo "[4/5] Setting up Azure Container Apps Environment: $ENV_NAME..."
az extension add --name containerapp --upgrade --yes
az containerapp env create \
    --name "$ENV_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    -o table

# 6. Deploy Container App
echo "[5/5] Deploying Container App: $APP_NAME..."
ACR_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_USER=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASS=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

az containerapp create \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$ENV_NAME" \
    --image "${ACR_SERVER}/${APP_NAME}:latest" \
    --target-port 4000 \
    --ingress external \
    --registry-server "$ACR_SERVER" \
    --registry-username "$ACR_USER" \
    --registry-password "$ACR_PASS" \
    --cpu 0.5 \
    --memory 1.0Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --env-vars \
        NODE_ENV="production" \
        PORT="4000" \
        HOST="0.0.0.0" \
        DATABASE_PATH="/app/data/jeevanmitra.db" \
        DEFAULT_DISTRICT="Moradabad" \
        DEFAULT_STATE="Uttar Pradesh" \
        AI_PROVIDER="mock" \
        CONFIDENCE_THRESHOLD="0.75" \
    -o table

APP_URL=$(az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)

echo "================================================================"
echo "  DEPLOYMENT SUCCESSFUL!"
echo "  Service URL:       https://$APP_URL"
echo "  Health Endpoint:   https://$APP_URL/api/health"
echo "  Planning Matrix:   https://$APP_URL/api/planning/supply-gap-matrix?district=Moradabad"
echo "================================================================"

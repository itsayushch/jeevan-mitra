# JeevanMitra 2.0 - Microsoft Azure Deployment Guide

This guide provides instructions for deploying the **JeevanMitra 2.0 Backend** Docker container to Microsoft Azure.

---

## Architecture on Microsoft Azure

```
   [Beneficiaries / VLE Workers / District Officers]
                           │
                           ▼ HTTPS (Port 443)
              ┌────────────────────────┐
              │  Azure Front Door /    │
              │  Azure Container Apps  │
              │  Ingress Controller    │
              └────────────┬───────────┘
                           │
                           ▼ Port 4000
              ┌────────────────────────┐
              │  JeevanMitra 2.0       │
              │  Docker Container      │
              │  (Node.js 22 LTS)      │
              └────────────┬───────────┘
                           │
                           ▼ Mount /app/data
              ┌────────────────────────┐
              │  Azure Files Storage   │
              │  (Persistent SQLite    │
              │   Database Volume)     │
              └────────────────────────┘
```

---

## Deployment Options

We provide two production deployment options:
* **Option 1: Azure Container Apps (ACA) — Recommended:** Serverless, auto-scales down to zero or up based on HTTP traffic, built-in TLS, lowest cost.
* **Option 2: Azure App Service (Web App for Containers):** Traditional PaaS with dedicated compute instances.

> **Cloud Build Feature:** You do **not** need Docker Desktop running on your local machine. Azure Container Registry (ACR) builds the container directly in the cloud via `az acr build`.

---

## Automated Deployment (One-Click Scripts)

### On Windows (PowerShell)
```powershell
cd backend
.\azure-deploy.ps1 -ResourceGroup "rg-jeevanmitra" -Location "centralindia"
```

### On Linux / macOS / Azure Cloud Shell (Bash)
```bash
cd backend
chmod +x azure-deploy.sh
./azure-deploy.sh
```

---

## Manual Step-by-Step Deployment (Azure CLI)

### Step 1: Login to Azure
```bash
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID_OR_NAME>"
```

### Step 2: Create Resource Group
```bash
az group create \
  --name rg-jeevanmitra \
  --location centralindia
```

### Step 3: Create Azure Container Registry (ACR)
```bash
az acr create \
  --resource-group rg-jeevanmitra \
  --name acrjeevanmitra \
  --sku Basic \
  --admin-enabled true
```

### Step 4: Build Docker Image Directly in Azure (No local Docker needed)
```bash
cd backend
az acr build \
  --registry acrjeevanmitra \
  --image jeevanmitra-backend:latest .
```

### Step 5: Create Azure Container Apps Environment
```bash
az extension add --name containerapp --upgrade --yes

az containerapp env create \
  --name env-jeevanmitra \
  --resource-group rg-jeevanmitra \
  --location centralindia
```

### Step 6: Deploy the Container App
```bash
ACR_SERVER=$(az acr show --name acrjeevanmitra --query loginServer -o tsv)
ACR_USER=$(az acr credential show --name acrjeevanmitra --query username -o tsv)
ACR_PASS=$(az acr credential show --name acrjeevanmitra --query "passwords[0].value" -o tsv)

az containerapp create \
  --name jeevanmitra-backend \
  --resource-group rg-jeevanmitra \
  --environment env-jeevanmitra \
  --image "$ACR_SERVER/jeevanmitra-backend:latest" \
  --target-port 4000 \
  --ingress external \
  --registry-server "$ACR_SERVER" \
  --registry-username "$ACR_USER" \
  --registry-password "$ACR_PASS" \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 5 \
  --env-vars \
    NODE_ENV=production \
    PORT=4000 \
    HOST=0.0.0.0 \
    DATABASE_PATH=/app/data/jeevanmitra.db \
    DEFAULT_DISTRICT=Moradabad \
    DEFAULT_STATE="Uttar Pradesh" \
    AI_PROVIDER=mock \
    CONFIDENCE_THRESHOLD=0.75
```

Retrieve the application URL:
```bash
az containerapp show \
  --name jeevanmitra-backend \
  --resource-group rg-jeevanmitra \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv
```

---

## Persistent Storage: Azure Files Volume Mount for SQLite

To persist data permanently across container revisions and scaling:

1. **Create an Azure Storage Account & File Share**:
   ```bash
   az storage account create \
     --name stjeevanmitra \
     --resource-group rg-jeevanmitra \
     --location centralindia \
     --sku Standard_LRS

   STORAGE_KEY=$(az storage account keys list --account-name stjeevanmitra --resource-group rg-jeevanmitra --query "[0].value" -o tsv)

   az storage share create \
     --account-name stjeevanmitra \
     --account-key "$STORAGE_KEY" \
     --name jeevanmitra-data
   ```

2. **Link the Storage Share to Container Apps Environment**:
   ```bash
   az containerapp env storage set \
     --name env-jeevanmitra \
     --resource-group rg-jeevanmitra \
     --storage-name data-share \
     --azure-file-account-name stjeevanmitra \
     --azure-file-account-key "$STORAGE_KEY" \
     --azure-file-share-name jeevanmitra-data \
     --access-mode ReadWrite
   ```

3. **Mount the Storage to the Container App at `/app/data`**:
   Add `--volume-mounts` and `--volumes` to your container definition.

---

## Option 2: Deploying to Azure App Service (Web App for Containers)

```bash
# 1. Create an App Service Plan (B1 Basic or higher)
az appservice plan create \
  --name plan-jeevanmitra \
  --resource-group rg-jeevanmitra \
  --location centralindia \
  --is-linux \
  --sku B1

# 2. Create the Web App with the Docker image
az webapp create \
  --resource-group rg-jeevanmitra \
  --plan plan-jeevanmitra \
  --name app-jeevanmitra-backend \
  --deployment-container-image-name "$ACR_SERVER/jeevanmitra-backend:latest"

# 3. Configure App Settings & Port
az webapp config appsettings set \
  --resource-group rg-jeevanmitra \
  --name app-jeevanmitra-backend \
  --settings \
    WEBSITES_PORT=4000 \
    NODE_ENV=production \
    PORT=4000 \
    HOST=0.0.0.0 \
    DATABASE_PATH=/app/data/jeevanmitra.db \
    DEFAULT_DISTRICT=Moradabad \
    AI_PROVIDER=mock
```

---

## Production Verification

After deployment, test the live endpoints:
* **Health Check Probe:** `curl https://<APP_URL>/api/health`
* **Root API Info:** `curl https://<APP_URL>/`
* **Planning Supply-Gap Matrix:** `curl https://<APP_URL>/api/planning/supply-gap-matrix?district=Moradabad`
* **Audit Ledger:** `curl https://<APP_URL>/api/audit-events`

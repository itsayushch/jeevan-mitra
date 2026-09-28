# ==============================================================================
# JEEVAN-MITRA 2.0 - AZURE DEPLOYMENT SCRIPT (PowerShell)
# Deploys Backend Docker Container to Azure Container Apps (ACA) or App Service
# ==============================================================================

param (
    [string]$ResourceGroup = "rg-jeevanmitra",
    [string]$Location = "centralindia",
    [string]$AcrName = "acrjeevanmitra$((Get-Random -Minimum 1000 -Maximum 9999))",
    [string]$AppName = "jeevanmitra-backend",
    [string]$EnvironmentName = "env-jeevanmitra"
)

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  JeevanMitra 2.0 - Microsoft Azure Deployment" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 1. Check Azure CLI
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI ('az') is not installed. Please install it from https://aka.ms/installazurecliwindows"
    exit 1
}

Write-Host "[1/6] Verifying Azure Login..." -ForegroundColor Yellow
$account = az account show --output json 2>$null
if (-not $account) {
    Write-Host "Logging in to Azure..." -ForegroundColor Yellow
    az login
}

# 2. Create Resource Group
Write-Host "[2/6] Ensuring Resource Group '$ResourceGroup' in '$Location'..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location --output table

# 3. Create Azure Container Registry (ACR)
Write-Host "[3/6] Creating Azure Container Registry '$AcrName'..." -ForegroundColor Yellow
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true --output table

# 4. Build Docker Image directly in ACR (Cloud Build - no local Docker daemon needed!)
Write-Host "[4/6] Building Docker image in Azure Container Registry (Cloud Build)..." -ForegroundColor Yellow
az acr build --registry $AcrName --image "${AppName}:latest" .

# 5. Create Azure Container Apps Environment
Write-Host "[5/6] Creating Azure Container Apps Managed Environment '$EnvironmentName'..." -ForegroundColor Yellow
az extension add --name containerapp --upgrade --yes
az containerapp env create `
    --name $EnvironmentName `
    --resource-group $ResourceGroup `
    --location $Location `
    --output table

# 6. Deploy Container App
Write-Host "[6/6] Deploying Container App '$AppName'..." -ForegroundColor Yellow
$acrServer = az acr show --name $AcrName --query loginServer --output tsv
$acrUsername = az acr credential show --name $AcrName --query username --output tsv
$acrPassword = az acr credential show --name $AcrName --query "passwords[0].value" --output tsv

az containerapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --environment $EnvironmentName `
    --image "${acrServer}/${AppName}:latest" `
    --target-port 4000 `
    --ingress external `
    --registry-server $acrServer `
    --registry-username $acrUsername `
    --registry-password $acrPassword `
    --cpu 0.5 `
    --memory 1.0Gi `
    --min-replicas 1 `
    --max-replicas 3 `
    --env-vars `
        NODE_ENV="production" `
        PORT="4000" `
        HOST="0.0.0.0" `
        DATABASE_PATH="/app/data/jeevanmitra.db" `
        DEFAULT_DISTRICT="Moradabad" `
        DEFAULT_STATE="Uttar Pradesh" `
        AI_PROVIDER="mock" `
        CONFIDENCE_THRESHOLD="0.75" `
    --output table

$appUrl = az containerapp show --name $AppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" --output tsv

Write-Host "================================================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "  Service URL:       https://$appUrl" -ForegroundColor Green
Write-Host "  Health Endpoint:   https://$appUrl/api/health" -ForegroundColor Green
Write-Host "  Planning Matrix:   https://$appUrl/api/planning/supply-gap-matrix?district=Moradabad" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    [string]$Location = "eastus",
    [string]$AcrName = "candidatevalidationacr",
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

Write-Host "=== Deploying Candidate Validation Platform to Azure ===" -ForegroundColor Green

$acrLoginServer = "$AcrName.azurecr.io"
$imageName = "$acrLoginServer/candidate-validation-backend:latest"

if (-not $WhatIf) {
    # Login
    az account show --output none 2>$null
    if (-not $?) {
        az login --output none
    }

    # Create resource group
    az group create --name $ResourceGroupName --location $Location --output none

    # Create ACR
    az acr create --resource-group $ResourceGroupName --name $AcrName --sku Basic --admin-enabled true --output none

    # Build and push Docker image
    az acr build --registry $AcrName --image "candidate-validation-backend:latest" --file backend/Dockerfile .

    # Create App Service plan
    az appservice plan create `
        --resource-group $ResourceGroupName `
        --name "${AppName}-plan" `
        --location $Location `
        --sku B1 `
        --is-linux `
        --output none

    # Create web app
    az webapp create `
        --resource-group $ResourceGroupName `
        --plan "${AppName}-plan" `
        --name $AppName `
        --deployment-container-image-name $imageName `
        --output none

    # Configure app settings
    az webapp config appsettings set `
        --resource-group $ResourceGroupName `
        --name $AppName `
        --settings `
            AZURE_STORAGE_CONNECTION_STRING="@Microsoft.KeyVault(VaultName=${AppName}-kv;SecretName=storage-connection-string)" `
            AZURE_STORAGE_CONTAINER_NAME="validation-reports" `
            AZURE_STORAGE_SAS_EXPIRY_HOURS=48 `
            LOG_LEVEL="INFO" `
            CORS_ORIGINS="*" `
        --output none

    # Enable container logging
    az webapp log config `
        --resource-group $ResourceGroupName `
        --name $AppName `
        --docker-container-logging filesystem `
        --output none

    Write-Host "Deployment complete!" -ForegroundColor Green
    Write-Host "App URL: https://$AppName.azurewebsites.net" -ForegroundColor Cyan
} else {
    Write-Host "WhatIf mode - would run:" -ForegroundColor Yellow
    Write-Host "  ResourceGroup: $ResourceGroupName"
    Write-Host "  AppName: $AppName"
    Write-Host "  Location: $Location"
    Write-Host "  ACR: $AcrName"
    Write-Host "  Image: $imageName"
}

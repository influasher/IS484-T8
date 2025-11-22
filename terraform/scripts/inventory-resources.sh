#!/bin/bash
set -e

RESOURCE_GROUP="${1:-sentifinance.azurecr.io}"
OUTPUT_DIR="terraform/environments/production"

echo "📋 Inventorying resources in $RESOURCE_GROUP..."
echo ""

# Get all resources in resource group
echo "All resources:"
az resource list --resource-group $RESOURCE_GROUP --query "[].{Name:name, Type:type, Location:location}" -o table

# Save detailed JSON
az resource list --resource-group $RESOURCE_GROUP --output json > $OUTPUT_DIR/resource-inventory.json
echo ""
echo "✅ Detailed inventory saved to $OUTPUT_DIR/resource-inventory.json"
echo ""

# Generate resource IDs for import
echo "📝 Generating resource IDs for import..."
echo ""

echo "# Resource IDs for Terraform Import" > $OUTPUT_DIR/resource-ids.sh
echo "# Generated: $(date)" >> $OUTPUT_DIR/resource-ids.sh
echo "" >> $OUTPUT_DIR/resource-ids.sh

# Resource Group
RG_ID=$(az group show --name $RESOURCE_GROUP --query id -o tsv)
echo "export RG_ID='$RG_ID'" >> $OUTPUT_DIR/resource-ids.sh

# AKS
AKS_ID=$(az aks list --resource-group $RESOURCE_GROUP --query "[0].id" -o tsv)
if [ -n "$AKS_ID" ]; then
  echo "export AKS_ID='$AKS_ID'" >> $OUTPUT_DIR/resource-ids.sh
  echo "  ✓ AKS cluster found"
fi

# ACR
ACR_ID=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].id" -o tsv)
if [ -n "$ACR_ID" ]; then
  echo "export ACR_ID='$ACR_ID'" >> $OUTPUT_DIR/resource-ids.sh
  echo "  ✓ Container Registry found"
fi

# Key Vault
KV_ID=$(az keyvault list --resource-group $RESOURCE_GROUP --query "[0].id" -o tsv)
if [ -n "$KV_ID" ]; then
  echo "export KV_ID='$KV_ID'" >> $OUTPUT_DIR/resource-ids.sh
  echo "  ✓ Key Vault found"
fi

# PostgreSQL
PSQL_ID=$(az postgres flexible-server list --resource-group $RESOURCE_GROUP --query "[0].id" -o tsv)
if [ -n "$PSQL_ID" ]; then
  echo "export PSQL_ID='$PSQL_ID'" >> $OUTPUT_DIR/resource-ids.sh
  echo "  ✓ PostgreSQL server found"
fi

# VNet
VNET_ID=$(az network vnet list --resource-group $RESOURCE_GROUP --query "[0].id" -o tsv)
if [ -n "$VNET_ID" ]; then
  echo "export VNET_ID='$VNET_ID'" >> $OUTPUT_DIR/resource-ids.sh
  echo "  ✓ Virtual Network found"
fi

echo ""
echo "✅ Resource IDs saved to $OUTPUT_DIR/resource-ids.sh"
echo ""
echo "To use these IDs:"
echo "  source $OUTPUT_DIR/resource-ids.sh"

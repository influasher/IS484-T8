#!/usr/bin/env bash
set -euo pipefail

# Script to add secrets from Backend/.env to GitHub Actions
# Usage: ./add_secrets_to_gha.sh

REPO="influasher/IS484-T8"
ENV_FILE="Backend/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: $ENV_FILE not found"
    exit 1
fi

echo "📋 Reading secrets from $ENV_FILE..."
echo ""

# Function to add a secret
add_secret() {
    local key=$1
    local value=$2
    
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $key (empty value)"
        return
    fi
    
    echo "Adding $key..."
    echo "$value" | gh secret set "$key" --repo "$REPO"
    
    if [ $? -eq 0 ]; then
        echo "✅ $key added successfully"
    else
        echo "❌ Failed to add $key"
    fi
    echo ""
}

# Parse .env file and add each secret
while IFS='=' read -r key value || [ -n "$key" ]; do
    # Skip empty lines and comments
    if [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Trim whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # Remove quotes if present
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    
    # Convert key to uppercase and replace - with _
    secret_name=$(echo "$key" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
    
    add_secret "$secret_name" "$value"
    
done < "$ENV_FILE"

echo ""
echo "🎉 Done! All secrets have been added to GitHub Actions."
echo ""
echo "To verify, run:"
echo "  gh secret list --repo $REPO"

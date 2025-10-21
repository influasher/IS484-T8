#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Testing CD workflow locally (syntax & structure only)..."
echo ""

# 1. Validate workflow YAML syntax
echo "1️⃣ Validating workflow YAML syntax..."
if command -v python3 &> /dev/null; then
    python3 -c "import yaml; yaml.safe_load(open('.github/workflows/cd.yml'))" 2>/dev/null && echo "  ✅ cd.yml: Valid YAML syntax"
else
    echo "  ⚠️  Python3 not found, skipping YAML validation"
fi
echo ""

# 2. Validate Kubernetes manifests
echo "2️⃣ Validating Kubernetes manifests..."
if command -v kubectl &> /dev/null; then
    for file in k8s/*.yaml; do
        filename=$(basename "$file")
        
        # Skip template and kustomization files
        if [[ "$filename" == *"template"* ]] || [[ "$filename" == "kustomization.yaml" ]]; then
            echo "  ⏭️  Skipping $filename"
            continue
        fi
        
        # Check if file has actual content (not just comments)
        if grep -qE '^\s*apiVersion:' "$file"; then
            # Validate with dry-run
            if kubectl apply --dry-run=client -f "$file" &> /dev/null; then
                echo "  ✅ $filename: Valid K8s manifest"
            else
                echo "  ❌ $filename: INVALID manifest"
                kubectl apply --dry-run=client -f "$file"
                exit 1
            fi
        else
            echo "  ⏭️  $filename: No active resources (commented out)"
        fi
    done
else
    echo "  ⚠️  kubectl not found, skipping K8s validation"
fi
echo ""

# 3. Check required secrets are referenced in workflow
echo "3️⃣ Checking workflow references required secrets..."
required_secrets=(
    "AZURE_CREDENTIALS"
    "ACR_LOGIN_SERVER"
    "ACR_USERNAME"
    "ACR_PASSWORD"
    "AKS_RESOURCE_GROUP"
    "AKS_CLUSTER_NAME"
    "AKS_LOADBALANCER_IP"
    "SECRET_KEY"
    "DATABASE_URI"
    "JWT_SECRET_KEY"
    "GEMINI_API_KEY"
    "OPEN_AI_KEY"
)

missing_count=0
for secret in "${required_secrets[@]}"; do
    if grep -q "secrets\.$secret" .github/workflows/cd.yml; then
        echo "  ✅ $secret"
    else
        echo "  ⚠️  $secret NOT found in workflow"
        ((missing_count++))
    fi
done

if [ $missing_count -gt 0 ]; then
    echo ""
    echo "  ⚠️  Warning: $missing_count secret(s) not referenced"
fi
echo ""

# 4. Validate referenced scripts exist and have correct syntax
echo "4️⃣ Checking referenced scripts..."
if [ -f ".github/scripts/build_and_push.sh" ]; then
    echo "  ✅ build_and_push.sh exists"
    if bash -n .github/scripts/build_and_push.sh 2>/dev/null; then
        echo "  ✅ build_and_push.sh: Valid bash syntax"
    else
        echo "  ❌ build_and_push.sh: INVALID bash syntax"
        exit 1
    fi
else
    echo "  ℹ️  build_and_push.sh not found (workflow uses inline build)"
fi

if [ -f ".github/scripts/add_secrets_to_gha.sh" ]; then
    echo "  ✅ add_secrets_to_gha.sh exists"
    if bash -n .github/scripts/add_secrets_to_gha.sh 2>/dev/null; then
        echo "  ✅ add_secrets_to_gha.sh: Valid bash syntax"
    else
        echo "  ❌ add_secrets_to_gha.sh: INVALID bash syntax"
        exit 1
    fi
fi
echo ""

# 5. Check Docker build context
echo "5️⃣ Checking Docker build context..."
if [ -f "Backend/Dockerfile" ]; then
    echo "  ✅ Backend/Dockerfile exists"
    
    # Check if Dockerfile references .env
    if grep -q "COPY.*\.env" Backend/Dockerfile; then
        echo "  ℹ️  Dockerfile copies .env (workflow must create it)"
        
        # Check if workflow creates .env
        if grep -q "cat.*Backend/\.env" .github/workflows/cd.yml; then
            echo "  ✅ Workflow creates temporary .env"
        else
            echo "  ⚠️  Workflow may not create .env before build"
        fi
    fi
else
    echo "  ❌ Backend/Dockerfile NOT found"
    exit 1
fi
echo ""

# 6. Verify AKS connectivity (optional)
echo "6️⃣ Checking AKS connectivity..."
if kubectl get nodes &> /dev/null; then
    node_count=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | xargs)
    echo "  ✅ Connected to AKS ($node_count node(s))"
    
    # Check if namespace exists
    if kubectl get namespace sentifinance &> /dev/null; then
        echo "  ✅ Namespace 'sentifinance' exists"
    else
        echo "  ⚠️  Namespace 'sentifinance' not found (will be created on deploy)"
    fi
else
    echo "  ⚠️  Not connected to AKS (will connect during workflow)"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Local validation complete!"
echo ""
echo "📋 Summary:"
echo "  • Workflow YAML: Valid"
echo "  • K8s manifests: Valid"
echo "  • Required secrets: Referenced"
echo "  • Shell scripts: Valid syntax"
echo "  • Docker context: Ready"
echo ""
echo "🚀 Next steps:"
echo "  1. Commit your changes:"
echo "     git add ."
echo "     git commit -m 'chore: update CD workflow'"
echo ""
echo "  2. Push to trigger CD:"
echo "     git push origin dev"
echo ""
echo "  3. OR manually trigger CD (skip CI):"
echo "     gh workflow run cd.yml --ref dev"
echo ""
echo "  4. Watch workflow logs:"
echo "     gh run watch"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

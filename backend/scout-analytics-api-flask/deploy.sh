#!/bin/bash

# Scout Analytics - Container Deployment Script
# This script handles the complete deployment process for the Scout Analytics API

set -e  # Exit on any error

echo "🚀 Scout Analytics Container Deployment Script"
echo "=============================================="

# Configuration
API_NAME="scout-api"
VERSION="3.0"
RESOURCE_GROUP="scout-ai-group"
WEBAPP_NAME="g8h3ilc786zz"
REGISTRY_NAME="<your-acr>"  # Replace with actual Azure Container Registry name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker status..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if Azure CLI is installed and logged in
check_azure_cli() {
    print_status "Checking Azure CLI status..."
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it and try again."
        exit 1
    fi
    
    if ! az account show > /dev/null 2>&1; then
        print_error "Not logged in to Azure. Please run 'az login' and try again."
        exit 1
    fi
    print_success "Azure CLI is ready"
}

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found in current directory"
        exit 1
    fi
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found in current directory"
        exit 1
    fi
    
    docker build -t ${API_NAME}:${VERSION} .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Tag image for registry
tag_image() {
    print_status "Tagging image for Azure Container Registry..."
    
    docker tag ${API_NAME}:${VERSION} ${REGISTRY_NAME}.azurecr.io/${API_NAME}:${VERSION}
    
    if [ $? -eq 0 ]; then
        print_success "Image tagged successfully"
    else
        print_error "Failed to tag image"
        exit 1
    fi
}

# Push image to registry
push_image() {
    print_status "Pushing image to Azure Container Registry..."
    
    # Login to ACR
    az acr login --name ${REGISTRY_NAME}
    
    docker push ${REGISTRY_NAME}.azurecr.io/${API_NAME}:${VERSION}
    
    if [ $? -eq 0 ]; then
        print_success "Image pushed successfully"
    else
        print_error "Failed to push image"
        exit 1
    fi
}

# Update Azure Web App
update_webapp() {
    print_status "Updating Azure Web App configuration..."
    
    az webapp config container set \
        --name ${WEBAPP_NAME} \
        --resource-group ${RESOURCE_GROUP} \
        --docker-custom-image-name ${REGISTRY_NAME}.azurecr.io/${API_NAME}:${VERSION}
    
    if [ $? -eq 0 ]; then
        print_success "Web App updated successfully"
    else
        print_error "Failed to update Web App"
        exit 1
    fi
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Wait for deployment to complete
    print_status "Waiting for deployment to complete (30 seconds)..."
    sleep 30
    
    # Check health endpoint
    HEALTH_URL="https://${WEBAPP_NAME}.manus.space/api/health"
    
    for i in {1..5}; do
        print_status "Health check attempt $i/5..."
        
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${HEALTH_URL})
        
        if [ "$HTTP_STATUS" = "200" ]; then
            print_success "Health check passed! API is responding correctly."
            
            # Get health response
            HEALTH_RESPONSE=$(curl -s ${HEALTH_URL})
            echo "Health Response: ${HEALTH_RESPONSE}"
            return 0
        else
            print_warning "Health check failed (HTTP $HTTP_STATUS). Retrying in 10 seconds..."
            sleep 10
        fi
    done
    
    print_error "Health check failed after 5 attempts"
    return 1
}

# Update CORS settings
update_cors() {
    print_status "Updating CORS configuration..."
    
    az webapp cors add \
        --name ${WEBAPP_NAME} \
        --resource-group ${RESOURCE_GROUP} \
        --allowed-origins https://ewlwkasq.manus.space
    
    if [ $? -eq 0 ]; then
        print_success "CORS configuration updated"
    else
        print_warning "CORS update failed (may already be configured)"
    fi
}

# Main deployment function
main() {
    echo ""
    print_status "Starting Scout Analytics API deployment..."
    echo ""
    
    # Pre-deployment checks
    check_docker
    check_azure_cli
    
    # Build and deploy
    build_image
    tag_image
    push_image
    update_webapp
    
    # Post-deployment verification
    health_check
    update_cors
    
    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Scout Analytics API URLs:"
    echo "   Health Check: https://${WEBAPP_NAME}.manus.space/api/health"
    echo "   Overview:     https://${WEBAPP_NAME}.manus.space/api/analytics/overview"
    echo "   Dashboard:    https://ewlwkasq.manus.space"
    echo ""
    echo "🔧 Next Steps:"
    echo "   1. Verify dashboard loads data correctly"
    echo "   2. Test all API endpoints"
    echo "   3. Monitor performance metrics"
    echo "   4. Update frontend environment variables if needed"
    echo ""
}

# Script usage
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --version  Show version information"
    echo ""
    echo "Environment Variables:"
    echo "  REGISTRY_NAME  Azure Container Registry name (required)"
    echo ""
    echo "Example:"
    echo "  REGISTRY_NAME=myregistry $0"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -v|--version)
            echo "Scout Analytics Deployment Script v${VERSION}"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check if registry name is provided
if [ -z "${REGISTRY_NAME}" ] || [ "${REGISTRY_NAME}" = "<your-acr>" ]; then
    print_error "Please set REGISTRY_NAME environment variable or update the script with your Azure Container Registry name"
    echo ""
    echo "Example:"
    echo "  export REGISTRY_NAME=myregistry"
    echo "  $0"
    exit 1
fi

# Run main deployment
main


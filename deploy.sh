#!/bin/bash

# Transport Routing API Deployment Script
# This script automates the deployment process
#
# PURPOSE: Automated deployment script with comprehensive error checking
#
# KEY COMPONENTS:
# - Prerequisites validation (AWS CLI, CDK, Python)
# - AWS credentials verification
# - CDK bootstrap management
# - Automated deployment with error handling
# - Post-deployment testing and URL extraction
#
# CODE STRUCTURE:
# 1. Color-coded output functions
# 2. Prerequisites checking
# 3. AWS environment validation
# 4. CDK bootstrap verification
# 5. Template synthesis and deployment
# 6. Post-deployment testing
#
# WHY USED:
# - Reduces deployment complexity and human error
# - Handles prerequisites automatically
# - Provides clear feedback and error handling
# - Extracts and displays important deployment information
# - Enables one-command deployment workflow

set -e  # Exit on any error

echo "🚀 Starting Transport Routing API Deployment"
echo "============================================="

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

# Check prerequisites
print_status "Checking prerequisites..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    print_error "AWS CDK is not installed. Please install it with: npm install -g aws-cdk"
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null; then
    print_error "Python is not installed. Please install Python 3.11 or later."
    exit 1
fi

# Check AWS credentials
print_status "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
print_success "AWS Account: $AWS_ACCOUNT, Region: $AWS_REGION"

# Install Python dependencies
print_status "Installing Python dependencies..."
if pip install -r requirements.txt; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

# Check if CDK is bootstrapped
print_status "Checking CDK bootstrap status..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &> /dev/null; then
    print_warning "CDK not bootstrapped. Bootstrapping now..."
    if cdk bootstrap; then
        print_success "CDK bootstrapped successfully"
    else
        print_error "CDK bootstrap failed"
        exit 1
    fi
else
    print_success "CDK already bootstrapped"
fi

# Synthesize the stack
print_status "Synthesizing CloudFormation template..."
if cdk synth; then
    print_success "Template synthesized successfully"
else
    print_error "Template synthesis failed"
    exit 1
fi

# Deploy the stack
print_status "Deploying to AWS..."
echo "This may take a few minutes..."

if cdk deploy --require-approval never; then
    print_success "Deployment completed successfully!"
    
    # Extract API URL from CDK output
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name TransportRoutingStack \
        --query 'Stacks[0].Outputs[?OutputKey==`apiurl`].OutputValue' \
        --output text \
        --region $AWS_REGION)
    
    if [ ! -z "$API_URL" ]; then
        echo ""
        echo "🎉 Deployment Summary"
        echo "===================="
        echo "API URL: $API_URL"
        echo "Health Check: ${API_URL}health"
        echo "API Docs: ${API_URL}docs"
        echo ""
        echo "Test your API:"
        echo "curl \"${API_URL}routes?arrival_time=20241201084500&start_stop=Aalto%20Yliopisto&end_stop=Keilaniemi\""
        echo ""
        
        # Test the API
        print_status "Testing deployed API..."
        if curl -s "${API_URL}health" > /dev/null; then
            print_success "API is responding correctly"
        else
            print_warning "API might still be starting up. Try again in a few moments."
        fi
    else
        print_warning "Could not retrieve API URL from stack outputs"
    fi
else
    print_error "Deployment failed"
    exit 1
fi

echo ""
print_success "Deployment process completed!"
echo "Check the AWS Console for detailed monitoring and logs."
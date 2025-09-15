# Transport Routing API - AWS Deployment Guide

<!--
PURPOSE: Comprehensive deployment documentation with troubleshooting

KEY COMPONENTS:
- Step-by-step deployment instructions
- Prerequisites and setup requirements
- Troubleshooting common issues
- Cost optimization guidance
- Security considerations
- Production deployment checklist

STRUCTURE:
1. Prerequisites installation and configuration
2. Environment setup and validation
3. CDK bootstrap and deployment process
4. Testing and verification steps
5. Monitoring and maintenance guidance
6. Troubleshooting and cleanup procedures

WHY USED:
- Reduces deployment friction for new users
- Provides comprehensive troubleshooting guidance
- Documents best practices and security considerations
- Enables self-service deployment
- Supports both development and production deployments
-->

## Prerequisites

Before deploying, ensure you have:

1. **AWS Account**: Active AWS account with appropriate permissions
2. **AWS CLI**: Installed and configured with your credentials
3. **Node.js**: Version 14 or later (for AWS CDK)
4. **Python**: Version 3.11 or later
5. **AWS CDK**: Installed globally

## Step 1: Install AWS CLI and Configure Credentials

### Install AWS CLI
```bash
# On macOS
brew install awscli

# On Windows
# Download from: https://aws.amazon.com/cli/

# On Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Configure AWS Credentials
```bash
aws configure
```
Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `eu-west-1`)
- Default output format (e.g., `json`)

## Step 2: Install Node.js and AWS CDK

### Install Node.js
Download from: https://nodejs.org/

### Install AWS CDK globally
```bash
npm install -g aws-cdk
```

### Verify installation
```bash
cdk --version
```

## Step 3: Prepare Python Environment

### Install Python dependencies
```bash
pip install -r requirements.txt
```

### Verify Python setup
```bash
python --version
python -c "import aws_cdk; print('CDK installed successfully')"
```

## Step 4: Bootstrap CDK (First-time only)

This step is required only once per AWS account/region combination:

```bash
cdk bootstrap
```

This creates the necessary S3 bucket and IAM roles for CDK deployments.

## Step 5: Synthesize CloudFormation Template (Optional)

To see what will be deployed without actually deploying:

```bash
cdk synth
```

This generates the CloudFormation template in the `cdk.out` directory.

## Step 6: Deploy the Stack

### Deploy to AWS
```bash
cdk deploy
```

You'll see output similar to:
```
✨  Synthesis time: 2.34s

TransportRoutingStack: deploying...
[0%] start: Publishing assets
[50%] success: Published assets
TransportRoutingStack: creating CloudFormation changeset...

 ✅  TransportRoutingStack

✨  Deployment time: 45.67s

Outputs:
TransportRoutingStack.apiurl = https://abc123def4.execute-api.eu-west-1.amazonaws.com/prod/
```

### Note the API URL
Save the API URL from the output - this is your deployed API endpoint.

## Step 7: Test the Deployed API

### Test health endpoint
```bash
curl https://YOUR-API-URL/health
```

### Test routes endpoint
```bash
curl "https://YOUR-API-URL/routes?arrival_time=20241201084500&start_stop=Aalto%20Yliopisto&end_stop=Keilaniemi"
```

## Step 8: View API Documentation

Visit your API documentation at:
```
https://YOUR-API-URL/docs
```

## Step 9: Monitor and Logs

### View CloudWatch Logs
1. Go to AWS Console → CloudWatch → Log Groups
2. Find `/aws/lambda/TransportRoutingStack-TransportRoutingFunction-XXXXX`
3. View real-time logs

### View API Gateway Metrics
1. Go to AWS Console → API Gateway
2. Select your API
3. View metrics and monitoring

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Ensure your AWS credentials have sufficient permissions
   aws sts get-caller-identity
   ```

2. **CDK Bootstrap Required**
   ```bash
   # If you see bootstrap errors
   cdk bootstrap aws://ACCOUNT-NUMBER/REGION
   ```

3. **Python Dependencies**
   ```bash
   # If deployment fails due to missing dependencies
   pip install -r requirements.txt --upgrade
   ```

4. **Lambda Timeout**
   - Check CloudWatch logs for timeout errors
   - Increase timeout in `transport_routing_stack.py` if needed

### Useful CDK Commands

```bash
# List all stacks
cdk list

# Show differences between deployed and local
cdk diff

# Destroy the stack (cleanup)
cdk destroy

# View CDK documentation
cdk docs
```

## Cost Optimization

### Free Tier Usage
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free
- CloudWatch: Basic monitoring included

### Estimated Costs (after free tier)
- Lambda: ~$0.20 per 1M requests
- API Gateway: ~$3.50 per 1M requests
- CloudWatch Logs: ~$0.50 per GB

## Security Considerations

1. **API Rate Limiting**: Consider adding rate limiting for production
2. **Authentication**: Add API keys or OAuth for production use
3. **CORS**: Currently allows all origins - restrict for production
4. **VPC**: Consider deploying Lambda in VPC for enhanced security

## Production Checklist

- [ ] Set up proper monitoring and alerting
- [ ] Configure custom domain name
- [ ] Add API authentication
- [ ] Set up CI/CD pipeline
- [ ] Configure backup and disaster recovery
- [ ] Add rate limiting and throttling
- [ ] Set up proper logging and monitoring
- [ ] Configure SSL certificate

## Support

For issues:
1. Check CloudWatch logs first
2. Verify API Gateway configuration
3. Test Lambda function directly
4. Check IAM permissions

## Cleanup

To remove all AWS resources:
```bash
cdk destroy
```

This will delete:
- Lambda function
- API Gateway
- CloudWatch log groups
- IAM roles and policies
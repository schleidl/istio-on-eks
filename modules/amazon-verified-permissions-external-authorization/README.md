# Amazon Verified Permissions Authorization
This document provides instructions on how to deploy and manage the extension authorization (ext-authz) Lambda function using Amazon Web Services (AWS), Docker, and Kubernetes. Please follow these steps carefully to ensure successful deployment.
Prerequisites

Before starting, make sure you have installed:

    AWS CLI
    Docker
    kubectl
    jq (for processing JSON)

# Create ECR Repository
First, create an Elastic Container Registry (ECR) repository to store your Docker images.

    aws ecr create-repository --repository-name ext-authz-lbamda-repo

# Authenticate Docker to ECR

    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 851725369072.dkr.ecr.us-east-1.amazonaws.com

# Build and Push Docker Image

    docker build -t 851725369072.dkr.ecr.us-east-1.amazonaws.com/ext-authz-lambda-repo:latest .
    
    docker push 851725369072.dkr.ecr.us-east-1.amazonaws.com/ext-authz-lambda-repo:latest

# IAM Role and Policies for Lambda
Create an IAM role for Lambda execution and attach the necessary policies.

    aws iam create-role --role-name LambdaExecutionRole --assume-role-policy-document file://lambda-trust-policy.json
    
    aws iam attach-role-policy --role-name LambdaExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    aws iam create-policy --policy-name LambdaVerifiedPermissionsPolicy --policy-document file://verified-permissions-access-policy.json
    
    aws iam attach-role-policy --role-name LambdaExecutionRole --policy-arn arn:aws:iam::851725369072:policy/LambdaVerifiedPermissionsPolicy

# Create Lambda Function
Deploy your Lambda function using the Docker image.

    aws lambda create-function --function-name extauthz \
    --package-type Image \
    --code ImageUri=851725369072.dkr.ecr.us-east-1.amazonaws.com/ext-authz-lambda-repo:latest \
    --role arn:aws:iam::851725369072:role/LambdaExecutionRole \
    --region us-east-1 \
    --architectures arm64

Note: Ensure the CPU architecture (ARM vs. x86) is compatible with your Lambda function requirements.

# Create API Gateway
    aws apigatewayv2 create-api --name 'verified-permissions-api' --protocol-type 'HTTP' --target arn:aws:lambda:us-east-1:851725369072:function:extauthz

    aws apigatewayv2 create-integration --api-id q3u74hcvxh --integration-type AWS_PROXY --integration-uri arn:aws:lambda:us-east-1:851725369072:function:extauthz --payload-format-version 2.0

    aws apigatewayv2 create-route --api-id q3u74hcvxh --route-key 'ANY /' --target integrations/66plr05

    aws apigatewayv2 create-deployment --api-id q3u74hcvxh --description 'verified permissions api deployment'

    Run permission command generated in API Gateway console. See screenshot api-gateway-lambda-integration.jpg

    aws lambda add-permission --function-name extauthz --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn arn:aws:execute-api:us-east-1:851725369072:q3u74hcvxh/ --statement-id 1


# Test Lambda Function
aws lambda invoke --function-name extauthz --payload file://entities.json response.json

# Integration with Envoy

Configure Istio's Envoy filter for external authorization.

    EXT_ENVOY_EXT_AUTHZ_HTTPS=$(cat <<EOM
    extensionProviders:
    - name: opa-ext-authz-http
        envoyExtAuthzHttp:
            service: https://e2xwgimjtcovugrdizbokchcsy0dcrlp.lambda-url.us-east-1.on.aws/
            port: 443
EOM
)

    kubectl get cm istio -n istio-system -o json \
    | jq ".data.mesh += \"\n$EXT_ENVOY_EXT_AUTHZ_HTTPS\"" \
    | kubectl apply -f -

Verify the ConfigMap update:
    
    kubectl get cm istio -n istio-system -o jsonpath='{.data.mesh}'

Apply any necessary authorization policies:

    kubectl apply -f productapp-authorizationpolicy.yaml

# Update Lambda Function
    docker build -t 851725369072.dkr.ecr.us-east-1.amazonaws.com/ext-authz-lambda-repo:latest .
    
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 851725369072.dkr.ecr.us-east-1.amazonaws.com

    docker push 851725369072.dkr.ecr.us-east-1.amazonaws.com/ext-authz-lambda-repo:latest

    aws lambda update-function-code --function-name extauthz \
    --image-uri=851725369072.dkr.ecr.us-east-1.amazonaws.com/ext-authz-lambda-repo:latest \
    --region us-east-1




# Amazon Verified Permissions Authorization
This is a demo Lambda function invoking Amazon Verified Permissions. The Lambda function can be invoked by the aws command line tool. 

Get started by running through Lab 1 of this workshop: 
https://catalog.workshops.aws/verified-permissions-in-action/en-US/30-lab1-avp-console-demo

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




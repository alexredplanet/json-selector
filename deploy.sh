#!/bin/bash

# JSON Selector Deployment Script
# This script builds and pushes the Docker image to Docker Hub

set -e

# Configuration
IMAGE_NAME="json-selector"
DOCKER_HUB_USERNAME="your-dockerhub-username"  # Replace with your Docker Hub username
VERSION="latest"

echo "🚀 Starting deployment process..."

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME:$VERSION .

# Tag for Docker Hub
echo "🏷️  Tagging image for Docker Hub..."
docker tag $IMAGE_NAME:$VERSION $DOCKER_HUB_USERNAME/$IMAGE_NAME:$VERSION

# Push to Docker Hub (you'll need to login first: docker login)
echo "⬆️  Pushing to Docker Hub..."
docker push $DOCKER_HUB_USERNAME/$IMAGE_NAME:$VERSION

echo "✅ Image pushed successfully!"
echo "📋 To deploy on your EC2 server, run:"
echo "   docker run -d -p 80:5000 --name json-selector $DOCKER_HUB_USERNAME/$IMAGE_NAME:$VERSION"
echo ""
echo "🌐 Your application will be available at: http://your-ec2-ip"

#!/bin/bash

# Docker run script for Japanese Railway Translation API
# Use this when you can't use docker-compose but can use docker build/run

set -e

echo "🐳 Building and Running Japanese Railway Translation API"
echo "======================================================="

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t japanese-railway-translation-api .

echo "✅ Docker image built successfully!"

# Check if container is already running
if docker ps | grep -q "translation-api"; then
    echo "🛑 Stopping existing container..."
    docker stop translation-api
    docker rm translation-api
fi

# Check if container exists but stopped
if docker ps -a | grep -x "translation-api"; then
    echo "🗑️ Removing existing stopped container..."
    docker rm translation-api
fi

# Run the container
echo "🚀 Starting container..."
docker run -d \
    --name translation-api \
    -p 8002:8000 \
    -v "$(pwd)/train_entity.csv:/app/train_entity.csv:ro" \
    japanese-railway-translation-api

echo "⏳ Waiting for container to start..."
sleep 10

# Check if container is running
if docker ps | grep -q "translation-api"; then
    echo "✅ Container is running successfully!"
    echo ""
    echo "📋 Container Information:"
    docker ps --filter "name=translation-api" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "🌐 API is available at: http://localhost:8002"
    echo "📖 API Documentation: http://localhost:8002/docs"
    echo ""
    echo "🧪 Test the API:"
    echo "   curl http://localhost:8002/api/v1/health"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs:     docker logs translation-api"
    echo "   Follow logs:   docker logs -f translation-api"
    echo "   Stop:          docker stop translation-api"
    echo "   Remove:        docker rm translation-api"
else
    echo "❌ Container failed to start. Checking logs..."
    docker logs translation-api
    exit 1
fi

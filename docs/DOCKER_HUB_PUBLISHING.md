# Docker Hub Publishing Guide

This guide explains how to build and publish the HostBridge Docker image to Docker Hub.

## Prerequisites

- Docker installed and running
- Docker Hub account
- Logged in to Docker Hub (`docker login`)

## Building the Image

### Standard Build

```bash
# Build with default tag
docker build -t hostbridge:latest .

# Build with specific version tag
docker build -t hostbridge:0.1.0 .
```

### Multi-platform Build (Recommended)

For compatibility with different architectures:

```bash
# Enable buildx for multi-platform builds
docker buildx create --use

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t hostbridge:latest .
```

## Tagging Convention

Use semantic versioning:

```bash
# Latest stable release
docker tag hostbridge:latest yourusername/hostbridge:latest

# Specific version
docker tag hostbridge:latest yourusername/hostbridge:0.1.0

# Version series
docker tag hostbridge:latest yourusername/hostbridge:0.1
```

## Publishing to Docker Hub

### Step 1: Login

```bash
docker login
```

### Step 2: Tag the Image

```bash
# Replace 'yourusername' with your Docker Hub username
docker tag hostbridge:latest yourusername/hostbridge:latest
docker tag hostbridge:latest yourusername/hostbridge:0.1.0
```

### Step 3: Push

```bash
docker push yourusername/hostbridge:latest
docker push yourusername/hostbridge:0.1.0
```

### One-liner

```bash
docker build -t yourusername/hostbridge:latest -t yourusername/hostbridge:0.1.0 . && \
docker push yourusername/hostbridge:latest && \
docker push yourusername/hostbridge:0.1.0
```

## GitHub Actions Automation

Create `.github/workflows/docker-publish.yml`:

```yaml
name: Docker Publish

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/hostbridge:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/hostbridge:${{ steps.version.outputs.VERSION }}
```

## Docker Hub Repository Setup

1. Create repository on Docker Hub:
   - Go to https://hub.docker.com/
   - Click "Create Repository"
   - Name: `hostbridge`
   - Description: "Unified MCP + OpenAPI Tool Server for Self-Hosted LLM Stacks"
   - Set visibility (public recommended)

2. Add repository description:
   ```markdown
   # HostBridge

   Unified MCP + OpenAPI Tool Server for Self-Hosted LLM Stacks

   ## Quick Start

   ```bash
   docker run -d \
     -p 8080:8080 \
     -v ./workspace:/workspace \
     -v ./data:/data \
     -e ADMIN_PASSWORD=your_password \
     yourusername/hostbridge:latest
   ```

   ## Features

   - Dual Protocol Support: MCP + OpenAPI
   - Filesystem, Shell, Git, Docker tools
   - Knowledge Graph Memory
   - DAG-based Plan Execution
   - HITL Approval System
   - Admin Dashboard

   ## Documentation

   - [GitHub Repository](https://github.com/yourusername/hostbridge)
   - [Documentation](https://github.com/yourusername/hostbridge#readme)
   ```

3. Configure webhooks (optional):
   - For automated deployments
   - For CI/CD integration

## Version Management

### Creating a Release

```bash
# 1. Update version in code
# 2. Commit changes
git commit -am "Release v0.1.0"

# 3. Create tag
git tag v0.1.0

# 4. Push tag
git push origin v0.1.0

# 5. GitHub Actions will build and publish automatically
```

### Rolling Back

```bash
# Re-tag a previous version as latest
docker pull yourusername/hostbridge:0.0.9
docker tag yourusername/hostbridge:0.0.9 yourusername/hostbridge:latest
docker push yourusername/hostbridge:latest
```

## Security Best Practices

1. **Never commit secrets** to the repository
2. Use GitHub secrets for Docker Hub credentials
3. Scan images for vulnerabilities:
   ```bash
   docker scout cves yourusername/hostbridge:latest
   ```
4. Sign images with Docker Content Trust
5. Use minimal base images for smaller attack surface

## Verification

After publishing, verify the image:

```bash
# Pull fresh image
docker pull yourusername/hostbridge:latest

# Run and test
docker run -d -p 8080:8080 -e ADMIN_PASSWORD=test yourusername/hostbridge:latest

# Check health
curl http://localhost:8080/health
```

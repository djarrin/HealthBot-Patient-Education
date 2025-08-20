#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up HealthBot Backend for Local Development${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js and try again.${NC}"
    exit 1
fi

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    echo -e "${RED}❌ Python 3.11 is not installed. Please install Python 3.11 and try again.${NC}"
    echo -e "${YELLOW}   This version must match your Lambda runtime (python3.11)${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3.11 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Using Python ${PYTHON_VERSION} (matches Lambda runtime)${NC}"

# Clean up existing node_modules and package-lock.json to avoid conflicts
echo -e "${YELLOW}🧹 Cleaning up existing dependencies...${NC}"
rm -rf node_modules package-lock.json

# Install Node.js dependencies
echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
npm install

# Install Python dependencies with Python 3.11
echo -e "${YELLOW}🐍 Installing Python dependencies with Python 3.11...${NC}"
python3.11 -m pip install --upgrade pip
python3.11 -m pip install --no-deps -r requirements.txt
python3.11 -m pip install -r requirements.txt

# Install serverless plugins (plugins are already in package.json)
echo -e "${YELLOW}🔌 Serverless plugins will be installed via npm...${NC}"

# Try to install DynamoDB local, but don't fail if it doesn't work
echo -e "${YELLOW}🗄️  Installing DynamoDB local...${NC}"
if npx serverless dynamodb install; then
    echo -e "${GREEN}✅ DynamoDB local installed successfully${NC}"
else
    echo -e "${YELLOW}⚠️  DynamoDB local installation failed, but you can still use Docker or AWS CLI${NC}"
    echo -e "${YELLOW}   You can manually install it later with: npx serverless dynamodb install${NC}"
fi

# Check for top-level .env file
if [ ! -f ../.env ]; then
    echo -e "${YELLOW}📝 Creating top-level .env file from template...${NC}"
    cp ../env.example ../.env
    echo -e "${GREEN}✅ Top-level .env file created!${NC}"
    echo -e "${YELLOW}⚠️  Please edit ../.env file with your API keys:${NC}"
    echo -e "   - OPENAI_API_KEY"
    echo -e "   - TAVILY_API_KEY"
    echo -e "   - REACT_APP_COGNITO_USER_POOL_ID"
    echo -e "   - REACT_APP_COGNITO_CLIENT_ID"
else
    echo -e "${GREEN}✅ Top-level .env file already exists${NC}"
fi

echo -e "${GREEN}🎉 Local development setup complete!${NC}"
echo -e ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Edit ../.env file with your API keys and Cognito configuration"
echo -e "2. Start DynamoDB local: ${YELLOW}npm run dynamodb:docker:start${NC} (recommended)"
echo -e "3. Start the server: ${YELLOW}npm run dev${NC}"
echo -e ""
echo -e "${BLUE}Available commands:${NC}"
echo -e "  ${YELLOW}npm run dev${NC} - Start serverless offline"
echo -e "  ${YELLOW}npm run dynamodb:docker:start${NC} - Start DynamoDB with Docker (recommended)"
echo -e "  ${YELLOW}npm run dynamodb:docker:admin${NC} - Start DynamoDB + Admin UI with Docker"
echo -e "  ${YELLOW}npm run dynamodb:docker:stop${NC} - Stop DynamoDB Docker containers"
echo -e "  ${YELLOW}npm run deploy${NC} - Deploy to AWS"
echo -e ""
echo -e "${BLUE}Local endpoints:${NC}"
echo -e "  API: http://localhost:3001"
echo -e "  Health check: http://localhost:3001/health"
echo -e "  DynamoDB: http://localhost:8000"
echo -e "  DynamoDB Admin: http://localhost:8001 (with docker:admin)"
echo -e ""
echo -e "${BLUE}Environment file location:${NC}"
echo -e "  Top-level .env: ../.env (shared between frontend and backend)"
echo -e ""
echo -e "${YELLOW}Note: If DynamoDB local installation failed, you can:${NC}"
echo -e "  - Use Docker: ${YELLOW}npm run dynamodb:docker:start${NC}"
echo -e "  - Use AWS CLI with local endpoint: aws dynamodb --endpoint-url http://localhost:8000"
echo -e "  - Try manual installation: npx serverless dynamodb install"

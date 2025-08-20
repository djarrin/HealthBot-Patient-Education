#!/bin/bash

echo "🚀 Setting up HealthBot Frontend for Local Development"
echo ""

# Check if top-level .env file exists
if [ ! -f ../.env ]; then
    echo "📝 Creating top-level .env file from template..."
    cp ../env.example ../.env
    echo "✅ Top-level .env file created!"
    echo ""
    echo "⚠️  IMPORTANT: Please edit the ../.env file with your configuration:"
    echo "   - REACT_APP_COGNITO_USER_POOL_ID"
    echo "   - REACT_APP_COGNITO_CLIENT_ID" 
    echo "   - REACT_APP_API_GATEWAY_URL (set to http://localhost:3001 for local dev)"
    echo "   - OPENAI_API_KEY (for backend)"
    echo "   - TAVILY_API_KEY (for backend)"
    echo ""
else
    echo "✅ Top-level .env file already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Install dotenv-cli if not already installed
if ! npm list dotenv-cli > /dev/null 2>&1; then
    echo "🔧 Installing dotenv-cli for environment variable loading..."
    npm install --save-dev dotenv-cli
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit ../.env file with your configuration"
echo "2. Start the backend: cd ../backend && npm run dev"
echo "3. Start the frontend: npm start"
echo ""
echo "For local development:"
echo "  - Set REACT_APP_API_GATEWAY_URL=http://localhost:3001 in ../.env"
echo "  - Start backend first: cd ../backend && npm run dev"
echo "  - Then start frontend: npm start"
echo ""
echo "Environment file location: ../.env (shared between frontend and backend)"

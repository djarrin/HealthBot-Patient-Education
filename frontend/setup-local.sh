#!/bin/bash

echo "🚀 Setting up HealthBot Frontend for Local Development"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created!"
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file with your AWS configuration:"
    echo "   - REACT_APP_COGNITO_USER_POOL_ID"
    echo "   - REACT_APP_COGNITO_CLIENT_ID" 
    echo "   - REACT_APP_API_GATEWAY_URL"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your AWS configuration"
echo "2. Deploy your backend using: cd ../backend && serverless deploy"
echo "3. Start the frontend: npm start"
echo ""
echo "For more information, see README.md"

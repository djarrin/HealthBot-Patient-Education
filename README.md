# HealthBot-Patient-Education

## Local Development Setup

### 🚀 Quick Start for Local Development

This guide will help you set up the HealthBot application for local development, allowing you to work on AI workflows without deploying to AWS.

#### Prerequisites

- **Node.js** (v18 or higher)
- **Python 3.9** (for backend Lambda functions)
- **Git**

#### 1. Clone and Setup the Project

```bash
git clone <your-repo-url>
cd HealthBot-Patient-Education
```

#### 2. Create Environment Configuration

Create a top-level `.env` file with your API keys:

```bash
# Create the environment file
cp env.example .env
```

Edit `.env` with your API keys:
```env
# API Keys (required for AI functionality)
OPENAI_API_KEY=your-openai-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here

# AWS Configuration (for local development, these can be mock values)
AWS_ACCESS_KEY_ID=local
AWS_SECRET_ACCESS_KEY=local
AWS_DEFAULT_REGION=us-east-1

# Backend Configuration
OPENAI_BASE_URL=https://openai.vocareum.com/v1
OPENAI_MODEL=gpt-4o-mini

# Frontend Configuration (for local development)
REACT_APP_COGNITO_REGION=us-east-1
REACT_APP_COGNITO_USER_POOL_ID=local-dev-pool
REACT_APP_COGNITO_CLIENT_ID=local-dev-client
REACT_APP_API_GATEWAY_URL=http://localhost:3001
```

#### 3. Setup Backend (Local Development)

```bash
cd backend

# Install Node.js dependencies
npm install

# Install Python dependencies for local development
python3 -m pip install -r requirements.txt

# Start the local backend server
npm run dev
```

The backend will start on `http://localhost:3001` with:
- ✅ **Serverless Offline** - Local Lambda emulation
- ✅ **Memory Checkpointer** - No DynamoDB required
- ✅ **Local API Keys** - Uses your `.env` configuration
- ✅ **Real-time Logs** - See AI workflow execution

#### 4. Setup Frontend (Local Development)

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start the frontend development server
npm start
```

The frontend will start on `http://localhost:3000` and automatically connect to your local backend.

#### 5. Test Your Local Setup

1. **Open your browser** to `http://localhost:3000`
2. **Send a test message** like "My heart hurts"
3. **Watch the backend logs** to see the AI workflow in action
4. **Verify the response** appears in the frontend chat

### 🔧 Local Development Features

#### Backend Features
- **Real AI Workflows**: Full LangGraph workflow execution
- **Local Search**: Tavily search integration works locally
- **Memory State**: Session state stored in memory (no DynamoDB needed)
- **Hot Reload**: Changes to Python code restart automatically
- **Debug Logs**: Detailed logging of AI workflow steps

#### Frontend Features
- **Local Authentication**: Bypasses AWS Cognito for development
- **Real-time Chat**: Live communication with local backend
- **Markdown Rendering**: Proper display of AI responses with headers and formatting
- **Session Management**: Maintains conversation state locally

### 🛠️ Development Workflow

#### Making Changes to AI Workflows

1. **Edit the workflow** in `backend/src/handlers/healthbot_graph.py`
2. **Save the file** - backend will auto-restart
3. **Test immediately** - send a message through the frontend
4. **See real-time logs** - watch the backend terminal for execution details

#### Example: Modifying the Search Node

```python
# In healthbot_graph.py
def node_search(state: HealthBotState) -> HealthBotState:
    # Your changes here
    print("Custom search logic running...")
    # ...
```

#### Making Changes to Frontend

1. **Edit React components** in `frontend/src/components/`
2. **Save the file** - frontend will hot-reload
3. **See changes immediately** - no restart needed

### 🐛 Troubleshooting Local Development

#### Backend Issues

**"Unsupported runtime" warning:**
- ✅ This is normal and expected - the backend uses Python 3.9 locally
- ✅ The warning doesn't affect functionality

**"Module not found" errors:**
```bash
cd backend
python3 -m pip install -r requirements.txt
```

**Port already in use:**
```bash
# Kill existing processes
pkill -f "serverless offline"
npm run dev
```

#### Frontend Issues

**"API connection failed":**
- ✅ Ensure backend is running on `http://localhost:3001`
- ✅ Check that the frontend is using the correct backend URL

**"Authentication errors":**
- ✅ Local development bypasses authentication
- ✅ Check that `REACT_APP_API_GATEWAY_URL=http://localhost:3001` in `.env`

#### General Issues

**Environment variables not loading:**
```bash
# Ensure you're using the top-level .env file
ls -la .env
cat .env  # Verify your API keys are set
```

**Python version issues:**
```bash
# Check your Python version
python3 --version  # Should be 3.9.x
```

### 📁 Project Structure for Local Development

```
HealthBot-Patient-Education/
├── .env                    # Top-level environment configuration
├── backend/
│   ├── src/handlers/
│   │   ├── healthbot_graph.py    # Main AI workflow logic
│   │   └── process_user_message.py # Lambda handler
│   ├── serverless.yml            # Serverless configuration
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/components/
│   │   └── HealthBotChat.js      # Main chat component
│   └── src/services/
│       └── api.js               # API communication
```

### 🚀 Next Steps

Once your local development environment is working:

1. **Explore the AI workflow** in `healthbot_graph.py`
2. **Test different health topics** through the chat interface
3. **Modify the workflow logic** and see changes immediately
4. **Add new AI capabilities** using LangChain and LangGraph
5. **Deploy to AWS** when ready using the deployment instructions below

---

### Getting Your AWS Configuration

After deploying the backend, you can find the required values:

- **Cognito User Pool ID**: AWS Console → Cognito → User Pools → Your Pool → Pool ID
- **Cognito Client ID**: AWS Console → Cognito → User Pools → Your Pool → App Integration → App Client ID
- **API Gateway URL**: From the `serverless deploy` output or AWS Console → API Gateway → Your API → Stages → dev

### Troubleshooting Local Development

- **CORS Issues**: The backend is configured with CORS headers, but if you encounter issues, check that your API Gateway URL is correct
- **Authentication Errors**: Ensure your Cognito configuration matches between frontend and backend
- **API Connection**: Verify the backend Lambda function is deployed and the API Gateway endpoint is accessible

---

## Initial AWS Setup

### 👤 Creating the IAM User with Correct Permissions

To securely deploy via GitHub Actions, you'll need an IAM user with appropriate permissions.

### 1. Create an IAM user in AWS Console

- Go to [IAM Console](https://console.aws.amazon.com/iam/)
- Click **Users → Add Users**
- Name it something like: `github-deploy-bot`
- Enable **Programmatic access**
- Skip group assignment

### 2. Attach these AWS managed policies to the IAM user

To avoid inline policy size limits and simplify management, attach these AWS managed policies to the `github-deploy-bot` user:

#### Required AWS Managed Policies:

- **AWSCloudFormationFullAccess** - For deploying CloudFormation stacks
- **AmazonS3FullAccess** - For S3 bucket and website deployment
- **AWSLambda_FullAccess** - For Lambda function deployment
- **AmazonAPIGatewayAdministrator** - For API Gateway (REST and HTTP/WebSocket)
- **AmazonDynamoDBFullAccess** - For DynamoDB table management
- **SecretsManagerReadWrite** - For Secrets Manager operations
- **CloudWatchLogsFullAccess** - For CloudWatch Logs management
- **AmazonCognitoPowerUser** - For Cognito User Pool and Client management

#### Additional IAM Permissions:

You'll also need to create a custom managed policy for IAM role management. Name it `HealthBot-IAMRoleManagement`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:UpdateAssumeRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "iam:TagRole",
        "iam:UntagRole"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Deployment order

- Deploy the backend first (run the "Deploy Backend" workflow or `serverless deploy` in `backend/`).
- Then deploy the frontend (run the "Deploy Frontend" workflow or `serverless deploy` in `frontend/`).
- Rationale: the frontend build reads CloudFormation exports (`HealthBotUserPoolId`, `HealthBotUserPoolClientId`, `HealthBotApiBaseUrl`) produced by the backend.

### 4. Download the credentials and add to GitHub

Paste them into GitHub Secrets under:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### 5. Add API Keys to GitHub Secrets

Add these additional secrets to your GitHub repository (Settings > Secrets and variables > Actions):

- `OPENAI_API_KEY` - Your OpenAI API key for LLM functionality
- `TAVILY_API_KEY` - Your Tavily API key for web search functionality

---
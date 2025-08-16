# HealthBot-Patient-Education

## Local Development Setup

### Quick Start for Local Development

1. **Clone and setup the project:**
   ```bash
   git clone <your-repo-url>
   cd HealthBot-Patient-Education
   ```

2. **Deploy the backend first:**
   ```bash
   cd backend
   npm install
   serverless deploy
   ```
   Note down the API Gateway URL from the deployment output.

3. **Setup the frontend:**
   ```bash
   cd ../frontend
   ./setup-local.sh
   ```

4. **Configure environment variables:**
   Edit the `.env` file in the frontend directory with your AWS configuration:
   ```env
   REACT_APP_COGNITO_REGION=us-east-1
   REACT_APP_COGNITO_USER_POOL_ID=your-user-pool-id
   REACT_APP_COGNITO_CLIENT_ID=your-client-id
   REACT_APP_API_GATEWAY_URL=https://your-api-gateway-url/dev
   ```

5. **Start the frontend:**
   ```bash
   npm start
   ```

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
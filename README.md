# HealthBot-Patient-Education

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
        "iam:PassRole"
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

---
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

### 2. Attach this **inline policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:CreateBucket",
        "s3:PutBucketTagging",
        "s3:GetBucketTagging",
        "s3:PutEncryptionConfiguration",
        "s3:GetEncryptionConfiguration",
        "s3:PutBucketPolicy",
        "s3:PutBucketWebsite",
        "s3:GetBucketWebsite",
        "s3:PutBucketPublicAccessBlock",
        "s3:GetBucketPublicAccessBlock"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackResource",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:GetTemplate",
        "cloudformation:ValidateTemplate",
        "cloudformation:CreateChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:DescribeStackEvents",
        "cloudformation:ListStackResources"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:GetRole"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Download the credentials and add to GitHub

Paste them into GitHub Secrets under:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

---
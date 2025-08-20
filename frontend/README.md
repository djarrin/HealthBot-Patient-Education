# Getting Started with HealthBot Frontend

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Local Development Setup

### Quick Start

1. **Setup the project:**
   ```bash
   chmod +x setup-local.sh
   ./setup-local.sh
   ```

2. **Configure environment variables:**
   Edit the top-level `.env` file (located at `../.env`) with your configuration:
   ```env
   # For local development
   REACT_APP_API_GATEWAY_URL=http://localhost:3001
   REACT_APP_COGNITO_REGION=us-east-1
   REACT_APP_COGNITO_USER_POOL_ID=your-user-pool-id
   REACT_APP_COGNITO_CLIENT_ID=your-client-id
   ```

3. **Start the backend first:**
   ```bash
   cd ../backend
   npm run dev
   ```

4. **Start the frontend:**
   ```bash
   npm start
   ```

Your app will be available at [http://localhost:3000](http://localhost:3000).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

**Note**: This script automatically loads environment variables from the top-level `.env` file.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Environment Configuration

The frontend uses environment variables from the top-level `.env` file (located at `../.env`). This file is shared between frontend and backend for consistent configuration.

### Required Environment Variables

- `REACT_APP_API_GATEWAY_URL` - Backend API endpoint
- `REACT_APP_COGNITO_REGION` - AWS Cognito region
- `REACT_APP_COGNITO_USER_POOL_ID` - Cognito User Pool ID
- `REACT_APP_COGNITO_CLIENT_ID` - Cognito Client ID

### Local Development

For local development, set:
```env
REACT_APP_API_GATEWAY_URL=http://localhost:3001
```

### Production Deployment

For production, set:
```env
REACT_APP_API_GATEWAY_URL=https://your-api-gateway-url/dev
```

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

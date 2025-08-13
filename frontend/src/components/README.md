# Components Directory

This directory contains all React components organized by functionality.

## Authentication Components (`/auth`)

- **AuthForm.js** - Main authentication form orchestrator
- **useAuth.js** - Custom hook for authentication logic
- **AuthInput.js** - Reusable input component
- **AuthButton.js** - Reusable button component
- **AuthNavigation.js** - Navigation between auth steps
- **AuthMessage.js** - Message display component
- **AuthFormSteps.js** - Form steps logic
- **authConstants.js** - Constants and step definitions
- **index.js** - Clean exports for the auth module

## Main Components

- **HealthBotChat.js** - Interactive chat interface with quiz functionality
- **ProtectedRoute.js** - Route wrapper that checks authentication
- **LoadingSpinner.js** - Reusable loading component

## Routing Structure

- `/` - Redirects to `/auth`
- `/auth` - Authentication form (signup, signin, password reset)
- `/dashboard` - Protected HealthBot chat interface (requires authentication)

## Authentication Flow

1. User visits `/auth` and can sign up or sign in
2. After successful authentication, user is redirected to `/dashboard`
3. ProtectedRoute ensures only authenticated users can access `/dashboard`
4. Users can sign out from the HealthBot chat interface and return to `/auth`

## HealthBot Chat Flow

1. **Welcome**: Bot greets user and asks for health topic
2. **Topic Selection**: User specifies health topic/condition
3. **Information Search**: Bot searches and summarizes medical information
4. **Reading Time**: User reads the summarized information
5. **Quiz Preparation**: User indicates readiness for comprehension check
6. **Quiz**: Multiple choice question based on the information
7. **Evaluation**: Bot grades answer and provides explanation with citations
8. **Session End**: Option to learn about another topic or end session

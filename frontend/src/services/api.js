import { getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';

class ApiService {
  constructor() {
    this.baseUrl = process.env.REACT_APP_API_GATEWAY_URL;
    console.log('API Service initialized with base URL:', this.baseUrl);
  }

  async getAuthToken() {
    try {
      // First check if user is authenticated
      const user = await getCurrentUser();
      console.log('Current user:', user.username);
      
      const session = await fetchAuthSession();
      if (!session.tokens || !session.tokens.idToken) {
        throw new Error('No valid session found. Please log in again.');
      }
      
      const token = session.tokens.idToken.toString();
      console.log('Auth token retrieved successfully');
      return token;
    } catch (error) {
      console.error('Error getting auth token:', error);
      if (error.message.includes('No current user')) {
        throw new Error('No user is currently signed in. Please log in first.');
      }
      throw new Error('Failed to get authentication token. Please try logging in again.');
    }
  }

  async sendMessage(message, sessionId = null) {
    try {
      console.log('Sending message to API:', { message, sessionId });
      const token = await this.getAuthToken();
      
      const requestBody = {
        message: message,
        ...(sessionId && { sessionId })
      };

      console.log('Request body:', requestBody);

      // Use fetch directly instead of Amplify API
      const response = await fetch(`${this.baseUrl}/api/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      console.log('API response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const responseBody = await response.json();
      console.log('API response:', responseBody);
      return responseBody;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  // Test method to verify API connectivity
  async testConnection() {
    try {
      console.log('Testing API connection...');
      const token = await this.getAuthToken();
      console.log('Auth token obtained successfully');
      
      // Try a simple request to test connectivity
      const response = await fetch(`${this.baseUrl}/api/messages`, {
        method: 'OPTIONS',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Connection test response status:', response.status);
      return response.ok;
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }
}

export default new ApiService();

import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { signOut } from 'aws-amplify/auth';
import apiService from '../services/api';
import '../assets/healthbot-chat.css';

export default function HealthBotChat() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentStep, setCurrentStep] = useState('welcome');
  const [quizQuestion, setQuizQuestion] = useState(null);
  const [quizAnswer, setQuizAnswer] = useState('');
  const [showQuiz, setShowQuiz] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize with welcome message
    addMessage({
      type: 'bot',
      content: "Hello! I'm your HealthBot assistant. I'm here to help you learn about health topics and test your knowledge. What health topic or medical condition would you like to learn about today?",
      timestamp: new Date()
    });

    // Test API connection on component mount
    const testConnection = async () => {
      try {
        const isConnected = await apiService.testConnection();
        if (!isConnected) {
          console.warn('API connection test failed - check your configuration');
        } else {
          console.log('API connection test successful');
        }
      } catch (error) {
        console.error('API connection test error:', error);
      }
    };

    testConnection();
  }, []);

  const addMessage = (message) => {
    setMessages(prev => [...prev, { ...message, id: Date.now() }]);
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/auth');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const sendMessageToAPI = async (messageContent) => {
    try {
      setIsTyping(true);
      
      const response = await apiService.sendMessage(messageContent, sessionId);

      // Update session ID if provided
      if (response.sessionId && !sessionId) {
        setSessionId(response.sessionId);
      }

      // Add bot response
      if (response.response && response.response.content) {
        addMessage({
          type: 'bot',
          content: response.response.content,
          timestamp: new Date(response.response.timestamp || Date.now())
        });
      }

      return response;
    } catch (error) {
      console.error('Error sending message to API:', error);
      
      // Add error message
      addMessage({
        type: 'bot',
        content: "I'm sorry, I'm having trouble connecting to my services right now. Please try again in a moment.",
        timestamp: new Date()
      });
      
      throw error;
    } finally {
      setIsTyping(false);
    }
  };

  const handleTopicSubmit = async (topic) => {
    addMessage({
      type: 'user',
      content: `I'd like to learn about: ${topic}`,
      timestamp: new Date()
    });

    setCurrentStep('searching');

    try {
      const response = await sendMessageToAPI(`I'd like to learn about: ${topic}`);
      
      // Check if the response indicates we're ready for a quiz
      if (response.response && response.response.status === 'ready_for_quiz') {
        setCurrentStep('ready-for-quiz');
      } else {
        setCurrentStep('ready-for-quiz');
      }
    } catch (error) {
      setCurrentStep('error');
    }
  };

  const handleReadyForQuiz = async () => {
    addMessage({
      type: 'user',
      content: 'I\'m ready for the comprehension check!',
      timestamp: new Date()
    });

    try {
      const response = await sendMessageToAPI('I\'m ready for the comprehension check!');
      
      // Check if the response contains quiz information
      if (response.response && response.response.content) {
        // Parse quiz from response if available
        // For now, we'll use a simple approach and let the backend handle the quiz logic
        setCurrentStep('quiz');
      }
    } catch (error) {
      setCurrentStep('error');
    }
  };

  const handleQuizSubmit = async () => {
    if (!quizAnswer) return;

    addMessage({
      type: 'user',
      content: `My answer: ${quizAnswer}`,
      timestamp: new Date()
    });

    try {
      const response = await sendMessageToAPI(`My answer: ${quizAnswer}`);
      
      setShowQuiz(false);
      setCurrentStep('quiz-complete');
      
      // Check if we should end the session or continue
      if (response.response && response.response.status === 'session_end') {
        setCurrentStep('session-end');
      }
    } catch (error) {
      setCurrentStep('error');
    }
  };

  const handleNewTopic = () => {
    setMessages([]);
    setCurrentStep('welcome');
    setQuizQuestion(null);
    setQuizAnswer('');
    setShowQuiz(false);
    setSessionId(null); // Reset session for new topic

    setTimeout(() => {
      addMessage({
        type: 'bot',
        content: "Great! Let's start fresh. What health topic or medical condition would you like to learn about?",
        timestamp: new Date()
      });
    }, 500);
  };

  const handleEndSession = async () => {
    addMessage({
      type: 'user',
      content: 'I\'d like to end this session.',
      timestamp: new Date()
    });

    try {
      await sendMessageToAPI('I\'d like to end this session.');
    } catch (error) {
      // Even if API fails, show end message
      addMessage({
        type: 'bot',
        content: 'Thank you for using HealthBot! I hope you learned something valuable today. Feel free to come back anytime to learn about more health topics. Take care!',
        timestamp: new Date()
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isTyping) return;

    const userInput = inputValue.trim();
    setInputValue('');

    if (currentStep === 'welcome') {
      await handleTopicSubmit(userInput);
    } else if (currentStep === 'ready-for-quiz' && userInput.toLowerCase().includes('ready')) {
      await handleReadyForQuiz();
    } else if (currentStep === 'session-end') {
      if (userInput.toLowerCase().includes('another') || userInput.toLowerCase().includes('new')) {
        handleNewTopic();
      } else if (userInput.toLowerCase().includes('end') || userInput.toLowerCase().includes('exit')) {
        await handleEndSession();
      } else {
        addMessage({
          type: 'bot',
          content: 'I didn\'t understand. Would you like to learn about another health topic, or would you like to end this session?',
          timestamp: new Date()
        });
      }
    } else {
      // Send any other message to the API
      addMessage({
        type: 'user',
        content: userInput,
        timestamp: new Date()
      });
      
      try {
        await sendMessageToAPI(userInput);
      } catch (error) {
        // Error handling is done in sendMessageToAPI
      }
    }
  };

  return (
    <div className="healthbot-container">
      <div className="healthbot-header">
        <div className="healthbot-title">
          <h1>🤖 HealthBot</h1>
          <p>Your AI Health Education Assistant</p>
        </div>
        <button onClick={handleSignOut} className="sign-out-button">
          Sign Out
        </button>
      </div>

      <div className="chat-container">
        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-content">
                {message.type === 'bot' && (
                  <div className="bot-avatar">🤖</div>
                )}
                <div className="message-text">
                  {message.content.split('\n').map((line, index) => (
                    <div key={index}>
                      {line.startsWith('**') && line.endsWith('**') ? (
                        <strong>{line.slice(2, -2)}</strong>
                      ) : line.startsWith('•') ? (
                        <div className="bullet-point">{line}</div>
                      ) : (
                        line
                      )}
                    </div>
                  ))}
                </div>
                {message.type === 'user' && (
                  <div className="user-avatar">👤</div>
                )}
              </div>
              <div className="message-timestamp">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="message bot">
              <div className="message-content">
                <div className="bot-avatar">🤖</div>
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          {showQuiz && quizQuestion && (
            <div className="message bot">
              <div className="message-content">
                <div className="bot-avatar">🤖</div>
                <div className="message-text">
                  <h3>📝 Comprehension Check</h3>
                  <p>{quizQuestion.question}</p>
                  <div className="quiz-options">
                    {quizQuestion.options.map((option, index) => (
                      <label key={index} className="quiz-option">
                        <input
                          type="radio"
                          name="quiz-answer"
                          value={option}
                          checked={quizAnswer === option}
                          onChange={(e) => setQuizAnswer(e.target.value)}
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                  <button 
                    onClick={handleQuizSubmit}
                    disabled={!quizAnswer}
                    className="quiz-submit-button"
                  >
                    Submit Answer
                  </button>
                </div>
              </div>
              <div className="message-timestamp">
                {new Date().toLocaleTimeString()}
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="input-container">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={
              currentStep === 'welcome' 
                ? "What health topic would you like to learn about?"
                : currentStep === 'ready-for-quiz'
                ? "Type 'ready' when you're ready for the quiz..."
                : currentStep === 'session-end'
                ? "Type 'another' for a new topic or 'end' to finish..."
                : "Type your message..."
            }
            className="message-input"
            disabled={isTyping}
          />
          <button type="submit" className="send-button" disabled={!inputValue.trim() || isTyping}>
            ➤
          </button>
        </form>
      </div>
    </div>
  );
}

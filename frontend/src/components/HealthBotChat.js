import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { signOut } from 'aws-amplify/auth';
import '../assets/healthbot-chat.css';

export default function HealthBotChat() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentStep, setCurrentStep] = useState('welcome');
  const [quizQuestion, setQuizQuestion] = useState(null);
  const [quizAnswer, setQuizAnswer] = useState('');
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizResult, setQuizResult] = useState(null);
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

  const simulateBotResponse = (response, delay = 1000) => {
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      addMessage({
        type: 'bot',
        content: response,
        timestamp: new Date()
      });
    }, delay);
  };

  const handleTopicSubmit = async (topic) => {
    addMessage({
      type: 'user',
      content: `I'd like to learn about: ${topic}`,
      timestamp: new Date()
    });

    setCurrentStep('searching');
    setIsTyping(true);

    // Simulate searching for information
    setTimeout(() => {
      setIsTyping(false);
      addMessage({
        type: 'bot',
        content: `I'm searching for the latest information about ${topic}...`,
        timestamp: new Date()
      });

      // Simulate finding and summarizing information
      setTimeout(() => {
        addMessage({
          type: 'bot',
          content: `Here's what I found about ${topic}:\n\n**Summary:**\nThis is a patient-friendly summary of the latest medical information about ${topic}. The information includes key points, important facts, and practical advice that you should know.\n\n**Key Points:**\n• Point 1 about ${topic}\n• Point 2 about ${topic}\n• Point 3 about ${topic}\n\nTake your time to read through this information. When you're ready for a comprehension check, just let me know!`,
          timestamp: new Date()
        });
        setCurrentStep('ready-for-quiz');
      }, 2000);
    }, 1500);
  };

  const handleReadyForQuiz = () => {
    addMessage({
      type: 'user',
      content: 'I\'m ready for the comprehension check!',
      timestamp: new Date()
    });

    // Simulate generating quiz question
    setTimeout(() => {
      const mockQuiz = {
        question: `Based on the information about the health topic, which of the following is most accurate?`,
        options: [
          'Option A: This is the correct answer',
          'Option B: This is an incorrect option',
          'Option C: This is another incorrect option',
          'Option D: This is also incorrect'
        ],
        correctAnswer: 0
      };
      
      setQuizQuestion(mockQuiz);
      setShowQuiz(true);
      setCurrentStep('quiz');
    }, 1000);
  };

  const handleQuizSubmit = () => {
    if (!quizAnswer) return;

    addMessage({
      type: 'user',
      content: `My answer: ${quizAnswer}`,
      timestamp: new Date()
    });

    // Simulate evaluating the answer
    setTimeout(() => {
      const isCorrect = quizAnswer === 'Option A: This is the correct answer';
      const result = {
        correct: isCorrect,
        grade: isCorrect ? 'A' : 'C',
        explanation: isCorrect 
          ? 'Excellent! You correctly identified the key point from the information provided. This demonstrates a good understanding of the topic.'
          : 'Good effort! The correct answer was Option A. Here\'s why: [explanation with citations from the summary]. Keep learning!',
        citations: ['Citation 1 from the summary', 'Citation 2 from the summary']
      };
      
      setQuizResult(result);
      setShowQuiz(false);
      setCurrentStep('quiz-complete');
      
      addMessage({
        type: 'bot',
        content: `**Quiz Result: Grade ${result.grade}**\n\n${result.explanation}\n\n**Citations:**\n${result.citations.map(c => `• ${c}`).join('\n')}`,
        timestamp: new Date()
      });

      setTimeout(() => {
        addMessage({
          type: 'bot',
          content: 'Would you like to learn about another health topic, or would you like to end this session?',
          timestamp: new Date()
        });
        setCurrentStep('session-end');
      }, 1000);
    }, 1500);
  };

  const handleNewTopic = () => {
    setMessages([]);
    setCurrentStep('welcome');
    setQuizQuestion(null);
    setQuizAnswer('');
    setShowQuiz(false);
    setQuizResult(null);
    
    setTimeout(() => {
      addMessage({
        type: 'bot',
        content: "Great! Let's start fresh. What health topic or medical condition would you like to learn about?",
        timestamp: new Date()
      });
    }, 500);
  };

  const handleEndSession = () => {
    addMessage({
      type: 'user',
      content: 'I\'d like to end this session.',
      timestamp: new Date()
    });

    addMessage({
      type: 'bot',
      content: 'Thank you for using HealthBot! I hope you learned something valuable today. Feel free to come back anytime to learn about more health topics. Take care!',
      timestamp: new Date()
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userInput = inputValue.trim();
    setInputValue('');

    if (currentStep === 'welcome') {
      handleTopicSubmit(userInput);
    } else if (currentStep === 'ready-for-quiz' && userInput.toLowerCase().includes('ready')) {
      handleReadyForQuiz();
    } else if (currentStep === 'session-end') {
      if (userInput.toLowerCase().includes('another') || userInput.toLowerCase().includes('new')) {
        handleNewTopic();
      } else if (userInput.toLowerCase().includes('end') || userInput.toLowerCase().includes('exit')) {
        handleEndSession();
      } else {
        addMessage({
          type: 'bot',
          content: 'I didn\'t understand. Would you like to learn about another health topic, or would you like to end this session?',
          timestamp: new Date()
        });
      }
    } else {
      addMessage({
        type: 'user',
        content: userInput,
        timestamp: new Date()
      });
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
          
          <div ref={messagesEndRef} />
        </div>

        {showQuiz && quizQuestion && (
          <div className="quiz-container">
            <div className="quiz-question">
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
        )}

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

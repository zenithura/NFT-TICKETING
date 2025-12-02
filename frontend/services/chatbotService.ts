// File header: Chatbot service for communicating with Gemini API via backend.
// Provides functions to send messages, manage sessions, and handle responses.

/**
 * Chatbot Service
 * Handles communication with the backend Gemini chatbot API
 */

// Purpose: API base URL from environment or default.
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Purpose: Message interface for chat messages.
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Purpose: Request interface for sending chat messages.
export interface ChatRequest {
  message: string;
  session_id?: string;
  user_id?: string;
}

// Purpose: Response interface for chatbot replies.
export interface ChatResponse {
  response: string;
  session_id: string;
  timestamp: string;
  error?: string;
}

// Purpose: Send a message to the chatbot API.
// Params: message (string) - User message, sessionId (string?) - Optional session ID.
// Returns: Promise<ChatResponse> - Chatbot response with session ID.
// Side effects: Makes HTTP POST request to backend API.
export const sendChatMessage = async (
  message: string,
  sessionId?: string,
  userId?: string
): Promise<ChatResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chatbot/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        user_id: userId,
      } as ChatRequest),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to send message' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
};

// Purpose: Check chatbot service health.
// Returns: Promise with health status.
// Side effects: Makes HTTP GET request to backend API.
export const checkChatbotHealth = async (): Promise<{
  status: string;
  gemini_available: boolean;
  message: string;
}> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chatbot/health`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error checking chatbot health:', error);
    return {
      status: 'error',
      gemini_available: false,
      message: 'Unable to check chatbot status',
    };
  }
};


// FastAPI Quiz System Client

// const QUIZ_API_BASE = "http://127.0.0.1:8009";
const QUIZ_API_BASE = import.meta.env.VITE_API_URL;


export interface QuizStartResponse {
  sessionId: string;
  done: boolean;
  questionIndex: number;
  assistantMessage: string;
  passed: null;
}

export interface QuizAnswerRequest {
  sessionId: string;
  answer: string;
}

export interface QuizAnswerResponse {
  sessionId: string;
  done: boolean;
  questionIndex: number;
  assistantMessage: string;
  passed: boolean | null;
}

export async function startQuiz(): Promise<QuizStartResponse> {
  const response = await fetch(`${QUIZ_API_BASE}/tutor/erc8004/quiz/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to start quiz: ${response.statusText}`);
  }

  return response.json();
}

export async function submitAnswer(
  data: QuizAnswerRequest
): Promise<QuizAnswerResponse> {
  const response = await fetch(`${QUIZ_API_BASE}/tutor/erc8004/quiz/answer`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to submit answer: ${response.statusText}`);
  }

  return response.json();
}

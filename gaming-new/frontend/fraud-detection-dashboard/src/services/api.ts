declare var process: {
  env: {
    REACT_APP_API_BASE_URL?: string;
  };
};

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi(endpoint: string, options?: RequestInit) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new ApiError(response.status, `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, `Network error: ${error}`);
  }
}

export const fetchFraudDetection = () => fetchApi('/fraud/detect');

export const fetchRiskMetrics = () => fetchApi('/fraud/metrics');

export const fetchOperatorProfile = (operatorId: string) => 
  fetchApi(`/fraud/operators/${operatorId}`);

export const fetchTrends = () => fetchApi('/fraud/trends');

export const checkApiHealth = () => fetchApi('/');

export { ApiError };
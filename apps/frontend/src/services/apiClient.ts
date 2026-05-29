const BASE_URL = '/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || JSON.stringify(errorData);
      if (Array.isArray(errorDetail)) {
        errorDetail = errorDetail.map((d: any) => d.msg).join(', ');
      }
    } catch (e) {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const apiClient = {
  async post<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return handleResponse<T>(response);
    } catch (err: any) {
      if (err.name === 'TypeError') {
        throw new Error('Network error: Is the backend server running?');
      }
      throw err;
    }
  },

  async get<T>(endpoint: string): Promise<T> {
    try {
      const response = await fetch(`${BASE_URL}${endpoint}`);
      return handleResponse<T>(response);
    } catch (err: any) {
      if (err.name === 'TypeError') {
        throw new Error('Network error: Is the backend server running?');
      }
      throw err;
    }
  },

  async patch<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return handleResponse<T>(response);
    } catch (err: any) {
      if (err.name === 'TypeError') {
        throw new Error('Network error: Is the backend server running?');
      }
      throw err;
    }
  },
};

import axios from 'axios';

const apiInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Request interceptor to attach token
apiInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const api = {
  login: async (email: string, password: string) => {
    const response = await apiInstance.post('/api/v1/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  register: async (email: string, password: string, full_name: string) => {
    const response = await apiInstance.post('/api/v1/auth/register', {
      email,
      password,
      full_name,
    });
    return response.data;
  },
  
  // existing uploads / analysis methods:
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiInstance.post('/api/v1/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  startAnalysis: async (fileId: number) => {
    const response = await apiInstance.post(`/api/v1/jobs`, {
      file_id: fileId
    });
    return response.data;
  },

  getAnalysisStatus: async (jobId: string) => {
    const response = await apiInstance.get(`/api/v1/jobs/${jobId}`);
    return response.data;
  },

  getVariants: async (jobId: string) => {
    const response = await apiInstance.get(`/api/v1/variants/${jobId}`);
    return response.data;
  },

  getReport: async (jobId: string) => {
    const response = await apiInstance.get(`/api/v1/variants/${jobId}/report`);
    return response.data;
  },

  chatWithResults: async (
    jobId: string,
    message: string,
    history: Array<{ role: 'user' | 'assistant'; content: string }>
  ) => {
    const response = await apiInstance.post(`/api/v1/variants/${jobId}/chat`, {
      message,
      history,
    });
    return response.data;
  }
};

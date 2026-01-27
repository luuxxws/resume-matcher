/**
 * API Client for Resume Matcher Backend
 */

const API_BASE = '/api';

// Types matching the backend schemas
export interface HealthResponse {
  status: string;
  version: string;
}

export interface StatsResponse {
  total_resumes: number;
  with_embeddings: number;
  with_parsed_data: number;
}

export interface CandidateInfo {
  name: string | null;
  position: string | null;
  email: string | null;
  phone: string | null;
  skills: string[];
  years_experience: number | null;
  summary: string | null;
}

export interface ResumeResponse {
  id: number;
  file_name: string;
  file_path: string;
  has_embedding: boolean;
  json_data: Record<string, unknown>;
}

export interface ResumeListResponse {
  total: number;
  limit: number;
  offset: number;
  resumes: ResumeResponse[];
}

export interface MatchedResumeResponse {
  rank: number;
  id: number;
  file_name: string;
  file_path: string;
  similarity_percent: number;
  candidate: CandidateInfo;
}

export interface EmbeddingMatchResponse {
  mode: 'embedding';
  total_resumes_in_db: number;
  matches_found: number;
  matches: MatchedResumeResponse[];
}

export interface LLMMatchedResumeResponse {
  rank: number;
  id: number;
  file_name: string;
  combined_score: number;
  llm_score: number;
  embedding_score_percent: number;
  match_level: string;
  matching_skills: string[];
  missing_skills: string[];
  strengths: string[];
  concerns: string[];
  explanation: string;
}

export interface VacancyInfo {
  job_title: string;
  seniority_level: string | null;
  must_have_skills: string[];
  nice_to_have_skills: string[];
  min_years_experience: number | null;
  summary: string;
}

export interface LLMMatchResponse {
  mode: 'llm';
  vacancy: VacancyInfo;
  matches_found: number;
  matches: LLMMatchedResumeResponse[];
}

export type MatchResponse = EmbeddingMatchResponse | LLMMatchResponse;

export interface MatchRequest {
  vacancy_text: string;
  top_n?: number;
  min_score?: number;
  max_score?: number;
  use_llm?: boolean;
  embedding_candidates?: number;
  lang?: string; // Language for LLM responses: 'en' | 'ru'
}

export interface ImportResponse {
  status: string;
  files_found: number;
  message: string;
}

// API Error class
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// Helper function for API calls
async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Network error - is the backend running?');
  }
}

// API Methods
export const api = {
  // Health & Info
  health: () => apiCall<HealthResponse>('/health'),
  stats: () => apiCall<StatsResponse>('/stats'),

  // Resumes
  listResumes: (params?: { limit?: number; offset?: number; search?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.search) searchParams.set('search', params.search);
    const query = searchParams.toString();
    return apiCall<ResumeListResponse>(`/resumes${query ? `?${query}` : ''}`);
  },

  getResume: (id: number) => apiCall<ResumeResponse>(`/resumes/${id}`),
  
  deleteResume: (id: number) => 
    apiCall<{ status: string; id: string }>(`/resumes/${id}`, { method: 'DELETE' }),

  // Matching
  match: (request: MatchRequest) =>
    apiCall<MatchResponse>('/match', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  matchFile: async (
    file: File,
    params?: { top_n?: number; use_llm?: boolean }
  ): Promise<MatchResponse> => {
    const formData = new FormData();
    formData.append('vacancy_file', file);
    
    const searchParams = new URLSearchParams();
    if (params?.top_n) searchParams.set('top_n', params.top_n.toString());
    if (params?.use_llm !== undefined) searchParams.set('use_llm', params.use_llm.toString());
    
    const query = searchParams.toString();
    const url = `${API_BASE}/match/file${query ? `?${query}` : ''}`;
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, error.detail);
    }

    return response.json();
  },

  // Import
  importResumes: (params: { directory?: string; force?: boolean; limit?: number }) => {
    const formData = new FormData();
    if (params.directory) formData.append('directory', params.directory);
    if (params.force !== undefined) formData.append('force', params.force.toString());
    if (params.limit !== undefined) formData.append('limit', params.limit.toString());
    
    return fetch(`${API_BASE}/import`, {
      method: 'POST',
      body: formData,
    }).then(async (res) => {
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new ApiError(res.status, error.detail);
      }
      return res.json() as Promise<ImportResponse>;
    });
  },

  importFile: async (file: File): Promise<{ status: string; file_name: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/import/file`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, error.detail);
    }

    return response.json();
  },
};

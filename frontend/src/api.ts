import {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  ProjectListItem,
  ProjectDetail,
  CreateProjectRequest,
  InviteResponse,
  Checkin,
  ProjectAnalytics,
  UserAnalytics,
} from './types';

const API_BASE = 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401 && this.refreshToken) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          headers['Authorization'] = `Bearer ${this.accessToken}`;
          const retryResponse = await fetch(url, { ...options, headers });
          if (retryResponse.ok) {
            return retryResponse.json();
          }
        }
      }

      const errorText = await response.text();
      let errorMessage = errorText;
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorText;
      } catch {
        // Use text as is
      }
      throw new ApiError(response.status, errorMessage);
    }

    return response.json();
  }

  private async refreshAccessToken(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (response.ok) {
        const data: TokenResponse = await response.json();
        this.setTokens(data.access_token, data.refresh_token);
        return true;
      }
    } catch {
      this.clearTokens();
    }
    return false;
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  // Auth endpoints
  async register(data: RegisterRequest): Promise<User> {
    return this.request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await this.request<TokenResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setTokens(response.access_token, response.refresh_token);
    return response;
  }

  logout() {
    this.clearTokens();
  }

  async getMe(): Promise<User> {
    return this.request<User>('/api/auth/me');
  }

  // Project endpoints
  async getProjects(): Promise<ProjectListItem[]> {
    return this.request<ProjectListItem[]>('/api/projects');
  }

  async getProject(id: number): Promise<ProjectDetail> {
    return this.request<ProjectDetail>(`/api/projects/${id}`);
  }

  async createProject(data: CreateProjectRequest): Promise<void> {
    await this.request('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Invite endpoints
  async createInvite(projectId: number): Promise<InviteResponse> {
    return this.request<InviteResponse>('/api/invites', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId }),
    });
  }

  async acceptInvite(code: string): Promise<{ project_id: number }> {
    return this.request<{ project_id: number }>('/api/invites/accept', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  }

  // Checkin endpoints
  async createCheckin(projectId: number): Promise<Checkin> {
    return this.request<Checkin>('/api/checkins', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId }),
    });
  }

  // Analytics endpoints
  async getProjectAnalytics(projectId: number): Promise<ProjectAnalytics> {
    return this.request<ProjectAnalytics>(`/api/analytics/projects/${projectId}`);
  }

  async getUserAnalytics(
    userId: number,
    projectId: number
  ): Promise<UserAnalytics> {
    return this.request<UserAnalytics>(
      `/api/analytics/users/${userId}/projects/${projectId}`
    );
  }
}

export const api = new ApiClient();
export { ApiError };

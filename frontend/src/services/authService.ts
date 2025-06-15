import { apiClient } from './api'
import { API_BASE_URL } from './apiConstants';

export interface User {
  id: number;
  username: string;
  role: 'admin' | 'user' | 'expert';
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  role: 'admin' | 'user' | 'expert';
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// 新增邀请码相关接口
export interface InviteCode {
  id: number;
  code: string;
  created_by: number;
  created_at: string;
  expires_at: string;
  is_used: boolean;
  used_by?: number;
  used_at?: string;
}

export interface InviteCodeCreateRequest {
  expires_in_hours?: number;
}

class AuthService {
  private baseUrl = 'http://localhost:8000';  async register(data: RegisterRequest): Promise<AuthResponse> {
    try {
      const response = await apiClient.post('/auth/register', data)
      
      // 注册成功后自动登录
      const loginResponse = await this.login({
        username: data.username,
        password: data.password
      })
      
      return loginResponse
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '注册失败')
    }
  }  async login(data: LoginRequest): Promise<AuthResponse> {
    try {
      const tokenResponse = await apiClient.post('/auth/login', data)
      const tokenData = tokenResponse.data
      
      // 获取用户信息
      const userResponse = await apiClient.get('/auth/me', {
        headers: {
          'Authorization': `Bearer ${tokenData.access_token}`,
        },
      })

      const user = userResponse.data
      
      return {
        access_token: tokenData.access_token,
        token_type: tokenData.token_type,
        user: user
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '登录失败')
    }
  }  async getCurrentUser(): Promise<User> {
    const token = this.getToken()
    if (!token) {
      throw new Error('未找到认证令牌')
    }

    try {
      const response = await apiClient.get('/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        this.clearToken()
        throw new Error('认证已过期，请重新登录')
      }
      throw new Error('获取用户信息失败')
    }
  }

  saveToken(token: string, user: User): void {
    localStorage.setItem('access_token', token);
    localStorage.setItem('userInfo', JSON.stringify(user));
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  clearToken(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('userInfo');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getCurrentUserFromStorage(): User | null {
    const userInfo = localStorage.getItem('userInfo');
    return userInfo ? JSON.parse(userInfo) : null;
  }

  async logout(): Promise<void> {
    this.clearToken();
  }

  async getMyInviteCode(): Promise<{ invite_code: string }> {
    try {
      const response = await apiClient.get('/auth/invite-codes');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取邀请码失败');
    }
  }

  async generateInviteCode(expiresInHours = 24): Promise<InviteCode> {
    try {
      const response = await apiClient.post('/auth/invite-codes', {
        expires_in_hours: expiresInHours
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '生成邀请码失败');
    }
  }

  async getMyInviteCodes(): Promise<InviteCode[]> {
    try {
      const response = await apiClient.get('/auth/invite-codes');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取邀请码列表失败');
    }
  }

  async revokeInviteCode(codeId: number): Promise<void> {
    try {
      await apiClient.delete(`/auth/invite-codes/${codeId}`);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '撤销邀请码失败');
    }
  }

  async joinWithInviteCode(inviteCode: string): Promise<{ message: string }> {
    try {
      const response = await apiClient.post('/auth/join-with-invite', {
        invite_code: inviteCode
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '使用邀请码加入失败');
    }
  }
}

export const authService = new AuthService();

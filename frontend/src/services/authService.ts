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
}

export const authService = new AuthService();

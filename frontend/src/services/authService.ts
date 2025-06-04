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
  private baseUrl = 'http://localhost:8000';
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '注册失败');
    }

    const user = await response.json();
    
    // 注册成功后自动登录
    const loginResponse = await this.login({
      username: data.username,
      password: data.password
    });
    
    return loginResponse;
  }  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '登录失败');
    }

    const tokenData = await response.json();
    
    // 获取用户信息
    const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${tokenData.access_token}`,
      },
    });

    if (!userResponse.ok) {
      throw new Error('获取用户信息失败');
    }

    const user = await userResponse.json();
    
    return {
      access_token: tokenData.access_token,
      token_type: tokenData.token_type,
      user: user
    };
  }
  async getCurrentUser(): Promise<User> {
    const token = this.getToken();
    if (!token) {
      throw new Error('未找到认证令牌');
    }

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken();
        throw new Error('认证已过期，请重新登录');
      }
      throw new Error('获取用户信息失败');
    }

    return response.json();
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

import { API_BASE_URL } from "./apiConstants";

export interface Dataset {
  id: number;
  name: string;
  description: string;
  created_by: number; 
  is_public: boolean;
  create_time: string;
}

export interface DatasetWithStats extends Dataset {
  std_questions_count: number;
  std_answers_count: number;
  raw_questions_count: number;
  creator_username?: string;
}

export interface DatasetCreate {
  name: string;
  description: string;
  is_public?: boolean;
}

// 添加认证头部的辅助函数
const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
};

export const datasetService = {
  // 获取数据库市场列表
  async getMarketplace(
    skip = 0,
    limit = 50,
    currentUser?: string
  ): Promise<DatasetWithStats[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (currentUser) {
      params.append("current_user", currentUser);
    }

    const response = await fetch(`${API_BASE_URL}/datasets/marketplace?${params}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to fetch datasets marketplace");
    }

    return response.json();
  },

  // 获取用户的数据集
  async getUserDatasets(
    skip = 0,
    limit = 50
  ): Promise<Dataset[]> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    const response = await fetch(`${API_BASE_URL}/datasets/my?${params}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to fetch user datasets");
    }

    return response.json();
  },
  // 创建新数据集
  async createDataset(dataset: DatasetCreate): Promise<Dataset> {
    const response = await fetch(`${API_BASE_URL}/datasets/`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(dataset),
    });

    if (!response.ok) {
      throw new Error("Failed to create dataset");
    }

    return response.json();
  },

  // 获取数据集详情
  async getDataset(id: number): Promise<Dataset> {
    const response = await fetch(`${API_BASE_URL}/datasets/${id}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to fetch dataset");
    }

    return response.json();
  },

  // 获取数据集统计信息
  async getDatasetStats(id: number): Promise<{
    dataset_id: number;
    description: string;
    create_time: string;
    std_questions_count: number;
    std_answers_count: number;
  }> {
    const response = await fetch(`${API_BASE_URL}/datasets/${id}/stats`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error("Failed to fetch dataset stats");
    }

    return response.json();
  },

  // 更新数据集
  async updateDataset(
    id: number,
    update: Partial<DatasetCreate>
  ): Promise<Dataset> {
    const response = await fetch(`${API_BASE_URL}/datasets/${id}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(update),
    });

    if (!response.ok) {
      throw new Error("Failed to update dataset");
    }

    return response.json();
  },

  // 删除数据集
  async deleteDataset(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/datasets/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to delete dataset");
    }
  },
};

import { apiClient } from './api'
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
  creator_username?: string;
}

export interface DatasetCreate {
  name: string;
  description: string;
  is_public?: boolean;
}

export const datasetService = {
  // 获取数据库市场列表
  async getMarketplace(
    skip = 0,
    limit = 50,
    currentUser?: string
  ): Promise<DatasetWithStats[]> {
    try {
      const params: any = {
        skip: skip.toString(),
        limit: limit.toString(),
      };

      if (currentUser) {
        params.current_user = currentUser;
      }

      const response = await apiClient.get('/datasets/marketplace', { params });
      return response.data;
    } catch (error) {
      throw new Error("Failed to fetch datasets marketplace");
    }
  },

  // 获取用户的数据集
  async getUserDatasets(
    skip = 0,
    limit = 50
  ): Promise<DatasetWithStats[]> {
    try {
      const params: any = {
        skip: skip.toString(),
        limit: limit.toString(),
      };

      const response = await apiClient.get('/datasets/my', { params });
      return response.data;
    } catch (error) {
      throw new Error("Failed to fetch user datasets");
    }
  },

  // 创建新数据集
  async createDataset(dataset: DatasetCreate): Promise<Dataset> {
    try {
      const response = await apiClient.post('/datasets/', dataset);
      return response.data;
    } catch (error) {
      throw new Error("Failed to create dataset");
    }
  },

  // 获取数据集详情
  async getDataset(id: number): Promise<Dataset> {
    try {
      const response = await apiClient.get(`/datasets/${id}`);
      return response.data;
    } catch (error) {
      throw new Error("Failed to fetch dataset");
    }
  },

  // 获取数据集统计信息
  async getDatasetStats(id: number): Promise<{
    dataset_id: number;
    description: string;
    create_time: string;
    std_questions_count: number;
    std_answers_count: number;
  }> {
    try {
      const response = await apiClient.get(`/datasets/${id}/stats`);
      return response.data;
    } catch (error) {
      throw new Error("Failed to fetch dataset stats");
    }
  },

  // 更新数据集
  async updateDataset(
    id: number,
    update: Partial<DatasetCreate>
  ): Promise<Dataset> {
    try {
      const response = await apiClient.put(`/datasets/${id}`, update);
      return response.data;
    } catch (error) {
      throw new Error("Failed to update dataset");
    }
  },

  // 删除数据集
  async deleteDataset(id: number): Promise<void> {
    try {
      await apiClient.delete(`/datasets/${id}`);
    } catch (error) {
      throw new Error("Failed to delete dataset");
    }
  },
};

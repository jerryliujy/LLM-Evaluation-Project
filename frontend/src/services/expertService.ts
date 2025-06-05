import { apiClient } from './api'
import type { ExpertCreate, Expert, ExpertLogin } from "@/types/expert";

export const expertService = {
  // 创建专家
  async createExpert(expertData: ExpertCreate): Promise<Expert> {
    try {
      const response = await apiClient.post('/experts/', expertData);
      return response.data;
    } catch (error) {
      throw new Error("创建专家失败");
    }
  },

  // 专家登录
  async login(
    loginData: ExpertLogin
  ): Promise<{ expert: Expert; success: boolean }> {
    try {
      const response = await apiClient.post('/experts/login', loginData);
      const result = response.data;
      return {
        expert: result.expert,
        success: result.success,
      };
    } catch (error) {
      throw new Error("登录失败");
    }
  },

  // 获取专家信息
  async getExpert(expertId: number): Promise<Expert> {
    try {
      const response = await apiClient.get(`/experts/${expertId}`);
      return response.data;
    } catch (error) {
      throw new Error("获取专家信息失败");
    }
  },

  // 获取所有专家
  async getAllExperts(includeDeleted = false): Promise<Expert[]> {
    try {
      const params: any = {};
      if (includeDeleted) {
        params.include_deleted = "true";
      }

      const response = await apiClient.get('/experts/', { params });
      return response.data;
    } catch (error) {
      throw new Error("获取专家列表失败");
    }
  },

  // 删除专家
  async deleteExpert(expertId: number): Promise<void> {
    try {
      await apiClient.delete(`/experts/${expertId}`);
    } catch (error) {
      throw new Error("删除专家失败");
    }
  },

  // 恢复专家
  async restoreExpert(expertId: number): Promise<Expert> {
    try {
      const response = await apiClient.post(`/experts/${expertId}/restore`);
      return response.data;
    } catch (error) {
      throw new Error("恢复专家失败");
    }
  },
};

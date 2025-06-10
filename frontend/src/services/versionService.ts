import { apiClient } from './api';

export interface VersionCreateRequest {
  name: string;
  description?: string;
}

export interface VersionPublishRequest {
  is_public: boolean;
}

export interface VersionQuestionUpdateRequest {
  body?: string;
  question_type?: string;
  tags?: string[];
  std_answers?: Array<{
    answer: string;
    answered_by?: string;
    scoring_points?: Array<{
      answer: string;
      point_order: number;
    }>;
  }>;
}

export interface VersionQACreateRequest {
  question: {
    body: string;
    question_type: string;
    tags?: string[];
  };
  answer: {
    answer: string;
    answered_by?: string;
    scoring_points?: Array<{
      answer: string;
      point_order: number;
    }>;
  };
}

export class VersionService {
  // 创建数据集版本
  async createDatasetVersion(datasetId: number, data: VersionCreateRequest) {
    const response = await apiClient.post(`/datasets/${datasetId}/versions`, data);
    return response.data;
  }

  // 获取版本信息
  async getVersion(versionId: number) {
    const response = await apiClient.get(`/versions/${versionId}`);
    return response.data;
  }

  // 获取版本中的问答对
  async getVersionQuestions(versionId: number) {
    const response = await apiClient.get(`/versions/${versionId}/std-qa`);
    return response.data;
  }

  // 更新版本中的问题
  async updateVersionQuestion(versionId: number, questionId: number, data: VersionQuestionUpdateRequest) {
    const response = await apiClient.put(`/versions/${versionId}/std-questions/${questionId}`, data);
    return response.data;
  }

  // 删除版本中的问题
  async deleteVersionQuestion(versionId: number, questionId: number) {
    const response = await apiClient.delete(`/versions/${versionId}/std-questions/${questionId}`);
    return response.data;
  }

  // 在版本中创建问答对
  async createVersionQA(versionId: number, data: VersionQACreateRequest) {
    const response = await apiClient.post(`/versions/${versionId}/std-qa`, data);
    return response.data;
  }

  // 提交版本
  async commitVersion(versionId: number, data: VersionPublishRequest) {
    const response = await apiClient.post(`/versions/${versionId}/commit`, data);
    return response.data;
  }

  // 导入数据到版本
  async importDataToVersion(versionId: number, data: any[]) {
    const response = await apiClient.post(`/versions/${versionId}/import`, { data });
    return response.data;
  }
}

export const versionService = new VersionService();

import { apiClient } from './api';

export interface DatasetVersionWorkCreateRequest {
  dataset_id: number;
  current_version: number;
  target_version: number;
  work_description?: string;
  notes?: string;
}

export interface VersionStdQuestionCreateRequest {
  original_question_id?: number;
  is_modified?: boolean;
  is_new?: boolean;
  is_deleted?: boolean;
  modified_body?: string;
  modified_question_type?: 'choice' | 'text';
}

export interface VersionStdAnswerCreateRequest {
  version_question_id: number;
  original_answer_id?: number;
  is_modified?: boolean;
  is_deleted?: boolean;
  is_new?: boolean;
  modified_answer?: string;
  modified_answered_by?: number;
}

export interface VersionTagCreateRequest {
  version_question_id: number;
  tag_label: string;
  is_deleted?: boolean;
  is_new?: boolean;
}

export interface CreateVersionResponse {
  success: boolean;
  message: string;
  version_info: {
    dataset_id: number;
    version: number;
    questions_count: number;
    description?: string;
    created_at?: string;
  };
  work: any;
}

export class DatasetVersionWorkService {
  
  // 创建版本工作
  async createVersionWork(data: DatasetVersionWorkCreateRequest) {
    const response = await apiClient.post('/dataset-version-work/', data);
    return response.data;
  }

  // 获取版本工作详情
  async getVersionWork(workId: number) {
    const response = await apiClient.get(`/dataset-version-work/${workId}`);
    return response.data;
  }

  // 获取我的版本工作列表
  async getMyVersionWorks(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    dataset_id?: number;
  }) {
    const response = await apiClient.get('/dataset-version-work/', { params });
    return response.data;
  }

  // 更新版本工作
  async updateVersionWork(workId: number, data: Partial<DatasetVersionWorkCreateRequest>) {
    const response = await apiClient.put(`/dataset-version-work/${workId}`, data);
    return response.data;
  }

  // 完成版本工作（原有方法）
  async completeVersionWork(workId: number) {
    const response = await apiClient.post(`/dataset-version-work/${workId}/complete`);
    return response.data;
  }

  // 创建新版本（推荐使用）
  async createNewVersion(workId: number): Promise<CreateVersionResponse> {
    const response = await apiClient.post(`/dataset-version-work/${workId}/create-version`);
    return response.data;
  }

  // 取消版本工作
  async cancelVersionWork(workId: number) {
    const response = await apiClient.post(`/dataset-version-work/${workId}/cancel`);
    return response.data;
  }

  // 删除版本工作
  async deleteVersionWork(workId: number) {
    const response = await apiClient.delete(`/dataset-version-work/${workId}`);
    return response.data;
  }

  // ============ Version Questions ============

  // 创建版本问题
  async createVersionQuestion(workId: number, data: VersionStdQuestionCreateRequest) {
    const response = await apiClient.post(`/dataset-version-work/${workId}/questions`, data);
    return response.data;
  }

  // 获取版本问题列表
  async getVersionQuestions(workId: number) {
    const response = await apiClient.get(`/dataset-version-work/${workId}/questions`);
    return response.data;
  }

  // 更新版本问题
  async updateVersionQuestion(workId: number, questionId: number, data: Partial<VersionStdQuestionCreateRequest>) {
    const response = await apiClient.put(`/dataset-version-work/${workId}/questions/${questionId}`, data);
    return response.data;
  }

  // 删除版本问题
  async deleteVersionQuestion(workId: number, questionId: number) {
    const response = await apiClient.delete(`/dataset-version-work/${workId}/questions/${questionId}`);
    return response.data;
  }

  // ============ Version Answers ============

  // 创建版本答案
  async createVersionAnswer(workId: number, data: VersionStdAnswerCreateRequest) {
    const response = await apiClient.post(`/dataset-version-work/${workId}/answers`, data);
    return response.data;
  }

  // 更新版本答案
  async updateVersionAnswer(workId: number, answerId: number, data: Partial<VersionStdAnswerCreateRequest>) {
    const response = await apiClient.put(`/dataset-version-work/${workId}/answers/${answerId}`, data);
    return response.data;
  }

  // ============ Version Tags ============

  // 创建版本标签
  async createVersionTag(workId: number, data: VersionTagCreateRequest) {
    const response = await apiClient.post(`/dataset-version-work/${workId}/tags`, data);
    return response.data;
  }

  // ============ Utility Methods ============

  // 从现有数据集加载到版本工作
  async loadDatasetToVersionWork(workId: number, datasetId: number, version: number) {
    const response = await apiClient.post(`/dataset-version-work/${workId}/load-dataset`, {
      dataset_id: datasetId,
      version: version
    });
    return response.data;
  }

  // 获取版本工作统计
  async getVersionWorkStatistics(workId: number) {
    const response = await apiClient.get(`/dataset-version-work/${workId}/statistics`);
    return response.data;
  }

  // 预览版本更改
  async previewVersionChanges(workId: number) {
    const response = await apiClient.get(`/dataset-version-work/${workId}/preview`);
    return response.data;
  }
}

export const datasetVersionWorkService = new DatasetVersionWorkService();

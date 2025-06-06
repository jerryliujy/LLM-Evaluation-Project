import { apiClient } from './api'
import { RawQuestion } from "@/types/questions";
import { RawAnswer, ExpertAnswer } from "@/types/answers";
import { ApiMessage } from "@/types/api";
import { API_BASE_URL } from "./apiConstants";

export const rawQuestionService = {
  // 获取用户的原始问题列表（调整为通用端点）
  async getRawQuestions(skip = 0, limit = 100, include_deleted = false, deleted_only = false): Promise<RawQuestion[]> {
    const response = await apiClient.get(`/raw_questions/`, {
      params: { skip, limit, include_deleted, deleted_only },
    });
    return response.data.data; // 返回分页响应中的data字段
  },

  // 创建新的原始问题
  async createRawQuestion(questionData: Partial<RawQuestion>): Promise<RawQuestion> {
    const response = await apiClient.post('/raw_questions/', questionData);
    return response.data;
  },

  // 更新原始问题
  async updateRawQuestion(id: number, questionData: Partial<RawQuestion>): Promise<RawQuestion> {
    const response = await apiClient.put(`/raw_questions/${id}`, questionData);
    return response.data;
  },

  // 获取单个原始问题
  async getRawQuestion(id: number): Promise<RawQuestion> {
    const response = await apiClient.get(`/raw_questions/${id}/`);
    return response.data;
  },

  async deleteRawQuestion(questionId: number): Promise<ApiMessage> {
    const response = await apiClient.delete(`/raw_questions/${questionId}/`);
    return response.data;
  },

  async forceDeleteRawQuestion(questionId: number): Promise<ApiMessage> {
    const response = await apiClient.delete(`/raw_questions/${questionId}/force-delete/`);
    return response.data;
  },

  async restoreRawQuestion(questionId: number): Promise<RawQuestion> {
    const response = await apiClient.post(`/raw_questions/${questionId}/restore/`);
    return response.data;
  },

  async deleteMultipleRawQuestions (questionIds: number[]): Promise<ApiMessage> {
    const response = await apiClient.post('/raw_questions/delete-multiple/', questionIds);
    return response.data;
  },

  async restoreMultipleRawQuestions (questionIds: number[]): Promise<ApiMessage> {
    const response = await apiClient.post('/raw_questions/restore-multiple/', questionIds);
    return response.data;
  },

  // Raw Answers
  async deleteRawAnswer (answerId: number): Promise<ApiMessage> {
    const response = await apiClient.delete(`/raw_answers/${answerId}/`);
    return response.data;
  },

  async restoreRawAnswer (answerId: number): Promise<RawAnswer> {
    const response = await apiClient.post(`/raw_answers/${answerId}/restore/`);
    return response.data;
  },

  async deleteMultipleRawAnswers (answerIds: number[]): Promise<ApiMessage> {
    const response = await apiClient.post('/raw_answers/delete-multiple/', answerIds);
    return response.data;
  },

  // Expert Answers
  async deleteExpertAnswer (answerId: number): Promise<ApiMessage> {
    const response = await apiClient.delete(`/expert_answers/${answerId}/`);
    return response.data;
  },

  async restoreExpertAnswer (answerId: number): Promise<ExpertAnswer> {
    const response = await apiClient.post(`/expert_answers/${answerId}/restore/`);
    return response.data;
  },

  async deleteMultipleExpertAnswers (answerIds: number[]): Promise<ApiMessage> {
    const response = await apiClient.post('/expert_answers/delete-multiple/', answerIds);
    return response.data;
  },

  // 获取原始问题概览（包含所有回答）
  async getRawQuestionsOverview(skip = 0, limit = 20, include_deleted = false, deleted_only = false): Promise<any> {
    const response = await apiClient.get(`/raw_questions/overview`, {
      params: { skip, limit, include_deleted, deleted_only },
    });
    return response.data;
  },

  // 获取原始回答视图
  async getRawAnswersView(skip = 0, limit = 20, include_deleted = false, deleted_only = false): Promise<any> {
    const response = await apiClient.get(`/raw_questions/raw-answers-view`, {
      params: { skip, limit, include_deleted, deleted_only },
    });
    return response.data;
  },

  // 获取专家回答视图
  async getExpertAnswersView(skip = 0, limit = 20, include_deleted = false, deleted_only = false): Promise<any> {
    const response = await apiClient.get(`/raw_questions/expert-answers-view`, {
      params: { skip, limit, include_deleted, deleted_only },
    });
    return response.data;
  },
}
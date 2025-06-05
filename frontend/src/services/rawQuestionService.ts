import { apiClient } from './api'
import { RawQuestion } from "@/types/questions";
import { RawAnswer, ExpertAnswer } from "@/types/answers";
import { ApiMessage } from "@/types/api";
import { API_BASE_URL } from "./apiConstants";

// Raw Questions
export const fetchRawQuestions = async (
  skip: number,
  limit: number
): Promise<RawQuestion[]> => {
  const response = await apiClient.get('/raw_questions/', {
    params: { skip, limit },
  });
  return response.data;
};

export const deleteRawQuestion = async (
  questionId: number
): Promise<ApiMessage> => {
  const response = await apiClient.delete(`/raw_questions/${questionId}/`);
  return response.data;
};

export const restoreRawQuestion = async (
  questionId: number
): Promise<RawQuestion> => {
  const response = await apiClient.post(`/raw_questions/${questionId}/restore/`);
  return response.data;
};

export const deleteMultipleRawQuestions = async (
  questionIds: number[]
): Promise<ApiMessage> => {
  const response = await apiClient.post('/raw_questions/delete-multiple/', questionIds);
  return response.data;
};

export const restoreMultipleRawQuestions = async (
  questionIds: number[]
): Promise<ApiMessage> => {
  const response = await apiClient.post('/raw_questions/restore-multiple/', questionIds);
  return response.data;
};

// Raw Answers
export const deleteRawAnswer = async (
  answerId: number
): Promise<ApiMessage> => {
  const response = await apiClient.delete(`/raw_answers/${answerId}/`);
  return response.data;
};

export const restoreRawAnswer = async (
  answerId: number
): Promise<RawAnswer> => {
  const response = await apiClient.post(`/raw_answers/${answerId}/restore/`);
  return response.data;
};

export const deleteMultipleRawAnswers = async (
  answerIds: number[]
): Promise<ApiMessage> => {
  const response = await apiClient.post('/raw_answers/delete-multiple/', answerIds);
  return response.data;
};

// Expert Answers
export const deleteExpertAnswer = async (
  answerId: number
): Promise<ApiMessage> => {
  const response = await apiClient.delete(`/expert_answers/${answerId}/`);
  return response.data;
};

export const restoreExpertAnswer = async (
  answerId: number
): Promise<ExpertAnswer> => {
  const response = await apiClient.post(`/expert_answers/${answerId}/restore/`);
  return response.data;
};

export const deleteMultipleExpertAnswers = async (
  answerIds: number[]
): Promise<ApiMessage> => {
  const response = await apiClient.post('/expert_answers/delete-multiple/', answerIds);
  return response.data;
};

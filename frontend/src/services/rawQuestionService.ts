import axios from 'axios';
import { RawQuestion } from '@/types/questions';
import { RawAnswer, ExpertAnswer } from '@/types/answers';
import { ApiMessage } from '@/types/api';
import { API_BASE_URL } from './apiConstants';

const RQ_ENDPOINT = `${API_BASE_URL}/raw_questions`;
const RA_ENDPOINT = `${API_BASE_URL}/raw_answers`;
const EX_ENDPOINT = `${API_BASE_URL}/expert_answers`;

// Raw Questions
export const fetchRawQuestions = async (skip: number, limit: number): Promise<RawQuestion[]> => {
  const response = await axios.get<RawQuestion[]>(`${RQ_ENDPOINT}/`, { params: { skip, limit } });
  return response.data;
};

export const deleteRawQuestion = async (questionId: number): Promise<ApiMessage> => {
  const response = await axios.delete<ApiMessage>(`${RQ_ENDPOINT}/${questionId}/`);
  return response.data;
};

export const restoreRawQuestion = async (questionId: number): Promise<RawQuestion> => {
  const response = await axios.post<RawQuestion>(`${RQ_ENDPOINT}/${questionId}/restore/`);
  return response.data;
};

export const deleteMultipleRawQuestions = async (questionIds: number[]): Promise<ApiMessage> => {
    const response = await axios.post<ApiMessage>(`${RQ_ENDPOINT}/delete-multiple/`, questionIds);
    return response.data;
};

export const restoreMultipleRawQuestions = async (questionIds: number[]): Promise<ApiMessage> => {
    const response = await axios.post<ApiMessage>(`${RQ_ENDPOINT}/restore-multiple/`, questionIds);
    return response.data;
};

// Raw Answers
export const deleteRawAnswer = async (answerId: number): Promise<ApiMessage> => {
  const response = await axios.delete<ApiMessage>(`${RA_ENDPOINT}/${answerId}/`);
  return response.data;
};

export const restoreRawAnswer = async (answerId: number): Promise<RawAnswer> => {
  const response = await axios.post<RawAnswer>(`${RA_ENDPOINT}/${answerId}/restore/`);
  return response.data;
};

export const deleteMultipleRawAnswers = async (answerIds: number[]): Promise<ApiMessage> => {
    const response = await axios.post<ApiMessage>(`${RA_ENDPOINT}/delete-multiple/`, answerIds);
    return response.data;
};

// Expert Answers
export const deleteExpertAnswer = async (answerId: number): Promise<ApiMessage> => {
  const response = await axios.delete<ApiMessage>(`${EX_ENDPOINT}/${answerId}/`);
  return response.data;
};

export const restoreExpertAnswer = async (answerId: number): Promise<ExpertAnswer> => {
  const response = await axios.post<ExpertAnswer>(`${EX_ENDPOINT}/${answerId}/restore/`);
  return response.data;
};

export const deleteMultipleExpertAnswers = async (answerIds: number[]): Promise<ApiMessage> => {
    const response = await axios.post<ApiMessage>(`${EX_ENDPOINT}/delete-multiple/`, answerIds);
    return response.data;
};
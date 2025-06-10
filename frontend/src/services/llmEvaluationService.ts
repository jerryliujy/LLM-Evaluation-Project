/**
 * LLM评测相关的API服务
 */
import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error.response?.data || error);
  }
);

export interface MarketplaceDataset {
  id: number;
  name: string;
  description: string;
  version: number;
  question_count: number;
  is_public: boolean;
  created_by: number;
  create_time: string;
}

export interface DatasetDownloadResponse {
  dataset_info: MarketplaceDataset;
  questions: Array<{
    id: number;
    body: string;
    question_type: string;
    std_answers: Array<{
      id: number;
      answer: string;
      scoring_points: Array<{
        answer: string;
        point_order: number;
      }>;
    }>;
  }>;
}

export interface LLMAnswer {
  llm_id: number;
  std_question_id: number;
  answer: string;
  api_request_id?: string;
  model_params?: string;
  cost_tokens?: number;
  scoring_points?: Array<{
    answer: string;
    point_order: number;
  }>;
}

export interface LLMEvaluationRequest {
  llm_answers: LLMAnswer[];
  evaluation_config?: Record<string, any>;
}

export interface LLMEvaluationResponse {
  evaluation_id: string;
  status: string;
  created_answers: Array<{
    id: number;
    llm_id: number;
    std_question_id: number;
    answer: string;
    answered_at: string;
    is_valid: boolean;
  }>;
  evaluation_results?: Record<string, any>;
}

export interface EvaluationResult {
  id: number;
  score: number;
  evaluator_type: string;
  feedback?: string;
  evaluation_time: string;
}

export const llmEvaluationService = {
  // 获取数据集市场列表
  async getMarketplaceDatasets(params: {
    skip?: number;
    limit?: number;
    search?: string;
  } = {}): Promise<MarketplaceDataset[]> {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params.search) queryParams.append('search', params.search);
    
    return api.get(`/llm-evaluation/marketplace/datasets?${queryParams}`);
  },

  // 下载数据集
  async downloadDataset(datasetId: number): Promise<DatasetDownloadResponse> {
    return api.get(`/llm-evaluation/marketplace/datasets/${datasetId}/download`);
  },

  // 提交LLM回答进行评测
  async submitLLMAnswers(request: LLMEvaluationRequest): Promise<LLMEvaluationResponse> {
    return api.post('/llm-evaluation/submit', request);
  },

  // 获取评测状态
  async getEvaluationStatus(evaluationId: string): Promise<{
    evaluation_id: string;
    status: string;
    progress?: number;
  }> {
    return api.get(`/llm-evaluation/evaluation/${evaluationId}/status`);
  },

  // 获取我的LLM回答列表
  async getMyLLMAnswers(params: {
    skip?: number;
    limit?: number;
  } = {}): Promise<Array<{
    id: number;
    llm_id: number;
    std_question_id: number;
    answer: string;
    answered_at: string;
    is_valid: boolean;
    llm?: {
      id: number;
      name: string;
      version: string;
    };
    std_question?: {
      id: number;
      body: string;
      question_type: string;
    };
    scoring_points?: Array<{
      id: number;
      answer: string;
      point_order: number;
    }>;
  }>> {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    
    return api.get(`/llm-evaluation/answers?${queryParams}`);
  },

  // 手动评估LLM回答
  async manualEvaluateAnswers(request: {
    llm_answer_ids: number[];
    evaluation_type: string;
    evaluation_criteria?: string;
  }): Promise<EvaluationResult[]> {
    return api.post('/llm-evaluation/evaluate', request);
  },

  // 下载评测结果
  async downloadEvaluationResults(answerId: number): Promise<{
    llm_answer: {
      id: number;
      question_id: number;
      answer: string;
      answered_at: string;
    };
    evaluations: EvaluationResult[];
    average_score: number;
  }> {
    return api.get(`/llm-evaluation/results/${answerId}/download`);
  },

  // 获取支持的LLM模型列表
  async getSupportedModels(): Promise<Array<{
    id: number;
    name: string;
    version: string;
    affiliation?: string;
  }>> {
    return api.get('/llm-evaluation/models');
  },

  // 通过API调用LLM
  async callLLMAPI(request: {
    model_name: string;
    questions: Array<{
      id: number;
      body: string;
      question_type: string;
    }>;
    api_config: {
      api_key?: string;
      base_url?: string;
      temperature?: number;
      max_tokens?: number;
    };
  }): Promise<{
    success: boolean;
    answers: Array<{
      question_id: number;
      answer: string;
      cost_tokens?: number;
    }>;
    error?: string;
  }> {
    return api.post('/llm-evaluation/api-call', request);
  }
};

export default llmEvaluationService;

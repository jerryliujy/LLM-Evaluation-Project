/**
 * LLM评测相关的API服务 - 任务管理版本
 */
import { apiClient } from './api';

export interface MarketplaceDataset {
  id: number;
  name: string;
  description: string;
  version: number;
  question_count: number;
  choice_question_count: number;
  text_question_count: number;
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

export interface AvailableModel {
  id: string;
  name: string;
  display_name: string;
  description: string;
  provider: string;
  api_endpoint?: string;
  max_tokens: number;
  pricing?: Record<string, number>;
}

export interface EvaluationTask {
  id: number;
  name?: string;  // 任务名称
  task_name?: string;  // 兼容旧字段
  dataset_id: number;
  dataset?: MarketplaceDataset;
  model_id?: number;  // 模型ID
  model_name?: string;  // 模型名称（兼容）
  status: string;
  progress: number;
  current_question?: number;
  total_questions: number;
  successful_count?: number;
  failed_count?: number;
  completed_questions?: number;  // 新字段名
  average_score?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  
  // 配置字段
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  top_k?: number;
  enable_reasoning?: boolean;
  evaluation_prompt?: string;
}

export interface TaskProgress {
  task_id: number;
  status: string;
  progress: number;
  current_question: number;
  total_questions: number;
  successful_count: number;
  failed_count: number;
  average_score?: number;
  estimated_remaining_time?: number;
  questions_per_minute?: number;
  latest_answer?: string;
  latest_score?: number;
}

export interface EvaluationResult {
  id: number;
  score: number;
  evaluator_type: string;
  feedback?: string;
  evaluation_time: string;
}

export const llmEvaluationService = {  // 获取数据集市场列表
  async getMarketplaceDatasets(params: {
    skip?: number;
    limit?: number;
    search?: string;
    all_datasets?: boolean  // 新增：是否获取所有数据集
  } = {}): Promise<MarketplaceDataset[]> {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.all_datasets) queryParams.append('all_datasets', 'true');
    
    const response = await apiClient.get(`/llm-evaluation/marketplace/datasets?${queryParams}`);
    return response.data;
  },

  // 获取单个数据集信息
  async getMarketplaceDataset(datasetId: number): Promise<MarketplaceDataset> {
    const response = await apiClient.get(`/llm-evaluation/marketplace/datasets/${datasetId}`);
    return response.data;
  },

  // 下载数据集
  async downloadDataset(datasetId: number): Promise<DatasetDownloadResponse> {
    const response = await apiClient.get(`/llm-evaluation/marketplace/datasets/${datasetId}/download`);
    return response.data;
  },

  // 获取可用模型列表
  async getAvailableModels(): Promise<AvailableModel[]> {
    const response = await apiClient.get('/llm-evaluation/models');
    return response.data;
  },  
  
  // 创建评测任务
  async createEvaluationTask(taskData: {
    task_name: string;
    dataset_id: number;
    model_config: {
      model_id: number;
      api_key: string;
      system_prompt?: string;
      temperature?: number;
      max_tokens?: number;
      top_k?: number;
      enable_reasoning?: boolean;
    };
    evaluation_config?: Record<string, any>;
    is_auto_score?: boolean;
    question_limit?: number;
  }): Promise<EvaluationTask> {
    console.log('LLM Evaluation Service - sending task data:', JSON.stringify(taskData, null, 2));
    const response = await apiClient.post('/llm-evaluation/tasks', taskData);
    return response.data;
  },

  // 创建新任务
  async createTask(taskData: {
    task_name: string;
    dataset_id: number;
    model_config: any;
  }): Promise<EvaluationTask> {
    const response = await apiClient.post('/llm-evaluation/tasks', taskData);
    return response.data;
  },

  // 获取我的评测任务列表
  async getMyEvaluationTasks(params: {
    skip?: number;
    limit?: number;
    status_filter?: string;
  } = {}): Promise<EvaluationTask[]> {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params.status_filter) queryParams.append('status_filter', params.status_filter);
    
    const response = await apiClient.get(`/llm-evaluation/tasks?${queryParams}`);
    return response.data;
  },

  // 获取评测任务详情
  async getEvaluationTask(taskId: number): Promise<EvaluationTask> {
    const response = await apiClient.get(`/llm-evaluation/tasks/${taskId}`);
    return response.data;
  },

  // 获取任务进度
  async getTaskProgress(taskId: number): Promise<TaskProgress> {
    const response = await apiClient.get(`/llm-evaluation/tasks/${taskId}/progress`);
    return response.data;
  },

  // 取消评测任务
  async cancelEvaluationTask(taskId: number): Promise<{ message: string }> {
    const response = await apiClient.post(`/llm-evaluation/tasks/${taskId}/cancel`);
    return response.data;
  },

  // 获取单个数据集详情
  async getDatasetInfo(datasetId: number): Promise<MarketplaceDataset> {
    const response = await apiClient.get(`/llm-evaluation/marketplace/datasets/${datasetId}`);
    return response.data;
  },

  // 获取任务详情
  async getTaskDetail(taskId: number): Promise<EvaluationTask> {
    const response = await apiClient.get(`/llm-evaluation/tasks/${taskId}`);
    return response.data;
  },

  // 获取任务结果
  async getTaskResults(taskId: number): Promise<any> {
    const response = await apiClient.get(`/llm-evaluation/tasks/${taskId}/results`);
    return response.data;
  },

  // 获取任务详细结果
  async getTaskDetailedResults(taskId: number): Promise<any> {
    const response = await apiClient.get(`/llm-evaluation/tasks/${taskId}/detailed-results`);
    return response.data;
  },

  // 更新任务状态
  async updateTaskStatus(taskId: number, statusUpdate: { status: string; [key: string]: any }): Promise<EvaluationTask> {
    const response = await apiClient.put(`/llm-evaluation/tasks/${taskId}/status`, statusUpdate);
    return response.data;
  },

  // 启动评测阶段
  async startTaskEvaluation(taskId: number, evaluationConfig: {
    evaluation_prompt: string;
  }): Promise<any> {
    const response = await apiClient.post(`/llm-evaluation/tasks/${taskId}/start-evaluation`, evaluationConfig);
    return response.data;
  },

  // 下载任务结果
  async downloadTaskResults(taskId: number, options: {
    format?: string;
    include_raw_responses?: boolean;
    include_prompts?: boolean;
  } = {}): Promise<any> {
    const response = await apiClient.post(`/llm-evaluation/tasks/${taskId}/download`, {
      task_id: taskId,
      ...options
    });
    return response.data;
  },

  // Prompt模板相关
  async getPromptTemplates(params: {
    template_type?: 'system' | 'evaluation';
  } = {}): Promise<any[]> {
    const queryParams = new URLSearchParams();
    if (params.template_type) queryParams.append('template_type', params.template_type);
    
    const response = await apiClient.get(`/llm-evaluation/prompt-templates?${queryParams}`);
    return response.data;
  },

  async getPromptTemplate(templateKey: string): Promise<any> {
    const response = await apiClient.get(`/llm-evaluation/prompt-templates/${templateKey}`);
    return response.data;
  }
};

export default llmEvaluationService;

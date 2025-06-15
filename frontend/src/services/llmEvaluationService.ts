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
  default_temperature?: number;
  top_k?: number;
  enable_reasoning?: boolean;  // 新增：是否支持推理模式
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
  completed_questions: number;  // 新字段，与后端保持一致
  failed_questions: number;     // 新字段，与后端保持一致
  average_score?: number;
  estimated_remaining_time?: number;
  questions_per_minute?: number;
  latest_score?: number;
  latest_content?: string;      // 新字段：最新内容（答案或评测结果）
  latest_content_type?: string; // 新字段：内容类型（"answer" 或 "evaluation"）
}

export interface EvaluationResult {
  id: number;
  score: number;
  evaluator_type: string;
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
    }, {
      responseType: 'blob' 
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
  },  // 创建evaluation记录
  async createEvaluation(evaluation: {
    answer_id: number;
    score: number;
    reasoning: string;
    evaluator_type: 'user' | 'llm';
  }): Promise<any> {
    const response = await apiClient.post('/llm-evaluation/evaluations', evaluation);
    return response.data;
  },
  
  // 获取任务的答案列表用于手动评测
  async getTaskAnswersForManualEvaluation(taskId: number): Promise<any[]> {
    const response = await apiClient.get(`/llm-evaluation/tasks/${taskId}/answers`);
    return response.data;
  },

  // 提交手动评测
  async submitManualEvaluation(answerId: number, evaluation: {
    score: number;
    reasoning: string;
  }): Promise<any> {
    const response = await apiClient.post(`/llm-evaluation/answers/${answerId}/manual-evaluate`, evaluation);
    return response.data;
  },

  // 批量导入手动评测结果
  async importManualEvaluations(taskId: number, evaluations: Array<{
    answer_id: number;
    score: number;
    reasoning?: string;
  }>): Promise<any> {
    const response = await apiClient.post(`/llm-evaluation/tasks/${taskId}/import-evaluations`, {
      evaluations
    });
    return response.data;
  },

  // 下载答案数据
  async downloadAnswersOnly(taskId: number): Promise<Blob> {
    const response = await apiClient.get(`/llm-evaluation/tasks/${taskId}/download/answers`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // 自动评测答案
  async autoEvaluateAnswer(answerId: number, options: { use_llm: boolean }): Promise<any> {
    const response = await apiClient.post(`/llm-evaluation/answers/${answerId}/auto-evaluate`, options);
    return response.data;
  },  
  
  // 获取数据集的问题列表
  async getDatasetQuestions(datasetId: number): Promise<any> {
    const response = await apiClient.get(`/llm-evaluation/datasets/${datasetId}/questions`);
    return response.data;
  },

  // 创建手动评测任务
  async createManualEvaluationTask(taskData: {
    name: string;
    description?: string;
    dataset_id: number;
    model_id: number;
    entries: Array<{
      question_id: number;
      answer: string;
      score: number;
      reasoning?: string;
    }>;
    system_prompt?: string;
    choice_system_prompt?: string;
    text_system_prompt?: string;
    choice_evaluation_prompt?: string;
    text_evaluation_prompt?: string;
    evaluation_prompt?: string;
    temperature?: number;
    max_tokens?: number;
    top_k?: number;
    enable_reasoning?: boolean;
  }): Promise<any> {
    const response = await apiClient.post('/llm-evaluation/tasks/manual', taskData);
    return response.data;
  },
};

export default llmEvaluationService;

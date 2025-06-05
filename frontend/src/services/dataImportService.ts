import { apiClient } from './api'
import { API_BASE_URL } from "./apiConstants";

const DATA_IMPORT_ENDPOINT = `${API_BASE_URL}/data-import`;

export interface Dataset {
  id: number;
  name: string;
  description: string;
  is_public?: boolean;
  create_time: string;
}

export interface DataImportResult {
  message: string;
  imported_questions: number;
  imported_answers: number;
  imported_expert_answers?: number;
}

export type DataType = 'raw-qa' | 'expert-answers' | 'std-qa';

export const dataImportService = {
  // 创建数据集 (调整为调用 /api/datasets/ endpoint)
  async createDataset(
    name: string,
    description: string,
    isPublic = true
  ): Promise<{ id: number; name: string; description: string }> { // Adjusted return type to match common DatasetResponse
    const response = await apiClient.post('/datasets/', { // Changed endpoint
      name,
      description,
      is_public: isPublic 
    });
    return response.data;
  },

  // 获取数据集列表
  async getDatasets(skip = 0, limit = 100, public_only = true): Promise<Dataset[]> { // Added params for pagination and filtering
    const response = await apiClient.get('/datasets/', { 
      params: { skip, limit, public_only }
    });
    return response.data;
  },

  // 上传原始Q&A数据到用户的原始问题池
  async uploadRawQAToPool(
    data: any[]
  ): Promise<DataImportResult> {
    const response = await apiClient.post('/data-import/raw-qa', { data });
    return response.data;
  },

  // 上传专家回答数据到指定数据集
  async uploadExpertAnswers(
    datasetId: number,
    data: any[]
  ): Promise<DataImportResult> {
    const response = await apiClient.post(`/data-import/expert-answers/${datasetId}`, { data });
    return response.data;
  },

  // 上传标准Q&A数据到指定数据集（暂未实现）
  async uploadStdQAData(
    datasetId: number, 
    data: any[]
  ): Promise<DataImportResult> {
    const response = await apiClient.post(`/data-import/std-qa/${datasetId}`, { data });
    return response.data;
  },

  // 验证数据格式
  validateDataFormat(dataType: DataType, data: any[]): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];
    
    if (!Array.isArray(data) || data.length === 0) {
      errors.push("数据必须是非空数组");
      return { isValid: false, errors };
    }

    switch (dataType) {
      case 'raw-qa':
        // 验证原始Q&A数据格式
        data.forEach((item, index) => {
          if (!item.title) {
            errors.push(`第${index + 1}项缺少标题(title)字段`);
          }
          if (!item.answers || !Array.isArray(item.answers)) {
            errors.push(`第${index + 1}项缺少或格式错误的回答(answers)字段`);
          }
        });
        break;
        
      case 'expert-answers':
        // 验证专家回答数据格式
        data.forEach((item, index) => {
          if (!item.question_id && !item.title) {
            errors.push(`第${index + 1}项缺少问题ID(question_id)或标题(title)字段`);
          }
          if (!item.expert_answers || !Array.isArray(item.expert_answers)) {
            errors.push(`第${index + 1}项缺少或格式错误的专家回答(expert_answers)字段`);
          }
        });
        break;
        
      case 'std-qa':
        // 验证标准Q&A数据格式
        data.forEach((item, index) => {
          if (!item.question) {
            errors.push(`第${index + 1}项缺少问题(question)字段`);
          }
          if (!item.answer) {
            errors.push(`第${index + 1}项缺少回答(answer)字段`);
          }
        });
        break;
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // 预览数据（获取前几项进行展示）
  previewData(data: any[], maxItems = 3): any[] {
    return data.slice(0, maxItems);
  },

};

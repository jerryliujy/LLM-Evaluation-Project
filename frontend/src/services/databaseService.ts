import { apiClient } from './api'
import { API_BASE_URL } from "./apiConstants";

interface TableDataResult {
  data: any[];
  total: number;
  deletedCount: number;
}

interface OverviewStatistics {
  raw_questions_count: number;
  std_questions_count: number;
  total_raw_answers: number;
  total_expert_answers: number;
  total_std_answers: number;
  avg_raw_answers_per_question: number;
  avg_expert_answers_per_question: number;
}

export const databaseService = {
  // 获取表格数据
  async getTableData(
    tableName: string,
    skip = 0,
    limit = 20,
    includeDeleted = false,
    datasetId?: number,
    deletedOnly = false,
    searchQuery?: string,
    tagFilter?: string,
    questionTypeFilter?: string,
    stdQuestionFilter?: string,
    scoringPointFilter?: string,
    scoringPointsFilter?: string,
    version?: number
  ): Promise<TableDataResult> {
    const endpoint = this.getTableEndpoint(tableName);
    const params: any = {
      skip: skip.toString(),
      limit: limit.toString(),
    };

    if (includeDeleted) {
      params.include_deleted = "true";
    }

    if (deletedOnly) {
      params.deleted_only = "true";
    }

    if (datasetId) {
      params.dataset_id = datasetId.toString();
    }
    
    if (version !== undefined) {
      params.version = version.toString();
    }

    // 标准问题的搜索参数
    if (tableName === 'std_questions') {
      if (searchQuery) params.search_query = searchQuery;
      if (tagFilter) params.tag_filter = tagFilter;
      if (questionTypeFilter) params.question_type_filter = questionTypeFilter;
      if (scoringPointsFilter) params.scoring_points_filter = scoringPointsFilter;
    }

    // 标准答案的搜索参数
    if (tableName === 'std_answers') {
      if (searchQuery) params.search_query = searchQuery;
      if (stdQuestionFilter) params.std_question_filter = stdQuestionFilter;
      if (scoringPointFilter) params.scoring_point_filter = scoringPointFilter;
      if (scoringPointsFilter) params.scoring_points_filter = scoringPointsFilter;
    }

    try {
      const response = await apiClient.get(endpoint, { params });
      const result = response.data;
      
      return {
        data: result.data,
        total: result.total,
        deletedCount: result.data.filter((item: any) => item.is_deleted).length,
      };
    } catch (error) {
      throw new Error(`Failed to fetch ${tableName} data`);
    }
  },
  // 删除单个项目
  async deleteItem(tableName: string, id: number): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    try {
      await apiClient.delete(`${endpoint}/${id}/`);
    } catch (error) {
      throw new Error(`Failed to delete ${tableName} item`);
    }
  },

  // 恢复单个项目
  async restoreItem(tableName: string, id: number): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    try {
      await apiClient.post(`${endpoint}/${id}/restore/`);
    } catch (error) {
      throw new Error(`Failed to restore ${tableName} item`);
    }
  },

  // 永久删除单个项目
  async forceDeleteItem(tableName: string, id: number): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    try {
      await apiClient.delete(`${endpoint}/${id}/force-delete/`);
    } catch (error) {
      throw new Error(`Failed to force delete ${tableName} item`);
    }
  },
  // 批量删除
  async bulkDelete(tableName: string, ids: number[]): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    try {
      await apiClient.post(`${endpoint}/delete-multiple/`, ids);
    } catch (error) {
      throw new Error(`Failed to bulk delete ${tableName} items`);
    }
  },

  // 批量恢复
  async bulkRestore(tableName: string, ids: number[]): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    try {
      await apiClient.post(`${endpoint}/restore-multiple/`, ids);
    } catch (error) {
      throw new Error(`Failed to bulk restore ${tableName} items`);
    }
  },
  // 更新项目
  async updateItem(tableName: string, id: number, data: any): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    try {
      await apiClient.put(`${endpoint}/${id}`, data);
    } catch (error) {
      throw new Error(`Failed to update ${tableName} item`);
    }
  },

  // 创建新项目
  async createItem(tableName: string, data: any): Promise<any> {
    const endpoint = this.getTableEndpoint(tableName);
    try {
      const response = await apiClient.post(endpoint, data);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create ${tableName} item`);
    }
  },

  // 获取单个项目详情
  async getItem(tableName: string, id: number): Promise<any> {
    const endpoint = this.getTableEndpoint(tableName);
    try {
      const response = await apiClient.get(`${endpoint}/${id}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get ${tableName} item`);
    }
  },
  // 获取表格对应的API端点
  getTableEndpoint(tableName: string): string {
    const endpointMap: Record<string, string> = {
      raw_questions: `${API_BASE_URL}/raw_questions`,
      raw_answers: `${API_BASE_URL}/raw_answers`,
      expert_answers: `${API_BASE_URL}/expert_answers`,
      std_questions: `${API_BASE_URL}/std-questions`,
      std_answers: `${API_BASE_URL}/std-answers`,
      overview_raw: `${API_BASE_URL}/overview/raw-questions`,
      overview_std: `${API_BASE_URL}/overview/std-questions`,
    };

    const endpoint = endpointMap[tableName];
    if (!endpoint) {
      throw new Error(`Unknown table: ${tableName}`);
    }

    return endpoint;
  },  // 获取原始问题总览
  async getRawQuestionsOverview(
    skip = 0,
    limit = 20,
    datasetId?: number
  ): Promise<TableDataResult> {
    const params: any = {
      skip: skip.toString(),
      limit: limit.toString(),
    };

    if (datasetId) {
      params.dataset_id = datasetId.toString();
    }

    try {
      const response = await apiClient.get('/overview/raw-questions', { params });
      const data = response.data;
      return {
        data: data.data || data,
        total: data.total || data.length,
        deletedCount: 0,
      };
    } catch (error) {
      throw new Error("Failed to fetch raw questions overview");
    }
  },
  // 获取标准问题总览
  async getStdQuestionsOverview(
    skip = 0,
    limit = 20,
    datasetId?: number,
    searchQuery?: string,
    tagFilter?: string,
    questionTypeFilter?: string,
    version?: number
  ): Promise<TableDataResult> {
    const params: any = {
      skip: skip.toString(),
      limit: limit.toString(),
    };

    if (datasetId) {
      params.dataset_id = datasetId.toString();
    }

    if (version !== undefined) {
      params.version = version.toString();
    }

    if (searchQuery) {
      params.search_query = searchQuery;
    }

    if (tagFilter) {
      params.tag_filter = tagFilter;
    }

    if (questionTypeFilter) {
      params.question_type_filter = questionTypeFilter;
    }

    try {
      const response = await apiClient.get('/overview/std-questions', { params });
      const data = response.data;
      return {
        data: data.data || data,
        total: data.total || data.length,
        deletedCount: 0,
      };
    } catch (error) {
      throw new Error("Failed to fetch std questions overview");
    }
  },

  // 获取总览统计信息
  async getOverviewStatistics(): Promise<OverviewStatistics> {
    try {
      const response = await apiClient.get('/overview/statistics');
      return response.data;
    } catch (error) {
      throw new Error("Failed to fetch overview statistics");
    }
  },

  // 获取数据库统计信息
  async getDatabaseStats(): Promise<{
    raw_questions: number;
    raw_answers: number;
    expert_answers: number;
    std_questions: number;
    std_answers: number;
  }> {
    try {
      // 并行获取各个表的统计信息
      const [rawQuestions, rawAnswers, expertAnswers, stdQuestions, stdAnswers] = await Promise.all([
        this.getTableData("raw_questions", 0, 1),
        this.getTableData("raw_answers", 0, 1),
        this.getTableData("expert_answers", 0, 1),
        this.getTableData("std_questions", 0, 1),
        this.getTableData("std_answers", 0, 1),
      ]);

      return {
        raw_questions: rawQuestions.total,
        raw_answers: rawAnswers.total,
        expert_answers: expertAnswers.total,
        std_questions: stdQuestions.total,
        std_answers: stdAnswers.total,
      };
    } catch (error) {
      console.error("Failed to get database stats:", error);
      return {
        raw_questions: 0,
        raw_answers: 0,
        expert_answers: 0,
        std_questions: 0,
        std_answers: 0,
      };
    }
  },
  // 搜索功能
  async searchItems(
    tableName: string,
    query: string,
    skip = 0,
    limit = 20
  ): Promise<TableDataResult> {
    const endpoint = this.getTableEndpoint(tableName);
    const params: any = {
      q: query,
      skip: skip.toString(),
      limit: limit.toString(),
    };

    try {
      const response = await apiClient.get(`${endpoint}/search`, { params });
      const data = response.data;
      return {
        data: data.results || data,
        total: data.total || data.length,
        deletedCount: 0,
      };
    } catch (error) {
      throw new Error(`Failed to search ${tableName}`);
    }
  },
};

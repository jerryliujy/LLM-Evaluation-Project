import { API_BASE_URL } from "./apiConstants";

interface TableDataResult {
  data: any[];
  total: number;
  deletedCount: number;
}

export const databaseService = {
  // 获取表格数据
  async getTableData(
    tableName: string,
    skip = 0,
    limit = 20,
    includeDeleted = false
  ): Promise<TableDataResult> {
    const endpoint = this.getTableEndpoint(tableName);
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });

    if (includeDeleted) {
      params.append("include_deleted", "true");
    }

    const response = await fetch(`${endpoint}?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${tableName} data`);
    }

    const data = await response.json();
    
    // 计算统计信息
    const total = data.length; // 简化处理，实际应该从后端获取总数
    const deletedCount = data.filter((item: any) => item.is_deleted).length;

    return {
      data,
      total,
      deletedCount,
    };
  },

  // 删除单个项目
  async deleteItem(tableName: string, id: number): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    const response = await fetch(`${endpoint}/${id}/`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`Failed to delete ${tableName} item`);
    }
  },

  // 恢复单个项目
  async restoreItem(tableName: string, id: number): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    const response = await fetch(`${endpoint}/${id}/restore/`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`Failed to restore ${tableName} item`);
    }
  },

  // 批量删除
  async bulkDelete(tableName: string, ids: number[]): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    const response = await fetch(`${endpoint}/delete-multiple/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(ids),
    });

    if (!response.ok) {
      throw new Error(`Failed to bulk delete ${tableName} items`);
    }
  },

  // 批量恢复
  async bulkRestore(tableName: string, ids: number[]): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    const response = await fetch(`${endpoint}/restore-multiple/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(ids),
    });

    if (!response.ok) {
      throw new Error(`Failed to bulk restore ${tableName} items`);
    }
  },

  // 更新项目
  async updateItem(tableName: string, id: number, data: any): Promise<void> {
    const endpoint = this.getTableEndpoint(tableName);
    const response = await fetch(`${endpoint}/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to update ${tableName} item`);
    }
  },

  // 创建新项目
  async createItem(tableName: string, data: any): Promise<any> {
    const endpoint = this.getTableEndpoint(tableName);
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to create ${tableName} item`);
    }

    return response.json();
  },

  // 获取单个项目详情
  async getItem(tableName: string, id: number): Promise<any> {
    const endpoint = this.getTableEndpoint(tableName);
    const response = await fetch(`${endpoint}/${id}`);

    if (!response.ok) {
      throw new Error(`Failed to get ${tableName} item`);
    }

    return response.json();
  },

  // 获取表格对应的API端点
  getTableEndpoint(tableName: string): string {
    const endpointMap: Record<string, string> = {
      raw_questions: `${API_BASE_URL}/raw_questions`,
      raw_answers: `${API_BASE_URL}/raw_answers`,
      expert_answers: `${API_BASE_URL}/expert_answers`,
      std_questions: `${API_BASE_URL}/std-questions`,
      std_answers: `${API_BASE_URL}/std-answers`,
    };

    const endpoint = endpointMap[tableName];
    if (!endpoint) {
      throw new Error(`Unknown table: ${tableName}`);
    }

    return endpoint;
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
    const params = new URLSearchParams({
      q: query,
      skip: skip.toString(),
      limit: limit.toString(),
    });

    const response = await fetch(`${endpoint}/search?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to search ${tableName}`);
    }

    const data = await response.json();
    return {
      data: data.results || data,
      total: data.total || data.length,
      deletedCount: 0,
    };
  },
};

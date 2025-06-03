import type { ExpertCreate, Expert, ExpertLogin } from "@/types/expert";

const API_BASE_URL = "http://localhost:8000/api";

export const expertService = {
  // 创建专家
  async createExpert(expertData: ExpertCreate): Promise<Expert> {
    const response = await fetch(`${API_BASE_URL}/experts/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(expertData),
    });

    if (!response.ok) {
      throw new Error("创建专家失败");
    }

    return response.json();
  },

  // 专家登录
  async login(
    loginData: ExpertLogin
  ): Promise<{ expert: Expert; success: boolean }> {
    const response = await fetch(`${API_BASE_URL}/experts/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(loginData),
    });

    if (!response.ok) {
      throw new Error("登录失败");
    }

    const result = await response.json();
    return {
      expert: result.expert,
      success: result.success,
    };
  },

  // 获取专家信息
  async getExpert(expertId: number): Promise<Expert> {
    const response = await fetch(`${API_BASE_URL}/experts/${expertId}`);

    if (!response.ok) {
      throw new Error("获取专家信息失败");
    }

    return response.json();
  },

  // 获取所有专家
  async getAllExperts(includeDeleted = false): Promise<Expert[]> {
    const url = new URL(`${API_BASE_URL}/experts/`);
    if (includeDeleted) {
      url.searchParams.append("include_deleted", "true");
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error("获取专家列表失败");
    }

    return response.json();
  },

  // 删除专家
  async deleteExpert(expertId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/experts/${expertId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error("删除专家失败");
    }
  },

  // 恢复专家
  async restoreExpert(expertId: number): Promise<Expert> {
    const response = await fetch(
      `${API_BASE_URL}/experts/${expertId}/restore`,
      {
        method: "POST",
      }
    );

    if (!response.ok) {
      throw new Error("恢复专家失败");
    }

    return response.json();
  },
};

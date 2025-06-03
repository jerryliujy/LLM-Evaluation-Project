import axios from "axios";
import { ApiMessage } from "@/types/api";
import { API_BASE_URL } from "./apiConstants";

const DATA_IMPORT_ENDPOINT = `${API_BASE_URL}/data-import`;

export interface Dataset {
  id: number;
  description: string;
  create_time: string;
}

export interface DataImportResult {
  message: string;
  imported_questions: number;
  imported_answers: number;
  imported_expert_answers?: number;
}

export const dataImportService = {
  // 创建数据集
  async createDataset(
    description: string
  ): Promise<{ dataset_id: number; description: string }> {
    const formData = new FormData();
    formData.append("description", description);

    const response = await axios.post(
      `${DATA_IMPORT_ENDPOINT}/dataset`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  // 上传问题文件
  async uploadQuestions(file: File): Promise<DataImportResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post<DataImportResult>(
      `${DATA_IMPORT_ENDPOINT}/upload-questions`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  // 直接上传JSON数据
  async uploadData(data: any[]): Promise<DataImportResult> {
    const response = await axios.post<DataImportResult>(
      `${DATA_IMPORT_ENDPOINT}/upload-json-data`,
      { data },
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    return response.data;
  },

  // 获取数据集列表
  async getDatasets(): Promise<Dataset[]> {
    const response = await axios.get<Dataset[]>(
      `${DATA_IMPORT_ENDPOINT}/datasets`
    );
    return response.data;
  },
};

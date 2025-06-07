import { RawAnswer, ExpertAnswer, StdAnswer } from "./answers";

export interface RawQuestion {
  id: number;
  title: string;
  url?: string;
  body?: string;
  votes?: string;  // 支持 "1.1k" 格式的投票数
  views?: string;  // 支持 "1.1m" 格式的查看数
  author?: string;
  tags?: string[];
  tags_json?: string[]; // 添加 tags_json 字段用于后端兼容
  issued_at?: string | Date;
  created_at?: string | Date;
  is_deleted: boolean;
  raw_answers: RawAnswer[];
  expert_answers: ExpertAnswer[];
  // 扩展字段，用于视图模式支持
  type?: 'question' | 'raw-answer' | 'expert-answer';
  original_data?: any;
}

export interface StdQuestion {
  id: number;
  dataset_id: number;
  raw_question_id: number;
  body: string;
  created_at: string | Date;
  question_type: string;
  is_valid: boolean;
  created_by?: number;
  version: number;
  previous_version_id?: number; // Nullable for the first version
  std_answers?: StdAnswer[]; // Optional relationship to standard answers
}
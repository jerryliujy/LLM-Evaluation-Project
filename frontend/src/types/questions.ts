import { RawAnswer, ExpertAnswer, StdAnswer } from "./answers";

export interface RawQuestion {
  id: number;
  title: string;
  url?: string;
  body?: string;
  vote_count?: number;
  view_count?: number;
  author?: string;
  tags?: string[];
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
  text: string;
  create_time: string | Date;
  question_type: string;
  is_valid: boolean;
  created_by?: string;
  version: number;
  previous_version_id?: number; // Nullable for the first version
  std_answers?: StdAnswer[]; // Optional relationship to standard answers
}
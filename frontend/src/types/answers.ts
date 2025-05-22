export interface RawAnswer {
  id: number;
  question_id: number;
  content: string;
  vote_count?: number;
  author?: string;
  answered_at?: string | Date;
  is_deleted: boolean;
}

export interface ExpertAnswer {
  id: number;
  question_id: number;
  content: string;
  source: string;
  vote_count?: number;
  author?: string;
  created_at: string | Date;
  is_deleted: boolean;
}
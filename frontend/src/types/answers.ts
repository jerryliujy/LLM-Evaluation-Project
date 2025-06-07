import { StdQuestion } from './questions';

export interface RawAnswer {
  id: number;
  question_id: number;
  answer: string;
  upvotes?: string;
  answered_by?: string;
  answered_at?: string | Date;
  is_deleted: boolean;
}

export interface ExpertAnswer {
  id: number;
  question_id: number;
  answer: string;
  answered_by?: string;
  answered_at: string | Date;
  is_deleted: boolean;
}

export interface StdAnswerScoringPoint {
  id: number;
  std_answer_id: number;
  answer: string;
  score?: number;
  created_by?: number;
  create_time?: string | Date;
}

export interface StdAnswer {
  id: number;
  std_question_id: number;
  answer: string;
  is_valid: boolean;
  answered_by?: number;  
  answered_at: string | Date;
  previous_version_id?: number; // Nullable for the first version
  std_question?: StdQuestion; // Optional relationship
  previous_version?: StdAnswer; // Optional relationship to previous version
  scoring_points?: StdAnswerScoringPoint[]; // Optional relationship to scoring points
}
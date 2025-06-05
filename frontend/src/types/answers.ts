import { StdQuestion } from './questions';

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

export interface StdAnswerScoringPoint {

}

export interface StdAnswer {
  id: number;
  std_question_id: number;
  answer: string;
  is_valid: boolean;
  created_by?: string;  
  create_time: string | Date;
  version: number;
  previous_version_id?: number; // Nullable for the first version
  std_question?: StdQuestion; // Optional relationship
  previous_version?: StdAnswer; // Optional relationship to previous version
  scoring_points?: StdAnswerScoringPoint[]; // Optional relationship to scoring points
}
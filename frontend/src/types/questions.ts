import { RawAnswer, ExpertAnswer } from "./answers";

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
  is_deleted: boolean;
  raw_answers: RawAnswer[];
  expert_answers: ExpertAnswer[];
}

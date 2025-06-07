// 专家任务相关类型
export interface ExpertTask {
  id: number
  expert_id: number
  admin_id: number
  invite_code: string
  task_name?: string
  description?: string
  created_at: string
  is_active: boolean
  expert_username?: string
  admin_username?: string
}

export interface ExpertTaskCreate {
  invite_code: string
}

export interface ExpertTaskUpdate {
  task_name?: string
  description?: string
  is_active?: boolean
}

// 管理员问题池类型
export interface AdminPool {
  admin_id: number
  admin_username: string
  invite_code: string
  joined_at: string
  question_count: number
  answer_count: number
  task_id: number
  is_active: boolean
}

// 专家统计信息
export interface ExpertStats {
  total_admins: number
  total_questions: number
  total_answers: number
  pending_questions: number
}

// 邀请码信息
export interface InviteCodeInfo {
  admin_username: string
  admin_id: number
  invite_code: string
}

export interface ExpertAnswerCreate {
  question_id: number
  answer: string
}

export interface ExpertAnswerUpdate {
  answer: string
}
import { apiClient } from './api'

export interface StandardQuestion {
  id?: number
  dataset_id: number
  question_text: string
  difficulty_level?: string
  knowledge_points?: string[]
  tags?: string[]
  notes?: string
  created_by?: string
  created_at?: Date
  updated_at?: Date
  is_valid?: boolean
  question_type?: string
  version?: number
}

export interface StandardAnswer {
  id?: number
  std_question_id?: number
  answer_text: string
  answer_type?: string
  scoring_points?: ScoringPoint[]
  total_score?: number
  explanation?: string
  created_by?: string
  created_at?: Date
  updated_at?: Date
  is_valid?: boolean
  version?: number
}

export interface ScoringPoint {
  id?: number
  answer: string
  point_order?: number
  score?: number
}

export interface RelationRecord {
  id?: number
  notes?: string
  created_by?: string
  created_at?: Date
}

export interface RawQuestionRelation extends RelationRecord {
  raw_question_id: number
}

export interface RawAnswerRelation extends RelationRecord {
  raw_answer_id: number
}

export interface ExpertAnswerRelation extends RelationRecord {
  expert_answer_id: number
}

export interface StandardQAWithRelations {
  std_question: StandardQuestion
  std_answer: StandardAnswer
  raw_question_relations?: RawQuestionRelation[]
  raw_answer_relations?: RawAnswerRelation[]
  expert_answer_relations?: ExpertAnswerRelation[]
}

export interface CreateStandardQARequest {
  // 标准问题字段
  dataset_id: number
  question_text: string
  difficulty_level?: string
  knowledge_points?: string[]
  tags?: string[]
  notes?: string
  created_by?: number
  
  // 标准答案字段
  answer_text: string
  answer_type?: string
  scoring_points?: ScoringPoint[]
  total_score?: number
  explanation?: string
  answered_by?: number
  
  // 关系记录
  raw_question_relations?: RawQuestionRelation[]
  raw_answer_relations?: RawAnswerRelation[]
  expert_answer_relations?: ExpertAnswerRelation[]
}

class StandardQAService {
  // 使用新的多对多关系架构创建标准问答对
  async createStandardQAWithRelations(data: CreateStandardQARequest): Promise<StandardQAWithRelations> {
    try {
      const response = await apiClient.post('/std-qa-management/create-with-relations', data)
      return response.data
    } catch (error) {
      console.error('创建标准问答失败:', error)
      throw error
    }
  }

  // 获取标准问答及其关系记录
  async getStandardQAWithRelations(questionId: number): Promise<StandardQAWithRelations> {
    try {
      const response = await apiClient.get(`/std-qa-management/${questionId}/with-relations`)
      return response.data
    } catch (error) {
      console.error('获取标准问答及关系失败:', error)
      throw error
    }
  }

  // 删除标准问答及其所有关系记录
  async deleteStandardQAWithRelations(questionId: number): Promise<void> {
    try {
      await apiClient.delete(`/std-qa-management/${questionId}/with-relations`)
    } catch (error) {
      console.error('删除标准问答及关系失败:', error)
      throw error
    }
  }

  // 获取所有标准问题（分页）
  async getStandardQuestions(params?: {
    skip?: number
    limit?: number
    include_deleted?: boolean
    deleted_only?: boolean
  }): Promise<{items: StandardQuestion[], total: number, page: number, per_page: number, pages: number}> {
    try {
      const response = await apiClient.get('/std-questions/', { params })
      return response.data
    } catch (error) {
      console.error('获取标准问题失败:', error)
      throw error
    }
  }

  // 获取特定问题的标准回答
  async getStandardAnswersByQuestionId(questionId: number): Promise<StandardAnswer[]> {
    try {
      const response = await apiClient.get(`/std-answers/by-question/${questionId}`)
      return response.data
    } catch (error) {
      console.error('获取标准回答失败:', error)
      throw error
    }
  }

  // 获取所有标准答案（分页）
  async getStandardAnswers(params?: {
    skip?: number
    limit?: number
    include_deleted?: boolean
    deleted_only?: boolean
  }): Promise<{items: StandardAnswer[], total: number, page: number, per_page: number, pages: number}> {
    try {
      const response = await apiClient.get('/std-answers/', { params })
      return response.data
    } catch (error) {
      console.error('获取标准答案失败:', error)
      throw error
    }
  }
  // 获取标准问答对（包含问题和回答）- 兼容性方法
  async getStandardQAPairs(params?: {
    skip?: number
    limit?: number
    include_deleted?: boolean
  }): Promise<StandardQAWithRelations[]> {
    try {
      const questionsResponse = await this.getStandardQuestions(params)
      const qaPairs: StandardQAWithRelations[] = []

      for (const question of questionsResponse.items) {
        try {
          const qaWithRelations = await this.getStandardQAWithRelations(question.id!)
          qaPairs.push(qaWithRelations)
        } catch (error) {
          // 如果获取关系失败，可能是因为没有对应的答案，跳过这个问题
          console.warn(`跳过问题 ${question.id}:`, error)
        }
      }

      return qaPairs
    } catch (error) {
      console.error('获取标准问答对失败:', error)
      throw error
    }
  }

  // 更新标准问题
  async updateStandardQuestion(id: number, data: Partial<StandardQuestion>): Promise<StandardQuestion> {
    try {
      const response = await apiClient.put(`/std-questions/${id}`, data)
      return response.data
    } catch (error) {
      console.error('更新标准问题失败:', error)
      throw error
    }
  }

  // 更新标准回答
  async updateStandardAnswer(id: number, data: Partial<StandardAnswer>): Promise<StandardAnswer> {
    try {
      const response = await apiClient.put(`/std-answers/${id}`, data)
      return response.data
    } catch (error) {
      console.error('更新标准回答失败:', error)
      throw error
    }
  }

  // 删除标准问题（软删除）
  async deleteStandardQuestion(id: number): Promise<void> {
    try {
      await apiClient.delete(`/std-questions/${id}/`)
    } catch (error) {
      console.error('删除标准问题失败:', error)
      throw error
    }
  }

  // 恢复标准问题
  async restoreStandardQuestion(id: number): Promise<StandardQuestion> {
    try {
      const response = await apiClient.post(`/std-questions/${id}/restore/`)
      return response.data
    } catch (error) {
      console.error('恢复标准问题失败:', error)
      throw error
    }
  }

  // 删除标准回答（软删除）
  async deleteStandardAnswer(id: number): Promise<void> {
    try {
      await apiClient.delete(`/std-answers/${id}/`)
    } catch (error) {
      console.error('删除标准回答失败:', error)
      throw error
    }
  }

  // 恢复标准回答
  async restoreStandardAnswer(id: number): Promise<StandardAnswer> {
    try {
      const response = await apiClient.post(`/std-answers/${id}/restore/`)
      return response.data
    } catch (error) {
      console.error('恢复标准回答失败:', error)
      throw error
    }
  }

  // 关系记录管理方法
  // 创建标准问题-原始问题关系记录
  async createStdQuestionRawQuestionRelation(data: {
    std_question_id: number
    raw_question_id: number
    notes?: string
    created_by?: string
  }): Promise<RelationRecord> {
    try {
      const response = await apiClient.post('/relationship-records/std-question-raw-question', data)
      return response.data
    } catch (error) {
      console.error('创建标准问题-原始问题关系失败:', error)
      throw error
    }
  }
  // 创建标准答案-原始答案关系记录
  async createStdAnswerRawAnswerRelation(data: {
    std_answer_id: number
    raw_answer_id: number
    notes?: string
    created_by?: string
  }): Promise<RelationRecord> {
    try {
      const response = await apiClient.post('/relationship-records/std-answer-raw-answer', data)
      return response.data
    } catch (error) {
      console.error('创建标准答案-原始答案关系失败:', error)
      throw error
    }
  }
  // 创建标准答案-专家答案关系记录
  async createStdAnswerExpertAnswerRelation(data: {
    std_answer_id: number
    expert_answer_id: number
    notes?: string
    created_by?: string
  }): Promise<RelationRecord> {
    try {
      const response = await apiClient.post('/relationship-records/std-answer-expert-answer', data)
      return response.data
    } catch (error) {
      console.error('创建标准答案-专家答案关系失败:', error)
      throw error
    }
  }

  // 删除关系记录
  async deleteRelationRecord(recordType: 'std-question-raw-question' | 'std-answer-raw-answer' | 'std-answer-expert-answer', recordId: number): Promise<void> {
    try {
      await apiClient.delete(`/relationship-records/${recordType}/${recordId}`)
    } catch (error) {
      console.error('删除关系记录失败:', error)
      throw error
    }
  }

  // 搜索标准问答
  async searchStandardQA(query: string, filters?: {
    dataset_id?: number
    difficulty_level?: string
    include_deleted?: boolean
  }): Promise<StandardQAWithRelations[]> {
    try {
      const params = {
        search: query,
        ...filters
      }
      return await this.getStandardQAPairs(params)
    } catch (error) {
      console.error('搜索标准问答失败:', error)
      throw error
    }
  }
}

export const standardQAService = new StandardQAService()

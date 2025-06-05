import { apiClient } from './api'

export interface StandardQuestion {
  id?: number
  title: string
  body?: string
  difficulty?: 'beginner' | 'intermediate' | 'advanced'
  category?: string
  tags?: string[]
  created_at?: Date
}

export interface StandardAnswer {
  id?: number
  std_question_id?: number
  content: string
  source?: string
  confidence?: 'high' | 'medium' | 'low'
  tags?: string[]
  created_at?: Date
  referenced_raw_answer_ids?: number[]
  referenced_expert_answer_ids?: number[]
}

export interface StandardQAPair {
  question: StandardQuestion
  answer: StandardAnswer
  references?: {
    question_ids?: number[]
    raw_answer_ids?: number[]
    expert_answer_ids?: number[]
  }
}

class StandardQAService {
  // 创建标准问答对
  async createStandardQA(data: StandardQAPair): Promise<any> {
    try {
      // 首先创建标准问题
      const questionResponse = await apiClient.post('/std-questions/', {
        title: data.question.title,
        body: data.question.body || '',
        difficulty: data.question.difficulty || 'intermediate',
        category: data.question.category || '',
        tags: data.question.tags || []
      })

      const questionId = questionResponse.data.id

      // 然后创建标准回答，关联到问题
      const answerResponse = await apiClient.post('/std-answers/', {
        std_question_id: questionId,
        content: data.answer.content,
        source: data.answer.source || '',
        confidence: data.answer.confidence || 'medium',
        tags: data.answer.tags || [],
        referenced_raw_answer_ids: data.references?.raw_answer_ids || [],
        referenced_expert_answer_ids: data.references?.expert_answer_ids || []
      })

      return {
        question: questionResponse.data,
        answer: answerResponse.data
      }
    } catch (error) {
      console.error('创建标准问答失败:', error)
      throw error
    }
  }

  // 获取所有标准问题
  async getStandardQuestions(params?: {
    skip?: number
    limit?: number
    category?: string
    difficulty?: string
    search?: string
  }): Promise<StandardQuestion[]> {
    try {
      const response = await apiClient.get('/std-questions/', { params })
      return response.data
    } catch (error) {
      console.error('获取标准问题失败:', error)
      throw error
    }
  }

  // 获取特定问题的标准回答
  async getStandardAnswers(questionId: number): Promise<StandardAnswer[]> {
    try {
      const response = await apiClient.get(`/std-answers/question/${questionId}`)
      return response.data
    } catch (error) {
      console.error('获取标准回答失败:', error)
      throw error
    }
  }

  // 获取标准问答对（包含问题和回答）
  async getStandardQAPairs(params?: {
    skip?: number
    limit?: number
    category?: string
    difficulty?: string
    search?: string
  }): Promise<StandardQAPair[]> {
    try {
      const questions = await this.getStandardQuestions(params)
      const qaPairs: StandardQAPair[] = []

      for (const question of questions) {
        const answers = await this.getStandardAnswers(question.id!)
        if (answers.length > 0) {
          qaPairs.push({
            question,
            answer: answers[0] // 假设每个问题只有一个标准回答
          })
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

  // 删除标准问题（会同时删除相关回答）
  async deleteStandardQuestion(id: number): Promise<void> {
    try {
      await apiClient.delete(`/std-questions/${id}`)
    } catch (error) {
      console.error('删除标准问题失败:', error)
      throw error
    }
  }

  // 删除标准回答
  async deleteStandardAnswer(id: number): Promise<void> {
    try {
      await apiClient.delete(`/std-answers/${id}`)
    } catch (error) {
      console.error('删除标准回答失败:', error)
      throw error
    }
  }

  // 搜索标准问答
  async searchStandardQA(query: string, filters?: {
    category?: string
    difficulty?: string
    confidence?: string
  }): Promise<StandardQAPair[]> {
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

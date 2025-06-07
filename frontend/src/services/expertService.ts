import { apiClient } from './api'
import type { RawQuestion } from '@/types'
import type { ExpertTask, ExpertTaskCreate, AdminPool, ExpertStats, InviteCodeInfo } from '@/types/expert'
import type { ExpertAnswer } from '@/types/answers'

export interface InviteCodeRequest {
  invite_code: string
}

class ExpertService {
  // 通过邀请码加入任务
  async joinTask(request: InviteCodeRequest): Promise<ExpertTask> {
    try {
      const response = await apiClient.post('/expert/tasks', request)
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '加入任务失败')
    }
  }

  // 获取我的任务列表（用于构建管理员问题池）
  async getTasks(): Promise<ExpertTask[]> {
    try {
      const response = await apiClient.get('/expert/tasks')
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取任务失败')
    }
  }

  // 转换任务为管理员问题池格式
  async getAdminPools(): Promise<AdminPool[]> {
    try {
      const tasks = await this.getTasks()
      const pools: AdminPool[] = []

      for (const task of tasks) {
        if (task.is_active) {
          // 获取该管理员的问题数量
          const questions = await this.getTaskQuestions(task.id)
          // 获取我在该管理员问题池中的回答数量
          const myAnswers = await this.getMyAnswers()
          const adminAnswerCount = myAnswers.filter(answer => 
            questions.some(q => q.id === answer.question_id)
          ).length

          pools.push({
            admin_id: task.admin_id,
            admin_username: task.admin_username || `管理员 ${task.admin_id}`,
            invite_code: task.invite_code,
            joined_at: task.created_at,
            question_count: questions.length,
            answer_count: adminAnswerCount,
            task_id: task.id,
            is_active: task.is_active
          })
        }
      }

      return pools
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取管理员问题池失败')
    }
  }

  // 获取任务对应的问题
  async getTaskQuestions(taskId: number): Promise<RawQuestion[]> {
    try {
      const response = await apiClient.get(`/expert/tasks/${taskId}/questions`)
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取问题失败')
    }
  }
  // 创建专家回答
  async createAnswer(data: { question_id: number; answer: string }): Promise<ExpertAnswer> {
    try {
      const response = await apiClient.post('/expert/answers', data)
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '创建回答失败')
    }
  }

  // 获取我的所有回答
  async getMyAnswers(skip = 0, limit = 100): Promise<ExpertAnswer[]> {
    try {
      const response = await apiClient.get('/expert/answers', {
        params: { skip, limit }
      })
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取回答失败')
    }
  }

  // 获取单个回答
  async getAnswer(answerId: number): Promise<ExpertAnswer> {
    try {
      const response = await apiClient.get(`/expert_answers/${answerId}`)
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取回答失败')
    }
  }
  // 更新回答
  async updateAnswer(answerId: number, data: { answer: string }): Promise<ExpertAnswer> {
    try {
      const response = await apiClient.put(`/expert_answers/${answerId}`, data)
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '更新回答失败')
    }
  }

  // 删除回答
  async deleteAnswer(answerId: number): Promise<void> {
    try {
      await apiClient.delete(`/expert_answers/${answerId}`)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '删除回答失败')
    }
  }

  // 获取专家统计信息
  async getStats(): Promise<ExpertStats> {
    try {
      const pools = await this.getAdminPools()
      const allAnswers = await this.getMyAnswers()
      
      const totalQuestions = pools.reduce((sum, pool) => sum + pool.question_count, 0)
      const totalAnswers = allAnswers.length
      const pendingQuestions = totalQuestions - totalAnswers

      return {
        total_admins: pools.length,
        total_questions: totalQuestions,
        total_answers: totalAnswers,
        pending_questions: Math.max(0, pendingQuestions)
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取统计信息失败')
    }
  }

  // 获取邀请码信息
  async getInviteCodeInfo(inviteCode: string): Promise<InviteCodeInfo> {
    try {
      const response = await apiClient.get('/expert/invite-code/info', {
        params: { invite_code: inviteCode }
      })
      return response.data
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取邀请码信息失败')
    }
  }

  // 获取专家回答的历史记录
  async getAnswerHistory(questionId: number): Promise<ExpertAnswer[]> {
    try {
      const allAnswers = await this.getMyAnswers()
      return allAnswers.filter(answer => answer.question_id === questionId)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || '获取回答历史失败')
    }
  }
}

export const expertService = new ExpertService()
export default expertService
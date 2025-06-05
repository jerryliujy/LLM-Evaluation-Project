<template>
  <div class="expert-dashboard">
    <!-- 页面头部 -->
    <div class="dashboard-header">
      <div class="header-info">
        <h1>专家工作台</h1>
        <p>欢迎，{{ currentUser?.username }}！您可以通过邀请码加入不同管理员的问题池</p>
      </div>
      <div class="header-actions">
        <button class="btn-primary" @click="showJoinDialog = true">
          输入邀请码
        </button>
        <button class="btn-secondary" @click="logout">
          退出登录
        </button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-grid">
      <div class="stat-card">
        <h3>已加入管理员</h3>
        <div class="stat-number">{{ adminPools.length }}</div>
        <p>个问题池</p>
      </div>

      <div class="stat-card">
        <h3>总问题数</h3>
        <div class="stat-number">{{ totalQuestions }}</div>
        <p>个问题</p>
      </div>

      <div class="stat-card">
        <h3>我的回答</h3>
        <div class="stat-number">{{ totalAnswers }}</div>
        <p>条回答</p>
      </div>

      <div class="stat-card">
        <h3>待处理</h3>
        <div class="stat-number">{{ pendingQuestions }}</div>
        <p>个问题</p>
      </div>
    </div>

    <!-- 管理员问题池列表 -->
    <div class="admin-pools-section">
      <h2>我的问题池</h2>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="adminPools.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>还没有加入任何问题池</h3>
        <p>请输入管理员提供的邀请码来加入问题池</p>
        <button class="btn-primary" @click="showJoinDialog = true">
          输入邀请码
        </button>
      </div>
      <div v-else class="pools-grid">
        <div 
          v-for="pool in adminPools" 
          :key="pool.admin_id" 
          class="pool-card"
          @click="selectPool(pool)"
          :class="{ active: selectedPool?.admin_id === pool.admin_id }"
        >
          <div class="pool-header">
            <h3>{{ pool.admin_username }}</h3>
            <span class="pool-status">活跃</span>
          </div>
          <div class="pool-stats">
            <div class="pool-stat">
              <span class="stat-label">问题数</span>
              <span class="stat-value">{{ pool.question_count }}</span>
            </div>
            <div class="pool-stat">
              <span class="stat-label">我的回答</span>
              <span class="stat-value">{{ pool.answer_count }}</span>
            </div>
          </div>
          <div class="pool-meta">
            <p>加入时间: {{ formatDate(pool.joined_at) }}</p>
            <p v-if="pool.invite_code">邀请码: {{ pool.invite_code }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 问题列表 -->
    <div v-if="selectedPool" class="questions-section">
      <div class="section-header">
        <h2>{{ selectedPool.admin_username }} 的问题</h2>
        <div class="question-filter">
          <select v-model="questionFilter" @change="filterQuestions">
            <option value="all">全部问题</option>
            <option value="unanswered">未回答</option>
            <option value="answered">已回答</option>
          </select>
        </div>
      </div>
      
      <div v-if="questionsLoading" class="loading">加载问题中...</div>
      <div v-else-if="filteredQuestions.length === 0" class="empty-state">
        <p>{{ getEmptyMessage() }}</p>
      </div>
      <div v-else class="questions-list">
        <div 
          v-for="question in filteredQuestions" 
          :key="question.id" 
          class="question-item"
          :class="{ answered: hasAnswer(question.id) }"
        >
          <div class="question-content">
            <h4>{{ question.title }}</h4>
            <p class="question-body">{{ truncateText(question.body || '') }}</p>
            <div class="question-meta">
              <span>作者: {{ question.author }}</span>
              <span>投票: {{ question.vote_count }}</span>
              <span>浏览: {{ question.view_count }}</span>
              <span>发布: {{ formatDate(question.issued_at || '') }}</span>
            </div>
          </div>
          <div class="question-actions">
            <button 
              v-if="hasAnswer(question.id)"
              class="btn-outline btn-sm"
              @click="editAnswer(question)"
            >
              编辑回答
            </button>
            <button 
              v-else
              class="btn-primary btn-sm"
              @click="createAnswer(question)"
            >
              创建回答
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入邀请码对话框 -->
    <div v-if="showJoinDialog" class="modal-overlay" @click="closeJoinDialog">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>输入邀请码</h3>
          <button class="modal-close" @click="closeJoinDialog">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="joinWithInviteCode">
            <div class="form-group">
              <label for="inviteCode">管理员邀请码</label>
              <input
                id="inviteCode"
                v-model="inviteCodeInput"
                type="text"
                placeholder="请输入管理员提供的邀请码"
                required
                class="invite-input"
              />
              <p class="help-text">
                输入邀请码后，您将可以访问该管理员的所有原始问题
              </p>
            </div>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeJoinDialog">
                取消
              </button>
              <button type="submit" class="btn-primary" :disabled="joiningPool">
                {{ joiningPool ? '加入中...' : '加入问题池' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 成功提示 -->
    <div v-if="successMessage" class="success-toast">
      {{ successMessage }}
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-toast">
      {{ errorMessage }}
    </div>

    <!-- 回答编辑器 -->
    <AnswerEditor
      v-if="showAnswerEditor && currentQuestion"
      :question="currentQuestion!"
      :answer="currentAnswer"
      @close="closeAnswerEditor"
      @saved="onAnswerSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { RawQuestion } from '@/types/questions'
import type { AdminPool } from '@/types/expert'
import type { ExpertAnswer } from '@/types/answers'
import { expertService } from '@/services/expertService'
import { authService } from '@/services/authService'
import AnswerEditor from '@/components/AnswerEditor.vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const questionsLoading = ref(false)
const joiningPool = ref(false)

// 管理员问题池相关
const adminPools = ref<AdminPool[]>([])
const selectedPool = ref<AdminPool | null>(null)
const questions = ref<RawQuestion[]>([])
const answers = ref<ExpertAnswer[]>([])

// 对话框状态
const showJoinDialog = ref(false)
const showAnswerEditor = ref(false)
const inviteCodeInput = ref('')

// 答案编辑器
const currentQuestion = ref<RawQuestion | null>(null)
const currentAnswer = ref<ExpertAnswer | null>(null)

// 过滤器
const questionFilter = ref('all')

// 提示信息
const successMessage = ref('')
const errorMessage = ref('')

// 用户信息
const currentUser = authService.getCurrentUserFromStorage()

// 计算属性
const totalQuestions = computed(() => {
  return adminPools.value.reduce((sum, pool) => sum + pool.question_count, 0)
})

const totalAnswers = computed(() => {
  return adminPools.value.reduce((sum, pool) => sum + pool.answer_count, 0)
})

const pendingQuestions = computed(() => {
  return totalQuestions.value - totalAnswers.value
})

const filteredQuestions = computed(() => {
  if (questionFilter.value === 'all') {
    return questions.value
  } else if (questionFilter.value === 'answered') {
    return questions.value.filter(q => hasAnswer(q.id))
  } else if (questionFilter.value === 'unanswered') {
    return questions.value.filter(q => !hasAnswer(q.id))
  }
  return questions.value
})

// 生命周期
onMounted(() => {
  loadAdminPools()
  loadAnswers()
})

// 方法
async function loadAdminPools() {
  loading.value = true
  try {
    adminPools.value = await expertService.getAdminPools()
  } catch (error) {
    console.error('加载管理员问题池失败:', error)
    showError('加载管理员问题池失败')
  } finally {
    loading.value = false
  }
}

async function selectPool(pool: AdminPool) {
  selectedPool.value = pool
  await loadPoolQuestions(pool.task_id)
}

async function loadPoolQuestions(taskId: number) {
  questionsLoading.value = true
  try {
    questions.value = await expertService.getTaskQuestions(taskId)
  } catch (error) {
    console.error('加载问题失败:', error)
    showError('加载问题失败')
  } finally {
    questionsLoading.value = false
  }
}

async function loadAnswers() {
  try {
    answers.value = await expertService.getMyAnswers()
  } catch (error) {
    console.error('加载回答失败:', error)
  }
}

function hasAnswer(questionId: number): boolean {
  return answers.value.some(answer => answer.question_id === questionId)
}

async function joinWithInviteCode() {
  if (!inviteCodeInput.value.trim()) return
  
  joiningPool.value = true
  try {
    await expertService.joinTask({ invite_code: inviteCodeInput.value })
    await loadAdminPools()
    await loadAnswers() // 重新加载回答数据
    closeJoinDialog()
    showSuccess('成功加入问题池！')
  } catch (error: any) {
    console.error('加入问题池失败:', error)
    
    // 如果是已经加入的错误，重新加载数据而不显示错误
    if (error.message?.includes('您已经接受了该管理员的任务')) {
      await loadAdminPools()
      await loadAnswers()
      closeJoinDialog()
      showSuccess('您已经在此问题池中，数据已刷新！')
    } else {
      showError(error.message || '加入问题池失败，请检查邀请码是否正确')
    }
  } finally {
    joiningPool.value = false
  }
}

function closeJoinDialog() {
  showJoinDialog.value = false
  inviteCodeInput.value = ''
}

function filterQuestions() {
  // 筛选逻辑在计算属性中处理
}

function getEmptyMessage(): string {
  if (questionFilter.value === 'answered') {
    return '还没有已回答的问题'
  } else if (questionFilter.value === 'unanswered') {
    return '没有待回答的问题'
  }
  return '此管理员还没有发布任何问题'
}

function createAnswer(question: RawQuestion) {
  currentQuestion.value = question
  currentAnswer.value = null
  showAnswerEditor.value = true
}

function editAnswer(question: RawQuestion) {
  currentQuestion.value = question
  currentAnswer.value = answers.value.find(a => a.question_id === question.id) || null
  showAnswerEditor.value = true
}

function closeAnswerEditor() {
  showAnswerEditor.value = false
  currentQuestion.value = null
  currentAnswer.value = null
}

async function onAnswerSaved() {
  await loadAnswers()
  await loadAdminPools() // 重新加载以更新统计信息
  closeAnswerEditor()
  showSuccess('回答已保存！')
}

function formatDate(date: string | Date): string {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

function truncateText(text: string, maxLength = 200): string {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

function showSuccess(message: string) {
  successMessage.value = message
  setTimeout(() => {
    successMessage.value = ''
  }, 3000)
}

function showError(message: string) {
  errorMessage.value = message
  setTimeout(() => {
    errorMessage.value = ''
  }, 5000)
}

async function logout() {
  try {
    await authService.logout()
    router.push({ name: 'Login' })
  } catch (error) {
    console.error('退出登录失败:', error)
  }
}
</script>

<style scoped>
.expert-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-info h1 {
  margin: 0 0 5px 0;
  color: #333;
}

.header-info p {
  margin: 0;
  color: #666;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn-primary {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-primary:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary:hover {
  background-color: #545b62;
}

.btn-outline {
  padding: 8px 16px;
  background-color: transparent;
  color: #007bff;
  border: 1px solid #007bff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-outline:hover {
  background-color: #007bff;
  color: white;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-card h3 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
  font-weight: normal;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #007bff;
  margin: 10px 0;
}

.stat-card p {
  margin: 0;
  color: #999;
  font-size: 14px;
}

.admin-pools-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.admin-pools-section h2 {
  margin: 0 0 20px 0;
  color: #333;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.empty-state h3 {
  margin: 10px 0;
  color: #333;
}

.pools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.pool-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.pool-card:hover {
  border-color: #007bff;
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.1);
}

.pool-card.active {
  border-color: #007bff;
  background-color: #f8f9ff;
}

.pool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.pool-header h3 {
  margin: 0;
  color: #333;
}

.pool-status {
  background-color: #28a745;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.pool-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.pool-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #007bff;
}

.pool-meta {
  border-top: 1px solid #e9ecef;
  padding-top: 15px;
}

.pool-meta p {
  margin: 5px 0;
  font-size: 12px;
  color: #666;
}

.questions-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
  color: #333;
}

.question-filter select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.question-item {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.question-item.answered {
  background-color: #f8f9fa;
  border-color: #28a745;
}

.question-content {
  flex: 1;
}

.question-content h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.question-body {
  margin: 10px 0;
  color: #666;
  line-height: 1.5;
}

.question-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #999;
  margin-top: 10px;
}

.question-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.invite-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.help-text {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.success-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: #28a745;
  color: white;
  padding: 15px 20px;
  border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 1100;
}

.error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: #dc3545;
  color: white;
  padding: 15px 20px;
  border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 1100;
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .pools-grid {
    grid-template-columns: 1fr;
  }

  .question-item {
    flex-direction: column;
    align-items: stretch;
  }

  .question-actions {
    flex-direction: row;
  }

  .section-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
}
</style>

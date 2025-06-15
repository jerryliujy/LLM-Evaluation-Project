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
        <div class="section-actions">
          <button class="btn-import" @click="showDataImportDialog = true">
            📁 导入专家回答数据
          </button>
          <div class="question-filter">
            <select v-model="questionFilter" @change="filterQuestions">
              <option value="all">全部问题</option>
              <option value="unanswered">未回答</option>
              <option value="answered">已回答</option>
            </select>
          </div>
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
              <span>投票: {{ question.votes }}</span>
              <span>浏览: {{ question.views }}</span>
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

    <!-- 数据导入对话框 -->
    <div v-if="showDataImportDialog" class="modal-overlay" @click="closeDataImportDialog">
      <div class="modal-content data-import-modal" @click.stop>
        <div class="modal-header">
          <h3>导入专家回答数据</h3>
          <button class="modal-close" @click="closeDataImportDialog">&times;</button>
        </div>
        <div class="modal-body">
          <div class="import-info">
            <p><strong>目标管理员:</strong> {{ selectedPool?.admin_username }}</p>
            <p><strong>数据格式:</strong> 专家回答数据 JSON 格式</p>
          </div>
          
          <div class="import-step" v-if="importStep === 'select'">
            <h4>选择数据文件</h4>
            <div class="file-upload-area">
              <input
                type="file"
                id="dataFile"
                accept=".json"
                @change="handleFileSelect"
                class="file-input"
              />
              <label for="dataFile" class="file-upload-label">
                <div class="upload-icon">📁</div>
                <div class="upload-text">
                  <p>点击选择 JSON 文件</p>
                  <p class="upload-hint">支持 .json 格式</p>
                </div>
              </label>
            </div>
            
            <div class="data-format-help">
              <h5>数据格式示例：</h5>
              <pre class="format-example">[
  {
    "question_id": 1,
    "answer": "专家回答内容...",
    "referenced_raw_answer_ids": [1, 2]
  }
]</pre>
            </div>
          </div>

          <div class="import-step" v-if="importStep === 'preview'">
            <h4>数据预览</h4>
            <div class="preview-stats">
              <span class="stat-item">
                <strong>总记录数:</strong> {{ importData.length }}
              </span>
              <span class="stat-item">
                <strong>有效记录:</strong> {{ validRecords }}
              </span>
            </div>
            
            <div class="preview-data" v-if="previewData.length > 0">
              <div v-for="(item, index) in previewData" :key="index" class="preview-item">
                <div class="preview-header">
                  <span class="preview-id">问题ID: {{ item.question_id }}</span>
                  <span class="preview-status" :class="{ 
                    valid: item.question_id && item.answer,
                    invalid: !item.question_id || !item.answer
                  }">
                    {{ item.question_id && item.answer ? '✓ 有效' : '✗ 无效' }}
                  </span>
                </div>
                <div class="preview-answer">
                  {{ truncateText(item.answer || '无回答内容', 100) }}
                </div>
              </div>
            </div>

            <div class="validation-errors" v-if="validationErrors.length > 0">
              <h5>验证错误：</h5>
              <ul>
                <li v-for="error in validationErrors" :key="error">{{ error }}</li>
              </ul>
            </div>
          </div>

          <div class="import-step" v-if="importStep === 'importing'">
            <div class="importing-status">
              <div class="loading-spinner"></div>
              <p>正在导入数据，请稍候...</p>
            </div>
          </div>

          <div class="import-step" v-if="importStep === 'result'">
            <div class="import-result">
              <div class="result-icon" :class="{ success: importSuccess, error: !importSuccess }">
                {{ importSuccess ? '✅' : '❌' }}
              </div>
              <h4>{{ importSuccess ? '导入成功' : '导入失败' }}</h4>
              <p v-if="importSuccess">
                成功导入 {{ importResult?.imported_answers || 0 }} 条专家回答
              </p>
              <p v-else class="error-text">
                {{ importErrorMessage }}
              </p>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="closeDataImportDialog">
              {{ importStep === 'result' ? '关闭' : '取消' }}
            </button>
            <button 
              v-if="importStep === 'select'" 
              type="button" 
              class="btn-primary" 
              @click="loadTestData"
            >
              加载测试数据
            </button>
            <button 
              v-if="importStep === 'preview'" 
              type="button" 
              class="btn-primary" 
              :disabled="validRecords === 0 || importing"
              @click="startImport"
            >
              {{ importing ? '导入中...' : '开始导入' }}
            </button>
            <button 
              v-if="importStep === 'result' && importSuccess" 
              type="button" 
              class="btn-primary" 
              @click="closeDataImportDialog"
            >
              完成
            </button>
          </div>
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
const showDataImportDialog = ref(false)
const inviteCodeInput = ref('')

// 数据导入相关
const importStep = ref<'select' | 'preview' | 'importing' | 'result'>('select')
const importing = ref(false)
const importData = ref<any[]>([])
const importSuccess = ref(false)
const importResult = ref<{ imported_answers: number } | null>(null)
const importErrorMessage = ref('')
const validationErrors = ref<string[]>([])

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

// 数据导入相关计算属性
const validRecords = computed(() => {
  return importData.value.filter(item => item.question_id && item.answer).length
})

const previewData = computed(() => {
  return importData.value.slice(0, 3) // 显示前3条记录
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

// 数据导入相关方法
function closeDataImportDialog() {
  showDataImportDialog.value = false
  resetImportState()
}

function resetImportState() {
  importStep.value = 'select'
  importing.value = false
  importData.value = []
  importSuccess.value = false
  importResult.value = null
  importErrorMessage.value = ''
  validationErrors.value = []
}

function handleFileSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target?.result as string)
      if (Array.isArray(data)) {
        importData.value = data
        validateImportData(data)
        importStep.value = 'preview'
      } else {
        showError('文件格式错误：应该是JSON数组格式')
      }
    } catch (error) {
      showError('文件解析失败：请确保是有效的JSON文件')
    }
  }
  reader.readAsText(file)
}

function validateImportData(data: any[]) {
  const errors: string[] = []
  
  data.forEach((item, index) => {
    if (!item.question_id) {
      errors.push(`第${index + 1}项缺少question_id字段`)
    }
    if (!item.answer) {
      errors.push(`第${index + 1}项缺少answer字段`)
    }
  })
  
  validationErrors.value = errors
}

async function loadTestData() {
  try {
    // 加载测试数据
    const response = await fetch('/test_data/expert_answers_data.json')
    if (!response.ok) {
      throw new Error('加载测试数据失败')
    }
    const data = await response.json()
    
    if (Array.isArray(data)) {
      importData.value = data
      validateImportData(data)
      importStep.value = 'preview'
    } else {
      showError('测试数据格式错误')
    }
  } catch (error) {
    showError('加载测试数据失败，请检查测试文件是否存在')
  }
}

async function startImport() {
  if (!selectedPool.value || validRecords.value === 0) return
  
  importing.value = true
  importStep.value = 'importing'
  
  try {
    const result = await expertService.importAnswersToTask(
      selectedPool.value.task_id,
      importData.value.filter(item => item.question_id && item.answer)
    )
    
    importSuccess.value = true
    importResult.value = result
    importStep.value = 'result'
    
    // 重新加载数据
    await loadAnswers()
    await loadAdminPools()
    
  } catch (error: any) {
    importSuccess.value = false
    importErrorMessage.value = error.message || '导入失败'
    importStep.value = 'result'
  } finally {
    importing.value = false
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

/* 数据导入相关样式 */
.section-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.btn-import {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-import:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(40, 167, 69, 0.3);
}

.data-import-modal {
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.import-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.import-info p {
  margin: 5px 0;
  color: #495057;
}

.import-step {
  margin-bottom: 20px;
}

.file-upload-area {
  position: relative;
  margin: 15px 0;
}

.file-input {
  display: none;
}

.file-upload-label {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.file-upload-label:hover {
  border-color: #007bff;
  background-color: #f8f9fa;
}

.upload-icon {
  font-size: 24px;
}

.upload-text p {
  margin: 0;
}

.upload-hint {
  font-size: 0.9em;
  color: #6c757d;
}

.data-format-help {
  margin-top: 20px;
  background: #e9ecef;
  padding: 15px;
  border-radius: 6px;
}

.format-example {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 0.9em;
  overflow-x: auto;
}

.preview-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.stat-item {
  padding: 8px 12px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.9em;
}

.preview-data {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 6px;
}

.preview-item {
  padding: 15px;
  border-bottom: 1px solid #e9ecef;
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.preview-id {
  font-weight: 500;
  color: #495057;
}

.preview-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: 500;
}

.preview-status.valid {
  background: #d4edda;
  color: #155724;
}

.preview-status.invalid {
  background: #f8d7da;
  color: #721c24;
}

.preview-answer {
  color: #6c757d;
  font-size: 0.9em;
  line-height: 1.4;
}

.validation-errors {
  margin-top: 15px;
  padding: 15px;
  background: #f8d7da;
  border-radius: 6px;
  color: #721c24;
}

.validation-errors ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

.importing-status {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.import-result {
  text-align: center;
  padding: 30px;
}

.result-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.result-icon.success {
  color: #28a745;
}

.result-icon.error {
  color: #dc3545;
}

.error-text {
  color: #dc3545;
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

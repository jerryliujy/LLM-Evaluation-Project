<template>
  <div class="raw-question-management">
    <!-- 头部 -->
    <div class="header">
      <div class="header-left">
        <h1>原始问题池管理</h1>
        <p class="subtitle">管理您的原始问题和回答，创建标准问答对</p>
      </div>      <div class="header-actions">
        <button @click="addNewQuestion" class="action-btn primary">
          <span class="btn-icon">✏️</span>
          <span>手动添加问题</span>
        </button>
        <button @click="showImportDialog" class="action-btn primary">
          <span class="btn-icon">📁</span>
          <span>文件导入数据</span>
        </button>
        <button @click="refreshData" class="action-btn secondary" :disabled="loading">
          {{ loading ? "加载中..." : "刷新" }}
        </button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总计:</span>
        <span class="stat-value">{{ totalQuestions }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">当前页:</span>
        <span class="stat-value">{{ filteredQuestions.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">选中:</span>
        <span class="stat-value">{{ selectedItems.length }}</span>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="actions-bar">
      <div class="bulk-actions">
        <button 
          @click="selectAll" 
          class="action-btn"
          :disabled="filteredQuestions.length === 0"
        >
          {{ selectedItems.length === filteredQuestions.length ? "取消全选" : "全选" }}
        </button>
        <button 
          @click="deleteSelectedQuestions" 
          class="action-btn danger"
          :disabled="selectedItems.length === 0"
        >
          批量删除 ({{ selectedItems.length }})
        </button>
        <button 
          @click="createStandardQA" 
          class="action-btn success"
          :disabled="selectedItems.length === 0"
        >
          创建标准问答
        </button>
      </div>      <div class="view-options">
        <select v-model="viewMode" @change="handleViewModeChange" class="view-mode-select">
          <option value="overview">概览模式</option>
          <option value="questions">原始问题</option>
          <option value="raw-answers">原始回答</option>
          <option value="expert-answers">专家回答</option>
        </select>
        
        <select v-model="showMode" @change="handleShowModeChange" class="show-mode-select">
          <option value="active_only">仅显示未删除</option>
          <option value="deleted_only">仅显示已删除</option>
          <option value="all">显示全部</option>
        </select>
        
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索问题..."
          class="search-input"
        />
        <select v-model="itemsPerPage" @change="loadData" class="per-page-select">
          <option value="20">20条/页</option>
          <option value="50">50条/页</option>
          <option value="100">100条/页</option>
        </select>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table class="data-table" v-if="filteredQuestions.length > 0">        <thead>
          <tr>
            <!-- 概览模式下不显示复选框 -->
            <th v-if="viewMode !== 'overview'" class="checkbox-col">
              <input 
                type="checkbox" 
                :checked="selectedItems.length === filteredQuestions.length && filteredQuestions.length > 0"
                @change="selectAll"
              />
            </th>
            
            <!-- 概览模式简化表头 -->
            <template v-if="viewMode === 'overview'">
              <th class="id-col">ID</th>
              <th class="title-col">原始问题</th>
              <th class="answers-col">原始回答</th>
              <th class="expert-answers-col">专家回答</th>
            </template>
            
            <!-- 其他模式的表头 -->
            <template v-else>
              <th class="id-col">ID</th>
              <th class="title-col">
                <span v-if="viewMode === 'questions'">标题</span>
                <span v-else-if="viewMode === 'raw-answers'">原始回答内容</span>
                <span v-else-if="viewMode === 'expert-answers'">专家回答内容</span>
              </th>
              <th class="author-col">作者</th>
              <th v-if="viewMode === 'raw-answers' || viewMode === 'expert-answers'" class="question-col">关联问题</th>
              <th class="stats-col">统计</th>
              <th class="tags-col">标签</th>
              <th class="date-col">创建时间</th>
              <th class="actions-col">操作</th>
            </template>
          </tr>
        </thead>
        <tbody>          
          <tr v-for="question in paginatedQuestions" :key="question.id" class="data-row">
            <!-- 概览模式的简化行 -->
            <template v-if="viewMode === 'overview'">
              <td class="id-col">{{ question.id }}</td>
              <td class="title-col">
                <div class="cell-content">
                  <div class="title-text" @click="viewQuestion(question)" :title="question.title">
                    {{ question.title }}
                  </div>
                  <div v-if="question.body" class="body-preview" :title="question.body">
                    {{ truncateText(question.body, 50) }}
                  </div>
                </div>
              </td>
              <td class="answers-col">
                <div class="answers-content">
                  <div v-if="question.raw_answers && question.raw_answers.length > 0" class="answer-group">
                    <div class="answer-count">{{ question.raw_answers.length }}个回答</div>
                    <div class="answer-preview">{{ truncateText(question.raw_answers[0].content, 60) }}</div>
                    <div v-if="question.raw_answers.length > 1" class="more-answers">+{{ question.raw_answers.length - 1 }}个</div>
                  </div>
                  <div v-else class="no-answers">暂无原始回答</div>
                </div>
              </td>
              <td class="expert-answers-col">
                <div class="answers-content">
                  <div v-if="question.expert_answers && question.expert_answers.length > 0" class="answer-group">
                    <div class="answer-count">{{ question.expert_answers.length }}个专家回答</div>
                    <div class="answer-preview">{{ truncateText(question.expert_answers[0].content, 60) }}</div>
                    <div v-if="question.expert_answers.length > 1" class="more-answers">+{{ question.expert_answers.length - 1 }}个</div>
                  </div>
                  <div v-else class="no-answers">暂无专家回答</div>
                </div>
              </td>
            </template>
            
            <!-- 其他模式的完整行 -->
            <template v-else>
                <div>
                  <span class="answer-type">原始({{ question.raw_answers.length }})</span>
                  <span class="answer-text">{{ truncateText(question.raw_answers[0].content, 30) }}</span>
                  <span v-if="question.raw_answers.length > 1" class="more-answers">+{{ question.raw_answers.length - 1 }}</span>
                </div>
                
                <div v-if="question.expert_answers && question.expert_answers.length > 0" class="answer-group">
                  <span class="answer-type">专家({{ question.expert_answers.length }})</span>
                  <span class="answer-text">{{ truncateText(question.expert_answers[0].content, 30) }}</span>
                  <span v-if="question.expert_answers.length > 1" class="more-answers">+{{ question.expert_answers.length - 1 }}</span>
                </div>
                
                <div v-if="(!question.raw_answers || question.raw_answers.length === 0) && (!question.expert_answers || question.expert_answers.length === 0)" class="no-answers">
                  暂无回答
                </div>
            </template>
            <td v-if="viewMode === 'raw-answers' || viewMode === 'expert-answers'" class="question-col">
              <div class="cell-content">
                <div class="question-info" v-if="question.original_data && question.original_data.question">
                  <div class="question-title" :title="question.original_data.question.title">
                    {{ truncateText(question.original_data.question.title, 40) }}
                  </div>
                  <div class="question-meta">
                    <span>ID: {{ question.original_data.question.id }}</span>
                  </div>
                </div>
                <div v-else class="no-question">
                  无关联问题信息
                </div>
              </div>
            </td>            
            <td class="stats-col">
              <div class="stats-content">
                <div class="stats-info">
                  <!-- 原始问题和概览模式显示浏览和点赞 -->
                  <template v-if="viewMode === 'overview' || viewMode === 'questions'">
                    <span v-if="question.view_count !== undefined && question.view_count !== null" class="stats-item">👁 {{ question.view_count }}</span>
                    <span v-if="question.vote_count !== undefined && question.vote_count !== null" class="stats-item">⭐ {{ question.vote_count }}</span>
                  </template>
                  <!-- 原始回答模式不显示浏览和点赞 -->
                  <template v-else-if="viewMode === 'raw-answers'">
                    <span class="stats-item">原始回答</span>
                  </template>
                  <!-- 专家回答模式不显示浏览和点赞 -->
                  <template v-else-if="viewMode === 'expert-answers'">
                    <span class="stats-item">专家回答</span>
                  </template>
                </div>
              </div>
            </td>
            <td class="tags-col">
              <div class="tags-content">
                <span 
                  v-for="tag in question.tags?.slice(0, 2)" 
                  :key="tag" 
                  class="tag"
                  :title="question.tags?.join(', ')"
                >
                  {{ tag }}
                </span>
                <span v-if="question.tags && question.tags.length > 2" class="tag">
                  +{{ question.tags.length - 2 }}
                </span>
              </div>
            </td>
            <td class="date-col">
              <span class="truncate-text" :title="formatDate(question.created_at || question.issued_at)">
                {{ formatDate(question.created_at || question.issued_at) }}
              </span>
            </td>            <td class="actions-col">
              <div class="row-actions">
                <button 
                  @click.stop="viewQuestion(question)" 
                  class="action-btn small"
                  title="查看详情"
                >
                  👁️
                </button>
                <button 
                  @click.stop="editQuestion(question)" 
                  class="action-btn small"
                  title="编辑"
                >
                  ✏️
                </button>
                <button 
                  @click.stop="showDeleteConfirm(question)" 
                  class="action-btn small danger"
                  title="删除"
                >
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>      <div v-if="loading" class="loading-state">
        <p>加载中...</p>
      </div>

      <div v-else-if="filteredQuestions.length === 0" class="empty-state">
        <p>暂无数据</p>
        <p v-if="searchQuery">尝试调整搜索条件，或者<button @click="searchQuery = ''" class="link-btn">清除搜索</button></p>
        <p v-else>您还没有添加任何问题，<button @click="addNewQuestion" class="link-btn">开始添加</button>或<button @click="showImportDialog" class="link-btn">导入数据</button></p>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="totalPages > 1">
      <button 
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage <= 1"
        class="action-btn"
      >
        上一页
      </button>
      <span class="page-info">
        第 {{ currentPage }} 页，共 {{ totalPages }} 页
      </span>
      <button 
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage >= totalPages"
        class="action-btn"
      >
        下一页
      </button>
    </div>

    <!-- 对话框组件 -->
    <QuestionEditDialog 
      v-model:visible="questionDialogVisible"
      :question="currentQuestion"
      @save="handleQuestionSave"
    />
    
    <AnswerEditDialog
      v-model:visible="answerDialogVisible"
      :answer="currentAnswer"
      :type="currentAnswerType"
      @save="handleAnswerSave"
    />

    <StandardQADialog
      v-model:visible="standardQADialogVisible"
      :selected-items="selectedQuestionData"
      :questions="filteredQuestions"
      @created="handleStandardQACreated"
    />   
    
    <RawQAImportDialog
      v-model:visible="importDialogVisible"
      @imported="handleDataImported"
    />
    
    <QuestionDetailDialog
      v-model:visible="detailDialogVisible"
      :question="currentQuestion"
      :view-mode="viewMode"
      @edit="handleDetailEdit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RawQuestion } from '@/types/questions'
import { RawAnswer, ExpertAnswer } from '@/types/answers'
import QuestionEditDialog from '@/components/QuestionEditDialog.vue'
import AnswerEditDialog from '@/components/AnswerEditDialog.vue'
import StandardQADialog from '@/components/StandardQADialog.vue'
import RawQAImportDialog from '@/components/RawQAImportDialog.vue'
import QuestionDetailDialog from '@/components/QuestionDetailDialog.vue'
import { rawQuestionService } from "@/services/rawQuestionService"

// 响应式状态
const loading = ref(false)
const searchQuery = ref('')
const itemsPerPage = ref(20)
const currentPage = ref(1)
const selectedItems = ref<number[]>([])
const allQuestions = ref<RawQuestion[]>([])

// 视图模式状态
const viewMode = ref<'overview' | 'questions' | 'raw-answers' | 'expert-answers'>('overview')
const showMode = ref<'active_only' | 'deleted_only' | 'all'>('active_only')

// 对话框状态
const questionDialogVisible = ref(false)
const answerDialogVisible = ref(false)
const standardQADialogVisible = ref(false)
const importDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const currentQuestion = ref<RawQuestion | null>(null)
const currentAnswer = ref<RawAnswer | ExpertAnswer | null>(null)
const currentAnswerType = ref<'raw' | 'expert'>('raw')

// 计算属性
const totalQuestions = computed(() => allQuestions.value.length)

const filteredQuestions = computed(() => {
  let questions = allQuestions.value
  
  // 根据显示模式过滤
  if (showMode.value === 'active_only') {
    questions = questions.filter(q => !q.is_deleted)
  } else if (showMode.value === 'deleted_only') {
    questions = questions.filter(q => q.is_deleted)
  }
  // 'all' 模式不需要过滤
  
  // 根据搜索查询过滤
  if (!searchQuery.value) return questions
  const query = searchQuery.value.toLowerCase()
  return questions.filter(q => 
    q.title.toLowerCase().includes(query) ||
    q.body?.toLowerCase().includes(query) ||
    q.tags?.some(tag => tag.toLowerCase().includes(query))
  )
})

const totalPages = computed(() => 
  Math.ceil(filteredQuestions.value.length / itemsPerPage.value)
)

const paginatedQuestions = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredQuestions.value.slice(start, end)
})

const selectedQuestionData = computed(() => ({
  questions: new Set(selectedItems.value),
  rawAnswers: new Set<number>(),
  expertAnswers: new Set<number>()
}))

// 方法
const showMessage = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
  // 简单的消息提示实现
  alert(`${type.toUpperCase()}: ${message}`)
}

const formatDate = (date: string | Date | undefined) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN')
}

const truncateText = (text: string | undefined | null, maxLength: number) => {
  if (!text || text.length <= maxLength) return text || ''
  return text.substring(0, maxLength) + '...'
}

const loadData = async () => {
  try {
    loading.value = true
    
    // 根据显示模式确定参数
    let include_deleted = false
    let deleted_only = false
    
    if (showMode.value === 'all') {
      include_deleted = true
    } else if (showMode.value === 'deleted_only') {
      include_deleted = true
      deleted_only = true
    }
      // 根据视图模式调用不同的接口
    let response
    if (viewMode.value === 'overview' || viewMode.value === 'questions') {
      response = await rawQuestionService.getRawQuestionsOverview(0, 100, include_deleted, deleted_only)
      allQuestions.value = response.data || []    } else if (viewMode.value === 'raw-answers') {
      response = await rawQuestionService.getRawAnswersView(0, 100, include_deleted, deleted_only)
      // 将原始回答数据转换为问题格式以便在表格中显示
      allQuestions.value = (response.data || []).map((answer: any) => ({
        id: answer.id,
        title: answer.answer_text ? `${truncateText(answer.answer_text, 60)}` : '原始回答',
        body: answer.answer_text,
        author: answer.author || '匿名',
        view_count: 0,
        vote_count: answer.vote_count || 0,
        issued_at: answer.issued_at,
        created_at: answer.created_at,
        is_deleted: answer.is_deleted,
        tags: answer.question?.tags || [],
        type: 'raw-answer',
        original_data: answer,
        raw_answers: [], // 确保有这些数组字段
        expert_answers: []
      }))
    } else if (viewMode.value === 'expert-answers') {
      response = await rawQuestionService.getExpertAnswersView(0, 100, include_deleted, deleted_only)
      // 将专家回答数据转换为问题格式以便在表格中显示
      allQuestions.value = (response.data || []).map((answer: any) => ({
        id: answer.id,
        title: answer.answer_text ? `${truncateText(answer.answer_text, 60)}` : '专家回答',
        body: answer.answer_text,
        author: answer.expert_name || `专家 ${answer.expert_id}`,
        view_count: 0,
        vote_count: 0,
        issued_at: answer.issued_at,
        created_at: answer.created_at,
        is_deleted: answer.is_deleted,
        tags: answer.question?.tags || [],        type: 'expert-answer',
        raw_answers: [], // 确保有这些数组字段
        expert_answers: [],
        original_data: answer
      }))
    }
    
    console.log('加载的数据:', allQuestions.value) // 添加调试日志
  } catch (error) {
    console.error('加载数据失败:', error)
    showMessage('加载数据失败', 'error')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadData()
}

const selectAll = () => {
  if (selectedItems.value.length === paginatedQuestions.value.length) {
    selectedItems.value = []
  } else {
    selectedItems.value = paginatedQuestions.value.map(q => q.id)
  }
}

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    selectedItems.value = [] // 清空选择
  }
}

const addNewQuestion = () => {
  console.log('添加新问题') // 添加调试日志
  currentQuestion.value = null
  questionDialogVisible.value = true
}

const editQuestion = (question: RawQuestion) => {
  console.log('编辑问题:', question.title) // 添加调试日志
  currentQuestion.value = question
  questionDialogVisible.value = true
}

const viewQuestion = (question: RawQuestion) => {
  console.log('查看问题详情:', question.title) // 添加调试日志
  currentQuestion.value = question
  detailDialogVisible.value = true
}

const deleteQuestion = async (question: RawQuestion) => {
  try {
    await rawQuestionService.deleteRawQuestion(question.id)
    
    // 从本地数组中移除
    const index = allQuestions.value.findIndex(q => q.id === question.id)
    if (index !== -1) {
      allQuestions.value.splice(index, 1)
    }
      // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== question.id)
    
    showMessage('问题已删除', 'success')
  } catch (error) {
    console.error('删除问题失败:', error)
    showMessage('删除失败', 'error')
  }
}

// 视图模式处理
const handleViewModeChange = () => {
  console.log('视图模式切换到:', viewMode.value)
  // 重置到第一页并重新加载数据
  currentPage.value = 1
  selectedItems.value = []
  loadData()
}

const handleShowModeChange = () => {
  console.log('显示模式切换到:', showMode.value)
  // 这里会自动触发 filteredQuestions 的重新计算
  // 重置到第一页
  currentPage.value = 1
  selectedItems.value = []
}

const deleteSelectedQuestions = async () => {
  if (selectedItems.value.length === 0) return
  
  if (!confirm(`确定要删除选中的 ${selectedItems.value.length} 个问题吗？`)) return
  
  try {
    // 使用批量删除API
    await rawQuestionService.deleteMultipleRawQuestions(selectedItems.value)
    
    // 从本地数组中移除
    allQuestions.value = allQuestions.value.filter(q => !selectedItems.value.includes(q.id))
      const deletedCount = selectedItems.value.length
    selectedItems.value = []
    showMessage(`已删除 ${deletedCount} 个问题`, 'success')
  } catch (error) {
    console.error('批量删除失败:', error)
    showMessage('批量删除失败', 'error')
  }
}

const createStandardQA = () => {
  if (selectedItems.value.length === 0) {
    showMessage('请先选择问题', 'warning')
    return
  }
  standardQADialogVisible.value = true
}

const showImportDialog = () => {
  importDialogVisible.value = true
}

const handleDataImported = () => {
  // 重新加载问题列表
  loadData()
  showMessage('数据导入完成，问题列表已更新', 'success')
}

const handleQuestionSave = async (questionData: Partial<RawQuestion>) => {
  try {
    if (currentQuestion.value) {
      // 更新现有问题
      await rawQuestionService.updateRawQuestion(currentQuestion.value.id, questionData)
      showMessage('问题已更新', 'success')
    } else {
      // 创建新问题
      await rawQuestionService.createRawQuestion(questionData)
      showMessage('问题已创建', 'success')
    }
    questionDialogVisible.value = false
    loadData() // 重新加载数据
  } catch (error) {
    console.error('保存问题失败:', error)
    showMessage('保存问题失败', 'error')
  }
}

const handleAnswerSave = () => {
  showMessage('回答已保存', 'success')
  answerDialogVisible.value = false
  loadData() // 重新加载数据
}

const handleStandardQACreated = () => {
  showMessage('标准问答已创建', 'success')
  standardQADialogVisible.value = false
  selectedItems.value = []
}

const handleDetailEdit = (question: RawQuestion) => {
  detailDialogVisible.value = false
  editQuestion(question)
}

// 删除确认和处理
const showDeleteConfirm = (question: RawQuestion) => {
  const message = question.is_deleted 
    ? `问题 "${question.title}" 已被软删除。\n\n请选择操作：\n- 确定：恢复问题\n- 取消：永久删除问题`
    : `确定要删除问题 "${question.title}" 吗？`
  
  if (question.is_deleted) {
    // 已删除的问题，询问是恢复还是永久删除
    if (confirm(message)) {
      restoreQuestion(question)
    } else {
      if (confirm(`确定要永久删除问题 "${question.title}" 吗？此操作无法撤销！`)) {
        forceDeleteQuestion(question)
      }
    }
  } else {
    // 未删除的问题，直接软删除
    if (confirm(message)) {
      softDeleteQuestion(question)
    }
  }
}

// 删除功能
const softDeleteQuestion = async (question: RawQuestion) => {
  try {
    await rawQuestionService.updateRawQuestion(question.id, { is_deleted: true })
    
    // 更新本地状态
    const index = allQuestions.value.findIndex(q => q.id === question.id)
    if (index !== -1) {
      allQuestions.value[index].is_deleted = true
    }
    
    showMessage('问题已软删除', 'success')
  } catch (error) {
    console.error('软删除失败:', error)
    showMessage('软删除失败', 'error')
  }
}

const restoreQuestion = async (question: RawQuestion) => {
  try {
    await rawQuestionService.updateRawQuestion(question.id, { is_deleted: false })
    
    // 更新本地状态
    const index = allQuestions.value.findIndex(q => q.id === question.id)
    if (index !== -1) {
      allQuestions.value[index].is_deleted = false
    }
    
    showMessage('问题已恢复', 'success')
  } catch (error) {
    console.error('恢复失败:', error)
    showMessage('恢复失败', 'error')
  }
}

const forceDeleteQuestion = async (question: RawQuestion) => {
  try {
    // 如果问题未被软删除，先软删除
    if (!question.is_deleted) {
      await rawQuestionService.deleteRawQuestion(question.id)
    }
    
    // 然后强制删除
    await rawQuestionService.forceDeleteRawQuestion(question.id)
    
    // 从本地数组中移除
    const index = allQuestions.value.findIndex(q => q.id === question.id)
    if (index !== -1) {
      allQuestions.value.splice(index, 1)
    }
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== question.id)
    
    showMessage('问题已永久删除', 'success')
  } catch (error) {
    console.error('强制删除失败:', error)
    showMessage('强制删除失败', 'error')
  }
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.raw-question-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  flex: 1;
}

.header h1 {
  margin: 0 0 8px 0;
  color: #303133;
}

.subtitle {
  color: #606266;
  margin: 0;
}

/* 操作栏样式 */
.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 24px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f2f5;
}

.bulk-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.view-options {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 14px;
  min-width: 200px;
}

.search-input:focus {
  outline: none;
  border-color: #409eff;
}

.per-page-select {
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

/* 表格容器样式 */
.table-container {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 24px;
  overflow-x: auto; /* 添加水平滚动 */
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed; /* 固定表格布局 */
  min-width: 1400px; /* 增加最小宽度给内容更多空间 */
}

.data-table th {
  background: #f8f9fb;
  padding: 16px 12px; /* 增加内边距 */
  text-align: left;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  font-size: 14px; /* 稍微增大字体 */
  white-space: nowrap; /* 防止标题换行 */
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-table td {
  padding: 16px 12px; /* 增加内边距 */
  border-bottom: 1px solid #f0f2f5;
  vertical-align: middle; /* 改为中间对齐 */
  height: 70px; /* 稍微增加行高 */
  overflow: hidden;
}

.data-table tr:hover {
  background: #f8f9fb;
}

/* 优化的列宽控制 - 重新分配宽度给内容更多空间 */
.checkbox-col {
  width: 4%;
  min-width: 50px;
  text-align: center;
}

.id-col {
  width: 6%;
  min-width: 60px;
  text-align: center;
}

.title-col {
  width: 28%; /* 给标题更多空间 */
  min-width: 250px;
  white-space: normal; /* 标题可以换行 */
  max-height: 70px;
  overflow: hidden;
  position: relative;
}

.author-col {
  width: 10%;
  min-width: 120px;
}

.stats-col {
  width: 10%;
  min-width: 100px;
}

.tags-col {
  width: 12%;
  min-width: 140px;
}

.date-col {
  width: 10%;
  min-width: 100px;
}

.actions-col {
  width: 10%;
  min-width: 120px;
  text-align: center;
}

/* 回答信息列样式 - 给更多空间 */
.answers-col {
  width: 30%; /* 增加回答列宽度 */
  min-width: 280px;
  white-space: normal;
}

/* 关联问题列样式 */
.question-col {
  width: 25%;
  min-width: 250px;
  white-space: normal;
}

.question-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 2px 0;
}

.question-title {
  font-weight: 500;
  color: #409eff;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
}

.question-meta {
  font-size: 11px;
  color: #909399;
}

.no-question {
  font-size: 12px;
  color: #c0c4cc;
  text-align: center;
  padding: 8px 4px;
}

.answers-content {
  display: flex;
  flex-direction: column;
  gap: 6px; /* 增加间距 */
  max-height: 66px; /* 调整高度以匹配新的行高 */
  overflow: hidden;
  padding: 2px 0; /* 添加垂直内边距 */
}

.answer-group {
  border: 1px solid #e4e7ed;
  border-radius: 4px; /* 稍微增大圆角 */
  padding: 4px 8px; /* 增加内边距 */
  background-color: #f9f9f9;
  margin-bottom: 3px; /* 增加底部间距 */
  display: flex;
  align-items: center;
  gap: 8px; /* 添加元素间距 */
}

.answer-type {
  font-weight: bold;
  font-size: 12px; /* 稍微增大字体 */
  color: #409eff;
  flex-shrink: 0; /* 防止压缩 */
  min-width: 40px; /* 设置最小宽度 */
}

.answer-preview {
  font-size: 12px; /* 增大字体 */
  line-height: 1.3;
  flex: 1; /* 占据剩余空间 */
  display: flex;
  align-items: center;
  gap: 6px;
}

.answer-author {
  font-weight: 500;
  color: #303133;
  font-size: 12px; /* 增大字体 */
  flex-shrink: 0;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.answer-text {
  color: #606266;
  font-size: 12px; /* 增大字体 */
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-answers {
  font-size: 11px; /* 稍微增大 */
  color: #909399;
  font-style: italic;
  text-align: center;
  padding: 2px 4px;
}

.no-answers {
  font-size: 12px; /* 增大字体 */
  color: #c0c4cc;
  text-align: center;
  padding: 8px 4px; /* 增加内边距 */
}

/* 添加作者列样式 */
.author-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 0;
}

.author-name {
  font-weight: 500;
  color: #303133;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.author-role {
  font-size: 11px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.truncate-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* 标题列内容样式 */
.cell-content {
  display: flex;
  flex-direction: column;
  gap: 4px; /* 增加间距 */
  height: 100%;
  justify-content: center;
  padding: 2px 0; /* 添加垂直内边距 */
}

.title-text {
  font-weight: 500;
  color: #409eff;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2; /* 允许显示两行 */
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  font-size: 14px; /* 增大字体 */
  margin-bottom: 2px;
}

.title-text:hover {
  text-decoration: underline;
}

.body-preview {
  font-size: 12px; /* 稍微增大字体 */
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin: 0;
  line-height: 1.3;
}

/* 标签样式优化 - 单行显示 */
.tags-content {
  display: flex;
  flex-wrap: nowrap; /* 不换行 */
  gap: 2px; /* 减小标签间距 */
  align-items: center;
  padding: 2px 0;
  overflow: hidden; /* 隐藏溢出 */
}

.tag {
  display: inline-block;
  padding: 1px 4px; /* 减小内边距 */
  margin: 0;
  background: #f0f2f5;
  border-radius: 2px; /* 减小圆角 */
  font-size: 10px; /* 减小字体 */
  color: #606266;
  max-width: 60px; /* 减小最大宽度 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

/* 统计信息样式优化 - 单行显示 */
.stats-content {
  display: flex;
  flex-direction: row; /* 改为横向排列 */
  gap: 8px; /* 增加间距 */
  align-items: center;
  padding: 2px 0;
  justify-content: flex-start;
}

.stats-info {
  font-size: 11px; /* 稍微减小字体 */
  line-height: 1.2;
  display: flex;
  gap: 8px;
}

.stats-item {
  display: inline-block; /* 改为行内块元素 */
  margin: 0;
  white-space: nowrap;
  color: #606266;
  font-size: 11px; /* 减小字体 */
}

.stats-item strong {
  color: #303133;
  font-weight: 600;
}

/* 操作按钮优化 - 单行显示 */
.row-actions {
  display: flex;
  gap: 3px; /* 减小按钮间距 */
  justify-content: center;
  align-items: center;
  flex-wrap: nowrap; /* 不允许换行 */
}

.action-btn.small {
  padding: 4px 6px; /* 减小内边距 */
  font-size: 11px; /* 减小字体 */
  min-width: auto;
  line-height: 1.1;
  white-space: nowrap; /* 防止按钮文字换行 */
}

/* 通用按钮样式 */
.btn {
  padding: 6px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.btn:hover:not(:disabled) {
  background: #f8f9fb;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.primary {
  background: #409eff;
  border-color: #409eff;
  color: white;
}

.btn.primary:hover:not(:disabled) {
  background: #337ecc;
}

.btn.success {
  background: #67c23a;
  border-color: #67c23a;
  color: white;
}

.btn.success:hover:not(:disabled) {
  background: #529b2e;
}

.btn.danger {
  background: #f56c6c;
  border-color: #f56c6c;
  color: white;
}

.btn.danger:hover:not(:disabled) {
  background: #dd6161;
}

.btn.secondary {
  background: #909399;
  border-color: #909399;
  color: white;
}

.btn.secondary:hover:not(:disabled) {
  background: #73767a;
}

/* 分页样式 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-top: 24px;
}

.pagination-info {
  font-size: 14px;
  color: #606266;
}

/* 下拉菜单样式 */
.dropdown-wrapper {
  position: relative;
  display: inline-block;
}

.dropdown-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.dropdown-icon {
  font-size: 12px;
  transition: transform 0.2s ease;
  display: inline-block;
}

.dropdown-icon.rotated {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
  margin-top: 4px;
  min-width: 200px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #f5f7fa;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background-color: #f5f7fa;
}

.dropdown-item:active {
  background-color: #e4e7ed;
}

.item-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.item-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-title {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.item-desc {
  font-size: 12px;
  color: #909399;
}

/* 美化头部样式 */
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px 32px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  opacity: 0.9;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.action-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-icon {
  font-size: 16px;
}

.action-btn.primary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.action-btn.primary:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

/* 统计栏美化 */
.stats-bar {
  display: flex;
  gap: 24px;
  background: white;
  padding: 16px 24px;
  border-radius: 10px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f2f5;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.stat-value {
  color: #409eff;
  font-weight: 600;
  font-size: 16px;
}

/* 下拉菜单样式 */
.dropdown-wrapper {
  position: relative;
  display: inline-block;
}

.dropdown-icon {
  font-size: 12px;
  transition: transform 0.2s ease;
  display: inline-block;
  margin-left: 4px;
}

.dropdown-icon.rotated {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
  margin-top: 4px;
  min-width: 200px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #f5f7fa;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background-color: #f5f7fa;
}

.dropdown-item:active {
  background-color: #e4e7ed;
}

.item-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.item-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-title {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.item-desc {
  font-size: 12px;
  color: #909399;
}

.action-btn.small {
  padding: 4px 8px;
  font-size: 12px;
  min-width: auto;
}

.action-btn.active {
  background-color: #e6f7ff;
  border-color: #91d5ff;
  color: #1890ff;
}

/* 新添加的视图选择器样式 */
.view-mode-select,
.show-mode-select {
  padding: 6px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
}

.view-mode-select:focus,
.show-mode-select:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}
</style>
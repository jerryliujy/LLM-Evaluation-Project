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
      </div>
      <div class="view-options">
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
      <table class="data-table" v-if="filteredQuestions.length > 0">
        <thead>
          <tr>
            <th class="checkbox-col">
              <input 
                type="checkbox" 
                :checked="selectedItems.length === filteredQuestions.length && filteredQuestions.length > 0"
                @change="selectAll"
              />
            </th>
            <th class="id-col">ID</th>
            <th class="title-col">标题</th>
            <th class="author-col">作者</th>
            <th class="stats-col">统计</th>
            <th class="tags-col">标签</th>
            <th class="date-col">创建时间</th>
            <th class="actions-col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="question in paginatedQuestions" :key="question.id" class="data-row">
            <td class="checkbox-col">
              <input 
                type="checkbox" 
                :value="question.id"
                v-model="selectedItems"
              />
            </td>
            <td class="id-col">{{ question.id }}</td>
            <td class="title-col">
              <div class="cell-content">
                <span class="title-text" @click="viewQuestion(question)">{{ question.title }}</span>
                <p v-if="question.body" class="body-preview">{{ truncateText(question.body, 100) }}</p>
              </div>
            </td>
            <td class="author-col">{{ question.author || '匿名' }}</td>            <td class="stats-col">
              <div class="stats-content">
                <span class="stat-item">👁 {{ question.view_count || 0 }}</span>
                <span class="stat-item">⭐ {{ question.vote_count || 0 }}</span>
                <span class="stat-item">💬 {{ (question.raw_answers?.length || 0) + (question.expert_answers?.length || 0) }}</span>
              </div>
            </td>
            <td class="tags-col">
              <div class="tags-content">
                <span 
                  v-for="tag in question.tags" 
                  :key="tag" 
                  class="tag"
                >
                  {{ tag }}
                </span>
              </div>
            </td>
            <td class="date-col">{{ formatDate(question.created_at || question.issued_at) }}</td>
            <td class="actions-col">
              <div class="row-actions">
                <button 
                  @click="viewQuestion(question)" 
                  class="action-btn small"
                  title="查看详情"
                >
                  📄
                </button>
                <button 
                  @click="editQuestion(question)" 
                  class="action-btn small"
                  title="编辑"
                >
                  ✏️
                </button>
                <button 
                  @click="deleteQuestion(question)" 
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
import { rawQuestionService } from "@/services/rawQuestionService"

// 响应式状态
const loading = ref(false)
const searchQuery = ref('')
const itemsPerPage = ref(20)
const currentPage = ref(1)
const selectedItems = ref<number[]>([])
const allQuestions = ref<RawQuestion[]>([])

// 对话框状态
const questionDialogVisible = ref(false)
const answerDialogVisible = ref(false)
const standardQADialogVisible = ref(false)
const importDialogVisible = ref(false)
const currentQuestion = ref<RawQuestion | null>(null)
const currentAnswer = ref<RawAnswer | ExpertAnswer | null>(null)
const currentAnswerType = ref<'raw' | 'expert'>('raw')

// 计算属性
const totalQuestions = computed(() => allQuestions.value.length)

const filteredQuestions = computed(() => {
  if (!searchQuery.value) return allQuestions.value
  const query = searchQuery.value.toLowerCase()
  return allQuestions.value.filter(q => 
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

const loadData = async () => {
  try {
    loading.value = true
    const response = await rawQuestionService.getRawQuestions(0, 100) // 暂时加载所有数据
    allQuestions.value = response || []
    console.log('加载的问题数据:', allQuestions.value) // 添加调试日志
  } catch (error) {
    console.error('加载原始问题失败:', error)
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
  currentQuestion.value = null
  questionDialogVisible.value = true
}

const editQuestion = (question: RawQuestion) => {
  currentQuestion.value = question
  questionDialogVisible.value = true
}

const viewQuestion = (question: RawQuestion) => {
  // 可以在这里实现查看详情功能
  editQuestion(question)
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

const deleteSelectedQuestions = async () => {
  if (selectedItems.value.length === 0) return
  
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

const formatDate = (date: string | Date | undefined) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN')
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
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
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f8f9fb;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  font-size: 14px;
}

.data-table td {
  padding: 16px 12px;
  border-bottom: 1px solid #f0f2f5;
  vertical-align: top;
}

.data-table tr:hover {
  background: #f8f9fb;
}

/* 列宽控制 */
.checkbox-col {
  width: 50px;
  text-align: center;
}

.id-col {
  width: 80px;
  text-align: center;
}

.title-col {
  min-width: 250px;
  max-width: 350px;
}

.author-col {
  width: 120px;
}

.stats-col {
  width: 140px;
}

.tags-col {
  width: 150px;
}

.date-col {
  width: 120px;
}

.actions-col {
  width: 120px;
  text-align: center;
}

/* 单元格内容样式 */
.cell-content {
  max-height: 80px;
  overflow: hidden;
}

.title-text {
  color: #409eff;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
}

.title-text:hover {
  text-decoration: underline;
}

.body-preview {
  margin: 8px 0 0 0;
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
}

.stats-content {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.tags-content {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  background: #f0f2f5;
  color: #606266;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

.row-actions {
  display: flex;
  gap: 6px;
  justify-content: center;
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
</style>
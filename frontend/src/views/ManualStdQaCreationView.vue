<template>
  <div class="manual-creation-container">
    <div class="header">
      <div class="header-left">
        <button @click="goBackToDataImport" class="back-btn">
          ← 返回数据导入
        </button>
        <div class="title-section">
          <h2>手动创建标准问答对</h2>
          <p class="subtitle" v-if="currentDataset">
            数据库: {{ currentDataset.name }}
          </p>
        </div>
      </div>
    </div>

    <div class="creation-layout">
      <!-- 左侧：创建表单 -->
      <div class="creation-form-panel">
        <div class="form-section">
          <h3>创建标准问答对</h3>
          
          <form @submit.prevent="submitStdQa" class="std-qa-form">
            <div class="form-group">
              <label for="question">标准问题 *</label>
              <textarea
                id="question"
                v-model="stdQaForm.question"
                placeholder="请输入标准化的问题内容"
                rows="3"
                required
                class="form-control"
              ></textarea>
            </div>

            <div class="form-group">
              <label for="answer">标准答案 *</label>
              <textarea
                id="answer"
                v-model="stdQaForm.answer"
                placeholder="请输入标准答案内容"
                rows="5"
                required
                class="form-control"
              ></textarea>
            </div>

            <div class="form-group">
              <label for="questionType">问题类型</label>
              <select id="questionType" v-model="stdQaForm.questionType" class="form-control">
                <option value="text">文本问题</option>
                <option value="code">代码问题</option>
                <option value="concept">概念问题</option>
                <option value="procedure">流程问题</option>
              </select>
            </div>

            <div class="form-group">
              <label for="keyPoints">关键点 (可选)</label>
              <div class="key-points-input">
                <textarea
                  id="keyPoints"
                  v-model="keyPointsText"
                  placeholder="每行一个关键点"
                  rows="3"
                  class="form-control"
                ></textarea>
                <small class="form-hint">每行输入一个关键点，将自动转换为数组格式</small>
              </div>
            </div>

            <!-- 关联的原始问答 -->
            <div class="form-section">
              <h4>关联原始问答 (可选)</h4>
              <div class="reference-section">
                <div v-if="stdQaForm.rawQuestionId" class="selected-reference">
                  <div class="reference-item">
                    <strong>已选择原始问题:</strong>
                    <p>{{ selectedRawQuestion?.title }}</p>
                    <button type="button" @click="clearRawQuestion" class="clear-btn">移除</button>
                  </div>
                </div>
                <div v-if="stdQaForm.rawAnswerId" class="selected-reference">
                  <div class="reference-item">
                    <strong>已选择原始回答:</strong>
                    <p>{{ selectedRawAnswer?.answer?.substring(0, 100) }}...</p>
                    <button type="button" @click="clearRawAnswer" class="clear-btn">移除</button>
                  </div>
                </div>
                <div v-if="stdQaForm.expertAnswerId" class="selected-reference">
                  <div class="reference-item">
                    <strong>已选择专家回答:</strong>
                    <p>{{ selectedExpertAnswer?.answer?.substring(0, 100) }}...</p>
                    <button type="button" @click="clearExpertAnswer" class="clear-btn">移除</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" @click="resetForm" class="btn btn-secondary">
                重置表单
              </button>
              <button type="submit" :disabled="submitting" class="btn btn-primary">
                {{ submitting ? '创建中...' : '创建标准问答对' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- 右侧：浏览与检索面板 -->
      <div class="browse-panel">
        <div class="panel-tabs">
          <button
            @click="activeTab = 'raw-questions'"
            :class="{ active: activeTab === 'raw-questions' }"
            class="tab-btn"
          >
            原始问题
          </button>
          <button
            @click="activeTab = 'raw-answers'"
            :class="{ active: activeTab === 'raw-answers' }"
            class="tab-btn"
          >
            原始回答
          </button>
          <button
            @click="activeTab = 'expert-answers'"
            :class="{ active: activeTab === 'expert-answers' }"
            class="tab-btn"
          >
            专家回答
          </button>
        </div>

        <div class="search-section">
          <div class="search-controls">
            <input
              v-model="searchQuery"
              @input="performSearch"
              placeholder="搜索内容..."
              class="search-input"
            />
            <button @click="performSearch" class="search-btn">搜索</button>
          </div>
        </div>

        <!-- 原始问题列表 -->
        <div v-if="activeTab === 'raw-questions'" class="content-list">
          <div v-if="loading" class="loading-state">正在加载...</div>
          <div v-else-if="rawQuestions.length === 0" class="empty-state">
            暂无原始问题数据
          </div>
          <div v-else>
            <div
              v-for="question in rawQuestions"
              :key="question.id"
              @click="selectRawQuestion(question)"
              class="list-item"
              :class="{ selected: stdQaForm.rawQuestionId === question.id }"
            >
              <div class="item-header">
                <span class="item-id">ID: {{ question.id }}</span>
                <span class="item-author">{{ question.author }}</span>
              </div>
              <div class="item-title">{{ question.title }}</div>
              <div class="item-body">{{ question.body?.substring(0, 150) }}...</div>
              <div class="item-meta">
                <span>投票: {{ question.votes }}</span>
                <span>浏览: {{ question.views }}</span>
                <span>{{ formatDate(question.issued_at) }}</span>
              </div>
            </div>
          </div>
          
          <div class="pagination">
            <button
              @click="loadPreviousPage('raw-questions')"
              :disabled="currentPages.rawQuestions <= 1"
              class="page-btn"
            >
              上一页
            </button>
            <span class="page-info">
              第 {{ currentPages.rawQuestions }} 页
            </span>
            <button
              @click="loadNextPage('raw-questions')"
              :disabled="rawQuestions.length < itemsPerPage"
              class="page-btn"
            >
              下一页
            </button>
          </div>
        </div>

        <!-- 原始回答列表 -->
        <div v-if="activeTab === 'raw-answers'" class="content-list">
          <div v-if="loading" class="loading-state">正在加载...</div>
          <div v-else-if="rawAnswers.length === 0" class="empty-state">
            暂无原始回答数据
          </div>
          <div v-else>
            <div
              v-for="answer in rawAnswers"
              :key="answer.id"
              @click="selectRawAnswer(answer)"
              class="list-item"
              :class="{ selected: stdQaForm.rawAnswerId === answer.id }"
            >
              <div class="item-header">
                <span class="item-id">ID: {{ answer.id }}</span>
                <span class="item-author">{{ answer.answered_by }}</span>
              </div>
              <div class="item-content">{{ answer.answer?.substring(0, 200) }}...</div>
              <div class="item-meta">
                <span>问题ID: {{ answer.question_id }}</span>
                <span>赞同: {{ answer.upvotes }}</span>
                <span>{{ formatDate(answer.answered_at) }}</span>
              </div>
            </div>
          </div>

          <div class="pagination">
            <button
              @click="loadPreviousPage('raw-answers')"
              :disabled="currentPages.rawAnswers <= 1"
              class="page-btn"
            >
              上一页
            </button>
            <span class="page-info">
              第 {{ currentPages.rawAnswers }} 页
            </span>
            <button
              @click="loadNextPage('raw-answers')"
              :disabled="rawAnswers.length < itemsPerPage"
              class="page-btn"
            >
              下一页
            </button>
          </div>
        </div>

        <!-- 专家回答列表 -->
        <div v-if="activeTab === 'expert-answers'" class="content-list">
          <div v-if="loading" class="loading-state">正在加载...</div>
          <div v-else-if="expertAnswers.length === 0" class="empty-state">
            暂无专家回答数据
          </div>
          <div v-else>
            <div
              v-for="answer in expertAnswers"
              :key="answer.id"
              @click="selectExpertAnswer(answer)"
              class="list-item"
              :class="{ selected: stdQaForm.expertAnswerId === answer.id }"
            >
              <div class="item-header">
                <span class="item-id">ID: {{ answer.id }}</span>
                <span class="item-author">专家ID: {{ answer.answered_by }}</span>
              </div>
              <div class="item-content">{{ answer.answer?.substring(0, 200) }}...</div>
              <div class="item-meta">
                <span>问题ID: {{ answer.question_id }}</span>
                <span>{{ formatDate(answer.answered_at) }}</span>
              </div>
            </div>
          </div>

          <div class="pagination">
            <button
              @click="loadPreviousPage('expert-answers')"
              :disabled="currentPages.expertAnswers <= 1"
              class="page-btn"
            >
              上一页
            </button>
            <span class="page-info">
              第 {{ currentPages.expertAnswers }} 页
            </span>
            <button
              @click="loadNextPage('expert-answers')"
              :disabled="expertAnswers.length < itemsPerPage"
              class="page-btn"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 成功消息 -->
    <div v-if="successMessage" class="success-message">
      {{ successMessage }}
    </div>

    <!-- 错误消息 -->
    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { datasetService } from '@/services/datasetService'
import { databaseService } from '@/services/databaseService'
import { formatDate } from '@/utils/formatters'

// 路由
const route = useRoute()
const router = useRouter()

// 响应式数据
const datasetId = computed(() => route.params.datasetId as string)
const currentDataset = ref<any>(null)
const loading = ref(false)
const submitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// 表单数据
const stdQaForm = ref({
  question: '',
  answer: '',
  questionType: 'text',
  rawQuestionId: null as number | null,
  rawAnswerId: null as number | null,
  expertAnswerId: null as number | null
})

const keyPointsText = ref('')

// 选中的项目
const selectedRawQuestion = ref<any>(null)
const selectedRawAnswer = ref<any>(null)
const selectedExpertAnswer = ref<any>(null)

// 浏览面板
const activeTab = ref<'raw-questions' | 'raw-answers' | 'expert-answers'>('raw-questions')
const searchQuery = ref('')
const itemsPerPage = 10

// 数据列表
const rawQuestions = ref<any[]>([])
const rawAnswers = ref<any[]>([])
const expertAnswers = ref<any[]>([])

// 分页
const currentPages = ref({
  rawQuestions: 1,
  rawAnswers: 1,
  expertAnswers: 1
})

// 计算属性
const keyPointsArray = computed(() => {
  return keyPointsText.value
    .split('\n')
    .map(point => point.trim())
    .filter(point => point.length > 0)
})

// 生命周期
onMounted(async () => {
  await loadDataset()
  await loadTabData()
})

// 监听标签页切换
watch(activeTab, () => {
  loadTabData()
})

// 方法
const goBackToDataImport = () => {
  router.push({
    name: 'DataImport',
    query: { datasetId: datasetId.value }
  })
}

const loadDataset = async () => {
  try {
    const response = await datasetService.getDataset(parseInt(datasetId.value))
    currentDataset.value = response
  } catch (error) {
    console.error('Failed to load dataset:', error)
    errorMessage.value = '加载数据集信息失败'
  }
}

const loadTabData = async () => {
  loading.value = true
  try {
    switch (activeTab.value) {
      case 'raw-questions':
        await loadRawQuestions()
        break
      case 'raw-answers':
        await loadRawAnswers()
        break
      case 'expert-answers':
        await loadExpertAnswers()
        break
    }
  } catch (error) {
    console.error('Failed to load data:', error)
    errorMessage.value = '加载数据失败'
  } finally {
    loading.value = false
  }
}

const loadRawQuestions = async () => {
  try {
    let result;
    if (searchQuery.value.trim()) {
      result = await databaseService.searchItems(
        'raw_questions',
        searchQuery.value.trim(),
        (currentPages.value.rawQuestions - 1) * itemsPerPage,
        itemsPerPage
      )
    } else {
      result = await databaseService.getTableData(
        'raw_questions',
        (currentPages.value.rawQuestions - 1) * itemsPerPage,
        itemsPerPage,
        false,
        undefined,
        false
      )
    }
    rawQuestions.value = result.data
  } catch (error) {
    console.error('Failed to load raw questions:', error)
  }
}

const loadRawAnswers = async () => {
  try {
    let result;
    if (searchQuery.value.trim()) {
      result = await databaseService.searchItems(
        'raw_answers',
        searchQuery.value.trim(),
        (currentPages.value.rawAnswers - 1) * itemsPerPage,
        itemsPerPage
      )
    } else {
      result = await databaseService.getTableData(
        'raw_answers',
        (currentPages.value.rawAnswers - 1) * itemsPerPage,
        itemsPerPage,
        false,
        undefined,
        false
      )
    }
    rawAnswers.value = result.data
  } catch (error) {
    console.error('Failed to load raw answers:', error)
  }
}

const loadExpertAnswers = async () => {
  try {
    let result;
    if (searchQuery.value.trim()) {
      result = await databaseService.searchItems(
        'expert_answers',
        searchQuery.value.trim(),
        (currentPages.value.expertAnswers - 1) * itemsPerPage,
        itemsPerPage
      )
    } else {
      result = await databaseService.getTableData(
        'expert_answers',
        (currentPages.value.expertAnswers - 1) * itemsPerPage,
        itemsPerPage,
        false,
        undefined,
        false
      )
    }
    expertAnswers.value = result.data
  } catch (error) {
    console.error('Failed to load expert answers:', error)
  }
}

const performSearch = () => {
  currentPages.value[activeTab.value.replace('-', '') as 'rawQuestions' | 'rawAnswers' | 'expertAnswers'] = 1
  loadTabData()
}

const loadNextPage = (tab: string) => {
  const tabKey = tab.replace('-', '') as 'rawQuestions' | 'rawAnswers' | 'expertAnswers'
  currentPages.value[tabKey]++
  loadTabData()
}

const loadPreviousPage = (tab: string) => {
  const tabKey = tab.replace('-', '') as 'rawQuestions' | 'rawAnswers' | 'expertAnswers'
  if (currentPages.value[tabKey] > 1) {
    currentPages.value[tabKey]--
    loadTabData()
  }
}

// 选择项目
const selectRawQuestion = (question: any) => {
  stdQaForm.value.rawQuestionId = question.id
  selectedRawQuestion.value = question
}

const selectRawAnswer = (answer: any) => {
  stdQaForm.value.rawAnswerId = answer.id
  selectedRawAnswer.value = answer
}

const selectExpertAnswer = (answer: any) => {
  stdQaForm.value.expertAnswerId = answer.id
  selectedExpertAnswer.value = answer
}

// 清除选择
const clearRawQuestion = () => {
  stdQaForm.value.rawQuestionId = null
  selectedRawQuestion.value = null
}

const clearRawAnswer = () => {
  stdQaForm.value.rawAnswerId = null
  selectedRawAnswer.value = null
}

const clearExpertAnswer = () => {
  stdQaForm.value.expertAnswerId = null
  selectedExpertAnswer.value = null
}

// 表单处理
const resetForm = () => {
  stdQaForm.value = {
    question: '',
    answer: '',
    questionType: 'text',
    rawQuestionId: null,
    rawAnswerId: null,
    expertAnswerId: null
  }
  keyPointsText.value = ''
  clearRawQuestion()
  clearRawAnswer()
  clearExpertAnswer()
}

const submitStdQa = async () => {
  if (!stdQaForm.value.question.trim() || !stdQaForm.value.answer.trim()) {
    errorMessage.value = '问题和答案不能为空'
    return
  }

  submitting.value = true
  try {
    const payload = {
      dataset_id: parseInt(datasetId.value),
      question: stdQaForm.value.question.trim(),
      answer: stdQaForm.value.answer.trim(),
      question_type: stdQaForm.value.questionType,
      key_points: keyPointsArray.value.length > 0 ? keyPointsArray.value : undefined,
      raw_question_id: stdQaForm.value.rawQuestionId,
      raw_answer_id: stdQaForm.value.rawAnswerId,
      expert_answer_id: stdQaForm.value.expertAnswerId
    }

    // 调用API创建标准问答对
    await createStdQaPair(payload)
    
    successMessage.value = '标准问答对创建成功！'
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
    
    resetForm()
  } catch (error) {
    console.error('Failed to create standard QA pair:', error)
    errorMessage.value = '创建标准问答对失败，请重试'
  } finally {
    submitting.value = false
  }
}

// 创建标准问答对的API调用
const createStdQaPair = async (payload: any) => {
  const response = await fetch('/api/std-qa/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Failed to create standard QA pair')
  }

  return response.json()
}

// 清除错误消息
const clearError = () => {
  errorMessage.value = ''
}

// 监听错误消息，5秒后自动清除
watch(errorMessage, (newValue) => {
  if (newValue) {
    setTimeout(() => {
      errorMessage.value = ''
    }, 5000)
  }
})
</script>

<style scoped>
.manual-creation-container {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.back-btn:hover {
  background: #f8f9fa;
}

.title-section h2 {
  margin: 0 0 5px 0;
  color: #333;
}

.subtitle {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.creation-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  height: calc(100vh - 140px);
}

.creation-form-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.browse-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.form-section {
  margin-bottom: 30px;
}

.form-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  border-bottom: 2px solid #007bff;
  padding-bottom: 10px;
}

.form-section h4 {
  margin: 20px 0 15px 0;
  color: #555;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-hint {
  color: #666;
  font-size: 12px;
  margin-top: 5px;
}

.reference-section {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

.selected-reference {
  margin-bottom: 10px;
}

.reference-item {
  background: white;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.reference-item strong {
  color: #007bff;
}

.reference-item p {
  margin: 5px 0;
  color: #333;
}

.clear-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
}

.clear-btn:hover {
  background: #c82333;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.panel-tabs {
  display: flex;
  border-bottom: 1px solid #dee2e6;
}

.tab-btn {
  flex: 1;
  padding: 15px;
  border: none;
  background: white;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f8f9fa;
}

.tab-btn.active {
  border-bottom-color: #007bff;
  color: #007bff;
  font-weight: 600;
}

.search-section {
  padding: 15px;
  border-bottom: 1px solid #dee2e6;
}

.search-controls {
  display: flex;
  gap: 10px;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.search-btn:hover {
  background: #0056b3;
}

.content-list {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.list-item {
  padding: 15px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.list-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.1);
}

.list-item.selected {
  border-color: #007bff;
  background: #e3f2fd;
}

.item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  color: #666;
}

.item-id {
  font-weight: 600;
}

.item-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  line-height: 1.4;
}

.item-body, .item-content {
  color: #555;
  line-height: 1.4;
  margin-bottom: 8px;
}

.item-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #666;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  padding: 15px;
  border-top: 1px solid #dee2e6;
}

.page-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.success-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #d4edda;
  color: #155724;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #c3e6cb;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #f5c6cb;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

@media (max-width: 1200px) {
  .creation-layout {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .browse-panel {
    height: 600px;
  }
}
</style>

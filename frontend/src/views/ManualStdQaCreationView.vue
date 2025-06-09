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
            </div>            <div class="form-group">
              <label for="questionType">问题类型</label>
              <select id="questionType" v-model="stdQaForm.questionType" class="form-control">
                <option value="choice">选择题</option>
                <option value="text">问答题</option>
              </select>
            </div>

            <!-- 动态题目内容区域 -->
            <div v-if="stdQaForm.questionType === 'choice'" class="form-group">
              <label>选择题选项</label>
              <div class="choice-options">
                <div v-for="(option, index) in choiceOptions" :key="index" class="option-input">
                  <input 
                    v-model="option.text" 
                    :placeholder="`选项 ${String.fromCharCode(65 + index)}`"
                    class="form-control option-text"
                  />
                  <label class="correct-option">
                    <input 
                      type="radio" 
                      :value="index" 
                      v-model="correctOptionIndex"
                      name="correctOption"
                    />
                    正确答案
                  </label>
                  <button type="button" @click="removeOption(index)" class="remove-option-btn" v-if="choiceOptions.length > 2">
                    ×
                  </button>
                </div>
                <button type="button" @click="addOption" class="add-option-btn" v-if="choiceOptions.length < 6">
                  + 添加选项
                </button>
              </div>
            </div>            <!-- 得分点输入 - 仅对问答题显示 -->
            <div v-if="stdQaForm.questionType === 'text'" class="form-group">
              <label for="keyPoints">关键点/得分点 (可选)</label>
              <div class="key-points-input">
                <div v-for="(point, index) in keyPoints" :key="index" class="key-point-item">
                  <input 
                    v-model="point.content"
                    :placeholder="`得分点 ${index + 1}`"
                    class="form-control point-content"
                  />
                  <button type="button" @click="removeKeyPoint(index)" class="remove-point-btn" v-if="keyPoints.length > 1">
                    ×
                  </button>
                </div>
                <button type="button" @click="addKeyPoint" class="add-point-btn">
                  + 添加得分点
                </button>
                <small class="form-hint">每个得分点包含具体内容，顺序按添加先后排列</small>
              </div>
            </div>

            <!-- 选择题得分点提示 -->
            <div v-if="stdQaForm.questionType === 'choice'" class="form-group">
              <label>得分点设置</label>
              <div class="scoring-info">
                <p class="info-text">
                  <i class="info-icon">ℹ️</i>
                  选择题不存在得分点。
                </p>
              </div>
            </div>            <!-- 标签管理 -->
            <div class="form-group">
              <label for="tags">标签</label>
              <div class="tags-section">
                <!-- 显示从关联原始问题获取的标签 -->
                <div v-if="inheritedTags.length > 0" class="inherited-tags">
                  <h5>从关联原始问题获取的标签：</h5>
                  <div class="tag-list">
                    <span v-for="tag in inheritedTags" :key="tag" class="tag inherited-tag">
                      {{ tag }}
                    </span>
                  </div>
                </div>
                
                <!-- 用户额外添加的标签 -->
                <div class="custom-tags">
                  <h5>额外标签：</h5>
                  <div class="tag-input-section">
                    <input
                      v-model="newTag"
                      @keyup.enter="addTag"
                      placeholder="输入标签后按回车添加"
                      class="form-control tag-input"
                    />
                    <button type="button" @click="addTag" class="add-tag-btn">添加标签</button>
                  </div>
                  <div v-if="stdQaForm.customTags.length > 0" class="tag-list">
                    <span v-for="(tag, index) in stdQaForm.customTags" :key="index" class="tag custom-tag">
                      {{ tag }}
                      <button type="button" @click="removeTag(index)" class="remove-tag-btn">×</button>
                    </span>
                  </div>
                </div>
                
                <!-- 最终标签预览 -->
                <div v-if="allTags.length > 0" class="final-tags-preview">
                  <h5>最终标签（包含继承 + 自定义）：</h5>
                  <div class="tag-list">
                    <span v-for="tag in allTags" :key="tag" class="tag final-tag">
                      {{ tag }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 关联的原始问题（必填） -->
            <div class="form-section">
              <h4>关联原始问题 *</h4>
              <div class="reference-section">
                <div v-if="stdQaForm.rawQuestionIds.length > 0" class="selected-reference">
                  <div v-for="questionId in stdQaForm.rawQuestionIds" :key="questionId" class="reference-item">
                    <strong>已选择原始问题 ID: {{ questionId }}</strong>
                    <p>{{ getRawQuestionTitle(questionId) }}</p>
                    <button type="button" @click="removeRawQuestion(questionId)" class="clear-btn">移除</button>
                  </div>
                </div>
                <div v-else class="empty-reference">
                  <p class="warning-text">⚠️ 标准问题必须关联至少一个原始问题</p>
                </div>
              </div>
            </div><!-- 关联的原始回答和专家回答（可选） -->
            <div class="form-section">
              <h4>关联原始回答 (可选)</h4>
              <div class="reference-section">
                <div v-if="stdQaForm.rawAnswerIds.length > 0" class="selected-reference">
                  <div v-for="answerId in stdQaForm.rawAnswerIds" :key="answerId" class="reference-item">
                    <strong>已选择原始回答 ID: {{ answerId }}</strong>
                    <p>{{ getRawAnswerContent(answerId) }}</p>
                    <button type="button" @click="removeRawAnswer(answerId)" class="clear-btn">移除</button>
                  </div>
                </div>
                <div v-else class="empty-reference">
                  <p class="info-text">暂未选择原始回答</p>
                </div>
              </div>
            </div>

            <div class="form-section">
              <h4>关联专家回答 (可选)</h4>
              <div class="reference-section">
                <div v-if="stdQaForm.expertAnswerIds.length > 0" class="selected-reference">
                  <div v-for="answerId in stdQaForm.expertAnswerIds" :key="answerId" class="reference-item">
                    <strong>已选择专家回答 ID: {{ answerId }}</strong>
                    <p>{{ getExpertAnswerContent(answerId) }}</p>
                    <button type="button" @click="removeExpertAnswer(answerId)" class="clear-btn">移除</button>
                  </div>
                </div>
                <div v-else class="empty-reference">
                  <p class="info-text">暂未选择专家回答</p>
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
              :key="question.id"              @click="selectRawQuestion(question)"
              class="list-item"
              :class="{ selected: stdQaForm.rawQuestionIds.includes(question.id) }"
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
              第 {{ currentPages.rawQuestions }} 页 / 共 {{ totalPages.rawQuestions }} 页
            </span>
            <button
              @click="loadNextPage('raw-questions')"
              :disabled="currentPages.rawQuestions >= totalPages.rawQuestions"
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
          <div v-else>            <div
              v-for="answer in rawAnswers"
              :key="answer.id"
              @click="selectRawAnswer(answer)"
              class="list-item"
              :class="{ selected: stdQaForm.rawAnswerIds.includes(answer.id) }"
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
          </div>          <div class="pagination">
            <button
              @click="loadPreviousPage('raw-answers')"
              :disabled="currentPages.rawAnswers <= 1"
              class="page-btn"
            >
              上一页
            </button>
            <span class="page-info">
              第 {{ currentPages.rawAnswers }} 页 / 共 {{ totalPages.rawAnswers }} 页
            </span>
            <button
              @click="loadNextPage('raw-answers')"
              :disabled="currentPages.rawAnswers >= totalPages.rawAnswers"
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
              :class="{ selected: stdQaForm.expertAnswerIds.includes(answer.id) }"
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
          </div>          <div class="pagination">
            <button
              @click="loadPreviousPage('expert-answers')"
              :disabled="currentPages.expertAnswers <= 1"
              class="page-btn"
            >
              上一页
            </button>
            <span class="page-info">
              第 {{ currentPages.expertAnswers }} 页 / 共 {{ totalPages.expertAnswers }} 页
            </span>
            <button
              @click="loadNextPage('expert-answers')"
              :disabled="currentPages.expertAnswers >= totalPages.expertAnswers"
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
import { apiClient } from '@/services/api'
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
  rawQuestionIds: [] as number[], 
  rawAnswerIds: [] as number[], 
  expertAnswerIds: [] as number[],
  customTags: [] as string[] // 用户自定义的额外标签
})

// 标签相关数据
const newTag = ref('')
const inheritedTags = ref<string[]>([]) // 从关联原始问题继承的标签

// 计算所有标签（继承的 + 自定义的）
const allTags = computed(() => {
  const combined = [...inheritedTags.value, ...stdQaForm.value.customTags]
  return [...new Set(combined)] // 去重
})

const keyPointsText = ref('')

// 得分点数据
const keyPoints = ref([
  { content: '' }
])

// 选择题和填空题的数据
const choiceOptions = ref([
  { text: '' },
  { text: '' }
])
const correctOptionIndex = ref(0)

// 选中的项目
const selectedRawQuestions = ref<any[]>([]) // 改为数组
const selectedRawAnswers = ref<any[]>([]) // 改为数组，支持多个原始回答
const selectedExpertAnswers = ref<any[]>([]) // 改为数组，支持多个专家回答

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

const totalCounts = ref({
  rawQuestions: 0,
  rawAnswers: 0,
  expertAnswers: 0
})

const tabKeyMap = {
  'raw-questions': 'rawQuestions',
  'raw-answers':   'rawAnswers',
  'expert-answers':'expertAnswers'
} as const

// 计算属性
const totalPages = computed(() => ({
  rawQuestions: Math.ceil(totalCounts.value.rawQuestions / itemsPerPage),
  rawAnswers: Math.ceil(totalCounts.value.rawAnswers / itemsPerPage),
  expertAnswers: Math.ceil(totalCounts.value.expertAnswers / itemsPerPage)
}))

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
    totalCounts.value.rawQuestions = result.total
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
    totalCounts.value.rawAnswers = result.total
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
    totalCounts.value.expertAnswers = result.total
  } catch (error) {
    console.error('Failed to load expert answers:', error)
  }
}

const performSearch = () => {
    const key = tabKeyMap[activeTab.value]
    currentPages.value[key] = 1
    loadTabData()
}

const loadNextPage = (tab: keyof typeof tabKeyMap) => {
  const key = tabKeyMap[tab]
  currentPages.value[key]++

  if (tab === 'raw-questions')   loadRawQuestions()
  if (tab === 'raw-answers')     loadRawAnswers()
  if (tab === 'expert-answers')  loadExpertAnswers()
}

const loadPreviousPage = (tab: keyof typeof tabKeyMap) => {
  const key = tabKeyMap[tab]
  if (currentPages.value[key] > 1) {
    currentPages.value[key]--
    if (tab === 'raw-questions')   loadRawQuestions()
    if (tab === 'raw-answers')     loadRawAnswers()
    if (tab === 'expert-answers')  loadExpertAnswers()
  }
}

// 选择项目
const selectRawQuestion = (question: any) => {
  if (!stdQaForm.value.rawQuestionIds.includes(question.id)) {
    stdQaForm.value.rawQuestionIds.push(question.id)
    selectedRawQuestions.value.push(question)
    // 更新继承的标签
    updateInheritedTags()
  }
}

const selectRawAnswer = (answer: any) => {
  if (!stdQaForm.value.rawAnswerIds.includes(answer.id)) {
    stdQaForm.value.rawAnswerIds.push(answer.id)
    selectedRawAnswers.value.push(answer)
  }
}

const selectExpertAnswer = (answer: any) => {
  if (!stdQaForm.value.expertAnswerIds.includes(answer.id)) {
    stdQaForm.value.expertAnswerIds.push(answer.id)
    selectedExpertAnswers.value.push(answer)
  }
}

// 清除选择
const removeRawQuestion = (questionId: number) => {
  const index = stdQaForm.value.rawQuestionIds.indexOf(questionId)
  if (index > -1) {
    stdQaForm.value.rawQuestionIds.splice(index, 1)
    const selectedIndex = selectedRawQuestions.value.findIndex(q => q.id === questionId)
    if (selectedIndex > -1) {
      selectedRawQuestions.value.splice(selectedIndex, 1)
    }
    // 更新继承的标签
    updateInheritedTags()
  }
}

const removeRawAnswer = (answerId: number) => {
  const index = stdQaForm.value.rawAnswerIds.indexOf(answerId)
  if (index > -1) {
    stdQaForm.value.rawAnswerIds.splice(index, 1)
    const selectedIndex = selectedRawAnswers.value.findIndex(a => a.id === answerId)
    if (selectedIndex > -1) {
      selectedRawAnswers.value.splice(selectedIndex, 1)
    }
  }
}

const removeExpertAnswer = (answerId: number) => {
  const index = stdQaForm.value.expertAnswerIds.indexOf(answerId)
  if (index > -1) {
    stdQaForm.value.expertAnswerIds.splice(index, 1)
    const selectedIndex = selectedExpertAnswers.value.findIndex(a => a.id === answerId)
    if (selectedIndex > -1) {
      selectedExpertAnswers.value.splice(selectedIndex, 1)
    }
  }
}

// 获取原始问题标题
const getRawQuestionTitle = (questionId: number) => {
  const question = selectedRawQuestions.value.find(q => q.id === questionId)
  return question ? question.title || question.body?.substring(0, 50) + '...' : `问题 ID: ${questionId}`
}

// 获取原始回答内容
const getRawAnswerContent = (answerId: number) => {
  const answer = selectedRawAnswers.value.find(a => a.id === answerId)
  return answer ? answer.answer?.substring(0, 100) + '...' : `回答 ID: ${answerId}`
}

// 获取专家回答内容
const getExpertAnswerContent = (answerId: number) => {
  const answer = selectedExpertAnswers.value.find(a => a.id === answerId)
  return answer ? answer.answer?.substring(0, 100) + '...' : `专家回答 ID: ${answerId}`
}

// 选择题方法
const addOption = () => {
  if (choiceOptions.value.length < 6) {
    choiceOptions.value.push({ text: '' })
  }
}

const removeOption = (index: number) => {
  if (choiceOptions.value.length > 2) {
    choiceOptions.value.splice(index, 1)
    if (correctOptionIndex.value >= choiceOptions.value.length) {
      correctOptionIndex.value = 0
    }
  }
}

// 得分点方法
const addKeyPoint = () => {
  keyPoints.value.push({ content: '' })
}

const removeKeyPoint = (index: number) => {
  if (keyPoints.value.length > 1) {
    keyPoints.value.splice(index, 1)
  }
}

// 标签管理方法
const addTag = () => {
  const tag = newTag.value.trim()
  if (tag && !stdQaForm.value.customTags.includes(tag) && !inheritedTags.value.includes(tag)) {
    stdQaForm.value.customTags.push(tag)
    newTag.value = ''
  }
}

const removeTag = (index: number) => {
  stdQaForm.value.customTags.splice(index, 1)
}

// 更新继承的标签（当选择原始问题时调用）
const updateInheritedTags = async () => {
  const tagSet = new Set<string>()
  
  for (const questionId of stdQaForm.value.rawQuestionIds) {
    try {
      const question = selectedRawQuestions.value.find(q => q.id === questionId)
      if (question && question.tags) {
        question.tags.forEach((tag: string) => tagSet.add(tag))
      }
    } catch (error) {
      console.error(`Error getting tags for question ${questionId}:`, error)
    }
  }
  
  inheritedTags.value = Array.from(tagSet)
}

// 表单处理
const resetForm = () => {
  stdQaForm.value = {
    question: '',
    answer: '',
    questionType: 'text', // 默认为问答题
    rawQuestionIds: [],
    rawAnswerIds: [],
    expertAnswerIds: [],
    customTags: [] // 重置自定义标签
  }
  keyPointsText.value = ''
  keyPoints.value = [{ content: '' }]
  selectedRawQuestions.value = []
  selectedRawAnswers.value = []
  selectedExpertAnswers.value = []
  
  // 重置选择题数据
  choiceOptions.value = [{ text: '' }, { text: '' }]
  correctOptionIndex.value = 0
  
  // 重置标签相关数据
  newTag.value = ''
  inheritedTags.value = []
  
  // 重置消息
  successMessage.value = ''
  errorMessage.value = ''
}

const submitStdQa = async () => {
  if (!stdQaForm.value.question.trim() || !stdQaForm.value.answer.trim()) {
    errorMessage.value = '问题和答案不能为空'
    return
  }

  if (stdQaForm.value.rawQuestionIds.length === 0) {
    errorMessage.value = '标准问题必须关联至少一个原始问题'
    return
  }

  submitting.value = true
  try {    // 根据问题类型处理答案格式和得分点
    let finalAnswer = stdQaForm.value.answer.trim()
    let finalKeyPoints = keyPoints.value.filter(point => point.content.trim()).map(point => ({
      content: point.content.trim()
    }))
      // 根据问题类型处理问题和答案格式
    let finalQuestion = stdQaForm.value.question.trim()
      if (stdQaForm.value.questionType === 'choice') {
      const validOptions = choiceOptions.value.filter(opt => opt.text.trim())
      if (validOptions.length < 2) {
        errorMessage.value = '选择题至少需要2个选项'
        return
      }
      const optionsText = validOptions.map((opt, index) => 
        `${String.fromCharCode(65 + index)}. ${opt.text.trim()}`
      ).join('; ')
      
      // 将选项放到问题中，添加提示文本
      finalQuestion = `${stdQaForm.value.question.trim()}\n\nThe choices are: ${optionsText}`
      
      // 答案只存储正确选项
      const correctOption = String.fromCharCode(65 + correctOptionIndex.value)
      finalAnswer = correctOption
      
      // 对于选择题，不设置得分点，只有answer
      finalKeyPoints = []
    }        
    
    const payload = {
      dataset_id: parseInt(datasetId.value),
      question: finalQuestion,
      answer: finalAnswer,
      question_type: stdQaForm.value.questionType,
      key_points: finalKeyPoints,
      raw_question_ids: stdQaForm.value.rawQuestionIds, 
      raw_answer_ids: stdQaForm.value.rawAnswerIds, 
      expert_answer_ids: stdQaForm.value.expertAnswerIds, 
      tags: stdQaForm.value.customTags 
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
  const response = await apiClient.post('/std-qa/create', payload)
  return response.data
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

.choice-options {
  margin-top: 10px;
}

.option-input {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}

.option-text {
  flex: 1;
}

.correct-option {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #007bff;
  font-size: 14px;
  white-space: nowrap;
}

.correct-option input[type="radio"] {
  margin: 0;
}

.remove-option-btn, .remove-blank-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
}

.remove-option-btn:hover, .remove-blank-btn:hover {
  background: #c82333;
}

.add-option-btn, .add-blank-btn {
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

.add-option-btn:hover, .add-blank-btn:hover {
  background: #218838;
}

.fill-blank-answers {
  margin-top: 10px;
}

.blank-input {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}

.blank-input .form-control {
  flex: 1;
}

.empty-reference {
  text-align: center;
  padding: 20px;
}

.warning-text {
  color: #856404;
  background: #fff3cd;
  border: 1px solid #ffeeba;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
}

.key-point-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}

.point-content {
  flex: 1;
}

.remove-point-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
}

.remove-point-btn:hover {
  background: #c82333;
}

.add-point-btn {
  background: #17a2b8;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

.add-point-btn:hover {
  background: #138496;
}

.scoring-info {
  background: #e7f3ff;
  border: 1px solid #b8daff;
  border-radius: 4px;
  padding: 12px;
  margin-top: 8px;
}

.info-text {
  margin: 0;
  color: #0c5460;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-icon {
  font-size: 16px;
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

<template>
  <div class="raw-question-management">
    <div class="header">
      <h1>原始问题池管理</h1>
      <p class="subtitle">管理本地原始问题和回答，创建标准问答对</p>
    </div>

    <div class="toolbar">
      <el-button type="primary" @click="addNewQuestion">
        <el-icon><Plus /></el-icon>
        添加问题
      </el-button>
      <el-button 
        :disabled="selectedQuestions.size === 0" 
        @click="deleteSelectedQuestions"
      >
        删除选中
      </el-button>
      <el-button 
        :disabled="selectedItems.questions.size === 0 && selectedItems.rawAnswers.size === 0 && selectedItems.expertAnswers.size === 0"
        @click="createStandardQA"
      >
        创建标准问答
      </el-button>
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索问题..."
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <div class="content">
      <div class="question-list" v-loading="store.isLoading">
        <div v-if="filteredQuestions.length === 0" class="empty-state">
          <el-empty description="暂无问题数据">
            <el-button type="primary" @click="addNewQuestion">添加第一个问题</el-button>
          </el-empty>
        </div>
        
        <div v-else>
          <div 
            v-for="question in filteredQuestions" 
            :key="question.id"
            class="question-card"
          >
            <div class="question-header">
              <el-checkbox 
                :model-value="selectedQuestions.has(question.id)"
                @change="toggleQuestionSelection(question.id)"
              />
              <div class="question-info">
                <h3 @click="editQuestion(question)">{{ question.title }}</h3>
                <div class="meta">
                  <span class="author">{{ question.author || '匿名' }}</span>
                  <span class="date">{{ formatDate(question.issued_at) }}</span>
                  <span class="stats">
                    <el-icon><View /></el-icon>{{ question.view_count || 0 }}
                    <el-icon><Star /></el-icon>{{ question.vote_count || 0 }}
                  </span>
                  <div class="tags" v-if="question.tags?.length">
                    <el-tag v-for="tag in question.tags" :key="tag" size="small">{{ tag }}</el-tag>
                  </div>
                </div>
              </div>
              <div class="actions">
                <el-button size="small" @click="editQuestion(question)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteQuestion(question)">删除</el-button>
              </div>
            </div>

            <div class="question-body" v-if="question.body">
              <p>{{ truncateText(question.body, 200) }}</p>
            </div>

            <!-- 原始回答列表 -->
            <div class="answers-section" v-if="question.raw_answers?.length">
              <h4>原始回答 ({{ question.raw_answers.length }})</h4>
              <div 
                v-for="answer in question.raw_answers" 
                :key="answer.id"
                class="answer-item"
              >
                <el-checkbox 
                  :model-value="selectedItems.rawAnswers.has(answer.id)"
                  @change="toggleAnswerSelection('rawAnswer', answer.id)"
                />
                <div class="answer-content">
                  <p>{{ truncateText(answer.content, 150) }}</p>
                  <div class="answer-meta">
                    <span>{{ answer.author || '匿名' }}</span>
                    <span>{{ formatDate(answer.answered_at) }}</span>
                    <span v-if="answer.vote_count">
                      <el-icon><Star /></el-icon>{{ answer.vote_count }}
                    </span>
                  </div>
                </div>
                <div class="answer-actions">
                  <el-button size="small" @click="editAnswer(answer, 'raw')">编辑</el-button>
                  <el-button size="small" type="danger" @click="deleteAnswer(answer, question.id, 'raw')">删除</el-button>
                </div>
              </div>
              <el-button size="small" type="text" @click="addAnswer(question.id, 'raw')">
                <el-icon><Plus /></el-icon>添加原始回答
              </el-button>
            </div>

            <!-- 专家回答列表 -->
            <div class="answers-section" v-if="question.expert_answers?.length">
              <h4>专家回答 ({{ question.expert_answers.length }})</h4>
              <div 
                v-for="answer in question.expert_answers" 
                :key="answer.id"
                class="answer-item expert"
              >
                <el-checkbox 
                  :model-value="selectedItems.expertAnswers.has(answer.id)"
                  @change="toggleAnswerSelection('expertAnswer', answer.id)"
                />
                <div class="answer-content">
                  <p>{{ truncateText(answer.content, 150) }}</p>
                  <div class="answer-meta">
                    <span>{{ answer.author || '匿名' }}</span>
                    <span>{{ answer.source }}</span>
                    <span>{{ formatDate(answer.created_at) }}</span>
                  </div>
                </div>
                <div class="answer-actions">
                  <el-button size="small" @click="editAnswer(answer, 'expert')">编辑</el-button>
                  <el-button size="small" type="danger" @click="deleteAnswer(answer, question.id, 'expert')">删除</el-button>
                </div>
              </div>
              <el-button size="small" type="text" @click="addAnswer(question.id, 'expert')">
                <el-icon><Plus /></el-icon>添加专家回答
              </el-button>
            </div>

            <!-- 如果没有回答 -->
            <div v-if="!question.raw_answers?.length && !question.expert_answers?.length" class="no-answers">
              <p>暂无回答</p>
              <div class="add-answer-buttons">
                <el-button size="small" @click="addAnswer(question.id, 'raw')">添加原始回答</el-button>
                <el-button size="small" @click="addAnswer(question.id, 'expert')">添加专家回答</el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="store.hasMore && !store.isLoading" class="load-more">
          <el-button @click="store.loadMoreQuestions()">加载更多</el-button>
        </div>
      </div>
    </div>

    <!-- 撤销删除提示 -->
    <div v-if="store.recentlyDeleted.length > 0" class="undo-bar">
      <span>已删除 {{ store.recentlyDeleted.length }} 项</span>
      <el-button size="small" type="text" @click="undoDelete">撤销</el-button>
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
      :selected-items="selectedItems"
      :questions="store.questions"
      @created="handleStandardQACreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRawQuestionStore } from '@/store/rawQuestionStore'
import { RawQuestion } from '@/types/questions'
import { RawAnswer, ExpertAnswer } from '@/types/answers'
import QuestionEditDialog from '@/components/QuestionEditDialog.vue'
import AnswerEditDialog from '@/components/AnswerEditDialog.vue'
import StandardQADialog from '@/components/StandardQADialog.vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, View, Star } from '@element-plus/icons-vue'

const store = useRawQuestionStore()

// 状态管理
const searchQuery = ref('')
const questionDialogVisible = ref(false)
const answerDialogVisible = ref(false)
const standardQADialogVisible = ref(false)
const currentQuestion = ref<RawQuestion | null>(null)
const currentAnswer = ref<RawAnswer | ExpertAnswer | null>(null)
const currentAnswerType = ref<'raw' | 'expert'>('raw')

// 计算属性
const selectedQuestions = computed(() => store.selectedItemIds.questions)
const selectedItems = computed(() => store.selectedItemIds)

const filteredQuestions = computed(() => {
  if (!searchQuery.value) return store.questions
  const query = searchQuery.value.toLowerCase()
  return store.questions.filter(q => 
    q.title.toLowerCase().includes(query) ||
    q.body?.toLowerCase().includes(query) ||
    q.tags?.some(tag => tag.toLowerCase().includes(query))
  )
})

// 方法
const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

const toggleQuestionSelection = (id: number) => {
  store.toggleSelection('question', id)
}

const toggleAnswerSelection = (type: 'rawAnswer' | 'expertAnswer', id: number) => {
  store.toggleSelection(type, id)
}

const addNewQuestion = () => {
  currentQuestion.value = null
  questionDialogVisible.value = true
}

const editQuestion = (question: RawQuestion) => {
  currentQuestion.value = question
  questionDialogVisible.value = true
}

const deleteQuestion = (question: RawQuestion) => {
  store.deleteQuestion(question)
  ElMessage.success('问题已删除')
}

const deleteSelectedQuestions = () => {
  const count = selectedQuestions.value.size
  store.deleteSelectedQuestions()
  ElMessage.success(`已删除 ${count} 个问题`)
}

const addAnswer = (questionId: number, type: 'raw' | 'expert') => {
  currentAnswer.value = null
  currentAnswerType.value = type
  answerDialogVisible.value = true
}

const editAnswer = (answer: RawAnswer | ExpertAnswer, type: 'raw' | 'expert') => {
  currentAnswer.value = answer
  currentAnswerType.value = type
  answerDialogVisible.value = true
}

const deleteAnswer = (answer: RawAnswer | ExpertAnswer, questionId: number, type: 'raw' | 'expert') => {
  if (type === 'raw') {
    store.deleteRawAnswer(answer as RawAnswer, questionId)
  } else {
    store.deleteExpertAnswer(answer as ExpertAnswer, questionId)
  }
  ElMessage.success('回答已删除')
}

const createStandardQA = () => {
  standardQADialogVisible.value = true
}

const handleQuestionSave = () => {
  ElMessage.success('问题已保存')
  questionDialogVisible.value = false
}

const handleAnswerSave = () => {
  ElMessage.success('回答已保存')
  answerDialogVisible.value = false
}

const handleStandardQACreated = () => {
  ElMessage.success('标准问答已创建')
  standardQADialogVisible.value = false
  store.clearSelections()
}

const undoDelete = () => {
  store.undoLastDelete()
  ElMessage.success('删除已撤销')
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
  store.loadInitialQuestions()
})
</script>

<style scoped>
.raw-question-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 20px;
}

.header h1 {
  margin: 0 0 8px 0;
  color: #303133;
}

.subtitle {
  color: #606266;
  margin: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-box {
  margin-left: auto;
  width: 300px;
}

.question-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: white;
}

.question-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.question-info {
  flex: 1;
}

.question-info h3 {
  margin: 0 0 8px 0;
  color: #409eff;
  cursor: pointer;
  font-size: 16px;
}

.question-info h3:hover {
  text-decoration: underline;
}

.meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: #909399;
  flex-wrap: wrap;
}

.stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.question-body {
  margin: 12px 0;
  color: #606266;
  line-height: 1.5;
}

.answers-section {
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.answers-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
}

.answer-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  margin-bottom: 8px;
}

.answer-item.expert {
  background-color: #fdf6ec;
  border-color: #fcdcb6;
}

.answer-content {
  flex: 1;
}

.answer-content p {
  margin: 0 0 8px 0;
  color: #606266;
  line-height: 1.4;
}

.answer-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 12px;
  align-items: center;
}

.no-answers {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.add-answer-buttons {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  justify-content: center;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}

.undo-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #303133;
  color: white;
  padding: 12px 20px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 1000;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}
</style>
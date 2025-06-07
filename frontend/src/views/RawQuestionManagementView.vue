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
    </div>    <!-- 操作栏 -->
    <div class="actions-bar">      <div class="bulk-actions" v-if="isNotOverviewMode">        <button 
          @click="selectAll" 
          class="action-btn"
          :disabled="filteredQuestions.length === 0"
        >
          {{ selectedItems.length === filteredQuestions.length ? "取消全选" : "全选" }}
        </button>
        <!-- 概览模式禁用批量删除和创建标准问答 -->        <button 
          v-if="isNotOverviewMode"
          @click="deleteSelectedQuestions" 
          class="action-btn danger"
          :disabled="selectedItems.length === 0"
        >
          批量删除 ({{ selectedItems.length }})
        </button>        <button 
          v-if="isQuestionsMode"
          @click="createStandardQA" 
          class="action-btn success"
          :disabled="selectedItems.length === 0"
        >
          创建标准问答
        </button>
      </div>
      
      <!-- 概览模式下的提示信息 -->
      <div class="overview-info" v-if="isOverviewMode">
        <span class="info-text">概览模式 - 仅供浏览</span>
      </div><div class="view-options">
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
        <select v-model="itemsPerPage" @change="() => loadData()" class="per-page-select">
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
            <th v-if="isNotOverviewMode" class="checkbox-col">
              <input 
                type="checkbox" 
                :checked="selectedItems.length === filteredQuestions.length && filteredQuestions.length > 0"
                @change="selectAll"
              />
            </th>              <!-- 概览模式简化表头 -->
            <template v-if="isOverviewMode">
              <th class="id-col">ID</th>
              <th class="title-col">原始问题</th>
              <th class="answers-col">原始回答</th>
              <th class="expert-answers-col">专家回答</th>
              <th class="actions-col">操作</th>
            </template>
              <!-- 其他模式的表头 -->
            <template v-else>
              <th class="id-col">ID</th>
              <th class="title-col">                <span v-if="isQuestionsMode">标题</span>
                <span v-else-if="isRawAnswersMode">原始回答内容</span>
                <span v-else-if="isExpertAnswersMode">专家回答内容</span>
              </th>
              <th class="author-col">作者</th>
              <th v-if="isRawAnswersMode || isExpertAnswersMode" class="question-col">关联问题</th>
              <th v-if="!isExpertAnswersMode" class="stats-col">统计</th>
              <th class="tags-col">标签</th>
              <th class="date-col">创建时间</th>
              <th class="actions-col">操作</th>
            </template>
          </tr>
        </thead>        <tbody>          
          <tr v-for="question in paginatedQuestions" :key="question.id" class="data-row">            <!-- 概览模式的简化行 -->
            <template v-if="isOverviewMode">
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
                    <div class="answer-preview">{{ truncateText(question.raw_answers[0].answer || '', 60) }}</div>
                    <div v-if="question.raw_answers.length > 1" class="more-answers">+{{ question.raw_answers.length - 1 }}个</div>
                  </div>
                  <div v-else class="no-answers">暂无原始回答</div>
                </div>
              </td>

              <td class="expert-answers-col">
                <div class="answers-content">
                  <div v-if="question.expert_answers && question.expert_answers.length > 0" class="answer-group">
                    <div class="answer-count">{{ question.expert_answers.length }}个专家回答</div>
                    <div class="answer-preview">{{ truncateText(question.expert_answers[0].answer || '', 60) }}</div>
                    <div v-if="question.expert_answers.length > 1" class="more-answers">+{{ question.expert_answers.length - 1 }}个</div>
                  </div>
                  <div v-else class="no-answers">暂无专家回答</div>
                </div>
              </td>
              <td class="actions-col">
                <div class="row-actions">
                  <button 
                    @click.stop="viewQuestion(question)" 
                    class="action-btn small"
                    title="查看详情"
                  >
                    👁️
                  </button>
                </div>
              </td>
            </template>
            
            <!-- 其他模式的完整行 -->
            <template v-else>
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
                  <div class="title-text" @click="viewQuestion(question)" :title="question.title">
                    {{ question.title }}
                  </div>
                  <div v-if="question.body" class="body-preview" :title="question.body">
                    {{ truncateText(question.body, 50) }}
                  </div>
                </div>
              </td>
              <td class="author-col">
                <span class="truncate-text" :title="question.author || '匿名'">
                  {{ question.author || '匿名' }}
                </span>              </td>
              
              <!-- 非概览模式下显示关联问题信息 -->
              <td v-if="isRawAnswersMode || isExpertAnswersMode" class="question-col">
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
              
              <!-- 只在非专家回答模式下显示统计列 -->
              <td v-if="!isExpertAnswersMode" class="stats-col">                
                <div class="stats-content">                  
                  <div class="stats-info">                    <!-- 概览和原始问题模式显示浏览和点赞 -->
                    <template v-if="isOverviewOrQuestions">
                      <span v-if="question.views !== undefined && question.views !== null" class="stats-item">👁 {{ question.views }}</span>
                      <span v-if="question.votes !== undefined && question.votes !== null" class="stats-item">⭐ {{ question.votes }}</span>
                    </template>                    <!-- 原始回答模式显示upvotes数量 -->
                    <template v-else-if="isRawAnswersMode">
                      <span v-if="question.original_data && question.original_data.score !== undefined && question.original_data.score !== null" class="stats-item">👍 {{ question.original_data.score }}</span>
                      <span v-else-if="question.votes !== undefined && question.votes !== null" class="stats-item">👍 {{ question.votes }}</span>
                      <span v-else class="stats-item">👍 0</span>
                    </template>
                  </div>
                </div>
              </td>              
              <td class="tags-col">
                <div class="tags-content">
                  <span 
                    v-for="tag in formatTags(question.tags)?.slice(0, 2)" 
                    :key="tag" 
                    class="tag"
                    :title="formatTags(question.tags)?.join(', ')"
                  >
                    {{ tag }}
                  </span>
                  <span v-if="formatTags(question.tags) && formatTags(question.tags).length > 2" class="tag">
                    +{{ formatTags(question.tags).length - 2 }}
                  </span>
                </div>
              </td>
              <td class="date-col">
                <span class="truncate-text" :title="formatDate(question.issued_at || question.created_at)">
                  {{ formatDate(question.issued_at || question.created_at) }}
                </span>
              </td>              
              <td class="actions-col">
                <div class="row-actions">
                  <button 
                    @click.stop="viewQuestion(question)" 
                    class="action-btn small"
                    title="查看详情"
                  >
                    👁️                  
                  </button>                  <!-- 概览模式只允许查看，不允许编辑和删除 -->
                  <template v-if="isNotOverviewMode">                    <!-- 原始问题模式 -->
                    <template v-if="isQuestionsMode">
                      <button 
                        v-if="!question.is_deleted"
                        @click.stop="editQuestion(question)" 
                        class="action-btn small"
                        title="编辑"
                      >
                        ✏️
                      </button>
                      <template v-if="!question.is_deleted">
                        <button 
                          @click.stop="softDeleteQuestion(question)" 
                          class="action-btn small danger"
                          title="删除问题"
                        >
                          🗑️
                        </button>
                      </template>
                      <template v-else>
                        <button 
                          @click.stop="restoreQuestion(question)" 
                          class="action-btn small success"
                          title="恢复问题"
                        >
                          ♻️
                        </button>
                        <button 
                          @click.stop="forceDeleteQuestion(question)" 
                          class="action-btn small danger"
                          title="永久删除问题"
                        >
                          💀
                        </button>
                      </template>
                    </template>                    <!-- 原始回答模式 -->
                    <template v-else-if="isRawAnswersMode">
                      <button 
                        v-if="!question.is_deleted"
                        @click.stop="editRawAnswer(question)" 
                        class="action-btn small"
                        title="编辑原始回答"
                      >
                        ✏️
                      </button>
                      <template v-if="!question.is_deleted">
                        <button 
                          @click.stop="deleteRawAnswer(question)" 
                          class="action-btn small danger"
                          title="删除原始回答"
                        >
                          🗑️
                        </button>
                      </template>
                      <template v-else>
                        <button 
                          @click.stop="restoreRawAnswer(question)" 
                          class="action-btn small success"
                          title="恢复原始回答"
                        >
                          ♻️
                        </button>
                        <button 
                          @click.stop="forceDeleteRawAnswer(question)" 
                          class="action-btn small danger"
                          title="永久删除原始回答"
                        >
                          💀
                        </button>
                      </template>
                    </template>                    <!-- 专家回答模式 -->
                    <template v-else-if="isExpertAnswersMode">
                      <button 
                        v-if="!question.is_deleted"
                        @click.stop="editExpertAnswer(question)" 
                        class="action-btn small"
                        title="编辑专家回答"
                      >
                        ✏️
                      </button>
                      <button 
                        v-if="!question.is_deleted"
                        @click.stop="deleteExpertAnswer(question)" 
                        class="action-btn small danger"
                        title="删除专家回答"
                      >
                        🗑️
                      </button>
                      <button 
                        v-if="question.is_deleted"
                        @click.stop="restoreExpertAnswer(question)" 
                        class="action-btn small success"
                        title="恢复专家回答"
                      >
                        ♻️
                      </button>
                    </template>
                  </template>
                </div>
              </td>
            </template>
          </tr>
        </tbody>
      </table>      <div v-if="loading" class="loading-state">
        <div class="loading-content">
          <div class="loading-icon">⏳</div>
          <p class="loading-text">加载中...</p>
        </div>
      </div>

      <div v-else-if="filteredQuestions.length === 0" class="empty-state">
        <div class="empty-content">
          <!-- 搜索无结果的情况 -->
          <template v-if="searchQuery">
            <div class="empty-icon">🔍</div>
            <h3 class="empty-title">未找到匹配的数据</h3>
            <p class="empty-description">尝试调整搜索条件，或者清除搜索重新查看所有数据</p>
            <button @click="searchQuery = ''" class="empty-action-btn primary">
              <span class="btn-icon">🔄</span>
              清除搜索
            </button>
          </template>
            <!-- 专家回答模式下无数据的情况 -->
          <template v-else-if="isExpertAnswersMode">
            <div class="empty-icon">👨‍🏫</div>
            <h3 class="empty-title">暂无专家回答</h3>
            <p class="empty-description">当前还没有专家回答数据。专家回答需要通过专家用户在专家仪表板中创建。</p>
          </template>
            <!-- 原始回答模式下无数据的情况 -->
          <template v-else-if="isRawAnswersMode">
            <div class="empty-icon">💬</div>
            <h3 class="empty-title">暂无原始回答</h3>
            <p class="empty-description">当前还没有原始回答数据。您可以通过导入数据或手动添加问题和回答来创建内容。</p>
            <div class="empty-actions">
              <button @click="addNewQuestion" class="empty-action-btn primary">
                <span class="btn-icon">✏️</span>
                手动添加问答
              </button>
              <button @click="showImportDialog" class="empty-action-btn secondary">
                <span class="btn-icon">📁</span>
                导入数据
              </button>
            </div>
          </template>
          
          <!-- 默认情况（概览模式或问题模式）无数据 -->
          <template v-else>
            <div class="empty-icon">📝</div>
            <h3 class="empty-title">暂无问题数据</h3>
            <p class="empty-description">您还没有添加任何问题。开始创建您的第一个问题，或导入现有数据来快速开始。</p>
            <div class="empty-actions">
              <button @click="addNewQuestion" class="empty-action-btn primary">
                <span class="btn-icon">✏️</span>
                手动添加问题
              </button>
              <button @click="showImportDialog" class="empty-action-btn secondary">
                <span class="btn-icon">📁</span>
                导入数据
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>    <!-- 分页 -->
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

    <!-- 数据加载状态和加载更多 -->
    <div class="load-more-section" v-if="allQuestions.length > 0">
      <div class="data-info">
        <span class="info-text">
          已加载 {{ allQuestions.length }} / {{ totalItems }} 条记录
        </span>
        <span v-if="hasMore" class="more-info">还有更多数据可加载</span>
        <span v-else class="complete-info">已加载全部数据</span>
      </div>
      
      <button 
        v-if="hasMore"
        @click="loadMoreData"
        :disabled="loadingMore"
        class="load-more-btn"
      >
        {{ loadingMore ? '加载中...' : `加载更多 (剩余约 ${totalItems - allQuestions.length} 条)` }}
      </button>
    </div><!-- 对话框组件 -->
    <SimpleQuestionEditDialog 
      v-model:visible="questionDialogVisible"
      :question="currentQuestion"
      @save="handleQuestionSave"
    />
    
    <!-- 问题和回答添加对话框 -->
    <QuestionAnswerDialog 
      v-model:visible="addDialogVisible"
      @save="handleQuestionAnswerSave"
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
      @edit="handleDetailEdit"    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RawQuestion } from '@/types/questions'
import { RawAnswer, ExpertAnswer } from '@/types/answers'
import SimpleQuestionEditDialog from '@/components/SimpleQuestionEditDialog.vue'
import QuestionAnswerDialog from '@/components/QuestionAnswerDialog.vue'
import AnswerEditDialog from '@/components/AnswerEditDialog.vue'
import StandardQADialog from '@/components/StandardQADialog.vue'
import RawQAImportDialog from '@/components/RawQAImportDialog.vue'
import QuestionDetailDialog from '@/components/QuestionDetailDialog.vue'
import { rawQuestionService } from "@/services/rawQuestionService"
import { formatTags, formatDate } from '@/utils/formatters'

// 响应式状态
const loading = ref(false)
const loadingMore = ref(false) // 新增：加载更多状态
const searchQuery = ref('')
const itemsPerPage = ref(20)
const currentPage = ref(1)
const selectedItems = ref<number[]>([])
const allQuestions = ref<RawQuestion[]>([])

// 分页和加载更多状态
const currentSkip = ref(0) // 新增：当前跳过的记录数
const totalItems = ref(0) // 新增：总记录数
const hasMore = ref(true) // 新增：是否还有更多数据
const loadSize = ref(1000) // 新增：每次加载的数量

// 视图模式状态
const viewMode = ref<'overview' | 'questions' | 'raw-answers' | 'expert-answers'>('overview');
const showMode = ref<'active_only' | 'deleted_only' | 'all'>('active_only')

// 计算属性来避免TypeScript类型推断问题
const isOverviewMode = computed(() => viewMode.value === 'overview')
const isQuestionsMode = computed(() => viewMode.value === 'questions')
const isRawAnswersMode = computed(() => viewMode.value === 'raw-answers')
const isExpertAnswersMode = computed(() => viewMode.value === 'expert-answers')
const isNotOverviewMode = computed(() => viewMode.value !== 'overview')
const isOverviewOrQuestions = computed(() => viewMode.value === 'overview' || viewMode.value === 'questions')

// 对话框状态
const questionDialogVisible = ref(false)
const addDialogVisible = ref(false)
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
    formatTags(q.tags).some(tag => tag.toLowerCase().includes(query))
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

const truncateText = (text: string | undefined | null, maxLength: number) => {
  if (!text || text.length <= maxLength) return text || ''
  return text.substring(0, maxLength) + '...'
}

const loadData = async (loadMore = false) => {
  try {
    if (loadMore) {
      loadingMore.value = true
    } else {
      loading.value = true
      // 重置状态
      allQuestions.value = []
      currentSkip.value = 0
      hasMore.value = true
    }
    
    // 根据显示模式确定参数
    let include_deleted = false
    let deleted_only = false
    
    if (showMode.value === 'all') {
      include_deleted = true
    } else if (showMode.value === 'deleted_only') {
      include_deleted = true
      deleted_only = true
    }    // 根据视图模式调用不同的接口
    let response
    const skip = loadMore ? currentSkip.value : 0
    const limit = loadSize.value

    if (viewMode.value === 'overview') {
      // 使用概览接口，包含完整的嵌套回答数据
      response = await rawQuestionService.getRawQuestionsOverview(skip, limit, include_deleted, deleted_only)
      const newData = response.data || []
      if (loadMore) {
        allQuestions.value.push(...newData)
      } else {
        allQuestions.value = newData
      }
    } else if (viewMode.value === 'questions') {
      // 使用标准的原始问题接口
      response = await rawQuestionService.getRawQuestions(skip, limit, include_deleted, deleted_only)
      const newData = response || []
      if (loadMore) {
        allQuestions.value.push(...newData)
      } else {
        allQuestions.value = newData
      }} else if (viewMode.value === 'raw-answers') {
      response = await rawQuestionService.getRawAnswersView(skip, limit, include_deleted, deleted_only)      // 将原始回答数据转换为问题格式以便在表格中显示
      const newData = (response.data || []).map((answer: any) => ({
        id: answer.id,
        title: answer.answer ? `${truncateText(answer.answer, 60)}` : '原始回答',
        body: answer.answer,
        author: answer.answered_by || '匿名',
        view_count: 0,
        vote_count: answer.upvotes || 0,
        issued_at: answer.answered_at, // note: 原始回答使用 answered_at 作为发布时间
        created_at: answer.answered_at,
        is_deleted: answer.is_deleted,
        tags: answer.question?.tags || [],
        type: 'raw-answer',
        url: answer.question?.url,
        original_data: answer,
        // 构造原始回答数组，用于详情对话框显示
        raw_answers: [{
          id: answer.id,
          answer: answer.answer,
          answered_by: answer.answered_by,
          answered_at: answer.answered_at,
          upvotes: answer.upvotes,
          is_deleted: answer.is_deleted
        }],
        expert_answers: []
      }))
      if (loadMore) {
        allQuestions.value.push(...newData)
      } else {
        allQuestions.value = newData
      }    } else if (viewMode.value === 'expert-answers') {
      response = await rawQuestionService.getExpertAnswersView(skip, limit, include_deleted, deleted_only)      // 将专家回答数据转换为问题格式以便在表格中显示
      const newData = (response.data || []).map((answer: any) => ({
        id: answer.id,
        title: answer.answer ? `${truncateText(answer.answer, 60)}` : '专家回答',
        body: answer.answer,        
        author: answer.answered_by || '匿名专家',
        view_count: undefined,
        vote_count: undefined,
        issued_at: answer.answered_at, // note: 专家回答使用 answered_at 作为发布时间
        created_at: answer.answered_at,
        is_deleted: answer.is_deleted,
        tags: answer.question?.tags || [],
        type: 'expert-answer',
        url: answer.question?.url,
        original_data: answer,
        raw_answers: [],
        // 构造专家回答数组，用于详情对话框显示
        expert_answers: [{
          id: answer.id,
          answer: answer.answer,
          answered_by: answer.answered_by,
          answered_at: answer.answered_at,
          is_deleted: answer.is_deleted
        }]
      }))
      if (loadMore) {
        allQuestions.value.push(...newData)
      } else {
        allQuestions.value = newData
      }
    }
    
    // 更新分页状态
    if (response) {
      totalItems.value = response.total || 0
      currentSkip.value += (response.data || []).length
      hasMore.value = currentSkip.value < totalItems.value
    }
    
    console.log('加载的数据:', { 
      currentCount: allQuestions.value.length, 
      total: totalItems.value,
      hasMore: hasMore.value,
      skip: currentSkip.value 
    })
  } catch (error) {
    console.error('加载数据失败:', error)
    showMessage('加载数据失败', 'error')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const refreshData = () => {
  loadData()
}

// 新增：加载更多数据
const loadMoreData = () => {
  if (!loadingMore.value && hasMore.value) {
    loadData(true)
  }
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
  console.log('添加新问题和回答') // 添加调试日志
  addDialogVisible.value = true
}

const editQuestion = (question: RawQuestion) => {
  console.log('编辑问题:', question.title) // 添加调试日志
  currentQuestion.value = question
  questionDialogVisible.value = true
}

// 编辑原始回答（仅显示提示信息，因为原始回答按设计不可编辑）
const editRawAnswer = (question: RawQuestion) => {
  if (question.is_deleted) {
    showMessage('已删除的原始回答不允许编辑', 'warning')
    return
  }
  showMessage('根据系统设计，原始回答内容不可编辑，只能删除或恢复', 'info')
}

// 编辑专家回答（仅显示提示信息，因为编辑功能需要专门的编辑器）
const editExpertAnswer = (question: RawQuestion) => {
  if (question.is_deleted) {
    showMessage('已删除的专家回答不允许编辑', 'warning')
    return
  }
  showMessage('专家回答编辑功能请使用专家仪表板', 'info')
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

// 原始回答的删除恢复函数
const deleteRawAnswer = async (question: RawQuestion) => {
  if (!question.original_data) return
  
  try {
    const answerId = question.original_data.id
    await rawQuestionService.deleteRawAnswer(answerId)
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== answerId)
    
    showMessage('原始回答已删除', 'success')
  } catch (error) {
    console.error('删除原始回答失败:', error)
    showMessage('删除原始回答失败', 'error')
  }
}

const restoreRawAnswer = async (question: RawQuestion) => {
  if (!question.original_data) return
    try {
    const answerId = question.original_data.id
    await rawQuestionService.restoreRawAnswer(answerId)
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== answerId)
    
    showMessage('原始回答已恢复', 'success')
  } catch (error: any) {
    console.error('恢复原始回答失败:', error)
    const errorMessage = error?.response?.data?.detail || error?.message || '恢复原始回答失败'
    showMessage(errorMessage, 'error')
  }
}

const forceDeleteRawAnswer = async (question: RawQuestion) => {
  if (!question.original_data) return
  
  if (!confirm(`确定要永久删除这个原始回答吗？此操作无法撤销！`)) return
  
  try {
    const answerId = question.original_data.id
    
    // 如果回答未被软删除，先软删除
    if (!question.is_deleted) {
      await rawQuestionService.deleteRawAnswer(answerId)
    }
    
    // 然后强制删除
    await rawQuestionService.forceDeleteRawAnswer(answerId)
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== answerId)
    
    showMessage('原始回答已永久删除', 'success')
  } catch (error) {
    console.error('强制删除原始回答失败:', error)
    showMessage('强制删除原始回答失败', 'error')
  }
}

// 专家回答的删除恢复函数
const deleteExpertAnswer = async (question: RawQuestion) => {
  if (!question.original_data) return
  
  try {
    const answerId = question.original_data.id
    await rawQuestionService.deleteExpertAnswer(answerId)
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== answerId)
    
    showMessage('专家回答已删除', 'success')
  } catch (error) {
    console.error('删除专家回答失败:', error)
    showMessage('删除专家回答失败', 'error')
  }
}

const restoreExpertAnswer = async (question: RawQuestion) => {
  if (!question.original_data) return
  
  try {
    const answerId = question.original_data.id
    await rawQuestionService.restoreExpertAnswer(answerId)
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== answerId)
    
    showMessage('专家回答已恢复', 'success')
  } catch (error: any) {
    console.error('恢复专家回答失败:', error)
    const errorMessage = error?.response?.data?.detail || error?.message || '恢复专家回答失败'
    showMessage(errorMessage, 'error')
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
    
    // 记录删除数量
    const deletedCount = selectedItems.value.length
    
    // 清空选中项
    selectedItems.value = []
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
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

const handleDataImported = async () => {
  try {
    // 重新加载问题列表
    await loadData()
    showMessage('数据导入完成，问题列表已更新', 'success')
  } catch (error) {
    console.error('刷新数据失败:', error)
    showMessage('数据导入成功，但刷新失败，请手动刷新页面', 'warning')
  }
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

const handleQuestionAnswerSave = async (data: { question: Partial<RawQuestion>, answers: any[] }) => {
  try {
    // 准备回答数据
    const answersData = data.answers.map(answer => ({
      answer: answer.body, // 后端数据库字段名
      answered_by: answer.author || '匿名',
      upvotes: answer.upvotes?.toString() || '0',
      answered_at: answer.answered_at || new Date().toISOString()
    }))
    
    // 使用事务性API一次性创建问题和所有回答
    const result = await rawQuestionService.createRawQuestionWithAnswers({
      question: data.question,
      answers: answersData
    })
      if (result.success) {
      showMessage(`问题和 ${result.answers.length} 个回答已创建`, 'success')
      addDialogVisible.value = false
      loadData() // 重新加载数据
    } else {
      throw new Error(result.message || '创建失败')
    }
  } catch (error) {
    console.error('保存问题和回答失败:', error)
    showMessage('保存问题和回答失败', 'error')
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
  // 检查问题是否已被删除，已删除的问题不允许编辑
  if (question.is_deleted) {
    showMessage('已删除的问题不允许编辑', 'warning')
    return
  }
  
  detailDialogVisible.value = false
  editQuestion(question)
}

// 删除确认和处理
const showDeleteConfirm = (question: RawQuestion) => {
  if (question.is_deleted) {
    // 已删除的问题，显示恢复和强制删除选项
    showDeletedQuestionActions(question)
  } else {
    // 未删除的问题，直接软删除
    const message = `确定要删除问题 "${question.title}" 吗？`
    if (confirm(message)) {
      softDeleteQuestion(question)
    }
  }
}

// 显示已删除问题的操作选项
const showDeletedQuestionActions = (question: RawQuestion) => {
  // 创建一个更友好的操作选择界面
  const choice = window.confirm(
    `问题 "${question.title}" 已被软删除。\n\n点击"确定"恢复问题，点击"取消"查看永久删除选项。`
  )
  
  if (choice) {
    // 用户选择恢复
    restoreQuestion(question)
  } else {
    // 用户选择查看永久删除选项
    const forceDelete = window.confirm(
      `您选择了查看删除选项。\n\n点击"确定"将永久删除问题 "${question.title}"，此操作无法撤销！\n点击"取消"将不执行任何操作。`
    )
    
    if (forceDelete) {
      forceDeleteQuestion(question)
    }
    // 如果用户取消，不执行任何操作
  }
}

// 删除功能
const softDeleteQuestion = async (question: RawQuestion) => {
  try {
    await rawQuestionService.deleteRawQuestion(question.id);
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== question.id)
    
    showMessage('问题已软删除', 'success')
  } catch (error) {
    console.error('软删除失败:', error)
    showMessage('软删除失败', 'error')
  }
}

const restoreQuestion = async (question: RawQuestion) => {
  try {
    await rawQuestionService.restoreRawQuestion(question.id)
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(id => id !== question.id)
    
    showMessage('问题已恢复', 'success')
  } catch (error: any) {
    console.error('恢复失败:', error)
    const errorMessage = error?.response?.data?.detail || error?.message || '恢复失败'
    showMessage(errorMessage, 'error')
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
    
    // 重新加载数据以确保显示状态正确
    await loadData()
    
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

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  background: white;
  color: #303133;
  text-decoration: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.action-btn:hover:not(:disabled) {
  background: #f5f7fa;
  border-color: #c6e2ff;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.action-btn.primary {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  border-color: #409eff;
  color: white;
}

.action-btn.primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #337ecc 0%, #2b6cb0 100%);
  border-color: #337ecc;
}

.action-btn.secondary {
  background: #f8f9fb;
  border-color: #e4e7ed;
  color: #606266;
}

.action-btn.secondary:hover:not(:disabled) {
  background: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-icon {
  font-size: 16px;
}

/* 统计栏样式 */
.stats-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px 24px;
  background: white;
  border-radius: 10px;
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
  font-weight: 600;
  color: #303133;
  font-size: 16px;
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

.overview-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-text {
  color: #666;
  font-size: 14px;
  font-style: italic;
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

/* 概览模式样式 */
.answers-col, .expert-answers-col {
  min-width: 200px;
  max-width: 300px;
}

.answer-group {
  padding: 8px 0;
}

.answer-count {
  font-weight: 600;
  color: #333;
  font-size: 13px;
  margin-bottom: 4px;
}

.answer-preview {
  color: #666;
  font-size: 12px;
  line-height: 1.4;
  margin-bottom: 4px;
}

.more-answers {
  color: #007bff;
  font-size: 11px;
  font-style: italic;
}

.no-answers {
  color: #999;
  font-style: italic;
  font-size: 12px;
  padding: 8px 0;
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

/* 加载更多样式 */
.load-more-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-top: 16px;
}

.data-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.info-text {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.more-info {
  font-size: 12px;
  color: #409eff;
}

.complete-info {
  font-size: 12px;
  color: #67c23a;
}

.load-more-btn {
  padding: 12px 24px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 200px;
}

.load-more-btn:hover:not(:disabled) {
  background: #337ecc;
  transform: translateY(-1px);
}

.load-more-btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
  transform: none;
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

/* 加载状态样式 */
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-icon {
  font-size: 48px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.loading-text {
  color: #606266;
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

/* 空状态样式 */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin: 24px 0;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 480px;
  gap: 20px;
}

.empty-icon {
  font-size: 64px;
  opacity: 0.6;
  margin-bottom: 8px;
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  line-height: 1.3;
}

.empty-description {
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.empty-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 8px;
}

.empty-action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  background: white;
  color: #303133;
  text-decoration: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  min-width: 140px;
  justify-content: center;
}

.empty-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.empty-action-btn.primary {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  border-color: #409eff;
  color: white;
}

.empty-action-btn.primary:hover {
  background: linear-gradient(135deg, #337ecc 0%, #2b6cb0 100%);
  border-color: #337ecc;
}

.empty-action-btn.secondary {
  background: #f8f9fb;
  border-color: #e4e7ed;
  color: #606266;
}

.empty-action-btn.secondary:hover {
  background: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
}

.empty-action-btn .btn-icon {
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .empty-content {
    max-width: 320px;
    gap: 16px;
  }
  
  .empty-icon {
    font-size: 48px;
  }
  
  .empty-title {
    font-size: 20px;
  }
  
  .empty-description {
    font-size: 14px;
  }
  
  .empty-actions {
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }
  
  .empty-action-btn {
    width: 100%;
    min-width: unset;
  }
}
</style>
<template>
  <div v-if="dialogVisible" class="dialog-overlay" @click="handleOverlayClick">
    <div class="dialog" @click.stop>
      <div class="dialog-header">
        <h3>创建标准问答</h3>
        <button class="close-btn" @click="handleClose">&times;</button>
      </div>
      
      <div class="dialog-body">
        <div class="standard-qa-content">
          <!-- 选中内容概览 -->
          <div class="selected-summary">
            <h4>选中的内容概览</h4>
            <div class="summary-stats">
              <span class="tag tag-info">原始问题: {{ selectedQuestionCount }} 个</span>
              <span class="tag tag-success">原始回答: {{ selectedRawAnswerCount }} 个</span>
              <span class="tag tag-warning">专家回答: {{ selectedExpertAnswerCount }} 个</span>
            </div>
          </div>

          <!-- 表单 -->
          <form ref="formRef" @submit.prevent="handleSave" class="form">
            <!-- 标准问题部分 -->
            <div class="form-section">
              <h4>标准问题</h4>
              
              <div class="form-item">
                <label class="form-label required">数据集</label>
                <select 
                  v-model="formData.dataset_id" 
                  class="form-select"
                  :disabled="datasetsLoading"
                  required
                >
                  <option value="">选择数据集</option>
                  <option 
                    v-for="dataset in datasets" 
                    :key="dataset.id" 
                    :value="dataset.id"
                  >
                    {{ dataset.name }}
                  </option>
                </select>
                <div v-if="datasetsLoading" class="loading-text">加载中...</div>
              </div>

              <div class="form-item">
                <label class="form-label required">问题内容</label>
                <textarea
                  v-model="formData.question_text"
                  class="form-textarea"
                  placeholder="请输入标准问题的详细内容"
                  rows="4"
                  maxlength="1000"
                  required
                ></textarea>
                <div class="char-count">{{ formData.question_text.length }}/1000</div>
              </div>

              <div class="form-item">
                <label class="form-label">难度等级</label>
                <select v-model="formData.difficulty_level" class="form-select">
                  <option value="">选择难度等级</option>
                  <option value="beginner">初级</option>
                  <option value="intermediate">中级</option>
                  <option value="advanced">高级</option>
                </select>
              </div>

              <div class="form-item">
                <label class="form-label">知识点</label>
                <div class="tags-input">
                  <span
                    v-for="point in formData.knowledge_points"
                    :key="point"
                    class="tag tag-closable"
                  >
                    {{ point }}
                    <button 
                      type="button" 
                      class="tag-close" 
                      @click="removeKnowledgePoint(point)"
                    >
                      ×
                    </button>
                  </span>
                  <input
                    v-if="knowledgePointInputVisible"
                    ref="knowledgePointInputRef"
                    v-model="knowledgePointInputValue"
                    class="tag-input"
                    @keyup.enter="handleKnowledgePointInputConfirm"
                    @blur="handleKnowledgePointInputConfirm"
                    placeholder="输入知识点"
                  />
                  <button 
                    v-else 
                    type="button"
                    class="btn btn-small btn-secondary" 
                    @click="showKnowledgePointInput"
                  >
                    + 添加知识点
                  </button>
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">标签</label>
                <div class="tags-input">
                  <span
                    v-for="tag in formData.tags"
                    :key="tag"
                    class="tag tag-closable"
                  >
                    {{ tag }}
                    <button 
                      type="button" 
                      class="tag-close" 
                      @click="removeTag(tag)"
                    >
                      ×
                    </button>
                  </span>
                  <input
                    v-if="tagInputVisible"
                    ref="tagInputRef"
                    v-model="tagInputValue"
                    class="tag-input"
                    @keyup.enter="handleTagInputConfirm"
                    @blur="handleTagInputConfirm"
                    placeholder="输入标签"
                  />
                  <button 
                    v-else 
                    type="button"
                    class="btn btn-small btn-secondary" 
                    @click="showTagInput"
                  >
                    + 添加标签
                  </button>
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">备注</label>
                <textarea
                  v-model="formData.notes"
                  class="form-textarea"
                  placeholder="问题备注（可选）"
                  rows="2"
                ></textarea>
              </div>
            </div>

            <!-- 标准回答部分 -->
            <div class="form-section">
              <h4>标准回答</h4>
              
              <div class="form-item">
                <label class="form-label required">回答内容</label>
                <textarea
                  v-model="formData.answer_text"
                  class="form-textarea"
                  placeholder="请输入标准回答内容"
                  rows="6"
                  maxlength="2000"
                  required
                ></textarea>
                <div class="char-count">{{ formData.answer_text.length }}/2000</div>
              </div>

              <div class="form-row">
                <div class="form-item">
                  <label class="form-label">回答类型</label>
                  <select v-model="formData.answer_type" class="form-select">
                    <option value="">选择回答类型</option>
                    <option value="direct">直接答案</option>
                    <option value="step-by-step">步骤指导</option>
                    <option value="code-example">代码示例</option>
                    <option value="reference">参考链接</option>
                    <option value="comprehensive">综合答案</option>
                  </select>
                </div>
                <div class="form-item">
                  <label class="form-label">总分</label>
                  <input
                    v-model.number="formData.total_score"
                    type="number"
                    class="form-input"
                    min="0"
                    max="100"
                    placeholder="总分"
                  />
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">评分点</label>
                <div class="scoring-points">
                  <div 
                    v-for="(point, index) in formData.scoring_points" 
                    :key="index"
                    class="scoring-point-item"
                  >
                    <input
                      v-model="point.scoring_point_text"
                      type="text"
                      class="form-input"
                      placeholder="评分点内容"
                    />
                    <input
                      v-model.number="point.score"
                      type="number"
                      class="form-input score-input"
                      min="0"
                      max="100"
                      placeholder="分值"
                    />
                    <button 
                      type="button"
                      class="btn btn-small btn-danger"
                      @click="removeScoringPoint(index)"
                    >
                      删除
                    </button>
                  </div>
                  <button 
                    type="button"
                    class="btn btn-small btn-secondary" 
                    @click="addScoringPoint"
                  >
                    + 添加评分点
                  </button>
                </div>
              </div>

              <div class="form-item">
                <label class="form-label">详细解释</label>
                <textarea
                  v-model="formData.explanation"
                  class="form-textarea"
                  placeholder="对回答的详细解释（可选）"
                  rows="3"
                ></textarea>
              </div>
            </div>

            <!-- 关系配置部分 -->
            <div class="form-section">
              <h4>关系配置</h4>
              
              <!-- 原始问题关系 -->
              <div v-if="selectedQuestions.length > 0" class="relation-group">
                <h5>关联的原始问题 ({{ selectedQuestions.length }})</h5>
                <div 
                  v-for="(question, index) in selectedQuestions" 
                  :key="question.id"
                  class="relation-item"
                >
                  <div class="relation-content">
                    <strong>{{ question.title }}</strong>
                    <p>{{ truncateText(question.body || '', 100) }}</p>
                  </div>
                  <div class="relation-config">
                    <input
                      v-model="rawQuestionRelations[index].notes"
                      type="text"
                      class="form-input small"
                      placeholder="备注"
                    />
                  </div>
                </div>
              </div>

              <!-- 原始回答关系 -->
              <div v-if="selectedRawAnswers.length > 0" class="relation-group">
                <h5>关联的原始回答 ({{ selectedRawAnswers.length }})</h5>
                <div 
                  v-for="(answer, index) in selectedRawAnswers" 
                  :key="answer.id"
                  class="relation-item"
                >
                  <div class="relation-content">
                    <strong>原始回答</strong>
                    <p>{{ truncateText(answer.content, 100) }}</p>
                    <small>{{ answer.author || '匿名' }} · {{ formatDate(answer.answered_at) }}</small>
                  </div>
                  <div class="relation-config">
                    <input
                      v-model="rawAnswerRelations[index].notes"
                      type="text"
                      class="form-input small"
                      placeholder="备注"
                    />
                  </div>
                </div>
              </div>

              <!-- 专家回答关系 -->
              <div v-if="selectedExpertAnswers.length > 0" class="relation-group">
                <h5>关联的专家回答 ({{ selectedExpertAnswers.length }})</h5>
                <div 
                  v-for="(answer, index) in selectedExpertAnswers" 
                  :key="answer.id"
                  class="relation-item"
                >
                  <div class="relation-content">
                    <strong>专家回答</strong>
                    <p>{{ truncateText(answer.content, 100) }}</p>
                    <small>来源: {{ answer.source }} | 作者: {{ answer.author || '匿名' }}</small>
                  </div>
                  <div class="relation-config">
                    <input
                      v-model="expertAnswerRelations[index].notes"
                      type="text"
                      class="form-input small"
                      placeholder="备注"
                    />
                  </div>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>

      <div class="dialog-footer">
        <button 
          type="button"
          class="btn btn-secondary" 
          @click="handleClose"
        >
          取消
        </button>
        <button 
          type="button"
          class="btn btn-primary" 
          @click="handleSave" 
          :disabled="loading"
        >
          {{ loading ? '创建中...' : '创建标准问答' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { RawQuestion } from '@/types/questions'
import { RawAnswer, ExpertAnswer } from '@/types/answers'
import { 
  standardQAService, 
  type CreateStandardQARequest,
  type ScoringPoint,
  type RawQuestionRelation,
  type RawAnswerRelation,
  type ExpertAnswerRelation
} from '@/services/standardQAService'
import { datasetService, type Dataset } from '@/services/datasetService'
import { authService } from '@/services/authService'

interface Props {
  visible: boolean
  selectedItems: {
    questions: Set<number>
    rawAnswers: Set<number>
    expertAnswers: Set<number>
  }
  questions: RawQuestion[]
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'created'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const formRef = ref<HTMLFormElement>()
const loading = ref(false)
const datasetsLoading = ref(false)
const datasets = ref<Dataset[]>([])

// 标签和知识点输入
const knowledgePointInputVisible = ref(false)
const knowledgePointInputValue = ref('')
const knowledgePointInputRef = ref<HTMLInputElement>()
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref<HTMLInputElement>()

// 表单数据
const formData = ref<CreateStandardQARequest>({
  dataset_id: 0,
  question_text: '',
  difficulty_level: '',
  knowledge_points: [],
  tags: [],
  notes: '',
  answer_text: '',
  answer_type: '',
  scoring_points: [],
  total_score: undefined,
  explanation: '',
  raw_question_relations: [],
  raw_answer_relations: [],
  expert_answer_relations: []
})

// 关系记录
const rawQuestionRelations = ref<RawQuestionRelation[]>([])
const rawAnswerRelations = ref<RawAnswerRelation[]>([])
const expertAnswerRelations = ref<ExpertAnswerRelation[]>([])

// 计算属性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const selectedQuestionCount = computed(() => props.selectedItems.questions.size)
const selectedRawAnswerCount = computed(() => props.selectedItems.rawAnswers.size)
const selectedExpertAnswerCount = computed(() => props.selectedItems.expertAnswers.size)

const selectedQuestions = computed(() => 
  props.questions.filter(q => props.selectedItems.questions.has(q.id))
)

const selectedRawAnswers = computed(() => {
  const answers: RawAnswer[] = []
  props.questions.forEach(q => {
    q.raw_answers.forEach(a => {
      if (props.selectedItems.rawAnswers.has(a.id)) {
        answers.push(a)
      }
    })
  })
  return answers
})

const selectedExpertAnswers = computed(() => {
  const answers: ExpertAnswer[] = []
  props.questions.forEach(q => {
    q.expert_answers.forEach(a => {
      if (props.selectedItems.expertAnswers.has(a.id)) {
        answers.push(a)
      }
    })
  })
  return answers
})

// 监听选中内容变化，自动填充部分内容
watch(() => props.selectedItems, () => {
  if (selectedQuestions.value.length === 1) {
    const question = selectedQuestions.value[0]
    formData.value.question_text = question.title + '\n' + (question.body || '')
    if (question.tags) {
      formData.value.tags = [...question.tags]
    }
  }
  
  // 如果有专家回答，可以作为标准回答的参考
  if (selectedExpertAnswers.value.length === 1) {
    const expertAnswer = selectedExpertAnswers.value[0]
    if (!formData.value.answer_text) {
      formData.value.answer_text = expertAnswer.content
    }
  }

  // 初始化关系记录
  initializeRelations()
}, { deep: true })

// 方法
const loadDatasets = async () => {
  datasetsLoading.value = true
  try {
    // 获取用户可访问的数据集
    datasets.value = await datasetService.getUserDatasets()
  } catch (error) {
    console.error('加载数据集失败:', error)
    showMessage('加载数据集失败', 'error')
  } finally {
    datasetsLoading.value = false
  }
}

const initializeRelations = () => {
  // 初始化原始问题关系记录
  rawQuestionRelations.value = selectedQuestions.value.map(q => ({
    raw_question_id: q.id,
    notes: ''
  }))

  // 初始化原始回答关系记录
  rawAnswerRelations.value = selectedRawAnswers.value.map(a => ({
    raw_answer_id: a.id,
    notes: ''
  }))

  // 初始化专家回答关系记录
  expertAnswerRelations.value = selectedExpertAnswers.value.map(a => ({
    expert_answer_id: a.id,
    notes: ''
  }))
}

const removeKnowledgePoint = (point: string) => {
  formData.value.knowledge_points = formData.value.knowledge_points?.filter(p => p !== point) || []
}

const showKnowledgePointInput = () => {
  knowledgePointInputVisible.value = true
  nextTick(() => {
    knowledgePointInputRef.value?.focus()
  })
}

const handleKnowledgePointInputConfirm = () => {
  const value = knowledgePointInputValue.value.trim()
  if (value && !(formData.value.knowledge_points || []).includes(value)) {
    formData.value.knowledge_points = [...(formData.value.knowledge_points || []), value]
  }
  knowledgePointInputVisible.value = false
  knowledgePointInputValue.value = ''
}

const removeTag = (tag: string) => {
  formData.value.tags = formData.value.tags?.filter(t => t !== tag) || []
}

const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const handleTagInputConfirm = () => {
  const value = tagInputValue.value.trim()
  if (value && !(formData.value.tags || []).includes(value)) {
    formData.value.tags = [...(formData.value.tags || []), value]
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

const addScoringPoint = () => {
  formData.value.scoring_points = [
    ...(formData.value.scoring_points || []),
    { scoring_point_text: '', score: 0 }
  ]
}

const removeScoringPoint = (index: number) => {
  formData.value.scoring_points?.splice(index, 1)
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatDate = (date: Date | string | undefined) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN')
}

const showMessage = (message: string, type: 'success' | 'error' | 'warning' = 'success') => {
  // 简单的消息提示实现
  const messageEl = document.createElement('div')
  messageEl.className = `message message-${type}`
  messageEl.textContent = message
  messageEl.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 4px;
    color: white;
    z-index: 10000;
    background-color: ${type === 'success' ? '#67c23a' : type === 'error' ? '#f56c6c' : '#e6a23c'};
  `
  document.body.appendChild(messageEl)
  setTimeout(() => {
    // 确保元素仍然存在且有父节点再进行移除
    if (messageEl && messageEl.parentNode) {
      messageEl.parentNode.removeChild(messageEl)
    }
  }, 3000)
}

const validateForm = (): boolean => {
  if (!formData.value.dataset_id) {
    showMessage('请选择数据集', 'error')
    return false
  }
  if (!formData.value.question_text.trim()) {
    showMessage('请输入标准问题内容', 'error')
    return false
  }
  if (formData.value.question_text.trim().length < 10) {
    showMessage('问题内容至少需要10个字符', 'error')
    return false
  }
  if (!formData.value.answer_text.trim()) {
    showMessage('请输入标准回答内容', 'error')
    return false
  }
  if (formData.value.answer_text.trim().length < 20) {
    showMessage('回答内容至少需要20个字符', 'error')
    return false
  }
  return true
}

const resetForm = () => {
  formData.value = {
    dataset_id: 0,
    question_text: '',
    difficulty_level: '',
    knowledge_points: [],
    tags: [],
    notes: '',
    answer_text: '',
    answer_type: '',
    scoring_points: [],
    total_score: undefined,
    explanation: '',
    raw_question_relations: [],
    raw_answer_relations: [],
    expert_answer_relations: []
  }
  rawQuestionRelations.value = []
  rawAnswerRelations.value = []
  expertAnswerRelations.value = []
  knowledgePointInputVisible.value = false
  knowledgePointInputValue.value = ''
  tagInputVisible.value = false
  tagInputValue.value = ''
}

const handleOverlayClick = () => {
  handleClose()
}

const handleClose = () => {
  dialogVisible.value = false
  resetForm()
}

const handleSave = async () => {
  if (!validateForm()) return

  try {
    loading.value = true

    // 获取当前用户信息
    const currentUser = authService.getCurrentUserFromStorage()
    const created_by = currentUser?.username || 'anonymous'

    // 构建要提交的数据
    const requestData: CreateStandardQARequest = {
      ...formData.value,
      created_by,
      raw_question_relations: rawQuestionRelations.value.map(rel => ({
        ...rel,
        created_by
      })),
      raw_answer_relations: rawAnswerRelations.value.map(rel => ({
        ...rel,
        created_by
      })),
      expert_answer_relations: expertAnswerRelations.value.map(rel => ({
        ...rel,
        created_by
      }))
    }

    // 调用API创建标准问答
    await standardQAService.createStandardQAWithRelations(requestData)
    
    emit('created')
    showMessage('标准问答创建成功', 'success')
    handleClose()
  } catch (error) {
    console.error('创建标准问答失败:', error)
    showMessage('创建失败，请检查网络连接和输入内容', 'error')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(async () => {
  await loadDatasets()
})
</script>

<style scoped>
/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e4e7ed;
}

.dialog-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #909399;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.close-btn:hover {
  color: #606266;
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
}

/* 内容样式 */
.standard-qa-content {
  max-height: none;
}

.selected-summary {
  background-color: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.selected-summary h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.summary-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 表单样式 */
.form-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e4e7ed;
}

.form-section:last-child {
  border-bottom: none;
}

.form-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  color: #606266;
  font-size: 14px;
  font-weight: 500;
}

.form-label.required::after {
  content: ' *';
  color: #f56c6c;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  transition: border-color 0.2s ease;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #409eff;
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.loading-text {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
}

.btn:hover {
  opacity: 0.8;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-small {
  padding: 4px 8px;
  font-size: 12px;
}

.btn-primary {
  background-color: #409eff;
  border-color: #409eff;
  color: white;
}

.btn-secondary {
  background-color: #f4f4f5;
  border-color: #dcdfe6;
  color: #606266;
}

.btn-danger {
  background-color: #f56c6c;
  border-color: #f56c6c;
  color: white;
}

/* 标签样式 */
.tag {
  display: inline-block;
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
  margin-right: 8px;
  margin-bottom: 4px;
}

.tag-info {
  background-color: #ecf5ff;
  color: #409eff;
  border: 1px solid #b3d8ff;
}

.tag-success {
  background-color: #f0f9ff;
  color: #67c23a;
  border: 1px solid #b3e19d;
}

.tag-warning {
  background-color: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #f5dab1;
}

.tag-closable {
  background-color: #f4f4f5;
  color: #909399;
  border: 1px solid #e4e7ed;
  padding-right: 20px;
  position: relative;
}

.tag-close {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #909399;
  cursor: pointer;
  font-size: 12px;
  width: 12px;
  height: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.tag-close:hover {
  color: #606266;
}

.tags-input {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-input {
  width: 120px;
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 12px;
}

/* 评分点样式 */
.scoring-points .scoring-point-item {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.score-input {
  width: 100px;
}

/* 关系配置样式 */
.relation-group {
  margin-bottom: 20px;
}

.relation-group h5 {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
}

.relation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 8px;
  background-color: #fafafa;
}

.relation-content {
  flex: 1;
  min-width: 0;
}

.relation-content strong {
  color: #303133;
  display: block;
  margin-bottom: 4px;
}

.relation-content p {
  margin: 4px 0;
  color: #606266;
  line-height: 1.4;
  word-break: break-word;
}

.relation-content small {
  color: #909399;
  font-size: 12px;
}

.relation-config {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-left: 16px;
  flex-shrink: 0;
}

.form-select.small,
.form-input.small {
  width: 100px;
  padding: 4px 8px;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dialog {
    width: 95%;
    margin: 10px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .relation-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .relation-config {
    margin-left: 0;
    margin-top: 8px;
    justify-content: flex-start;
  }
}
</style>

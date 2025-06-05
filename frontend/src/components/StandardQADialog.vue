<template>
  <div class="modal-overlay" @click="$emit('cancel')">
    <div class="modal standard-qa-modal" @click.stop>
      <div class="modal-header">
        <h3>创建标准问答</h3>
        <button @click="$emit('cancel')" class="close-btn">×</button>
      </div>
      <div class="modal-body">
        <div class="selected-content">
          <h4>选中的内容概览</h4>
          <div class="content-summary">
            <div class="summary-item">
              <span class="summary-label">问题:</span>
              <span class="summary-count">{{ selectedItems.questions.length }} 个</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">原始回答:</span>
              <span class="summary-count">{{ selectedItems.rawAnswers.length }} 个</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">专家回答:</span>
              <span class="summary-count">{{ selectedItems.expertAnswers.length }} 个</span>
            </div>
          </div>
        </div>

        <form @submit.prevent="handleSave">
          <div class="form-section">
            <h4>标准问题</h4>
            <div class="form-group">
              <label for="std_question_title">问题标题 *</label>
              <input
                id="std_question_title"
                v-model="formData.question.title"
                type="text"
                required
                class="form-control"
                placeholder="输入标准问题标题"
              >
            </div>

            <div class="form-group">
              <label for="std_question_body">问题内容</label>
              <textarea
                id="std_question_body"
                v-model="formData.question.body"
                class="form-control"
                rows="4"
                placeholder="输入标准问题的详细内容"
              ></textarea>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="difficulty">难度等级</label>
                <select
                  id="difficulty"
                  v-model="formData.question.difficulty"
                  class="form-control"
                >
                  <option value="beginner">初级</option>
                  <option value="intermediate">中级</option>
                  <option value="advanced">高级</option>
                </select>
              </div>

              <div class="form-group">
                <label for="category">分类</label>
                <input
                  id="category"
                  v-model="formData.question.category"
                  type="text"
                  class="form-control"
                  placeholder="问题分类"
                >
              </div>
            </div>

            <div class="form-group">
              <label for="question_tags">标签</label>
              <div class="tags-input">
                <div class="tags-display">
                  <span
                    v-for="(tag, index) in formData.question.tags"
                    :key="index"
                    class="tag"
                  >
                    {{ tag }}
                    <button
                      type="button"
                      @click="removeQuestionTag(index)"
                      class="tag-remove"
                    >×</button>
                  </span>
                </div>
                <input
                  v-model="newQuestionTag"
                  type="text"
                  class="form-control"
                  placeholder="输入标签后按回车添加"
                  @keydown.enter.prevent="addQuestionTag"
                  @keydown.space.prevent="addQuestionTag"
                >
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>标准回答</h4>
            <div class="form-group">
              <label for="std_answer_content">回答内容 *</label>
              <textarea
                id="std_answer_content"
                v-model="formData.answer.content"
                required
                class="form-control"
                rows="8"
                placeholder="输入标准回答内容"
              ></textarea>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="answer_source">来源</label>
                <input
                  id="answer_source"
                  v-model="formData.answer.source"
                  type="text"
                  class="form-control"
                  placeholder="回答来源"
                >
              </div>

              <div class="form-group">
                <label for="confidence">置信度</label>
                <select
                  id="confidence"
                  v-model="formData.answer.confidence"
                  class="form-control"
                >
                  <option value="high">高</option>
                  <option value="medium">中</option>
                  <option value="low">低</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label for="answer_tags">回答标签</label>
              <div class="tags-input">
                <div class="tags-display">
                  <span
                    v-for="(tag, index) in formData.answer.tags"
                    :key="index"
                    class="tag"
                  >
                    {{ tag }}
                    <button
                      type="button"
                      @click="removeAnswerTag(index)"
                      class="tag-remove"
                    >×</button>
                  </span>
                </div>
                <input
                  v-model="newAnswerTag"
                  type="text"
                  class="form-control"
                  placeholder="输入标签后按回车添加"
                  @keydown.enter.prevent="addAnswerTag"
                  @keydown.space.prevent="addAnswerTag"
                >
              </div>
            </div>
          </div>

          <!-- 参考内容预览 -->
          <div class="form-section">
            <h4>参考内容</h4>
            <div class="reference-content">
              <!-- 参考问题 -->
              <div v-if="selectedItems.questions.length > 0" class="reference-section">
                <h5>参考问题 ({{ selectedItems.questions.length }})</h5>
                <div class="reference-items">
                  <div
                    v-for="question in selectedItems.questions"
                    :key="question.id"
                    class="reference-item"
                  >
                    <h6>{{ question.title }}</h6>
                    <p v-if="question.body">{{ truncateText(question.body, 100) }}</p>
                    <div class="reference-meta">
                      <span>作者: {{ question.author || '未知' }}</span>
                      <span v-if="question.tags?.length">
                        标签: {{ question.tags.join(', ') }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 参考的原始回答 -->
              <div v-if="selectedItems.rawAnswers.length > 0" class="reference-section">
                <h5>参考原始回答 ({{ selectedItems.rawAnswers.length }})</h5>
                <div class="reference-items">
                  <div
                    v-for="answer in selectedItems.rawAnswers"
                    :key="answer.id"
                    class="reference-item"
                  >
                    <p>{{ truncateText(answer.content, 150) }}</p>
                    <div class="reference-meta">
                      <span>作者: {{ answer.author || '未知' }}</span>
                      <span>问题: {{ answer.question?.title }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 参考的专家回答 -->
              <div v-if="selectedItems.expertAnswers.length > 0" class="reference-section">
                <h5>参考专家回答 ({{ selectedItems.expertAnswers.length }})</h5>
                <div class="reference-items">
                  <div
                    v-for="answer in selectedItems.expertAnswers"
                    :key="answer.id"
                    class="reference-item expert-reference"
                  >
                    <p>{{ truncateText(answer.content, 150) }}</p>
                    <div class="reference-meta">
                      <span>作者: {{ answer.author || '未知' }}</span>
                      <span>来源: {{ answer.source }}</span>
                      <span>问题: {{ answer.question?.title }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" @click="$emit('cancel')" class="btn btn-secondary">
              取消
            </button>
            <button type="button" @click="autoGenerate" class="btn btn-info">
              智能生成
            </button>
            <button type="submit" class="btn btn-primary">
              创建标准问答
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { standardQAService } from '@/services/standardQAService'

interface Props {
  selectedItems: {
    questions: any[]
    rawAnswers: any[]
    expertAnswers: any[]
  }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  save: [standardQA: any]
  cancel: []
}>()

// 表单数据
const formData = ref({
  question: {
    title: '',
    body: '',
    difficulty: 'intermediate' as 'beginner' | 'intermediate' | 'advanced',
    category: '',
    tags: [] as string[]
  },
  answer: {
    content: '',
    source: '',
    confidence: 'high' as 'high' | 'medium' | 'low',
    tags: [] as string[]
  }
})

const newQuestionTag = ref('')
const newAnswerTag = ref('')
const isLoading = ref(false)

// 初始化表单数据
onMounted(() => {
  // 如果只有一个问题被选中，使用它作为标准问题的基础
  if (props.selectedItems.questions.length === 1) {
    const question = props.selectedItems.questions[0]
    formData.value.question.title = question.title
    formData.value.question.body = question.body || ''
    formData.value.question.tags = [...(question.tags || [])]
  }

  // 如果有专家回答，优先使用专家回答作为标准回答的基础
  if (props.selectedItems.expertAnswers.length > 0) {
    const expertAnswer = props.selectedItems.expertAnswers[0]
    formData.value.answer.content = expertAnswer.content
    formData.value.answer.source = expertAnswer.source
  } else if (props.selectedItems.rawAnswers.length > 0) {
    // 否则使用原始回答
    const rawAnswer = props.selectedItems.rawAnswers[0]
    formData.value.answer.content = rawAnswer.content
  }
})

// 工具函数
const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 标签管理
const addQuestionTag = () => {
  const tag = newQuestionTag.value.trim()
  if (tag && !formData.value.question.tags.includes(tag)) {
    formData.value.question.tags.push(tag)
    newQuestionTag.value = ''
  }
}

const removeQuestionTag = (index: number) => {
  formData.value.question.tags.splice(index, 1)
}

const addAnswerTag = () => {
  const tag = newAnswerTag.value.trim()
  if (tag && !formData.value.answer.tags.includes(tag)) {
    formData.value.answer.tags.push(tag)
    newAnswerTag.value = ''
  }
}

const removeAnswerTag = (index: number) => {
  formData.value.answer.tags.splice(index, 1)
}

// 智能生成
const autoGenerate = () => {
  // 基于选中的内容智能生成标准问答
  
  // 自动生成问题标题（如果为空）
  if (!formData.value.question.title && props.selectedItems.questions.length > 0) {
    // 使用第一个问题的标题，或者合并多个问题的关键词
    const titles = props.selectedItems.questions.map(q => q.title)
    formData.value.question.title = titles[0] // 简单实现，可以改进为更智能的合并
  }

  // 自动生成标签
  const allTags = new Set<string>()
  
  // 收集问题标签
  props.selectedItems.questions.forEach(q => {
    q.tags?.forEach((tag: string) => allTags.add(tag))
  })
  
  // 将标签添加到问题和回答中
  const tagsArray = Array.from(allTags).slice(0, 8) // 限制标签数量
  formData.value.question.tags = [...new Set([...formData.value.question.tags, ...tagsArray])]
  formData.value.answer.tags = [...new Set([...formData.value.answer.tags, ...tagsArray])]

  // 自动判断难度
  if (props.selectedItems.expertAnswers.length > 0 || 
      props.selectedItems.questions.some(q => q.vote_count > 10)) {
    formData.value.question.difficulty = 'advanced'
  } else if (props.selectedItems.rawAnswers.length > 2) {
    formData.value.question.difficulty = 'intermediate'
  }

  // 自动设置置信度
  if (props.selectedItems.expertAnswers.length > 0) {
    formData.value.answer.confidence = 'high'
  } else if (props.selectedItems.rawAnswers.length > 1) {
    formData.value.answer.confidence = 'medium'
  } else {
    formData.value.answer.confidence = 'low'
  }

  alert('已自动生成部分内容，请检查并完善！')
}

// 保存处理
const handleSave = async () => {
  // 验证必填字段
  if (!formData.value.question.title?.trim()) {
    alert('请输入标准问题标题')
    return
  }

  if (!formData.value.answer.content?.trim()) {
    alert('请输入标准回答内容')
    return
  }

  isLoading.value = true

  try {
    const standardQA = {
      question: {
        title: formData.value.question.title.trim(),
        body: formData.value.question.body?.trim() || '',
        difficulty: formData.value.question.difficulty,
        category: formData.value.question.category?.trim() || '',
        tags: formData.value.question.tags,
        created_at: new Date()
      },
      answer: {
        content: formData.value.answer.content.trim(),
        source: formData.value.answer.source?.trim() || '',
        confidence: formData.value.answer.confidence,
        tags: formData.value.answer.tags,
        created_at: new Date()
      },
      references: {
        question_ids: props.selectedItems.questions.map(q => q.id),
        raw_answer_ids: props.selectedItems.rawAnswers.map(a => a.id),
        expert_answer_ids: props.selectedItems.expertAnswers.map(a => a.id)
      }
    }

    // 调用API保存到数据库
    const result = await standardQAService.createStandardQA(standardQA)
    
    emit('save', result)
  } catch (error) {
    console.error('保存标准问答失败:', error)
    alert('保存失败：' + (error as any).message)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.standard-qa-modal {
  max-width: 900px;
  max-height: 95vh;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 10px;
  width: 90%;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.close-btn:hover {
  background: #f0f0f0;
}

.modal-body {
  padding: 20px;
}

.selected-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.selected-content h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.content-summary {
  display: flex;
  gap: 20px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.summary-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.summary-count {
  font-size: 1.5em;
  font-weight: bold;
  color: #007bff;
}

.form-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.form-section h4 {
  margin: 0 0 20px 0;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 10px;
}

.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s ease;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

textarea.form-control {
  resize: vertical;
  font-family: inherit;
}

.tags-input {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 8px;
  min-height: 80px;
}

.tags-display {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 8px;
}

.tag {
  background: #e9ecef;
  color: #495057;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tag-remove {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tag-remove:hover {
  background: #dee2e6;
  color: #495057;
}

.tags-input .form-control {
  border: none;
  padding: 4px 0;
  margin: 0;
}

.tags-input .form-control:focus {
  box-shadow: none;
}

.reference-content {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
}

.reference-section {
  margin-bottom: 20px;
}

.reference-section h5 {
  margin: 0 0 10px 0;
  color: #555;
  font-size: 1.1em;
}

.reference-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reference-item {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #007bff;
}

.reference-item.expert-reference {
  border-left-color: #28a745;
}

.reference-item h6 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 1em;
}

.reference-item p {
  margin: 0 0 8px 0;
  color: #555;
  line-height: 1.4;
}

.reference-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #666;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
  position: sticky;
  bottom: 0;
  background: white;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
</style>

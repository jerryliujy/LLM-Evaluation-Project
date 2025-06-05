<template>
  <div class="modal-overlay" @click="closeEditor">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ isEditing ? '编辑回答' : '创建回答' }}</h3>
        <button class="modal-close" @click="closeEditor">&times;</button>
      </div>
      
      <div class="modal-body">
        <!-- 问题信息 -->
        <div class="question-info">
          <h4>问题</h4>
          <div class="question-card">
            <h5>{{ question.title }}</h5>
            <p class="question-body">{{ truncateText(question.body || '') }}</p>            <div class="question-meta">
              <span>作者: {{ question.author }}</span>
              <span>投票: {{ question.vote_count }}</span>
              <span>浏览: {{ question.view_count }}</span>
            </div>
          </div>
        </div>

        <!-- 回答编辑器 -->
        <form @submit.prevent="saveAnswer">
          <div class="form-group">
            <label for="answerContent">您的专家回答</label>
            <textarea
              id="answerContent"
              v-model="answerContent"
              rows="12"
              placeholder="请提供详细的专家回答..."
              required
            ></textarea>
            <div class="char-count">
              {{ answerContent.length }} / {{ maxLength }} 字符
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="closeEditor">
              取消
            </button>
            <button 
              type="submit" 
              class="btn-primary" 
              :disabled="saving || answerContent.length === 0 || answerContent.length > maxLength"
            >
              {{ saving ? '保存中...' : (isEditing ? '更新回答' : '创建回答') }}
            </button>
          </div>
        </form>

        <!-- 答案历史（如果是编辑模式） -->
        <div v-if="isEditing && answerHistory.length > 0" class="answer-history">
          <h4>修改历史</h4>
          <div class="history-list">
            <div 
              v-for="(historyItem, index) in answerHistory" 
              :key="index"
              class="history-item"
            >
              <div class="history-header">
                <span class="history-date">{{ formatDate(historyItem.created_at) }}</span>
              </div>
              <div class="history-content">
                {{ truncateText(historyItem.content, 200) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { RawQuestion } from '@/types'
import type { ExpertAnswer } from '@/types/answers'
import { expertService } from '@/services/expertService'

// Props
interface Props {
  question: RawQuestion
  answer?: ExpertAnswer | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
  saved: [answer: ExpertAnswer]
}>()

// 响应式数据
const answerContent = ref('')
const saving = ref(false)
const answerHistory = ref<ExpertAnswer[]>([])
const maxLength = 10000

// 计算属性
const isEditing = computed(() => !!props.answer)

// 生命周期
onMounted(async () => {
  if (props.answer) {
    answerContent.value = props.answer.content
    await loadAnswerHistory()
  }
})

// 监听props变化
watch(() => props.answer, (newAnswer) => {
  if (newAnswer) {
    answerContent.value = newAnswer.content
  } else {
    answerContent.value = ''
  }
})

// 方法
async function saveAnswer() {
  if (!answerContent.value.trim()) return
  
  saving.value = true
  try {
    let savedAnswer: ExpertAnswer
    
    if (isEditing.value && props.answer) {
      // 更新现有回答
      savedAnswer = await expertService.updateAnswer(props.answer.id, {
        content: answerContent.value.trim()
      })
    } else {
      // 创建新回答
      savedAnswer = await expertService.createAnswer({
        question_id: props.question.id,
        content: answerContent.value.trim()
      })
    }
    
    emit('saved', savedAnswer)
  } catch (error) {
    console.error('保存回答失败:', error)
    alert('保存回答失败，请重试')
  } finally {
    saving.value = false
  }
}

async function loadAnswerHistory() {
  if (!props.question.id) return
  
  try {
    answerHistory.value = await expertService.getAnswerHistory(props.question.id)
  } catch (error) {
    console.error('加载回答历史失败:', error)
  }
}

function closeEditor() {
  emit('close')
}

function formatDate(date: string | Date): string {
  return new Date(date).toLocaleString('zh-CN')
}

function truncateText(text: string, maxLength = 500): string {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}
</script>

<style scoped>
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
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  background-color: #f8f9fa;
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
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  padding: 20px;
}

.question-info {
  margin-bottom: 30px;
}

.question-info h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.question-card {
  background-color: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
}

.question-card h5 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 16px;
}

.question-body {
  margin: 10px 0;
  color: #666;
  line-height: 1.5;
}

.question-meta {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: #888;
  margin-top: 10px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
  color: #333;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 200px;
}

.form-group textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.answer-history {
  margin-top: 30px;
  border-top: 1px solid #e0e0e0;
  padding-top: 20px;
}

.answer-history h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 10px;
  background-color: #f8f9fa;
}

.history-header {
  margin-bottom: 10px;
}

.history-date {
  font-size: 12px;
  color: #666;
}

.history-content {
  color: #333;
  line-height: 1.5;
  font-size: 14px;
}

/* 按钮样式 */
.btn-primary, .btn-secondary {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-primary:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 10px;
  }
  
  .question-meta {
    flex-direction: column;
    gap: 5px;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style>

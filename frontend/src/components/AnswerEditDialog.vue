<template>
  <div v-if="dialogVisible" class="modal-overlay">
    <div class="modal-content">
      <div class="modal-header">
        <span class="modal-title">{{ dialogTitle }}</span>
        <button class="modal-close" @click="handleClose">×</button>
      </div>
      <form @submit.prevent="handleSave">
        <div class="form-group">
          <label>回答内容</label>
          <textarea v-model="formData.answer" rows="6" maxlength="3000" required placeholder="请输入回答内容"></textarea>
          <div class="form-hint">{{ formData.answer.length }}/3000</div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>回答者</label>
            <input v-model="formData.answered_by" type="text" placeholder="请输入回答者名称" />
          </div>
          <div class="form-group" v-if="type === 'raw'">
            <label>投票数</label>
            <input v-model="formData.upvotes" type="number" min="0" placeholder="请输入投票数" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>回答时间</label>
            <input v-model="formData.answered_at" type="datetime-local" />
          </div>
          <div class="form-group" v-if="type === 'expert'">
            <label>来源</label>
            <input v-model="formData.source" type="text" placeholder="请输入答案来源" />
          </div>
        </div>
        <div class="form-group" v-if="!answer">
          <label>关联问题</label>
          <select v-model="formData.question_id">
            <option value="">请选择关联的问题</option>
            <option v-for="question in availableQuestions" :key="question.id" :value="question.id">
              {{ question.title }}
            </option>
          </select>
        </div>
        <div class="modal-footer">
          <button type="button" @click="handleClose">取消</button>
          <button type="submit" :disabled="loading">{{ isEdit ? '更新' : '创建' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { RawAnswer, ExpertAnswer } from '@/types/answers'
import { useRawQuestionStore } from '@/store/rawQuestionStore'

interface Props {
  visible: boolean
  answer: RawAnswer | ExpertAnswer | null
  type: 'raw' | 'expert'
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'save', answer: RawAnswer | ExpertAnswer): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const store = useRawQuestionStore()

const loading = ref(false)

const formData = ref({
  answer: '',
  answered_by: '',
  upvotes: '0',
  question_id: 0,
  answered_at: '',
  source: '',
  created_by: '',
  create_time: ''
})

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const isEdit = computed(() => !!props.answer)

const dialogTitle = computed(() => {
  const typeText = props.type === 'expert' ? '专家回答' : '原始回答'
  return isEdit.value ? `编辑${typeText}` : `添加${typeText}`
})

const availableQuestions = computed(() => store.questions)

const resetForm = () => {
  const now = new Date().toISOString().slice(0, 16)
  formData.value = {
    answer: '',
    answered_by: '',
    upvotes: '0',
    question_id: 0,
    answered_at: now,
    source: '',
    created_by: '',
    create_time: now
  }
}

watch(() => props.answer, (newAnswer) => {
  if (newAnswer) {
    let answered_at = ''
    if (newAnswer.answered_at) {
      if (typeof newAnswer.answered_at === 'string') {
        answered_at = newAnswer.answered_at.length > 16 ? newAnswer.answered_at.slice(0, 16) : newAnswer.answered_at
      } else {
        answered_at = new Date(newAnswer.answered_at).toISOString().slice(0, 16)
      }
    }
    formData.value = {
      answer: newAnswer.answer,
      answered_by: newAnswer.answered_by || '',
      upvotes: String((newAnswer as RawAnswer).upvotes || '0'),
      question_id: newAnswer.question_id,
      answered_at,
      source: (newAnswer as any).source || '',
      created_by: (newAnswer as any).created_by || '',
      create_time: (newAnswer as any).create_time || ''
    }
  } else {
    resetForm()
  }
}, { immediate: true })

const handleClose = () => {
  dialogVisible.value = false
  resetForm()
}

const handleSave = async () => {
  // 简单校验
  if (!formData.value.answer || formData.value.answer.length < 10) {
    alert('请输入至少10个字符的回答内容')
    return
  }
  if (!formData.value.question_id && !props.answer) {
    alert('请选择关联问题')
    return
  }
  if (props.type === 'expert' && !formData.value.source) {
    alert('请输入专家回答来源')
    return
  }
  loading.value = true
  try {
    const baseAnswerData = {
      id: props.answer?.id || 0,
      answer: formData.value.answer,
      question_id: formData.value.question_id,
      is_deleted: false
    }
    if (props.type === 'expert') {
      const expertAnswerData: ExpertAnswer = {
        ...baseAnswerData,
        answered_by: formData.value.answered_by,
        answered_at: formData.value.answered_at,
        source: formData.value.source
      }
      emit('save', expertAnswerData)
    } else {
      const rawAnswerData: RawAnswer = {
        ...baseAnswerData,
        answered_by: formData.value.answered_by,
        answered_at: formData.value.answered_at,
        upvotes: formData.value.upvotes
      }
      emit('save', rawAnswerData)
    }
    handleClose()
  } catch (error) {
    alert('保存失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.25);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 420px;
  max-width: 95vw;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  padding: 28px 28px 18px 28px;
  position: relative;
  animation: modal-fade-in 0.18s;
}
@keyframes modal-fade-in {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: none; }
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}
.modal-title {
  font-size: 21px;
  font-weight: 600;
  color: #222;
}
.modal-close {
  background: none;
  border: none;
  font-size: 26px;
  cursor: pointer;
  color: #aaa;
  transition: color 0.2s;
}
.modal-close:hover {
  color: #409eff;
}
.form-group {
  margin-bottom: 18px;
  display: flex;
  flex-direction: column;
}
.form-group label {
  font-size: 15px;
  color: #333;
  margin-bottom: 6px;
  font-weight: 500;
}
.form-row {
  display: flex;
  gap: 16px;
}
.form-row .form-group {
  flex: 1;
  margin-bottom: 0;
}
textarea, input, select {
  font-size: 15px;
  padding: 7px 10px;
  border: 1px solid #e0e0e0;
  border-radius: 5px;
  outline: none;
  background: #fafbfc;
  transition: border-color 0.2s;
}
textarea:focus, input:focus, select:focus {
  border-color: #409eff;
  background: #fff;
}
textarea {
  resize: vertical;
  min-height: 80px;
}
.form-hint {
  font-size: 12px;
  color: #aaa;
  margin-top: 2px;
  align-self: flex-end;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  margin-top: 18px;
}
.modal-footer button {
  min-width: 90px;
  padding: 8px 0;
  border-radius: 5px;
  border: none;
  background: #f3f4f6;
  color: #333;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: background 0.18s, color 0.18s;
}
.modal-footer button[type="submit"] {
  background: #409eff;
  color: #fff;
}
.modal-footer button[type="submit"]:hover {
  background: #337ecc;
}
.modal-footer button[type="button"]:hover {
  background: #e6e8eb;
}
.modal-footer button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
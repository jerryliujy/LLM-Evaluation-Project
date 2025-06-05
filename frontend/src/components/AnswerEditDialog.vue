<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="700px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="80px"
      label-position="top"
    >
      <el-form-item label="回答内容" prop="content">
        <el-input
          v-model="formData.content"
          type="textarea"
          placeholder="请输入回答内容"
          :rows="8"
          maxlength="3000"
          show-word-limit
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="作者">
            <el-input
              v-model="formData.author"
              placeholder="请输入作者名称"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="投票数">
            <el-input-number
              v-model="formData.vote_count"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20" v-if="type === 'expert'">
        <el-col :span="12">
          <el-form-item label="来源" prop="source">
            <el-input
              v-model="formData.source"
              placeholder="请输入答案来源"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="创建时间">
            <el-date-picker
              v-model="formData.created_at"
              type="datetime"
              placeholder="选择创建时间"
              style="width: 100%"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row v-if="type === 'raw'">
        <el-col :span="12">
          <el-form-item label="回答时间">
            <el-date-picker
              v-model="formData.answered_at"
              type="datetime"
              placeholder="选择回答时间"
              style="width: 100%"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 选择问题 -->
      <el-form-item label="关联问题" prop="question_id" v-if="!answer">
        <el-select
          v-model="formData.question_id"
          placeholder="请选择关联的问题"
          style="width: 100%"
          filterable
        >
          <el-option
            v-for="question in availableQuestions"
            :key="question.id"
            :label="question.title"
            :value="question.id"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="loading">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { RawAnswer, ExpertAnswer } from '@/types/answers'
import { useRawQuestionStore } from '@/store/rawQuestionStore'

interface Props {
  visible: boolean
  answer: RawAnswer | ExpertAnswer | null
  type: 'raw' | 'expert'
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'save'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const store = useRawQuestionStore()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const formData = ref({
  content: '',
  author: '',
  vote_count: 0,
  question_id: 0,
  source: '', // 专家回答专用
  created_at: '', // 专家回答专用
  answered_at: '' // 原始回答专用
})

// 计算属性
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

// 重置表单 - 需要在watch之前定义
const resetForm = () => {
  const now = new Date().toISOString().slice(0, 19).replace('T', ' ')
  formData.value = {
    content: '',
    author: '',
    vote_count: 0,
    question_id: 0,
    source: '',
    created_at: now,
    answered_at: now
  }
}

// 表单验证规则
const rules: FormRules = {
  content: [
    { required: true, message: '请输入回答内容', trigger: 'blur' },
    { min: 10, message: '回答内容至少需要10个字符', trigger: 'blur' }
  ],
  question_id: [
    { required: true, message: '请选择关联问题', trigger: 'change' }
  ],
  source: [
    { 
      required: true, 
      message: '请输入专家回答来源', 
      trigger: 'blur',      // 只在专家回答时验证
      validator: (rule: any, value: string, callback: (error?: Error) => void) => {
        if (props.type === 'expert' && !value) {
          callback(new Error('请输入专家回答来源'))
        } else {
          callback()
        }
      }
    }
  ]
}

// 监听props变化
watch(() => props.answer, (newAnswer) => {
  if (newAnswer) {
    formData.value = {
      content: newAnswer.content,
      author: newAnswer.author || '',
      vote_count: newAnswer.vote_count || 0,
      question_id: newAnswer.question_id,
      source: (newAnswer as ExpertAnswer).source || '',
      created_at: (newAnswer as ExpertAnswer).created_at ? 
        (typeof (newAnswer as ExpertAnswer).created_at === 'string' 
          ? (newAnswer as ExpertAnswer).created_at as string
          : ((newAnswer as ExpertAnswer).created_at as Date).toISOString()) : '',
      answered_at: (newAnswer as RawAnswer).answered_at ? 
        (typeof (newAnswer as RawAnswer).answered_at === 'string' 
          ? (newAnswer as RawAnswer).answered_at as string
          : ((newAnswer as RawAnswer).answered_at as Date).toISOString()) : ''
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// 对话框方法
const handleClose = () => {
  dialogVisible.value = false
  resetForm()
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    const baseAnswerData = {
      id: props.answer?.id || Date.now() + Math.random(),
      content: formData.value.content,
      author: formData.value.author,
      vote_count: formData.value.vote_count,
      question_id: formData.value.question_id,
      is_deleted: false
    }

    if (props.type === 'expert') {
      const expertAnswerData: ExpertAnswer = {
        ...baseAnswerData,
        source: formData.value.source,
        created_at: formData.value.created_at || new Date().toISOString()
      }

      if (isEdit.value) {
        store.updateExpertAnswer(expertAnswerData)
      } else {
        store.addExpertAnswer(expertAnswerData)
      }
    } else {
      const rawAnswerData: RawAnswer = {
        ...baseAnswerData,
        answered_at: formData.value.answered_at || new Date().toISOString()
      }

      if (isEdit.value) {
        store.updateRawAnswer(rawAnswerData)
      } else {
        store.addRawAnswer(rawAnswerData)
      }
    }

    emit('save')
    ElMessage.success(isEdit.value ? '回答已更新' : '回答已创建')
  } catch (error) {
    console.error('保存回答失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
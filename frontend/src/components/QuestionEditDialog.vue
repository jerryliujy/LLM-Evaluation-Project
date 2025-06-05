<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '编辑问题' : '添加问题'"
    width="800px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="80px"
      label-position="top"
    >
      <el-form-item label="问题标题" prop="title">
        <el-input
          v-model="formData.title"
          placeholder="请输入问题标题"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="问题内容" prop="body">
        <el-input
          v-model="formData.body"
          type="textarea"
          placeholder="请输入问题的详细内容"
          :rows="6"
          maxlength="2000"
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
          <el-form-item label="URL">
            <el-input
              v-model="formData.url"
              placeholder="原始问题链接（可选）"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="浏览数">
            <el-input-number
              v-model="formData.view_count"
              :min="0"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="投票数">
            <el-input-number
              v-model="formData.vote_count"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="发布时间">
            <el-date-picker
              v-model="formData.issued_at"
              type="datetime"
              placeholder="选择发布时间"
              style="width: 100%"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="标签">
        <div class="tags-input">
          <el-tag
            v-for="tag in formData.tags"
            :key="tag"
            closable
            :disable-transitions="false"
            @close="removeTag(tag)"
            class="tag-item"
          >
            {{ tag }}
          </el-tag>
          <el-input
            v-if="inputVisible"
            ref="inputRef"
            v-model="inputValue"
            size="small"
            style="width: 120px"
            @keyup.enter="handleInputConfirm"
            @blur="handleInputConfirm"
          />
          <el-button v-else size="small" @click="showInput">
            + 添加标签
          </el-button>
        </div>
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
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { RawQuestion } from '@/types/questions'

interface Props {
  visible: boolean
  question: RawQuestion | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'save', questionData: Partial<RawQuestion>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const formRef = ref<FormInstance>()
const loading = ref(false)
const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref()

// 表单数据
const formData = ref({
  title: '',
  body: '',
  author: '',
  url: '',
  view_count: 0,
  vote_count: 0,
  issued_at: '',
  tags: [] as string[]
})

// 计算属性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const isEdit = computed(() => !!props.question)

// 重置表单
const resetForm = () => {
  formData.value = {
    title: '',
    body: '',
    author: '',
    url: '',
    view_count: 0,
    vote_count: 0,
    issued_at: new Date().toISOString().slice(0, 19).replace('T', ' '),
    tags: []
  }
  inputVisible.value = false
  inputValue.value = ''
}

// 表单验证规则
const rules: FormRules = {
  title: [
    { required: true, message: '请输入问题标题', trigger: 'blur' },
    { min: 5, message: '标题至少需要5个字符', trigger: 'blur' }
  ],
  body: [
    { required: true, message: '请输入问题内容', trigger: 'blur' },
    { min: 10, message: '内容至少需要10个字符', trigger: 'blur' }
  ]
}

// 监听props变化
watch(() => props.question, (newQuestion) => {
  if (newQuestion) {
    formData.value = {
      title: newQuestion.title,
      body: newQuestion.body || '',
      author: newQuestion.author || '',
      url: newQuestion.url || '',
      view_count: newQuestion.view_count || 0,
      vote_count: newQuestion.vote_count || 0,
      issued_at: newQuestion.issued_at ? 
        (typeof newQuestion.issued_at === 'string' ? newQuestion.issued_at : newQuestion.issued_at.toISOString()) : '',
      tags: [...(newQuestion.tags || [])]
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// 标签相关方法
const removeTag = (tag: string) => {
  formData.value.tags = formData.value.tags.filter(t => t !== tag)
}

const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const handleInputConfirm = () => {
  const value = inputValue.value.trim()
  if (value && !formData.value.tags.includes(value)) {
    formData.value.tags.push(value)
  }
  inputVisible.value = false
  inputValue.value = ''
}

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

    const questionData: Partial<RawQuestion> = {
      title: formData.value.title,
      body: formData.value.body,
      author: formData.value.author,
      url: formData.value.url,
      view_count: formData.value.view_count,
      vote_count: formData.value.vote_count,
      issued_at: formData.value.issued_at || new Date().toISOString(),
      tags: formData.value.tags,
    }

    // 如果是编辑模式，包含ID
    if (isEdit.value && props.question) {
      questionData.id = props.question.id
    }

    emit('save', questionData)
  } catch (error) {
    console.error('保存问题失败:', error)
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.tags-input {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
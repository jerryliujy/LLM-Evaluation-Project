<template>
  <div v-if="visible" class="dialog-overlay" @click="handleClose">
    <div class="dialog-container" @click.stop>
      <div class="dialog-header">
        <h3>{{ isEdit ? '编辑问题' : '添加新问题' }}</h3>
        <button class="close-btn" @click="handleClose">&times;</button>
      </div>
      
      <div class="dialog-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="title">问题标题 *</label>
            <input
              id="title"
              v-model="formData.title"
              type="text"
              placeholder="请输入问题标题"
              maxlength="200"
              required
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="body">问题内容</label>
            <textarea
              id="body"
              v-model="formData.body"
              placeholder="请输入问题的详细内容"
              rows="6"
              maxlength="2000"
              class="form-textarea"
            ></textarea>
          </div>          <div class="form-row">
            <div class="form-group">
              <label for="author">作者</label>
              <input
                id="author"
                v-model="formData.author"
                type="text"
                placeholder="请输入作者名称"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="url">原始链接</label>
              <input
                id="url"
                v-model="formData.url"
                type="url"
                placeholder="原始问题链接（可选）"
                class="form-input"
              />
            </div>
          </div>

          <!-- 可选的元数据字段 -->
          <div class="form-section">
            <h4 class="section-title">可选信息</h4>
            
            <div class="form-row">
              <div class="form-group">
                <label for="votes">投票数</label>
                <input
                  id="votes"
                  v-model="formData.votes"
                  type="text"
                  placeholder="如：123 或 1.2k"
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="views">浏览数</label>
                <input
                  id="views"
                  v-model="formData.views"
                  type="text"
                  placeholder="如：456 或 2.5k"
                  class="form-input"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="issued_at">发布时间</label>
              <input
                id="issued_at"
                v-model="formData.issued_at"
                type="datetime-local"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="tags">标签</label>
            <input
              id="tags"
              v-model="tagsInput"
              type="text"
              placeholder="输入标签，用逗号分隔"
              class="form-input"
            />
            <div v-if="formData.tags && formData.tags.length > 0" class="tags-preview">
              <span v-for="tag in formData.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>

          <div class="form-group">
            <label>
              <input
                v-model="formData.is_deleted"
                type="checkbox"
                class="form-checkbox"
              />
              标记为已删除
            </label>
          </div>
        </form>
      </div>

      <div class="dialog-footer">
        <button type="button" @click="handleClose" class="btn btn-secondary">
          取消
        </button>
        <button type="button" @click="handleSubmit" class="btn btn-primary">
          {{ isEdit ? '更新' : '创建' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { RawQuestion } from '@/types/questions'

interface Props {
  visible: boolean
  question?: RawQuestion | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'save', data: Partial<RawQuestion>): void
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  question: null
})

const emit = defineEmits<Emits>()

const formData = ref<Partial<RawQuestion>>({
  title: '',
  body: '',
  author: '',
  url: '',
  tags: [],
  votes: '',
  views: '',
  issued_at: '',
  is_deleted: false
})

const tagsInput = ref('')

const isEdit = computed(() => !!props.question?.id)

// 格式化日期时间为本地输入格式
const formatDateTimeLocal = (dateTime: string | Date): string => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  return date.toISOString().slice(0, 16) // 格式: YYYY-MM-DDTHH:mm
}

// 监听问题变化，初始化表单数据
watch(() => props.question, (newQuestion) => {
  if (newQuestion) {
    formData.value = {
      title: newQuestion.title || '',
      body: newQuestion.body || '',
      author: newQuestion.author || '',
      url: newQuestion.url || '',
      tags: newQuestion.tags || [],
      votes: newQuestion.votes || '',
      views: newQuestion.views || '',
      issued_at: newQuestion.issued_at ? formatDateTimeLocal(newQuestion.issued_at) : '',
      is_deleted: newQuestion.is_deleted || false
    }
    tagsInput.value = newQuestion.tags?.join(', ') || ''
  } else {
    // 新建问题，重置表单
    formData.value = {
      title: '',
      body: '',
      author: '',
      url: '',
      tags: [],
      votes: '',
      views: '',
      issued_at: '',
      is_deleted: false
    }
    tagsInput.value = ''
  }
}, { immediate: true })

// 监听标签输入变化
watch(tagsInput, (newValue) => {
  if (newValue) {
    formData.value.tags = newValue.split(',').map(tag => tag.trim()).filter(tag => tag)
  } else {
    formData.value.tags = []
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = () => {
  if (!formData.value.title?.trim()) {
    alert('请输入问题标题')
    return
  }  // 清理数据
  const submitData: Partial<RawQuestion> = {
    title: formData.value.title.trim(),
    body: formData.value.body?.trim() || '',
    author: formData.value.author?.trim() || '',
    url: formData.value.url?.trim() || '',
    tags_json: formData.value.tags || [],  // 修正字段名为 tags_json
    votes: formData.value.votes?.trim() || undefined,
    views: formData.value.views?.trim() || undefined,
    issued_at: formData.value.issued_at || undefined,
    is_deleted: formData.value.is_deleted || false
  }

  // 如果是编辑模式，包含ID
  if (isEdit.value && props.question?.id) {
    submitData.id = props.question.id
  }

  emit('save', submitData)
}
</script>

<style scoped>
.dialog-overlay {
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

.dialog-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e4e7ed;
  background: #f8f9fb;
}

.dialog-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #909399;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #e4e7ed;
  color: #606266;
}

.dialog-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-section {
  margin: 24px 0;
  padding: 16px;
  background: #f8f9fb;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
}

.form-checkbox {
  margin-right: 8px;
}

.tags-preview {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  display: inline-block;
  padding: 4px 8px;
  background: #f0f2f5;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
  background: #f8f9fb;
}

.btn {
  padding: 10px 20px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  background: white;
  min-width: 80px;
}

.btn:hover {
  opacity: 0.8;
}

.btn-primary {
  background: #409eff;
  border-color: #409eff;
  color: white;
}

.btn-primary:hover {
  background: #337ecc;
  border-color: #337ecc;
}

.btn-secondary {
  background: #909399;
  border-color: #909399;
  color: white;
}

.btn-secondary:hover {
  background: #73767a;
  border-color: #73767a;
}
</style>

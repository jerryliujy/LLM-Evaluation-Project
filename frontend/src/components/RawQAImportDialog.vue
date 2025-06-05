<template>  <!-- 遮罩层 -->
  <div v-if="dialogVisible" class="modal-overlay" @click="handleClose">
    <!-- 弹窗主体 -->
    <div class="modal-container" @click.stop>
      <!-- 弹窗头部 -->
      <div class="modal-header">
        <h3>导入原始问答数据</h3>
        <button class="close-btn" @click="handleClose">×</button>
      </div>

      <!-- 弹窗内容 -->
      <div class="modal-body">
        <div class="import-dialog-content">
          <!-- 说明部分 -->
          <div class="import-info">
            <h4>导入说明</h4>
            <p>将原始问答数据直接导入到您的原始问题池中，不依赖于任何数据集。</p>
            <ul>
              <li>导入的数据将关联到当前用户</li>
              <li>支持 JSON 格式文件</li>
              <li>数据将存储在您的个人原始问题池中</li>
            </ul>
          </div>

          <!-- 格式示例 -->
          <div class="format-example">
            <h4>数据格式示例</h4>
            <pre class="code-example">{{ formatExample }}</pre>
          </div>

          <!-- 文件上传区域 -->
          <div class="upload-section">
            <div 
              class="upload-area"
              :class="{ 'drag-over': isDragOver }"
              @drop="handleDrop"
              @dragover.prevent="isDragOver = true"
              @dragleave="isDragOver = false"
              @click="triggerFileInput"
            >
              <div class="upload-icon">📁</div>
              <p>点击或拖拽文件到此区域上传</p>
              <p class="upload-hint">支持 .json 文件</p>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept=".json"
              style="display: none"
              @change="handleFileSelect"
            />
          </div>

          <!-- 数据预览 -->
          <div v-if="previewData.length > 0" class="preview-section">
            <h4>数据预览</h4>
            <div class="preview-stats">
              <span>将导入 {{ previewData.length }} 个问题</span>
              <span>包含 {{ totalAnswers }} 个回答</span>
            </div>
            
            <div class="preview-list">
              <div
                v-for="(item, index) in previewData.slice(0, 3)"
                :key="index"
                class="preview-item"
              >
                <h5>{{ item.title || '无标题' }}</h5>
                <p v-if="item.body">{{ truncateText(item.body, 100) }}</p>
                <div class="preview-meta">
                  <span v-if="item.author">作者: {{ item.author }}</span>
                  <span v-if="item.answers">回答数: {{ item.answers.length }}</span>
                  <span v-if="item.tags">标签: {{ item.tags.join(', ') }}</span>
                </div>
              </div>
              <div v-if="previewData.length > 3" class="more-items">
                ... 还有 {{ previewData.length - 3 }} 个问题
              </div>
            </div>
          </div>

          <!-- 错误信息 -->
          <div v-if="error" class="error-section">
            <div class="alert alert-error">
              <div class="alert-icon">⚠️</div>
              <div class="alert-message">{{ error }}</div>
            </div>
          </div>

          <!-- 上传进度 -->
          <div v-if="uploading" class="progress-section">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            </div>
            <p>正在上传数据... {{ uploadProgress }}%</p>
          </div>

          <!-- 上传结果 -->
          <div v-if="uploadResult" class="result-section">
            <div class="alert alert-success">
              <div class="alert-icon">✅</div>
              <div class="alert-content">
                <h4>导入成功</h4>
                <div class="result-details">
                  <p>成功导入 {{ uploadResult.imported_questions }} 个问题</p>
                  <p>成功导入 {{ uploadResult.imported_answers }} 个回答</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 弹窗底部 -->
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="handleClose">取消</button>
        <button 
          v-if="!uploadResult"
          class="btn btn-primary" 
          @click="handleImport"
          :disabled="!previewData.length || uploading"
        >
          <span v-if="uploading">导入中...</span>
          <span v-else>开始导入</span>
        </button>
        <button 
          v-else
          class="btn btn-success"
          @click="handleClose"
        >
          完成
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { dataImportService } from '@/services/dataImportService'

// 创建一个简单的消息提示函数
const showMessage = (message: string, type: 'success' | 'error' | 'warning' = 'success') => {
  // 创建临时提示元素
  const msgEl = document.createElement('div')
  msgEl.textContent = message
  msgEl.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 12px 24px;
    border-radius: 6px;
    color: white;
    font-size: 14px;
    z-index: 9999;
    background: ${type === 'success' ? '#67c23a' : type === 'error' ? '#f56c6c' : '#e6a23c'};
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  `
  
  document.body.appendChild(msgEl)
  
  // 3秒后移除
  setTimeout(() => {
    if (msgEl.parentNode) {
      msgEl.parentNode.removeChild(msgEl)
    }
  }, 3000)
}

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'imported'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const fileInput = ref<HTMLInputElement>()
const isDragOver = ref(false)
const previewData = ref<any[]>([])
const error = ref('')
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadResult = ref<any>(null)

// 计算属性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const totalAnswers = computed(() => {
  return previewData.value.reduce((total, item) => {
    return total + (item.answers?.length || 0)
  }, 0)
})

const formatExample = `[
  {
    "title": "如何在Docker中运行Python应用？",
    "body": "我想在Docker容器中运行我的Python应用，应该怎么配置Dockerfile？",
    "url": "https://example.com/question/1",
    "votes": "15",
    "views": "1.2k",
    "author": "developer123",
    "tags": ["docker", "python", "deployment"],
    "issued_at": "2024-01-01 12:00",
    "answers": [
      {
        "answer": "你可以使用官方Python镜像作为基础...",
        "upvotes": "8",
        "answered_by": "expert_user",
        "answered_at": "2024-01-01 13:00"
      }
    ]
  }
]`

// 监听对话框关闭，重置状态
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    resetState()
  }
})

// 方法
const resetState = () => {
  previewData.value = []
  error.value = ''
  uploading.value = false
  uploadProgress.value = 0
  uploadResult.value = null
  isDragOver.value = false
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    processFile(file)
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  const file = event.dataTransfer?.files[0]
  if (file) {
    processFile(file)
  }
}

const processFile = async (file: File) => {
  error.value = ''
  
  if (!file.name.endsWith('.json')) {
    error.value = '请选择 JSON 格式的文件'
    return
  }

  try {
    const text = await file.text()
    const data = JSON.parse(text)
    
    if (!Array.isArray(data)) {
      error.value = '文件格式错误：数据应该是一个数组'
      return
    }

    // 验证数据格式
    const validation = validateData(data)
    if (!validation.isValid) {
      error.value = validation.errors.join('\n')
      return
    }    previewData.value = data
    showMessage(`成功加载 ${data.length} 个问题`, 'success')
  } catch (err) {
    error.value = '文件解析失败：请检查 JSON 格式是否正确'
    console.error('File processing error:', err)
  }
}

const validateData = (data: any[]) => {
  const errors: string[] = []
  
  if (data.length === 0) {
    errors.push('数据不能为空')
    return { isValid: false, errors }
  }

  data.forEach((item, index) => {
    if (!item.title) {
      errors.push(`第 ${index + 1} 项缺少标题(title)字段`)
    }
    if (item.answers && !Array.isArray(item.answers)) {
      errors.push(`第 ${index + 1} 项的回答(answers)字段格式错误`)
    }
  })

  return {
    isValid: errors.length === 0,
    errors
  }
}

const handleImport = async () => {
  if (previewData.value.length === 0) {
    error.value = '没有可导入的数据'
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  error.value = ''

  try {
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    // 调用导入API
    const result = await dataImportService.uploadRawQAToPool(previewData.value)
    
    clearInterval(progressInterval)
    uploadProgress.value = 100
      uploadResult.value = result
    emit('imported')
    showMessage('数据导入成功', 'success')
  } catch (err: any) {
    error.value = err.message || '导入失败，请重试'
    console.error('Import error:', err)
  } finally {
    uploading.value = false
  }
}

const handleClose = () => {
  emit('update:visible', false)
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
/* 模态框遮罩层 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 模态框容器 */
.modal-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 模态框头部 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  background: #f8f9fa;
}

.modal-header h3 {
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
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #606266;
}

/* 模态框主体 */
.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

/* 模态框底部 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
  background: #f8f9fa;
}

/* 按钮样式 */
.btn {
  padding: 8px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #409eff;
  border-color: #409eff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #337ecc;
}

.btn-secondary {
  background: white;
  color: #606266;
}

.btn-secondary:hover {
  background: #f5f7fa;
}

.btn-success {
  background: #67c23a;
  border-color: #67c23a;
  color: white;
}

.btn-success:hover {
  background: #529b2e;
}

/* 警告和进度条样式 */
.alert {
  padding: 12px;
  border-radius: 4px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.alert-error {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  color: #f56c6c;
}

.alert-success {
  background: #f0f9ff;
  border: 1px solid #c6e2ff;
  color: #409eff;
}

.alert-icon {
  font-size: 16px;
}

.alert-message {
  flex: 1;
}

.alert-content {
  flex: 1;
}

.alert-content h4 {
  margin: 0 0 8px 0;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: #e4e7ed;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #409eff;
  transition: width 0.3s ease;
}

.import-dialog-content {
  max-height: 70vh;
  overflow-y: auto;
}

.import-info {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.import-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.import-info p {
  margin: 0 0 8px 0;
  color: #606266;
}

.import-info ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
  color: #606266;
}

.format-example {
  margin-bottom: 20px;
}

.format-example h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.code-example {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  font-size: 12px;
  color: #606266;
  overflow-x: auto;
  white-space: pre-wrap;
  margin: 0;
}

.upload-section {
  margin-bottom: 20px;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: #409eff;
  background: #f0f9ff;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-area p {
  margin: 8px 0;
  color: #606266;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.preview-section {
  margin-bottom: 20px;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.preview-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.preview-list {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.preview-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-item h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.preview-item p {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 12px;
  line-height: 1.4;
}

.preview-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #909399;
}

.more-items {
  padding: 12px;
  text-align: center;
  color: #909399;
  font-style: italic;
}

.error-section,
.progress-section,
.result-section {
  margin-bottom: 20px;
}

.progress-section p {
  text-align: center;
  margin-top: 8px;
  color: #606266;
}

.result-details p {
  margin: 4px 0;
}
</style>

<template>
  <div class="data-import-container">
    <div class="header">
      <h2>数据导入</h2>
      <p class="subtitle">支持导入JSON格式的问答数据到数据库</p>
    </div>

    <!-- 文件上传区域 -->
    <div class="upload-section">
      <h3>上传数据文件</h3>
      <div 
        class="upload-area" 
        @drop="handleDrop" 
        @dragover.prevent 
        @dragenter.prevent
        @dragleave="handleDragLeave"
        :class="{ 'drag-over': isDragOver }"
      >
        <div v-if="!uploading" class="upload-content">
          <div class="upload-icon">📁</div>
          <p class="upload-text">
            拖拽JSON文件到此处，或
            <label class="file-input-label">
              <input
                type="file"
                ref="fileInput"
                @change="handleFileSelect"
                accept=".json"
                class="file-input"
              />
              点击选择文件
            </label>
          </p>
          <p class="upload-hint">支持的格式: .json</p>
        </div>

        <div v-else class="upload-progress">
          <div class="progress-icon">⏳</div>
          <p>正在上传和处理数据...</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="error" class="error-message">
        <h4>❌ 错误</h4>
        <p>{{ error }}</p>
        <button @click="clearError" class="clear-error-btn">清除</button>
      </div>

      <!-- 上传结果 -->
      <div v-if="uploadResult" class="upload-result success">
        <h4>✅ 上传成功</h4>
        <div class="result-stats">
          <div class="stat-item">
            <span class="stat-label">导入问题:</span>
            <span class="stat-value">{{ uploadResult.imported_questions || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">导入答案:</span>
            <span class="stat-value">{{ uploadResult.imported_answers || 0 }}</span>
          </div>
          <div v-if="uploadResult.imported_expert_answers" class="stat-item">
            <span class="stat-label">专家答案:</span>
            <span class="stat-value">{{ uploadResult.imported_expert_answers }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据预览 -->
    <div v-if="previewData.length > 0" class="preview-section">
      <h3>数据预览</h3>
      <div class="preview-stats">
        <div class="stat-card">
          <div class="stat-number">{{ previewData.length }}</div>
          <div class="stat-label">总记录数</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ getPreviewStats().questions }}</div>
          <div class="stat-label">问题数</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ getPreviewStats().answers }}</div>
          <div class="stat-label">答案数</div>
        </div>
      </div>

      <div class="preview-table-container">
        <table class="preview-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>作者</th>
              <th>投票数</th>
              <th>浏览数</th>
              <th>答案数</th>
              <th>发布时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in previewData.slice(0, 10)" :key="index">
              <td class="title-cell">{{ item.title }}</td>
              <td>{{ item.author }}</td>
              <td>{{ item.votes }}</td>
              <td>{{ item.views }}</td>
              <td>{{ (item.answers || []).length }}</td>
              <td>{{ formatDate(item.issued_at) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="previewData.length > 10" class="preview-note">
          显示前10条记录，总共{{ previewData.length }}条
        </p>
      </div>

      <div class="preview-actions">
        <button @click="clearPreview" class="clear-btn">清除预览</button>
        <button @click="confirmUpload" class="upload-btn" :disabled="uploading">
          确认导入到数据库
        </button>
      </div>
    </div>

    <!-- 数据库状态 -->
    <div class="database-status">
      <h3>数据库状态</h3>
      <div class="status-grid">
        <div class="status-card">
          <div class="status-icon">❓</div>
          <div class="status-info">
            <div class="status-number">{{ databaseStats.raw_questions }}</div>
            <div class="status-label">原始问题</div>
          </div>
        </div>
        <div class="status-card">
          <div class="status-icon">💬</div>
          <div class="status-info">
            <div class="status-number">{{ databaseStats.raw_answers }}</div>
            <div class="status-label">原始答案</div>
          </div>
        </div>
        <div class="status-card">
          <div class="status-icon">👨‍🏫</div>
          <div class="status-info">
            <div class="status-number">{{ databaseStats.expert_answers }}</div>
            <div class="status-label">专家答案</div>
          </div>
        </div>
        <div class="status-card">
          <div class="status-icon">✅</div>
          <div class="status-info">
            <div class="status-number">{{ databaseStats.std_questions }}</div>
            <div class="status-label">标准问题</div>
          </div>
        </div>
      </div>
      <button @click="refreshDatabaseStats" class="refresh-btn" :disabled="loadingStats">
        {{ loadingStats ? '刷新中...' : '刷新统计' }}
      </button>
    </div>

    <!-- 帮助信息 -->
    <div class="help-section">
      <h3>数据格式说明</h3>
      <div class="help-content">
        <p>支持的JSON格式示例：</p>
        <pre class="code-example">
[
  {
    "title": "问题标题",
    "body": "问题内容",
    "author": "提问者",
    "votes": "5",
    "views": 100,
    "tags": ["tag1", "tag2"],
    "issued_at": "2024-01-01 12:00:00",
    "url": "https://example.com/question/1",
    "answers": [
      {
        "answer": "答案内容",
        "answered_by": "回答者",
        "upvotes": "3",
        "answered_at": "2024-01-01 13:00:00"
      }
    ]
  }
]</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dataImportService } from '@/services/dataImportService'
import { databaseService } from '@/services/databaseService'

// 响应式数据
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const uploadProgress = ref(0)
const error = ref('')
const uploadResult = ref<any>(null)
const previewData = ref<any[]>([])
const isDragOver = ref(false)
const loadingStats = ref(false)

const databaseStats = ref({
  raw_questions: 0,
  raw_answers: 0,
  expert_answers: 0,
  std_questions: 0,
  std_answers: 0
})

// 拖拽处理
const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    const file = files[0]
    if (file.type === 'application/json' || file.name.endsWith('.json')) {
      handleFile(file)
    } else {
      error.value = '请选择JSON格式的文件'
    }
  }
}

const handleDragLeave = () => {
  isDragOver.value = false
}

// 文件选择处理
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    handleFile(file)
  }
}

// 处理文件
const handleFile = async (file: File) => {
  clearError()
  uploadResult.value = null
  
  try {
    // 读取文件内容进行预览
    const text = await file.text()
    const data = JSON.parse(text)
    
    if (Array.isArray(data)) {
      previewData.value = data
    } else {
      error.value = 'JSON文件应该包含一个数组'
    }
  } catch (err) {
    error.value = '文件格式错误，请检查JSON格式是否正确'
    console.error('File processing error:', err)
  }
}

// 确认上传
const confirmUpload = async () => {
  if (previewData.value.length === 0) {
    error.value = '没有可上传的数据'
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

    // 调用上传服务
    const result = await dataImportService.uploadData(previewData.value)
    
    clearInterval(progressInterval)
    uploadProgress.value = 100

    uploadResult.value = result

    // 清除预览数据
    previewData.value = []
    
    // 刷新数据库统计
    await refreshDatabaseStats()

  } catch (err: any) {
    error.value = err.message || '上传失败'
    console.error('Upload error:', err)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

// 刷新数据库统计
const refreshDatabaseStats = async () => {
  loadingStats.value = true
  try {
    const stats = await databaseService.getDatabaseStats()
    databaseStats.value = stats
  } catch (err) {
    console.error('Failed to refresh database stats:', err)
  } finally {
    loadingStats.value = false
  }
}

// 获取预览统计
const getPreviewStats = () => {
  const questions = previewData.value.length
  const answers = previewData.value.reduce((total, item) => {
    return total + (item.answers?.length || 0)
  }, 0)
  
  return { questions, answers }
}

// 清除预览
const clearPreview = () => {
  previewData.value = []
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 清除错误
const clearError = () => {
  error.value = ''
}

// 格式化日期
const formatDate = (dateStr: string) => {
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

// 组件挂载时加载数据库统计
onMounted(() => {
  refreshDatabaseStats()
})
</script>

<style scoped>
.data-import-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h2 {
  margin: 0 0 10px 0;
  color: #333;
}

.subtitle {
  color: #666;
  margin: 0;
}

.upload-section {
  margin-bottom: 30px;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: #fafafa;
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: #007bff;
  background: #f0f8ff;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.upload-icon {
  font-size: 48px;
  opacity: 0.6;
}

.upload-text {
  margin: 0;
  color: #333;
  font-size: 16px;
}

.file-input-label {
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
}

.file-input {
  display: none;
}

.upload-hint {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.progress-icon {
  font-size: 48px;
}

.progress-bar {
  width: 100%;
  max-width: 300px;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
}

.error-message {
  margin-top: 20px;
  padding: 15px;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
}

.clear-error-btn {
  margin-top: 10px;
  padding: 5px 10px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.upload-result {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
}

.upload-result.success {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
}

.result-stats {
  display: flex;
  gap: 20px;
  margin-top: 10px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
}

.preview-section {
  margin-bottom: 30px;
}

.preview-stats {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  padding: 15px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  text-align: center;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.preview-table-container {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 15px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.preview-table th,
.preview-table td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.preview-table th {
  background: #f8f9fa;
  font-weight: bold;
}

.title-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-note {
  padding: 10px;
  background: #e9ecef;
  margin: 0;
  font-size: 12px;
  color: #495057;
}

.preview-actions {
  display: flex;
  gap: 10px;
}

.clear-btn, .upload-btn, .refresh-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.clear-btn {
  background: #6c757d;
  color: white;
}

.upload-btn {
  background: #007bff;
  color: white;
}

.refresh-btn {
  background: #28a745;
  color: white;
}

.clear-btn:hover,
.upload-btn:hover:not(:disabled),
.refresh-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.upload-btn:disabled,
.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.database-status {
  margin-bottom: 30px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-icon {
  font-size: 24px;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.status-number {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.status-label {
  font-size: 12px;
  color: #666;
}

.help-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.help-content {
  margin-top: 15px;
}

.code-example {
  background: #2d3748;
  color: #e2e8f0;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.4;
}
</style>

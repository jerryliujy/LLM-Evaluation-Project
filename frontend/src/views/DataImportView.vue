<template>
  <div class="data-import-container">
    <div class="header">
      <div class="header-left">
        <button @click="goBackToMarketplace" class="back-btn">
          ← 返回数据库市场
        </button>
        <div class="title-section">
          <h2>数据导入</h2>
          <p class="subtitle" v-if="currentDataset">
            当前数据库: {{ currentDataset.description }}
          </p>
          <p class="subtitle" v-else>
            创建数据集并导入不同类型的数据
          </p>
        </div>
      </div>
    </div>

    <!-- 步骤指示器 -->
    <div class="steps-indicator">
      <div class="step" :class="{ active: currentStep === 1 }">
        <div class="step-number">1</div>
        <div class="step-title">选择/创建数据集</div>
      </div>
      <div class="step" :class="{ active: currentStep === 2 }">
        <div class="step-number">2</div>
        <div class="step-title">选择数据类型</div>
      </div>
      <div class="step" :class="{ active: currentStep === 3 }">
        <div class="step-number">3</div>
        <div class="step-title">上传数据</div>
      </div>
    </div>

    <!-- 第一步：选择或创建数据集 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="dataset-section">
        <h3>选择现有数据集或创建新数据集</h3>
        
        <!-- 创建新数据集 -->
        <div v-if="isCreatingNew" class="create-form">
          <h4>创建新数据集</h4>
          <div class="form-group">
            <label class="form-label" for="datasetName">数据集名称：</label>
            <input
              id="datasetName"
              v-model="newDatasetName"
              type="text"
              placeholder="请输入数据集名称"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label" for="datasetDescription">数据集描述：</label>
            <textarea
              id="datasetDescription"
              v-model="newDatasetDescription"
              placeholder="请输入数据集描述"
              class="form-input"
              rows="3"
            ></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">
              <input
                type="checkbox"
                v-model="newDatasetIsPublic"
              />
              公开数据集
            </label>
          </div>
          <div class="form-actions">
            <button @click="createDataset" :disabled="!newDatasetName.trim() || !newDatasetDescription.trim() || creatingDataset" class="btn btn-primary">
              {{ creatingDataset ? '创建中...' : '创建数据集' }}
            </button>
            <button @click="cancelCreate" class="btn btn-secondary">取消</button>
          </div>
        </div>

        <!-- 创建新数据集按钮 -->
        <button v-if="!isCreatingNew" @click="showCreateNew" class="create-new-btn">
          + 创建新数据集
        </button>

        <!-- 选择现有数据集 -->
        <div v-if="datasets.length > 0 && !isCreatingNew" class="dataset-list">
          <h4>选择现有数据集</h4>
          <div
            v-for="dataset in datasets"
            :key="dataset.id"
            @click="selectDataset(dataset)"
            class="dataset-item"
            :class="{ selected: selectedDataset?.id === dataset.id }"
          >
            <div class="dataset-name">{{ dataset.name }}</div>
            <div class="dataset-description">{{ dataset.description }}</div>
            <div class="dataset-meta">
              <span class="dataset-visibility">{{ dataset.is_public ? '公开' : '私有' }}</span>
              <span class="dataset-date">创建时间: {{ formatDate(dataset.create_time) }}</span>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <div></div>
          <button @click="goToStep(2)" :disabled="!selectedDataset" class="next-btn">
            下一步
          </button>
        </div>
      </div>
    </div>

    <!-- 第二步：选择数据类型 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="data-type-section">
        <h3>选择要导入的数据类型</h3>
        <div class="data-types">
          <div
            @click="selectDataType('raw-qa')"
            class="data-type-card"
            :class="{ selected: selectedDataType === 'raw-qa' }"
          >
            <div class="type-icon">📝</div>
            <h4>原始问答数据</h4>
            <p>包含原始问题和对应的原始回答（一对多关系）</p>
          </div>
          
          <div
            @click="selectDataType('expert-answers')"
            class="data-type-card"
            :class="{ selected: selectedDataType === 'expert-answers' }"
          >
            <div class="type-icon">👨‍🏫</div>
            <h4>专家回答</h4>
            <p>针对已存在问题的专家回答</p>
          </div>
          
          <div
            @click="selectDataType('std-qa')"
            class="data-type-card disabled"
            title="暂未实现"
          >
            <div class="type-icon">✅</div>
            <h4>标准问答对</h4>
            <p>标准化的问题和答案对（暂未实现）</p>
          </div>
        </div>

        <div class="step-actions">
          <button @click="goToStep(1)" class="prev-btn">上一步</button>
          <button @click="goToStep(3)" :disabled="!selectedDataType" class="next-btn">下一步</button>
        </div>
      </div>
    </div>

    <!-- 第三步：上传数据 -->
    <div v-if="currentStep === 3" class="step-content">
      <div class="upload-section">
        <h3>上传{{ getDataTypeLabel() }}数据</h3>
        
        <!-- 数据格式说明 -->
        <div class="format-info">
          <h4>数据格式要求：</h4>
          <pre class="format-example">{{ getFormatExample() }}</pre>
        </div>

        <!-- 文件上传区域 -->
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

        <!-- 数据预览 -->
        <div v-if="previewData.length > 0" class="preview-section">
          <h4>数据预览</h4>
          <div class="preview-stats">
            <span>总记录数: {{ previewData.length }}</span>
          </div>
          
          <div class="preview-table-container">
            <table class="preview-table">
              <thead>
                <tr>
                  <th v-for="header in getPreviewHeaders()" :key="header">{{ header }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in previewData.slice(0, 5)" :key="index">
                  <td v-for="header in getPreviewHeaders()" :key="header" class="preview-cell">
                    {{ getPreviewValue(item, header) }}
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-if="previewData.length > 5" class="preview-note">
              显示前5条记录，总共{{ previewData.length }}条
            </p>
          </div>

          <div class="preview-actions">
            <button @click="clearPreview" class="clear-btn">清除预览</button>
            <button @click="confirmUpload" class="upload-btn" :disabled="uploading">
              确认导入到数据集
            </button>
          </div>
        </div>

        <!-- 上传结果 -->
        <div v-if="uploadResult" class="upload-result success">
          <h4>✅ 导入成功</h4>
          <div class="result-stats">
            <div v-if="uploadResult.imported_questions" class="stat-item">
              <span class="stat-label">导入问题:</span>
              <span class="stat-value">{{ uploadResult.imported_questions }}</span>
            </div>
            <div v-if="uploadResult.imported_answers" class="stat-item">
              <span class="stat-label">导入答案:</span>
              <span class="stat-value">{{ uploadResult.imported_answers }}</span>
            </div>
            <div v-if="uploadResult.imported_expert_answers" class="stat-item">
              <span class="stat-label">导入专家答案:</span>
              <span class="stat-value">{{ uploadResult.imported_expert_answers }}</span>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <button @click="goToStep(2)" class="prev-btn">上一步</button>
          <button @click="resetWizard" class="reset-btn">重新开始</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { dataImportService, type Dataset, type DataType } from '@/services/dataImportService'
import { databaseService } from '@/services/databaseService'
import { datasetService } from '@/services/datasetService'

// 路由相关
const route = useRoute()
const router = useRouter()

// 响应式数据 - 统一定义，避免重复
const currentStep = ref(1)
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const uploadProgress = ref(0)
const error = ref('')
const uploadResult = ref<any>(null)
const previewData = ref<any[]>([])
const isDragOver = ref(false)

// 数据集相关
const datasets = ref<Dataset[]>([])
const selectedDataset = ref<Dataset | null>(null)
const newDatasetName = ref('')
const newDatasetDescription = ref('')
const newDatasetIsPublic = ref(true)
const creatingDataset = ref(false)
const isCreatingNew = ref(false)

// 数据类型选择
const selectedDataType = ref<DataType | null>(null)

// 路由参数：数据集ID
const datasetId = computed(() => route.query.datasetId as string)

// 当前数据集信息（用于显示）
const currentDataset = computed(() => {
  if (datasetId.value) {
    return datasets.value.find(d => d.id.toString() === datasetId.value)
  }
  return selectedDataset.value
})

// 返回到数据库市场
const goBackToMarketplace = () => {
  router.push({ name: 'DatasetMarketplace' })
}

// 重置向导
const resetWizard = () => {
  currentStep.value = 1
  selectedDataset.value = null
  selectedDataType.value = null
  clearError()
  clearPreview()
  uploadResult.value = null
  isCreatingNew.value = false
  newDatasetDescription.value = ''
}

// 步骤导航
const goToStep = (step: number) => {
  if (step === 2 && !selectedDataset.value) {
    error.value = '请先选择或创建数据集'
    return
  }
  if (step === 3 && !selectedDataType.value) {
    error.value = '请先选择数据类型'
    return
  }
  currentStep.value = step
  clearError()
}

// 数据集管理
const loadDatasets = async () => {
  try {
    const data = await dataImportService.getDatasets()
    datasets.value = data
  } catch (err: any) {
    error.value = '加载数据集失败: ' + err.message
  }
}

const selectDataset = (dataset: Dataset) => {
  selectedDataset.value = dataset
  isCreatingNew.value = false
}

const showCreateNew = () => {
  isCreatingNew.value = true
  selectedDataset.value = null
  newDatasetName.value = ''
  newDatasetDescription.value = ''
  newDatasetIsPublic.value = true
}

const createDataset = async () => {
  if (!newDatasetName.value.trim() || !newDatasetDescription.value.trim()) {
    error.value = '请填写数据集名称和描述'
    return
  }

  creatingDataset.value = true
  try {
    const result = await dataImportService.createDataset(
      newDatasetName.value.trim(),
      newDatasetDescription.value.trim(),
      newDatasetIsPublic.value
    )
    const newDataset: Dataset = {
      id: result.dataset_id,
      name: result.name,
      description: result.description,
      create_time: new Date().toISOString()
    }
    
    datasets.value.unshift(newDataset)
    selectedDataset.value = newDataset
    isCreatingNew.value = false
    newDatasetName.value = ''
    newDatasetDescription.value = ''
    newDatasetIsPublic.value = true
  } catch (err: any) {
    error.value = '创建数据集失败: ' + err.message
  } finally {
    creatingDataset.value = false
  }
}

const cancelCreate = () => {
  isCreatingNew.value = false
  newDatasetName.value = ''
  newDatasetDescription.value = ''
  newDatasetIsPublic.value = true
}

// 数据类型选择
const selectDataType = (type: DataType) => {
  if (type === 'std-qa') return // 暂未实现
  selectedDataType.value = type
}

const getDataTypeLabel = () => {
  const labels = {
    'raw-qa': '原始问答数据',
    'expert-answers': '专家回答数据',
    'std-qa': '标准问答对'
  }
  return selectedDataType.value ? labels[selectedDataType.value] : ''
}

const getFormatExample = () => {
  if (!selectedDataType.value) return ''
  
  const examples = {
    'raw-qa': `[
  {
    "title": "问题标题",
    "body": "问题详细内容",
    "url": "问题链接",
    "votes": "投票数",
    "views": "浏览数",
    "author": "作者",
    "tags": ["标签1", "标签2"],
    "issued_at": "2024-01-01 12:00",
    "answers": [
      {
        "answer": "回答内容",
        "upvotes": "赞同数",
        "answered_by": "回答者",
        "answered_at": "2024-01-01 13:00"
      }
    ]
  }
]`,
    'expert-answers': `[
  {
    "question_id": 123,
    "content": "专家回答内容",
    "source": "Expert Review",
    "vote_count": 5,
    "expert_id": 1
  }
]`,
    'std-qa': `[
  {
    "question": "标准问题",
    "answer": "标准答案",
    "category": "分类",
    "difficulty": "difficulty_level"
  }
]`
  }
  
  return examples[selectedDataType.value]
}

// 预览相关
const getPreviewHeaders = () => {
  if (!selectedDataType.value || previewData.value.length === 0) return []
  
  const firstItem = previewData.value[0]
  return Object.keys(firstItem).slice(0, 5) // 只显示前5个字段
}

const getPreviewValue = (item: any, header: string) => {
  const value = item[header]
  if (typeof value === 'object') {
    return JSON.stringify(value).substring(0, 50) + '...'
  }
  const stringValue = String(value || '')
  return stringValue.length > 30 ? stringValue.substring(0, 30) + '...' : stringValue
}

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
    const text = await file.text()
    const data = JSON.parse(text)
    
    if (Array.isArray(data)) {
      // 验证数据格式
      if (selectedDataType.value) {
        const validation = dataImportService.validateDataFormat(selectedDataType.value, data)
        if (!validation.isValid) {
          error.value = '数据格式验证失败:\n' + validation.errors.join('\n')
          return
        }
      }
      
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

  if (!selectedDataset.value || !selectedDataType.value) {
    error.value = '请确保已选择数据集和数据类型'
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

    let result
    // 根据数据类型调用不同的上传方法
    switch (selectedDataType.value) {
      case 'raw-qa':
        result = await dataImportService.uploadRawQAData(selectedDataset.value.id, previewData.value)
        break
      case 'expert-answers':
        result = await dataImportService.uploadExpertAnswers(selectedDataset.value.id, previewData.value)
        break
      case 'std-qa':
        result = await dataImportService.uploadStdQAData(selectedDataset.value.id, previewData.value)
        break
    }
    
    clearInterval(progressInterval)
    uploadProgress.value = 100

    uploadResult.value = result
    previewData.value = []

  } catch (err: any) {
    error.value = err.message || '上传失败'
    console.error('Upload error:', err)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

// 工具函数
const clearPreview = () => {
  previewData.value = []
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const clearError = () => {
  error.value = ''
}

const formatDate = (dateStr: string) => {
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

// 组件挂载时加载数据集
onMounted(async () => {
  await loadDatasets()
  
  // 如果URL参数中有数据集ID，自动选择该数据集
  if (datasetId.value) {
    const dataset = datasets.value.find(d => d.id.toString() === datasetId.value)
    if (dataset) {
      selectedDataset.value = dataset
      // 如果指定了数据集，直接跳到数据类型选择步骤
      currentStep.value = 2
    }
  }
})
</script>

<style scoped>
/* 保持原有的CSS样式不变 */
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

/* 步骤指示器样式 */
.steps-indicator {
  display: flex;
  justify-content: center;
  margin-bottom: 40px;
  position: relative;
}

.steps-indicator::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 25%;
  right: 25%;
  height: 2px;
  background: #e9ecef;
  z-index: 1;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
  min-width: 120px;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  background: #e9ecef;
  color: #6c757d;
}

.step.active .step-number {
  background: #007bff;
  color: white;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  text-align: center;
  color: #6c757d;
}

.step.active .step-title {
  color: #333;
}

/* 步骤内容样式 */
.step-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.step-content h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 24px;
}

/* 数据集选择样式 */
.create-new-btn {
  width: 100%;
  padding: 15px;
  border: 2px dashed #007bff;
  background: transparent;
  color: #007bff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.create-new-btn:hover {
  background: #f0f8ff;
}

.create-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dataset-list {
  margin-bottom: 20px;
}

.dataset-item {
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dataset-item:hover {
  border-color: #007bff;
  background: #f8f9fa;
}

.dataset-item.selected {
  border-color: #007bff;
  background: #e3f2fd;
}

.dataset-name {
  font-weight: 600;
  margin-bottom: 5px;
  color: #333;
}

.dataset-date {
  font-size: 14px;
  color: #666;
}

/* 数据类型选择样式 */
.data-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.data-type-card {
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.data-type-card:hover:not(.disabled) {
  border-color: #007bff;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 123, 255, 0.15);
}

.data-type-card.selected {
  border-color: #007bff;
  background: #f0f8ff;
}

.data-type-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.type-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.data-type-card h4 {
  margin: 0 0 8px 0;
  color: #333;
}

.data-type-card p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

/* 上传区域样式 */
.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: #fafafa;
  transition: all 0.3s ease;
  cursor: pointer;
  margin-bottom: 20px;
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

/* 格式信息样式 */
.format-info {
  margin-bottom: 20px;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
}

.format-info h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.format-example {
  background: #2d3748;
  color: #e2e8f0;
  padding: 15px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  margin: 0;
  white-space: pre;
}

/* 错误信息样式 */
.error-message {
  margin-bottom: 20px;
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

/* 预览表格样式 */
.preview-section {
  margin-bottom: 20px;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.preview-stats {
  margin-bottom: 15px;
  font-weight: 500;
  color: #333;
}

.preview-table-container {
  overflow-x: auto;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  margin-bottom: 15px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  font-size: 12px;
}

.preview-table th,
.preview-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.preview-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
}

.preview-cell {
  max-width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-note {
  margin: 10px 0 0 0;
  font-size: 12px;
  color: #666;
}

.preview-actions {
  display: flex;
  gap: 10px;
}

/* 上传结果样式 */
.upload-result {
  margin-bottom: 20px;
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

/* 按钮样式 */
.clear-btn, .upload-btn, .reset-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.clear-btn {
  background: #6c757d;
  color: white;
}

.upload-btn {
  background: #28a745;
  color: white;
}

.reset-btn {
  background: #17a2b8;
  color: white;
}

.clear-btn:hover,
.upload-btn:hover:not(:disabled),
.reset-btn:hover {
  opacity: 0.9;
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 步骤操作按钮样式 */
.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
}

.prev-btn, .next-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.prev-btn {
  background: #6c757d;
  color: white;
}

.prev-btn:hover {
  background: #5a6268;
}

.next-btn {
  background: #007bff;
  color: white;
}

.next-btn:hover:not(:disabled) {
  background: #0056b3;
}

.next-btn:disabled {
  background: #e9ecef;
  color: #6c757d;
  cursor: not-allowed;
}
</style>
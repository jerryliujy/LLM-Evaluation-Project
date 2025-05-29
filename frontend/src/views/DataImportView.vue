<template>
  <div class="data-import-container">
    <h2>数据导入管理</h2>
    
    <!-- 创建数据集部分 -->
    <div class="section">
      <h3>创建新数据集</h3>
      <form @submit.prevent="createDataset" class="create-dataset-form">
        <div class="form-group">
          <label for="description">数据集描述:</label>
          <textarea 
            id="description"
            v-model="newDatasetDescription"
            required
            placeholder="请输入数据集描述..."
            rows="3"
          ></textarea>
        </div>
        <button type="submit" :disabled="!newDatasetDescription.trim()">
          创建数据集
        </button>
      </form>
    </div>

    <!-- 数据集列表 -->
    <div class="section">
      <h3>现有数据集</h3>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="datasets.length === 0" class="no-data">暂无数据集</div>
      <div v-else class="datasets-list">
        <div 
          v-for="dataset in datasets" 
          :key="dataset.id"
          class="dataset-item"
          :class="{ 'selected': selectedDataset?.id === dataset.id }"
          @click="selectDataset(dataset)"
        >
          <h4>{{ dataset.description }}</h4>
          <p class="dataset-info">
            ID: {{ dataset.id }} | 
            创建时间: {{ formatDate(dataset.create_time) }}
          </p>
          <div v-if="datasetStats[dataset.id]" class="stats">
            问题数: {{ datasetStats[dataset.id].question_count }} | 
            回答数: {{ datasetStats[dataset.id].answer_count }}
          </div>
        </div>
      </div>
    </div>

    <!-- 文件上传部分 -->
    <div class="section" v-if="selectedDataset">
      <h3>上传数据到: {{ selectedDataset.description }}</h3>
      <form @submit.prevent="uploadFile" class="upload-form">
        <div class="form-group">
          <label for="file">选择JSON文件:</label>
          <input 
            type="file" 
            id="file"
            ref="fileInput"
            accept=".json"
            @change="onFileChange"
            required
          >
        </div>
        <button 
          type="submit" 
          :disabled="!selectedFile || uploading"
        >
          {{ uploading ? '上传中...' : '上传数据' }}
        </button>
      </form>
      
      <!-- 上传结果 -->
      <div v-if="uploadResult" class="upload-result">
        <h4>上传结果:</h4>
        <p>{{ uploadResult.message }}</p>
        <p>导入问题数: {{ uploadResult.imported_questions }}</p>
        <p>导入回答数: {{ uploadResult.imported_answers }}</p>
      </div>
    </div>

    <!-- 错误消息 -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import axios from 'axios'

interface Dataset {
  id: number
  description: string
  create_time: string
}

interface DatasetStats {
  question_count: number
  answer_count: number
}

interface UploadResult {
  message: string
  dataset_id: number
  imported_questions: number
  imported_answers: number
}

export default defineComponent({
  name: 'DataImportView',
  setup() {
    const datasets = ref<Dataset[]>([])
    const selectedDataset = ref<Dataset | null>(null)
    const datasetStats = ref<Record<number, DatasetStats>>({})
    const newDatasetDescription = ref('')
    const selectedFile = ref<File | null>(null)
    const loading = ref(false)
    const uploading = ref(false)
    const error = ref('')
    const uploadResult = ref<UploadResult | null>(null)
    const fileInput = ref<HTMLInputElement>()

    const API_BASE = 'http://localhost:8000/api/data-import'

    const loadDatasets = async () => {
      try {
        loading.value = true
        const response = await axios.get(`${API_BASE}/datasets`)
        datasets.value = response.data
        
        // 为每个数据集加载统计信息
        for (const dataset of datasets.value) {
          try {
            const statsResponse = await axios.get(`${API_BASE}/dataset/${dataset.id}/stats`)
            datasetStats.value[dataset.id] = statsResponse.data
          } catch (err) {
            console.error(`Failed to load stats for dataset ${dataset.id}:`, err)
          }
        }
      } catch (err) {
        error.value = '加载数据集失败'
        console.error('Error loading datasets:', err)
      } finally {
        loading.value = false
      }
    }

    const createDataset = async () => {
      try {
        const formData = new FormData()
        formData.append('description', newDatasetDescription.value)
        
        const response = await axios.post(`${API_BASE}/dataset`, formData)
        
        // 重新加载数据集列表
        await loadDatasets()
        newDatasetDescription.value = ''
        error.value = ''
      } catch (err) {
        error.value = '创建数据集失败'
        console.error('Error creating dataset:', err)
      }
    }

    const selectDataset = (dataset: Dataset) => {
      selectedDataset.value = dataset
      uploadResult.value = null
      error.value = ''
    }

    const onFileChange = (event: Event) => {
      const target = event.target as HTMLInputElement
      selectedFile.value = target.files?.[0] || null
      uploadResult.value = null
      error.value = ''
    }

    const uploadFile = async () => {
      if (!selectedDataset.value || !selectedFile.value) return

      try {
        uploading.value = true
        const formData = new FormData()
        formData.append('file', selectedFile.value)

        const response = await axios.post(
          `${API_BASE}/upload-questions/${selectedDataset.value.id}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )

        uploadResult.value = response.data
        
        // 重新加载数据集统计信息
        const statsResponse = await axios.get(`${API_BASE}/dataset/${selectedDataset.value.id}/stats`)
        datasetStats.value[selectedDataset.value.id] = statsResponse.data
        
        // 清空文件选择
        selectedFile.value = null
        if (fileInput.value) {
          fileInput.value.value = ''
        }
        
        error.value = ''
      } catch (err: any) {
        error.value = err.response?.data?.detail || '上传失败'
        console.error('Error uploading file:', err)
      } finally {
        uploading.value = false
      }
    }

    const formatDate = (dateStr: string) => {
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    onMounted(() => {
      loadDatasets()
    })

    return {
      datasets,
      selectedDataset,
      datasetStats,
      newDatasetDescription,
      selectedFile,
      loading,
      uploading,
      error,
      uploadResult,
      fileInput,
      loadDatasets,
      createDataset,
      selectDataset,
      onFileChange,
      uploadFile,
      formatDate
    }
  }
})
</script>

<style scoped>
.data-import-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

.create-dataset-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: bold;
}

.form-group textarea,
.form-group input[type="file"] {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background: #0056b3;
}

.datasets-list {
  display: grid;
  gap: 15px;
}

.dataset-item {
  padding: 15px;
  border: 2px solid #ddd;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.dataset-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.dataset-item.selected {
  border-color: #007bff;
  background: #e3f2fd;
}

.dataset-item h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.dataset-info {
  margin: 5px 0;
  color: #666;
  font-size: 12px;
}

.stats {
  margin-top: 10px;
  padding: 8px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 12px;
  color: #495057;
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.upload-result {
  margin-top: 20px;
  padding: 15px;
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  color: #155724;
}

.error-message {
  margin-top: 20px;
  padding: 15px;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  color: #721c24;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.no-data {
  text-align: center;
  padding: 20px;
  color: #999;
}
</style>

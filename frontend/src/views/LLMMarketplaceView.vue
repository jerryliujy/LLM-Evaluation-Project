<template>
  <div class="llm-marketplace">
    <div class="header">
      <h1>数据集市场</h1>
      <p>浏览和下载公开数据集，进行大模型评测</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filters">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索数据集..."
            prefix-icon="el-icon-search"
            @input="handleSearch"
            clearable
          />
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadDatasets">刷新</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 数据集列表 -->
    <div class="datasets-container">
      <el-row :gutter="20">
        <el-col 
          v-for="dataset in datasets" 
          :key="dataset.id" 
          :span="8"
          style="margin-bottom: 20px;"
        >
          <el-card class="dataset-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="dataset-name">{{ dataset.name }}</span>
                <el-tag size="small">v{{ dataset.version }}</el-tag>
              </div>
            </template>
            
            <div class="dataset-info">
              <p class="description">{{ dataset.description }}</p>
              
              <div class="stats">
                <el-row>
                  <el-col :span="12">
                    <div class="stat-item">
                      <i class="el-icon-document"></i>
                      <span>{{ dataset.question_count }} 个问题</span>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="stat-item">
                      <i class="el-icon-time"></i>
                      <span>{{ formatDate(dataset.create_time) }}</span>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>

            <template #footer>
              <div class="card-actions">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="viewDataset(dataset)"
                >
                  查看详情
                </el-button>
                <el-button 
                  type="success" 
                  size="small" 
                  @click="downloadDataset(dataset)"
                  :loading="downloading[dataset.id]"
                >
                  下载数据集
                </el-button>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[12, 24, 48]"
        :total="totalDatasets"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 数据集详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="数据集详情"
      width="70%"
      destroy-on-close
    >
      <div v-if="selectedDataset" class="dataset-detail">
        <div class="detail-header">
          <h3>{{ selectedDataset.name }}</h3>
          <el-tag>版本 {{ selectedDataset.version }}</el-tag>
        </div>
        
        <div class="detail-info">
          <p><strong>描述：</strong>{{ selectedDataset.description }}</p>
          <p><strong>问题数量：</strong>{{ selectedDataset.question_count }}</p>
          <p><strong>创建时间：</strong>{{ formatDate(selectedDataset.create_time) }}</p>
        </div>

        <div class="sample-questions" v-if="sampleQuestions.length > 0">
          <h4>示例问题</h4>
          <div v-for="question in sampleQuestions" :key="question.id" class="question-item">
            <p><strong>问题：</strong>{{ question.body }}</p>
            <p><strong>类型：</strong>{{ question.question_type === 'choice' ? '选择题' : '文本题' }}</p>
            <div v-if="question.answers && question.answers.length > 0">
              <p><strong>标准答案：</strong></p>
              <ul>
                <li v-for="answer in question.answers.slice(0, 2)" :key="answer.id">
                  {{ answer.answer }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDetailDialog = false">关闭</el-button>
          <el-button 
            type="primary" 
            @click="downloadDataset(selectedDataset)"
            :loading="downloading[selectedDataset?.id]"
          >
            下载数据集
          </el-button>
          <el-button 
            type="success" 
            @click="startEvaluation(selectedDataset)"
          >
            开始评测
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import apiClient from '@/services/api'

const router = useRouter()

// 响应式数据
const datasets = ref<any[]>([])
const totalDatasets = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const searchQuery = ref('')
const loading = ref(false)
const downloading = reactive<Record<number, boolean>>({})

// 对话框相关
const showDetailDialog = ref(false)
const selectedDataset = ref<any>(null)
const sampleQuestions = ref<any[]>([])

// 生命周期
onMounted(() => {
  loadDatasets()
})

// 方法
const loadDatasets = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/llm/marketplace/datasets', {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value,
        search: searchQuery.value || undefined
      }
    })
    datasets.value = response.data
    // 这里应该从响应头或者单独的API获取总数
    totalDatasets.value = response.data.length > 0 ? response.data.length * 10 : 0
  } catch (error) {
    console.error('加载数据集失败:', error)
    ElMessage.error('加载数据集失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadDatasets()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadDatasets()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadDatasets()
}

const viewDataset = async (dataset: any) => {
  selectedDataset.value = dataset
  showDetailDialog.value = true
  
  // 加载示例问题
  try {
    const response = await apiClient.get(`/llm/marketplace/datasets/${dataset.id}/download`)
    if (response.data.questions) {
      sampleQuestions.value = response.data.questions.slice(0, 3) // 只显示前3个示例
    }
  } catch (error) {
    console.error('加载示例问题失败:', error)
  }
}

const downloadDataset = async (dataset: any) => {
  downloading[dataset.id] = true
  try {
    const response = await apiClient.get(`/llm/marketplace/datasets/${dataset.id}/download`, {
      params: { format: 'json' }
    })
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(response.data, null, 2)], {
      type: 'application/json'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${dataset.name}_v${dataset.version}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('数据集下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  } finally {
    downloading[dataset.id] = false
  }
}

const startEvaluation = (dataset: any) => {
  showDetailDialog.value = false
  router.push({
    name: 'LLMEvaluation',
    params: { datasetId: dataset.id }
  })
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.llm-marketplace {
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  color: #303133;
  margin-bottom: 10px;
}

.header p {
  color: #909399;
  font-size: 16px;
}

.filters {
  margin-bottom: 30px;
}

.dataset-card {
  height: 300px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dataset-name {
  font-weight: bold;
  font-size: 16px;
}

.dataset-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.description {
  color: #606266;
  margin-bottom: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.stats {
  margin-top: auto;
}

.stat-item {
  display: flex;
  align-items: center;
  color: #909399;
  font-size: 14px;
}

.stat-item i {
  margin-right: 5px;
}

.card-actions {
  display: flex;
  justify-content: space-between;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.dataset-detail {
  padding: 20px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.detail-info {
  margin-bottom: 30px;
}

.detail-info p {
  margin-bottom: 10px;
  line-height: 1.6;
}

.sample-questions h4 {
  margin-bottom: 15px;
  color: #303133;
}

.question-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 15px;
}

.question-item p {
  margin-bottom: 8px;
}

.question-item ul {
  margin-left: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

<template>
  <div class="marketplace-container">
    <!-- 头部标题 -->
    <div class="page-header">
      <h1>LLM评测平台</h1>
      <div class="stats">
        <span>任务: {{ tasks.length }}</span>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane name="marketplace">
          <template #label>
            <span class="tab-label">我的任务</span>
          </template>
          
          <!-- 任务筛选器 -->
          <div class="task-filters">
            <div class="filter-group">              
              <el-select 
                v-model="taskStatusFilter" 
                placeholder="任务状态" 
                clearable 
                @change="loadTasks"
                size="default"
                style="width: 200px;"
              >
                <el-option label="全部任务" value="" />
                <el-option label="配置参数中" value="config_params" />
                <el-option label="配置提示词中" value="config_prompts" />
                <el-option label="生成答案中" value="generating_answers" />
                <el-option label="评测答案中" value="evaluating_answers" />
                <el-option label="已完成" value="completed" />
                <el-option label="失败" value="failed" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
              <el-button 
                type="primary" 
                size="default" 
                @click="loadTasks"
                :loading="tasksLoading"
              >
                刷新任务
              </el-button>
            </div>
          </div>

          <!-- 任务列表 -->
          <div class="tasks-list" v-loading="tasksLoading">
            <el-empty 
              v-if="tasks.length === 0 && !tasksLoading" 
              description="暂无评测任务"
              :image-size="120"
            >
              <template #description>
                <p>还没有创建任何评测任务</p>
                <el-button type="primary" @click="activeTab = 'marketplace'">
                  去创建任务
                </el-button>
              </template>
            </el-empty>
            
            <div v-else class="tasks-container">
              <div 
                v-for="task in tasks" 
                :key="task.id" 
                class="task-card"
                :class="getTaskCardClass(task.status)"
              >
                <div class="task-header">
                  <div class="task-title-section">
                    <h4 class="task-title">
                      {{ task.name || `评测任务 #${task.id}` }}
                    </h4>
                    <el-tag 
                      :type="getTaskStatusType(task.status)" 
                      size="small"
                      class="status-tag"
                    >
                      {{ getTaskStatusText(task.status) }}
                    </el-tag>
                  </div>
                  <div class="task-time">
                    <el-icon><Clock /></el-icon>
                    {{ formatDateTime(task.created_at) }}
                  </div>
                </div>                <div class="task-info">
                  <div class="info-grid">
                    <div class="info-item">
                      <div class="info-label">数据集</div>
                      <div class="info-value">{{ task.dataset?.name || '未知' }}</div>
                    </div>
                    <div class="info-item">
                      <div class="info-label">模型</div>
                      <div class="info-value">{{ task.model?.display_name || '未知' }}</div>
                    </div>
                    <div class="info-item">
                      <div class="info-label">总题数</div>
                      <div class="info-value">{{ task.total_questions || 0 }}</div>
                    </div>
                    <div class="info-item">
                      <div class="info-label">完成数</div>
                      <div class="info-value">{{ task.completed_questions || 0 }}</div>
                    </div>
                  </div>
                </div>                <!-- 进度条 -->
                <div v-if="isTaskInProgress(task.status) || task.status === 'completed'" class="task-progress">
                  <div class="progress-info">
                    <span>进度</span>
                    <span>{{ task.progress || 0 }}%</span>
                  </div>
                  <el-progress 
                    :percentage="task.progress || 0" 
                    :status="task.status === 'completed' ? 'success' : (task.status === 'failed' ? 'exception' : '')"
                    :stroke-width="8"
                    class="progress-bar"
                  />
                </div>                
                
                <!-- 任务操作按钮 -->
                <div class="task-actions">
                  <!-- 继续任务按钮 -->
                  <el-button 
                    size="small" 
                    type="primary"
                    @click="continueTask(task)"
                    v-if="canContinueTask(task.status)"
                    class="action-btn"
                  >
                    继续任务
                  </el-button>
                  <!-- 查看结果按钮 -->
                  <el-button 
                    size="small" 
                    type="success"
                    @click="viewTaskResults(task)"
                    v-if="task.status === 'completed'"
                    class="action-btn"
                  >
                    查看结果
                  </el-button>
                  <!-- 取消任务按钮 -->
                  <el-button 
                    size="small" 
                    type="danger" 
                    @click="cancelTask(task)"
                    v-if="canCancelTask(task.status)"
                    class="action-btn"
                  >
                    取消任务
                  </el-button>
                  <!-- 下载结果按钮 -->
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="downloadTaskResults(task)"
                    v-if="task.status === 'completed'"
                    class="action-btn"
                  >
                    下载结果
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 数据集详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="数据集详情"
      width="80%"
      destroy-on-close
      class="detail-dialog"
    >
      <div v-if="selectedDataset" class="dataset-detail">          
        <div class="detail-header">
            <div class="header-info">
              <h2 class="detail-title">{{ selectedDataset.name }}</h2>
              <div class="detail-tags">
                <el-tag type="success" size="large">版本 {{ selectedDataset.version }}</el-tag>
                <el-tag type="info" size="large">{{ selectedDataset.question_count || 0 }} 个问题</el-tag>
              </div>
            </div>
          </div>
        
        <div class="detail-content">          
          <div class="info-section">
            <h3>描述信息</h3>
            <p class="description-text">{{ selectedDataset.description || '暂无描述' }}</p>
          </div>

          <div class="info-section">
            <h3>基本信息</h3>
            <div class="info-grid">
              <div class="info-card">
                <div class="info-text">
                  <div class="info-number">{{ selectedDataset.question_count || 0 }}</div>
                  <div class="info-desc">问题数量</div>
                </div>
              </div>
              <div class="info-card">
                <div class="info-text">
                  <div class="info-number">{{ formatDate(selectedDataset.create_time) }}</div>
                  <div class="info-desc">创建时间</div>
                </div>
              </div>
            </div>
          </div>

          <div class="info-section" v-if="sampleQuestions.length > 0">
            <h3>示例问题</h3>
            <div class="sample-questions">
              <div v-for="(question, index) in sampleQuestions" :key="question.id" class="question-card">
                <div class="question-header">
                  <span class="question-index">Q{{ index + 1 }}</span>
                  <el-tag size="small" :type="question.question_type === 'choice' ? 'warning' : 'info'">
                    {{ question.question_type === 'choice' ? '选择题' : '文本题' }}
                  </el-tag>
                </div>
                <div class="question-body">
                  <p><strong>问题：</strong>{{ question.body }}</p>
                  <div v-if="question.answers && question.answers.length > 0" class="answers-section">
                    <p><strong>标准答案：</strong></p>
                    <ul class="answers-list">
                      <li v-for="answer in question.answers.slice(0, 2)" :key="answer.id">
                        {{ answer.answer }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>        <div class="dialog-footer">
          <el-button size="large" @click="showDetailDialog = false">
            关闭
          </el-button>
          <el-button 
            size="large"
            @click="downloadDataset(selectedDataset)"
            :loading="downloading[selectedDataset?.id]"
          >
            下载数据集
          </el-button>
          <el-button 
            type="primary" 
            size="large"
            @click="startEvaluation(selectedDataset)"
          >
            开始评测
          </el-button>
        </div>
      </template>
    </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { Clock } from '@element-plus/icons-vue'
import apiClient from '@/services/api'

const router = useRouter()

// 响应式数据
const activeTab = ref('marketplace')
const datasets = ref<any[]>([])
const totalDatasets = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const searchQuery = ref('')
const loading = ref(false)
const downloading = reactive<Record<number, boolean>>({})

// 任务相关数据
const tasks = ref<any[]>([])
const tasksLoading = ref(false)
const taskStatusFilter = ref('')

// 对话框相关
const showDetailDialog = ref(false)
const selectedDataset = ref<any>(null)
const sampleQuestions = ref<any[]>([])

// 生命周期
onMounted(() => {
  loadDatasets()
  loadTasks()
})

// 方法
const handleTabChange = (tabName: string) => {
  if (tabName === 'tasks') {
    loadTasks()
  } else if (tabName === 'marketplace') {
    loadDatasets()
  }
}

const loadDatasets = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/llm-evaluation/marketplace/datasets', {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value,
        search: searchQuery.value || undefined
      }
    })
    datasets.value = response.data
    totalDatasets.value = response.data.length > 0 ? response.data.length * 10 : 0
  } catch (error) {
    console.error('加载数据集失败:', error)
    ElMessage.error('加载数据集失败')
  } finally {
    loading.value = false
  }
}

const loadTasks = async () => {
  tasksLoading.value = true
  try {
    const response = await apiClient.get('/llm-evaluation/tasks', {
      params: {
        status: taskStatusFilter.value || undefined
      }
    })
    tasks.value = response.data
  } catch (error) {
    console.error('加载任务失败:', error)
    ElMessage.error('加载任务失败')
  } finally {
    tasksLoading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadDatasets()
}

const viewDataset = async (dataset: any) => {
  selectedDataset.value = dataset
  showDetailDialog.value = true
  
  try {
    const response = await apiClient.get(`/llm-evaluation/marketplace/datasets/${dataset.id}/download`)
    if (response.data.questions) {
      sampleQuestions.value = response.data.questions.slice(0, 3)
    }
  } catch (error) {
    console.error('加载示例问题失败:', error)
  }
}

const downloadDataset = async (dataset: any) => {
  downloading[dataset.id] = true
  try {
    const response = await apiClient.get(`/llm-evaluation/marketplace/datasets/${dataset.id}/download`, {
      params: { format: 'json' }
    })
    
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

// 任务相关方法
const viewTaskProgress = (task: any) => {
  router.push({
    name: 'LLMEvaluation',
    params: { datasetId: task.dataset_id },
    query: { taskId: task.id }
  })
}

const viewTaskResults = (task: any) => {
  router.push({
    name: 'LLMEvaluation',
    params: { datasetId: task.dataset_id },
    query: { taskId: task.id, view: 'results' }
  })
}

const cancelTask = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消任务 "${task.name || `#${task.id}`}" 吗？`,
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await apiClient.post(`/llm-evaluation/tasks/${task.id}/cancel`)
    ElMessage.success('任务已取消')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error('取消任务失败')
    }
  }
}

const downloadTaskResults = async (task: any) => {
  try {
    const response = await apiClient.post(`/llm-evaluation/tasks/${task.id}/download`, {
      format: 'json'
    })
    
    const blob = new Blob([JSON.stringify(response.data, null, 2)], {
      type: 'application/json'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `task_${task.id}_results.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('结果下载成功')
  } catch (error) {
    console.error('下载结果失败:', error)
    ElMessage.error('下载结果失败')
  }
}

// 继续任务
const continueTask = (task: any) => {
  router.push({
    name: 'LLMEvaluation',
    params: { datasetId: task.dataset_id },
    query: { taskId: task.id }
  })
}

// 任务状态辅助函数
const isTaskInProgress = (status: string): boolean => {
  return ['generating_answers', 'evaluating_answers'].includes(status)
}

const canContinueTask = (status: string): boolean => {
  return ['config_params', 'config_prompts', 'generating_answers', 'evaluating_answers'].includes(status)
}

const canCancelTask = (status: string): boolean => {
  return ['config_params', 'config_prompts', 'generating_answers', 'evaluating_answers'].includes(status)
}

// 工具方法
const getTaskStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'config_params': 'info',
    'config_prompts': 'info', 
    'generating_answers': 'warning',
    'evaluating_answers': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || 'info'
}

const getTaskStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'config_params': '配置参数中',
    'config_prompts': '配置提示词中',
    'generating_answers': '生成答案中',
    'evaluating_answers': '评测答案中', 
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || '未知'
}

const getTaskCardClass = (status: string) => {
  return `task-card-${status}`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
/* 全局样式 */
.llm-marketplace {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 0;
}

/* 页面头部 */
.header {
  background: white;
  padding: 30px 0;
  margin-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  flex: 1;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 1rem;
  color: #666;
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 30px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.stat-number {
  font-size: 1.2rem;
  font-weight: 600;
  color: #409eff;
}

/* 标签页容器 */
.tabs-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.custom-tabs {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tab-label {
  font-size: 1rem;
  font-weight: 500;
}

/* 搜索和筛选区域 */
.filters-section {
  margin-bottom: 20px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  flex: 1;
  max-width: 400px;
}

.refresh-btn {
  border-radius: 4px;
}

/* 数据集网格 */
.datasets-grid {
  min-height: 400px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.dataset-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease;
  border: 1px solid #e0e0e0;
}

.dataset-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.dataset-meta {
  flex: 1;
}

.dataset-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 6px 0;
}

.card-body {
  margin-bottom: 20px;
}

.dataset-description {
  color: #666;
  line-height: 1.5;
  margin-bottom: 16px;
  height: 3em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.dataset-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  color: #888;
  font-size: 0.9rem;
}

.card-footer {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  border-radius: 4px;
}

/* 任务相关样式 */
.task-filters {
  margin-bottom: 20px;
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.tasks-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
  border-left: 4px solid #e0e0e0;
}

.task-card-pending {
  border-left-color: #409eff;
}

.task-card-running {
  border-left-color: #e6a23c;
}

.task-card-completed {
  border-left-color: #67c23a;
}

.task-card-failed {
  border-left-color: #f56c6c;
}

.task-card-cancelled {
  border-left-color: #909399;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.task-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.task-time {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #888;
  font-size: 0.9rem;
}

.task-info {
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

.info-value {
  font-weight: 600;
  color: #333;
}

.task-progress {
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 0.9rem;
  color: #666;
}

.task-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 对话框样式 */
.dataset-detail {
  padding: 20px 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.header-info {
  flex: 1;
}

.detail-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.detail-tags {
  display: flex;
  gap: 8px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-section h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.description-text {
  color: #666;
  line-height: 1.6;
  font-size: 1rem;
  background: #f9f9f9;
  padding: 16px;
  border-radius: 6px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-card {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-text {
  flex: 1;
}

.info-number {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.info-desc {
  color: #666;
  font-size: 0.9rem;
}

.sample-questions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-card {
  background: #f9f9f9;
  border-radius: 6px;
  padding: 16px;
  border-left: 3px solid #409eff;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-index {
  background: #409eff;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9rem;
}

.question-body p {
  color: #333;
  line-height: 1.6;
  margin-bottom: 12px;
}

.answers-section {
  background: white;
  padding: 12px;
  border-radius: 4px;
  margin-top: 8px;
}

.answers-list {
  margin-left: 16px;
  color: #666;
}

.answers-list li {
  margin-bottom: 4px;
  line-height: 1.4;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .grid-container {
    grid-template-columns: 1fr;
  }
  
  .search-bar {
    flex-direction: column;
  }
  
  .task-header {
    flex-direction: column;
    gap: 8px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .detail-header {
    flex-direction: column;
    text-align: center;
  }
}
</style>

<template>
  <div class="marketplace-container">
    <!-- 头部标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1>🤖 LLM评测平台</h1>
        <p class="header-subtitle">管理和监控您的LLM评测任务</p>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-number">{{ tasks.length }}</span>
          <span class="stat-label">总任务数</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ completedTasksCount }}</span>
          <span class="stat-label">已完成</span>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <div class="tabs-container">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="custom-tabs">
        <el-tab-pane name="marketplace">
          <template #label>
            <span class="tab-label">📋 我的任务</span>
          </template>
          
          <!-- 任务筛选器 -->
          <div class="filters-section">
            <div class="filter-group">              
              <el-select 
                v-model="taskStatusFilter" 
                placeholder="任务状态" 
                clearable 
                @change="loadTasks"
                size="default"
                class="status-filter"
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
                class="refresh-btn"
              >
                <span v-if="tasksLoading" class="loading-spinner"></span>
                🔄 刷新任务
              </el-button>
            </div>
          </div>

          <!-- 任务列表 -->
          <div class="tasks-list" v-loading="tasksLoading">
            <el-empty 
              v-if="tasks.length === 0 && !tasksLoading" 
              description="暂无评测任务"
              :image-size="120"
              class="empty-state"
            >
              <template #description>
                <p>还没有创建任何评测任务</p>
                <el-button type="primary" @click="activeTab = 'marketplace'" class="create-task-btn">
                  🚀 去创建任务
                </el-button>
              </template>
            </el-empty>
            
            <div v-else class="tasks-container">
              <div 
                v-for="task in tasks" 
                :key="task.id" 
                class="task-row"
                :class="getTaskCardClass(task.status)"
              >
                <!-- 任务标题和状态 -->
                <div class="task-title-cell">
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
                
                <!-- 数据集 -->
                <div class="task-dataset-cell">
                  <div class="cell-label">📁 数据集</div>
                  <div class="cell-value">{{ task.dataset?.name || '未知' }}</div>
                </div>
                
                <!-- 模型 -->
                <div class="task-model-cell">
                  <div class="cell-label">🤖 模型</div>
                  <div class="cell-value">{{ task.model?.display_name || '未知' }}</div>
                </div>
                
                <!-- 进度信息 -->
                <div class="task-progress-cell">
                  <div class="progress-numbers">
                    <span class="completed">{{ task.completed_questions || 0 }}</span>
                    <span class="separator">/</span>
                    <span class="total">{{ task.total_questions || 0 }}</span>
                  </div>
                  <div v-if="isTaskInProgress(task.status) || task.status === 'completed'" class="progress-bar-mini">
                    <el-progress 
                      :percentage="task.progress || 0" 
                      :status="task.status === 'completed' ? 'success' : (task.status === 'failed' ? 'exception' : '')"
                      :stroke-width="6"
                      :show-text="false"
                    />
                  </div>
                </div>
                
                <!-- 创建时间 -->
                <div class="task-time-cell">
                  <div class="cell-label">📅 创建时间</div>
                  <div class="cell-value">{{ formatDateTime(task.created_at) }}</div>
                </div>
                
                <!-- 操作按钮 -->
                <div class="task-actions-cell">
                  <el-button 
                    size="small" 
                    type="primary"
                    @click="continueTask(task)"
                    v-if="canContinueTask(task.status)"
                    class="action-btn"
                  >
                    🔄 继续
                  </el-button>
                  <el-button 
                    size="small" 
                    type="success"
                    @click="viewTaskResults(task)"
                    v-if="task.status === 'completed'"
                    class="action-btn"
                  >
                    📊 结果
                  </el-button>
                  <el-button 
                    size="small" 
                    type="danger" 
                    @click="cancelTask(task)"
                    v-if="canCancelTask(task.status)"
                    class="action-btn"
                  >
                    ❌ 取消
                  </el-button>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="downloadTaskResults(task)"
                    v-if="task.status === 'completed'"
                    class="action-btn"
                  >
                    📥 下载
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
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

// 计算属性
const completedTasksCount = computed(() => {
  return tasks.value.filter(task => task.status === 'completed').length
})

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
  return `task-row-${status}`
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
.marketplace-container {
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 249, 250, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.page-header:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.header-content h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 0.5rem 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-subtitle {
  color: #6c757d;
  font-size: 1rem;
  margin: 0;
  font-weight: 400;
}

.header-stats {
  display: flex;
  gap: 2rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
}

.stat-number {
  font-size: 1.75rem;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  font-size: 0.85rem;
  color: #6c757d;
  font-weight: 500;
}

/* 标签页容器 */
.tabs-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 249, 250, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.custom-tabs {
  padding: 1.5rem;
}

.tab-label {
  font-size: 1rem;
  font-weight: 600;
  color: #495057;
}

/* 筛选器区域 */
.filters-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 1px solid #dee2e6;
}

.filter-group {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.status-filter {
  min-width: 200px;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 任务列表 */
.tasks-list {
  min-height: 400px;
}

.empty-state {
  padding: 3rem 0;
}

.empty-state p {
  font-size: 1.1rem;
  color: #6c757d;
  margin-bottom: 1.5rem;
}

.create-task-btn {
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.create-task-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.tasks-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* 任务行样式 */
.task-row {
  background: white;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
  display: grid;
  grid-template-columns: 2fr 1.2fr 1.2fr 1fr 1.2fr 1.5fr;
  gap: 1rem;
  align-items: center;
  min-height: 80px;
  position: relative;
}

.task-row::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: 2px 0 0 2px;
}

.task-row:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* 根据任务状态调整左边框颜色 */
.task-row-config_params::before { background: #409EFF; }
.task-row-config_prompts::before { background: #409EFF; }
.task-row-generating_answers::before { background: #E6A23C; }
.task-row-evaluating_answers::before { background: #E6A23C; }
.task-row-completed::before { background: #67C23A; }
.task-row-failed::before { background: #F56C6C; }
.task-row-cancelled::before { background: #909399; }

/* 单元格样式 */
.task-title-cell {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
}

.task-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
  line-height: 1.3;
}

.status-tag {
  font-weight: 500;
  border-radius: 6px;
}

.task-dataset-cell,
.task-model-cell,
.task-time-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.cell-label {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 500;
}

.cell-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
  line-height: 1.3;
}

.task-progress-cell {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
}

.progress-numbers {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 600;
}

.progress-numbers .completed {
  color: #67C23A;
}

.progress-numbers .separator {
  color: #909399;
}

.progress-numbers .total {
  color: #6c757d;
}

.progress-bar-mini {
  width: 100%;
  max-width: 80px;
}

.task-actions-cell {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.action-btn {
  font-size: 0.8rem;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.info-item:hover {
  background: #e9ecef;
  transform: translateY(-1px);
}

.info-label {
  font-size: 0.8rem;
  color: #6c757d;
  font-weight: 500;
}

.info-value {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

.task-progress {
  margin-bottom: 1.25rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: #6c757d;
  font-weight: 500;
}

.progress-bar {
  border-radius: 8px;
  overflow: hidden;
}

.progress-bar :deep(.el-progress-bar__outer) {
  border-radius: 8px;
  background: #e9ecef;
}

.progress-bar :deep(.el-progress-bar__inner) {
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.task-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  justify-content: flex-end;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
  width: 100%;
  padding: 0.5rem 1rem;
  justify-content: center;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.continue-btn:hover {
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.view-btn:hover {
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
}

.cancel-btn:hover {
  box-shadow: 0 4px 15px rgba(245, 108, 108, 0.3);
}

.download-btn:hover {
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

/* 对话框样式 */
.detail-dialog :deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.detail-dialog :deep(.el-dialog__header) {
  padding: 1.5rem 2rem 1rem;
  border-bottom: 1px solid #e9ecef;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.detail-dialog :deep(.el-dialog__title) {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
}

.detail-dialog :deep(.el-dialog__body) {
  padding: 2rem;
}

.dataset-detail {
  padding: 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
}

.header-info {
  flex: 1;
}

.detail-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 1rem 0;
}

.detail-tags {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.detail-tags :deep(.el-tag) {
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: none;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.info-section h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid rgba(102, 126, 234, 0.2);
  display: inline-block;
}

.description-text {
  color: #495057;
  line-height: 1.7;
  font-size: 1rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 1.25rem;
  border-radius: 12px;
  border: 1px solid #dee2e6;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.25rem;
}

.info-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 1.5rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
  border: 1px solid #dee2e6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.info-number {
  font-size: 1.75rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 0.25rem;
}

.info-desc {
  color: #6c757d;
  font-size: 0.9rem;
  font-weight: 500;
}

.sample-questions {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.question-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid #dee2e6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.question-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  border-color: #667eea;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.question-index {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.85rem;
}

.question-body p {
  color: #495057;
  line-height: 1.6;
  margin-bottom: 0.75rem;
  font-size: 1rem;
}

.question-body p strong {
  font-weight: 600;
  color: #2c3e50;
}

.answers-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 1rem;
  border-radius: 8px;
  margin-top: 0.75rem;
  border: 1px solid #dee2e6;
}

.answers-section p strong {
  font-weight: 600;
  color: #2c3e50;
}

.answers-list {
  margin: 0.75rem 0 0 0;
  padding-left: 1.25rem;
  list-style-type: disc;
  color: #495057;
}

.answers-list li {
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}

.dialog-footer .el-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  border-radius: 10px;
  transition: all 0.3s ease;
  min-width: 120px;
  justify-content: center;
}

.dialog-footer .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.close-btn:hover {
  box-shadow: 0 4px 15px rgba(108, 117, 125, 0.3);
}

.download-btn:hover {
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.start-btn:hover {
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .tasks-container {
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  }
}

@media (max-width: 992px) {
  .tasks-container {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1.5rem;
  }
  
  .header-stats {
    align-self: stretch;
    justify-content: space-around;
  }
}

@media (max-width: 768px) {
  .marketplace-container {
    padding: 1rem;
  }
  
  .page-header {
    padding: 1.5rem;
  }
  
  .page-header h1 {
    font-size: 1.75rem;
  }
  
  .task-row {
    grid-template-columns: 1fr;
    gap: 0.75rem;
    padding: 1rem;
    text-align: left;
  }
  
  .task-title-cell {
    align-items: flex-start;
  }
  
  .task-dataset-cell,
  .task-model-cell,
  .task-time-cell {
    align-items: flex-start;
  }
  
  .task-progress-cell {
    align-items: flex-start;
  }
  
  .progress-bar-mini {
    max-width: 100%;
  }
  
  .task-actions-cell {
    justify-content: flex-start;
  }
  
  .action-btn {
    font-size: 0.75rem;
    padding: 0.375rem 0.75rem;
  }
  
  .filter-group {
    flex-direction: column;
    align-items: stretch;
  }
  
  .status-filter {
    width: 100% !important;
  }
  
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
  }
  
  .detail-title {
    font-size: 1.5rem;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .dialog-footer {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .dialog-footer .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 1rem;
  }
  
  .page-header h1 {
    font-size: 1.5rem;
  }
  
  .header-stats {
    flex-direction: column;
    gap: 1rem;
  }
  
  .stat-item {
    flex-direction: row;
    justify-content: space-between;
    padding: 0.75rem 1rem;
  }
  
  .custom-tabs {
    padding: 1rem;
  }
  
  .filters-section {
    padding: 1rem;
  }
  
  .task-card {
    padding: 1rem;
  }
  
  .task-actions {
    flex-direction: column;
  }
  
  .action-btn {
    width: 100%;
  }
}
</style>

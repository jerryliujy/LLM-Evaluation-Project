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
.marketplace-container {
  padding: 20px;
  background-color: #f7f8fa; /* 更柔和的背景色 */
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 24px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.06);
}

.page-header h1 {
  font-size: 1.8rem; /* 调整标题大小 */
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.page-header .stats {
  font-size: 0.9rem;
  color: #606266;
}

.page-header .stats span {
  margin-left: 16px;
}


/* 标签页 */
.el-tabs {
  background-color: #ffffff;
  padding: 10px 20px; /* 调整内边距 */
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.06);
}

.tab-label {
  font-size: 1rem; /* 调整标签字体大小 */
  font-weight: 500;
}

/* 任务筛选器 */
.task-filters {
  margin-bottom: 20px;
  padding: 16px; /* 增加内边距 */
  background-color: #fbfcfd; /* 轻微背景色区分 */
  border-radius: 6px;
  /* border: 1px solid #e9e9eb; */
}

.filter-group {
  display: flex;
  gap: 16px; /* 调整元素间距 */
  align-items: center;
}

/* 任务列表 */
.tasks-list {
  min-height: 300px; /* 调整最小高度 */
}

.tasks-container {
  display: grid; /* 改为 grid 布局 */
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); /* 响应式列 */
  gap: 20px; /* 卡片间距 */
}

.task-card {
  background: #ffffff;
  border-radius: 8px; /* 更大的圆角 */
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); /* 调整阴影 */
  border: 1px solid #e9e9eb; /* 更淡的边框 */
  transition: box-shadow 0.3s ease, transform 0.2s ease; /* 添加过渡效果 */
  display: flex;
  flex-direction: column;
  justify-content: space-between; /* 使内容垂直分布 */
}

.task-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12); /* 悬停阴影 */
  transform: translateY(-3px); /* 轻微上浮效果 */
}

/* 根据任务状态调整左边框颜色 */
.task-card-config_params { border-left: 5px solid #409EFF; }
.task-card-config_prompts { border-left: 5px solid #409EFF; }
.task-card-generating_answers { border-left: 5px solid #E6A23C; }
.task-card-evaluating_answers { border-left: 5px solid #E6A23C; }
.task-card-completed { border-left: 5px solid #67C23A; }
.task-card-failed { border-left: 5px solid #F56C6C; }
.task-card-cancelled { border-left: 5px solid #909399; }


.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start; /* 顶部对齐 */
  margin-bottom: 12px; /* 调整间距 */
}

.task-title-section {
  display: flex;
  flex-direction: column; /* 标题和标签垂直排列 */
  gap: 6px; /* 标题和标签间距 */
  flex-grow: 1; /* 占据更多空间 */
}

.task-title {
  font-size: 1.2rem; /* 调整标题大小 */
  font-weight: 600;
  color: #303133;
  margin: 0;
  line-height: 1.3;
}

.status-tag {
  align-self: flex-start; /* 状态标签靠左 */
}

.task-time {
  display: flex;
  align-items: center;
  gap: 6px; /* 图标和时间间距 */
  color: #909399; /* 时间颜色 */
  font-size: 0.85rem; /* 时间字体大小 */
  white-space: nowrap; /* 防止时间换行 */
  margin-left: 10px; /* 与标题部分隔开 */
}

.task-info {
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr); /* 两列布局 */
  gap: 10px 16px; /* 行间距和列间距 */
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px; /* 标签和值之间的间距 */
}

.info-label {
  font-size: 0.85rem;
  color: #606266;
  font-weight: 400; /* 标签字体不加粗 */
}

.info-value {
  font-weight: 500; /* 值字体稍粗 */
  color: #303133;
  font-size: 0.9rem;
}

.task-progress {
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 0.85rem;
  color: #606266;
}

.progress-bar {
  /* el-progress 默认样式通常不错，可按需调整 */
  /* 例如：自定义高度 */
  /* --el-progress-bar-height: 10px; */
}
.progress-bar .el-progress-bar__outer {
  border-radius: 6px; /* 进度条圆角 */
}
.progress-bar .el-progress-bar__inner {
  border-radius: 6px; /* 进度条内部圆角 */
}


.task-actions {
  display: flex;
  gap: 10px; /* 按钮间距 */
  flex-wrap: wrap; /* 按钮换行 */
  margin-top: auto; /* 将按钮推到底部 */
  padding-top: 16px; /* 与上方内容分隔 */
  border-top: 1px solid #f0f2f5; /* 分隔线 */
}

.task-actions .action-btn {
  /* 按钮样式已由 Element Plus 提供，可按需覆盖 */
  /* 例如：统一大小 */
  /* padding: 8px 12px; */
  /* min-width: 80px; */ /* 示例：最小宽度 */
  /* 添加一些实际样式以避免空规则 */
  margin-right: 8px; /* 示例：按钮间添加一些右边距 */
}

/* 空状态 */
.el-empty {
  padding: 40px 0; /* 增加上下内边距 */
}
.el-empty p {
  font-size: 1rem;
  color: #909399;
  margin-bottom: 20px;
}

/* 对话框样式 */
.detail-dialog .el-dialog__header {
  padding: 20px 24px 10px; /* 调整头部内边距 */
  border-bottom: 1px solid #e9e9eb; /* 头部底边框 */
  margin-right: 0; /* 移除element plus默认的margin */
}

.detail-dialog .el-dialog__title {
  font-size: 1.3rem; /* 标题字体 */
  font-weight: 600;
  color: #303133;
}

.detail-dialog .el-dialog__body {
  padding: 20px 24px; /* 主体内容内边距 */
}

.dataset-detail {
  padding: 0; /* 移除内部的 padding，由 dialog body 控制 */
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 20px; /* 间距 */
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f2f5; /* 更柔和的分割线 */
}

.header-info {
  flex: 1;
}

.detail-title {
  font-size: 1.6rem; /* 调整标题大小 */
  font-weight: 600;
  color: #2c3e50; /* 深色标题 */
  margin: 0 0 10px 0;
}

.detail-tags .el-tag {
  font-size: 0.9rem; /* 标签字体 */
  padding: 0 12px; /* 标签内边距 */
  height: 30px; /* 标签高度 */
  line-height: 30px; /* 标签行高 */
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 28px; /* 区块间距 */
}

.info-section h3 {
  font-size: 1.15rem; /* 小节标题 */
  font-weight: 600;
  color: #34495e; /* 小节标题颜色 */
  margin-bottom: 16px; /* 与内容间距 */
  padding-bottom: 8px; /* 标题下划线间距 */
  border-bottom: 2px solid #409EFF; /* 标题下划线 */
  display: inline-block; /* 使下划线适应文字宽度 */
}

.description-text {
  color: #555;
  line-height: 1.7;
  font-size: 0.95rem;
  background: #fdfdfd; /* 更亮的背景 */
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #f0f2f5;
}

.info-grid { /* 此处 info-grid 与任务卡片中的有重复，注意区分或合并 */
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); /* 调整最小宽度 */
  gap: 16px;
}

.info-card { /* 用于数据集详情中的信息卡片 */
  background: #f8f9fa; /* 卡片背景 */
  padding: 20px;
  border-radius: 8px;
  display: flex;
  flex-direction: column; /* 垂直排列 */
  align-items: flex-start; /* 左对齐 */
  gap: 8px;
  border: 1px solid #e9ecef;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

.info-number {
  font-size: 1.5rem; /* 数字大小 */
  font-weight: 600;
  color: #409EFF; /* 主题色 */
  margin-bottom: 2px;
}

.info-desc {
  color: #6c757d; /* 描述文字颜色 */
  font-size: 0.9rem;
}

.sample-questions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-card {
  background: #ffffff;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #e9ecef;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-index {
  background: #409EFF;
  color: white;
  padding: 5px 12px; /* 调整内边距 */
  border-radius: 16px; /* 更圆的角 */
  font-weight: 500;
  font-size: 0.85rem;
}

.question-body p {
  color: #333;
  line-height: 1.6;
  margin-bottom: 10px;
  font-size: 0.95rem;
}
.question-body p strong {
  font-weight: 600;
  color: #34495e;
}

.answers-section {
  background: #f9fafb; /* 答案区域背景 */
  padding: 12px;
  border-radius: 4px;
  margin-top: 10px;
  border: 1px solid #f0f2f5;
}
.answers-section p strong {
  font-weight: 500;
  color: #34495e;
}

.answers-list {
  margin-left: 0; /* 移除默认的 ul 缩进 */
  padding-left: 18px; /* 使用 padding 代替 margin */
  list-style-type: disc; /* 使用实心圆点 */
  color: #555;
}

.answers-list li {
  margin-bottom: 6px;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px; /* 页脚内边距 */
  border-top: 1px solid #e9e9eb; /* 页脚上边框 */
}

.dialog-footer .el-button {
  /* 可以为对话框按钮设置特定样式，如大小 */
  /* padding: 10px 20px; */
  /* min-width: 100px; */ /* 示例：最小宽度 */
  /* 添加一些实际样式以避免空规则 */
  margin-left: 10px; /* 示例：按钮间添加一些左边距 */
}


/* 移除旧的、可能冲突的样式 */
/* .llm-marketplace, .header, .header-content, .title-section, .page-title, .page-subtitle, .header-stats, .stat-item, .stat-label, .stat-number, .tabs-container, .custom-tabs, .filters-section, .search-bar, .search-input, .refresh-btn, .datasets-grid, .grid-container, .dataset-card, .card-header, .dataset-meta, .dataset-name, .card-body, .dataset-description, .dataset-stats, .card-footer, .action-btn (部分保留，看具体情况) */
/* .task-card-pending, .task-card-running, .task-card-completed, .task-card-failed, .task-card-cancelled (已用 border-left 替代) */


/* 响应式设计 */
@media (max-width: 992px) { /* 调整断点 */
  .tasks-container {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }
  .info-grid { /* 任务卡片内的信息栅格 */
    grid-template-columns: 1fr; /* 在较小屏幕上单列显示 */
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start; /* 左对齐 */
    gap: 12px;
  }
  .page-header h1 {
    font-size: 1.6rem;
  }
  .tasks-container {
    grid-template-columns: 1fr; /* 单列显示任务卡片 */
  }
  .filter-group {
    flex-direction: column;
    align-items: stretch; /* 筛选器元素撑满宽度 */
  }
  .filter-group .el-select {
    width: 100% !important; /* Element Plus select 宽度覆盖 */
  }
  .task-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .task-time {
    margin-left: 0; /* 移除左边距 */
  }
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
  }
  .detail-title {
    font-size: 1.4rem;
  }
  .info-grid { /* 对话框内的信息栅格 */
     grid-template-columns: 1fr;
  }
  .dialog-footer {
    flex-direction: column; /* 按钮垂直排列 */
    gap: 10px;
  }
  .dialog-footer .el-button {
    width: 100%; /* 按钮撑满宽度 */
  }
}
</style>

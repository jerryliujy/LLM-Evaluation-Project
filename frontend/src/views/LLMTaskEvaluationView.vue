<template>
  <div class="llm-task-evaluation">
    <div class="header">
      <h1>LLM评测任务管理</h1>
      <div class="actions">
        <el-button type="primary" @click="showCreateTaskDialog = true">
          <el-icon><Plus /></el-icon>
          创建新任务
        </el-button>
        <el-button @click="refreshTasks">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="task-list">
      <el-card v-for="task in tasks" :key="task.id" class="task-card">
        <template #header>
          <div class="card-header">
            <span class="task-name">{{ task.task_name }}</span>
            <el-tag :type="getStatusType(task.status)" class="status-tag">
              {{ getStatusText(task.status) }}
            </el-tag>
          </div>
        </template>
        
        <div class="task-content">
          <div class="task-info">
            <p><strong>数据集:</strong> {{ task.dataset?.name || 'Unknown' }}</p>
            <p><strong>模型:</strong> {{ task.model_name }}</p>
            <p><strong>创建时间:</strong> {{ formatDateTime(task.created_at) }}</p>
            <p v-if="task.completed_at"><strong>完成时间:</strong> {{ formatDateTime(task.completed_at) }}</p>
          </div>
          
          <!-- 进度条 -->
          <div v-if="task.status === 'running' || task.status === 'completed'" class="progress-section">
            <el-progress 
              :percentage="Math.round(task.progress)"
              :status="task.status === 'completed' ? 'success' : 'info'"
              :stroke-width="8"
            />
            <div class="progress-info">
              <span>{{ task.current_question }}/{{ task.total_questions }} 问题</span>
              <span v-if="task.average_score !== null">平均分: {{ task.average_score.toFixed(1) }}</span>
            </div>
          </div>
          
          <!-- 任务结果 -->
          <div v-if="task.status === 'completed'" class="results-section">
            <div class="results-stats">
              <el-statistic title="成功" :value="task.successful_count" />
              <el-statistic title="失败" :value="task.failed_count" />
              <el-statistic 
                v-if="task.average_score !== null" 
                title="平均分" 
                :value="task.average_score" 
                :precision="1" 
              />
            </div>
          </div>
          
          <!-- 错误信息 -->
          <div v-if="task.status === 'failed'" class="error-section">
            <el-alert
              title="任务执行失败"
              :description="task.error_message"
              type="error"
              show-icon
            />
          </div>
        </div>
        
        <template #footer>
          <div class="task-actions">
            <el-button size="small" @click="viewTaskDetails(task)">
              查看详情
            </el-button>
            <el-button 
              v-if="task.status === 'running' || task.status === 'pending'"
              size="small" 
              type="warning" 
              @click="cancelTask(task.id)"
            >
              取消任务
            </el-button>
            <el-button 
              v-if="task.status === 'completed'"
              size="small" 
              type="success" 
              @click="downloadResults(task.id)"
            >
              下载结果
            </el-button>
          </div>
        </template>
      </el-card>
      
      <!-- 空状态 -->
      <el-empty v-if="tasks.length === 0" description="暂无评测任务" />
    </div>

    <!-- 创建任务对话框 -->
    <el-dialog 
      v-model="showCreateTaskDialog" 
      title="创建LLM评测任务" 
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="taskFormRef" 
        :model="taskForm" 
        :rules="taskFormRules" 
        label-width="120px"
      >
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="taskForm.task_name" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="数据集" prop="dataset_id">
          <el-select v-model="taskForm.dataset_id" placeholder="选择数据集" style="width: 100%">
            <el-option 
              v-for="dataset in datasets" 
              :key="dataset.id" 
              :label="`${dataset.name} (${dataset.question_count}题)`"
              :value="dataset.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型" prop="model_name">
          <el-select v-model="taskForm.model_config.model_name" placeholder="选择模型" style="width: 100%">
            <el-option 
              v-for="model in availableModels" 
              :key="model.name" 
              :label="model.display_name"
              :value="model.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="API密钥" prop="api_key">
          <el-input 
            v-model="taskForm.model_config.api_key" 
            placeholder="请输入API密钥" 
            type="password" 
            show-password
          />
        </el-form-item>
        
        <el-form-item label="系统Prompt">
          <el-input 
            v-model="taskForm.model_config.system_prompt" 
            type="textarea" 
            :rows="4"
            placeholder="请输入系统prompt（可选）"
          />
        </el-form-item>
        
        <el-form-item label="问题限制">
          <el-input-number 
            v-model="taskForm.question_limit" 
            :min="1" 
            :max="1000"
            placeholder="限制评测问题数量（可选）"
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="taskForm.is_auto_score">
            启用自动评分（选择题）
          </el-checkbox>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateTaskDialog = false">取消</el-button>
          <el-button type="primary" @click="createTask" :loading="creating">
            创建并开始
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog 
      v-model="showTaskDetailDialog" 
      title="任务详情" 
      width="900px"
    >
      <div v-if="selectedTask">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ selectedTask.task_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedTask.status)">
              {{ getStatusText(selectedTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据集">{{ selectedTask.dataset?.name }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ selectedTask.model_name }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(selectedTask.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDateTime(selectedTask.started_at) }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- 实时进度 -->
        <div v-if="selectedTask.status === 'running'" class="task-progress">
          <h3>实时进度</h3>
          <el-progress 
            :percentage="Math.round(taskProgress.progress || 0)"
            :stroke-width="12"
          />
          <div class="progress-details">
            <p>当前: {{ taskProgress.current_question }}/{{ taskProgress.total_questions }}</p>
            <p v-if="taskProgress.questions_per_minute">
              处理速度: {{ taskProgress.questions_per_minute.toFixed(1) }} 题/分钟
            </p>
            <p v-if="taskProgress.estimated_remaining_time">
              预计剩余: {{ Math.round(taskProgress.estimated_remaining_time / 60) }} 分钟
            </p>
            <p v-if="taskProgress.latest_answer">
              最新回答: {{ taskProgress.latest_answer }}
            </p>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { llmEvaluationService } from '@/services/llmEvaluationService'

// 响应式数据
const tasks = ref([])
const datasets = ref([])
const availableModels = ref([])
const showCreateTaskDialog = ref(false)
const showTaskDetailDialog = ref(false)
const selectedTask = ref(null)
const taskProgress = ref({})
const creating = ref(false)

// 表单数据
const taskForm = reactive({
  task_name: '',
  dataset_id: null,
  model_config: {
    model_name: '',
    api_key: '',
    system_prompt: '',
    temperature: 0.7,
    max_tokens: 1000
  },
  question_limit: null,
  is_auto_score: true,
  evaluation_config: {}
})

// 表单验证规则
const taskFormRules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  dataset_id: [{ required: true, message: '请选择数据集', trigger: 'change' }],
  'model_config.model_name': [{ required: true, message: '请选择模型', trigger: 'change' }],
  'model_config.api_key': [{ required: true, message: '请输入API密钥', trigger: 'blur' }]
}

const taskFormRef = ref()

// 生命周期
onMounted(async () => {
  await loadInitialData()
})

// 方法
const loadInitialData = async () => {
  try {
    await Promise.all([
      loadTasks(),
      loadDatasets(),
      loadAvailableModels()
    ])
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  }
}

const loadTasks = async () => {
  try {
    tasks.value = await llmEvaluationService.getMyEvaluationTasks()
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

const loadDatasets = async () => {
  try {
    datasets.value = await llmEvaluationService.getMarketplaceDatasets()
  } catch (error) {
    console.error('加载数据集失败:', error)
  }
}

const loadAvailableModels = async () => {
  try {
    availableModels.value = await llmEvaluationService.getAvailableModels()
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const createTask = async () => {
  try {
    await taskFormRef.value.validate()
    creating.value = true
    
    const taskData = {
      task_name: taskForm.task_name,
      dataset_id: taskForm.dataset_id,
      model_config: taskForm.model_config,
      evaluation_config: taskForm.evaluation_config,
      is_auto_score: taskForm.is_auto_score,
      question_limit: taskForm.question_limit
    }
    
    await llmEvaluationService.createEvaluationTask(taskData)
    
    ElMessage.success('任务创建成功，正在后台执行')
    showCreateTaskDialog.value = false
    resetForm()
    await loadTasks()
    
  } catch (error) {
    ElMessage.error('创建任务失败')
    console.error(error)
  } finally {
    creating.value = false
  }
}

const cancelTask = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要取消这个任务吗？', '确认取消', {
      type: 'warning'
    })
    
    await llmEvaluationService.cancelEvaluationTask(taskId)
    ElMessage.success('任务已取消')
    await loadTasks()
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消任务失败')
      console.error(error)
    }
  }
}

const viewTaskDetails = async (task: any) => {
  selectedTask.value = task
  showTaskDetailDialog.value = true
  
  if (task.status === 'running') {
    await loadTaskProgress(task.id)
  }
}

const loadTaskProgress = async (taskId: number) => {
  try {
    taskProgress.value = await llmEvaluationService.getTaskProgress(taskId)
  } catch (error) {
    console.error('加载任务进度失败:', error)
  }
}

const downloadResults = async (taskId: number) => {
  try {
    const results = await llmEvaluationService.downloadTaskResults(taskId, {
      format: 'json',
      include_raw_responses: false,
      include_prompts: false
    })
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(results, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `evaluation_results_${taskId}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('结果下载完成')
    
  } catch (error) {
    ElMessage.error('下载结果失败')
    console.error(error)
  }
}

const refreshTasks = async () => {
  await loadTasks()
  ElMessage.success('任务列表已刷新')
}

const resetForm = () => {
  Object.assign(taskForm, {
    task_name: '',
    dataset_id: null,
    model_config: {
      model_name: '',
      api_key: '',
      system_prompt: '',
      temperature: 0.7,
      max_tokens: 1000
    },
    question_limit: null,
    is_auto_score: true,
    evaluation_config: {}
  })
}

// 工具函数
const getStatusType = (status: string) => {
  const statusMap = {
    'pending': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString()
}
</script>

<style scoped>
.llm-task-evaluation {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
}

.task-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.task-card {
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-name {
  font-weight: bold;
}

.status-tag {
  margin-left: 10px;
}

.task-content {
  margin-bottom: 15px;
}

.task-info p {
  margin: 8px 0;
}

.progress-section {
  margin: 15px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.results-section {
  margin: 15px 0;
}

.results-stats {
  display: flex;
  gap: 20px;
}

.error-section {
  margin: 15px 0;
}

.task-actions {
  display: flex;
  gap: 10px;
}

.task-progress {
  margin-top: 20px;
}

.progress-details {
  margin-top: 15px;
}

.progress-details p {
  margin: 5px 0;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

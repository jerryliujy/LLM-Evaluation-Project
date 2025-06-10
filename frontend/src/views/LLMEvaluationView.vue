<template>
  <div class="llm-evaluation">
    <div class="header">
      <h1>大模型评测</h1>
      <p>上传您的模型回答，获得自动化评测结果</p>
    </div>

    <!-- 步骤指示器 -->
    <el-steps :active="currentStep" align-center style="margin-bottom: 30px;">
      <el-step title="选择数据集" description="选择要评测的数据集" />
      <el-step title="配置模型" description="设置模型信息" />
      <el-step title="上传回答" description="上传模型回答文件" />
      <el-step title="查看结果" description="查看评测结果" />
    </el-steps>

    <!-- 步骤1: 数据集选择 -->
    <div v-if="currentStep === 0" class="step-content">
      <div class="dataset-selection">
        <h3>选择评测数据集</h3>
        <div v-if="selectedDatasetFromRoute">
          <el-card class="selected-dataset">
            <div class="dataset-info">
              <h4>{{ selectedDatasetFromRoute.name }}</h4>
              <p>{{ selectedDatasetFromRoute.description }}</p>
              <div class="dataset-stats">
                <span>问题数量: {{ selectedDatasetFromRoute.question_count }}</span>
                <span>版本: v{{ selectedDatasetFromRoute.version }}</span>
              </div>
            </div>
          </el-card>
        </div>
        <div v-else>
          <el-select 
            v-model="selectedDatasetId" 
            placeholder="请选择数据集" 
            style="width: 100%;"
            filterable
          >
            <el-option
              v-for="dataset in availableDatasets"
              :key="dataset.id"
              :label="`${dataset.name} (v${dataset.version}) - ${dataset.question_count}题`"
              :value="dataset.id"
            />
          </el-select>
        </div>
        
        <div class="step-actions">
          <el-button type="primary" @click="nextStep" :disabled="!hasSelectedDataset">
            下一步
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤2: 模型配置 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="model-config">
        <h3>配置模型信息</h3>
        <el-form :model="modelConfig" label-width="120px">
          <el-form-item label="模型名称" required>
            <el-select v-model="modelConfig.name" placeholder="选择或输入模型名称" filterable allow-create>
              <el-option label="qwen-plus" value="qwen-plus" />
              <el-option label="qwen-max" value="qwen-max" />
              <el-option label="qwen-turbo" value="qwen-turbo" />
              <el-option label="gpt-4" value="gpt-4" />
              <el-option label="gpt-3.5-turbo" value="gpt-3.5-turbo" />
              <el-option label="claude-3" value="claude-3" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="模型版本" required>
            <el-input v-model="modelConfig.version" placeholder="如: 20240401" />
          </el-form-item>
          
          <el-form-item label="所属机构">
            <el-input v-model="modelConfig.affiliation" placeholder="如: Alibaba, OpenAI" />
          </el-form-item>
        </el-form>
        
        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button type="primary" @click="nextStep" :disabled="!isModelConfigValid">
            下一步
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤3: 文件上传 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="file-upload">
        <h3>上传模型回答</h3>
        
        <!-- 文件格式说明 -->
        <el-alert
          title="文件格式要求"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <div>
            <p>请上传JSON格式文件，包含以下结构：</p>
            <pre>{{ formatExample }}</pre>
          </div>
        </el-alert>

        <!-- 文件上传区域 -->
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="handleFileChange"
          :before-remove="handleFileRemove"
          accept=".json"
          drag
          style="width: 100%;"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将JSON文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              只能上传JSON文件，且不超过10MB
            </div>
          </template>
        </el-upload>

        <!-- 上传进度 -->
        <div v-if="uploadProgress > 0" class="upload-progress">
          <el-progress :percentage="uploadProgress" />
        </div>
        
        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button 
            type="primary" 
            @click="submitEvaluation" 
            :loading="uploading"
            :disabled="!selectedFile"
          >
            开始评测
          </el-button>
        </div>
      </div>
    </div>

    <!-- 步骤4: 评测结果 -->
    <div v-if="currentStep === 3" class="step-content">
      <div class="evaluation-results">
        <h3>评测结果</h3>
        
        <div v-if="evaluationResults" class="results-summary">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-statistic title="总问题数" :value="evaluationResults.total_answers" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="已评测" :value="evaluatedCount" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="平均分" :value="averageScore" :precision="1" suffix="分" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="评测状态" :value="evaluationStatus" />
            </el-col>
          </el-row>
        </div>

        <!-- 答案列表 -->
        <div v-if="llmAnswers.length > 0" class="answers-list">
          <h4>回答详情</h4>
          <el-table :data="llmAnswers" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column label="问题" min-width="200">
              <template #default="{ row }">
                <div class="question-cell">
                  <p class="question-text">{{ row.std_question?.body || '未知问题' }}</p>
                  <el-tag size="small">{{ getQuestionTypeText(row.std_question?.question_type) }}</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="模型回答" min-width="200">
              <template #default="{ row }">
                <div class="answer-cell">
                  {{ row.answer }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="评测状态" width="120">
              <template #default="{ row }">
                <el-button 
                  v-if="!hasEvaluation(row.id)" 
                  size="small" 
                  type="primary" 
                  @click="evaluateAnswer(row)"
                >
                  评测
                </el-button>
                <el-tag v-else type="success">已评测</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="viewEvaluation(row)">查看详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="step-actions">
          <el-button @click="restart">重新开始</el-button>
          <el-button type="success" @click="downloadResults">下载结果</el-button>
        </div>
      </div>
    </div>

    <!-- 评测详情对话框 -->
    <el-dialog
      v-model="showEvaluationDialog"
      title="评测详情"
      width="70%"
      destroy-on-close
    >
      <div v-if="selectedAnswer" class="evaluation-detail">
        <div class="answer-info">
          <h4>问题</h4>
          <p>{{ selectedAnswer.std_question?.body }}</p>
          
          <h4>模型回答</h4>
          <p>{{ selectedAnswer.answer }}</p>
        </div>

        <div v-if="answerEvaluations.length > 0" class="evaluations">
          <h4>评测结果</h4>
          <div v-for="evaluation in answerEvaluations" :key="evaluation.id" class="evaluation-item">
            <el-card>
              <div class="eval-header">
                <span class="score">{{ evaluation.score }}分</span>
                <el-tag :type="evaluation.evaluator_type === 'user' ? 'primary' : 'success'">
                  {{ evaluation.evaluator_type === 'user' ? '人工评测' : '自动评测' }}
                </el-tag>
              </div>
              <div v-if="evaluation.feedback" class="feedback">
                <p><strong>反馈：</strong>{{ evaluation.feedback }}</p>
              </div>
              <div v-if="evaluation.evaluation_criteria" class="criteria">
                <p><strong>评测标准：</strong>{{ evaluation.evaluation_criteria }}</p>
              </div>
            </el-card>
          </div>
        </div>

        <!-- 手动评测表单 -->
        <div class="manual-evaluation">
          <h4>手动评测</h4>
          <el-form :model="manualEvaluation" label-width="100px">
            <el-form-item label="评分">
              <el-slider 
                v-model="manualEvaluation.score" 
                :min="0" 
                :max="100" 
                show-stops 
                show-input 
              />
            </el-form-item>
            <el-form-item label="评测标准">
              <el-input 
                v-model="manualEvaluation.evaluation_criteria" 
                type="textarea" 
                placeholder="请输入评测标准..."
              />
            </el-form-item>
            <el-form-item label="反馈意见">
              <el-input 
                v-model="manualEvaluation.feedback" 
                type="textarea" 
                placeholder="请输入反馈意见..."
              />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEvaluationDialog = false">关闭</el-button>
          <el-button 
            v-if="selectedAnswer && selectedAnswer.std_question?.question_type === 'choice'"
            type="warning"
            @click="autoEvaluate"
            :loading="autoEvaluating"
          >
            自动评测
          </el-button>
          <el-button 
            type="primary" 
            @click="submitManualEvaluation"
            :loading="submittingEvaluation"
          >
            提交评测
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import apiClient from '@/services/api'

const route = useRoute()

// 响应式数据
const currentStep = ref(0)
const availableDatasets = ref<any[]>([])
const selectedDatasetId = ref<number | null>(null)
const selectedDatasetFromRoute = ref<any>(null)

const modelConfig = reactive({
  name: '',
  version: '',
  affiliation: ''
})

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)

const evaluationResults = ref<any>(null)
const llmAnswers = ref<any[]>([])
const evaluations = ref<any[]>([])

// 对话框相关
const showEvaluationDialog = ref(false)
const selectedAnswer = ref<any>(null)
const answerEvaluations = ref<any[]>([])
const manualEvaluation = reactive({
  score: 80,
  evaluation_criteria: '',
  feedback: ''
})
const autoEvaluating = ref(false)
const submittingEvaluation = ref(false)

// 计算属性
const hasSelectedDataset = computed(() => {
  return selectedDatasetFromRoute.value || selectedDatasetId.value
})

const isModelConfigValid = computed(() => {
  return modelConfig.name && modelConfig.version
})

const evaluatedCount = computed(() => {
  return llmAnswers.value.filter(answer => hasEvaluation(answer.id)).length
})

const averageScore = computed(() => {
  const evaluatedAnswers = llmAnswers.value.filter(answer => hasEvaluation(answer.id))
  if (evaluatedAnswers.length === 0) return 0
    const totalScore = evaluatedAnswers.reduce((sum, answer) => {
    const answerEvals = evaluations.value.filter(evaluation => evaluation.llm_answer_id === answer.id)
    const avgScore = answerEvals.length > 0 
      ? answerEvals.reduce((s, e) => s + e.score, 0) / answerEvals.length 
      : 0
    return sum + avgScore
  }, 0)
  
  return totalScore / evaluatedAnswers.length
})

const evaluationStatus = computed(() => {
  if (evaluatedCount.value === 0) return '未开始'
  if (evaluatedCount.value === llmAnswers.value.length) return '已完成'
  return '进行中'
})

const formatExample = `{
  "answers": [
    {
      "question_id": 1,
      "answer": "Docker是一个开源的容器化平台，它可以让开发者将应用程序和依赖项打包到轻量级的容器中。",
      "scoring_points": [
        {"answer": "容器化技术", "point_order": 0},
        {"answer": "应用程序打包", "point_order": 1},
        {"answer": "轻量级部署", "point_order": 2}
      ]
    },
    {
      "question_id": 2,
      "answer": "A",
      "scoring_points": []
    }
  ]
}`

// 生命周期
onMounted(async () => {
  // 检查是否从路由传递了数据集ID
  if (route.params.datasetId) {
    try {
      const response = await apiClient.get(`/llm/marketplace/datasets`)
      const dataset = response.data.find((d: any) => d.id === parseInt(route.params.datasetId as string))
      if (dataset) {
        selectedDatasetFromRoute.value = dataset
      }
    } catch (error) {
      console.error('加载数据集失败:', error)
    }
  }
  
  // 加载可用数据集
  await loadAvailableDatasets()
})

// 方法
const loadAvailableDatasets = async () => {
  try {
    const response = await apiClient.get('/llm/marketplace/datasets')
    availableDatasets.value = response.data
  } catch (error) {
    console.error('加载可用数据集失败:', error)
  }
}

const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const handleFileChange = (uploadFile: any) => {
  const file = uploadFile.raw
  
  // 验证文件大小（10MB限制）
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    return
  }
  
  // 验证文件类型
  if (!file.name.toLowerCase().endsWith('.json')) {
    ElMessage.error('只支持JSON格式文件')
    return
  }
  
  selectedFile.value = file
  
  // 尝试读取和验证JSON格式
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = e.target?.result as string
      const data = JSON.parse(content)
      
      // 验证JSON结构
      if (!data.answers || !Array.isArray(data.answers)) {
        ElMessage.warning('JSON文件格式不正确：缺少answers数组')
        return
      }
      
      // 验证答案项目格式
      const invalidItems = data.answers.filter((item: any, index: number) => {
        return !item.question_id || !item.answer
      })
      
      if (invalidItems.length > 0) {
        ElMessage.warning(`JSON文件格式不正确：第${invalidItems.length}个答案缺少必要字段`)
        return
      }
      
      ElMessage.success(`文件验证成功，包含${data.answers.length}个答案`)
    } catch (error) {
      ElMessage.error('JSON文件格式错误，请检查文件内容')
      selectedFile.value = null
    }
  }
  reader.readAsText(file)
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const submitEvaluation = async () => {
  if (!selectedFile.value) {
    ElMessage.error('请选择文件')
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  
  try {
    const formData = new FormData()
    formData.append('answers_file', selectedFile.value)
    formData.append('llm_name', modelConfig.name)
    formData.append('llm_version', modelConfig.version)
    formData.append('dataset_id', String(selectedDatasetFromRoute.value?.id || selectedDatasetId.value))
    
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    const response = await apiClient.post('/llm/evaluation/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    clearInterval(progressInterval)
    uploadProgress.value = 100

    evaluationResults.value = response.data
    llmAnswers.value = response.data.created_answers || []
    
    // 加载评测结果
    await loadEvaluations()
    
    ElMessage.success('评测上传成功')
    nextStep()
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const loadEvaluations = async () => {
  try {
    // 加载所有答案的评测结果
    const evaluationPromises = llmAnswers.value.map(answer =>
      apiClient.get(`/llm/evaluation/statistics/${answer.id}`)
    )
    
    const results = await Promise.all(evaluationPromises)
    evaluations.value = results.flatMap(result => result.data.evaluations || [])
  } catch (error) {
    console.error('加载评测结果失败:', error)
  }
}

const hasEvaluation = (answerId: number) => {
  return evaluations.value.some(evaluation => evaluation.llm_answer_id === answerId)
}

const getQuestionTypeText = (type: string) => {
  return type === 'choice' ? '选择题' : '文本题'
}

const evaluateAnswer = (answer: any) => {
  selectedAnswer.value = answer
  answerEvaluations.value = evaluations.value.filter(evaluation => evaluation.llm_answer_id === answer.id)
  
  // 重置手动评测表单
  manualEvaluation.score = 80
  manualEvaluation.evaluation_criteria = ''
  manualEvaluation.feedback = ''
  
  showEvaluationDialog.value = true
}

const viewEvaluation = (answer: any) => {
  evaluateAnswer(answer)
}

const autoEvaluate = async () => {
  if (!selectedAnswer.value) return
  
  autoEvaluating.value = true
  try {
    const response = await apiClient.post(`/llm/evaluation/auto/${selectedAnswer.value.id}`, {
      evaluation_criteria: '自动评测 - 选择题匹配'
    })
    
    // 添加到评测列表
    evaluations.value.push(response.data)
    answerEvaluations.value.push(response.data)
    
    ElMessage.success('自动评测完成')
  } catch (error) {
    console.error('自动评测失败:', error)
    ElMessage.error('自动评测失败')
  } finally {
    autoEvaluating.value = false
  }
}

const submitManualEvaluation = async () => {
  if (!selectedAnswer.value) return
  
  submittingEvaluation.value = true
  try {
    const evaluationData = {
      std_question_id: selectedAnswer.value.std_question.id,
      llm_answer_id: selectedAnswer.value.id,
      score: manualEvaluation.score,
      evaluator_type: 'user',
      evaluation_criteria: manualEvaluation.evaluation_criteria,
      feedback: manualEvaluation.feedback
    }
    
    const response = await apiClient.post('/llm/evaluation/manual', evaluationData)
    
    // 添加到评测列表
    evaluations.value.push(response.data)
    answerEvaluations.value.push(response.data)
    
    ElMessage.success('评测提交成功')
    showEvaluationDialog.value = false
  } catch (error) {
    console.error('提交评测失败:', error)
    ElMessage.error('提交评测失败')
  } finally {
    submittingEvaluation.value = false
  }
}

const downloadResults = async () => {
  if (!evaluationResults.value) return
  
  try {
    const response = await apiClient.get(`/llm/evaluation/results/${evaluationResults.value.evaluation_id}/download`)
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(response.data, null, 2)], {
      type: 'application/json'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `evaluation_results_${evaluationResults.value.evaluation_id}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('结果下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

const restart = () => {
  currentStep.value = 0
  selectedDatasetId.value = null
  selectedDatasetFromRoute.value = null
  modelConfig.name = ''
  modelConfig.version = ''
  modelConfig.affiliation = ''
  selectedFile.value = null
  evaluationResults.value = null
  llmAnswers.value = []
  evaluations.value = []
  uploadProgress.value = 0
}
</script>

<style scoped>
.llm-evaluation {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
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

.step-content {
  min-height: 400px;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.step-content h3 {
  margin-bottom: 20px;
  color: #303133;
}

.selected-dataset {
  margin-bottom: 20px;
}

.dataset-info h4 {
  margin-bottom: 10px;
  color: #303133;
}

.dataset-stats {
  display: flex;
  gap: 20px;
  color: #909399;
  font-size: 14px;
}

.step-actions {
  margin-top: 30px;
  text-align: center;
}

.step-actions .el-button {
  margin: 0 10px;
}

.upload-progress {
  margin: 20px 0;
}

.results-summary {
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
}

.answers-list {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.question-cell {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-text {
  margin: 0;
  line-height: 1.4;
}

.answer-cell {
  max-height: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.evaluation-detail {
  padding: 20px;
}

.answer-info h4 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #303133;
}

.answer-info h4:first-child {
  margin-top: 0;
}

.evaluations {
  margin-top: 30px;
}

.evaluation-item {
  margin-bottom: 15px;
}

.eval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.score {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.feedback, .criteria {
  margin-top: 10px;
}

.manual-evaluation {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
</style>

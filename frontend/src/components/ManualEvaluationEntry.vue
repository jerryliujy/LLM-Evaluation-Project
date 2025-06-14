<template>
  <div class="manual-evaluation-entry">
    <!-- 页面头部 -->
    <div class="dashboard-header">
      <div class="header-info">
        <h1>📝 手动评测录入</h1>
        <p>直接录入LLM回答和评测结果，支持批量导入</p>
        <div v-if="currentDataset" class="dataset-info">
          <span class="dataset-badge">📊 数据集: {{ currentDataset.name }}</span>
          <span v-if="currentDataset.description" class="dataset-description">{{ currentDataset.description }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="$emit('switch-mode', 'auto')">
          🤖 切换到自动评测
        </button>
        <button class="btn btn-primary" @click="showImportDialog = true">
          📁 批量导入
        </button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-grid">
      <div class="stat-card">
        <h3>总问题数</h3>
        <div class="stat-number">{{ questions.length }}</div>
        <p>个标准问题</p>
      </div>
      <div class="stat-card">
        <h3>已录入</h3>
        <div class="stat-number">{{ completedCount }}</div>
        <p>条评测结果</p>
      </div>
      <div class="stat-card">
        <h3>待录入</h3>
        <div class="stat-number">{{ pendingCount }}</div>
        <p>条评测结果</p>
      </div>
      <div class="stat-card">
        <h3>完成度</h3>
        <div class="stat-number">{{ completionRate }}%</div>
        <p>录入进度</p>
      </div>
    </div>

    <!-- 任务基本信息 -->
    <div class="basic-info-section">
      <div class="content-card">
        <div class="card-header">
          <h3>📋 评测任务信息</h3>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">任务名称 <span class="required">*</span></label>
            <input 
              v-model="taskData.name" 
              type="text" 
              class="form-input"
              placeholder="请输入任务名称"
              required
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">选择模型 <span class="required">*</span></label>
            <select v-model="taskData.model_id" class="form-select" required>
              <option :value="null">请选择评测的模型</option>
              <option 
                v-for="model in availableModels" 
                :key="model.id" 
                :value="model.id"
              >
                {{ model.display_name }} ({{ model.provider }})
              </option>
            </select>
          </div>
          
          <div class="form-group description-group">
            <label class="form-label">任务描述</label>
            <textarea 
              v-model="taskData.description" 
              class="form-textarea"
              placeholder="请输入任务描述（可选）"
              rows="3"
            ></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- 高级配置选项 -->
    <div class="advanced-config-section">
      <div class="content-card">
        <div class="card-header">
          <h3>⚙️ 高级配置选项</h3>
          <button class="toggle-btn" @click="showAdvancedConfig = !showAdvancedConfig">
            {{ showAdvancedConfig ? '收起' : '展开' }}
          </button>
        </div>
        <div v-if="showAdvancedConfig" class="advanced-config-content">
          <div class="config-grid">
            <div class="form-group">
              <label class="form-label">系统提示词</label>
              <textarea 
                v-model="taskData.system_prompt" 
                class="form-textarea"
                placeholder="系统提示词（可选）"
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label">选择题系统提示词</label>
              <textarea 
                v-model="taskData.choice_system_prompt" 
                class="form-textarea"
                placeholder="选择题专用系统提示词（可选）"
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label">问答题系统提示词</label>
              <textarea 
                v-model="taskData.text_system_prompt" 
                class="form-textarea"
                placeholder="问答题专用系统提示词（可选）"
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label">选择题评估提示词</label>
              <textarea 
                v-model="taskData.choice_evaluation_prompt" 
                class="form-textarea"
                placeholder="选择题评估提示词（可选）"
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label">问答题评估提示词</label>
              <textarea 
                v-model="taskData.text_evaluation_prompt" 
                class="form-textarea"
                placeholder="问答题评估提示词（可选）"
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label">评估提示词</label>
              <textarea 
                v-model="taskData.evaluation_prompt" 
                class="form-textarea"
                placeholder="通用评估提示词（可选）"
                rows="3"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-label">温度参数</label>
              <input 
                v-model.number="taskData.temperature" 
                type="number" 
                min="0" 
                max="2" 
                step="0.1"
                class="form-input"
                placeholder="0.7"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">最大Token数</label>
              <input 
                v-model.number="taskData.max_tokens" 
                type="number" 
                min="1" 
                max="8000"
                class="form-input"
                placeholder="2000"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">Top-K采样</label>
              <input 
                v-model.number="taskData.top_k" 
                type="number" 
                min="1" 
                max="100"
                class="form-input"
                placeholder="50"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">启用推理模式</label>
              <div class="checkbox-group">
                <input 
                  v-model="taskData.enable_reasoning" 
                  type="checkbox" 
                  id="enable_reasoning"
                  class="form-checkbox"
                />
                <label for="enable_reasoning">启用推理模式</label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 提交任务区域 -->
    <div class="submit-task-section">
      <div class="content-card">
        <div class="card-header">
          <h3>🚀 提交评测任务</h3>
        </div>
        <div class="submit-content">
          <div class="submit-info">
            <div class="info-item">
              <span class="info-label">任务名称:</span>
              <span class="info-value">{{ taskData.name || '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">选择模型:</span>
              <span class="info-value">{{ getSelectedModelName() || '未选择' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">数据集:</span>
              <span class="info-value">{{ currentDataset?.name || '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">已完成评测:</span>
              <span class="info-value">{{ completedCount }} / {{ questions.length }} 条</span>
            </div>
          </div>
          
          <div class="submit-actions">
            <button 
              @click="createEvaluationTask"
              :disabled="!canCreateTask || creatingTask"
              class="btn btn-success btn-large"
            >
              <span v-if="creatingTask" class="loading-spinner"></span>
              {{ creatingTask ? '创建中...' : '🚀 创建评测任务' }}
            </button>
            <p class="submit-hint">
              创建任务后，所有已录入的评测数据将被保存到数据库中
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 问题列表 -->
    <div class="questions-section">
      <div class="section-header">
        <h2>📋 评测条目列表</h2>
        <div class="section-actions">
          <div class="filter-controls">
            <select v-model="questionFilter" @change="filterQuestions" class="form-select">
              <option value="all">全部问题</option>
              <option value="completed">已录入</option>
              <option value="pending">待录入</option>
            </select>
          </div>
          <button @click="loadQuestions" class="btn btn-secondary" :disabled="loading">
            <span v-if="loading" class="loading-spinner"></span>
            {{ loading ? '加载中...' : '🔄 刷新' }}
          </button>
          <button @click="saveAllEntries" class="btn btn-primary" :disabled="!hasChanges">
            💾 保存所有更改
          </button>
        </div>
      </div>
      
      <div v-if="loading" class="loading">加载问题中...</div>
      <div v-else-if="filteredQuestions.length === 0" class="empty-state">
        <div class="empty-icon">📝</div>
        <h3>{{ getEmptyMessage() }}</h3>
        <p>{{ getEmptyDescription() }}</p>
      </div>
      <div v-else class="questions-list">
        <div 
          v-for="question in filteredQuestions" 
          :key="question.id" 
          class="question-item"
          :class="{ completed: isQuestionCompleted(question.id) }"
        >
          <!-- 问题头部 -->
          <div class="question-header">
            <div class="question-info">
              <div class="question-title">
                <span class="question-number">#{{ question.id }}</span>
                <span class="question-type-badge" :class="question.question_type">
                  {{ question.question_type === 'choice' ? '选择题' : '文本题' }}
                </span>
              </div>
              <div class="completion-status">
                <span v-if="isQuestionCompleted(question.id)" class="status-badge completed">
                  ✓ 已录入
                </span>
                <span v-else class="status-badge pending">
                  ⏳ 待录入
                </span>
              </div>
            </div>
          </div>

          <!-- 问题内容 -->
          <div class="question-content">
            <div class="question-text">
              <label class="content-label">📋 问题内容</label>
              <div class="content-display">{{ question.body }}</div>
            </div>

            <!-- 标准答案显示 -->
            <div v-if="question.standard_answer" class="standard-answer-section">
              <div class="answer-display">
                <label class="content-label">📖 标准答案</label>
                <div class="content-display">{{ question.standard_answer }}</div>
              </div>
            </div>
          </div>

          <!-- 评测录入区域 -->
          <div class="evaluation-input-section">
            <div class="input-grid">
              <!-- LLM回答输入 -->
              <div class="input-group answer-input">
                <label class="input-label">🤖 LLM回答 <span class="required">*</span></label>
                <textarea 
                  v-model="getEvaluationData(question.id).answer"
                  @input="markAsChanged(question.id)"
                  class="input-textarea"
                  placeholder="请输入LLM的回答内容..."
                  rows="4"
                  required
                ></textarea>
              </div>
              
              <!-- 得分输入 -->
              <div class="input-group score-input">
                <label class="input-label">📊 得分 <span class="required">*</span></label>
                <input 
                  v-model.number="getEvaluationData(question.id).score"
                  @input="markAsChanged(question.id)"
                  type="number" 
                  min="0" 
                  max="100" 
                  step="0.1"
                  class="input-number"
                  placeholder="0-100"
                  required
                />
              </div>
              
              <!-- 评判理由输入 -->
              <div class="input-group reasoning-input">
                <label class="input-label">💭 评判理由</label>
                <textarea 
                  v-model="getEvaluationData(question.id).reasoning"
                  @input="markAsChanged(question.id)"
                  class="input-textarea"
                  placeholder="请输入评分理由和反馈..."
                  rows="3"
                ></textarea>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="question-actions">
              <button 
                @click="saveEvaluationData(question.id)"
                :disabled="!isQuestionChanged(question.id) || savingQuestions.has(question.id)"
                class="btn btn-primary btn-sm"
              >
                <span v-if="savingQuestions.has(question.id)" class="loading-spinner"></span>
                {{ savingQuestions.has(question.id) ? '保存中...' : '💾 保存' }}
              </button>
              <button 
                @click="clearEvaluationData(question.id)"
                :disabled="!hasEvaluationData(question.id)"
                class="btn btn-secondary btn-sm"
              >
                🗑️ 清空
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量导入对话框 -->
    <div v-if="showImportDialog" class="modal-overlay" @click="closeImportDialog">
      <div class="modal-content import-modal" @click.stop>
        <div class="modal-header">
          <h3>📁 批量导入评测数据</h3>
          <button class="modal-close" @click="closeImportDialog">&times;</button>
        </div>
        <div class="modal-body">
          <div class="import-step" v-if="importStep === 'select'">
            <div class="import-info">
              <p><strong>数据格式:</strong> JSON 格式的评测数据</p>
            </div>
            
            <div class="file-upload-area">
              <input
                type="file"
                id="importFile"
                accept=".json"
                @change="handleFileSelect"
                class="file-input"
              />
              <label for="importFile" class="file-upload-label">
                <div class="upload-icon">📁</div>
                <div class="upload-text">
                  <p>点击选择 JSON 文件</p>
                  <p class="upload-hint">支持 .json 格式</p>
                </div>
              </label>
            </div>
            
            <div class="data-format-help">
              <h5>数据格式示例：</h5>
              <pre class="format-example">{
  "metadata": {
    "name": "手动录入测试任务",
    "description": "手动录入的评测结果",
    "model_id": 1,
    "system_prompt": "你是一个专业的评测助手",
    "temperature": 0.7,
    "max_tokens": 2000,
    "enable_reasoning": false
  },
  "entries": [
    {
      "std_question_id": 1,
      "answer": "LLM回答内容...",
      "score": 85.5,
      "reasoning": "评分理由...",
      "prompt_used": "生成回答时使用的prompt",
      "generated_at": "2024-01-01T10:00:00Z",
      "evaluator_type": "manual",
      "evaluator_id": 1
    }
  ]
}</pre>
            </div>
          </div>

          <div class="import-step" v-if="importStep === 'preview'">
            <h4>数据预览</h4>
            <div class="preview-stats">
              <span class="stat-item">
                <strong>总记录数:</strong> {{ importData.length }}
              </span>
              <span class="stat-item">
                <strong>有效记录:</strong> {{ validImportRecords }}
              </span>
            </div>
            
            <div class="preview-data" v-if="previewData.length > 0">
              <div v-for="(item, index) in previewData" :key="index" class="preview-item">
                <div class="preview-header">
                  <span class="preview-id">问题ID: {{ item.std_question_id }}</span>
                  <span class="preview-status" :class="{ 
                    valid: isValidImportRecord(item),
                    invalid: !isValidImportRecord(item)
                  }">
                    {{ isValidImportRecord(item) ? '✓ 有效' : '✗ 无效' }}
                  </span>
                </div>
                <div class="preview-content">
                  <div class="preview-answer">{{ truncateText(item.answer || '无回答内容', 80) }}</div>
                  <div class="preview-score">得分: {{ item.score || 'N/A' }}</div>
                  <div class="preview-evaluator">评测者: {{ item.evaluator_type || 'manual' }}</div>
                </div>
              </div>
            </div>

            <div class="validation-errors" v-if="validationErrors.length > 0">
              <h5>验证错误：</h5>
              <ul>
                <li v-for="error in validationErrors" :key="error">{{ error }}</li>
              </ul>
            </div>
          </div>

          <div class="import-step" v-if="importStep === 'importing'">
            <div class="importing-status">
              <div class="loading-spinner"></div>
              <p>正在导入数据，请稍候...</p>
            </div>
          </div>

          <div class="import-step" v-if="importStep === 'result'">
            <div class="import-result">
              <div class="result-icon" :class="{ success: importSuccess, error: !importSuccess }">
                {{ importSuccess ? '✅' : '❌' }}
              </div>
              <h4>{{ importSuccess ? '导入成功' : '导入失败' }}</h4>
              <p v-if="importSuccess">
                成功导入 {{ importResult?.imported_count || 0 }} 条评测数据
              </p>
              <p v-else class="error-text">
                {{ importErrorMessage }}
              </p>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="closeImportDialog">
              {{ importStep === 'result' ? '关闭' : '取消' }}
            </button>
            <button 
              v-if="importStep === 'preview'" 
              type="button" 
              class="btn btn-primary" 
              @click="executeImport"
              :disabled="validImportRecords === 0"
            >
              导入 {{ validImportRecords }} 条数据
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { llmEvaluationService } from '@/services/llmEvaluationService'

export default {
  name: 'ManualEvaluationEntry',
  props: {
    mode: {
      type: String,
      default: 'manual'
    }
  },
  emits: ['switch-mode', 'task-created'],
  setup(props, { emit }) {
    const route = useRoute()
    
    // 数据状态
    const loading = ref(false)
    const questions = ref([])
    const evaluationData = ref(new Map()) // question_id -> { answer, score, reasoning }
    const changedQuestions = ref(new Set())
    const savingQuestions = ref(new Set())
    const availableModels = ref([])
    const currentDataset = ref(null)
    
    // 任务信息
    const taskData = ref({
      name: '',
      model_id: null,
      dataset_id: null, // 将从路由参数获取
      description: '',
      // 高级配置选项
      system_prompt: '',
      choice_system_prompt: '',
      text_system_prompt: '',
      choice_evaluation_prompt: '',
      text_evaluation_prompt: '',
      evaluation_prompt: '',
      temperature: 0.7,
      max_tokens: 2000,
      top_k: 50,
      enable_reasoning: false
    })
    
    // 筛选和显示
    const questionFilter = ref('all')
    const filteredQuestions = ref([])
    const showAdvancedConfig = ref(false)
    
    // 导入功能
    const showImportDialog = ref(false)
    const importStep = ref('select')
    const importData = ref([])
    const importMetadata = ref(null)
    const previewData = ref([])
    const validationErrors = ref([])
    const importSuccess = ref(false)
    const importResult = ref(null)
    const importErrorMessage = ref('')
    
    // 任务创建状态
    const creatingTask = ref(false)
    
    // 计算属性
    const completedCount = computed(() => {
      return questions.value.filter(q => isQuestionCompleted(q.id)).length
    })
    
    const pendingCount = computed(() => {
      return questions.value.length - completedCount.value
    })
    
    const completionRate = computed(() => {
      if (questions.value.length === 0) return 0
      return Math.round((completedCount.value / questions.value.length) * 100)
    })
    
    const hasChanges = computed(() => {
      return changedQuestions.value.size > 0
    })
    
    const validImportRecords = computed(() => {
      return importData.value.filter(item => isValidImportRecord(item)).length
    })
    
    const canCreateTask = computed(() => {
      return taskData.value.name && 
             taskData.value.model_id && 
             taskData.value.dataset_id && 
             completedCount.value > 0
    })
    
    // 方法
    const loadQuestions = async () => {
      if (!taskData.value.dataset_id) {
        console.warn('数据集ID未设置，无法加载问题')
        return
      }
      
      console.log('开始加载数据集问题，数据集ID:', taskData.value.dataset_id)
      loading.value = true
      try {
        const response = await llmEvaluationService.getDatasetQuestions(taskData.value.dataset_id)
        questions.value = response.questions || []
        console.log('成功加载问题数量:', questions.value.length)
        filterQuestions()
      } catch (error) {
        console.error('加载问题失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    const loadAvailableModels = async () => {
      try {
        const models = await llmEvaluationService.getAvailableModels()
        availableModels.value = models
      } catch (error) {
        console.error('加载模型失败:', error)
      }
    }
    
    const loadCurrentDataset = async () => {
      if (!taskData.value.dataset_id) return
      
      try {
        const response = await llmEvaluationService.getMarketplaceDatasets({ all_datasets: true })
        const dataset = response.find(d => d.id === taskData.value.dataset_id)
        if (dataset) {
          currentDataset.value = dataset
        }
      } catch (error) {
        console.error('加载数据集信息失败:', error)
      }
    }
    
    const filterQuestions = () => {
      switch (questionFilter.value) {
        case 'completed':
          filteredQuestions.value = questions.value.filter(q => isQuestionCompleted(q.id))
          break
        case 'pending':
          filteredQuestions.value = questions.value.filter(q => !isQuestionCompleted(q.id))
          break
        default:
          filteredQuestions.value = questions.value
      }
    }
    
    const isQuestionCompleted = (questionId) => {
      const data = evaluationData.value.get(questionId)
      return data && data.answer && data.score !== null && data.score !== undefined
    }
    
    const isQuestionChanged = (questionId) => {
      return changedQuestions.value.has(questionId)
    }
    
    const hasEvaluationData = (questionId) => {
      const data = evaluationData.value.get(questionId)
      return data && (data.answer || data.score !== null || data.reasoning)
    }
    
    const getEvaluationData = (questionId) => {
      if (!evaluationData.value.has(questionId)) {
        evaluationData.value.set(questionId, {
          answer: '',
          score: null,
          reasoning: ''
        })
      }
      return evaluationData.value.get(questionId)
    }
    
    const markAsChanged = (questionId) => {
      changedQuestions.value.add(questionId)
    }
    
    const saveEvaluationData = async (questionId) => {
      savingQuestions.value.add(questionId)
      try {
        const data = evaluationData.value.get(questionId)
        console.log('保存评测数据:', { questionId, data })
        
        // 模拟API延迟
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        changedQuestions.value.delete(questionId)
      } catch (error) {
        console.error('保存失败:', error)
      } finally {
        savingQuestions.value.delete(questionId)
      }
    }
    
    const clearEvaluationData = (questionId) => {
      evaluationData.value.set(questionId, {
        answer: '',
        score: null,
        reasoning: ''
      })
      changedQuestions.value.delete(questionId)
    }
    
    const saveAllEntries = async () => {
      const changedIds = Array.from(changedQuestions.value)
      for (const questionId of changedIds) {
        await saveEvaluationData(questionId)
      }
    }
    
    const getEmptyMessage = () => {
      switch (questionFilter.value) {
        case 'completed':
          return '还没有已录入的评测数据'
        case 'pending':
          return '所有问题都已录入完成'
        default:
          return '暂无问题数据'
      }
    }
    
    const getEmptyDescription = () => {
      switch (questionFilter.value) {
        case 'completed':
          return '开始录入评测数据后，已完成的条目将在这里显示'
        case 'pending':
          return '恭喜！您已经完成了所有问题的评测录入'
        default:
          return '请先选择数据集并加载问题数据'
      }
    }
    
    // 导入功能方法
    const closeImportDialog = () => {
      showImportDialog.value = false
      importStep.value = 'select'
      importData.value = []
      previewData.value = []
      validationErrors.value = []
    }
    
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (!file) return
      
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result)
          
          // 检查数据格式
          if (data.metadata && data.entries) {
            // 新格式：包含元信息和条目列表
            importData.value = data.entries
            importMetadata.value = data.metadata
          } else if (Array.isArray(data)) {
            // 旧格式：直接是条目数组
            importData.value = data
            importMetadata.value = null
          } else {
            throw new Error('数据格式不正确')
          }
          
          previewImportData()
        } catch (error) {
          alert('文件格式错误，请选择有效的JSON文件')
        }
      }
      reader.readAsText(file)
    }
    
    const previewImportData = () => {
      validationErrors.value = []
      previewData.value = importData.value.slice(0, 10) // 只预览前10条
      
      // 验证数据
      importData.value.forEach((item, index) => {
        if (!isValidImportRecord(item)) {
          validationErrors.value.push(`第${index + 1}条记录格式错误`)
        }
      })
      
      importStep.value = 'preview'
    }
    
    const isValidImportRecord = (item) => {
      return item && 
             typeof item.std_question_id === 'number' && 
             typeof item.answer === 'string' && item.answer.trim() &&
             typeof item.score === 'number' && item.score >= 0 && item.score <= 100
    }
    
    const executeImport = async () => {
      importStep.value = 'importing'
      try {
        const validRecords = importData.value.filter(item => isValidImportRecord(item))
        
        // 如果有元信息，更新任务数据
        if (importMetadata.value) {
          Object.assign(taskData.value, importMetadata.value)
        }
        
        // 批量导入数据到本地状态
        validRecords.forEach(item => {
          evaluationData.value.set(item.std_question_id, {
            answer: item.answer,
            score: item.score,
            reasoning: item.reasoning || '',
            // 保存额外信息
            prompt_used: item.prompt_used || '',
            generated_at: item.generated_at || '',
            evaluator_type: item.evaluator_type || 'manual',
            evaluator_id: item.evaluator_id || null
          })
          changedQuestions.value.add(item.std_question_id)
        })
        
        importSuccess.value = true
        importResult.value = { imported_count: validRecords.length }
        importStep.value = 'result'
        
        // 更新筛选结果
        filterQuestions()
      } catch (error) {
        importSuccess.value = false
        importErrorMessage.value = error.message
        importStep.value = 'result'
      }
    }
    
    const truncateText = (text, maxLength) => {
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }
    
    // 任务创建方法
    const getSelectedModelName = () => {
      const model = availableModels.value.find(m => m.id === taskData.value.model_id)
      return model ? `${model.display_name} (${model.provider})` : null
    }
    
    const createEvaluationTask = async () => {
      if (!canCreateTask.value) {
        alert('请完善任务信息并至少录入一条评测数据')
        return
      }
      
      creatingTask.value = true
      try {
        // 收集所有已完成的评测数据
        const entries = []
        for (const [questionId, data] of evaluationData.value.entries()) {
          if (data.answer && data.score !== null && data.score !== undefined) {
            entries.push({
              question_id: questionId,
              answer: data.answer,
              score: data.score,
              reasoning: data.reasoning || '手动录入评测'
            })
          }
        }
        
        if (entries.length === 0) {
          throw new Error('没有可提交的评测数据')
        }
        
        // 准备任务数据
        const taskPayload = {
          name: taskData.value.name,
          description: taskData.value.description || '手动录入的评测任务',
          dataset_id: taskData.value.dataset_id,
          model_id: taskData.value.model_id,
          entries: entries,
          // 高级配置
          system_prompt: taskData.value.system_prompt,
          choice_system_prompt: taskData.value.choice_system_prompt,
          text_system_prompt: taskData.value.text_system_prompt,
          choice_evaluation_prompt: taskData.value.choice_evaluation_prompt,
          text_evaluation_prompt: taskData.value.text_evaluation_prompt,
          evaluation_prompt: taskData.value.evaluation_prompt,
          temperature: taskData.value.temperature,
          max_tokens: taskData.value.max_tokens,
          top_k: taskData.value.top_k,
          enable_reasoning: taskData.value.enable_reasoning
        }
        
        console.log('提交任务数据:', taskPayload)
        
        // 调用API创建任务
        const result = await llmEvaluationService.createManualEvaluationTask(taskPayload)
        
        console.log('任务创建成功:', result)
        
        // 显示成功消息
        alert(`评测任务创建成功！\n任务ID: ${result.id}\n任务名称: ${result.name}\n已提交 ${entries.length} 条评测数据`)
        
        // 触发事件通知父组件
        emit('task-created', result)
        
        // 清空已提交的数据
        evaluationData.value.clear()
        changedQuestions.value.clear()
        
      } catch (error) {
        console.error('创建任务失败:', error)
        alert(`创建任务失败: ${error.message}`)
      } finally {
        creatingTask.value = false
      }
    }
    
    // 生命周期
    onMounted(async () => {
      // 从路由参数获取数据集ID
      if (route.params.datasetId) {
        taskData.value.dataset_id = parseInt(String(route.params.datasetId))
        console.log('从路由参数获取数据集ID:', taskData.value.dataset_id)
      }
      
      // 并行加载模型、数据集信息和问题
      await Promise.all([
        loadAvailableModels(),
        taskData.value.dataset_id ? loadCurrentDataset() : Promise.resolve(),
        taskData.value.dataset_id ? loadQuestions() : Promise.resolve()
      ])
    })
    
    return {
      // 数据
      loading,
      questions,
      filteredQuestions,
      evaluationData,
      changedQuestions,
      savingQuestions,
      availableModels,
      taskData,
      questionFilter,
      showAdvancedConfig,
      currentDataset,
      creatingTask,
      
      // 导入
      showImportDialog,
      importStep,
      importData,
      importMetadata,
      previewData,
      validationErrors,
      importSuccess,
      importResult,
      importErrorMessage,
      
      // 计算属性
      completedCount,
      pendingCount,
      completionRate,
      hasChanges,
      validImportRecords,
      canCreateTask,
      
      // 方法
      loadQuestions,
      loadAvailableModels,
      loadCurrentDataset,
      filterQuestions,
      isQuestionCompleted,
      isQuestionChanged,
      hasEvaluationData,
      getEvaluationData,
      markAsChanged,
      saveEvaluationData,
      clearEvaluationData,
      saveAllEntries,
      getEmptyMessage,
      getEmptyDescription,
      
      // 导入方法
      closeImportDialog,
      handleFileSelect,
      previewImportData,
      isValidImportRecord,
      executeImport,
      truncateText,
      
      // 任务创建方法
      getSelectedModelName,
      createEvaluationTask
    }
  }
}
</script>

<style scoped>
/* 全局样式 */
.manual-evaluation-entry {
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

/* 页面头部 */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-info h1 {
  margin: 0 0 8px 0;
  color: #2d3748;
  font-size: 28px;
  font-weight: 600;
}

.header-info p {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
}

.dataset-info {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dataset-badge {
  display: inline-block;
  background: #dbeafe;
  color: #1e40af;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
}

.dataset-description {
  color: #6b7280;
  font-size: 14px;
  font-style: italic;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-card h3 {
  margin: 0 0 8px 0;
  color: #4a5568;
  font-size: 14px;
  font-weight: 500;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
  margin: 8px 0;
}

.stat-card p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

/* 基本信息区域 */
.basic-info-section {
  margin-bottom: 24px;
}

.content-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.card-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 18px;
  font-weight: 600;
}

.form-grid {
  padding: 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group.description-group {
  grid-column: 1 / -1;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-weight: 500;
  font-size: 14px;
}

.required {
  color: #ef4444;
}

.form-input, .form-select, .form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
  box-sizing: border-box;
  margin-bottom: 16px;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

/* 问题列表区域 */
.questions-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.section-header h2 {
  margin: 0;
  color: #2d3748;
  font-size: 20px;
  font-weight: 600;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-controls .form-select {
  width: auto;
  min-width: 120px;
}

/* 问题条目 */
.questions-list {
  padding: 0;
}

.question-item {
  border-bottom: 1px solid #e2e8f0;
  padding: 24px;
  transition: background-color 0.2s;
}

.question-item:last-child {
  border-bottom: none;
}

.question-item.completed {
  background: linear-gradient(135deg, #f0fff4 0%, #ecfdf5 100%);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.question-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.question-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.question-number {
  font-weight: 600;
  color: #4f46e5;
  font-size: 16px;
}

.question-type-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.question-type-badge.choice {
  background: #dbeafe;
  color: #1e40af;
}

.question-type-badge.text {
  background: #f3e8ff;
  color: #7c3aed;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.completed {
  background: #dcfce7;
  color: #166534;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

/* 问题内容 */
.question-content {
  margin-bottom: 20px;
}

.content-label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-weight: 600;
  font-size: 14px;
}

.content-display {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  color: #374151;
  line-height: 1.6;
  margin-bottom: 16px;
  white-space: pre-wrap;
}

.standard-answer-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.scoring-points-list {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.scoring-point-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
}

.scoring-point-item:last-child {
  border-bottom: none;
}

.point-score {
  background: #3b82f6;
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  min-width: 50px;
  text-align: center;
}

.point-description {
  color: #374151;
  font-size: 14px;
}

/* 评测录入区域 */
.evaluation-input-section {
  background: #fefefe;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
}

.input-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 16px;
}

.reasoning-input {
  grid-column: 1 / -1;
}

.input-label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-weight: 500;
  font-size: 14px;
}

.input-textarea, .input-number {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.input-textarea:focus, .input-number:focus {
  outline: none;
  border-color: #3b82f6;
}

.input-textarea {
  resize: vertical;
  min-height: 100px;
}

.input-group {
  margin-bottom: 16px;
}

.question-actions {
  display: flex;
  gap: 8px;
}

/* 按钮样式 */
.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #4b5563;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* 加载和空状态 */
.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  color: #374151;
}

.empty-state p {
  margin: 0;
  color: #6b7280;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  color: #374151;
  font-size: 18px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.modal-close:hover {
  background: #f3f4f6;
}

.modal-body {
  padding: 24px;
}

/* 导入功能样式 */
.import-info {
  margin-bottom: 20px;
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
}

.file-upload-area {
  margin-bottom: 20px;
}

.file-input {
  display: none;
}

.file-upload-label {
  display: block;
  padding: 40px 20px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.file-upload-label:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.upload-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.upload-text p {
  margin: 4px 0;
}

.upload-hint {
  font-size: 12px;
  color: #6b7280;
}

.data-format-help {
  margin-top: 20px;
}

.format-example {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 16px;
  font-size: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.preview-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-item {
  color: #374151;
  font-size: 14px;
}

.preview-data {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.preview-item {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.preview-id {
  font-weight: 500;
  color: #374151;
}

.preview-status.valid {
  color: #059669;
  font-size: 12px;
}

.preview-status.invalid {
  color: #dc2626;
  font-size: 12px;
}

.preview-content {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.preview-answer {
  flex: 1;
  color: #6b7280;
  font-size: 13px;
}

.preview-score {
  color: #374151;
  font-size: 13px;
  font-weight: 500;
}

.preview-evaluator {
  color: #6b7280;
  font-size: 12px;
}

.validation-errors {
  margin-top: 16px;
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.validation-errors h5 {
  margin: 0 0 8px 0;
  color: #dc2626;
}

.validation-errors ul {
  margin: 0;
  padding-left: 20px;
  color: #dc2626;
  font-size: 14px;
}

.importing-status {
  text-align: center;
  padding: 40px;
}

.import-result {
  text-align: center;
  padding: 40px;
}

.result-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.result-icon.success {
  color: #059669;
}

.result-icon.error {
  color: #dc2626;
}

.error-text {
  color: #dc2626;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .standard-answer-section {
    grid-template-columns: 1fr;
  }
  
  .input-grid {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .section-actions {
    width: 100%;
    justify-content: space-between;
  }
}

/* 高级配置选项样式 */
.advanced-config-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.toggle-btn {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: #e5e7eb;
}

.advanced-config-content {
  padding: 24px;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.config-grid .form-group {
  margin-bottom: 20px;
}

.config-grid .form-input,
.config-grid .form-textarea {
  margin-bottom: 0;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.form-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
}

.checkbox-group label {
  margin: 0;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
}

/* 成功按钮样式 */
.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
}

/* 标准答案显示样式 */
.standard-answer-section {
  margin-top: 16px;
}

.answer-display {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 16px;
}

.answer-display .content-display {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  margin-top: 8px;
  color: #374151;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 提交任务区域 */
.submit-task-section {
  margin-bottom: 24px;
}

.submit-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.submit-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  font-weight: 500;
  color: #374151;
}

.info-value {
  font-weight: 600;
  color: #4b5563;
}

.submit-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.submit-hint {
  color: #6b7280;
  font-size: 12px;
}
</style>

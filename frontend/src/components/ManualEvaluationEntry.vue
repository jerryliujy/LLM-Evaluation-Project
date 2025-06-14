<template>
  <div class="manual-evaluation-entry">
    <!-- 模式选择 -->
    <div class="mode-selector">
      <div class="card-header">
        <h3>📝 手动录入评测结果</h3>
        <p>直接录入您已经完成的LLM评测结果，无需经过自动评测流程</p>
      </div>
      
      <div class="mode-tabs">
        <button 
          :class="['tab-btn', { active: mode === 'auto' }]"
          @click="$emit('switch-mode', 'auto')"
        >
          🤖 自动评测
        </button>
        <button 
          :class="['tab-btn', { active: mode === 'manual' }]"
          @click="$emit('switch-mode', 'manual')"
        >
          📝 手动录入
        </button>
      </div>
    </div>

    <!-- 手动录入表单 -->
    <div v-if="mode === 'manual'" class="manual-form">
      <!-- 基本信息 -->
      <div class="basic-info-section">
        <h4>基本信息</h4>
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
            <label class="form-label">任务描述</label>
            <textarea 
              v-model="taskData.description" 
              class="form-textarea"
              placeholder="请输入任务描述（可选）"
              rows="3"
            ></textarea>
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
        </div>
      </div>

      <!-- 问题列表 -->
      <div class="questions-section">
        <div class="section-header">
          <h4>评测条目录入</h4>
          <div class="section-actions">
            <button @click="loadQuestions" class="btn btn-secondary" :disabled="loading">
              {{ loading ? '加载中...' : '🔄 刷新问题列表' }}
            </button>
            <button @click="addAllQuestions" class="btn btn-primary" :disabled="!questions.length">
              ➕ 添加所有问题
            </button>
          </div>
        </div>
        
        <!-- 问题列表展示 -->
        <div v-if="questions.length" class="questions-list">
          <div class="questions-header">
            <span>数据集包含 {{ questions.length }} 个问题</span>
            <span class="entries-count">已录入 {{ taskData.entries.length }} 条</span>
          </div>
          
          <div class="questions-grid">
            <div 
              v-for="question in questions" 
              :key="question.id"
              class="question-card"
              :class="{ 'added': isQuestionAdded(question.id) }"
            >
              <div class="question-content">
                <div class="question-text">{{ question.body.substring(0, 100) }}...</div>
                <div class="question-meta">
                  <span class="question-type">{{ question.question_type }}</span>
                  <span class="question-id">#{{ question.id }}</span>
                </div>
              </div>
              <button 
                @click="addQuestion(question)"
                :disabled="isQuestionAdded(question.id)"
                class="btn btn-sm"
                :class="isQuestionAdded(question.id) ? 'btn-success' : 'btn-primary'"
              >
                {{ isQuestionAdded(question.id) ? '✓ 已添加' : '+ 添加' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 评测条目编辑 -->
      <div v-if="taskData.entries.length" class="entries-section">
        <h4>评测条目编辑</h4>
        <div class="entries-list">
          <div 
            v-for="(entry, index) in taskData.entries" 
            :key="entry.question_id"
            class="entry-card"
          >
            <div class="entry-header">
              <div class="entry-info">
                <span class="entry-title">问题 #{{ entry.question_id }}</span>
                <button @click="removeEntry(index)" class="btn-remove">✕</button>
              </div>
            </div>
            
            <div class="entry-content">
              <div class="question-display">
                <label class="form-label">问题内容</label>
                <div class="question-text">{{ getQuestionText(entry.question_id) }}</div>
              </div>
              
              <div class="form-group">
                <label class="form-label">LLM回答 <span class="required">*</span></label>
                <textarea 
                  v-model="entry.answer" 
                  class="form-textarea"
                  placeholder="请输入LLM的回答内容"
                  rows="4"
                  required
                ></textarea>
              </div>
              
              <div class="score-feedback-grid">
                <div class="form-group">
                  <label class="form-label">得分 <span class="required">*</span></label>
                  <input 
                    v-model.number="entry.score" 
                    type="number" 
                    min="0" 
                    max="100" 
                    step="0.1"
                    class="form-input"
                    placeholder="0-100"
                    required
                  />
                </div>
                
                <div class="form-group">
                  <label class="form-label">评分理由</label>
                  <textarea 
                    v-model="entry.reasoning" 
                    class="form-textarea"
                    placeholder="请输入评分理由（可选）"
                    rows="3"
                  ></textarea>
                </div>
                
                <div class="form-group">
                  <label class="form-label">反馈意见</label>
                  <textarea 
                    v-model="entry.feedback" 
                    class="form-textarea"
                    placeholder="请输入反馈意见（可选）"
                    rows="3"
                  ></textarea>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 提交按钮 -->
      <div class="submit-section">
        <div class="submit-summary">
          <div class="summary-stats">
            <span class="stat-item">
              <strong>{{ taskData.entries.length }}</strong> 条评测条目
            </span>
            <span v-if="averageScore !== null" class="stat-item">
              平均分: <strong>{{ averageScore.toFixed(1) }}</strong>
            </span>
          </div>
        </div>
        
        <div class="submit-actions">
          <button 
            @click="submitTask" 
            :disabled="!canSubmit || submitting"
            class="btn btn-primary btn-large"
          >
            {{ submitting ? '提交中...' : '🚀 提交评测任务' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

export default {
  name: 'ManualEvaluationEntry',
  props: {
    mode: {
      type: String,
      required: true
    },
    currentDataset: {
      type: Object,
      required: true
    },
    availableModels: {
      type: Array,
      default: () => []
    }
  },
  emits: ['switch-mode', 'task-created'],
  setup(props, { emit }) {
    const route = useRoute()
    
    // 状态数据
    const loading = ref(false)
    const submitting = ref(false)
    const questions = ref([])
    
    // 任务数据
    const taskData = ref({
      name: '',
      description: '',
      dataset_id: props.currentDataset?.id || null,
      model_id: null,
      entries: []
    })

    // 计算属性
    const averageScore = computed(() => {
      if (taskData.value.entries.length === 0) return null
      const total = taskData.value.entries.reduce((sum, entry) => sum + (entry.score || 0), 0)
      return total / taskData.value.entries.length
    })

    const canSubmit = computed(() => {
      return taskData.value.name.trim() &&
             taskData.value.dataset_id &&
             taskData.value.model_id &&
             taskData.value.entries.length > 0 &&
             taskData.value.entries.every(entry => 
               entry.answer.trim() && 
               entry.score !== null && 
               entry.score !== undefined &&
               entry.score >= 0 && 
               entry.score <= 100
             )
    })

    // 方法
    const loadQuestions = async () => {
      if (!props.currentDataset?.id) return
      
      loading.value = true
      try {
        const response = await api.get(`/api/llm-evaluation/datasets/${props.currentDataset.id}/questions`)
        questions.value = response.data.questions || []
      } catch (error) {
        console.error('Failed to load questions:', error)
        // 可以添加错误提示
      } finally {
        loading.value = false
      }
    }

    const isQuestionAdded = (questionId) => {
      return taskData.value.entries.some(entry => entry.question_id === questionId)
    }

    const addQuestion = (question) => {
      if (isQuestionAdded(question.id)) return
      
      taskData.value.entries.push({
        question_id: question.id,
        answer: '',
        score: null,
        reasoning: '',
        feedback: ''
      })
    }

    const addAllQuestions = () => {
      questions.value.forEach(question => {
        if (!isQuestionAdded(question.id)) {
          addQuestion(question)
        }
      })
    }

    const removeEntry = (index) => {
      taskData.value.entries.splice(index, 1)
    }

    const getQuestionText = (questionId) => {
      const question = questions.value.find(q => q.id === questionId)
      return question ? question.body : `问题 #${questionId}`
    }

    const submitTask = async () => {
      if (!canSubmit.value) return
      
      submitting.value = true
      try {
        const response = await api.post('/api/llm-evaluation/tasks/manual', taskData.value)
        
        // 通知父组件任务创建成功
        emit('task-created', response.data)
        
        // 可以添加成功提示
        console.log('Manual evaluation task created successfully:', response.data)
        
      } catch (error) {
        console.error('Failed to create manual evaluation task:', error)
        // 可以添加错误提示
      } finally {
        submitting.value = false
      }
    }

    // 生命周期
    onMounted(() => {
      // 设置数据集ID
      if (props.currentDataset?.id) {
        taskData.value.dataset_id = props.currentDataset.id
        loadQuestions()
      }
      
      // 设置默认任务名称
      if (props.currentDataset?.name) {
        taskData.value.name = `${props.currentDataset.name} - 手动评测`
      }
    })

    return {
      loading,
      submitting,
      questions,
      taskData,
      averageScore,
      canSubmit,
      loadQuestions,
      isQuestionAdded,
      addQuestion,
      addAllQuestions,
      removeEntry,
      getQuestionText,
      submitTask
    }
  }
}
</script>

<style scoped>
.manual-evaluation-entry {
  max-width: 1200px;
  margin: 0 auto;
}

.mode-selector {
  margin-bottom: 2rem;
}

.card-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.card-header h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.card-header p {
  color: #7f8c8d;
  font-size: 1rem;
}

.mode-tabs {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #e9ecef;
  background: white;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  border-color: #007bff;
  background: #f8f9fa;
}

.tab-btn.active {
  border-color: #007bff;
  background: #007bff;
  color: white;
}

.manual-form {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.basic-info-section,
.questions-section,
.entries-section {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.basic-info-section h4,
.questions-section h4,
.entries-section h4 {
  font-size: 1.25rem;
  color: #2c3e50;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group:nth-child(2) {
  grid-column: 1 / -1;
}

.form-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
}

.required {
  color: #dc3545;
}

.form-input,
.form-select,
.form-textarea {
  padding: 0.75rem;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.section-header {
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
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

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.questions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.entries-count {
  font-weight: 600;
  color: #007bff;
}

.questions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.question-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.question-card:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
}

.question-card.added {
  border-color: #28a745;
  background: #f8fff9;
}

.question-content {
  flex: 1;
  margin-right: 1rem;
}

.question-text {
  font-size: 0.9rem;
  color: #495057;
  margin-bottom: 0.5rem;
}

.question-meta {
  display: flex;
  gap: 0.5rem;
}

.question-type,
.question-id {
  font-size: 0.8rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  background: #e9ecef;
  color: #6c757d;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.8rem;
}

.entries-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.entry-card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.entry-header {
  background: #f8f9fa;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #dee2e6;
}

.entry-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.entry-title {
  font-weight: 600;
  color: #495057;
}

.btn-remove {
  background: none;
  border: none;
  color: #dc3545;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.3s ease;
}

.btn-remove:hover {
  background: #f5c6cb;
}

.entry-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.question-display .question-text {
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #495057;
}

.score-feedback-grid {
  display: grid;
  grid-template-columns: 200px 1fr 1fr;
  gap: 1rem;
}

.submit-section {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.submit-summary {
  margin-bottom: 1rem;
}

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 2rem;
}

.stat-item {
  font-size: 1rem;
  color: #495057;
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .questions-grid {
    grid-template-columns: 1fr;
  }
  
  .score-feedback-grid {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .summary-stats {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>

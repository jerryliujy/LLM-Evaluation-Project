<template>
  <div class="manual-evaluation-interface">
    <!-- 头部信息 -->
    <div class="evaluation-header">
      <div class="header-info">
        <h2>👤 手动评测界面</h2>
        <p>请对每个LLM生成的答案进行人工评分和评价</p>
        <div class="task-info">
          <span class="task-name">任务: {{ taskName }}</span>
          <span class="task-status" :class="taskStatus">{{ getStatusText(taskStatus) }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button @click="downloadAnswers" class="btn btn-secondary">
          📥 下载LLM回答
        </button>
        <button @click="showImportDialog = true" class="btn btn-info">
          📁 导入评测结果
        </button>
        <button @click="exitEvaluation" class="btn btn-outline">
          ← 退出评测
        </button>
      </div>
    </div>

    <!-- 进度信息 -->
    <div class="evaluation-progress">
      <div class="progress-header">
        <div class="progress-info">
          <span class="current-index">第 {{ currentIndex + 1 }} 题</span>
          <span class="total-count">共 {{ answers.length }} 题</span>
        </div>
        <div class="progress-percentage">
          {{ answers.length ? Math.round(((currentIndex + 1) / answers.length) * 100) : 0 }}%
        </div>
      </div>
      <div class="progress-bar">
        <div 
          class="progress-fill"
          :style="{ width: answers.length ? ((currentIndex + 1) / answers.length) * 100 + '%' : '0%' }"
        ></div>
      </div>
      <div class="progress-stats">
        <span class="stat-item">已评测: {{ evaluatedCount }}</span>
        <span class="stat-item">待评测: {{ pendingCount }}</span>
        <span class="stat-item">平均分: {{ averageScore.toFixed(1) }}</span>
      </div>
    </div>

    <!-- 评测内容 -->
    <div v-if="currentAnswer" class="evaluation-content">
      <div class="content-grid">
        <!-- 左侧：问题和标准答案 -->
        <div class="left-panel">
          <!-- 标准问题 -->
          <div class="question-section">
            <h3>📝 标准问题</h3>
            <div class="question-content">
              <div class="question-body">{{ currentAnswer.question.body }}</div>
              <div class="question-meta">
                <span class="question-type">{{ currentAnswer.question.question_type }}</span>
                <div class="question-tags">
                  <span v-for="tag in currentAnswer.question.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 标准答案 -->
          <div class="standard-answers-section">
            <h3>✅ 标准答案</h3>
            <div v-for="stdAnswer in currentAnswer.std_answers" :key="stdAnswer.id" class="std-answer-item">
              <div class="std-answer-content">
                <div class="answer-text">{{ stdAnswer.answer }}</div>
                <div class="answer-meta">
                  <span class="answered-by">回答者: {{ stdAnswer.answered_by }}</span>
                </div>
              </div>
              
              <!-- 得分点 -->
              <div v-if="stdAnswer.scoring_points && stdAnswer.scoring_points.length > 0" class="scoring-points">
                <h4>得分点:</h4>
                <div v-for="point in stdAnswer.scoring_points" :key="point.id" class="scoring-point">
                  <span class="point-order">{{ point.point_order }}.</span>
                  <span class="point-answer">{{ point.answer }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：LLM回答和评测 -->
        <div class="right-panel">
          <!-- LLM回答 -->
          <div class="llm-answer-section">
            <h3>🤖 LLM回答</h3>
            <div class="llm-answer-content">
              <div class="answer-text">{{ currentAnswer.llm_answer }}</div>
              <div class="answer-meta">
                <span class="answered-at">回答时间: {{ formatDateTime(currentAnswer.answered_at) }}</span>
                <span class="is-valid" :class="{ valid: currentAnswer.is_valid, invalid: !currentAnswer.is_valid }">
                  {{ currentAnswer.is_valid ? '有效' : '无效' }}
                </span>
              </div>
            </div>
          </div>

          <!-- 手动评测 -->
          <div class="manual-evaluation-section">
            <h3>📊 手动评测</h3>
            
            <!-- 评分 -->
            <div class="score-input">
              <label class="score-label">
                评分: <span class="score-value">{{ currentAnswer.manual_score || 0 }}</span>
              </label>
              <input 
                v-model.number="currentAnswer.manual_score" 
                type="range" 
                min="0" 
                max="100"
                step="0.5"
                class="score-slider"
                @input="markAsChanged"
              />
              <div class="score-range">
                <span>0</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>

            <!-- 评测理由 -->
            <div class="reasoning-input">
              <label class="reasoning-label">评测理由</label>
              <textarea 
                v-model="currentAnswer.manual_reasoning" 
                rows="4"
                class="reasoning-textarea"
                placeholder="请输入详细的评分理由和反馈..."
                @input="markAsChanged"
              ></textarea>
            </div>

            <!-- 评测状态 -->
            <div class="evaluation-status">
              <div v-if="currentAnswer.is_evaluated" class="status-evaluated">
                <span class="status-icon">✅</span>
                <span>已评测</span>
                <span class="evaluation-time">{{ formatDateTime(currentAnswer.evaluation_time) }}</span>
              </div>
              <div v-else class="status-pending">
                <span class="status-icon">⏳</span>
                <span>待评测</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 导航按钮 -->
    <div class="navigation-actions">
      <button 
        @click="previousAnswer" 
        :disabled="currentIndex === 0"
        class="btn btn-secondary"
      >
        ← 上一题
      </button>
      
      <div class="center-actions">
        <button 
          @click="saveCurrentEvaluation" 
          :disabled="!hasChanges || saving"
          class="btn btn-primary"
        >
          <span v-if="saving">💾 保存中...</span>
          <span v-else>💾 保存评测</span>
        </button>
        
        <button 
          @click="completeEvaluation" 
          :disabled="!isAllEvaluated"
          class="btn btn-success"
        >
          ✅ 完成评测
        </button>
      </div>
      
      <button 
        @click="nextAnswer" 
        :disabled="currentIndex === answers.length - 1"
        class="btn btn-secondary"
      >
        下一题 →
      </button>
    </div>

    <!-- 导入对话框 -->
    <div v-if="showImportDialog" class="modal-overlay" @click="closeImportDialog">
      <div class="modal-content import-modal" @click.stop>
        <div class="modal-header">
          <h3>📁 导入评测结果</h3>
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
              <pre class="format-example">[
  {
    "answer_id": 1,
    "score": 85.5,
    "reasoning": "评分理由..."
  }
]</pre>
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
                  <span class="preview-id">答案ID: {{ item.answer_id }}</span>
                  <span class="preview-status" :class="{ 
                    valid: isValidImportRecord(item),
                    invalid: !isValidImportRecord(item)
                  }">
                    {{ isValidImportRecord(item) ? '✓ 有效' : '✗ 无效' }}
                  </span>
                </div>
                <div class="preview-score">评分: {{ item.score }}</div>
                <div class="preview-reasoning">
                  {{ truncateText(item.reasoning || '无理由', 50) }}
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
              :disabled="validImportRecords === 0 || importing"
            >
              {{ importing ? '导入中...' : `导入 ${validImportRecords} 条数据` }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { llmEvaluationService } from '@/services/llmEvaluationService'

export default {
  name: 'ManualEvaluationInterface',
  props: {
    taskId: {
      type: Number,
      required: true
    },
    taskName: {
      type: String,
      default: ''
    },
    taskStatus: {
      type: String,
      default: 'running'
    }
  },
  emits: ['exit', 'completed'],
  setup(props, { emit }) {
    // 响应式数据
    const answers = ref([])
    const currentIndex = ref(0)
    const saving = ref(false)
    const loading = ref(false)
    
    // 导入相关
    const showImportDialog = ref(false)
    const importStep = ref('select')
    const importData = ref([])
    const validationErrors = ref([])
    const importing = ref(false)
    const importSuccess = ref(false)
    const importResult = ref(null)
    const importErrorMessage = ref('')

    // 计算属性
    const currentAnswer = computed(() => {
      return answers.value[currentIndex.value] || null
    })

    const evaluatedCount = computed(() => {
      return answers.value.filter(answer => answer.is_evaluated).length
    })

    const pendingCount = computed(() => {
      return answers.value.length - evaluatedCount.value
    })

    const averageScore = computed(() => {
      const evaluatedAnswers = answers.value.filter(answer => answer.manual_score !== null && answer.manual_score !== undefined)
      if (evaluatedAnswers.length === 0) return 0
      const totalScore = evaluatedAnswers.reduce((sum, answer) => sum + answer.manual_score, 0)
      return totalScore / evaluatedAnswers.length
    })

    const isAllEvaluated = computed(() => {
      return answers.value.every(answer => 
        answer.manual_score !== null && 
        answer.manual_score !== undefined && 
        answer.manual_reasoning && 
        answer.manual_reasoning.trim().length > 0
      )
    })

    const hasChanges = computed(() => {
      const answer = currentAnswer.value
      if (!answer) return false
      return answer.manual_score !== null || 
             (answer.manual_reasoning && answer.manual_reasoning.trim().length > 0)
    })

    const previewData = computed(() => {
      return importData.value.slice(0, 5) // 显示前5条记录
    })

    const validImportRecords = computed(() => {
      return importData.value.filter(item => isValidImportRecord(item)).length
    })

    // 方法
    const loadAnswers = async () => {
      loading.value = true
      try {
        const data = await llmEvaluationService.getTaskAnswersForManualEvaluation(props.taskId)
        answers.value = data
        currentIndex.value = 0
        console.log('已加载', answers.value.length, '个答案')
      } catch (error) {
        console.error('加载答案失败:', error)
        alert('加载答案失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }

    const saveCurrentEvaluation = async () => {
      const answer = currentAnswer.value
      if (!answer || !hasChanges.value) return

      // 验证输入
      if (answer.manual_score === null || answer.manual_score === undefined) {
        alert('请输入评分')
        return
      }

      if (!answer.manual_reasoning || answer.manual_reasoning.trim().length === 0) {
        alert('请输入评测理由')
        return
      }

      saving.value = true
      try {
        await llmEvaluationService.submitManualEvaluation(answer.id, {
          score: answer.manual_score,
          reasoning: answer.manual_reasoning
        })
        
        // 更新本地状态
        answer.is_evaluated = true
        answer.evaluation_time = new Date().toISOString()
        
        console.log('评测结果已保存')
      } catch (error) {
        console.error('保存评测失败:', error)
        alert('保存评测失败: ' + error.message)
      } finally {
        saving.value = false
      }
    }

    const previousAnswer = () => {
      if (currentIndex.value > 0) {
        currentIndex.value--
      }
    }

    const nextAnswer = () => {
      if (currentIndex.value < answers.value.length - 1) {
        currentIndex.value++
      }
    }

    const markAsChanged = () => {
      // 标记当前答案有变化
      console.log('答案已修改')
    }

    const completeEvaluation = async () => {
      if (!isAllEvaluated.value) {
        alert('请完成所有答案的评测')
        return
      }

      try {
        // 保存当前评测结果（如果有的话）
        if (hasChanges.value) {
          await saveCurrentEvaluation()
        }
        
        emit('completed')
        console.log('评测完成')
      } catch (error) {
        console.error('完成评测失败:', error)
        alert('完成评测失败: ' + error.message)
      }
    }

    const exitEvaluation = async () => {
      // 保存当前评测结果（如果有的话）
      if (hasChanges.value) {
        await saveCurrentEvaluation()
      }
      
      emit('exit')
    }

    const downloadAnswers = async () => {
      try {
        const blob = await llmEvaluationService.downloadAnswersOnly(props.taskId)
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `llm-answers-${props.taskId}.json`
        a.click()
        window.URL.revokeObjectURL(url)
        console.log('答案数据下载成功')
      } catch (error) {
        console.error('下载失败:', error)
        alert('下载失败: ' + error.message)
      }
    }

    // 导入相关方法
    const closeImportDialog = () => {
      showImportDialog.value = false
      importStep.value = 'select'
      importData.value = []
      validationErrors.value = []
      importSuccess.value = false
      importResult.value = null
      importErrorMessage.value = ''
    }

    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (!file) return

      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result)
          if (Array.isArray(data)) {
            importData.value = data
            validateImportData(data)
            importStep.value = 'preview'
          } else {
            alert('文件格式错误：应该是JSON数组格式')
          }
        } catch (error) {
          alert('文件解析失败：请确保是有效的JSON文件')
        }
      }
      reader.readAsText(file)
    }

    const validateImportData = (data) => {
      validationErrors.value = []
      
      data.forEach((item, index) => {
        if (!item.answer_id) {
          validationErrors.value.push(`第${index + 1}项缺少answer_id字段`)
        }
        if (item.score === null || item.score === undefined) {
          validationErrors.value.push(`第${index + 1}项缺少score字段`)
        }
      })
    }

    const isValidImportRecord = (item) => {
      return item && 
             typeof item.answer_id === 'number' && 
             item.score !== null && 
             item.score !== undefined
    }

    const executeImport = async () => {
      importing.value = true
      importStep.value = 'importing'
      
      try {
        const validRecords = importData.value.filter(item => isValidImportRecord(item))
        
        const result = await llmEvaluationService.importManualEvaluations(
          props.taskId,
          validRecords.map(item => ({
            answer_id: item.answer_id,
            score: item.score,
            reasoning: item.reasoning || ''
          }))
        )
        
        importSuccess.value = true
        importResult.value = result
        importStep.value = 'result'
        
        // 重新加载答案数据
        await loadAnswers()
        
      } catch (error) {
        importSuccess.value = false
        importErrorMessage.value = error.message || '导入失败'
        importStep.value = 'result'
      } finally {
        importing.value = false
      }
    }

    const getStatusText = (status) => {
      const statusMap = {
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      }
      return statusMap[status] || status
    }

    const formatDateTime = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString('zh-CN')
    }

    const truncateText = (text, maxLength) => {
      if (!text) return ''
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    }

    // 生命周期
    onMounted(() => {
      loadAnswers()
    })

    // 自动保存功能
    let autoSaveTimer = null
    const startAutoSave = () => {
      if (autoSaveTimer) clearTimeout(autoSaveTimer)
      autoSaveTimer = setTimeout(() => {
        if (hasChanges.value) {
          saveCurrentEvaluation()
        }
      }, 30000) // 30秒后自动保存
    }

    const stopAutoSave = () => {
      if (autoSaveTimer) {
        clearTimeout(autoSaveTimer)
        autoSaveTimer = null
      }
    }

    onUnmounted(() => {
      stopAutoSave()
    })

    return {
      // 数据
      answers,
      currentIndex,
      saving,
      loading,
      showImportDialog,
      importStep,
      importData,
      validationErrors,
      importing,
      importSuccess,
      importResult,
      importErrorMessage,

      // 计算属性
      currentAnswer,
      evaluatedCount,
      pendingCount,
      averageScore,
      isAllEvaluated,
      hasChanges,
      previewData,
      validImportRecords,

      // 方法
      loadAnswers,
      saveCurrentEvaluation,
      previousAnswer,
      nextAnswer,
      markAsChanged,
      completeEvaluation,
      exitEvaluation,
      downloadAnswers,
      closeImportDialog,
      handleFileSelect,
      validateImportData,
      isValidImportRecord,
      executeImport,
      getStatusText,
      formatDateTime,
      truncateText
    }
  }
}
</script>

<style scoped>
.manual-evaluation-interface {
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

/* 头部 */
.evaluation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-info h2 {
  margin: 0 0 8px 0;
  color: #2d3748;
  font-size: 24px;
  font-weight: 600;
}

.header-info p {
  margin: 0 0 12px 0;
  color: #6b7280;
  font-size: 16px;
}

.task-info {
  display: flex;
  gap: 16px;
  align-items: center;
}

.task-name {
  font-weight: 500;
  color: #4a5568;
}

.task-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.task-status.running {
  background: #e6fffa;
  color: #234e52;
}

.task-status.completed {
  background: #f0fff4;
  color: #22543d;
}

.task-status.failed {
  background: #fed7d7;
  color: #742a2a;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 进度条 */
.evaluation-progress {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-info {
  display: flex;
  gap: 16px;
  align-items: center;
}

.current-index {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.total-count {
  color: #6b7280;
}

.progress-percentage {
  font-size: 18px;
  font-weight: 600;
  color: #3182ce;
}

.progress-bar {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3182ce, #63b3ed);
  transition: width 0.3s ease;
}

.progress-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  color: #6b7280;
  font-size: 14px;
}

/* 评测内容 */
.evaluation-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  min-height: 600px;
}

.left-panel, .right-panel {
  padding: 24px;
}

.left-panel {
  border-right: 1px solid #e2e8f0;
}

/* 问题部分 */
.question-section {
  margin-bottom: 24px;
}

.question-section h3 {
  margin: 0 0 16px 0;
  color: #2d3748;
  font-size: 18px;
  font-weight: 600;
}

.question-content {
  background: #f7fafc;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #3182ce;
}

.question-body {
  font-size: 16px;
  line-height: 1.6;
  color: #2d3748;
  margin-bottom: 12px;
}

.question-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-type {
  background: #e6fffa;
  color: #234e52;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.question-tags {
  display: flex;
  gap: 8px;
}

.tag {
  background: #edf2f7;
  color: #4a5568;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

/* 标准答案部分 */
.standard-answers-section h3 {
  margin: 0 0 16px 0;
  color: #2d3748;
  font-size: 18px;
  font-weight: 600;
}

.std-answer-item {
  background: #f0fff4;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #38a169;
  margin-bottom: 16px;
}

.std-answer-content {
  margin-bottom: 12px;
}

.answer-text {
  font-size: 16px;
  line-height: 1.6;
  color: #2d3748;
  margin-bottom: 8px;
}

.answer-meta {
  color: #6b7280;
  font-size: 14px;
}

.scoring-points h4 {
  margin: 0 0 8px 0;
  color: #4a5568;
  font-size: 14px;
  font-weight: 600;
}

.scoring-point {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 14px;
  color: #4a5568;
}

.point-order {
  font-weight: 600;
  color: #3182ce;
  min-width: 20px;
}

/* LLM回答部分 */
.llm-answer-section {
  margin-bottom: 24px;
}

.llm-answer-section h3 {
  margin: 0 0 16px 0;
  color: #2d3748;
  font-size: 18px;
  font-weight: 600;
}

.llm-answer-content {
  background: #f7fafc;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #805ad5;
}

.llm-answer-content .answer-text {
  font-size: 16px;
  line-height: 1.6;
  color: #2d3748;
  margin-bottom: 12px;
}

.answer-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #6b7280;
  font-size: 14px;
}

.is-valid {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.is-valid.valid {
  background: #f0fff4;
  color: #22543d;
}

.is-valid.invalid {
  background: #fed7d7;
  color: #742a2a;
}

/* 手动评测部分 */
.manual-evaluation-section h3 {
  margin: 0 0 16px 0;
  color: #2d3748;
  font-size: 18px;
  font-weight: 600;
}

.score-input {
  margin-bottom: 20px;
}

.score-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #4a5568;
}

.score-value {
  color: #3182ce;
  font-weight: 600;
  font-size: 18px;
}

.score-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
}

.score-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3182ce;
  cursor: pointer;
}

.score-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3182ce;
  cursor: pointer;
  border: none;
}

.score-range {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  color: #6b7280;
  font-size: 12px;
}

.reasoning-input {
  margin-bottom: 20px;
}

.reasoning-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #4a5568;
}

.reasoning-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  font-family: inherit;
}

.reasoning-textarea:focus {
  outline: none;
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
}

.evaluation-status {
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
}

.status-evaluated {
  background: #f0fff4;
  color: #22543d;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-pending {
  background: #fef5e7;
  color: #744210;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  font-size: 16px;
}

.evaluation-time {
  margin-left: auto;
  font-size: 12px;
  opacity: 0.8;
}

/* 导航按钮 */
.navigation-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.center-actions {
  display: flex;
  gap: 12px;
}

/* 按钮样式 */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3182ce;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2c5aa0;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #4a5568;
}

.btn-success {
  background: #38a169;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #2f855a;
}

.btn-info {
  background: #0bc5ea;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #0891b2;
}

.btn-outline {
  background: transparent;
  color: #3182ce;
  border: 1px solid #3182ce;
}

.btn-outline:hover:not(:disabled) {
  background: #3182ce;
  color: white;
}

/* 导入对话框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.import-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 20px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
}

.modal-body {
  padding: 24px;
}

.import-info {
  margin-bottom: 20px;
  padding: 12px;
  background: #f7fafc;
  border-radius: 8px;
}

.file-upload-area {
  margin-bottom: 20px;
}

.file-input {
  display: none;
}

.file-upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  border: 2px dashed #cbd5e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.file-upload-label:hover {
  border-color: #3182ce;
  background: #f7fafc;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-text p {
  margin: 0;
  color: #4a5568;
}

.upload-hint {
  font-size: 14px;
  color: #6b7280;
}

.data-format-help {
  background: #f7fafc;
  padding: 16px;
  border-radius: 8px;
}

.data-format-help h5 {
  margin: 0 0 12px 0;
  color: #2d3748;
}

.format-example {
  background: #2d3748;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}

.preview-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.preview-item {
  background: #f7fafc;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.preview-id {
  font-weight: 500;
  color: #2d3748;
}

.preview-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.preview-status.valid {
  background: #f0fff4;
  color: #22543d;
}

.preview-status.invalid {
  background: #fed7d7;
  color: #742a2a;
}

.preview-score {
  color: #4a5568;
  margin-bottom: 4px;
}

.preview-reasoning {
  color: #6b7280;
  font-size: 14px;
}

.validation-errors {
  background: #fed7d7;
  padding: 12px;
  border-radius: 8px;
  margin-top: 16px;
}

.validation-errors h5 {
  margin: 0 0 8px 0;
  color: #742a2a;
}

.validation-errors ul {
  margin: 0;
  padding-left: 20px;
  color: #742a2a;
}

.importing-status {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #3182ce;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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
  color: #38a169;
}

.result-icon.error {
  color: #e53e3e;
}

.error-text {
  color: #e53e3e;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .left-panel {
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
  }
  
  .navigation-actions {
    flex-direction: column;
    gap: 16px;
  }
  
  .center-actions {
    order: -1;
  }
}
</style> 
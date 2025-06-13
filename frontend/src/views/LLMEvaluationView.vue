<template>
  <div class="llm-evaluation">
    <!-- 顶部标题栏 -->
    <div class="header">
      <div class="header-left">
        <button @click="backToMarketplace" class="back-btn">
          <span>← 返回数据集市场</span>
        </button>
        <h2>LLM在线评测</h2>
      </div>
      <div class="header-right">
        <button v-if="evaluationTask" @click="viewTaskProgress" class="progress-btn">
          📊 查看进度
        </button>
      </div>
    </div>    <!-- 步骤指示器 -->
    <div class="steps-container">
      <div class="steps-wrapper">
        <div class="step-item" :class="{ 
          active: currentStep === 0, 
          locked: isStepLocked(0) 
        }">
          <span class="step-number">
            <span v-if="isStepLocked(0)">🔒</span>
            <span v-else>1</span>
          </span>
          <span class="step-title">配置模型</span>
        </div>
        <div class="step-item" :class="{ 
          active: currentStep === 1, 
          locked: isStepLocked(1) 
        }">
          <span class="step-number">
            <span v-if="isStepLocked(1)">🔒</span>
            <span v-else>2</span>
          </span>
          <span class="step-title">配置系统Prompt</span>
        </div>
        <div class="step-item" :class="{ active: currentStep === 2 }">
          <span class="step-number">3</span>
          <span class="step-title">生成回答</span>
        </div>
        <div class="step-item" :class="{ 
          active: currentStep === 3, 
          locked: isStepLocked(3) 
        }">
          <span class="step-number">
            <span v-if="isStepLocked(3)">🔒</span>
            <span v-else>4</span>
          </span>
          <span class="step-title">配置评测</span>
        </div>
        <div class="step-item" :class="{ active: currentStep === 4 }">
          <span class="step-number">5</span>
          <span class="step-title">查看结果</span>
        </div>
      </div>
    </div><!-- 步骤1: 模型配置 -->
    <div v-if="currentStep === 0" class="step-content">
      <div class="content-card">
        <div class="card-header">
          <h3>⚙️ 配置模型和API信息</h3>
          <p>配置您要评测的大语言模型和相关API参数</p>
        </div>
        
        <!-- 显示选中的数据集信息 -->
        <div v-if="currentDataset" class="dataset-summary">
          <div class="summary-card">
            <div class="summary-content">
              <div class="summary-info">
                <h4>数据集名称：{{ currentDataset.name }}</h4>
                <p>数据集描述：{{ currentDataset.description }}</p>
                <div class="summary-tags">
                  <span class="tag">{{ currentDataset.question_count }} 题</span>
                  <span class="tag tag-success">v{{ currentDataset.version }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="config-section">
          <h4>💻 模型选择</h4>
          <div class="config-card">
            <div class="form-group">
              <label class="form-label">选择模型 
                <span class="required">*</span>
              </label>                <select 
                v-model="modelConfig.model_id" 
                class="form-select"
                :disabled="isStepLocked(0)"
              >
                <option :value="null">请选择要评测的模型</option>
                <option
                  v-for="model in availableModels"
                  :key="model.id"
                  :value="model.id"
                >
                  {{ model.display_name }} ({{ model.provider }}) - {{ model.max_tokens }} tokens
                </option>
              </select>
              
              <div v-if="selectedModel" class="model-details">
                <div class="alert alert-info">
                  <strong>{{ selectedModel.display_name }}</strong><br>
                  {{ selectedModel.description }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="config-section">
          <h4>🔑 API配置</h4>
          <div class="config-card">
            <div class="form-group">
              <label class="form-label">API Key <span class="required">*</span></label>              <input 
                v-model="modelConfig.api_key" 
                type="password" 
                class="form-input"
                placeholder="请输入您的API Key"
                :disabled="isStepLocked(0)"
              />
              <div class="form-tip">
                ℹ️ API Key将被安全加密存储，仅用于本次评测
              </div>            </div>
          </div>
        </div>

        <div class="config-section">
          <h4>🛠️ 模型参数</h4>
          <div class="config-card">
            <div class="form-group">
              <label class="form-label">温度参数: {{ modelConfig.temperature }}</label>              
              <input 
                v-model.number="modelConfig.temperature" 
                type="range" 
                min="0" 
                max="2" 
                step="0.1"
                class="form-range"
                :disabled="isStepLocked(0)"
              />
              <div class="range-labels">
                <span>保守</span>
                <span>平衡</span>
                <span>创新</span>
              </div>
              <div class="form-tip">
                ℹ️ 温度越高，回答越有创意但可能不够准确
              </div>
            </div>
              <div class="form-group">
              <label class="form-label">最大Token数</label>              <input 
                v-model.number="modelConfig.max_tokens" 
                type="number" 
                min="100" 
                max="8000" 
                step="100"
                class="form-input"
                :disabled="isStepLocked(0)"
              />
              <div class="form-tip">
                ℹ️ 建议设置为2000-4000，确保回答完整
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">Top-K采样: {{ modelConfig.top_k }}</label>              <input
                v-model.number="modelConfig.top_k" 
                type="range" 
                min="1" 
                max="100" 
                step="1"
                class="form-range"
                :disabled="isStepLocked(0)"
              />
              <div class="range-labels">
                <span>精确(1)</span>
                <span>平衡(50)</span>
                <span>多样(100)</span>
              </div>
              <div class="form-tip">
                ℹ️ 控制生成时考虑的候选词数量，值越小越保守
              </div>
            </div>
              <div class="form-group">
              <label class="form-label">                <input 
                  v-model="modelConfig.enable_reasoning" 
                  type="checkbox"
                  class="form-checkbox"
                  :disabled="isStepLocked(0)"
                />
                启用推理模式
              </label>
              <div class="form-tip">
                ℹ️ 启用后模型会展示详细的推理过程（如果支持）
              </div>
            </div>
          </div>
        </div><div class="step-actions">
          <button @click="nextStep" :disabled="!isModelConfigValid" class="btn btn-primary">
            下一步 →
          </button>
        </div>
      </div>
    </div>    <!-- 步骤2: 系统Prompt配置 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="content-card">
        <div class="card-header">
          <h3>🤖 配置系统Prompt</h3>
          <p>配置模型回答问题时的系统级指令，不同题型会有不同的要求</p>
        </div>
        
        <!-- 数据集题型分析 -->
        <div v-if="currentDataset" class="dataset-analysis">
          <h4>📊 数据集题型分析</h4>
          <div class="type-analysis-grid">
            <div class="analysis-card">
              <div class="analysis-icon">📝</div>
              <div class="analysis-info">
                <h5>选择题</h5>
                <p>{{ choiceQuestionCount }} 题</p>
                <div class="analysis-desc">需要强制输出选项标识</div>
              </div>
            </div>
            <div class="analysis-card">
              <div class="analysis-icon">💭</div>
              <div class="analysis-info">
                <h5>文本题</h5>
                <p>{{ textQuestionCount }} 题</p>
                <div class="analysis-desc">自由文本回答</div>
              </div>
            </div>
          </div>
        </div>        <!-- 系统Prompt配置 -->
        <div class="prompt-container">
          <div class="tabs">
            <button 
              @click="activeSystemPromptTab = 'choice'" 
              :class="['tab-button', { active: activeSystemPromptTab === 'choice' }]"
            >
              选择题Prompt
            </button>
            <button 
              @click="activeSystemPromptTab = 'text'" 
              :class="['tab-button', { active: activeSystemPromptTab === 'text' }]"
            >
              文本题Prompt
            </button>
          </div>
          
          <div v-if="activeSystemPromptTab === 'choice'" class="prompt-section">
            <div class="prompt-header">
              <div class="header-left">
                <span class="icon">📝</span>
                <div>
                  <h4>选择题系统Prompt</h4>
                  <p>指导模型如何回答选择题，要求强制输出选项标识</p>
                </div>
              </div>
              <div class="header-actions">
                <button @click="resetChoicePrompt" class="btn btn-small btn-info">
                  🔄 重置默认
                </button>
              </div>
            </div>
            
            <div class="prompt-editor">              <textarea
                v-model="systemPromptConfig.choice_system_prompt"
                rows="12"
                placeholder="请输入选择题系统Prompt..."
                class="prompt-textarea"
                :disabled="isStepLocked(1)"
              ></textarea>
              <div class="editor-info">
                <div class="char-count">
                  📄 {{ systemPromptConfig.choice_system_prompt.length }} 字符
                </div>
              </div>
            </div>
          </div>          
          <div v-else class="prompt-section">
            <div class="prompt-header">
              <div class="header-left">
                <span class="icon">💭</span>
                <div>
                  <h4>文本题系统Prompt</h4>
                  <p>指导模型如何回答开放性文本问题</p>
                </div>
              </div>
              <div class="header-actions">
                <button @click="resetTextPrompt" class="btn btn-small btn-info">
                  🔄 重置默认
                </button>
              </div>
            </div>
            
            <div class="prompt-editor">              <textarea
                v-model="systemPromptConfig.text_system_prompt"
                rows="12"
                placeholder="请输入文本题系统Prompt..."
                class="prompt-textarea"
                :disabled="isStepLocked(1)"
              ></textarea>
              <div class="editor-info">
                <div class="char-count">
                  📄 {{ systemPromptConfig.text_system_prompt.length }} 字符
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Prompt预览 -->
        <div class="prompt-preview">
          <h4>👁️ 预览效果</h4>
          <div class="preview-card">
            <div class="preview-content">
              <div class="message-item system">
                <div class="message-label">
                  🤖 系统
                </div>
                <div class="message-content">
                  {{ activeSystemPromptTab === 'choice' ? systemPromptConfig.choice_system_prompt : systemPromptConfig.text_system_prompt || '请输入系统Prompt...' }}
                </div>
              </div>
              <div class="message-item user">
                <div class="message-label">
                  👤 用户
                </div>
                <div class="message-content">{{ getSampleQuestion().question }}</div>
              </div>
            </div>
          </div>
        </div>
          <div class="step-actions">
          <button @click="prevStep" class="btn btn-secondary">
            ← 上一步
          </button>
          <button @click="nextStep" :disabled="!isSystemPromptValid" class="btn btn-primary">
            下一步 →
          </button>
        </div>
      </div>    </div>    <!-- 步骤3: 答案生成 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="content-card">
        <div class="card-header">
          <h3>🤖 答案生成</h3>
          <p>使用配置的模型和系统Prompt生成题目答案</p>        
        </div>
        
        <!-- 数据集分析 -->
        <div class="dataset-analysis">
          <h4>📊 数据集分析</h4>
          <div class="type-analysis-grid">
            <div class="analysis-card">
              <div class="analysis-header">
                <div class="analysis-icon">🔘</div>
                <h5 class="analysis-title">选择题</h5>
              </div>
              <div class="analysis-count">{{ choiceQuestionCount }}</div>
              <div class="analysis-desc">单项选择题</div>
            </div>
            <div class="analysis-card">
              <div class="analysis-header">
                <div class="analysis-icon">💭</div>
                <h5 class="analysis-title">文本题</h5>
              </div>
              <div class="analysis-count">{{ textQuestionCount }}</div>
              <div class="analysis-desc">自由文本回答</div>
            </div>
          </div>
        </div>
        
        <!-- 生成选项 -->
        <div class="generation-options">
          <h4>🔧 生成参数</h4>
          <div class="options-grid">
            <div class="option-item">
              <label>任务名称</label>
              <input
                v-model="answerGenerationOptions.task_name"
                type="text"
                placeholder="请输入任务名称"
                class="form-input"
                :disabled="isStepLocked(2)"
              />
            </div>
            
            <div class="option-item">
              <label>题目限制</label>
              <select v-model="answerGenerationOptions.question_limit_type" class="form-select" :disabled="isStepLocked(2)">
                <option value="all">生成全部题目</option>
                <option value="limit">限制题目数量</option>
              </select>
            </div>
              <div v-if="answerGenerationOptions.question_limit_type === 'limit'" class="option-item">
              <label>题目数量</label>
              <input
                v-model.number="answerGenerationOptions.question_limit"
                type="number"
                min="1"
                :max="currentDataset?.question_count"
                class="form-input"
                :disabled="isStepLocked(2)"
              />
            </div>
              <div class="option-item">
              <label>并发限制</label>
              <input
                v-model.number="answerGenerationOptions.concurrent_limit"
                type="number"
                min="1"
                max="10"
                class="form-input"
                :disabled="isStepLocked(2)"
              />
            </div>
          </div>
        </div>
        
        <!-- 配置摘要 -->
        <div class="config-summary-section">
          <h4>📋 配置摘要</h4>
          <div class="summary-grid">
            <div class="summary-item-card">
              <div class="summary-item">
                <div class="summary-icon">📁</div>
                <div class="summary-details">
                  <h5>数据集</h5>
                  <p>{{ currentDataset?.name }}</p>
                  <div class="summary-meta">
                    <span class="tag">{{ choiceQuestionCount }} 选择题</span>
                    <span class="tag">{{ textQuestionCount }} 文本题</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="summary-item-card">
              <div class="summary-item">
                <div class="summary-icon">💻</div>
                <div class="summary-details">
                  <h5>模型</h5>
                  <p>{{ selectedModel?.display_name }}</p>
                  <div class="summary-meta">
                    <span class="tag tag-info">{{ selectedModel?.name }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="summary-item-card">
              <div class="summary-item">
                <div class="summary-icon">📝</div>
                <div class="summary-details">
                  <h5>系统Prompt</h5>
                  <p>已配置选择题和文本题Prompt</p>
                  <div class="summary-meta">
                    <span class="tag tag-success">已配置</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="card-actions">
          <button @click="prevStep" class="btn btn-secondary">
            ← 上一步
          </button>          <!-- 根据答案生成状态显示不同按钮 -->
          <button 
            v-if="!answerGenerationTask || answerGenerationTask.status !== 'evaluating_answers'"
            @click="startAnswerGeneration" 
            :disabled="!isSystemPromptValid || starting || isStepLocked(2)" 
            class="btn btn-primary">
            <span v-if="starting">⏳ 生成中...</span>
            <span v-else>🚀 开始生成答案</span>
          </button>
          <button 
            v-else
            @click="nextStep" 
            class="btn btn-primary">
            下一步：配置评测 →
          </button>
        </div>
      </div>
    </div>    <!-- 步骤4: 评测配置 -->
    <div v-if="currentStep === 3" class="step-content">
      <div class="content-card">
        <div class="card-header">
          <h3>⚖️ 配置评测</h3>
          <p>配置评测Prompt来自动打分LLM的回答质量</p>
        </div>
        
        <!-- 评测Prompt配置 -->
        <div class="prompt-container">
          <div class="tabs">
            <button 
              @click="activeEvaluationTab = 'choice'" 
              :class="['tab-button', { active: activeEvaluationTab === 'choice' }]"
            >
              选择题评测
            </button>
            <button 
              @click="activeEvaluationTab = 'text'" 
              :class="['tab-button', { active: activeEvaluationTab === 'text' }]"
            >
              文本题评测
            </button>
          </div>
          
          <div v-if="activeEvaluationTab === 'choice'" class="prompt-section">
            <div class="prompt-header">
              <div class="header-left">
                <span class="icon">⚖️</span>
                <div>
                  <h4>选择题评测Prompt</h4>
                  <p>定义如何评测选择题的回答准确性</p>
                </div>
              </div>
              <div class="header-actions">
                <button @click="resetChoiceEvaluationPrompt" class="btn btn-small btn-info">
                  🔄 重置默认
                </button>
              </div>
            </div>
            
            <div class="prompt-editor">              <textarea
                v-model="evaluationConfig.choice_evaluation_prompt"
                rows="12"
                placeholder="请输入选择题评测Prompt..."
                class="prompt-textarea"
                :disabled="isStepLocked(3)"
              ></textarea>
              <div class="editor-info">
                <div class="char-count">
                  📄 {{ evaluationConfig.choice_evaluation_prompt.length }} 字符
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="prompt-section">
            <div class="prompt-header">
              <div class="header-left">
                <span class="icon">📊</span>
                <div>
                  <h4>文本题评测Prompt</h4>
                  <p>定义如何评测开放性文本题的回答质量</p>
                </div>
              </div>
              <div class="header-actions">
                <button @click="resetTextEvaluationPrompt" class="btn btn-small btn-info">
                  🔄 重置默认
                </button>
              </div>
            </div>
            
            <div class="prompt-editor">              
              <textarea
                v-model="evaluationConfig.text_evaluation_prompt"
                rows="12"
                placeholder="请输入文本题评测Prompt..."
                class="prompt-textarea"
                :disabled="isStepLocked(3)"
              ></textarea>
              <div class="editor-info">
                <div class="char-count">
                  📄 {{ evaluationConfig.text_evaluation_prompt.length }} 字符
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 评测选项 -->
        <div class="evaluation-options">
          <h4>🔧 评测选项</h4>
          <div class="options-grid">
            <div class="option-item">
              <label>评测任务名称</label>
              <input
                v-model="evaluationOptions.task_name"
                type="text"
                placeholder="请输入评测任务名称"
                class="form-input"
              />
            </div>
            
            <div class="option-item">
              <label>
                <input
                  v-model="evaluationOptions.is_auto_score"
                  type="checkbox"
                  class="form-checkbox"
                />
                启用自动打分
              </label>
              <p class="option-description">使用LLM自动对答案进行评分</p>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="card-actions">
          <button @click="prevStep" class="btn btn-secondary">
            ← 上一步
          </button>          
          <button @click="startEvaluation" :disabled="!isEvaluationConfigValid || starting" class="btn btn-primary">
            <span v-if="starting">⏳ 评测中...</span>
            <span v-else>🚀 开始评测</span>
          </button>
        </div>
      </div>    
    </div>    
    <!-- 步骤5: 查看结果 -->
    <div v-if="currentStep === 4" class="step-content">
      <div class="evaluation-results">
        <!-- 加载状态 -->
        <div v-if="loadingDetailedResults" class="loading-state">
          <div class="loading-spinner"></div>
          <p>正在加载详细结果...</p>
        </div>

        <!-- 详细结果显示 -->
        <div v-else-if="detailedResults" class="detailed-results">
          <!-- 头部操作 -->
          <div class="top-actions">
            <button @click="backToMarketplace" class="btn btn-secondary">返回数据集市场</button>
            <button 
              v-if="evaluationTask && evaluationTask.status === 'completed'"
              @click="downloadResults"
              class="btn btn-success"
            >
              📥 下载完整结果
            </button>
          </div>

          <!-- 任务基本信息 -->
          <div class="task-info-section">
            <div class="section-header">
              <h3>📋 任务信息</h3>
              <span class="status-tag" :class="getStatusType(detailedResults.task_info.status)">
                {{ getStatusText(detailedResults.task_info.status) }}
              </span>
            </div>
            
            <div class="task-info-grid">
              <div class="info-card">
                <div class="info-item">
                  <label>任务名称</label>
                  <span>{{ detailedResults.task_info.name }}</span>
                </div>
                <div class="info-item">
                  <label>数据集</label>
                  <span>{{ detailedResults.task_info.dataset_name }}</span>
                </div>
                <div class="info-item">
                  <label>模型</label>
                  <span>{{ detailedResults.task_info.model_name }}</span>
                  <span v-if="detailedResults.task_info.model_version" class="model-version">
                    v{{ detailedResults.task_info.model_version }}
                  </span>
                </div>
              </div>
              
              <div class="info-card">
                <div class="info-item">
                  <label>创建时间</label>
                  <span>{{ formatDateTime(detailedResults.task_info.created_at) }}</span>
                </div>
                <div class="info-item">
                  <label>开始时间</label>
                  <span>{{ formatDateTime(detailedResults.task_info.started_at) }}</span>
                </div>
                <div class="info-item">
                  <label>完成时间</label>
                  <span>{{ formatDateTime(detailedResults.task_info.completed_at) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 配置参数 -->
          <div class="configuration-section">
            <div class="section-header">
              <h3>⚙️ 配置参数</h3>
            </div>
            
            <div class="config-grid">
              <div class="config-card">
                <h4>🤖 模型参数</h4>
                <div class="config-items">
                  <div class="config-item">
                    <label>温度参数</label>
                    <span>{{ detailedResults.configuration.temperature || 0.7 }}</span>
                  </div>
                  <div class="config-item">
                    <label>最大Token数</label>
                    <span>{{ detailedResults.configuration.max_tokens || 2000 }}</span>
                  </div>
                  <div class="config-item">
                    <label>Top-K采样</label>
                    <span>{{ detailedResults.configuration.top_k || 50 }}</span>
                  </div>
                  <div class="config-item">
                    <label>推理模式</label>
                    <span class="boolean-value" :class="detailedResults.configuration.enable_reasoning ? 'enabled' : 'disabled'">
                      {{ detailedResults.configuration.enable_reasoning ? '启用' : '禁用' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 提示词信息 -->
          <div class="prompts-section">
            <div class="section-header">
              <h3>💬 提示词配置</h3>
            </div>
            
            <div class="prompts-grid">
              <div class="prompt-card">
                <h4>系统Prompt</h4>
                <div class="prompt-content">
                  <pre>{{ detailedResults.configuration.system_prompt || '未设置系统Prompt' }}</pre>
                </div>
              </div>
              
              <div class="prompt-card">
                <h4>评估Prompt</h4>
                <div class="prompt-content">
                  <pre>{{ detailedResults.configuration.evaluation_prompt || '未设置评估Prompt' }}</pre>
                </div>
              </div>
            </div>
          </div>

          <!-- 统计概览 -->
          <div class="statistics-section">
            <div class="section-header">
              <h3>📊 统计概览</h3>
            </div>
            
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-info">
                  <div class="stat-value">{{ detailedResults.statistics.total_answers }}</div>
                  <div class="stat-label">总答案数</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-info">
                  <div class="stat-value">{{ detailedResults.statistics.valid_answers }}</div>
                  <div class="stat-label">有效答案</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">🎯</div>
                <div class="stat-info">
                  <div class="stat-value">{{ detailedResults.statistics.evaluated_answers }}</div>
                  <div class="stat-label">已评分答案</div>
                </div>
              </div>
              
              <div class="stat-card overall-score">
                <div class="stat-icon">🏆</div>
                <div class="stat-info">
                  <div class="stat-value">{{ detailedResults.statistics.overall_average_score }}</div>
                  <div class="stat-label">平均分数</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">📈</div>
                <div class="stat-info">
                  <div class="stat-value">{{ Math.round(detailedResults.statistics.completion_rate * 100) }}%</div>
                  <div class="stat-label">完成率</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 详细答案列表 -->
          <div class="detailed-answers-section">
            <div class="section-header">
              <h3>📋 详细答案列表</h3>
              <div class="section-actions">
                <select v-model="pageSize" class="page-size-select">
                  <option value="10">10/页</option>
                  <option value="20">20/页</option>
                  <option value="50">50/页</option>
                </select>
              </div>
            </div>
            
            <div class="answers-table-container">
              <table class="detailed-answers-table">
                <thead>
                  <tr>
                    <th>序号</th>
                    <th>问题类型</th>
                    <th>问题内容</th>
                    <th>模型回答</th>
                    <th>标准答案</th>
                    <th>评分</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(answer, index) in paginatedDetailedAnswers" :key="answer.question_id">
                    <td>{{ (currentPage - 1) * pageSize + index + 1 }}</td>
                    <td>
                      <span class="question-type-badge" :class="answer.question_type">
                        {{ getQuestionTypeText(answer.question_type) }}
                      </span>
                    </td>
                    <td class="question-cell">
                      <div class="question-text">{{ answer.question_text }}</div>
                    </td>
                    <td class="answer-cell">
                      <div class="answer-text">{{ answer.llm_answer.answer }}</div>
                      <div v-if="!answer.llm_answer.is_valid" class="invalid-badge">无效答案</div>
                    </td>
                    <td class="standard-answers-cell">
                      <div v-for="stdAnswer in answer.standard_answers" :key="stdAnswer.id" class="standard-answer">
                        <div class="std-answer-text">{{ stdAnswer.answer }}</div>
                        <div v-if="stdAnswer.scoring_points && stdAnswer.scoring_points.length > 0" class="scoring-points">
                          <span v-for="point in stdAnswer.scoring_points" :key="point.point_order" class="scoring-point">
                            {{ point.answer }}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td class="score-cell">
                      <div v-if="answer.evaluations && answer.evaluations.length > 0">
                        <div v-for="evaluation in answer.evaluations" :key="evaluation.id" class="evaluation-score">
                          <span class="score-value" :class="getScoreClass(evaluation.score)">
                            {{ evaluation.score || '-' }}
                          </span>
                          <span class="evaluator-type">
                            {{ evaluation.evaluator_type === 'llm' ? 'LLM' : '人工' }}
                          </span>
                        </div>
                        <div class="average-score">
                          平均: {{ answer.average_score }}
                        </div>
                      </div>
                      <span v-else class="no-score">未评分</span>
                    </td>
                    <td>
                      <button @click="viewDetailedEvaluation(answer)" class="btn btn-small btn-info">
                        查看详情
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <!-- 分页控件 -->
            <div class="pagination">
              <div class="pagination-controls">
                <button 
                  @click="currentPage = 1" 
                  :disabled="currentPage === 1"
                  class="btn btn-small btn-secondary"
                >
                  首页
                </button>
                <button 
                  @click="currentPage--" 
                  :disabled="currentPage === 1"
                  class="btn btn-small btn-secondary"
                >
                  上一页
                </button>
                <span class="page-info">
                  第 {{ currentPage }} 页，共 {{ Math.ceil(detailedResults.detailed_answers.length / pageSize) }} 页
                </span>
                <button 
                  @click="currentPage++" 
                  :disabled="currentPage >= Math.ceil(detailedResults.detailed_answers.length / pageSize)"
                  class="btn btn-small btn-secondary"
                >
                  下一页
                </button>
                <button 
                  @click="currentPage = Math.ceil(detailedResults.detailed_answers.length / pageSize)" 
                  :disabled="currentPage >= Math.ceil(detailedResults.detailed_answers.length / pageSize)"
                  class="btn btn-small btn-secondary"
                >
                  末页
                </button>
              </div>
              
              <div class="total-info">
                共 {{ detailedResults.detailed_answers.length }} 条记录
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="result-actions">
            <button @click="restart" class="btn btn-secondary">重新开始评测</button>
            <button @click="downloadDetailedResults" class="btn btn-success">
              📥 下载详细结果
            </button>
            <button @click="downloadAnswersOnly" class="btn btn-info">
              📄 下载答案数据
            </button>
          </div>
        </div>

        <!-- 简单进度显示（运行中时） -->
        <div v-else-if="evaluationTask" class="simple-progress">
          <h3>评测进度</h3>
          <div class="progress-card">
            <div class="progress-header">
              <h4>{{ evaluationTask.task_name || '在线评测任务' }}</h4>
              <span class="status-tag" :class="getStatusType(evaluationTask.status)">{{ getStatusText(evaluationTask.status) }}</span>
            </div>
            
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ evaluationTask.total_questions }}</div>
                <div class="stat-label">总问题数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ evaluationTask.completed_questions }}</div>
                <div class="stat-label">已完成</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ evaluationTask.failed_questions }}</div>
                <div class="stat-label">失败数</div>
              </div>
            </div>
            
            <div class="progress-section">
              <div class="progress-bar-container">
                <div 
                  class="progress-bar" 
                  :style="{ width: (evaluationTask.progress || 0) + '%' }"
                  :class="{ 
                    success: evaluationTask.status === 'completed', 
                    error: evaluationTask.status === 'failed' 
                  }"
                ></div>
              </div>
              <div class="progress-text">
                {{ evaluationTask.progress || 0 }}%
              </div>
            </div>
          </div>

          <div class="step-actions">
            <button @click="restart" class="btn btn-secondary">重新开始</button>
            <button 
              v-if="evaluationTask.status === 'running'"
              @click="pauseEvaluation" 
              class="btn btn-warning"
            >
              暂停评测
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 评测详情对话框 -->
    <div v-if="showEvaluationDialog" class="modal-overlay" @click="showEvaluationDialog = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>评测详情</h3>
          <button @click="showEvaluationDialog = false" class="modal-close">×</button>
        </div>
        
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
              <div class="evaluation-card">
                <div class="eval-header">
                  <span class="score">{{ evaluation.score }}分</span>                  <span class="eval-type" :class="evaluation.evaluator_type === 'user' ? 'user-eval' : 'llm-eval'">
                    {{ evaluation.evaluator_type === 'user' ? '人工评测' : 'LLM评测' }}
                  </span>
                </div>
                <div v-if="evaluation.feedback" class="feedback">
                  <p><strong>反馈：</strong>{{ evaluation.feedback }}</p>
                </div>
                <div v-if="evaluation.evaluation_criteria" class="criteria">
                  <p><strong>评测标准：</strong>{{ evaluation.evaluation_criteria }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 手动评测表单 -->
          <div class="manual-evaluation">
            <h4>手动评测</h4>
            <div class="form-group">
              <label class="form-label">评分: {{ manualEvaluation.score }}</label>
              <input 
                v-model.number="manualEvaluation.score" 
                type="range" 
                min="0" 
                max="100"
                class="form-range"
              />
            </div>
            <div class="form-group">
              <label class="form-label">评测标准</label>
              <textarea 
                v-model="manualEvaluation.evaluation_criteria" 
                rows="3"
                class="form-textarea"
                placeholder="请输入评测标准..."
              ></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">反馈意见</label>
              <textarea 
                v-model="manualEvaluation.feedback" 
                rows="3"
                class="form-textarea"
                placeholder="请输入反馈意见..."
              ></textarea>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="showEvaluationDialog = false" class="btn btn-secondary">关闭</button>
          <button 
            v-if="selectedAnswer && selectedAnswer.std_question?.question_type === 'choice'"
            @click="autoEvaluate"
            :disabled="autoEvaluating"
            class="btn btn-warning"
          >
            <span v-if="autoEvaluating">⏳ 评测中...</span>
            <span v-else>自动评测</span>
          </button>
          <button 
            @click="submitManualEvaluation"
            :disabled="submittingEvaluation"
            class="btn btn-primary"
          >
            <span v-if="submittingEvaluation">⏳ 提交中...</span>
            <span v-else>提交评测</span>
          </button>        
        </div>
      </div>
    </div>    <!-- 评测进度弹窗 -->
    <div v-if="showProgressDialog" class="modal-overlay" @click="closeProgressDialog">
      <div class="progress-modal-content" @click.stop>        <div class="progress-modal-header">
          <h3 v-if="currentTaskType === 'answer_generation'">🤖 正在生成答案</h3>
          <h3 v-else-if="currentTaskType === 'evaluation'">⚖️ 正在进行评测</h3>
          <h3 v-else>📊 任务进度</h3>
          <button @click="closeProgressDialog" class="modal-close">×</button>
        </div>
        
        <div class="progress-modal-body">
          <div v-if="evaluationTask" class="progress-info">
            <div class="task-info">
              <h4>{{ evaluationTask.task_name || '在线评测任务' }}</h4>
              <div class="status-info">
                <span class="status-badge" :class="getStatusType(evaluationTask.status)">
                  {{ getStatusText(evaluationTask.status) }}
                </span>
              </div>
            </div>

            <!-- 进度条 -->
            <div class="progress-section">
              <div class="progress-stats">
                <div class="stat-item">
                  <span class="stat-label">总题数</span>
                  <span class="stat-value">{{ evaluationTask.total_questions || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">已完成</span>
                  <span class="stat-value">{{ evaluationTask.completed_questions || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">失败数</span>
                  <span class="stat-value">{{ evaluationTask.failed_questions || 0 }}</span>
                </div>
              </div>
              
              <div class="progress-bar-container">
                <div class="progress-bar">
                  <div 
                    class="progress-fill" 
                    :style="{ width: (evaluationTask.progress || 0) + '%' }"
                    :class="{ 
                      'progress-success': evaluationTask.status === 'completed',
                      'progress-error': evaluationTask.status === 'failed'
                    }"
                  ></div>
                </div>
                <div class="progress-text">
                  {{ evaluationTask.progress || 0 }}%
                </div>
              </div>
            </div>

            <!-- 实时信息 -->
            <div v-if="taskProgress" class="real-time-info">
              <div class="info-grid">
                <div class="info-item" v-if="taskProgress.questions_per_minute">
                  <label>处理速度:</label>
                  <span>{{ taskProgress.questions_per_minute.toFixed(1) }}题/分钟</span>
                </div>
                <div class="info-item" v-if="taskProgress.estimated_remaining_time">
                  <label>预计剩余:</label>
                  <span>{{ formatTime(taskProgress.estimated_remaining_time) }}</span>
                </div>
                <div class="info-item" v-if="taskProgress.average_score">
                  <label>平均分数:</label>
                  <span>{{ taskProgress.average_score.toFixed(1) }}分</span>
                </div>
              </div>
            </div>

            <!-- 最新回答预览 -->
            <div v-if="taskProgress && taskProgress.latest_answer" class="latest-answer">
              <div class="answer-preview">
                <h5>最新回答预览</h5>
                <div class="answer-content">
                  {{ taskProgress.latest_answer.substring(0, 100) }}
                  <span v-if="taskProgress.latest_answer.length > 100">...</span>
                </div>
              </div>
            </div>

            <!-- 错误信息 -->
            <div v-if="evaluationTask.status === 'failed' && evaluationTask.error_message" class="error-info">
              <div class="error-card">
                <h5>❌ 评测失败</h5>
                <p>{{ evaluationTask.error_message }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="progress-modal-footer">
          <button @click="backToMarketplaceFromProgress" class="btn btn-secondary">
            返回主界面
          </button>
          <button 
            v-if="evaluationTask && evaluationTask.status === 'running'" 
            @click="pauseEvaluation" 
            class="btn btn-warning"
          >
            暂停评测
          </button>
          <button 
            v-if="evaluationTask && evaluationTask.status === 'completed'" 
            @click="viewResultsFromProgress" 
            class="btn btn-primary"
          >
            查看结果
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { llmEvaluationService } from '@/services/llmEvaluationService'

// 简单的消息提示函数
const showMessage = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
  // 创建消息元素
  const messageEl = document.createElement('div')
  messageEl.className = `message-toast message-${type}`
  messageEl.textContent = message
  messageEl.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 4px;
    color: white;
    font-size: 14px;
    z-index: 9999;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  `
  
  // 设置背景色
  switch (type) {
    case 'success':
      messageEl.style.backgroundColor = '#67c23a'
      break
    case 'error':
      messageEl.style.backgroundColor = '#f56c6c'
      break
    case 'warning':
      messageEl.style.backgroundColor = '#e6a23c'
      break
    default:
      messageEl.style.backgroundColor = '#409eff'
  }
  
  document.body.appendChild(messageEl)
  
  // 显示动画
  setTimeout(() => {
    messageEl.style.transform = 'translateX(0)'
  }, 100)
  
  // 自动消失
  setTimeout(() => {
    messageEl.style.transform = 'translateX(100%)'
    setTimeout(() => {
      document.body.removeChild(messageEl)
    }, 300)
  }, 3000)
}

const route = useRoute()
const router = useRouter()

// 响应式数据
const currentStep = ref(0)
const currentDataset = ref<any>(null)
const availableModels = ref<any[]>([])

// 模型配置
const modelConfig = reactive<{
  model_id: number | null;
  api_key: string;
  temperature: number;
  max_tokens: number;
  top_k: number;
  enable_reasoning: boolean;
}>({
  model_id: null,
  api_key: '',
  temperature: 0.7,
  max_tokens: 2000,
  top_k: 50,
  enable_reasoning: false
})

// 系统Prompt配置（分选择题和文本题）
const systemPromptConfig = reactive({
  choice_system_prompt: '',
  text_system_prompt: ''
})

const activeSystemPromptTab = ref('choice')

// 答案生成选项
const answerGenerationOptions = reactive({
  task_name: '',
  question_limit_type: 'all',
  question_limit: 10,
  concurrent_limit: 5
})

// 答案生成任务
const answerGenerationTask = ref<any>(null)

// 评测配置（分选择题和文本题）
const evaluationConfig = reactive({
  choice_evaluation_prompt: '',
  text_evaluation_prompt: ''
})

const activeEvaluationTab = ref('choice')

// 评测选项
const evaluationOptions = reactive({
  task_name: '',
  question_limit_type: 'all',
  question_limit: 10,
  is_auto_score: true
})

// 评测任务和结果
const evaluationTask = ref<any>(null)
const taskProgress = ref<any>(null)
const llmAnswers = ref<any[]>([])
const starting = ref(false)

// 详细结果数据
const detailedResults = ref<any>(null)
const loadingDetailedResults = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 定时器
let progressTimer: number | null = null

// 对话框相关
const showEvaluationDialog = ref(false)
const showProgressDialog = ref(false) // 新增进度弹窗控制
const currentTaskType = ref<'answer_generation' | 'evaluation'>('answer_generation') // 跟踪当前任务类型
const selectedAnswer = ref<any>(null)
const answerEvaluations = ref<any[]>([])
const autoEvaluating = ref(false)
const submittingEvaluation = ref(false)
const manualEvaluation = reactive({
  score: 80,
  feedback: '',
  evaluation_criteria: ''
})

// 计算属性
const selectedModel = computed(() => {
  return availableModels.value.find(m => m.id === modelConfig.model_id)
})

const isModelConfigValid = computed(() => {
  return modelConfig.model_id !== null && modelConfig.api_key
})

// 获取题目数量统计
const choiceQuestionCount = computed(() => {
  return currentDataset.value?.choice_question_count || 0
})

const textQuestionCount = computed(() => {
  return currentDataset.value?.text_question_count || 0
})

const isSystemPromptValid = computed(() => {
  const hasChoicePrompt = choiceQuestionCount.value === 0 || systemPromptConfig.choice_system_prompt.trim()
  const hasTextPrompt = textQuestionCount.value === 0 || systemPromptConfig.text_system_prompt.trim()
  return hasChoicePrompt && hasTextPrompt
})

const isEvaluationConfigValid = computed(() => {
  const hasChoiceEvaluation = choiceQuestionCount.value === 0 || evaluationConfig.choice_evaluation_prompt.trim()
  const hasTextEvaluation = textQuestionCount.value === 0 || evaluationConfig.text_evaluation_prompt.trim()
  return hasChoiceEvaluation && hasTextEvaluation
})

// 判断答案生成是否完成
const isAnswerGenerationCompleted = computed(() => {
  if (!answerGenerationTask.value) return false
  
  // 如果任务状态是 evaluating_answers，说明答案生成已完成，进入评测阶段
  return answerGenerationTask.value.status === 'evaluating_answers'
})

// 计算步骤锁定状态
const isStepLocked = computed(() => {
  return (stepIndex: number) => {
    // 如果没有恢复的任务，不锁定任何步骤
    if (!evaluationTask.value) return false
    
    const taskStatus = evaluationTask.value.status
      // 根据任务状态确定已完成的步骤
    const completedSteps: number[] = []
      switch (taskStatus) {
      case 'config_prompts':
        completedSteps.push(0) // 参数配置已完成
        break      
      case 'generating_answers':
        completedSteps.push(0, 1) // 参数配置和提示词配置已完成，正在生成答案
        break
      case 'evaluating_answers':
        completedSteps.push(0, 1, 2) // 前三步已完成，答案生成完成，等待评测配置
        break
      case 'completed':
      case 'failed':
      case 'cancelled':
        completedSteps.push(0, 1, 2, 3) // 所有配置步骤已完成
        break
    }
    
    return completedSteps.includes(stepIndex)
  }
})

// 计算步骤是否可编辑
const isStepEditable = computed(() => {
  return (stepIndex: number) => {
    return !isStepLocked.value(stepIndex)
  }
})

const getSampleQuestion = () => {
  if (activeSystemPromptTab.value === 'choice') {
    return {
      type: 'choice',
      question: '以下哪个是JavaScript的正确变量声明方式？',
      options: ['var name;', 'variable name;', 'v name;', 'declare name;']
    }
  } else {
    return {
      type: 'text',
      question: '请解释什么是Docker容器化技术，并说明其主要优点。'
    }
  }
}

const paginatedAnswers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return llmAnswers.value.slice(start, end)
})

// 详细结果分页
const paginatedDetailedAnswers = computed(() => {
  if (!detailedResults.value || !detailedResults.value.detailed_answers) return []
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return detailedResults.value.detailed_answers.slice(start, end)
})

// 费用预估相关计算
const estimatedTokens = computed(() => {
  if (!currentDataset.value || !selectedModel.value) return 0
  
  const avgTokensPerQuestion = 150 // 估算每个问题平均token数
  const questionCount = evaluationOptions.question_limit_type === 'limit' 
    ? evaluationOptions.question_limit 
    : currentDataset.value.question_count
  
  return questionCount * avgTokensPerQuestion
})

const estimatedCost = computed(() => {
  if (!selectedModel.value?.pricing || !estimatedTokens.value) return '0.00'
  
  const inputCost = (estimatedTokens.value / 1000) * (selectedModel.value.pricing.input || 0)
  const outputCost = (estimatedTokens.value / 1000) * (selectedModel.value.pricing.output || 0)
  
  return (inputCost + outputCost).toFixed(2)
})

// 添加一个方法来查看任务进度
const viewTaskProgress = () => {
  if (evaluationTask.value) {
    const status = evaluationTask.value.status
    
    if (status === 'completed') {
      // 已完成 - 直接跳转到结果页面
      currentStep.value = 4
      showMessage('查看评测结果', 'info')
      
    } else if (status === 'generating_answers') {
      // 正在生成答案 - 显示答案生成进度弹窗
      currentTaskType.value = 'answer_generation'
      showProgressDialog.value = true
      startProgressPolling()
      showMessage('查看答案生成进度', 'info')
      
    } else if (status === 'evaluating_answers') {
      // 正在评测 - 显示评测进度弹窗
      currentTaskType.value = 'evaluation'
      showProgressDialog.value = true
      startProgressPolling()
      showMessage('查看评测进度', 'info')
      
    } else if (status === 'failed') {
      // 失败 - 跳转到结果页面显示错误
      currentStep.value = 4
      showMessage('查看任务错误信息', 'error')
      
    } else {
      // 其他状态 - 显示相应的配置阶段
      showMessage('任务当前处于配置阶段', 'info')
    }
  }
}

// 生命周期
onMounted(async () => {
  await initializeView()
})

// 初始化视图
const initializeView = async () => {
  try {
    // 获取路由参数
    const datasetId = route.params.datasetId as string
    const taskId = route.query.taskId as string
    const step = route.query.step as string
    const view = route.query.view as string
    
    if (!datasetId) {
      showMessage('未指定数据集', 'error')
      return
    }
    
    // 加载数据集信息
    await loadDatasetInfo(parseInt(datasetId))
    
    // 加载可用模型和默认prompt
    await Promise.all([
      loadAvailableModels(),
      loadDefaultPrompts()
    ])
    
    // 如果有taskId，说明是从任务列表恢复的
    if (taskId) {
      // 检查是否直接查看结果
      if (view === 'results') {
        await resumeTaskForResults(parseInt(taskId))
      } else {
        await resumeTask(parseInt(taskId))
      }
    } else if (step) {
      // 如果只有step参数，直接跳转到对应步骤
      currentStep.value = parseInt(step) - 1
    }
  } catch (error) {
    console.error('初始化失败:', error)
    showMessage('初始化失败', 'error')
  }
}

// 恢复任务
const resumeTask = async (taskId: number) => {
  try {
    // 从后端获取任务详情
    const task = await llmEvaluationService.getTaskDetail(taskId)
    
    if (!task) {
      showMessage('任务不存在', 'error')
      return
    }
    
    console.log('恢复任务:', task.name, '状态:', task.status)
    
    // 设置evaluationTask用于步骤锁定逻辑
    evaluationTask.value = task
    
    // 恢复任务配置数据
    if (task.model_id) {
      modelConfig.model_id = task.model_id
    }
    if (task.system_prompt) {
      // 根据数据集类型恢复prompt
      if (choiceQuestionCount.value > 0) {
        systemPromptConfig.choice_system_prompt = task.system_prompt
      }
      if (textQuestionCount.value > 0) {
        systemPromptConfig.text_system_prompt = task.system_prompt
      }
    }
    if (task.temperature) {
      modelConfig.temperature = task.temperature
    }
    if (task.max_tokens) {
      modelConfig.max_tokens = task.max_tokens
    }
    if (task.top_k) {
      modelConfig.top_k = task.top_k
    }
    if (typeof task.enable_reasoning === 'boolean') {
      modelConfig.enable_reasoning = task.enable_reasoning
    }
    
    // 恢复评测配置
    if (task.evaluation_prompt) {
      if (choiceQuestionCount.value > 0) {
        evaluationConfig.choice_evaluation_prompt = task.evaluation_prompt
      }
      if (textQuestionCount.value > 0) {
        evaluationConfig.text_evaluation_prompt = task.evaluation_prompt
      }
    }    // 根据任务状态决定显示内容
    if (task.status === 'generating_answers') {
      // 正在生成答案 - 显示第三阶段并弹出答案生成进度弹窗
      currentStep.value = 2
      currentTaskType.value = 'answer_generation'
      showProgressDialog.value = true      
      startProgressPolling()
      showMessage('正在生成答案，请查看进度...', 'info')
      
    } else if (task.status === 'evaluating_answers') {
      // 答案生成完成，进入评测阶段 - 跳转到评测配置步骤
      currentStep.value = 3
      answerGenerationTask.value = task // 设置答案生成任务，用于评测
      showMessage('答案生成已完成，请配置评测参数', 'success')
        } else if (task.status === 'completed') {
      // 已完成 - 跳转到结果页面并加载详细结果
      currentStep.value = 4
      await loadTaskDetailedResults()
      showMessage('任务已完成，查看评测结果', 'success')
      
    } else if (task.status === 'failed') {
      // 失败 - 跳转到结果页面显示错误信息
      currentStep.value = 4
      showMessage('任务执行失败，请查看错误信息', 'error')
      
    } else if (task.status === 'cancelled') {
      // 已取消 - 跳转到结果页面
      currentStep.value = 4
      showMessage('任务已取消', 'warning')
      
    } else if (task.status === 'config_prompts') {
      // 配置提示词阶段 - 跳转到第二阶段
      currentStep.value = 1
      showMessage('继续配置系统Prompt', 'info')
      
    } else {
      // 其他状态（如config_params）- 跳转到第一阶段
      currentStep.value = 0
      showMessage('继续配置模型参数', 'info')
    }
    
    console.log(`任务恢复完成: ${task.name || `任务#${taskId}`}, 当前步骤: ${currentStep.value}`)  } catch (error) {
    console.error('恢复任务失败:', error)
    showMessage('恢复任务失败', 'error')
  }
}

// 恢复任务用于查看结果
const resumeTaskForResults = async (taskId: number) => {
  try {
    // 从后端获取任务详情
    const task = await llmEvaluationService.getTaskDetail(taskId)
    
    if (!task) {
      showMessage('任务不存在', 'error')
      return
    }
    
    console.log('查看任务结果:', task.name, '状态:', task.status)
    
    // 设置evaluationTask
    evaluationTask.value = task
    
    // 直接跳转到结果页面
    currentStep.value = 4
    
    // 根据任务状态加载相应的结果
    if (task.status === 'completed') {
      // 已完成任务，加载详细结果
      await loadTaskDetailedResults()
      showMessage('正在查看评测结果', 'success')
    } else if (task.status === 'failed') {
      // 失败任务，显示错误信息
      showMessage('任务执行失败', 'error')
    } else if (task.status === 'generating_answers' || task.status === 'evaluating_answers') {
      // 正在进行的任务，显示进度
      showMessage('任务正在进行中', 'info')
    } else {
      // 其他状态的任务
      showMessage('任务未完成，无法查看结果', 'warning')
    }
    
    console.log(`结果查看完成: ${task.name || `任务#${taskId}`}`)
  } catch (error) {
    console.error('加载任务结果失败:', error)
    showMessage('加载任务结果失败', 'error')
  }
}

// 加载数据集信息
const loadDatasetInfo = async (datasetId: number) => {
  try {
    currentDataset.value = await llmEvaluationService.getDatasetInfo(datasetId)
  } catch (error) {
    console.error('加载数据集信息失败:', error)
    showMessage('加载数据集信息失败', 'error')
  }
}

// 加载任务结果
const loadResults = async (taskId: number) => {
  try {
    const results = await llmEvaluationService.getTaskResults(taskId)
    // 处理结果数据...
    showMessage('结果加载完成', 'success')
  } catch (error) {
    console.error('加载结果失败:', error)
    showMessage('加载结果失败', 'error')
  }
}

// 方法
const loadAvailableModels = async () => {
  try {
    availableModels.value = await llmEvaluationService.getAvailableModels()
  } catch (error) {
    console.error('加载可用模型失败:', error)
  }
}

const loadDefaultPrompts = async () => {
  try {
    // 从后端API获取prompt模板
    const choiceSystemTemplate = await llmEvaluationService.getPromptTemplate('choice_system_default')
    const textSystemTemplate = await llmEvaluationService.getPromptTemplate('text_system_default')
    const choiceEvaluationTemplate = await llmEvaluationService.getPromptTemplate('choice_evaluation_default')
    const textEvaluationTemplate = await llmEvaluationService.getPromptTemplate('text_evaluation_default')
    
    systemPromptConfig.choice_system_prompt = choiceSystemTemplate.content
    systemPromptConfig.text_system_prompt = textSystemTemplate.content
    evaluationConfig.choice_evaluation_prompt = choiceEvaluationTemplate.content
    evaluationConfig.text_evaluation_prompt = textEvaluationTemplate.content
  } catch (error) {
    console.error('加载默认prompt失败:', error)
    // 使用 llm_config.py 中的默认值作为后备
    systemPromptConfig.choice_system_prompt = '你是一个专业的问答助手。请仔细阅读问题和选项，选择最合适的答案。\n请按照以下格式回答：\n答案：[选项字母]\n解释：[简要说明选择理由]'
    systemPromptConfig.text_system_prompt = '你是一个专业的问答助手。请根据问题提供准确、详细、有用的回答。\n回答要求：\n1. 内容准确，逻辑清晰\n2. 语言简洁明了\n3. 针对问题的核心要点进行回答'
    evaluationConfig.choice_evaluation_prompt = '请评估以下选择题的回答质量：\n\n评估标准：\n1. 答案正确性 (50分)：是否选择了正确的选项\n2. 解释合理性 (30分)：解释是否逻辑清晰、合理\n3. 格式规范性 (20分)：是否按照要求的格式回答\n\n请按照以下JSON格式给出评分：\n{{"score": 85, "reasoning": "答案正确，解释清晰合理，格式规范", "feedback": "回答质量很好，但可以在解释部分提供更多细节"}}'
    evaluationConfig.text_evaluation_prompt = '请根据以下标准评估文本回答质量：\n\n评估标准：\n1. 准确性 (40分)：内容是否正确、符合事实\n2. 完整性 (30分)：是否全面回答了问题的各个方面\n3. 清晰性 (20分)：表达是否清楚、逻辑是否清晰\n4. 实用性 (10分)：回答是否对提问者有帮助\n\n请按照以下JSON格式给出评分：\n{{"score": 85, "reasoning": "内容准确，覆盖全面，表达清晰", "feedback": "很好的回答，建议可以提供更多实例说明"}}'
  }
}

const nextStep = async () => {
  const maxStep = 4  // 总共5步：0-4
  
  // 在进入下一步之前保存当前配置
  await saveCurrentStepConfig()
  
  if (currentStep.value < maxStep) {
    currentStep.value++
  }
}

// 保存当前步骤的配置
const saveCurrentStepConfig = async () => {
  try {
    const step = currentStep.value
    
    // 第二阶段不需要保存任何状态，用户点击"开始生成答案"时才创建任务
    if (step === 2) {
      return // 第三阶段不保存状态
    }
    
    // 只有在有任务ID的情况下才保存
    const taskId = route.query.taskId as string
    if (!taskId) {
      // 对于步骤0和1，不创建任务，只是本地保存配置
      // 任务会在用户点击"开始生成答案"时创建
      return
    }
    
    let statusUpdate: any = {}
    
    switch (step) {
      case 0: // 参数配置步骤
        statusUpdate = {
          status: 'config_prompts',
          model_id: modelConfig.model_id,
          api_key: modelConfig.api_key,
          temperature: modelConfig.temperature,
          max_tokens: modelConfig.max_tokens,
          top_k: modelConfig.top_k,
          enable_reasoning: modelConfig.enable_reasoning
        }
        break
          case 1: // 提示词配置步骤
        statusUpdate = {
          status: 'config_prompts',
          system_prompt: activeSystemPromptTab.value === 'choice' 
            ? systemPromptConfig.choice_system_prompt 
            : systemPromptConfig.text_system_prompt
        }
        break
        
      case 3: // 评测配置步骤
        statusUpdate = {
          status: 'evaluating_answers',
          evaluation_prompt: activeEvaluationTab.value === 'choice' 
            ? evaluationConfig.choice_evaluation_prompt 
            : evaluationConfig.text_evaluation_prompt
        }
        break
        
      default:
        return // 不需要保存
    }
    
    if (Object.keys(statusUpdate).length > 0) {
      await llmEvaluationService.updateTaskStatus(parseInt(taskId), statusUpdate)
      showMessage('配置已保存', 'success')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    showMessage('保存配置失败', 'error')
  }
}

// 这个方法已不再使用 - 任务只在用户点击"开始生成答案"时创建
// const createNewTask = async () => {
//   // 移除了自动创建任务的逻辑
//   // 任务会在startAnswerGeneration()中创建
// }

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// 系统Prompt重置方法
const resetChoicePrompt = async () => {
  try {
    const template = await llmEvaluationService.getPromptTemplate('choice_system_default')
    systemPromptConfig.choice_system_prompt = template.content
    showMessage('已重置为默认选择题系统Prompt', 'success')
  } catch (error) {
    // 使用 llm_config.py 中的默认值
    systemPromptConfig.choice_system_prompt = '你是一个专业的问答助手。请仔细阅读问题和选项，选择最合适的答案。\n请按照以下格式回答：\n答案：[选项字母]\n解释：[简要说明选择理由]'
    showMessage('已重置为默认选择题系统Prompt', 'success')
  }
}

const resetTextPrompt = async () => {
  try {
    const template = await llmEvaluationService.getPromptTemplate('text_system_default')
    systemPromptConfig.text_system_prompt = template.content
    showMessage('已重置为默认文本题系统Prompt', 'success')
  } catch (error) {
    // 使用 llm_config.py 中的默认值
    systemPromptConfig.text_system_prompt = '你是一个专业的问答助手。请根据问题提供准确、详细、有用的回答。\n回答要求：\n1. 内容准确，逻辑清晰\n2. 语言简洁明了\n3. 针对问题的核心要点进行回答'
    showMessage('已重置为默认文本题系统Prompt', 'success')
  }
}

// 评测Prompt重置方法
const resetChoiceEvaluationPrompt = async () => {
  try {
    const template = await llmEvaluationService.getPromptTemplate('choice_evaluation_default')
    evaluationConfig.choice_evaluation_prompt = template.content
    showMessage('已重置为默认选择题评测Prompt', 'success')
  } catch (error) {
    // 使用 llm_config.py 中的默认值
    evaluationConfig.choice_evaluation_prompt = '请评估以下选择题的回答质量：\n\n评估标准：\n1. 答案正确性 (50分)：是否选择了正确的选项\n2. 解释合理性 (30分)：解释是否逻辑清晰、合理\n3. 格式规范性 (20分)：是否按照要求的格式回答\n\n请按照以下JSON格式给出评分：\n{{"score": 85, "reasoning": "答案正确，解释清晰合理，格式规范", "feedback": "回答质量很好，但可以在解释部分提供更多细节"}}'
    showMessage('已重置为默认选择题评测Prompt', 'success')
  }
}

const resetTextEvaluationPrompt = async () => {
  try {
    const template = await llmEvaluationService.getPromptTemplate('text_evaluation_default')
    evaluationConfig.text_evaluation_prompt = template.content
    showMessage('已重置为默认文本题评测Prompt', 'success')
  } catch (error) {
    // 使用 llm_config.py 中的默认值
    evaluationConfig.text_evaluation_prompt = '请根据以下标准评估文本回答质量：\n\n评估标准：\n1. 准确性 (40分)：内容是否正确、符合事实\n2. 完整性 (30分)：是否全面回答了问题的各个方面\n3. 清晰性 (20分)：表达是否清楚、逻辑是否清晰\n4. 实用性 (10分)：回答是否对提问者有帮助\n\n请按照以下JSON格式给出评分：\n{{"score": 85, "reasoning": "内容准确，覆盖全面，表达清晰", "feedback": "很好的回答，建议可以提供更多实例说明"}}'
    showMessage('已重置为默认文本题评测Prompt', 'success')
  }
}

// 开始答案生成
const startAnswerGeneration = async () => {  
  if (!currentDataset.value || !isModelConfigValid.value || !isSystemPromptValid.value) {
    showMessage('请完善配置信息', 'error')
    return
  }
  if (!modelConfig.model_id) {
    showMessage('请选择模型', 'error')
    return
  }
  starting.value = true
  try {    
    console.log('Selected model for answer generation:', selectedModel.value)
    console.log('Model Config:', modelConfig)
    
    // 创建任务数据
    const taskData = {
      task_name: answerGenerationOptions.task_name || `${currentDataset.value.name} - 答案生成`,
      dataset_id: currentDataset.value.id,
      model_config: {
        model_id: modelConfig.model_id!, 
        api_key: modelConfig.api_key,
        system_prompt: systemPromptConfig.choice_system_prompt || systemPromptConfig.text_system_prompt,
        temperature: modelConfig.temperature,
        max_tokens: modelConfig.max_tokens,
        top_k: modelConfig.top_k,
        enable_reasoning: modelConfig.enable_reasoning
      },
      evaluation_config: {
        evaluation_prompt: evaluationConfig.choice_evaluation_prompt || evaluationConfig.text_evaluation_prompt
      },
      is_auto_score: false, // 答案生成阶段不自动评分
      question_limit: answerGenerationOptions.question_limit_type === 'limit' ? answerGenerationOptions.question_limit : undefined
    }
    
    console.log('Task Data to be sent:', JSON.stringify(taskData, null, 2))    // 调用API创建并启动任务
    answerGenerationTask.value = await llmEvaluationService.createEvaluationTask(taskData)
    
    showMessage('答案生成任务已创建，开始生成...', 'success')
    
    // 显示进度弹窗而不是跳转到下一步
    evaluationTask.value = answerGenerationTask.value // 将答案生成任务赋值给评测任务以便进度弹窗使用
    currentTaskType.value = 'answer_generation' // 设置任务类型为答案生成
    showProgressDialog.value = true
    
    // 开始轮询进度
    startProgressPolling()
    
  } catch (error: any) {
    console.error('启动答案生成失败:', error)
    showMessage('启动答案生成失败: ' + error.message, 'error')
  } finally {
    starting.value = false
  }
}

// 开始评测（新的评测阶段）
const startEvaluation = async () => {
  if (!answerGenerationTask.value || !isEvaluationConfigValid.value) {
    showMessage('请完成答案生成并配置评测参数', 'error')
    return  
  }
  starting.value = true
  try {
    // 准备评测配置
    const evalConfig = {
      evaluation_prompt: evaluationConfig.choice_evaluation_prompt || evaluationConfig.text_evaluation_prompt
    }
    
    console.log('启动评测，任务ID:', answerGenerationTask.value.id)
    console.log('评测配置:', evalConfig)
    
    // 调用启动评测接口
    const result = await llmEvaluationService.startTaskEvaluation(
      answerGenerationTask.value.id, 
      evalConfig
    )
    
    showMessage('评测任务已启动...', 'success')
    
    // 更新当前评测任务
    evaluationTask.value = answerGenerationTask.value
    
    // 显示进度弹窗
    currentTaskType.value = 'evaluation'
    showProgressDialog.value = true
    
    // 开始轮询进度
    startProgressPolling()
  } catch (error: any) {
    console.error('启动评测失败:', error)
    showMessage('启动评测失败: ' + error.message, 'error')
  } finally {
    starting.value = false
  }
}

const startProgressPolling = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
  }
  
  progressTimer = setInterval(async () => {
    if (!evaluationTask.value) return
    
    try {
      const progress = await llmEvaluationService.getTaskProgress(evaluationTask.value.id)
      taskProgress.value = progress
        // 更新任务状态
      evaluationTask.value = {
        ...evaluationTask.value,
        ...progress
      }
        // 根据当前任务状态自动识别任务类型（如果未设置）
      if (!currentTaskType.value || currentTaskType.value === 'answer_generation') {
        if (progress.status === 'generating_answers') {
          currentTaskType.value = 'answer_generation'
        } else if (progress.status === 'evaluating_answers') {
          currentTaskType.value = 'evaluation'
        }
      }
          // 如果任务完成，停止轮询并加载结果
      if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'answers_generated') {
        clearInterval(progressTimer!)
        progressTimer = null
        if (progress.status === 'completed') {
          // 根据任务类型决定下一步操作
          if (currentTaskType.value === 'answer_generation') {
            showMessage('答案生成完成！', 'success')
            // 关闭进度弹窗并跳转到评测配置步骤（第四阶段，索引为3）
            showProgressDialog.value = false
            currentStep.value = 3 // 跳转到评测配置步骤
          } else {
            await loadTaskResults()
            showMessage('评测任务完成！', 'success')
            // 关闭进度弹窗并跳转到结果页面
            showProgressDialog.value = false
            currentStep.value = 4 // 直接跳转到结果页面
          }
        } else if (progress.status === 'answers_generated') {
          // 答案生成完成，等待评测配置
          showMessage('答案生成完成！请配置评测参数', 'success')
          answerGenerationTask.value = evaluationTask.value // 保存答案生成任务
          // 关闭进度弹窗并跳转到评测配置步骤
          showProgressDialog.value = false
          currentStep.value = 3 // 跳转到评测配置步骤
        } else {
          const taskName = currentTaskType.value === 'answer_generation' ? '答案生成' : '评测'
          showMessage(`${taskName}任务失败`, 'error')
          showProgressDialog.value = false
          currentStep.value = 4 // 跳转到结果页面显示错误
        }
      }
    } catch (error) {
      console.error('获取进度失败:', error)
    }
  }, 2000) // 每2秒轮询一次
}

const loadTaskResults = async () => {
  if (!evaluationTask.value) return
  
  try {
    const results = await llmEvaluationService.getTaskResults(evaluationTask.value.id)
    llmAnswers.value = results.answers || []
  } catch (error) {
    console.error('加载评测结果失败:', error)
  }
}

const loadTaskDetailedResults = async () => {
  if (!evaluationTask.value) return
  
  loadingDetailedResults.value = true
  try {
    detailedResults.value = await llmEvaluationService.getTaskDetailedResults(evaluationTask.value.id)
    llmAnswers.value = detailedResults.value.detailed_answers || []
  } catch (error) {
    console.error('加载详细结果失败:', error)
    showMessage('加载详细结果失败', 'error')
  } finally {
    loadingDetailedResults.value = false
  }
}

const pauseEvaluation = async () => {
  if (!evaluationTask.value) return
  
  try {
    if (evaluationTask.value.status === 'running') {
      await llmEvaluationService.cancelEvaluationTask(evaluationTask.value.id)
      showMessage('评测已暂停', 'success')
    }
  } catch (error) {
    console.error('暂停评测失败:', error)
    showMessage('暂停评测失败', 'error')
  }
}

const backToMarketplace = () => {
  router.push('/llm-marketplace')
}

// 进度弹窗相关方法
const closeProgressDialog = () => {
  showProgressDialog.value = false
}

const backToMarketplaceFromProgress = () => {
  // 停止轮询
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
  
  // 关闭弹窗并返回市场
  showProgressDialog.value = false
  router.push('/llm-marketplace')
}

const viewResultsFromProgress = () => {
  // 关闭进度弹窗并跳转到结果页面
  showProgressDialog.value = false
  nextStep() // 跳转到结果页面
}

const getStatusType = (status: string) => {
  const normalizedStatus = status.toUpperCase()
  switch (normalizedStatus) {
    case 'GENERATING_ANSWERS':
    case 'EVALUATING_ANSWERS': return 'primary'
    case 'ANSWERS_GENERATED': return 'success'
    case 'COMPLETED': return 'success'
    case 'FAILED': return 'danger'
    case 'CANCELLED': return 'warning'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  const normalizedStatus = status.toUpperCase()
  switch (normalizedStatus) {
    case 'GENERATING_ANSWERS': return '生成答案中'
    case 'ANSWERS_GENERATED': return '答案已生成'
    case 'EVALUATING_ANSWERS': return '评测中'
    case 'COMPLETED': return '已完成'
    case 'FAILED': return '失败'
    case 'CANCELLED': return '已取消'
    case 'CONFIG_PARAMS': return '配置参数'
    case 'CONFIG_PROMPTS': return '配置提示词'
    default: return status || '未知'
  }
}

const formatTime = (seconds: number | undefined) => {
  if (!seconds) return '-'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 格式化日期时间
const formatDateTime = (dateString: string | null) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取分数样式类
const getScoreClass = (score: number | null) => {
  if (!score) return 'score-none'
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  if (score >= 40) return 'score-fair'
  return 'score-poor'
}

const getQuestionTypeText = (type: string) => {
  return type === 'choice' ? '选择题' : '文本题'
}

const getAverageScore = (evaluations: any[]) => {
  if (!evaluations || evaluations.length === 0) return '-'
  const sum = evaluations.reduce((acc, evaluation) => acc + evaluation.score, 0)
  return (sum / evaluations.length).toFixed(1)
}

// 查看详细评测结果
const viewDetailedEvaluation = (answer: any) => {
  selectedAnswer.value = answer
  answerEvaluations.value = answer.evaluations || []
  showEvaluationDialog.value = true
}

// 下载详细结果
const downloadDetailedResults = async () => {
  if (!evaluationTask.value) return
  
  try {
    const results = await llmEvaluationService.downloadTaskResults(evaluationTask.value.id, {
      format: 'json',
      include_raw_responses: true,
      include_prompts: true
    })
    
    const blob = new Blob([JSON.stringify(results, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `detailed_results_${evaluationTask.value.id}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    showMessage('详细结果下载完成', 'success')
  } catch (error) {
    console.error('下载失败:', error)
    showMessage('下载失败', 'error')
  }
}

// 下载答案数据
const downloadAnswersOnly = async () => {
  if (!detailedResults.value) return
  
  try {
    const answersData = detailedResults.value.detailed_answers.map((answer: any) => ({
      question_id: answer.question_id,
      question_text: answer.question_text,
      question_type: answer.question_type,
      llm_answer: answer.llm_answer.answer,
      is_valid: answer.llm_answer.is_valid,      evaluations: answer.evaluations.map((evaluation: any) => ({
        score: evaluation.score,
        reasoning: evaluation.reasoning,
        feedback: evaluation.feedback,
        evaluator_type: evaluation.evaluator_type
      })),
      average_score: answer.average_score
    }))
    
    const blob = new Blob([JSON.stringify(answersData, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `answers_${evaluationTask.value.id}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    showMessage('答案数据下载完成', 'success')
  } catch (error) {
    console.error('下载失败:', error)
    showMessage('下载失败', 'error')
  }
}

// 自动评测
const autoEvaluate = async () => {
  showMessage('自动评测功能正在开发中', 'info')
}

// 提交手动评测
const submitManualEvaluation = async () => {
  showMessage('手动评测功能正在开发中', 'info')
}

// 加载答案评测结果
const loadAnswerEvaluations = async (answerId: number) => {
  // 简化实现，直接使用现有数据
  console.log('加载答案评测结果', answerId)
}

// 重新开始
const restart = () => {
  // 重置所有状态
  currentStep.value = 0
  evaluationTask.value = null
  detailedResults.value = null
  llmAnswers.value = []
  showMessage('已重置，可以重新开始', 'info')
}

// 下载结果（简单版本）
const downloadResults = async () => {
  if (!evaluationTask.value) return
  
  try {
    const results = await llmEvaluationService.downloadTaskResults(evaluationTask.value.id, {
      format: 'json',
      include_raw_responses: false,
      include_prompts: false
    })
    
    const blob = new Blob([JSON.stringify(results, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `results_${evaluationTask.value.id}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    showMessage('结果下载完成', 'success')
  } catch (error) {
    console.error('下载失败:', error)
    showMessage('下载失败', 'error')
  }
}
</script>

<style scoped>
/* 全局样式 */
.llm-evaluation {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  padding: 20px;
}

/* 顶部标题栏 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px 0;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.back-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 28px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.progress-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.progress-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 步骤指示器 */
.steps-container {
  margin-bottom: 30px;
}

.steps-wrapper {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  border-radius: 10px;
  transition: all 0.3s ease;
  position: relative;
  min-width: 120px;
}

.step-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.step-item.locked {
  opacity: 0.6;
  background: #f8f9fa;
  color: #6c757d;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.2);
}

.step-item.active .step-number {
  background: rgba(255, 255, 255, 0.3);
}

.step-title {
  font-size: 13px;
  font-weight: 500;
  text-align: center;
  line-height: 1.2;
}

/* 步骤内容 */
.step-content {
  max-width: 1000px;
  margin: 0 auto;
}

.content-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.content-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
}

.card-header h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 24px;
  font-weight: 600;
}

.card-header p {
  margin: 0;
  color: #6c757d;
  font-size: 16px;
}

/* 数据集摘要 */
.dataset-summary {
  margin-bottom: 30px;
}

.summary-card {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #90caf9;
}

.summary-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.summary-info h4 {
  margin: 0 0 8px 0;
  color: #1565c0;
  font-size: 18px;
  font-weight: 600;
}

.summary-info p {
  margin: 0 0 12px 0;
  color: #1976d2;
  font-size: 14px;
  line-height: 1.4;
}

.summary-tags {
  display: flex;
  gap: 8px;
}

.tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.8);
  color: #1565c0;
  border: 1px solid rgba(21, 101, 192, 0.2);
}

.tag-success {
  background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
  color: #2e7d32;
  border-color: #4caf50;
}

/* 配置区域 */
.config-section {
  margin-bottom: 30px;
}

.config-section h4 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e9ecef;
}

/* 表单样式 */
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  color: #495057;
  font-weight: 500;
  font-size: 14px;
}

.required {
  color: #dc3545;
}

.form-input,
.form-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: white;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled,
.form-select:disabled {
  background: #f8f9fa;
  color: #6c757d;
  cursor: not-allowed;
}

.form-range {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e9ecef;
  outline: none;
  -webkit-appearance: none;
}

.form-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.form-range::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #6c757d;
}

.form-checkbox {
  margin-right: 8px;
  transform: scale(1.2);
}

.form-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
}

/* 模型详情 */
.model-details {
  margin-top: 15px;
}

.alert {
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid;
  font-size: 14px;
  line-height: 1.4;
}

.alert-info {
  background: #e3f2fd;
  border-left-color: #2196f3;
  color: #1565c0;
}

/* 数据集分析 */
.dataset-analysis {
  margin-bottom: 30px;
}

.dataset-analysis h4 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.type-analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.analysis-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  border: 1px solid #dee2e6;
  transition: all 0.3s ease;
}

.analysis-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.analysis-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 10px;
}

.analysis-icon {
  font-size: 24px;
}

.analysis-title {
  margin: 0;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
}

.analysis-count {
  font-size: 28px;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 5px;
}

.analysis-desc {
  font-size: 12px;
  color: #6c757d;
  margin: 0;
}

/* Prompt配置 */
.prompt-container {
  margin-bottom: 30px;
}

.tabs {
  display: flex;
  gap: 2px;
  margin-bottom: 20px;
  background: #e9ecef;
  border-radius: 8px;
  padding: 4px;
}

.tab-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: transparent;
  color: #6c757d;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.tab-button.active {
  background: white;
  color: #667eea;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.prompt-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e9ecef;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #dee2e6;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left .icon {
  font-size: 20px;
}

.header-left h4 {
  margin: 0 0 5px 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.header-left p {
  margin: 0;
  color: #6c757d;
  font-size: 13px;
}

.prompt-editor {
  position: relative;
}

.prompt-textarea {
  width: 100%;
  min-height: 200px;
  padding: 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: white;
  transition: all 0.3s ease;
}

.prompt-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.editor-info {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.char-count {
  font-size: 12px;
  color: #6c757d;
}

/* Prompt预览 */
.prompt-preview {
  margin-bottom: 30px;
}

.prompt-preview h4 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.preview-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: #f8f9fa;
}

.message-item.system {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
}

.message-item.user {
  background: #f3e5f5;
  border-left: 4px solid #9c27b0;
}

.message-label {
  font-size: 12px;
  font-weight: 600;
  color: #6c757d;
  min-width: 60px;
}

.message-content {
  flex: 1;
  font-size: 14px;
  line-height: 1.5;
  color: #495057;
  white-space: pre-wrap;
}

/* 生成选项 */
.generation-options {
  margin-bottom: 30px;
}

.generation-options h4 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.option-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-item label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
}

/* 步骤操作 */
.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
}

/* 基础按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
  white-space: nowrap;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn:active {
  transform: translateY(0);
}

.btn.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn.btn-success {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
}

.btn.btn-secondary {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
  color: #4a5568;
}

.btn.btn-info {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
}

.btn.btn-warning {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  color: white;
}

.btn.btn-danger {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
  color: white;
}

.btn.btn-small {
  padding: 8px 16px;
  font-size: 12px;
  border-radius: 6px;
}

.btn.btn-large {
  padding: 16px 32px;
  font-size: 16px;
  border-radius: 10px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.btn:disabled:hover {
  transform: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 进度弹窗 */
.progress-dialog {
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
  backdrop-filter: blur(5px);
}

.progress-content {
  background: white;
  border-radius: 16px;
  padding: 30px;
  max-width: 500px;
  width: 90%;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.progress-header {
  margin-bottom: 20px;
}

.progress-header h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
}

.progress-status {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 20px;
}

.progress-status.status-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.progress-status.status-success {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
}

.progress-status.status-danger {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
  color: white;
}

.progress-status.status-warning {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  color: white;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 15px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  font-size: 14px;
  color: #6c757d;
}

.progress-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* 结果页面样式 */
.results-container {
  max-width: 1200px;
  margin: 0 auto;
}

.task-info-section,
.configuration-section,
.prompts-section,
.statistics-section,
.detailed-answers-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.task-info-section:hover,
.configuration-section:hover,
.prompts-section:hover,
.statistics-section:hover,
.detailed-answers-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
}

.section-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
}

.section-icon {
  font-size: 24px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  border: 1px solid #dee2e6;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #6c757d;
  font-weight: 500;
}

/* 详细结果表格 */
.detailed-results {
  margin-top: 20px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.results-table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
}

.results-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e9ecef;
  font-size: 14px;
  color: #495057;
}

.results-table tr:hover {
  background: #f8f9fa;
}

.results-table tr:last-child td {
  border-bottom: none;
}

/* 分数样式 */
.score-value {
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.score-value:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.score-value.score-excellent {
  background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
  color: #22543d;
  border: 1px solid #68d391;
}

.score-value.score-good {
  background: linear-gradient(135deg, #bee3f8 0%, #90cdf4 100%);
  color: #2a4365;
  border: 1px solid #63b3ed;
}

.score-value.score-fair {
  background: linear-gradient(135deg, #feebc8 0%, #fbd38d 100%);
  color: #744210;
  border: 1px solid #f6ad55;
}

.score-value.score-poor {
  background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
  color: #742a2a;
  border: 1px solid #fc8181;
}

.score-value.score-none {
  background: #f7fafc;
  color: #a0aec0;
  border: 1px solid #e2e8f0;
}

.evaluator-type {
  font-size: 10px;
  color: #718096;
  background: #f1f5f9;
  padding: 2px 4px;
  border-radius: 3px;
}

.average-score {
  font-size: 11px;
  color: #4a5568;
  font-weight: 600;
  padding-top: 4px;
  border-top: 1px solid #e2e8f0;
  margin-top: 4px;
}

.no-score {
  color: #a0aec0;
  font-style: italic;
  font-size: 12px;
}

/* 分页控件 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.pagination-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.page-info {
  color: #4a5568;
  font-size: 14px;
  margin: 0 12px;
}

.page-size-select {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  font-size: 12px;
  color: #4a5568;
}

.total-info {
  color: #718096;
  font-size: 12px;
}

/* 操作按钮部分 */
.result-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
}

/* 动画效果 */
.detailed-results > * {
  animation: fadeInUp 0.6s ease-out;
}

.detailed-results > *:nth-child(1) {
  animation-delay: 0.1s;
}

.detailed-results > *:nth-child(2) {
  animation-delay: 0.2s;
}

.detailed-results > *:nth-child(3) {
  animation-delay: 0.3s;
}

.detailed-results > *:nth-child(4) {
  animation-delay: 0.4s;
}

.detailed-results > *:nth-child(5) {
  animation-delay: 0.5s;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 卡片悬浮效果 */
.task-info-section,
.configuration-section,
.prompts-section,
.statistics-section,
.detailed-answers-section {
  transition: all 0.3s ease;
}

.task-info-section:hover,
.configuration-section:hover,
.prompts-section:hover,
.statistics-section:hover,
.detailed-answers-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}
</style>
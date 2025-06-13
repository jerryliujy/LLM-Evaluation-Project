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
        <div class="step-item" :class="{ active: currentStep === 0 }">
          <span class="step-number">1</span>
          <span class="step-title">配置模型</span>
        </div>
        <div class="step-item" :class="{ active: currentStep === 1 }">
          <span class="step-number">2</span>
          <span class="step-title">配置系统Prompt</span>
        </div>
        <div class="step-item" :class="{ active: currentStep === 2 }">
          <span class="step-number">3</span>
          <span class="step-title">生成回答</span>
        </div>
        <div class="step-item" :class="{ active: currentStep === 3 }">
          <span class="step-number">4</span>
          <span class="step-title">配置评测</span>
        </div>
        <div class="step-item" :class="{ active: currentStep === 4 }">
          <span class="step-number">5</span>
          <span class="step-title">查看结果</span>
        </div>
      </div>
    </div>    <!-- 步骤1: 模型配置 -->
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
              </label>              
              <select 
                v-model="modelConfig.model_id" 
                class="form-select"
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
              <label class="form-label">API Key <span class="required">*</span></label>
              <input 
                v-model="modelConfig.api_key" 
                type="password" 
                class="form-input"
                placeholder="请输入您的API Key"
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
              <label class="form-label">最大Token数</label>
              <input 
                v-model.number="modelConfig.max_tokens" 
                type="number" 
                min="100" 
                max="8000" 
                step="100"
                class="form-input"
              />
              <div class="form-tip">
                ℹ️ 建议设置为2000-4000，确保回答完整
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">Top-K采样: {{ modelConfig.top_k }}</label>
              <input 
                v-model.number="modelConfig.top_k" 
                type="range" 
                min="1" 
                max="100" 
                step="1"
                class="form-range"
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
              <label class="form-label">
                <input 
                  v-model="modelConfig.enable_reasoning" 
                  type="checkbox"
                  class="form-checkbox"
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
            
            <div class="prompt-editor">
              <textarea
                v-model="systemPromptConfig.choice_system_prompt"
                rows="12"
                placeholder="请输入选择题系统Prompt..."
                class="prompt-textarea"
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
            
            <div class="prompt-editor">
              <textarea
                v-model="systemPromptConfig.text_system_prompt"
                rows="12"
                placeholder="请输入文本题系统Prompt..."
                class="prompt-textarea"
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
          <p>使用配置的模型和系统Prompt生成题目答案</p>        </div>
        
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
              />
            </div>
            
            <div class="option-item">
              <label>题目限制</label>
              <select v-model="answerGenerationOptions.question_limit_type" class="form-select">
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
          </button>
          <button @click="startAnswerGeneration" :disabled="!isSystemPromptValid || starting" class="btn btn-primary">
            <span v-if="starting">⏳ 生成中...</span>
            <span v-else>🚀 开始生成答案</span>
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
            
            <div class="prompt-editor">
              <textarea
                v-model="evaluationConfig.choice_evaluation_prompt"
                rows="12"
                placeholder="请输入选择题评测Prompt..."
                class="prompt-textarea"
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
    </div>    <!-- 步骤5: 查看结果 -->
    <div v-if="currentStep === 4" class="step-content">
      <div class="content-card">
        <div class="card-header">
          <h3>▶️ 准备开始评测</h3>
          <p>确认配置信息并启动在线评测任务</p>
        </div>
        
        <!-- 配置摘要 -->
        <div class="config-summary-section">
          <h4>📋 配置摘要</h4>
          <div class="summary-grid">
            <div class="summary-item-card">
              <div class="summary-item">
                <div class="summary-icon">
                  📁
                </div>
                <div class="summary-details">
                  <h5>数据集</h5>
                  <p>{{ currentDataset?.name }}</p>
                  <div class="summary-meta">
                    <span class="tag">{{ currentDataset?.question_count }} 题</span>
                    <span class="tag tag-success">v{{ currentDataset?.version }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="summary-item-card">
              <div class="summary-item">
                <div class="summary-icon">
                  💻
                </div>
                <div class="summary-details">
                  <h5>模型</h5>
                  <p>{{ selectedModel?.display_name }}</p>
                  <div class="summary-meta">
                    <span class="tag">{{ selectedModel?.provider }}</span>
                    <span class="tag tag-info">{{ modelConfig.max_tokens }} tokens</span>
                  </div>
                </div>
              </div>
            </div>            <div class="summary-item-card">
              <div class="summary-item">
                <div class="summary-icon">
                  🛠️
                </div>                <div class="summary-details">
                  <h5>参数配置</h5>
                  <p>温度: {{ modelConfig.temperature }} | Top-K: {{ modelConfig.top_k }}</p>
                  <div class="summary-meta">
                    <span v-if="modelConfig.enable_reasoning" class="tag tag-warning">推理模式</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 评测选项 -->
        <div class="evaluation-options-section">
          <h4>⚙️ 评测选项</h4>
          <div class="options-card">
            <div class="form-group">
              <label class="form-label">任务名称</label>
              <input 
                v-model="evaluationOptions.task_name" 
                type="text"
                class="form-input"
                placeholder="为这次评测起个名称（可选）"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">评测范围</label>
              <div class="range-options">
                <div class="radio-group">
                  <label class="radio-option">
                    <input 
                      type="radio" 
                      v-model="evaluationOptions.question_limit_type" 
                      value="all"
                    />
                    <span>📋 全部问题</span>
                  </label>
                  <label class="radio-option">
                    <input 
                      type="radio" 
                      v-model="evaluationOptions.question_limit_type" 
                      value="limit"
                    />
                    <span>🔢 限制数量</span>
                  </label>
                </div>
                <input 
                  v-if="evaluationOptions.question_limit_type === 'limit'"
                  v-model.number="evaluationOptions.question_limit"
                  type="number"
                  :min="1"
                  :max="currentDataset?.question_count"
                  class="form-input limit-input"
                />
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">自动评分</label>
              <div class="auto-score-option">
                <label class="switch">
                  <input 
                    type="checkbox" 
                    v-model="evaluationOptions.is_auto_score"
                  />
                  <span class="slider"></span>
                </label>
                <div class="option-description">
                  ℹ️ 开启后将自动对选择题进行评分，文本题可手动评分
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 费用预估 -->
        <div class="cost-estimation" v-if="selectedModel && selectedModel.pricing">
          <h4>💰 费用预估</h4>
          <div class="cost-card">
            <div class="cost-details">
              <div class="cost-item">
                <span>预计Token消耗:</span>
                <span>{{ estimatedTokens }} tokens</span>
              </div>
              <div class="cost-item">
                <span>预估费用:</span>
                <span class="cost-value">¥ {{ estimatedCost }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="step-actions">
          <button @click="prevStep" class="btn btn-secondary">
            ← 上一步
          </button>
          <button @click="startEvaluation" :disabled="starting" class="btn btn-primary start-btn">
            <span v-if="starting">⏳ 启动中...</span>
            <span v-else>▶️ 开始评测</span>
          </button>
        </div>
      </div>
    </div>    <!-- 步骤5: 评测结果和进度 -->
    <div v-if="currentStep === 4" class="step-content">
      <div class="evaluation-results">
        <h3>评测进度和结果</h3>
        
        <!-- 可以随时返回市场 -->
        <div class="top-actions">
          <button @click="backToMarketplace" class="btn btn-secondary">返回数据集市场</button>
          <button v-if="evaluationTask" @click="pauseEvaluation" class="btn" :class="evaluationTask.status === 'running' ? 'btn-warning' : 'btn-primary'">
            {{ evaluationTask.status === 'running' ? '暂停评测' : '继续评测' }}
          </button>
        </div>

        <!-- 评测进度 -->
        <div v-if="evaluationTask" class="progress-summary">
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
                <div class="stat-value">{{ evaluationTask.current_question }}</div>
                <div class="stat-label">当前进度</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ evaluationTask.successful_count }}</div>
                <div class="stat-label">成功数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ evaluationTask.failed_count }}</div>
                <div class="stat-label">失败数</div>
              </div>
            </div>
            
            <!-- 进度条 -->
            <div class="progress-section">
              <div class="progress-bar-container">
                <div 
                  class="progress-bar" 
                  :style="{ width: Math.round((evaluationTask.current_question / evaluationTask.total_questions) * 100) + '%' }"
                  :class="{ 
                    success: evaluationTask.status === 'completed', 
                    error: evaluationTask.status === 'failed' 
                  }"
                ></div>
              </div>
              <div class="progress-text">
                {{ Math.round((evaluationTask.current_question / evaluationTask.total_questions) * 100) }}%
              </div>
            </div>
            
            <!-- 实时信息 -->
            <div v-if="taskProgress" class="real-time-info">
              <div class="info-grid">
                <div class="info-item">
                  <label>平均分数:</label>
                  <span>{{ taskProgress.average_score ? taskProgress.average_score.toFixed(1) : '-' }}分</span>
                </div>
                <div class="info-item">
                  <label>处理速度:</label>
                  <span>{{ taskProgress.questions_per_minute || '-' }}题/分钟</span>
                </div>
                <div class="info-item">
                  <label>预计剩余:</label>
                  <span>{{ formatTime(taskProgress.estimated_remaining_time) }}</span>
                </div>
              </div>
            </div>
          </div>        
        </div>

        <!-- 最新回答预览 -->
        <div v-if="taskProgress && taskProgress.latest_answer" class="latest-answer">
          <div class="answer-card">
            <div class="latest-header">
              <h4>最新回答</h4>
              <span v-if="taskProgress.latest_score !== undefined" class="score-tag">
                {{ taskProgress.latest_score }}分
              </span>
            </div>
            <div class="answer-preview">
              {{ taskProgress.latest_answer }}
            </div>
          </div>
        </div>

        <!-- 答案列表 (评测完成后显示) -->
        <div v-if="evaluationTask && evaluationTask.status === 'completed' && llmAnswers.length > 0" class="answers-list">
          <h4>回答详情</h4>
          <div class="table-container">
            <table class="answers-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>问题</th>
                  <th>模型回答</th>
                  <th>评分</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="answer in paginatedAnswers" :key="answer.id">
                  <td>{{ answer.id }}</td>
                  <td class="question-cell">
                    <div class="question-text">{{ answer.std_question?.body || '未知问题' }}</div>
                    <span class="question-type">{{ getQuestionTypeText(answer.std_question?.question_type) }}</span>
                  </td>
                  <td class="answer-cell">
                    {{ answer.answer }}
                  </td>
                  <td>
                    <span v-if="answer.evaluations && answer.evaluations.length > 0">
                      {{ getAverageScore(answer.evaluations) }}分
                    </span>
                    <span v-else>-</span>
                  </td>
                  <td>
                    <button @click="viewEvaluation(answer)" class="btn btn-small btn-info">查看详情</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 分页 -->
          <div class="pagination">
            <select v-model="pageSize" class="page-size-select">
              <option value="10">10/页</option>
              <option value="20">20/页</option>
              <option value="50">50/页</option>
              <option value="100">100/页</option>
            </select>
            
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
                第 {{ currentPage }} 页，共 {{ Math.ceil(llmAnswers.length / pageSize) }} 页
              </span>
              <button 
                @click="currentPage++" 
                :disabled="currentPage >= Math.ceil(llmAnswers.length / pageSize)"
                class="btn btn-small btn-secondary"
              >
                下一页
              </button>
              <button 
                @click="currentPage = Math.ceil(llmAnswers.length / pageSize)" 
                :disabled="currentPage >= Math.ceil(llmAnswers.length / pageSize)"
                class="btn btn-small btn-secondary"
              >
                末页
              </button>
            </div>
            
            <div class="total-info">
              共 {{ llmAnswers.length }} 条记录
            </div>
          </div>
        </div>

        <div class="step-actions">
          <button @click="restart" class="btn btn-secondary">重新开始</button>
          <button 
            v-if="evaluationTask && evaluationTask.status === 'completed'"
            @click="downloadResults"
            class="btn btn-success"
          >
            下载结果
          </button>
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
                  <span class="score">{{ evaluation.score }}分</span>
                  <span class="eval-type" :class="evaluation.evaluator_type === 'user' ? 'user-eval' : 'auto-eval'">
                    {{ evaluation.evaluator_type === 'user' ? '人工评测' : '自动评测' }}
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
          </button>        </div>
      </div>
    </div>    <!-- 评测进度弹窗 -->
    <div v-if="showProgressDialog" class="modal-overlay" @click="closeProgressDialog">
      <div class="progress-modal-content" @click.stop>
        <div class="progress-modal-header">
          <h3 v-if="currentTaskType === 'answer_generation'">🤖 答案生成中</h3>
          <h3 v-else>⚖️ 评分进行中</h3>
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
                <div v-if="taskProgress.latest_score !== undefined" class="answer-score">
                  得分: {{ taskProgress.latest_score }}分
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
const manualEvaluation = reactive({
  score: 80,
  evaluation_criteria: '',
  feedback: ''
})
const autoEvaluating = ref(false)
const submittingEvaluation = ref(false)

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
    // 如果任务已完成，直接跳转到结果页面
    if (evaluationTask.value.status === 'completed') {
      currentStep.value = 4
    } else {
      // 否则显示进度弹窗
      showProgressDialog.value = true
      // 如果任务正在运行，开始轮询进度
      if (evaluationTask.value.status === 'running') {
        startProgressPolling()
      }
    }
  }
}

// 生命周期
onMounted(async () => {
  // 检查是否从路由传递了数据集ID
  if (route.params.datasetId) {
    try {
      // 直接获取指定的数据集信息，而不是获取所有数据集列表
      const datasetId = parseInt(route.params.datasetId as string)
      const dataset = await llmEvaluationService.getMarketplaceDataset(datasetId)
      if (dataset) {
        currentDataset.value = dataset
        // 如果从数据集市场进入，设置初始步骤
        currentStep.value = 0
      }
    } catch (error) {
      console.error('加载数据集失败:', error)
      showMessage('加载数据集失败，请检查数据集是否存在', 'error')
    }
  }
  
  // 加载数据
  await Promise.all([
    loadAvailableModels(),
    loadDefaultPrompts()
  ])
})

onUnmounted(() => {
  if (progressTimer) {
    clearInterval(progressTimer)
  }
})

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

const nextStep = () => {
  const maxStep = 4  // 总共5步：0-4
  if (currentStep.value < maxStep) {
    currentStep.value++
  }
}

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

  if (!modelConfig.model_id) {
    showMessage('请选择模型', 'error')
    return
  }

  starting.value = true
  try {
    console.log('Selected model:', selectedModel.value)
    console.log('Model ID:', modelConfig.model_id)
    console.log('Model Config:', modelConfig)
    
    const taskData = {
      task_name: evaluationOptions.task_name || `${currentDataset.value.name} - 评测`,
      dataset_id: currentDataset.value.id,
      model_config: {
        model_id: modelConfig.model_id!,  // 使用非空断言，因为前面已经验证过
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
      is_auto_score: evaluationOptions.is_auto_score,
      question_limit: evaluationOptions.question_limit_type === 'limit' ? evaluationOptions.question_limit : undefined
    }
    
    console.log('Evaluation Task Data to be sent:', JSON.stringify(taskData, null, 2))    
    evaluationTask.value = await llmEvaluationService.createEvaluationTask(taskData)
    
    showMessage('评测任务已创建，开始评测...', 'success')
    
    // 显示进度弹窗而不是跳转到下一步
    currentTaskType.value = 'evaluation' // 设置任务类型为评分
    showProgressDialog.value = true
    
    // 开始轮询进度
    startProgressPolling()
  } catch (error: any) {
    console.error('创建评测任务失败:', error)
    showMessage('创建评测任务失败: ' + error.message, 'error')
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
        // 如果任务完成，停止轮询并加载结果
      if (progress.status === 'completed' || progress.status === 'failed') {
        clearInterval(progressTimer!)
        progressTimer = null
        
        if (progress.status === 'completed') {
          // 根据任务类型决定下一步操作
          if (currentTaskType.value === 'answer_generation') {
            showMessage('答案生成完成！', 'success')
            // 关闭进度弹窗并跳转到评测配置步骤
            showProgressDialog.value = false
            nextStep() // 跳转到评测配置步骤（步骤3）
          } else {
            await loadTaskResults()
            showMessage('评测任务完成！', 'success')
            // 关闭进度弹窗并跳转到结果页面
            showProgressDialog.value = false
            nextStep() // 跳转到结果页面
          }
        } else {
          const taskName = currentTaskType.value === 'answer_generation' ? '答案生成' : '评测'
          showMessage(`${taskName}任务失败`, 'error')
          showProgressDialog.value = false
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
  switch (status) {
    case 'RUNNING': return 'primary'
    case 'COMPLETED': return 'success'
    case 'FAILED': return 'danger'
    case 'PAUSED': return 'warning'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'RUNNING': return '运行中'
    case 'COMPLETED': return '已完成'
    case 'FAILED': return '失败'
    case 'PAUSED': return '已暂停'
    case 'PENDING': return '等待中'
    default: return '未知'
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

const getQuestionTypeText = (type: string) => {
  return type === 'choice' ? '选择题' : '文本题'
}

const getAverageScore = (evaluations: any[]) => {
  if (!evaluations || evaluations.length === 0) return '-'
  const sum = evaluations.reduce((acc, evaluation) => acc + evaluation.score, 0)
  return (sum / evaluations.length).toFixed(1)
}

const viewEvaluation = (answer: any) => {
  selectedAnswer.value = answer
  answerEvaluations.value = answer.evaluations || []
  
  // 重置手动评测表单
  manualEvaluation.score = 80
  manualEvaluation.evaluation_criteria = ''
  manualEvaluation.feedback = ''
    showEvaluationDialog.value = true
}

const autoEvaluate = async () => {
  if (!selectedAnswer.value) return
  
  autoEvaluating.value = true
  try {
    // 这里应该调用自动评测API，目前先模拟
    const mockEvaluation = {
      id: Date.now(),
      score: selectedAnswer.value.std_question?.question_type === 'choice' ? 100 : 85,
      evaluator_type: 'auto',
      feedback: '自动评测完成',
      evaluation_time: new Date().toISOString()
    }
    
    answerEvaluations.value.push(mockEvaluation)
    showMessage('自动评测完成', 'success')
  } catch (error) {
    console.error('自动评测失败:', error)
    showMessage('自动评测失败', 'error')
  } finally {
    autoEvaluating.value = false
  }
}

const submitManualEvaluation = async () => {
  if (!selectedAnswer.value) return
  
  submittingEvaluation.value = true
  try {
    // 这里应该调用手动评测API，目前先模拟
    const mockEvaluation = {
      id: Date.now(),
      score: manualEvaluation.score,
      evaluator_type: 'user',
      feedback: manualEvaluation.feedback,
      evaluation_criteria: manualEvaluation.evaluation_criteria,
      evaluation_time: new Date().toISOString()
    }
    
    answerEvaluations.value.push(mockEvaluation)
    showMessage('评测提交成功', 'success')
    showEvaluationDialog.value = false
  } catch (error) {
    console.error('提交评测失败:', error)
    showMessage('提交评测失败', 'error')
  } finally {
    submittingEvaluation.value = false
  }
}

const downloadResults = async () => {
  if (!evaluationTask.value) return
  
  try {
    const results = await llmEvaluationService.downloadTaskResults(evaluationTask.value.id, {
      format: 'json',
      include_raw_responses: true,
      include_prompts: true
    })
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(results, null, 2)], {
      type: 'application/json'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `evaluation_results_${evaluationTask.value.id}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    showMessage('结果下载成功', 'success')
  } catch (error) {
    console.error('下载失败:', error)
    showMessage('下载失败', 'error')
  }
}

const restart = () => {
  // 停止轮询
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
  
  // 重置状态
  currentStep.value = 0  // 重置配置
  modelConfig.model_id = null
  modelConfig.api_key = ''
  modelConfig.temperature = 0.7
  modelConfig.max_tokens = 2000
  modelConfig.top_k = 50
  modelConfig.enable_reasoning = false
  
  evaluationOptions.task_name = ''
  evaluationOptions.question_limit_type = 'all'
  evaluationOptions.question_limit = 10
  evaluationOptions.is_auto_score = true
  
  // 重置结果
  evaluationTask.value = null
  taskProgress.value = null
  llmAnswers.value = []
  
  // 重新加载默认prompts
  loadDefaultPrompts()
}

// 动态下一步按钮文本计算属性
const nextStepButtonText = computed(() => {
  const step = currentStep.value
  switch (step) {
    case 0: return '下一步：配置系统Prompt →'
    case 1: return '下一步：生成回答 →'
    case 2: return '下一步：配置评测 →'
    case 3: return '下一步：查看结果 →'
    default: return '下一步 →'
  }
})
</script>

<style scoped>
/* 全局样式 */
.llm-evaluation {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  position: relative;
}

/* 顶部导航栏 */
.top-nav {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 20px 0;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-left .back-btn {
  color: #667eea;
  font-weight: 500;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.nav-left .back-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: translateX(-2px);
}

.nav-center {
  text-align: center;
}

.nav-center h1 {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 5px 0;
}

.nav-center p {
  color: #666;
  margin: 0;
  font-size: 14px;
}

/* 主要内容区域 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* 内容卡片 */
.content-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.content-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.15);
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
}

.card-header h3 {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 10px 0;
}

.card-header p {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.summary-tags {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.summary-tags .tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: #f0f2f5;
  color: #606266;
}

.summary-tags .tag-success {
  background: linear-gradient(135deg, #e6fffa 0%, #c7f9e9 100%);
  color: #67c23a;
}

/* 表单控件 */
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2d3748;
  font-size: 14px;
}

.form-input, .form-select, .form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  box-sizing: border-box;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: #667eea;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  transform: translateY(-1px);
}

.form-range {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  appearance: none;
}

.form-range::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  cursor: pointer;
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.form-range::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  cursor: pointer;
  border: none;
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  border-radius: 12px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  min-height: 44px;
  gap: 8px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  color: #495057;
  border: 2px solid #dee2e6;
}

.btn-secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.btn-success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  box-shadow: 0 8px 25px rgba(40, 167, 69, 0.3);
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(40, 167, 69, 0.4);
}

.btn-warning {
  background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
  color: white;
  box-shadow: 0 8px 25px rgba(255, 193, 7, 0.3);
}

.btn-warning:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(255, 193, 7, 0.4);
}

.btn-danger {
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  color: white;
  box-shadow: 0 8px 25px rgba(220, 53, 69, 0.3);
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(220, 53, 69, 0.4);
}

/* 步骤操作按钮 */
.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid rgba(102, 126, 234, 0.1);
}

.btn-large {
  padding: 16px 32px;
  font-size: 16px;
  font-weight: 700;
}

/* 表格样式 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.data-table th {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.data-table tr:hover {
  background: rgba(102, 126, 234, 0.05);
}

.data-table tr:last-child td {
  border-bottom: none;
}

/* 分页控件 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.pagination-info {
  font-size: 14px;
  color: #666;
}

.total-info {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

/* 进度条 */
.progress-container {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

/* 状态徽章 */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  gap: 4px;
}

.status-running {
  background: linear-gradient(135deg, #ffc107, #fd7e14);
  color: white;
}

.status-completed {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
}

.status-failed {
  background: linear-gradient(135deg, #dc3545, #c82333);
  color: white;
}

/* 评测详情样式 */
.evaluation-detail {
  padding: 20px 30px;
}

.answer-info {
  margin-bottom: 20px;
}

.answer-info h4 {
  margin: 0 0 8px 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
}

.answer-info p {
  margin: 0 0 16px 0;
  color: #4a5568;
  line-height: 1.6;
  background: #f7fafc;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.evaluations {
  margin-bottom: 20px;
}

.evaluation-item {
  margin-bottom: 16px;
}

.evaluation-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.eval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.score {
  font-size: 18px;
  font-weight: 700;
  color: #667eea;
}

.eval-type {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.user-eval {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.auto-eval {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
}

.feedback, .criteria {
  margin-bottom: 8px;
}

.feedback p, .criteria p {
  margin: 0;
  color: #4a5568;
  font-size: 14px;
  line-height: 1.5;
}

.manual-evaluation {
  border-top: 1px solid #e2e8f0;
  padding-top: 20px;
}

.manual-evaluation h4 {
  margin: 0 0 16px 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
}

/* 步骤指示器 */
.steps-container {
  max-width: 1000px;
  margin: 40px auto;
  padding: 0 20px;
}

/* Steps container styling - now using custom implementation */
.steps-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 40px;
  position: relative;
  overflow-x: auto;
  padding: 10px;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  min-width: 120px;
  text-align: center;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e4e7ed;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 10px;
  transition: all 0.3s ease;
}

.step-title {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.step-item.active .step-number {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
}

.step-item.active .step-title {
  color: #303133;
  font-weight: 600;
}

.step-item:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 20px;
  left: calc(100% + 10px);
  width: 20px;
  height: 2px;
  background: #e4e7ed;
  z-index: -1;
}

/* 消息提示样式 */
.message-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  padding: 12px 20px;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(20px);
}

/* 模态框组件 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-content {
  background: #fff;
  border-radius: 15px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 30px;
  border-bottom: 1px solid #e4e7ed;
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.modal-close {
  background: transparent;
  border: none;
  font-size: 24px;
  color: #909399;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: #f5f7fa;
  color: #606266;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  padding: 20px 30px;
  border-top: 1px solid #e4e7ed;
  background: #f8f9fa;
  border-radius: 0 0 15px 15px;
}

/* 答案生成相关样式 */
.generation-options {
  margin: 20px 0;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.generation-options h4 {
  margin: 0 0 16px 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.option-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-item label {
  font-weight: 500;
  color: #4a5568;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-checkbox {
  width: 16px;
  height: 16px;
  border: 2px solid #cbd5e0;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.form-checkbox:checked {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: #667eea;
}

.option-description {
  font-size: 12px;
  color: #718096;
  margin: 4px 0 0 0;
}

/* 评测配置相关样式 */
.evaluation-options {
  margin: 20px 0;
  padding: 20px;
  background: #f7fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.evaluation-options h4 {
  margin: 0 0 16px 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
}

/* 数据集分析样式 */
.dataset-analysis {
  margin: 20px 0;
  padding: 20px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.dataset-analysis h4 {
  margin: 0 0 16px 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.analysis-card {
  background: white;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.analysis-icon {
  font-size: 20px;
}

.analysis-title {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
}

.analysis-count {
  font-size: 24px;
  font-weight: 700;
  color: #4299e1;
  margin: 8px 0;
}

.analysis-desc {
  font-size: 12px;
  color: #718096;
  margin: 0;
}

/* Prompt容器增强样式 */
.prompt-container {
  margin: 20px 0;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.tabs {
  display: flex;
  background: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
}

.tab-button {
  flex: 1;
  padding: 12px 20px;
  background: transparent;
  border: none;
  color: #718096;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.tab-button:hover {
  background: #edf2f7;
  color: #4a5568;
}

.tab-button.active {
  background: white;
  color: #667eea;
  font-weight: 600;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.prompt-section {
  padding: 20px;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.header-left .icon {
  font-size: 20px;
  margin-top: 2px;
}

.header-left h4 {
  margin: 0 0 4px 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
}

.header-left p {
  margin: 0;
  color: #718096;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
}

.btn-info {
  background: linear-gradient(135deg, #4299e1, #3182ce);
  color: white;
  border: 1px solid #3182ce;
}

.btn-info:hover {
  background: linear-gradient(135deg, #3182ce, #2c5aa0);
  transform: translateY(-1px);
}

.prompt-editor {
  margin-top: 16px;
}

.prompt-textarea {
  width: 100%;
  min-height: 200px;
  padding: 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
  transition: all 0.3s ease;
  background: #fafafa;
}

.prompt-textarea:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.editor-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 8px 12px;
  background: #f7fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.char-count {
  font-size: 12px;
  color: #718096;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 预览卡片增强 */
.prompt-preview {
  margin: 20px 0;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.prompt-preview h4 {
  margin: 0;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f7fafc, #edf2f7);
  border-bottom: 1px solid #e2e8f0;
  color: #2d3748;
  font-size: 14px;
  font-weight: 600;
}

.preview-card {
  padding: 20px;
}

.preview-content {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.message-item {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-item:last-child {
  margin-bottom: 0;
}

.message-label {
  font-size: 12px;
  font-weight: 600;
  color: #718096;
  display: flex;
  align-items: center;
  gap: 6px;
}

.message-content {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  font-size: 14px;
  line-height: 1.5;
  color: #2d3748;
  white-space: pre-wrap;
}

.message-item.system .message-content {
  background: linear-gradient(135deg, #ebf8ff, #e6fffa);
  border-color: #bee3f8;
}

.message-item.user .message-content {
  background: linear-gradient(135deg, #f7fafc, #edf2f7);
  border-color: #e2e8f0;
}

/* 响应式设计增强 */
@media (max-width: 768px) {
  .type-analysis-grid {
    grid-template-columns: 1fr;
  }
  
  .options-grid {
    grid-template-columns: 1fr;
  }
  
  .tabs {
    flex-direction: column;
  }
  
  .tab-button {
    border-bottom: 1px solid #e2e8f0;
  }
  
  .tab-button:last-child {
    border-bottom: none;
  }
  
  .prompt-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .header-actions {
    align-self: flex-start;
  }
}

/* 动画增强 */
.prompt-section {
  animation: fadeInUp 0.4s ease;
}

.analysis-card {
  transition: all 0.3s ease;
}

.analysis-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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

/* 进度弹窗样式 */
.progress-modal-content {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease;
}

.progress-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 16px 16px 0 0;
}

.progress-modal-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 18px;
  font-weight: 600;
}

.progress-modal-body {
  padding: 24px;
}

.progress-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e2e8f0;
  background: #f8f9fa;
  border-radius: 0 0 16px 16px;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.task-info {
  text-align: center;
  margin-bottom: 20px;
}

.task-info h4 {
  margin: 0 0 8px 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
}

.status-info {
  display: flex;
  justify-content: center;
}

.progress-section {
  margin: 20px 0;
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.progress-bar-container {
  margin: 16px 0;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
  border-radius: 6px;
}

.progress-fill.progress-success {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

.progress-fill.progress-error {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.real-time-info {
  margin: 20px 0;
  padding: 16px;
  background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
  border-radius: 12px;
  border: 1px solid #bee3f8;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item label {
  font-size: 14px;
  color: #4a5568;
  font-weight: 500;
}

.info-item span {
  font-size: 14px;
  color: #2d3748;
  font-weight: 600;
}

.latest-answer {
  margin: 20px 0;
}

.answer-preview {
  padding: 16px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.answer-preview h5 {
  margin: 0 0 12px 0;
  color: #2d3748;
  font-size: 14px;
  font-weight: 600;
}

.answer-content {
  font-size: 14px;
  color: #4a5568;
  line-height: 1.5;
  margin-bottom: 8px;
}

.answer-score {
  font-size: 12px;
  color: #667eea;
  font-weight: 600;
}

.error-info {
  margin: 20px 0;
}

.error-card {
  padding: 16px;
  background: linear-gradient(135deg, #fed7d7 0%, #fbb6ce 100%);
  border-radius: 12px;
  border: 1px solid #f56565;
}

.error-card h5 {
  margin: 0 0 8px 0;
  color: #742a2a;
  font-size: 14px;
  font-weight: 600;
}

.error-card p {
  margin: 0;
  color: #742a2a;
  font-size: 14px;
  line-height: 1.5;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .progress-modal-content {
    width: 95%;
    margin: 20px;
  }
  
  .progress-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .progress-modal-footer {
    flex-direction: column;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>

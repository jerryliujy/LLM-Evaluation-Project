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
      <!-- <div class="header-right">
        <button v-if="evaluationTask" @click="viewTaskProgress" class="progress-btn">
          📊 查看进度
        </button>
      </div> -->
    </div>

    <!-- 评测模式选择 -->
    <div v-if="!evaluationTask" class="mode-selector">
      <div class="mode-tabs">
        <button 
          :class="['tab-btn', { active: evaluationMode === 'auto' }]"
          @click="switchEvaluationMode('auto')"
        >
          🤖 自动评测
        </button>
        <button 
          :class="['tab-btn', { active: evaluationMode === 'manual' }]"
          @click="switchEvaluationMode('manual')"
        >
          📝 手动录入
        </button>
      </div>
    </div>

    <!-- 手动录入组件 -->
    <ManualEvaluationEntry
      v-if="evaluationMode === 'manual'"
      :mode="evaluationMode"
      @switch-mode="switchEvaluationMode"
      @task-created="onManualTaskCreated"
    />

    <!-- 自动评测流程 -->
    <div v-else-if="evaluationMode === 'auto'">    
      <!-- 步骤指示器 -->
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
          </div>          <div class="step-item" :class="{ 
            active: currentStep === 2, 
            locked: isStepLocked(2) 
          }">
            <span class="step-number">
              <span v-if="isStepLocked(2)">🔒</span>
              <span v-else>3</span>
            </span>
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
                <h4>数据集名称：{{ currentDataset?.name }}</h4>
                <p>数据集描述：{{ currentDataset?.description }}</p>
                <div class="summary-tags">
                  <span class="tag">{{ currentDataset?.question_count }} 题</span>
                  <span class="tag tag-success">v{{ currentDataset?.version }}</span>
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
                  <strong>{{ selectedModel?.display_name }}</strong><br>
                  {{ selectedModel?.description }}
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
                :disabled="isStepLocked(0)"
              />
              <div class="form-tip">
                ℹ️ API Key将被安全加密存储，仅用于本次评测
              </div>            
            </div>
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
              <label class="form-label">最大Token数</label>              
              <input 
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
              <label class="form-label">Top-K采样: {{ modelConfig.top_k }}</label>              
              <input
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
              <label class="form-label">                
                <input 
                  v-model="modelConfig.enable_reasoning" 
                  type="checkbox"
                  class="form-checkbox"
                  :disabled="isStepLocked(0) || !isReasoningSupported"
                />
                启用推理模式
                <span v-if="!isReasoningSupported" class="unsupported-badge">不支持</span>
              </label>
              <div class="form-tip">
                <span v-if="isReasoningSupported">
                  ℹ️ 启用后模型会展示详细的推理过程
                </span>
                <span v-else class="warning-tip">
                  ⚠️ 当前选择的模型不支持推理模式
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="step-actions">
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
                :disabled="isStepLocked(1)"
              ></textarea>
              <div class="editor-info">                <div class="char-count">
                  📄 {{ systemPromptConfig?.choice_system_prompt?.length || 0 }} 字符
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
                :disabled="isStepLocked(1)"
              ></textarea>
              <div class="editor-info">                
                <div class="char-count">
                  📄 {{ systemPromptConfig?.text_system_prompt?.length || 0 }} 字符
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
                </div>                <div class="message-content">
                  {{ activeSystemPromptTab === 'choice' ? (systemPromptConfig?.choice_system_prompt || '请输入系统Prompt...') : (systemPromptConfig?.text_system_prompt || '请输入系统Prompt...') }}
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
      </div>    
    </div>    <!-- 步骤3: 答案生成 -->
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
            v-if="!answerGenerationTask || answerGenerationTask?.status !== 'evaluating_answers'"
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
    </div>    <!-- 步骤4: 评测方式选择 -->    
    <div v-if="currentStep === 3 && !hasSelectedEvaluationMode" class="step-content">
      <div class="content-card">
        <div class="card-header">
          <h3>⚖️ 选择评测方式</h3>
          <p>答案生成完成！请选择您希望使用的评测方式</p>
        </div>
        
        <!-- 评测方式选择 -->
        <div class="evaluation-mode-selection">
          <h4>📊 评测方式选择</h4>
          <div class="mode-buttons">
            <button 
              :class="['mode-button auto-mode', { 
                selected: evaluationConfig.evaluation_mode === 'auto',
                'not-selected': evaluationConfig.evaluation_mode && evaluationConfig.evaluation_mode !== 'auto'
              }]"
              @click="selectEvaluationMode('auto')"
            >
              <div class="button-header">
                <div class="mode-icon">🤖</div>
                <div class="mode-title">
                  <h5>LLM自动评测</h5>
                  <span class="mode-subtitle">智能化批量评测</span>
                </div>
                <div class="selection-indicator">
                  <span v-if="evaluationConfig.evaluation_mode === 'auto'" class="check-mark">✓</span>
                </div>
              </div>
              <div class="mode-description">
                <p>使用大语言模型自动评测答案质量和准确性，快速高效</p>
                <div class="mode-features">
                  <span class="feature-tag">⚡ 快速批量</span>
                  <span class="feature-tag">📊 标准化评分</span>
                  <span class="feature-tag">💡 详细理由</span>
                </div>
              </div>
            </button>
            
            <button 
              :class="['mode-button manual-mode', { 
                selected: evaluationConfig.evaluation_mode === 'manual',
                'not-selected': evaluationConfig.evaluation_mode && evaluationConfig.evaluation_mode !== 'manual'
              }]"
              @click="selectEvaluationMode('manual')"
            >
              <div class="button-header">
                <div class="mode-icon">👤</div>
                <div class="mode-title">
                  <h5>手动评测</h5>
                  <span class="mode-subtitle">人工精确评测</span>
                </div>
                <div class="selection-indicator">
                  <span v-if="evaluationConfig.evaluation_mode === 'manual'" class="check-mark">✓</span>
                </div>
              </div>
              <div class="mode-description">
                <p>人工逐个评测每个答案，提供精确的评分和个性化反馈</p>
                <div class="mode-features">
                  <span class="feature-tag">🎯 精确控制</span>
                  <span class="feature-tag">💭 个性化反馈</span>
                  <span class="feature-tag">💾 随时保存</span>
                </div>
              </div>
            </button>
          </div>
          
          <!-- 选择提示 -->
          <div v-if="evaluationConfig.evaluation_mode" class="selection-hint">
            <div class="hint-content">
              <span class="hint-icon">💡</span>
              <span v-if="evaluationConfig.evaluation_mode === 'auto'">
                您选择了<strong>LLM自动评测</strong>，系统将使用AI模型批量评测所有答案
              </span>
              <span v-else>
                您选择了<strong>手动评测</strong>，您将逐个查看和评分每个答案
              </span>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="card-actions">
          <button @click="prevStep" class="btn btn-secondary">
            ← 上一步
          </button>          
          <button 
            @click="confirmEvaluationMode" 
            :disabled="!evaluationConfig.evaluation_mode" 
            class="btn btn-primary"
            :class="{ 'pulse': evaluationConfig.evaluation_mode }"
          >
            <span v-if="evaluationConfig.evaluation_mode">
              {{ evaluationConfig.evaluation_mode === 'auto' ? '🚀 开始自动评测' : '👤 进入手动评测' }}
            </span>
            <span v-else>请先选择评测方式</span>
          </button>
        </div>
      </div>    
    </div>    <!-- 步骤4: 自动评测配置 -->
    <div v-if="currentStep === 3 && hasSelectedEvaluationMode && evaluationConfig.evaluation_mode === 'auto'" class="step-content">
      <div class="content-card">
        <div class="card-header">
          <h3>⚖️ 配置自动评测</h3>
          <p>配置LLM自动评测的参数和Prompt</p>
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
                :disabled="isStepLocked(3)"
              ></textarea>
              <div class="editor-info">
                <div class="char-count">
                  📄 {{ evaluationConfig.choice_evaluation_prompt?.length || 0 }} 字符
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
                  📄 {{ evaluationConfig.text_evaluation_prompt?.length || 0 }} 字符
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
          </div>
        </div>
        </div>

        <!-- 手动评测说明 -->
        <div v-if="evaluationConfig.evaluation_mode === 'manual'" class="manual-evaluation-info">
          <div class="info-card">
            <div class="info-header">
              <span class="info-icon">ℹ️</span>
              <h4>手动评测说明</h4>
            </div>
            <div class="info-content">
              <p>您将进入手动评测界面，需要对每个LLM生成的答案进行人工评分。</p>
              <ul class="info-list">
                <li>🎯 <strong>逐个评测</strong>：您将看到标准问答、得分点信息和LLM回答</li>
                <li>📝 <strong>输入评分</strong>：为每个答案输入0-100分的评分</li>
                <li>💭 <strong>判断理由</strong>：提供详细的评分理由和反馈</li>
                <li>💾 <strong>自动保存</strong>：您的评测进度会实时保存，可随时退出和继续</li>
                <li>🔄 <strong>灵活调整</strong>：已评测的内容可以随时修改</li>
              </ul>
              <div class="info-note">
                <span class="note-icon">📌</span>
                <span>手动评测过程中，您可以随时返回数据集市场，已评测的内容将被保存。</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="card-actions">
          <button @click="prevStep" class="btn btn-secondary">
            ← 上一步
          </button>          
          <button 
            v-if="evaluationConfig.evaluation_mode === 'auto'"
            @click="startEvaluation" 
            :disabled="!isEvaluationConfigValid || starting" 
            class="btn btn-primary"
          >
            <span v-if="starting">⏳ 评测中...</span>
            <span v-else>🚀 开始LLM评测</span>
          </button>
          <button 
            v-if="evaluationConfig.evaluation_mode === 'manual'"
            @click="startManualEvaluation" 
            :disabled="starting" 
            class="btn btn-primary"
          >
            <span v-if="starting">⏳ 准备中...</span>
            <span v-else>👤 开始手动评测</span>
          </button>
        </div>
      </div>    
    </div>      <!-- 步骤5: 查看结果 -->
    <div v-if="currentStep === 4" class="step-content">
      <div class="content-card">
        <div class="card-header">
          <h3>📊 评测完成</h3>
          <p>评测任务已完成，您可以查看详细结果或进行其他操作</p>
        </div>
        
        <!-- 任务概览 -->
        <div v-if="evaluationTask" class="task-overview">
          <div class="overview-grid">
            <div class="overview-card">
              <div class="overview-icon">📝</div>
              <div class="overview-info">
                <h4>{{ evaluationTask?.task_name || evaluationTask?.name }}</h4>
                <p>任务状态: <span class="status-badge" :class="getStatusType(evaluationTask?.status)">
                  {{ getStatusText(evaluationTask?.status) }}
                </span></p>
              </div>
            </div>
            
            <div class="overview-card" v-if="detailedResults?.statistics">
              <div class="overview-icon">📊</div>
              <div class="overview-info">
                <h4>评测统计</h4>
                <p>总答案: {{ detailedResults.statistics.total_answers }}</p>
                <p>平均分: {{ detailedResults.statistics.average_score?.toFixed(1) || 'N/A' }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="result-actions">
          <button @click="showDetailedResults" class="btn btn-primary">
            📋 查看详细结果
          </button>
          <button 
            v-if="evaluationTask && evaluationTask?.status === 'completed'"
            @click="downloadResults"
            class="btn btn-success"
          >
            📥 下载完整结果
          </button>
          <button @click="backToMarketplace" class="btn btn-secondary">
            返回数据集市场
          </button>        
        </div> <!-- 自动评测流程结束 -->
      </div>
    </div>    <!-- 手动评测界面 -->
    <div v-if="isManualEvaluating && evaluationConfig.evaluation_mode === 'manual'" class="manual-evaluation-interface">
      <div class="content-card">        
        <div class="card-header">
          <h3>👤 手动评测界面</h3>
          <p>请对每个LLM生成的答案进行人工评分和评价</p>
        </div>

        <!-- 加载状态 -->
        <div v-if="starting" class="loading-section">
          <div class="loading-spinner"></div>
          <p>正在加载评测数据...</p>
        </div>

        <!-- 无数据状态 -->
        <div v-else-if="!manualEvaluationAnswers.length" class="no-data-section">
          <div class="no-data-content">
            <span class="no-data-icon">📭</span>
            <h4>暂无评测数据</h4>
            <p>没有找到需要评测的答案，请检查答案生成任务是否完成。</p>
            <button @click="exitManualEvaluation" class="btn btn-secondary">
              返回上一步
            </button>
          </div>
        </div>        <!-- 评测内容 -->
        <div v-else>
          <!-- 统计信息 -->
          <div class="evaluation-stats">
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-label">总答案数</span>
                <span class="stat-value">{{ manualEvaluationAnswers.length }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">已评测</span>
                <span class="stat-value">{{ getEvaluatedCount() }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">未评测</span>
                <span class="stat-value">{{ manualEvaluationAnswers.length - getEvaluatedCount() }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">完成率</span>
                <span class="stat-value">{{ Math.round((getEvaluatedCount() / manualEvaluationAnswers.length) * 100) }}%</span>
              </div>
            </div>
          </div>

          <!-- 答案列表 -->
          <div class="answers-list">
            <div class="list-header">
              <h4>📋 答案评测列表</h4>
              <div class="list-actions">
                <button @click="saveAllEvaluations" class="btn btn-info btn-small">
                  💾 保存所有评测
                </button>
                <button 
                  @click="completeManualEvaluation" 
                  :disabled="!isAllEvaluated()"
                  class="btn btn-primary btn-small"
                >
                  ✅ 完成评测
                </button>
              </div>
            </div>
            
            <div class="answers-table">
              <div class="table-header">
                <div class="col col-index">#</div>
                <div class="col col-question">题目</div>
                <div class="col col-type">类型</div>
                <div class="col col-score">评分</div>
                <div class="col col-status">状态</div>
                <div class="col col-actions">操作</div>
              </div>
              
              <div class="table-body">
                <div 
                  v-for="(answer, index) in manualEvaluationAnswers" 
                  :key="answer.id"
                  :class="['table-row', { 
                    'selected': selectedAnswerIndex === index,
                    'evaluated': isAnswerEvaluated(answer),
                    'not-evaluated': !isAnswerEvaluated(answer)
                  }]"
                  @click="selectAnswer(index)"
                >
                  <div class="col col-index">{{ index + 1 }}</div>
                  <div class="col col-question">
                    <div class="question-preview">
                      {{ truncateText(answer.question?.body || '', 80) }}
                    </div>
                  </div>
                  <div class="col col-type">
                    <span class="type-badge" :class="answer.question?.question_type">
                      {{ answer.question?.question_type === 'choice' ? '选择题' : '文本题' }}
                    </span>
                  </div>
                  <div class="col col-score">
                    <div v-if="answer.manual_score !== null && answer.manual_score !== undefined" class="score-display">
                      <span class="score-value">{{ answer.manual_score }}</span>
                      <span class="score-unit">分</span>
                    </div>
                    <span v-else class="no-score">未评分</span>
                  </div>
                  <div class="col col-status">
                    <span :class="['status-badge', isAnswerEvaluated(answer) ? 'completed' : 'pending']">
                      {{ isAnswerEvaluated(answer) ? '已完成' : '待评测' }}
                    </span>
                  </div>
                  <div class="col col-actions">
                    <button @click.stop="selectAnswer(index)" class="btn btn-small btn-primary">
                      {{ isAnswerEvaluated(answer) ? '修改' : '评分' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 选中答案的详细信息 -->
          <div v-if="selectedAnswerIndex !== -1 && getCurrentAnswer()" class="answer-detail">
            <div class="detail-header">
              <h4>📝 答案详情 - 第{{ selectedAnswerIndex + 1 }}题</h4>
              <button @click="closeDetail" class="btn btn-small btn-secondary">
                ✕ 关闭
              </button>
            </div>            <!-- 题目内容 -->
            <div class="question-section">
              <div class="question-header">
                <h5>📝 题目内容</h5>
                <div class="question-type-badge">
                  {{ getCurrentQuestion().question_type === 'choice' ? '选择题' : '文本题' }}
                </div>
              </div>
              <div class="question-content">
                <div class="question-body">
                  {{ getCurrentQuestion().body }}
                </div>
              </div>
            </div>

            <!-- 标准答案信息 -->
            <div v-if="getCurrentAnswer()?.std_answers && getCurrentAnswer().std_answers.length > 0" class="standard-answer-section">
              <h5>📋 标准答案</h5>
              <div class="standard-answer-content">
                <div v-for="(stdAnswer, index) in getCurrentAnswer().std_answers" :key="stdAnswer.id" class="std-answer-item">
                  <div v-if="getCurrentAnswer().std_answers.length > 1" class="std-answer-header">
                    <h6>标准答案 {{ index + 1 }}</h6>
                    <span v-if="stdAnswer.answered_by" class="answered-by">作者：{{ stdAnswer.answered_by }}</span>
                  </div>
                  <div class="answer-text">
                    {{ stdAnswer.answer }}
                  </div>
                  <div v-if="stdAnswer.scoring_points && stdAnswer.scoring_points.length > 0" class="scoring-points">
                    <h6>评分要点：</h6>
                    <ul class="scoring-points-list">
                      <li 
                        v-for="point in stdAnswer.scoring_points" 
                        :key="point.id"
                        class="scoring-point"
                      >
                        <span class="point-text">{{ point.answer }}</span>
                        <span class="point-order">第{{ point.point_order }}点</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <!-- LLM答案 -->
            <div class="llm-answer-section">
              <h5>🤖 LLM回答</h5>
              <div class="llm-answer-content">
                <div class="answer-text">
                  {{ getCurrentAnswer().llm_answer }}
                </div>
                <div class="answer-meta">
                  <span class="model-info">模型：{{ selectedModel?.display_name || modelConfig.model_id }}</span>
                  <span class="generated-time">生成时间：{{ formatDateTime(getCurrentAnswer().answered_at) }}</span>
                  <span v-if="getCurrentAnswer().is_valid !== undefined" 
                        :class="['validity-status', getCurrentAnswer().is_valid ? 'valid' : 'invalid']">
                    {{ getCurrentAnswer().is_valid ? '✅ 有效答案' : '❌ 无效答案' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 评分表单 -->
            <div class="evaluation-form">
              <h5>📊 评分</h5>
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">分数 (0-100)</label>
                  <div class="score-input-container">
                    <input 
                      v-model.number="getCurrentAnswer().manual_score" 
                      type="number" 
                      min="0" 
                      max="100"
                      class="form-input score-input"
                      placeholder="请输入分数"
                      @input="onScoreChange"
                    />
                    <div class="score-slider">
                      <input 
                        v-model.number="getCurrentAnswer().manual_score" 
                        type="range" 
                        min="0" 
                        max="100"
                        class="form-range"
                        @input="onScoreChange"
                      />
                    </div>
                  </div>
                </div>
                <div class="form-group">
                  <label class="form-label">评分理由</label>
                  <textarea 
                    v-model="getCurrentAnswer().manual_reasoning" 
                    rows="4"
                    class="form-textarea"
                    placeholder="请输入详细的评分理由和反馈..."
                    @input="onReasoningChange"
                  ></textarea>
                </div>
              </div>
              
              <!-- 评分操作按钮 -->
              <div class="evaluation-actions">
                <button 
                  @click="saveCurrentEvaluation" 
                  class="btn btn-info"
                >
                  💾 保存评分
                </button>
                <button 
                  @click="clearCurrentEvaluation" 
                  class="btn btn-warning"
                >
                  🗑️ 清除评分
                </button>
              </div>
            </div>
          </div>
          
          <div class="action-buttons">
            <button 
              @click="saveCurrentEvaluation" 
              class="btn btn-info"
            >
              💾 保存当前评测
            </button>
            <button 
              @click="exitManualEvaluation" 
              class="btn btn-warning"
            >
              🚪 退出评测
            </button>
            <button 
              @click="completeManualEvaluation" 
              :disabled="!isAllEvaluated()"
              class="btn btn-primary"
            >
              ✅ 完成评测
            </button>
          </div>
        </div>        <!-- 评测完成状态 -->
        <div v-if="isAllEvaluated()" class="completion-notice">
          <div class="notice-card">
            <span class="notice-icon">🎉</span>
            <div class="notice-content">
              <h5>评测完成</h5>
              <p>所有答案已评测完成，您可以点击"完成评测"按钮提交结果。</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细结果弹窗 -->
    <div v-if="showResultsDialog" class="modal-overlay" @click="showResultsDialog = false">
      <div class="results-modal-content" @click.stop>
        <div class="modal-header">
          <h3>📊 详细评测结果</h3>
          <button @click="showResultsDialog = false" class="modal-close">×</button>
        </div>
        
        <div class="modal-body results-modal-body">
          <!-- 加载状态 -->
          <div v-if="loadingDetailedResults" class="loading-state">
            <div class="loading-spinner"></div>
            <p>正在加载详细结果...</p>
          </div>

          <!-- 详细结果显示 -->
          <div v-else-if="detailedResults" class="detailed-results">
            <!-- 任务基本信息 -->          
            <div class="task-info-section">
              <div class="section-header">
                <h3>📋 任务信息</h3>
                <span class="status-tag" :class="getStatusType(detailedResults?.task_info?.status)">
                  {{ getStatusText(detailedResults?.task_info?.status) }}
                </span>
              </div>
              
              <div class="task-info-grid">
                <div class="info-card">
                  <div class="info-item">
                    <label>任务名称</label>
                    <span>{{ detailedResults?.task_info?.name }}</span>
                  </div>
                  <div class="info-item">
                    <label>数据集</label>
                    <span>{{ detailedResults?.task_info?.dataset_name }}</span>
                  </div>
                  <div class="info-item">
                    <label>模型</label>
                    <span>{{ detailedResults?.task_info?.model_name }}</span>
                    <span v-if="detailedResults?.task_info?.model_version" class="model-version">
                      v{{ detailedResults?.task_info?.model_version }}
                    </span>
                  </div>
                </div>
                
                <div class="info-card">
                  <div class="info-item">
                    <label>创建时间</label>
                    <span>{{ formatDateTime(detailedResults?.task_info?.created_at) }}</span>
                  </div>
                  <div class="info-item">
                    <label>开始时间</label>
                    <span>{{ formatDateTime(detailedResults?.task_info?.started_at) }}</span>
                  </div>
                  <div class="info-item">
                    <label>完成时间</label>
                    <span>{{ formatDateTime(detailedResults?.task_info?.completed_at) }}</span>
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
                      <span>{{ detailedResults?.configuration?.temperature || 0.7 }}</span>
                    </div>
                    <div class="config-item">
                      <label>最大Token数</label>
                      <span>{{ detailedResults?.configuration?.max_tokens || 2000 }}</span>
                    </div>
                    <div class="config-item">
                      <label>Top-K采样</label>
                      <span>{{ detailedResults?.configuration?.top_k || 50 }}</span>
                    </div>
                    <div class="config-item">
                      <label>推理模式</label>
                      <span class="boolean-value" :class="detailedResults?.configuration?.enable_reasoning ? 'enabled' : 'disabled'">
                        {{ detailedResults?.configuration?.enable_reasoning ? '启用' : '禁用' }}
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
                <!-- 选择题系统Prompt -->
                <div v-if="detailedResults?.prompts?.choice_system_prompt" class="prompt-card">
                  <h4>选择题系统Prompt</h4>
                  <div class="prompt-content">
                    <pre>{{ detailedResults.prompts.choice_system_prompt }}</pre>
                  </div>
                </div>
                
                <!-- 文本题系统Prompt -->
                <div v-if="detailedResults?.prompts?.text_system_prompt" class="prompt-card">
                  <h4>文本题系统Prompt</h4>
                  <div class="prompt-content">
                    <pre>{{ detailedResults.prompts.text_system_prompt }}</pre>
                  </div>
                </div>
                
                <!-- 兼容旧的系统Prompt -->
                <div v-if="!detailedResults?.prompts?.choice_system_prompt && !detailedResults?.prompts?.text_system_prompt && detailedResults?.configuration?.system_prompt" class="prompt-card">
                  <h4>系统Prompt</h4>
                  <div class="prompt-content">
                    <pre>{{ detailedResults.configuration.system_prompt }}</pre>
                  </div>
                </div>
                
                <!-- 选择题评估Prompt -->
                <div v-if="detailedResults?.prompts?.choice_evaluation_prompt" class="prompt-card">
                  <h4>选择题评估Prompt</h4>
                  <div class="prompt-content">
                    <pre>{{ detailedResults.prompts.choice_evaluation_prompt }}</pre>
                  </div>
                </div>
                
                <!-- 文本题评估Prompt -->
                <div v-if="detailedResults?.prompts?.text_evaluation_prompt" class="prompt-card">
                  <h4>文本题评估Prompt</h4>
                  <div class="prompt-content">
                    <pre>{{ detailedResults.prompts.text_evaluation_prompt }}</pre>
                  </div>
                </div>
                
                <!-- 兼容旧的评估Prompt -->
                <div v-if="!detailedResults?.prompts?.choice_evaluation_prompt && !detailedResults?.prompts?.text_evaluation_prompt && detailedResults?.configuration?.evaluation_prompt" class="prompt-card">
                  <h4>评估Prompt</h4>
                  <div class="prompt-content">
                    <pre>{{ detailedResults.configuration.evaluation_prompt }}</pre>
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
                    <div class="stat-value">{{ detailedResults?.statistics?.total_answers }}</div>
                    <div class="stat-label">总答案数</div>
                  </div>
                </div>
                
                <div class="stat-card">
                  <div class="stat-icon">✅</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ detailedResults?.statistics?.valid_answers }}</div>
                    <div class="stat-label">有效答案</div>
                  </div>
                </div>
                
                <div class="stat-card">
                  <div class="stat-icon">🎯</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ detailedResults?.statistics?.evaluated_answers }}</div>
                    <div class="stat-label">已评分答案</div>
                  </div>
                </div>
                
                <div class="stat-card overall-score">
                  <div class="stat-icon">🏆</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ detailedResults?.statistics?.overall_average_score }}</div>
                    <div class="stat-label">平均分数</div>
                  </div>
                </div>
                
                <div class="stat-card">
                  <div class="stat-icon">📈</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ Math.round((detailedResults?.statistics?.completion_rate || 0) * 100) }}%</div>
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
                          <div v-if="stdAnswer?.scoring_points && stdAnswer?.scoring_points?.length > 0" class="scoring-points">
                            <span v-for="point in stdAnswer.scoring_points" :key="point.point_order" class="scoring-point">
                              {{ point.answer }}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td class="score-cell">
                        <div v-if="answer?.evaluations && answer?.evaluations?.length > 0">
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
                    第 {{ currentPage }} 页，共 {{ Math.ceil((detailedResults?.detailed_answers?.length || 0) / pageSize) }} 页
                  </span>
                  <button 
                    @click="currentPage++" 
                    :disabled="currentPage >= Math.ceil((detailedResults?.detailed_answers?.length || 0) / pageSize)"
                    class="btn btn-small btn-secondary"
                  >
                    下一页
                  </button>
                  <button 
                    @click="currentPage = Math.ceil((detailedResults?.detailed_answers?.length || 0) / pageSize)" 
                    :disabled="currentPage >= Math.ceil((detailedResults?.detailed_answers?.length || 0) / pageSize)"
                    class="btn btn-small btn-secondary"
                  >
                    末页
                  </button>
                </div>
                <div class="total-info">
                  共 {{ detailedResults?.detailed_answers?.length || 0 }} 条记录
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="downloadDetailedResults" class="btn btn-success">
            📥 下载详细结果
          </button>
          <button @click="downloadAnswersOnly" class="btn btn-info">
            📄 下载答案数据
          </button>          
          <button @click="showResultsDialog = false" class="btn btn-secondary">
            关闭
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

          <div v-if="answerEvaluations?.length > 0" class="evaluations">
            <h4>评测结果</h4>
            <div v-for="evaluation in answerEvaluations" :key="evaluation.id" class="evaluation-item">
              <div class="evaluation-card">
                <div class="eval-header">
                  <span class="score">{{ evaluation.score }}分</span>
                  <span class="eval-type" :class="evaluation.evaluator_type === 'user' ? 'user-eval' : 'llm-eval'">
                    {{ evaluation.evaluator_type === 'user' ? '人工评测' : 'LLM评测' }}
                  </span>
                </div>                <div v-if="evaluation.reasoning" class="criteria">
                  <p><strong>评测理由：</strong>{{ evaluation.reasoning }}</p>
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
              <label class="form-label">评测理由</label>
              <textarea 
                v-model="manualEvaluation.reasoning" 
                rows="3"
                class="form-textarea"
                placeholder="请输入评测理由..."
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
      <div class="progress-modal-content" @click.stop>
        <div class="progress-modal-header">
          <h3 v-if="currentTaskType === 'answer_generation'">🤖 正在生成答案</h3>
          <h3 v-else-if="currentTaskType === 'evaluation'">⚖️ 正在进行评测</h3>
          <h3 v-else>📊 任务进度</h3>
          <button @click="closeProgressDialog" class="modal-close">×</button>
        </div>
        
        <div class="progress-modal-body">          <div v-if="evaluationTask" class="progress-info">
            <div class="task-info">
              <h4>{{ evaluationTask?.task_name || '在线评测任务' }}</h4>
              <div class="status-info">                <span class="status-badge" :class="getStatusType(evaluationTask?.status)">
                  {{ getStatusText(evaluationTask?.status) }}
                </span>
              </div>
            </div>

            <!-- 进度条 -->
            <div class="progress-section">
              <div class="progress-stats">
                <div class="stat-item">
                  <span class="stat-label">总题数</span>
                  <span class="stat-value">{{ evaluationTask?.total_questions || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">已完成</span>
                  <span class="stat-value">{{ evaluationTask?.completed_questions || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">失败数</span>
                  <span class="stat-value">{{ evaluationTask?.failed_questions || 0 }}</span>
                </div>
              </div>
              
              <div class="progress-bar-container">
                <div class="progress-bar">                  
                  <div 
                    class="progress-fill" 
                    :style="{ width: (evaluationTask?.progress || 0) + '%' }"
                    :class="{ 
                      'progress-success': evaluationTask?.status === 'completed',
                      'progress-error': evaluationTask?.status === 'failed'
                    }"
                  ></div>
                </div>
                <div class="progress-text">
                  {{ evaluationTask?.progress || 0 }}%
                </div>
              </div>
            </div>            <!-- 实时信息 -->
            <div v-if="taskProgress" class="real-time-info">
              <div class="info-grid">
                <div class="info-item" v-if="taskProgress?.questions_per_minute">
                  <label>处理速度:</label>
                  <span>{{ taskProgress?.questions_per_minute?.toFixed(1) }}题/分钟</span>
                </div>
                <div class="info-item" v-if="taskProgress?.estimated_remaining_time">
                  <label>预计剩余:</label>
                  <span>{{ formatTime(taskProgress?.estimated_remaining_time) }}</span>
                </div>
                <div class="info-item" v-if="taskProgress?.average_score">
                  <label>平均分数:</label>
                  <span>{{ taskProgress?.average_score?.toFixed(1) }}分</span>
                </div>
              </div>
            </div>            <!-- 最新内容预览 -->
            <div v-if="taskProgress && (taskProgress?.latest_content || taskProgress?.latest_answer)" class="latest-content">
              <div class="content-preview">
                <h5 v-if="currentTaskType === 'answer_generation' || taskProgress?.latest_content_type === 'answer'">📝 最新答案预览</h5>
                <h5 v-else-if="currentTaskType === 'evaluation' || taskProgress?.latest_content_type === 'evaluation'">⚖️ 最新评测结果</h5>
                <h5 v-else>📋 最新内容</h5>
                <div class="content-body">
                  <!-- 优先显示 latest_content，如果没有则回退到 latest_answer -->
                  <div v-if="taskProgress?.latest_content" class="content-text">
                    {{ taskProgress.latest_content }}
                  </div>
                  <div v-else-if="taskProgress?.latest_answer" class="content-text">
                    {{ taskProgress.latest_answer.substring(0, 200) }}
                    <span v-if="taskProgress.latest_answer.length > 200">...</span>
                  </div>
                  <!-- 显示评分 -->
                  <div v-if="taskProgress?.latest_score !== null && taskProgress?.latest_score !== undefined" class="score-info">
                    <span class="score-badge">评分: {{ taskProgress.latest_score }}/100</span>
                  </div>
                </div>
              </div>
            </div><!-- 错误信息 -->
            <div v-if="evaluationTask?.status === 'failed' && evaluationTask?.error_message" class="error-info">
              <div class="error-card">
                <h5>❌ 评测失败</h5>
                <p>{{ evaluationTask?.error_message }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="progress-modal-footer">
          <button @click="backToMarketplaceFromProgress" class="btn btn-secondary">
            返回主界面
          </button>
          <button 
            v-if="evaluationTask && evaluationTask?.status === 'running'" 
            @click="pauseEvaluation" 
            class="btn btn-warning"
          >
            暂停评测          
          </button>          
          <button 
            v-if="evaluationTask && evaluationTask?.status === 'completed'" 
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
import { ref, reactive, computed, watch, onMounted, onUnmounted, version } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { llmEvaluationService } from '@/services/llmEvaluationService'
import ManualEvaluationEntry from '@/components/ManualEvaluationEntry.vue'

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
const evaluationMode = ref<'auto' | 'manual'>('auto')  // 评测模式

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
  text_evaluation_prompt: '',
  evaluation_mode: 'auto' // 默认使用自动评测
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
const isManualEvaluating = ref(false) // 手动评测状态
const manualEvaluationAnswers = ref<any[]>([]) // 手动评测答案列表
const currentAnswerIndex = ref(0) // 当前评测的答案索引
const selectedAnswerIndex = ref(-1) // 当前选中的答案索引（用于列表模式）
const hasSelectedEvaluationMode = ref(false)

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
const showProgressDialog = ref(false) // 进度弹窗控制
const showResultsDialog = ref(false) // 详细结果弹窗控制
const currentTaskType = ref<'answer_generation' | 'evaluation'>('answer_generation') // 跟踪当前任务类型
const selectedAnswer = ref<any>(null)
const answerEvaluations = ref<any[]>([])
const autoEvaluating = ref(false)
const submittingEvaluation = ref(false)
const manualEvaluation = reactive({
  score: 80,
  reasoning: ''
})

// 计算属性
const selectedModel = computed(() => {
  return availableModels.value.find(m => m.id === modelConfig.model_id)
})

const isReasoningSupported = computed(() => {
  return selectedModel.value?.enable_reasoning || false
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

const isSystemPromptValid = computed(() => {  const hasChoicePrompt = choiceQuestionCount.value === 0 || systemPromptConfig.choice_system_prompt?.trim()
  const hasTextPrompt = textQuestionCount.value === 0 || systemPromptConfig.text_system_prompt?.trim()
  return hasChoicePrompt && hasTextPrompt
})

const isEvaluationConfigValid = computed(() => {  const hasChoiceEvaluation = choiceQuestionCount.value === 0 || evaluationConfig.choice_evaluation_prompt?.trim()
  const hasTextEvaluation = textQuestionCount.value === 0 || evaluationConfig.text_evaluation_prompt?.trim()
  return hasChoiceEvaluation && hasTextEvaluation
})

// 判断答案生成是否完成
const isAnswerGenerationCompleted = computed(() => {
  if (!answerGenerationTask.value) return false
  
  // 如果任务状态是 evaluating_answers，说明答案生成已完成，进入评测阶段
  return answerGenerationTask.value?.status === 'evaluating_answers'
})

// 计算步骤锁定状态
const isStepLocked = computed(() => {
  return (stepIndex: number) => {
    // 如果没有恢复的任务，不锁定任何步骤
    if (!evaluationTask.value) return false
    
    const taskStatus = evaluationTask.value?.status      // 根据任务状态确定已完成的步骤
    const completedSteps: number[] = []
      switch (taskStatus) {
      case 'config_prompts':
        completedSteps.push(0) // 参数配置已完成
        break      
      case 'generating_answers':
        completedSteps.push(0, 1) // 参数配置和提示词配置已完成，正在生成答案
        break
      case 'answers_generated':
        completedSteps.push(0, 1, 2) // 前三步已完成，答案生成完成，等待评测配置
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

const confirmEvaluationMode = async () => {
  if (!evaluationConfig.evaluation_mode) {
    showMessage('请先选择评测方式', 'error')
    return
  }
  
  hasSelectedEvaluationMode.value = true
  console.log('确认评测方式:', evaluationConfig.evaluation_mode)
  
  if (evaluationConfig.evaluation_mode === 'manual') {
    // 如果选择手动评测，直接启动手动评测流程
    await startManualEvaluation()
  }
  // 自动评测的逻辑保持不变，用户需要在下一个界面配置后再启动
}

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
  return llmAnswers.value?.slice(start, end) || []
})

// 详细结果分页
const paginatedDetailedAnswers = computed(() => {
  if (!detailedResults.value || !detailedResults.value.detailed_answers) return []
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return detailedResults.value.detailed_answers?.slice(start, end) || []
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
    const status = evaluationTask.value?.status
    
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

// 监听器
// 当模型选择变化时，检查推理支持并自动禁用推理模式
watch(selectedModel, (newModel, oldModel) => {
  if (newModel && !newModel.enable_reasoning && modelConfig.enable_reasoning) {
    modelConfig.enable_reasoning = false
    showMessage('当前模型不支持推理模式，已自动禁用', 'warning')
  }
}, { immediate: true })

// 生命周期
onMounted(async () => {
  await initializeView()
})

// 初始化视图
const initializeView = async () => {
  try {
    // 获取路由参数
    const datasetId = route.params.datasetId as string
    const versionId = route.params.versionId as string
    const taskId = route.query.taskId as string
    const step = route.query.step as string
    const view = route.query.view as string
    
    if (!datasetId) {
      showMessage('未指定数据集', 'error')
      return
    }
    
    // 加载数据集信息
    await loadDatasetInfo(parseInt(datasetId), parseInt(versionId))
    
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
    
    console.log('恢复任务:', task?.name, '状态:', task?.status)
    
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
        evaluationConfig.text_evaluation_prompt = task.evaluation_prompt      }
    }
    
    // 根据任务状态决定显示内容
    if (task?.status === 'generating_answers') {
      // 正在生成答案 - 显示第三阶段并弹出答案生成进度弹窗
      currentStep.value = 2
      currentTaskType.value = 'answer_generation'
      showProgressDialog.value = true      
      startProgressPolling()
      showMessage('正在生成答案，请查看进度...', 'info')    } else if (task?.status === 'evaluating_answers') {
      // 答案生成完成，正在评测阶段 - 显示评测进度弹窗
      currentStep.value = 3
      answerGenerationTask.value = task // 设置答案生成任务，用于评测
      evaluationTask.value = task // 确保设置评测任务
      
      // 显示评测进度弹窗
      currentTaskType.value = 'evaluation'
      showProgressDialog.value = true
      startProgressPolling()
      
      showMessage('正在进行LLM评测，请查看进度...', 'info')
    } else if (task?.status === 'completed') {
      // 已完成 - 跳转到结果页面并加载详细结果
      currentStep.value = 4
      await loadTaskDetailedResults()
      showMessage('任务已完成，查看评测结果', 'success')
      
    } else if (task?.status === 'failed') {
      // 失败 - 跳转到结果页面显示错误信息
      currentStep.value = 4
      showMessage('任务执行失败，请查看错误信息', 'error')
      
    } else if (task?.status === 'cancelled') {
      // 已取消 - 跳转到结果页面
      currentStep.value = 4
      showMessage('任务已取消', 'warning')
      
    } else if (task?.status === 'config_prompts') {
      // 配置提示词阶段 - 跳转到第二阶段
      currentStep.value = 1
      showMessage('继续配置系统Prompt', 'info')
      
    } else {
      // 其他状态（如config_params）- 跳转到第一阶段
      currentStep.value = 0
      showMessage('继续配置模型参数', 'info')
    }
    
    console.log(`任务恢复完成: ${task?.name || `任务#${taskId}`}, 当前步骤: ${currentStep.value}`)  } catch (error) {
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
      console.log('查看任务结果:', task?.name, '状态:', task?.status)
    
    // 设置evaluationTask
    evaluationTask.value = task
    
    // 直接跳转到结果页面
    currentStep.value = 4
    
    // 根据任务状态加载相应的结果
    if (task?.status === 'completed') {
      // 已完成任务，加载详细结果
      await loadTaskDetailedResults()
      showMessage('正在查看评测结果', 'success')
    } else if (task?.status === 'failed') {
      // 失败任务，显示错误信息
      showMessage('任务执行失败', 'error')
    } else if (task?.status === 'generating_answers' || task?.status === 'evaluating_answers') {
      // 正在进行的任务，显示进度
      showMessage('任务正在进行中', 'info')
    } else {
      // 其他状态的任务
      showMessage('任务未完成，无法查看结果', 'warning')
    }
    
    console.log(`结果查看完成: ${task?.name || `任务#${taskId}`}`)
  } catch (error) {
    console.error('加载任务结果失败:', error)
    showMessage('加载任务结果失败', 'error')
  }
}

// 加载数据集信息
const loadDatasetInfo = async (datasetId: number, versionId: number) => {
  try {
    console.log("load version:", versionId)
    currentDataset.value = await llmEvaluationService.getDatasetInfo(datasetId, versionId)
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
    evaluationConfig.choice_evaluation_prompt = '请评估以下选择题的回答质量：\n\n评估标准：\n1. 答案正确性 (50分)：是否选择了正确的选项\n2. 解释合理性 (30分)：解释是否逻辑清晰、合理\n3. 格式规范性 (20分)：是否按照要求的格式回答\n\n请按照以下JSON格式给出评分：\n{{"score": 85, "reasoning": "答案正确，解释清晰合理，格式规范"}}'
    evaluationConfig.text_evaluation_prompt = '请根据以下标准评估文本回答质量：\n\n评估标准：\n1. 准确性 (40分)：内容是否正确、符合事实\n2. 完整性 (30分)：是否全面回答了问题的各个方面\n3. 清晰性 (20分)：表达是否清楚、逻辑是否清晰\n4. 实用性 (10分)：回答是否对提问者有帮助\n\n请按照以下JSON格式给出评分：\n{{"score": 85, "reasoning": "内容准确，覆盖全面，表达清晰"}}'
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
        statusUpdate = {          status: 'config_prompts',
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
          choice_system_prompt: systemPromptConfig.choice_system_prompt,
          text_system_prompt: systemPromptConfig.text_system_prompt,
          system_prompt: activeSystemPromptTab.value === 'choice' 
            ? systemPromptConfig.choice_system_prompt 
            : systemPromptConfig.text_system_prompt  // 兼容性保留
        }
        break
          case 3: // 评测配置步骤
        statusUpdate = {
          status: 'evaluating_answers',
          choice_evaluation_prompt: evaluationConfig.choice_evaluation_prompt,
          text_evaluation_prompt: evaluationConfig.text_evaluation_prompt,
          evaluation_prompt: activeEvaluationTab.value === 'choice' 
            ? evaluationConfig.choice_evaluation_prompt 
            : evaluationConfig.text_evaluation_prompt  // 兼容性保留
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
    evaluationConfig.choice_evaluation_prompt = '请评估以下选择题的回答质量：\n\n评估标准：\n1. 答案正确性 (50分)：是否选择了正确的选项\n2. 解释合理性 (30分)：解释是否逻辑清晰、合理\n3. 格式规范性 (20分)：是否按照要求的格式回答\n\n请按照以下JSON格式给出评分：\n{{"score": 85, "reasoning": "答案正确，解释清晰合理，格式规范"}}'
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
    evaluationConfig.text_evaluation_prompt = '请根据以下标准评估文本回答质量：\n\n评估标准：\n1. 准确性 (40分)：内容是否正确、符合事实\n2. 完整性 (30分)：是否全面回答了问题的各个方面\n3. 清晰性 (20分)：表达是否清楚、逻辑是否清晰\n4. 实用性 (10分)：回答是否对提问者有帮助\n\n请按照以下JSON格式给出评分：\n{{"score": 85, "reasoning": "内容准确，覆盖全面，表达清晰"}}'
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
      task_name: answerGenerationOptions.task_name || `${currentDataset.value?.name} - 答案生成`,
      dataset_id: currentDataset.value.id,
      model_config: {
        model_id: modelConfig.model_id!, 
        api_key: modelConfig.api_key,
        choice_system_prompt: systemPromptConfig.choice_system_prompt,
        text_system_prompt: systemPromptConfig.text_system_prompt,
        system_prompt: systemPromptConfig.choice_system_prompt || systemPromptConfig.text_system_prompt,  // 兼容性保留
        temperature: modelConfig.temperature,
        max_tokens: modelConfig.max_tokens,
        top_k: modelConfig.top_k,
        enable_reasoning: modelConfig.enable_reasoning
      },
      evaluation_config: {
        choice_evaluation_prompt: evaluationConfig.choice_evaluation_prompt,
        text_evaluation_prompt: evaluationConfig.text_evaluation_prompt,
        evaluation_prompt: evaluationConfig.choice_evaluation_prompt || evaluationConfig.text_evaluation_prompt  // 兼容性保留
      },
      is_auto_score: false, // 答案生成阶段不自动评分
      question_limit: answerGenerationOptions.question_limit_type === 'limit' ? answerGenerationOptions.question_limit : undefined
    }
      console.log('Task Data to be sent:', JSON.stringify(taskData, null, 2))
    
    // 调用API创建并启动任务
    answerGenerationTask.value = await llmEvaluationService.createEvaluationTask(taskData)
    
    showMessage('答案生成任务已创建，开始生成...', 'success')
      // 显示进度弹窗而不是跳转到下一步
    evaluationTask.value = answerGenerationTask.value // 将答案生成任务赋值给评测任务以便进度弹窗使用
    currentTaskType.value = 'answer_generation' // 设置任务类型为答案生成
    showProgressDialog.value = true
    
    // 防止页面滚动
    document.body.style.overflow = 'hidden'
    
    console.log('答案生成弹窗已显示，任务类型:', currentTaskType.value)
    console.log('弹窗状态:', showProgressDialog.value)
    
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
    
    // 更新当前评测任务，立即设置为评测状态
    evaluationTask.value = {
      ...answerGenerationTask.value,
      status: 'evaluating_answers'  // 立即设置为评测状态
    }
      // 立即设置任务类型为评测并显示进度弹窗
    currentTaskType.value = 'evaluation'
    showProgressDialog.value = true
    
    // 防止页面滚动
    document.body.style.overflow = 'hidden'
    
    console.log('评测弹窗已显示，任务类型:', currentTaskType.value)
    console.log('弹窗状态:', showProgressDialog.value)
    
    // 开始轮询进度
    startProgressPolling()
  } catch (error: any) {
    console.error('启动评测失败:', error)
    showMessage('启动评测失败: ' + error.message, 'error')
  } finally {
    starting.value = false
  }
}

// 停止进度轮询的通用函数
const stopProgressPolling = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
    console.log('已停止进度轮询')
  }
}

const startProgressPolling = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
  }
  
  progressTimer = setInterval(async () => {
    if (!evaluationTask.value?.id) return
      // 检查用户是否还在登录状态
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.log('用户已退出登录，停止轮询')
      stopProgressPolling()
      return
    }
    
    try {
      const progress = await llmEvaluationService.getTaskProgress(evaluationTask.value.id)
      taskProgress.value = progress
      
      // 更新任务状态
      evaluationTask.value = {
        ...evaluationTask.value,
        ...progress
      }
      
      // 任务类型处理逻辑：
      // 1. 如果当前没有设置任务类型，根据状态自动设置
      // 2. 如果任务状态从答案生成转为评测，自动切换任务类型
      // 3. 如果已经是评测类型，保持不变
      if (!currentTaskType.value) {
        if (progress?.status === 'generating_answers') {
          currentTaskType.value = 'answer_generation'
        } else if (progress?.status === 'evaluating_answers') {
          currentTaskType.value = 'evaluation'
        }
      } else if (progress?.status === 'evaluating_answers' && currentTaskType.value === 'answer_generation') {
        // 状态从答案生成切换到评测时，更新任务类型
        currentTaskType.value = 'evaluation'
        console.log('任务类型已切换为评测')
      }
      
      console.log('轮询进度 - 任务状态:', progress?.status, '任务类型:', currentTaskType.value)      // 如果任务完成，停止轮询并加载结果
      if (progress?.status === 'completed' || progress?.status === 'failed' || progress?.status === 'answers_generated') {
        stopProgressPolling()
        if (progress?.status === 'completed') {// 根据任务类型决定下一步操作
          if (currentTaskType.value === 'answer_generation') {
            showMessage('答案生成完成！', 'success')
            
            // 更新任务状态以确保步骤锁定逻辑正确工作
            if (evaluationTask.value) {
              evaluationTask.value = { ...evaluationTask.value, status: 'answers_generated' }
            }
              // 关闭进度弹窗并跳转到评测配置步骤（第四阶段，索引为3）
            showProgressDialog.value = false
            document.body.style.overflow = 'auto'
            currentStep.value = 3 // 跳转到评测配置步骤
          } else {
            await loadTaskResults()
            showMessage('评测任务完成！', 'success')
            // 关闭进度弹窗并跳转到结果页面
            showProgressDialog.value = false
            document.body.style.overflow = 'auto'
            currentStep.value = 4 // 直接跳转到结果页面
          }} else if (progress?.status === 'answers_generated') {
          // 答案生成完成，等待评测配置
          showMessage('答案生成完成！请配置评测参数', 'success')
          
          // 更新任务状态以确保步骤锁定逻辑正确工作
          if (evaluationTask.value) {
            evaluationTask.value = { ...evaluationTask.value, status: 'answers_generated' }
          }
          answerGenerationTask.value = evaluationTask.value // 保存答案生成任务
            // 关闭进度弹窗并跳转到评测配置步骤
          showProgressDialog.value = false
          document.body.style.overflow = 'auto'
          currentStep.value = 3 // 跳转到评测配置步骤
        } else {
          const taskName = currentTaskType.value === 'answer_generation' ? '答案生成' : '评测'
          showMessage(`${taskName}任务失败`, 'error')
          showProgressDialog.value = false
          document.body.style.overflow = 'auto'
          currentStep.value = 4 // 跳转到结果页面显示错误
        }
      }    } catch (error: any) {
      console.error('获取进度失败:', error)
        // 如果是403错误（未授权），说明用户已退出登录，停止轮询
      if (error.response?.status === 403) {
        console.log('用户未授权，停止轮询')
        stopProgressPolling()
        return
      }
    }
  }, 2000) // 每2秒轮询一次
}

const loadTaskResults = async () => {
  if (!evaluationTask.value?.id) return
  
  try {
    const results = await llmEvaluationService.getTaskResults(evaluationTask.value.id)
    llmAnswers.value = results.answers || []
  } catch (error) {
    console.error('加载评测结果失败:', error)
  }
}

const loadTaskDetailedResults = async () => {
  if (!evaluationTask.value?.id) return
  
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
  if (!evaluationTask.value?.id) return
  
  try {
    if (evaluationTask.value?.status === 'running') {
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

// 评测模式切换
const switchEvaluationMode = (mode: 'auto' | 'manual') => {
  evaluationMode.value = mode
  // 切换到手动模式时重置当前步骤
  if (mode === 'manual') {
    currentStep.value = 0
  }
}

// 评测模式选择
const selectEvaluationMode = (mode: 'auto' | 'manual') => {
  evaluationConfig.evaluation_mode = mode
  console.log('评测模式已切换为:', mode)
}

// 手动任务创建成功处理
const onManualTaskCreated = (task: any) => {
  console.log('Manual task created:', task)
  evaluationTask.value = task
  // 直接跳转到结果查看页面
  currentStep.value = 4
  showMessage('手动评测任务创建成功！', 'success')
}

// 开始手动评测
const startManualEvaluation = async () => {
  if (!answerGenerationTask.value || !answerGenerationTask.value.id) {
    showMessage('请先完成答案生成', 'error')
    return
  }
  
  starting.value = true
  try {
    console.log('启动手动评测，任务ID:', answerGenerationTask.value.id)
    
    // 设置手动评测状态
    isManualEvaluating.value = true
    
    // 加载需要手动评测的答案
    await loadAnswersForManualEvaluation()
    
    // 如果有数据，显示成功消息
    if (manualEvaluationAnswers.value.length > 0) {
      showMessage(`已进入手动评测模式，共${manualEvaluationAnswers.value.length}个答案待评测`, 'success')
    } else {
      showMessage('没有找到需要评测的答案', 'warning')
    }
  } catch (error: any) {
    console.error('启动手动评测失败:', error)
    showMessage('启动手动评测失败: ' + error.message, 'error')
    // 出错时重置状态
    isManualEvaluating.value = false
  } finally {
    starting.value = false
  }
}

// 加载需要手动评测的答案
const loadAnswersForManualEvaluation = async () => {
  if (!answerGenerationTask.value?.id) {
    throw new Error('没有找到答案生成任务ID')
  }
  
  try {
    console.log('开始加载答案，任务ID:', answerGenerationTask.value.id)
    // 使用正确的service方法
    const answers = await llmEvaluationService.getTaskAnswersForManualEvaluation(answerGenerationTask.value.id)
    
    if (!answers || !Array.isArray(answers)) {
      throw new Error('返回的答案数据格式不正确')
    }
    
    manualEvaluationAnswers.value = answers
    currentAnswerIndex.value = 0
    
    console.log('成功加载', manualEvaluationAnswers.value.length, '个答案待评测')
    console.log('第一个答案:', manualEvaluationAnswers.value[0])
    
    return answers
  } catch (error: any) {
    console.error('加载答案失败:', error)
    throw error
  }
}

// 获取当前问题信息
const getCurrentQuestion = () => {
  const currentAnswer = getCurrentAnswer()
  return currentAnswer?.question || null
}

// 获取当前答案信息
const getCurrentAnswer = () => {
  if (selectedAnswerIndex.value >= 0 && selectedAnswerIndex.value < manualEvaluationAnswers.value.length) {
    return manualEvaluationAnswers.value[selectedAnswerIndex.value]
  }
  // 兼容旧的currentAnswerIndex逻辑
  if (!manualEvaluationAnswers.value[currentAnswerIndex.value]) return null
  return manualEvaluationAnswers.value[currentAnswerIndex.value]
}

// 列表模式相关函数
const selectAnswer = (index: number) => {
  selectedAnswerIndex.value = index
  currentAnswerIndex.value = index // 保持兼容性
}

const closeDetail = () => {
  selectedAnswerIndex.value = -1
}

// 检查答案是否已评测
const isAnswerEvaluated = (answer: any) => {
  return answer.manual_score !== null && answer.manual_score !== undefined && 
         answer.manual_reasoning && answer.manual_reasoning.trim().length > 0
}

// 获取已评测数量
const getEvaluatedCount = () => {
  return manualEvaluationAnswers.value.filter(answer => isAnswerEvaluated(answer)).length
}

// 文本截断函数
const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 保存所有评测结果
const saveAllEvaluations = async () => {
  const unsavedAnswers = manualEvaluationAnswers.value.filter(answer => {
    return isAnswerEvaluated(answer) && !answer.is_saved
  })

  if (unsavedAnswers.length === 0) {
    showMessage('没有需要保存的评测结果', 'info')
    return
  }  try {
    let savedCount = 0
    for (const answer of unsavedAnswers) {
      await llmEvaluationService.createEvaluation({
        answer_id: answer.id,
        score: answer.manual_score,
        reasoning: answer.manual_reasoning,
        evaluator_type: 'user'
      })
      answer.is_saved = true
      savedCount++
    }
    showMessage(`已保存 ${savedCount} 个评测结果`, 'success')
  } catch (error: any) {
    console.error('批量保存失败:', error)
    showMessage('保存失败: ' + error.message, 'error')
  }
}

// 清除当前评分
const clearCurrentEvaluation = () => {
  const currentAnswer = getCurrentAnswer()
  if (currentAnswer) {
    currentAnswer.manual_score = null
    currentAnswer.manual_reasoning = ''
    currentAnswer.is_evaluated = false
    currentAnswer.is_saved = false
    showMessage('已清除当前评分', 'info')
  }
}

// 评分变化处理
const onScoreChange = () => {
  const currentAnswer = getCurrentAnswer()
  if (currentAnswer) {
    currentAnswer.is_saved = false
  }
}

// 理由变化处理
const onReasoningChange = () => {
  const currentAnswer = getCurrentAnswer()
  if (currentAnswer) {
    currentAnswer.is_saved = false
  }
}


// 保存当前评测结果
const saveCurrentEvaluation = async () => {
  const currentAnswer = getCurrentAnswer()
  if (!currentAnswer) {
    showMessage('无法保存评测结果', 'error')
    return
  }

  // 检查是否有评分和理由
  if (currentAnswer.manual_score === null || currentAnswer.manual_score === undefined) {
    showMessage('请输入评分', 'warning')
    return
  }

  if (!currentAnswer.manual_reasoning || currentAnswer.manual_reasoning.trim().length === 0) {
    showMessage('请输入评分理由', 'warning')
    return
  }  try {    // 使用通用的evaluation API
    await llmEvaluationService.createEvaluation({
      answer_id: currentAnswer.id,
      score: currentAnswer.manual_score,
      reasoning: currentAnswer.manual_reasoning,
      evaluator_type: 'user'
    })
    
    // 标记为已评测
    currentAnswer.is_evaluated = true
    
    showMessage('评测结果已保存', 'success')
  } catch (error: any) {
    console.error('保存评测失败:', error)
    showMessage('保存评测失败: ' + error.message, 'error')
  }
}

// 检查是否所有答案都已评测
const isAllEvaluated = () => {
  return manualEvaluationAnswers.value.every(answer => 
    answer.manual_score !== undefined && answer.manual_score !== null &&
    answer.manual_reasoning && answer.manual_reasoning.trim().length > 0
  )
}

// 退出手动评测
const exitManualEvaluation = async () => {
  try {
    // 保存当前评测结果
    if (manualEvaluationAnswers.value.length > 0) {
      await saveCurrentEvaluation()
    }    // 重置状态
    isManualEvaluating.value = false
    hasSelectedEvaluationMode.value = false
    evaluationConfig.evaluation_mode = ''
    currentAnswerIndex.value = 0
    selectedAnswerIndex.value = -1
    manualEvaluationAnswers.value = []
    
    // 返回到评测方式选择步骤
    showMessage('已退出手动评测，进度已保存', 'info')
  } catch (error: any) {
    console.error('退出手动评测时出错:', error)
    showMessage('退出时保存失败，但已成功退出', 'warning')
      // 即使保存失败也要重置状态
    isManualEvaluating.value = false
    hasSelectedEvaluationMode.value = false
    evaluationConfig.evaluation_mode = ''
  }
}

// 完成手动评测
const completeManualEvaluation = async () => {
  if (!isAllEvaluated()) {
    showMessage('请完成所有答案的评测', 'warning')
    return
  }

  try {
    // 保存当前评测结果（如果有的话）
    await saveCurrentEvaluation()
    
    // 更新任务状态
    if (answerGenerationTask.value) {
      evaluationTask.value = {
        ...answerGenerationTask.value,
        status: 'completed'
      }
    }
    
    // 跳转到结果页面
    isManualEvaluating.value = false
    currentStep.value = 4
    
    showMessage('手动评测已完成！', 'success')
    
    // 加载详细结果
    await loadTaskDetailedResults()
  } catch (error: any) {
    console.error('完成评测失败:', error)
    showMessage('完成评测失败: ' + error.message, 'error')
  }
}

// 格式化时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取状态类型（用于样式）
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': 'success',
    'running': 'info',
    'failed': 'error',
    'cancelled': 'warning',
    'config_params': 'info',
    'config_prompts': 'info',
    'generating_answers': 'info',
    'evaluating_answers': 'info',
    'answers_generated': 'success'
  }
  return statusMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': '已完成',
    'running': '运行中',
    'failed': '失败',
    'cancelled': '已取消',
    'config_params': '配置参数中',
    'config_prompts': '配置提示词中',
    'generating_answers': '生成答案中',
    'evaluating_answers': '评测答案中',
    'answers_generated': '答案生成完成'
  }
  return statusMap[status] || status
}

// 显示详细结果
const showDetailedResults = async () => {
  await loadTaskDetailedResults()
  showResultsDialog.value = true
}

// 下载结果
const downloadResults = async () => {
  if (!evaluationTask.value?.id) return
  
  try {
    const blob = await llmEvaluationService.downloadTaskResults(evaluationTask.value.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `evaluation-results-${evaluationTask.value.id}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    showMessage('结果下载成功', 'success')
  } catch (error: any) {
    console.error('下载失败:', error)
    showMessage('下载失败: ' + error.message, 'error')
  }
}

// 获取分数样式类
const getScoreClass = (score: number) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'average'
  if (score >= 60) return 'below-average'
  return 'poor'
}

// 查看详细评测
const viewDetailedEvaluation = (answer: any) => {
  selectedAnswer.value = answer
  showEvaluationDialog.value = true
}

// 获取题目类型文本
const getQuestionTypeText = (type: string) => {
  return type === 'choice' ? '选择题' : '文本题'
}

// 下载详细结果
const downloadDetailedResults = async () => {
  if (!evaluationTask.value?.id) return
  
  try {
    const blob = await llmEvaluationService.downloadTaskResults(evaluationTask.value.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `detailed-results-${evaluationTask.value.id}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    showMessage('详细结果下载成功', 'success')
  } catch (error: any) {
    console.error('下载失败:', error)
    showMessage('下载失败: ' + error.message, 'error')
  }
}

// 下载答案数据
const downloadAnswersOnly = async () => {
  if (!evaluationTask.value?.id) return
  
  try {
    const blob = await llmEvaluationService.downloadAnswersOnly(evaluationTask.value.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `answers-only-${evaluationTask.value.id}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    showMessage('答案数据下载成功', 'success')
  } catch (error: any) {
    console.error('下载失败:', error)
    showMessage('下载失败: ' + error.message, 'error')
  }
}

// 自动评测
const autoEvaluate = async () => {
  if (!selectedAnswer.value) return
  
  autoEvaluating.value = true
  try {
    const result = await llmEvaluationService.autoEvaluateAnswer(
      selectedAnswer.value.id,
      { use_llm: true }
    )
    
    // 更新答案的评测结果
    if (result.evaluation) {
      answerEvaluations.value.push(result.evaluation)
    }
    
    showMessage('自动评测完成', 'success')
  } catch (error: any) {
    console.error('自动评测失败:', error)
    showMessage('自动评测失败: ' + error.message, 'error')
  } finally {
    autoEvaluating.value = false
  }
}

// 提交手动评测
const submitManualEvaluation = async () => {
  if (!selectedAnswer.value) return
  
  submittingEvaluation.value = true
  try {
    const result = await llmEvaluationService.submitManualEvaluation(
      selectedAnswer.value.id,      {
        score: manualEvaluation.score,
        reasoning: manualEvaluation.reasoning
      }
    )
    
    // 更新答案的评测结果
    if (result.evaluation) {
      answerEvaluations.value.push(result.evaluation)
    }
    
    showMessage('手动评测提交成功', 'success')
    showEvaluationDialog.value = false
  } catch (error: any) {
    console.error('提交评测失败:', error)
    showMessage('提交评测失败: ' + error.message, 'error')
  } finally {
    submittingEvaluation.value = false
  }
}

// 关闭进度弹窗
const closeProgressDialog = () => {
  showProgressDialog.value = false
  document.body.style.overflow = 'auto'
  // 关闭弹窗时也停止轮询，避免后台继续请求
  stopProgressPolling()
}

// 格式化时间
const formatTime = (seconds: number) => {
  if (!seconds || seconds <= 0) return '计算中...'
  
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

// 从进度弹窗返回市场
const backToMarketplaceFromProgress = () => {
  closeProgressDialog()
  router.push('/llm-marketplace')
}

// 从进度弹窗查看结果
const viewResultsFromProgress = async () => {
  closeProgressDialog()
  await loadTaskDetailedResults()
  currentStep.value = 4
}

// 组件清理：在组件销毁时清理定时器
onUnmounted(() => {
  stopProgressPolling()
  console.log('组件销毁，已清理进度轮询定时器')
})

// 路由离开守卫：在路由切换时清理定时器
onBeforeRouteLeave((to, from, next) => {
  stopProgressPolling()
  console.log('路由离开，已清理进度轮询定时器')
  next()
})

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

/* 弹窗样式 */
.modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  background: rgba(0, 0, 0, 0.6) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 10000 !important;
  backdrop-filter: blur(4px);
}

.modal-content,
.progress-modal-content,
.results-modal-content {
  background: white !important;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 90vw;
  max-height: 90vh;
  min-width: 500px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 10001 !important;
}

.progress-modal-content {
  width: 650px;
  max-width: 90vw;
  border: 3px solid #667eea !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(102, 126, 234, 0.3) !important;
}

.modal-header,
.progress-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.modal-header h3,
.progress-modal-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 18px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #718096;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e2e8f0;
  color: #2d3748;
}

.modal-body,
.progress-modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  min-height: 200px;
}

.progress-modal-header {
  position: sticky;
  top: 0;
  background: #f8fafc;
  z-index: 10;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

/* 模式选择 */
.mode-selector {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-bottom: 2rem;
  text-align: center;
}

.mode-tabs {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
}

.tab-btn {
  padding: 0.75rem 2rem;
  border: 2px solid #e9ecef;
  background: white;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tab-btn:hover {
  border-color: #007bff;
  background: #f8f9fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.tab-btn.active {
  border-color: #007bff;
  background: #007bff;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.tab-btn.active:hover {
  background: #0056b3;
  border-color: #0056b3;
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

.form-range {  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e9ecef;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
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

/* .statistics-section,
.detailed-answers-section { margin: 0;
  background: rgba(255, 255, 255, 0.95);  color: #2c3e50;
  backdrop-filter: blur(20px); 20px;
  border-radius: 16px;00;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2); font-size: 24px;
  transition: all 0.3s ease;}
} */

/* .mode-selector {
  margin-bottom: 2rem; text-align: center;
  text-align: center;  border: 1px solid #dee2e6;
} 0.3s ease;  */

/* .mode-tabs {
  display: flex; 
  justify-content: 
  center; transform: translateY(-2px);
  gap: 1rem;
  adow: 0 4px 15px rgba(0, 0, 0, 0.1);
} */

.tab-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #007bff;
  color: #007bff;
  background: white;
  transition: all 0.3s ease;
  cursor: pointer;
  font-size: 1rem;
  border-radius: 8px;
}

.tab-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.tab-btn:hover {
  transition: all 0.3s ease;
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
}

/* 进度弹窗样式 */
.progress-modal-content {
  background: linear-gradient(135deg, #bee3f8 0%, #90cdf4 100%);
  border: 1px solid #63b3ed;
}

.progress-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-section {
  background: linear-gradient(135deg, #feebc8 0%, #fbd38d 100%);
  border: 1px solid #f6ad55;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.score-value.score-poor {
  background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
  border: 1px solid #fc8181;
}

.status-item {
  display: flex;
  justify-content: space-between;
  width: 100%;
  font-size: 14px;
  color: #495057;
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-info {
  padding: 2px 4px;
  border-radius: 3px;
}

/* 最新内容预览样式 */
.latest-content {
  margin-top: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.content-preview h5 {
  margin: 0 0 12px 0;
  color: #2d3748;
  font-size: 14px;
  font-weight: 600;
}

.content-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.content-text {
  background: white;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  font-size: 13px;
  line-height: 1.5;
  color: #4a5568;
  white-space: pre-wrap;
  word-break: break-word;
}

.score-info {
  display: flex;
  justify-content: flex-end;
}

.score-badge {
  background: #4299e1;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.close-btn:hover {
  background: #68d391;
  border: 1px solid #68d391;
  color: #495057;
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

/* 详细结果弹窗样式 */
.results-modal-content {
  width: 95%;
  max-width: 1200px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.results-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

/* 任务概览样式 */
.task-overview {
  margin: 20px 0;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.overview-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.overview-icon {
  font-size: 2.5rem;
  margin-right: 16px;
}

.overview-info h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.overview-info p {
  margin: 4px 0;
  opacity: 0.9;
  font-size: 14px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.primary {
  background: #4299e1;
  color: white;
}

.status-badge.success {
  background: #48bb78;
  color: white;
}

.status-badge.warning {
  background: #ed8936;
  color: white;
}

.status-badge.danger {
  background: #f56565;
  color: white;
}

.status-badge.secondary {
  background: #718096;
  color: white;
}

/* 推理模式相关样式 */
.unsupported-badge {
  background: #fed7d7;
  color: #c53030;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 8px;
}

.warning-tip {
  color: #ed8936 !important;
  font-weight: 500;
}

/* 手动评测界面样式 */
.manual-evaluation-interface {
  max-width: 1200px;
  margin: 0 auto;
}

.manual-progress {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
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

.current-index, .total-count {
  font-size: 14px;
  color: #4a5568;
  font-weight: 500;
}

.progress-percentage {
  font-size: 18px;
  font-weight: 700;
  color: #667eea;
}

.progress-bar {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.question-section, .standard-answer-section, .llm-answer-section, .evaluation-form {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.question-type-badge {
  background: #667eea;
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}

.question-body {
  font-size: 16px;
  line-height: 1.6;
  color: #2d3748;
  margin-bottom: 16px;
}

.choices-section {
  margin-top: 16px;
}

.choices-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.choice-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  transition: all 0.2s;
}

.choice-item.correct {
  background: #f0fff4;
  border-color: #68d391;
}

.choice-label {
  font-weight: 600;
  color: #4a5568;
  min-width: 20px;
}

.choice-text {
  flex: 1;
  color: #2d3748;
}

.correct-mark {
  color: #38a169;
  font-weight: 600;
  font-size: 12px;
}

.standard-answer-content, .llm-answer-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.answer-text {
  font-size: 15px;
  line-height: 1.6;
  color: #2d3748;
  margin-bottom: 12px;
}

.scoring-points {
  margin-top: 16px;
}

.scoring-points-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
}

.scoring-point {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-bottom: 8px;
}

.point-text {
  flex: 1;
  color: #2d3748;
}

.point-score {
  font-weight: 600;
  color: #667eea;
}

.answer-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #718096;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.form-grid {
  display: grid;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-label {
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 8px;
  font-size: 14px;
}

.score-input-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.score-input {
  padding: 10px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s;
  max-width: 120px;
}

.score-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.score-slider {
  width: 100%;
}

.form-range {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
}

.form-range::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.form-range::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.form-textarea {
  padding: 12px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.2s;
  font-family: inherit;
}

.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.manual-evaluation-actions {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.navigation-buttons, .action-buttons {
  display: flex;
  gap: 12px;
}

.completion-notice {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-top: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.notice-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
  border: 1px solid #68d391;
  border-radius: 8px;
}

.notice-icon {
  font-size: 24px;
}

.notice-content h5 {
  margin: 0 0 4px 0;
  color: #2d3748;
  font-size: 16px;
}

.notice-content p {
  margin: 0;
  color: #4a5568;
  font-size: 14px;
}

/* 手动评测列表样式 */
.evaluation-stats {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #718096;
  font-weight: 500;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: #2d3748;
}

.answers-list {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.list-header h4 {
  margin: 0;
  color: #2d3748;
  font-size: 16px;
}

.list-actions {
  display: flex;
  gap: 12px;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
}

.answers-table {
  width: 100%;
}

.table-header {
  display: grid;
  grid-template-columns: 50px 1fr 80px 80px 80px 100px;
  gap: 16px;
  align-items: center;
  padding: 16px 20px;
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  font-weight: 600;
  font-size: 14px;
  color: #475569;
}

.table-body {
  max-height: 400px;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 50px 1fr 80px 80px 80px 100px;
  gap: 16px;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: all 0.2s ease;
}

.table-row:hover {
  background: #f8fafc;
}

.table-row.selected {
  background: #e6f3ff;
  border-color: #3b82f6;
}

.table-row.evaluated {
  background: #f0f9ff;
}

.table-row.not-evaluated {
  background: #fffbeb;
}

.col {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.col-index {
  justify-content: center;
  font-weight: 600;
  color: #64748b;
}

.col-question {
  flex: 1;
}

.question-preview {
  color: #374151;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.type-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.type-badge.choice {
  background: #dbeafe;
  color: #1e40af;
}

.type-badge.text {
  background: #dcfce7;
  color: #166534;
}

.score-display {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.score-value {
  font-weight: 600;
  color: #059669;
}

.score-unit {
  font-size: 12px;
  color: #6b7280;
}

.no-score {
  color: #9ca3af;
  font-style: italic;
  font-size: 12px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.answer-detail {
  background: white;
  border-radius: 12px;
  margin-top: 20px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 2px solid #e6f3ff;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.detail-header h4 {
  margin: 0;
  color: #2d3748;
  font-size: 18px;
}

.answer-detail .question-section,
.answer-detail .standard-answer-section,
.answer-detail .llm-answer-section,
.answer-detail .evaluation-form {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.answer-detail h5 {
  margin: 0 0 12px 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
}

.answer-detail h6 {
  margin: 0 0 8px 0;
  color: #374151;
  font-size: 14px;
  font-weight: 600;
}

.evaluation-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  justify-content: flex-end;
}

/* 手动评测加载和状态样式 */
.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-left: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-section p {
  color: #718096;
  font-size: 16px;
  margin: 0;
}

.no-data-section {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
}

.no-data-content {
  text-align: center;
  max-width: 400px;
}

.no-data-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.no-data-content h4 {
  color: #2d3748;
  margin: 0 0 8px 0;
  font-size: 20px;
}

.no-data-content p {
  color: #718096;
  margin: 0 0 24px 0;
  line-height: 1.6;
}

/* 标准答案样式增强 */
.std-answer-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.std-answer-item:last-child {
  margin-bottom: 0;
}

.std-answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.std-answer-header h5 {
  margin: 0;
  color: #2d3748;
  font-size: 16px;
  font-weight: 600;
}

.answered-by {
  font-size: 12px;
  color: #718096;
  background: #edf2f7;
  padding: 2px 8px;
  border-radius: 12px;
}

.point-order {
  font-size: 12px;
  color: #718096;
  font-weight: 500;
}

.validity-status {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
}

.validity-status.valid {
  background: #c6f6d5;
  color: #2f855a;
}

.validity-status.invalid {
  background: #fed7d7;
  color: #c53030;
}

/* 评测方式选择样式 */
.evaluation-mode-selection {
  margin: 24px 0;
}

.mode-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.mode-button {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  position: relative;
  overflow: hidden;
}

.mode-button:hover {
  border-color: #cbd5e0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.mode-button.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
  transform: translateY(-4px);
}

.mode-button.selected::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.mode-button.not-selected {
  opacity: 0.6;
  filter: grayscale(0.3);
}

.auto-mode.selected {
  border-color: #38a169;
}

.auto-mode.selected::before {
  background: linear-gradient(90deg, #38a169 0%, #48bb78 100%);
}

.manual-mode.selected {
  border-color: #3182ce;
}

.manual-mode.selected::before {
  background: linear-gradient(90deg, #3182ce 0%, #4299e1 100%);
}

.button-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.mode-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7fafc;
  border-radius: 12px;
  flex-shrink: 0;
}

.mode-button.selected .mode-icon {
  background: rgba(102, 126, 234, 0.1);
}

.auto-mode.selected .mode-icon {
  background: rgba(56, 161, 105, 0.1);
}

.manual-mode.selected .mode-icon {
  background: rgba(49, 130, 206, 0.1);
}

.mode-title {
  flex: 1;
}

.mode-title h5 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.mode-subtitle {
  font-size: 14px;
  color: #718096;
  font-weight: 500;
}

.selection-indicator {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.check-mark {
  width: 20px;
  height: 20px;
  background: #48bb78;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  animation: checkAppear 0.3s ease;
}

@keyframes checkAppear {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.mode-description {
  color: #4a5568;
  line-height: 1.6;
}

.mode-description p {
  margin: 0 0 12px 0;
  font-size: 14px;
}

.mode-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-tag {
  background: #edf2f7;
  color: #4a5568;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.mode-button.selected .feature-tag {
  background: rgba(102, 126, 234, 0.1);
  color: #553c9a;
}

.auto-mode.selected .feature-tag {
  background: rgba(56, 161, 105, 0.1);
  color: #2f855a;
}

.manual-mode.selected .feature-tag {
  background: rgba(49, 130, 206, 0.1);
  color: #2c5282;
}

.selection-hint {
  margin-top: 24px;
  padding: 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 12px;
}

.hint-content {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #0c4a6e;
  font-size: 14px;
}

.hint-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.btn.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .mode-buttons {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .button-header {
    gap: 12px;
  }
  
  .mode-icon {
    width: 40px;
    height: 40px;
    font-size: 24px;
  }
  
  .mode-title h5 {
    font-size: 16px;
  }
  
  .mode-features {
    gap: 6px;
  }
  
  .feature-tag {
    font-size: 11px;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .manual-evaluation-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .navigation-buttons, .action-buttons {
    justify-content: center;
  }
  
  .progress-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .choice-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
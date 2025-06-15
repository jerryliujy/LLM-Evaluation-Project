<template>
  <div class="database-view">    <div class="header">
      <div class="header-left">
        <div class="dataset-info" v-if="currentDataset">
          <h2>{{ currentDataset.name }}</h2>
          <p class="dataset-description">{{ currentDataset.description }}</p>
        </div>
        <h2 v-else>数据库管理</h2>
      </div>      <div class="header-actions">        <select v-model="selectedTable" @change="loadTableData" class="table-select">
          <option value="overview_std">标准问答总览</option>
          <option value="std_questions">标准问题</option>
          <option value="std_answers">标准答案</option>
        </select>
        <button @click="createNewVersion" class="create-version-btn">
          创建新版本
        </button>
        <button @click="refreshData" class="refresh-btn" :disabled="loading">
          {{ loading ? "加载中..." : "刷新" }}
        </button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总计:</span>
        <span class="stat-value">{{ totalItems }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">当前页:</span>
        <span class="stat-value">{{ currentData.length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已删除:</span>
        <span class="stat-value">{{ deletedCount }}</span>
      </div>
    </div>    <!-- 操作栏 -->
    <div class="actions-bar" v-if="!isOverviewTable">      <div class="bulk-actions">
        <button 
          @click="selectAll" 
          class="action-btn"
          :disabled="currentData.length === 0"
        >
          {{ selectedItems.length === currentData.length ? "取消全选" : "全选" }}
        </button>        <!-- 在非纯删除模式下显示删除按钮 -->
        <button 
          v-if="viewMode !== 'deleted_only'"
          @click="bulkDelete" 
          class="action-btn danger"
          :disabled="selectedItems.length === 0 || selectedDeletedItems.length === selectedItems.length"
        >
          批量删除 ({{ selectedItems.length - selectedDeletedItems.length }})
        </button>          
        <button 
          v-if="viewMode === 'deleted_only'"
          @click="bulkRestore" 
          class="action-btn success"
          :disabled="selectedItems.length === 0"
        >
          批量恢复 ({{ selectedItems.length }})
        </button>
      </div>      <!-- 搜索和过滤选项 -->
      <div class="search-filters">        <!-- 标准问题的搜索选项 -->
        <template v-if="selectedTable === 'std_questions'">
          <div class="search-input-group">
            <span class="search-icon">🔍</span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索问题内容..."
              class="search-input"
              @input="handleSearch"
            />
          </div>
          <div class="filter-input-group">
            <span class="filter-icon">🏷️</span>
            <input
              v-model="tagFilter"
              type="text"
              placeholder="过滤标签..."
              class="filter-input"
              @input="handleSearch"
            />
          </div>
          <div class="select-group">
            <select v-model="questionTypeFilter" @change="handleSearch" class="filter-select">
              <option value="">所有问题类型</option>
              <option value="text">文本题</option>
              <option value="choice">选择题</option>
            </select>
          </div>
        </template>

        <!-- 标准答案的搜索选项 -->
        <template v-if="selectedTable === 'std_answers'">
          <div class="search-input-group">
            <span class="search-icon">🔍</span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索答案内容..."
              class="search-input"
              @input="handleSearch"
            />
          </div>
          <div class="filter-input-group">
            <span class="filter-icon">❓</span>
            <input
              v-model="stdQuestionFilter"
              type="text"
              placeholder="搜索关联问题..."
              class="filter-input"
              @input="handleSearch"
            />
          </div>
          <div class="filter-input-group">
            <span class="filter-icon">🎯</span>
            <input
              v-model="scoringPointFilter"
              type="text"
              placeholder="搜索得分点..."
              class="filter-input"
              @input="handleSearch"
            />
          </div>
          <div class="select-group">
            <select v-model="scoringPointsFilter" @change="handleSearch" class="filter-select">
              <option value="">得分点筛选</option>
              <option value="has_scoring_points">有得分点</option>
              <option value="no_scoring_points">无得分点</option>
            </select>
          </div>
        </template>
      </div>
        
      <div class="view-options">
        <select v-model="viewMode" @change="handleViewModeChange" class="view-mode-select">
          <option value="active_only">仅显示未删除</option>
          <option value="deleted_only">仅显示已删除</option>
          <option value="all">显示全部</option>
        </select>
        
        <select v-model="itemsPerPage" @change="loadTableData" class="per-page-select">
          <option value="20">20条/页</option>
          <option value="50">50条/页</option>
          <option value="100">100条/页</option>
        </select>
      </div>
    </div><!-- 总览操作栏 -->
    <div class="actions-bar" v-else>
      <div class="overview-info">
        <span class="info-text">总览模式：数据仅供查看，无法编辑</span>
      </div>
        <!-- 搜索和过滤选项 -->
      <div class="search-filters">
        <div class="search-input-group">
          <span class="search-icon">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索问题内容或答案内容..."
            class="search-input enhanced"
            @input="handleSearch"
          />
        </div>
        <div class="filter-input-group">
          <span class="filter-icon">🏷️</span>
          <input
            v-model="tagFilter"
            type="text"
            placeholder="过滤标签..."
            class="filter-input"
            @input="handleSearch"
          />
        </div>
        <div class="select-group">
          <select v-model="questionTypeFilter" @change="handleSearch" class="filter-select">
            <option value="">所有问题类型</option>
            <option value="text">文本题</option>
            <option value="choice">选择题</option>
          </select>
        </div>
      </div>
      
      <div class="view-options">
        <select v-model="itemsPerPage" @change="loadTableData" class="per-page-select">
          <option value="20">20条/页</option>
          <option value="50">50条/页</option>
          <option value="100">100条/页</option>
        </select>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table class="data-table" v-if="currentData.length > 0">        
        <thead>
          <tr>
            <th class="checkbox-col" v-if="!isOverviewTable">
              <input 
                type="checkbox" 
                :checked="selectedItems.length === currentData.length && currentData.length > 0"
                @change="selectAll"
              />
            </th>            <th v-for="column in tableColumns" :key="column.key" :class="column.className">
              {{ column.label }}
            </th>
            <th class="actions-col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="item in currentData" 
            :key="item.id" 
            :class="{ 'deleted-row': !item.is_valid }"
          >
            <td class="checkbox-col" v-if="!isOverviewTable">
              <input 
                type="checkbox" 
                :value="item.id" 
                v-model="selectedItems"
              />
            </td>            
            <td v-for="column in tableColumns" :key="column.key" :class="column.className">
              <div class="cell-content" :class="column.type">
                <span v-if="column.type === 'text'" class="text-content">
                  <template v-if="column.key === 'std_question_body'">
                    {{ formatCellValue(item.std_question_body, column) }}
                  </template>
                  <template v-else-if="column.key === 'expert_answers'">
                    <!-- 专家回答的特殊处理：优先显示详细信息，后备显示文本 -->
                    <span v-if="item.expert_answers_detail && item.expert_answers_detail.length > 0">
                      {{ item.expert_answers_detail.map((answer: any) => answer.content).join('; ').substring(0, 100) }}{{ item.expert_answers_detail.map((answer: any) => answer.content).join('; ').length > 100 ? '...' : '' }}
                    </span>
                    <span v-else-if="item.expert_answers && item.expert_answers !== '无专家回答'">
                      {{ formatCellValue(item.expert_answers, column) }}
                    </span>
                    <span v-else class="no-data-text">无专家回答</span>
                  </template>
                  <template v-else>
                    {{ formatCellValue(item[column.key], column) }}
                  </template>
                </span><span v-else-if="column.type === 'number' && column.key === 'scoring_points_count'" class="number-content">
                  <div class="scoring-points-count">
                    <div class="valid-count-container">
                      <span class="valid-count">{{ getScoringPointsCount(item) }}</span>
                      <span class="count-label">有效</span>
                    </div>
                    <div v-if="getDeletedScoringPointsCount(item) > 0" class="deleted-count-container" title="已删除的得分点">
                      <span class="deleted-count">{{ getDeletedScoringPointsCount(item) }}</span>
                      <span class="count-label deleted">已删除</span>
                    </div>
                  </div>
                </span>
                <span v-else-if="column.type === 'number'" class="number-content">
                  {{ item[column.key] || 0 }}
                </span>
                <span v-else-if="column.type === 'date'" class="date-content">
                  {{ formatDate(item[column.key]) }}
                </span>                
                <span v-else-if="column.type === 'tags'" class="tags-content">
                  <span 
                    v-for="tag in parseTagsValue(item[column.key])" 
                    :key="tag" 
                    class="tag"
                  >
                    {{ tag }}
                  </span>
                </span>
                <span v-else class="default-content">
                  {{ item[column.key] }}
                </span>
              </div>
            </td>            <td class="actions-col">
              <div class="row-actions">
                <button 
                  @click="viewItem(item)" 
                  class="action-btn small"
                  title="查看详情"
                >
                  👁️
                </button>
                <template v-if="!isOverviewTable">
                  <!-- 标准问题和标准答案绑定删除恢复逻辑 -->                 
                  <template v-if="selectedTable === 'std_questions' || selectedTable === 'std_answers'">
                    <button 
                      v-if="item.is_valid"
                      @click="editItem(item)" 
                      class="action-btn small"
                      title="编辑"
                    >
                      ✏️
                    </button>
                    <!-- 得分点管理按钮：只在标准答案视图中显示，且非选择题类型 -->                    <button 
                      v-if="selectedTable === 'std_answers' && item.is_valid && shouldShowScoringPointsButton(item)"
                      @click="manageScoringPoints(item)" 
                      :class="['action-btn', 'small', 'scoring-btn', { 'has-deleted': getDeletedScoringPointsCount(item) > 0 }]"
                      title="管理得分点 (有效: {{ getScoringPointsCount(item) }}, 已删除: {{ getDeletedScoringPointsCount(item) }})"
                    >
                      🎯
                    </button>
                    <template v-if="item.is_valid">
                      <button 
                        @click="deleteStdItem(item)" 
                        class="action-btn small danger"
                        title="删除（将同时删除关联的标准问题/答案）"
                      >
                        🗑️
                      </button>
                    </template>
                    <template v-else>
                      <button 
                        @click="restoreStdItem(item)" 
                        class="action-btn small success"
                        title="恢复（将同时恢复关联的标准问题/答案）"
                      >
                        ♻️
                      </button>
                      <button 
                        @click="forceDeleteStdItem(item)" 
                        class="action-btn small danger"
                        title="永久删除"
                      >
                        💀
                      </button>
                    </template>
                  </template><!-- 其他表的原有逻辑 -->
                  <template v-else>
                    <button 
                      v-if="item.is_valid"
                      @click="editItem(item)" 
                      class="action-btn small"
                      title="编辑"
                    >
                      ✏️
                    </button>
                    <template v-if="item.is_valid">
                      <button 
                        @click="deleteItem(item.id)" 
                        class="action-btn small danger"
                        title="删除"
                      >
                        🗑️
                      </button>
                    </template>
                    <template v-else>
                      <button 
                        @click="restoreItem(item.id)" 
                        class="action-btn small success"
                        title="恢复"
                      >
                        ♻️
                      </button>
                      <button 
                        @click="forceDeleteItem(item.id)" 
                        class="action-btn small danger"
                        title="永久删除"
                      >
                        💀
                      </button>
                    </template>
                  </template>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else-if="!loading" class="no-data">
        <p>暂无数据</p>
      </div>

      <div v-if="loading" class="loading">
        <p>加载中...</p>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="totalPages > 1">
      <button 
        @click="goToPage(1)" 
        :disabled="currentPage === 1"
        class="page-btn"
      >
        首页
      </button>
      <button 
        @click="goToPage(currentPage - 1)" 
        :disabled="currentPage === 1"
        class="page-btn"
      >
        上一页
      </button>
      
      <span class="page-info">
        第 {{ currentPage }} 页 / 共 {{ totalPages }} 页
      </span>
      
      <button 
        @click="goToPage(currentPage + 1)" 
        :disabled="currentPage === totalPages"
        class="page-btn"
      >
        下一页
      </button>
      <button 
        @click="goToPage(totalPages)" 
        :disabled="currentPage === totalPages"
        class="page-btn"
      >
        末页
      </button>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="showDetailModal" class="modal-overlay" @click="closeDetailModal">
      <div class="detail-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ selectedTable }} 详情</h3>
          <button @click="closeDetailModal" class="close-btn">×</button>
        </div>        
        <div class="modal-content">
          <div v-if="selectedItem" class="detail-content">            <!-- 只显示表格配置中定义的列 -->
            <div v-for="column in tableColumns" :key="column.key" class="detail-item">
              <strong>{{ column.label }}:</strong>
              <div class="detail-value" :class="{ 'multiline': column.multiline }">
                <!-- 特殊处理原始问题、原始回答和专家回答 -->
                <template v-if="column.key === 'raw_questions' && selectedItem.raw_questions_detail">
                  <div v-if="selectedItem.raw_questions_detail.length === 0" class="no-data">
                    无关联原始问题
                  </div>
                  <div v-else class="detail-list">
                    <div v-for="question in selectedItem.raw_questions_detail" :key="question.id" class="detail-box">
                      <div class="detail-box-header">
                        <span class="item-id">问题 #{{ question.id }}</span>
                        <span class="item-author">作者: {{ question.author || '匿名' }}</span>
                      </div>
                      <div class="detail-box-title">{{ question.title }}</div>
                      <div class="detail-box-content">{{ question.body }}</div>
                    </div>
                  </div>
                </template>
                
                <template v-else-if="column.key === 'raw_answers' && selectedItem.raw_answers_detail">
                  <div v-if="selectedItem.raw_answers_detail.length === 0" class="no-data">
                    无原始回答
                  </div>
                  <div v-else class="detail-list">
                    <div v-for="answer in selectedItem.raw_answers_detail" :key="answer.id" class="detail-box">
                      <div class="detail-box-header">
                        <span class="item-id">回答 #{{ answer.id }}</span>
                        <span class="item-author">作者: {{ answer.author || '匿名' }}</span>
                        <span class="item-relation">关联问题: {{ answer.question_title }}</span>
                      </div>
                      <div class="detail-box-content">{{ answer.content }}</div>
                    </div>
                  </div>
                </template>                
                <template v-else-if="column.key === 'expert_answers'">
                  
                  <!-- 优先使用expert_answers_detail -->
                  <template v-if="selectedItem.expert_answers_detail">
                    <div v-if="selectedItem.expert_answers_detail.length === 0" class="no-data">
                      无专家回答
                    </div>
                    <div v-else class="detail-list">
                      <div v-for="answer in selectedItem.expert_answers_detail" :key="answer.id" class="detail-box">
                        <div class="detail-box-header">
                          <span class="item-id">专家回答 #{{ answer.id }}</span>
                          <span class="item-author">专家: {{ answer.author || '匿名' }}</span>
                          <span class="item-relation">关联问题: {{ answer.question_title }}</span>
                        </div>
                        <div class="detail-box-content">{{ answer.content }}</div>
                      </div>
                    </div>
                  </template>
                  
                  <!-- 如果没有expert_answers_detail，则显示expert_answers的原始文本 -->
                  <template v-else>
                    <div v-if="!selectedItem.expert_answers || selectedItem.expert_answers === '无专家回答'" class="no-data">
                      无专家回答
                    </div>
                    <div v-else class="text-value">
                      {{ selectedItem.expert_answers }}
                    </div>
                  </template>
                </template><!-- 标准答案得分点的特殊显示 -->
                <template v-else-if="column.key === 'scoring_points_count'">
                  <!-- 调试信息 -->
                  <div v-if="selectedItem.id === 8" style="color: blue; font-size: 12px; margin-bottom: 5px;">
                    调试无条件: ID=8, column.key={{ column.key }}, scoring_points存在={{ !!selectedItem.scoring_points }}, 长度={{ selectedItem.scoring_points?.length }}
                  </div>
                  <div v-if="selectedItem.scoring_points" class="scoring-points-detail">
                    <div class="scoring-points-summary">
                      <span class="count">共 {{ selectedItem.scoring_points.length }} 个得分点</span>
                    </div>
                    <div v-if="selectedItem.scoring_points.length > 0" class="scoring-points-list">
                      <div v-for="(point, index) in selectedItem.scoring_points" :key="point.id" class="scoring-point-item">
                        <div class="scoring-point-header">
                          <span class="point-number">得分点 {{ index + 1 }}</span>
                          <span class="point-order">顺序: {{ point.point_order }}</span>
                        </div>
                        <div class="scoring-point-content">{{ point.answer }}</div>
                      </div>
                    </div>
                    <div v-else class="no-scoring-points">
                      暂无得分点
                    </div>
                  </div>
                </template>
                  <!-- 其他普通字段的显示 -->
                <template v-else>
                  <span v-if="column.type === 'text'" class="text-value">
                    {{ selectedItem[column.key] || '-' }}
                  </span>
                  <span v-else-if="column.type === 'number'" class="number-value">
                    {{ selectedItem[column.key] || 0 }}
                  </span>
                  <span v-else-if="column.type === 'date'" class="date-value">
                    {{ formatDate(selectedItem[column.key]) }}
                  </span>
                  <span v-else-if="column.type === 'boolean'" class="boolean-value">
                    {{ selectedItem[column.key] ? '是' : '否' }}
                  </span>
                  <span v-else class="default-value">
                    {{ selectedItem[column.key] || '-' }}
                  </span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="edit-modal" @click.stop>
        <div class="modal-header">
          <h3>编辑 {{ selectedTable }}</h3>
          <button @click="closeEditModal" class="close-btn">×</button>
        </div>
        <div class="modal-content">            <form @submit.prevent="saveEdit" class="edit-form">
            <div v-for="column in editableColumns" :key="column.key" class="form-group">
              <label :for="column.key">{{ column.label }}:</label>
              
              <!-- 标准问题类型的特殊处理 -->
              <select 
                v-if="selectedTable === 'std_questions' && column.key === 'question_type'"
                :id="column.key"
                v-model="editForm[column.key]"
                class="form-control"
              >
                <option value="text">文本题</option>
                <option value="choice">选择题</option>
              </select>
              
              <!-- 标签编辑的特殊处理 -->
              <div v-else-if="column.key === 'tags'" class="tags-editor">
                <div class="current-tags">
                  <span 
                    v-for="(tag, index) in editForm.tags" 
                    :key="index" 
                    class="tag-item"
                  >
                    {{ tag }}
                    <button 
                      type="button" 
                      @click="removeTag(index)" 
                      class="remove-tag-btn"
                      title="删除标签"
                    >
                      ×
                    </button>
                  </span>
                </div>
                <div class="add-tag">
                  <input 
                    v-model="newTag"
                    type="text" 
                    placeholder="输入新标签后按回车添加"
                    @keyup.enter="addTag"
                    class="form-control"
                  />
                  <button 
                    type="button" 
                    @click="addTag" 
                    class="add-tag-btn"
                    :disabled="!newTag.trim()"
                  >
                    添加标签
                  </button>
                </div>
              </div>
              
              <!-- 得分点编辑的特殊处理 -->
              <div v-else-if="column.key === 'scoring_points'" class="scoring-points-editor">
                <div class="scoring-points-list">
                  <div 
                    v-for="(point, index) in editForm.scoring_points" 
                    :key="index" 
                    class="scoring-point-edit-item"
                  >
                    <div class="point-header">
                      <label>得分点 {{ index + 1 }}:</label>
                    </div>
                    <textarea 
                      v-model="point.answer"
                      placeholder="输入得分点内容..."
                      rows="3"
                      class="form-control"
                    ></textarea>
                    <div class="point-order">
                      <label>排序:</label>
                      <input 
                        v-model.number="point.point_order"
                        type="number" 
                        min="1"
                        class="form-control small"
                      />
                    </div>
                  </div>
                </div>
                <button 
                  type="button" 
                  @click="addScoringPoint" 
                  class="add-point-btn"
                >
                  添加得分点
                </button>
              </div>
              
              <!-- 普通文本区域 -->
              <textarea 
                v-else-if="column.type === 'text' && column.multiline"
                :id="column.key"
                v-model="editForm[column.key]"
                :rows="3"
                class="form-control"
              ></textarea>
              <input 
                v-else
                :id="column.key"
                v-model="editForm[column.key]"
                :type="getInputType(column.type)"
                class="form-control"
              />
            </div>
            <div class="form-actions">
              <button type="button" @click="closeEditModal" class="cancel-btn">
                取消
              </button>
              <button type="submit" class="save-btn" :disabled="saving">
                {{ saving ? "保存中..." : "保存" }}
              </button>
            </div>
          </form>
        </div>
      </div>    
    </div>    <!-- 得分点管理弹窗 -->    
     <div v-if="showScoringPointsModal" class="modal-overlay" @click="closeScoringPointsModal">
      <div class="scoring-points-modal" @click.stop>
        <div class="modal-header">
          <h3>管理得分点 - {{ selectedItem?.answer || selectedItem?.std_question_body || '未知答案' }}</h3>
          <button @click="closeScoringPointsModal" class="close-btn">×</button>
        </div>
        
        <div class="modal-content">
          <div v-if="scoringPointsData.length === 0" class="no-data">
            暂无得分点
          </div>
          <div v-else class="scoring-points-list">            
            <div v-for="point in scoringPointsData" :key="point.id" 
                 :class="['scoring-point-item', { 'deleted-point': !point.is_valid }]">
              <div class="point-header">
                <span :class="['point-id', { 'deleted-text': !point.is_valid }]">得分点 #{{ point.id }}</span>
                <span class="point-order">顺序: {{ point.point_order }}</span>
                <span :class="['point-status', point.is_valid ? 'active' : 'deleted']">
                  {{ point.is_valid ? '有效' : '已删除' }}
                </span>
              </div>
              <div :class="['point-content', { 'deleted-text': !point.is_valid }]">{{ point.answer }}</div>
              <div class="point-actions">
                <template v-if="point.is_valid">
                  <button 
                    @click="deleteScoringPoint(point.id)" 
                    class="action-btn small danger"
                    title="软删除得分点"
                  >
                    🗑️ 删除
                  </button>
                </template>
                <template v-else>
                  <button 
                    @click="restoreScoringPoint(point.id)" 
                    class="action-btn small success"
                    title="恢复得分点"
                  >
                    ♻️ 恢复
                  </button>
                  <button 
                    @click="forceDeleteScoringPoint(point.id)" 
                    class="action-btn small danger"
                    title="永久删除得分点"
                  >
                    💀 永久删除
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="message" class="message" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { databaseService } from "@/services/databaseService";
import { datasetService } from "@/services/datasetService";
import { apiClient } from "@/services/api";
import { formatDate, formatTags } from "@/utils/formatters";

// 路由
const route = useRoute();
const router = useRouter();

// 类型定义
interface TableColumn {
  key: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'tags' | 'boolean' | 'action';
  className: string;
  multiline?: boolean;
}

interface TableConfig {
  columns: TableColumn[];
  editable: string[];
}

type TableName = 'std_questions' | 'std_answers' | 'overview_std';

interface DatabaseItem {
  id: number;
  is_valid?: boolean;
  [key: string]: any;
}

// 响应式数据
const selectedTable = ref<TableName>("overview_std");
const currentDatasetId = ref<number | undefined>(undefined);
const currentDataset = ref<any>(null);
const currentData = ref<DatabaseItem[]>([]);
const selectedItems = ref<number[]>([]);
const loading = ref(false);
const showDeleted = ref(false);
const viewMode = ref<"all" | "deleted_only" | "active_only">("active_only"); // 新增视图模式
const itemsPerPage = ref(20);
const currentPage = ref(1);
const totalItems = ref(0);

// 搜索相关
const searchQuery = ref("");
const tagFilter = ref("");
const questionTypeFilter = ref("");
const stdQuestionFilter = ref(""); // 标准答案视图中搜索关联问题
const scoringPointFilter = ref(""); // 标准答案视图中搜索得分点
const scoringPointsFilter = ref(""); // 标准问题视图中筛选得分点
const searchTimeout = ref<number | null>(null);

// 弹窗相关
const showDetailModal = ref(false);
const showEditModal = ref(false);
const showScoringPointsModal = ref(false);
const selectedItem = ref<DatabaseItem | null>(null);
const editForm = ref<Record<string, any>>({});
const saving = ref(false);
const scoringPointsData = ref<any[]>([]);

// 编辑相关变量
const newTag = ref("");

// 消息提示
const message = ref("");
const messageType = ref<"success" | "error">("success");

// 表格配置
const tableConfigs: Record<TableName, TableConfig> = {      
  std_questions: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "body", label: "问题文本", type: "text", className: "text-col", multiline: true },
      { key: "question_type", label: "问题类型", type: "text", className: "type-col" },
      { key: "tags", label: "标签", type: "tags", className: "tags-col" },
      { key: "std_answers_summary", label: "标准答案", type: "text", className: "answers-col", multiline: true },
    ],
    editable: ["body", "question_type", "tags"]
  },  
  std_answers: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "std_question_body", label: "标准问题", type: "text", className: "question-col", multiline: true },
      { key: "answer", label: "答案文本", type: "text", className: "answer-col", multiline: true },
      { key: "answered_by", label: "回答者", type: "text", className: "author-col" },
      { key: "scoring_points", label: "得分点", type: "text", className: "scoring-points-col", multiline: true },
      { key: "scoring_points_count", label: "得分点数量", type: "number", className: "scoring-points-count-col" },
    ],
    editable: ["answer", "answered_by", "scoring_points"]
  },
  overview_std: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "text", label: "标准问题", type: "text", className: "title-col", multiline: true },
      { key: "answer_text", label: "标准答案", type: "text", className: "answer-col", multiline: true },
      { key: "tags", label: "标签", type: "tags", className: "tags-col" },
      { key: "raw_questions", label: "原始问题", type: "text", className: "title-col", multiline: true },
      { key: "raw_answers", label: "原始回答", type: "text", className: "answer-col", multiline: true },
      { key: "expert_answers", label: "专家回答", type: "text", className: "answer-col", multiline: true },
      { key: "question_type", label: "问题类型", type: "text", className: "type-col" },
    ],
    editable: []
  }
};

// 计算属性
const tableColumns = computed<TableColumn[]>(() => {
  return tableConfigs[selectedTable.value]?.columns || [];
});

const editableColumns = computed<TableColumn[]>(() => {
  const config = tableConfigs[selectedTable.value];
  if (!config) return [];
  
  return config.columns.filter((col: TableColumn) => 
    config.editable.includes(col.key)
  );
});

const totalPages = computed(() => {
  return Math.ceil(totalItems.value / itemsPerPage.value);
});

const isOverviewTable = computed(() => {
  return selectedTable.value === 'overview_std';
});

// 计算选中的已删除项目
const selectedDeletedItems = computed(() => {
  return selectedItems.value.filter(id => {
    const item = currentData.value.find(item => item.id === id);
    return item && !item.is_valid;
  });
});

// 计算已删除项目的数量
const deletedCount = computed(() => {
  return currentData.value.filter(item => !item.is_valid).length;
});

const loadDataset = async (versionNumber?: number) => {
  if (!currentDatasetId.value) return;
  
  try {
    currentDataset.value = await datasetService.getDataset(currentDatasetId.value, versionNumber);
  } catch (error) {
    showMessage("加载数据集信息失败", "error");
    console.error("Load dataset error:", error);
  }
};

const loadTableData = async () => {
  loading.value = true;
  try {
    const skip = (currentPage.value - 1) * itemsPerPage.value;
    const limit = itemsPerPage.value;
    
    // 根据视图模式确定参数
    let includeDeleted = false;
    let deletedOnly = false;
    
    if (viewMode.value === 'all') {
      includeDeleted = true;
    } else if (viewMode.value === 'deleted_only') {
      includeDeleted = true;
      deletedOnly = true;
    }    
    
    // 获取当前数据集的版本信息
    const currentVersion = currentDataset.value?.version;
    
    let result;
    if (selectedTable.value === 'overview_std') {
      result = await databaseService.getStdQuestionsOverview(
        skip,
        limit,
        currentDatasetId.value,
        searchQuery.value || undefined,
        tagFilter.value || undefined,
        questionTypeFilter.value || undefined,
        currentVersion
      );    
    } else {
      result = await databaseService.getTableData(
        selectedTable.value,
        skip,
        limit,
        includeDeleted,
        currentDatasetId.value,
        deletedOnly,
        searchQuery.value || undefined,
        tagFilter.value || undefined,
        questionTypeFilter.value || undefined,
        stdQuestionFilter.value || undefined,
        scoringPointFilter.value || undefined,
        scoringPointsFilter.value || undefined,
        currentVersion
      );
    }
    currentData.value = result.data;    // 特殊处理标准问题数据，添加 tags、dataset_name 和答案摘要字段
    if (selectedTable.value === 'std_questions') {
      console.log('开始处理标准问题数据，原始数据:', result.data);
      
      currentData.value = result.data.map(item => {
        // 调试输出
        console.log(`处理标准问题 ID ${item.id}:`, {
          id: item.id,
          std_answers: item.std_answers,
          std_answers_length: item.std_answers?.length,
          std_answers_type: typeof item.std_answers,
          std_answers_detail: item.std_answers
        });
        
        let stdAnswersSummary = '无标准答案';
        
        if (item.std_answers) {
          if (Array.isArray(item.std_answers)) {
            console.log(`标准问题 ${item.id} 的答案数组:`, item.std_answers);
            const validAnswers = item.std_answers.filter((answer: any) => answer.is_valid !== false);
            console.log(`标准问题 ${item.id} 的有效答案:`, validAnswers);
            
            if (validAnswers.length > 0) {
              stdAnswersSummary = validAnswers
                .map((answer: any) => answer.answer || '无内容')
                .join('\n');
            }
          } else {
            console.log(`标准问题 ${item.id} 的答案不是数组:`, typeof item.std_answers, item.std_answers);
          }
        } else {
          console.log(`标准问题 ${item.id} 没有std_answers字段`);
        }

        console.log(`标准问题 ID ${item.id} 的最终答案摘要:`, stdAnswersSummary);

        return {
          ...item,
          tags: item.tags || [],  // 确保 tags 是数组
          std_answers_summary: stdAnswersSummary,
        };
      });
      
      console.log('处理后的标准问题数据:', currentData.value);
    }
    
    // 特殊处理标准答案数据，添加 std_question_body 和得分点相关字段
    if (selectedTable.value === 'std_answers') {
      currentData.value = result.data.map(item => {
        // 调试输出
        console.log(`处理标准答案 ID ${item.id}:`, {
          id: item.id,
          std_question: item.std_question,
          scoring_points: item.scoring_points,
          scoring_points_count: item.scoring_points_count,
          scoring_points_length: item.scoring_points?.length
        });
        
        // 处理得分点摘要
        const scoringPointsSummary = item.scoring_points && item.scoring_points.length > 0
          ? item.scoring_points
              .filter((point: any) => point.is_valid) // 只显示有效的得分点
              .sort((a: any, b: any) => a.point_order - b.point_order)
              .map((point: any) => `${point.point_order}. ${point.answer}`)
              .join('; ')
          : '无得分点';

        const processedItem = {
          ...item,
          std_question_body: item.std_question?.body || '无关联问题',
          scoring_points_summary: scoringPointsSummary,
          scoring_points_count: item.scoring_points ? item.scoring_points.filter((p: any) => p.is_valid).length : 0
        };
        
        console.log(`处理后的标准答案 ID ${item.id}:`, processedItem);
        return processedItem;
      });
    }
    totalItems.value = result.total;
    // deletedCount 是计算属性，不需要手动设置
    selectedItems.value = [];
  } catch (error) {
    showMessage("加载数据失败", "error");
    console.error("Load data error:", error);
  } finally {
    loading.value = false;
  }
};

const refreshData = () => {
  currentPage.value = 1;
  loadTableData();
};

// 创建新版本
const createNewVersion = () => {
  console.log('currentDatasetId:', currentDatasetId.value);
  console.log('route.params:', route.params);
  console.log('route.query:', route.query);
  
  if (!currentDatasetId.value) {
    showMessage("请先选择一个数据集", "error");
    return;
  }

  // 跳转到版本创建页面
  router.push({
    name: 'DatabaseVersionCreate',
    params: { datasetId: currentDatasetId.value.toString() }
  });
};

// 处理搜索的防抖方法
const handleSearch = () => {
  // 清除之前的超时
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  
  // 设置新的超时，实现防抖
  searchTimeout.value = setTimeout(() => {
    currentPage.value = 1; // 重置到第一页
    loadTableData();
  }, 300) as unknown as number; // 300ms 防抖延迟
};

const selectAll = () => {
  if (selectedItems.value.length === currentData.value.length) {
    selectedItems.value = [];
  } else {
    selectedItems.value = currentData.value.map(item => item.id);
  }
};

const bulkDelete = async () => {
  if (!confirm(`确定要删除选中的 ${selectedItems.value.length} 项吗？`)) return;
  
  try {
    await databaseService.bulkDelete(selectedTable.value, selectedItems.value);
    showMessage(`成功删除 ${selectedItems.value.length} 项`, "success");
    selectedItems.value = [];
    loadTableData();
  } catch (error) {
    showMessage("批量删除失败", "error");
  }
};

const bulkRestore = async () => {
  // 在 deleted_only 模式下，所有选中的项目都应该是已删除的
  const itemsToRestore = viewMode.value === 'deleted_only' ? selectedItems.value : selectedDeletedItems.value;
  if (!confirm(`确定要恢复选中的 ${itemsToRestore.length} 项吗？`)) return;
  
  try {
    await databaseService.bulkRestore(selectedTable.value, itemsToRestore);
    showMessage(`成功恢复 ${itemsToRestore.length} 项`, "success");
    selectedItems.value = [];
    loadTableData();
  } catch (error) {
    showMessage("批量恢复失败", "error");
  }
};

const deleteItem = async (id: number) => {
  if (!confirm("确定要删除这个项目吗？")) return;
  
  try {
    await databaseService.deleteItem(selectedTable.value, id);
    showMessage("删除成功", "success");
    loadTableData();
  } catch (error) {
    showMessage("删除失败", "error");
  }
};

const restoreItem = async (id: number) => {
  try {
    await databaseService.restoreItem(selectedTable.value, id);
    showMessage("恢复成功", "success");
    loadTableData();
  } catch (error) {
    showMessage("恢复失败", "error");
  }
};

const forceDeleteItem = async (id: number) => {
  if (!confirm("确定要永久删除这个项目吗？此操作不可恢复！")) return;
  
  try {
    await databaseService.forceDeleteItem(selectedTable.value, id);
    showMessage("永久删除成功", "success");
    loadTableData();
  } catch (error) {
    showMessage("永久删除失败", "error");
  }
};

// 标准问题/答案绑定删除逻辑
const deleteStdItem = async (item: DatabaseItem) => {
  const itemType = selectedTable.value === 'std_questions' ? '标准问题' : '标准答案';
  
  let confirmMessage = '';
  if (selectedTable.value === 'std_questions') {
    confirmMessage = `确定要删除这个${itemType}吗？\n\n注意：删除标准问题将同时删除所有关联的标准答案！`;
  } else {
    confirmMessage = `确定要删除这个${itemType}吗？\n\n注意：如果这是关联标准问题的最后一个答案，标准问题也将被同时删除！`;
  }
  
  if (!confirm(confirmMessage)) return;
  
  try {
    if (selectedTable.value === 'std_questions') {
      // 删除标准问题时，同时删除其关联的标准答案
      await databaseService.deleteItem('std_questions', item.id);
      // 后端会自动处理关联的标准答案删除
    } else {
      // 删除标准答案时，检查是否需要删除关联的标准问题
      await databaseService.deleteItem('std_answers', item.id);
    }
    
    showMessage(`${itemType}删除成功`, "success");
    loadTableData();
  } catch (error) {
    showMessage(`${itemType}删除失败`, "error");
  }
};

const restoreStdItem = async (item: DatabaseItem) => {
  const itemType = selectedTable.value === 'std_questions' ? '标准问题' : '标准答案';
  const bindingType = selectedTable.value === 'std_questions' ? '标准答案' : '标准问题';
  
  try {
    if (selectedTable.value === 'std_questions') {
      // 恢复标准问题时，同时恢复其关联的标准答案
      await databaseService.restoreItem('std_questions', item.id);
    } else {
      // 恢复标准答案时，检查是否需要恢复关联的标准问题
      await databaseService.restoreItem('std_answers', item.id);
    }
    
    showMessage(`${itemType}恢复成功`, "success");
    loadTableData();
  } catch (error) {
    showMessage(`${itemType}恢复失败`, "error");
  }
};

const forceDeleteStdItem = async (item: DatabaseItem) => {
  const itemType = selectedTable.value === 'std_questions' ? '标准问题' : '标准答案';
  
  if (!confirm(`确定要永久删除这个${itemType}吗？此操作不可恢复！\n\n注意：这将永久删除所有相关数据！`)) return;
  
  try {
    await databaseService.forceDeleteItem(selectedTable.value, item.id);
    showMessage(`${itemType}永久删除成功`, "success");
    loadTableData();
  } catch (error) {
    showMessage(`${itemType}永久删除失败`, "error");
  }
};

const manageScoringPoints = async (stdAnswer: DatabaseItem) => {
  selectedItem.value = stdAnswer;
  
  try {
    // 调用API获取所有得分点（包括已删除的）
    const response = await apiClient.get(`/std-answers/${stdAnswer.id}/scoring-points`);
    scoringPointsData.value = response.data;
  } catch (error) {
    console.error('Load scoring points error:', error);
    showMessage("加载得分点失败", "error");
    scoringPointsData.value = [];
  }
  
  showScoringPointsModal.value = true;
};

const deleteScoringPoint = async (pointId: number) => {
  if (!confirm("确定要删除这个得分点吗？")) return;
  
  try {
    await apiClient.delete(`/std-answers/scoring-points/${pointId}`);
    showMessage("得分点删除成功", "success");
    
    // 刷新得分点数据
    if (selectedItem.value) {
      await manageScoringPoints(selectedItem.value);
    }
    // 同时刷新主表数据以更新得分点计数
    loadTableData();
  } catch (error) {
    console.error('Delete scoring point error:', error);
    showMessage("得分点删除失败", "error");
  }
};

const restoreScoringPoint = async (pointId: number) => {
  try {
    await apiClient.post(`/std-answers/scoring-points/${pointId}/restore`);
    showMessage("得分点恢复成功", "success");
    
    // 刷新得分点数据
    if (selectedItem.value) {
      await manageScoringPoints(selectedItem.value);
    }
    // 同时刷新主表数据以更新得分点计数
    loadTableData();
  } catch (error) {
    console.error('Restore scoring point error:', error);
    showMessage("得分点恢复失败", "error");
  }
};

const forceDeleteScoringPoint = async (pointId: number) => {
  if (!confirm("确定要永久删除这个得分点吗？此操作不可恢复！")) return;
  
  try {
    await apiClient.delete(`/std-answers/scoring-points/${pointId}/force-delete`);
    showMessage("得分点永久删除成功", "success");
    
    // 刷新得分点数据
    if (selectedItem.value) {
      await manageScoringPoints(selectedItem.value);
    }
    // 同时刷新主表数据以更新得分点计数
    loadTableData();
  } catch (error) {
    console.error('Force delete scoring point error:', error);
    showMessage("得分点永久删除失败", "error");
  }
};

const closeScoringPointsModal = () => {
  showScoringPointsModal.value = false;
  selectedItem.value = null;
  scoringPointsData.value = [];
};

const handleViewModeChange = () => {
  currentPage.value = 1;
  selectedItems.value = [];
  loadTableData();
};

const viewItem = (item: any) => {
  selectedItem.value = item;
  showDetailModal.value = true;
};

const editItem = (item: any) => {
  selectedItem.value = item;
  editForm.value = { ...item };
  
  // 初始化标签数据
  if (item.tags) {
    editForm.value.tags = Array.isArray(item.tags) ? [...item.tags] : [];
  } else {
    editForm.value.tags = [];
  }
  
  // 初始化得分点数据
  if (item.scoring_points) {
    editForm.value.scoring_points = item.scoring_points.map((point: any) => ({
      id: point.id,
      answer: point.answer,
      point_order: point.point_order,
      is_valid: point.is_valid
    }));
  } else {
    editForm.value.scoring_points = [];
  }
  
  // 清空新标签输入
  newTag.value = "";
  
  showEditModal.value = true;
};

const saveEdit = async () => {
  if (!selectedItem.value) return;
  
  saving.value = true;
  try {
    // 根据表类型过滤允许更新的字段
    let updateData: any = {};
    
    if (selectedTable.value === 'std_questions') {
      // 标准问题只允许更新这些字段
      updateData = {
        dataset_id: editForm.value.dataset_id,
        body: editForm.value.body,
        question_type: editForm.value.question_type,
        is_valid: editForm.value.is_valid,
        tags: editForm.value.tags
      };    
    } else if (selectedTable.value === 'std_answers') {
      // 标准答案只允许更新这些字段
      updateData = {
        std_question_id: editForm.value.std_question_id,
        answer: editForm.value.answer,
        is_valid: editForm.value.is_valid,
        scoring_points: editForm.value.scoring_points
      };
    } else {
      // 其他表类型使用完整表单数据
      updateData = editForm.value;
    }
    
    await databaseService.updateItem(selectedTable.value, selectedItem.value.id, updateData);
    showMessage("保存成功", "success");
    closeEditModal();
    loadTableData();
  } catch (error) {
    showMessage("保存失败", "error");
  } finally {
    saving.value = false;
  }
};

const closeDetailModal = () => {
  showDetailModal.value = false;
  selectedItem.value = null;
};

const closeEditModal = () => {
  showEditModal.value = false;
  selectedItem.value = null;
  editForm.value = {};
};

const goToPage = (page: number) => {
  currentPage.value = page;
  loadTableData();
};

const formatCellValue = (value: any, column: any) => {
  if (!value) return "无";
  
  if (column.type === "text") {
    let text = "";
    
    // 处理数组类型的数据（总览中的关联数据）
    if (Array.isArray(value)) {
      if (value.length === 0) return "无";
      text = value.map((item: any) => {
        if (typeof item === 'object') {
          // 对于总览数据，显示主要内容
          return item.content || item.answer || item.text || item.title || JSON.stringify(item);
        }
        return String(item);
      }).join("; ");
    } else if (typeof value === 'object') {
      // 处理对象类型
      text = value.content || value.answer || value.text || value.title || value.body || JSON.stringify(value);
    } else {
      text = String(value);
    }
    
    // 处理特殊情况：如果是"无专家回答"或类似的文本，直接显示
    if (text === "无专家回答" || text === "无关联原始问题" || text === "无原始回答") {
      return text;
    }
    
    return text.length > 100 ? text.substring(0, 100) + "..." : text;
  }
  
  return value;
};

const formatDetailValue = (value: any) => {
  if (value === null || value === undefined) return "无";
  if (typeof value === "boolean") return value ? "是" : "否";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
};

const formatDetailTextValue = (value: any) => {
  if (!value) return "无";
  
  // 如果是字符串，直接返回
  if (typeof value === 'string') {
    return value;
  }
  
  // 如果是数组类型的数据（总览中的关联数据）
  if (Array.isArray(value)) {
    if (value.length === 0) return "无";    return value.map((item: any) => {
      if (typeof item === 'object') {
        return item.content || item.answer || item.text || item.title || item.body || JSON.stringify(item);
      }
      return String(item);
    }).join("\n\n");
  } 
    // 如果是对象类型
  if (typeof value === 'object') {
    return value.content || value.answer || value.text || value.title || value.body || JSON.stringify(value, null, 2);
  }
  
  return String(value);
};

const parseTagsValue = (value: any) => {
  return formatTags(value);
};

const getInputType = (columnType: string) => {
  switch (columnType) {
    case "number": return "number";
    case "date": return "datetime-local";
    case "boolean": return "checkbox";
    default: return "text";
  }
};

const showMessage = (text: string, type: "success" | "error" = "success") => {
  message.value = text;
  messageType.value = type;
  setTimeout(() => {
    message.value = "";
  }, 3000);
};

// 得分点相关辅助函数
const getScoringPointsCount = (item: DatabaseItem) => {
  console.log(`getScoringPointsCount for item ${item.id}:`, {
    scoring_points: item.scoring_points,
    is_array: Array.isArray(item.scoring_points),
    length: item.scoring_points?.length
  });
  
  if (!item.scoring_points) return 0;
  if (Array.isArray(item.scoring_points)) {
    const validCount = item.scoring_points.filter(point => point.is_valid !== false).length;
    console.log(`Valid scoring points count for item ${item.id}: ${validCount}`);
    return validCount;
  }
  return 0;
};

const getDeletedScoringPointsCount = (item: DatabaseItem) => {
  if (!item.scoring_points) return 0;
  if (Array.isArray(item.scoring_points)) {
    return item.scoring_points.filter(point => point.is_valid === false).length;
  }
  return 0;
};

// 判断是否应该显示得分点管理按钮
const shouldShowScoringPointsButton = (item: DatabaseItem) => {
  // 只有在标准答案视图中才显示
  if (selectedTable.value !== 'std_answers') return false;
  
  // 获取关联的标准问题类型
  const questionType = item.std_question?.question_type;
  
  // 对于选择题（choice）类型不显示得分点管理按钮
  return questionType !== 'choice';
};

// 标签编辑相关函数
const addTag = () => {
  const tag = newTag.value.trim();
  if (tag && !editForm.value.tags.includes(tag)) {
    editForm.value.tags.push(tag);
    newTag.value = "";
  }
};

const removeTag = (index: number) => {
  editForm.value.tags.splice(index, 1);
};

// 得分点编辑相关函数
const addScoringPoint = () => {
  const newOrder = editForm.value.scoring_points.length + 1;
  editForm.value.scoring_points.push({
    answer: "",
    point_order: newOrder,
    is_valid: true
  });
};

const removeScoringPoint = (index: number) => {
  editForm.value.scoring_points.splice(index, 1);
  // 重新排序剩余的得分点
  editForm.value.scoring_points.forEach((point: any, i: number) => {
    point.point_order = i + 1;
  });
};

// 生命周期
onMounted(async () => {
  // 从路由参数获取数据集ID和版本
  const datasetId = route.params.id || route.query.dataset;
  const version = route.params.version || route.query.version;
  
  if (datasetId && !isNaN(Number(datasetId))) {
    currentDatasetId.value = Number(datasetId);
    // 如果有版本参数，传递给loadDataset
    const versionNumber = version ? Number(version) : undefined;
    await loadDataset(versionNumber);
  }
  
  loadTableData();
});
</script>

<style scoped>
.database-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.table-select,
.per-page-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.refresh-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.refresh-btn:hover:not(:disabled) {
  background: #0056b3;
}

.refresh-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.create-version-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);
}

.create-version-btn:hover {
  background: linear-gradient(135deg, #218838 0%, #1abc9c 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

.stats-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 14px;
}

.stat-item {
  display: flex;
  gap: 5px;
}

.stat-label {
  color: #666;
}

.stat-value {
  font-weight: bold;
  color: #333;
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 15px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.bulk-actions {
  display: flex;
  gap: 10px;
}

.view-options {
  display: flex;
  gap: 15px;
  align-items: center;
  font-size: 14px;
}

/* 搜索和筛选区域样式 */
.search-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  background: linear-gradient(145deg, #f8f9fa 0%, #ffffff 100%);
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e9ecef;
  margin-bottom: 8px;
}

.search-input-group,
.filter-input-group,
.select-group {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 200px;
  flex: 1;
}

.search-input-group {
  min-width: 280px;
}

.filter-input-group {
  min-width: 220px;
}

.select-group {
  min-width: 180px;
}

.search-icon,
.filter-icon {
  position: absolute;
  left: 12px;
  z-index: 2;
  font-size: 16px;
  color: #6c757d;
  pointer-events: none;
  transition: all 0.3s ease;
}

.search-input,
.filter-input {
  width: 100%;
  padding: 12px 16px 12px 40px;
  border: 2px solid #e1e5e9;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  background: white;
  color: #495057;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.search-input.enhanced {
  background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
  border-color: #007bff;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.search-input:focus,
.filter-input:focus {
  border-color: #007bff;
  background: white;
  box-shadow: 0 0 0 4px rgba(0, 123, 255, 0.1), 0 4px 12px rgba(0, 123, 255, 0.15);
  transform: translateY(-1px);
}

.search-input:focus + .search-icon,
.filter-input:focus + .filter-icon {
  color: #007bff;
  transform: scale(1.1);
}

.search-input::placeholder,
.filter-input::placeholder {
  color: #adb5bd;
  font-weight: 400;
}

.filter-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
  color: #495057;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236c757d' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px;
  padding-right: 40px;
}

.filter-select:hover {
  border-color: #007bff;
  background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
  transform: translateY(-1px);
}

.filter-select:focus {
  border-color: #007bff;
  background: white;
  box-shadow: 0 0 0 4px rgba(0, 123, 255, 0.1), 0 4px 12px rgba(0, 123, 255, 0.15);
  transform: translateY(-1px);
}

.filter-select:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 总览操作栏 */
.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 15px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.view-mode-select,
.per-page-select {
  padding: 10px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
  color: #495057;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
  min-width: 140px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: relative;
}

.view-mode-select::after,
.per-page-select::after {
  content: '▼';
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #6c757d;
  font-size: 10px;
  pointer-events: none;
}

.view-mode-select:hover,
.per-page-select:hover {
  border-color: #007bff;
  background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
  transform: translateY(-1px);
}

.view-mode-select:focus,
.per-page-select:focus {
  border-color: #007bff;
  background: white;
  box-shadow: 0 0 0 4px rgba(0, 123, 255, 0.1), 0 4px 12px rgba(0, 123, 255, 0.15);
  transform: translateY(-1px);
}

.view-mode-select:active,
.per-page-select:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: #f8f9fa;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.danger {
  border-color: #dc3545;
  color: #dc3545;
}

.action-btn.danger:hover:not(:disabled) {
  background: #dc3545;
  color: white;
}

.action-btn.success {
  border-color: #28a745;
  color: #28a745;
}

.action-btn.success:hover:not(:disabled) {
  background: #28a745;
  color: white;
}

.action-btn.small {
  padding: 4px 8px;
  font-size: 12px;
  min-width: auto;
}

.action-btn.scoring-btn {
  border-color: #6f42c1;
  color: #6f42c1;
  position: relative;
}

.action-btn.scoring-btn:hover:not(:disabled) {
  background: #6f42c1;
  color: white;
}

.action-btn.scoring-btn.has-deleted {
  border-color: #dc3545;
  color: #dc3545;
  background: #fff5f5;
}

.action-btn.scoring-btn.has-deleted:hover:not(:disabled) {
  background: #dc3545;
  color: white;
}

.action-btn.scoring-btn.has-deleted::after {
  content: '!';
  position: absolute;
  top: -2px;
  right: -2px;
  background: #dc3545;
  color: white;
  font-size: 8px;
  font-weight: bold;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.overview-info {
  padding: 10px 15px;
  background: #e3f2fd;
  border-radius: 4px;
  color: #1976d2;
  font-weight: 500;
}

.overview-info .info-text {
  font-size: 14px;
}

/* 数据表格样式 */
.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  background: #f8f9fa;
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #dee2e6;
  white-space: nowrap;
}

.data-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #dee2e6;
  vertical-align: top;
}

.data-table tr:hover {
  background: #f8f9fa;
}

.deleted-row {
  opacity: 0.6;
  background: #fff3cd !important;
}

.deleted-row:hover {
  background: #ffeaa7 !important;
}

/* 列宽控制 */
.checkbox-col {
  width: 40px;
  text-align: center;
}

.id-col {
  width: 80px;
  text-align: center;
}

.title-col,
.answer-col,
.text-col {
  min-width: 200px;
  max-width: 300px;
}

.author-col,
.source-col {
  width: 120px;
}

.votes-col,
.views-col,
.version-col {
  width: 80px;
  text-align: center;
}

.date-col {
  width: 140px;
}

.tags-col {
  width: 150px;
}

.actions-col {
  width: 120px;
  text-align: center;
}

.cell-content {
  max-height: 60px;
  overflow: hidden;
}

.text-content {
  display: block;
  line-height: 1.4;
  word-break: break-word;
}

.tags-content {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  background: #e9ecef;
  color: #495057;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

/* 得分点计数样式 */
.scoring-points-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.valid-count {
  font-weight: bold;
  color: #28a745;
  font-size: 14px;
}

.deleted-count {
  font-size: 11px;
  color: #dc3545;
  font-weight: 500;
  background: rgba(220, 53, 69, 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid rgba(220, 53, 69, 0.2);
}

.deleted-number {
  font-weight: bold;
}

.row-actions {
  display: flex;
  gap: 5px;
  justify-content: center;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  margin: 0 20px;
  font-size: 14px;
  color: #666;
}

.no-data,
.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.detail-modal,
.edit-modal {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  width: 90%;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
  background: #f8f9fa;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
}

.close-btn:hover {
  color: #333;
}

.modal-content {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-value {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  word-break: break-word;
}

.detail-value.multiline {
  white-space: pre-wrap;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.5;
}

.detail-value .text-value {
  white-space: pre-wrap;
  line-height: 1.5;
}

.detail-value .number-value,
.detail-value .date-value,
.detail-value .boolean-value,
.detail-value .default-value {
  font-weight: 500;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: 600;
  color: #333;
}

.form-control {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #dee2e6;
}

.cancel-btn {
  padding: 10px 20px;
  border: 1px solid #6c757d;
  border-radius: 4px;
  background: white;
  color: #6c757d;
  cursor: pointer;
}

.cancel-btn:hover {
  background: #6c757d;
  color: white;
}

.save-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  background: #007bff;
  color: white;
  cursor: pointer;
}

.save-btn:hover:not(:disabled) {
  background: #0056b3;
}

.save-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

/* 消息提示 */
.message {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  color: white;
  z-index: 1100;
  animation: slideIn 0.3s ease;
}

.message.success {
  background: #28a745;
}

.message.error {
  background: #dc3545;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 总览表格样式 */
.overview-info {
  padding: 10px 15px;
  background: #e3f2fd;
  border-radius: 4px;
  color: #1976d2;
  font-weight: 500;
}

.overview-info .info-text {
  font-size: 14px;
}

/* 总览表格内容样式 */
.cell-content.text {
  max-width: 300px;
  line-height: 1.4;
}

.cell-content.text .text-content {
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .database-view {
    padding: 10px;
  }
  
  .header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .actions-bar {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .bulk-actions,
  .view-options {
    justify-content: center;
  }
  
  .data-table {
    font-size: 12px;
  }
  
  .data-table th,
  .data-table td {
    padding: 8px 4px;
  }
    .detail-modal,
  .edit-modal {
    width: 95%;
    margin: 10px;
  }
}

/* 详情弹窗特殊样式 */
.detail-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-height: 400px;
  overflow-y: auto;
}

.detail-box {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 10px;
}

.detail-box-header {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #666;
  flex-wrap: wrap;
}

.detail-box-header .item-id {
  font-weight: bold;
  color: #007bff;
}

.detail-box-header .item-author {
  color: #28a745;
}

.detail-box-header .item-relation {
  color: #6c757d;
  font-style: italic;
}

.detail-box-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #333;
  font-size: 14px;
  line-height: 1.3;
}

.detail-box-content {
  color: #555;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  background: white;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.no-data {
  color: #6c757d;
  font-style: italic;
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 4px;
}

/* 得分点样式 */
.scoring-points-detail {
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 15px;
  background: #f8f9fa;
}

.scoring-points-summary {
  margin-bottom: 15px;
  padding: 10px;
  background: #e3f2fd;
  border-radius: 4px;
  text-align: center;
}

.scoring-points-summary .count {
  font-weight: bold;
  color: #1976d2;
  font-size: 16px;
}

.scoring-points-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.scoring-point-item {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 15px;
  transition: box-shadow 0.2s ease;
}

.scoring-point-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.scoring-point-item.deleted-point {
  opacity: 0.7;
  border-left: 4px solid #dc3545;
  background: #fff5f5;
}

.deleted-text {
  color: #dc3545 !important;
  font-weight: bold;
  text-decoration: line-through;
}

.scoring-points-modal .deleted-text {
  opacity: 0.8;
}

.scoring-point-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9ecef;
}

.scoring-point-header .point-number {
  font-weight: bold;
  color: #007bff;
  font-size: 14px;
}

.scoring-point-header .point-order {
  color: #6c757d;
  font-size: 12px;
  background: #f8f9fa;
  padding: 2px 8px;
  border-radius: 12px;
}

.scoring-point-content {
  color: #333;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.no-scoring-points {
  color: #6c757d;
  font-style: italic;
  text-align: center;
  padding: 20px;
  background: white;
  border-radius: 4px;
  border: 1px dashed #dee2e6;
}

/* 表格中得分点数量列的样式 */
.scoring-points-count-col {
  width: 140px;
  text-align: center;
}

.scoring-points-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.scoring-points-count .valid-count-container {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: #e8f5e8;
  border-radius: 12px;
  border: 1px solid #28a745;
}

.scoring-points-count .valid-count {
  font-weight: bold;
  color: #28a745;
}

.scoring-points-count .deleted-count-container {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: #ffeaea;
  border-radius: 12px;
  border: 1px solid #dc3545;
  cursor: help;
}

.scoring-points-count .deleted-count {
  font-weight: bold;
  color: #dc3545;
}

.scoring-points-count .count-label {
  font-size: 10px;
  color: #28a745;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.scoring-points-count .count-label.deleted {
  color: #dc3545;
}

/* 得分点管理弹窗样式 */
.scoring-points-modal {
  background: white;
  border-radius: 8px;
  max-width: 700px;
  max-height: 80vh;
  width: 90%;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.scoring-points-modal .modal-content {
  max-height: 60vh;
}

.scoring-points-modal .scoring-points-list {
  max-height: 500px;
}

.scoring-points-modal .scoring-point-item {
  position: relative;
}

.scoring-points-modal .point-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9ecef;
}

.scoring-points-modal .point-id {
  font-weight: bold;
  color: #007bff;
  font-size: 14px;
}

.scoring-points-modal .point-order {
  color: #6c757d;
  font-size: 12px;
  background: #f8f9fa;
  padding: 2px 8px;
  border-radius: 12px;
}

.scoring-points-modal .point-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
}

.scoring-points-modal .point-status.active {
  background: #d4edda;
  color: #155724;
}

.scoring-points-modal .point-status.deleted {
  background: #f8d7da;
  color: #721c24;
}

.scoring-points-modal .point-content {
  color: #333;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.scoring-points-modal .point-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 删除状态的视觉样式 */
.scoring-points-modal .deleted-point {
  background: #fff5f5 !important;
  border: 1px solid #fed7d7 !important;
  opacity: 0.7;
}

.scoring-points-modal .deleted-text {
  color: #e53e3e !important;
  font-weight: bold;
  text-decoration: line-through;
}

.scoring-points-modal .deleted-point .point-content {
  background: #fed7d7 !important;
  color: #742a2a !important;
}

/* 标签编辑器样式 */
.tags-editor {
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 15px;
  background: #f8f9fa;
}

.current-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  min-height: 30px;
}

.tag-item {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  color: white;
  padding: 6px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  gap: 6px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
}

.tag-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.remove-tag-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: all 0.2s ease;
}

.remove-tag-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.add-tag {
  display: flex;
  gap: 10px;
  align-items: center;
}

.add-tag input {
  flex: 1;
  min-width: 200px;
}

.add-tag-btn {
  padding: 8px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.add-tag-btn:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(40, 167, 69, 0.3);
}

.add-tag-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 得分点编辑器样式 */
.scoring-points-editor {
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 15px;
  background: #f8f9fa;
}

.scoring-points-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 15px;
}

.scoring-point-edit-item {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 15px;
  transition: all 0.3s ease;
  position: relative;
}

.scoring-point-edit-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #007bff;
}

.scoring-point-edit-item .point-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9ecef;
}

.scoring-point-edit-item .point-header label {
  font-weight: bold;
  color: #495057;
  margin: 0;
}

.remove-point-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.remove-point-btn:hover {
  background: #c82333;
  transform: scale(1.05);
}

.scoring-point-edit-item textarea {
  margin-bottom: 10px;
  resize: vertical;
  min-height: 80px;
}

.point-order {
  display: flex;
  align-items: center;
  gap: 10px;
}

.point-order label {
  font-size: 13px;
  font-weight: 500;
  color: #6c757d;
  margin: 0;
  min-width: 40px;
}

.point-order input {
  width: 80px;
}

.form-control.small {
  padding: 6px 8px;
  font-size: 13px;
}

.add-point-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
}

.add-point-btn:hover {
  background: linear-gradient(135deg, #138496 0%, #117a8b 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(23, 162, 184, 0.3);
}

.add-point-btn::before {
  content: '➕';
  font-size: 12px;
}
</style>

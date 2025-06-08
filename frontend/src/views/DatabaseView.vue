<template>
  <div class="database-view">    <div class="header">
      <div class="header-left">
        <button @click="goBackToMarketplace" class="back-btn">
          ← 返回数据库市场
        </button>
        <div class="dataset-info" v-if="currentDataset">
          <h2>{{ currentDataset.name }}</h2>
          <p class="dataset-description">{{ currentDataset.description }}</p>
        </div>
        <h2 v-else>数据库管理</h2>
      </div>
      <div class="header-actions">        <select v-model="selectedTable" @change="loadTableData" class="table-select">
          <option value="overview_std">标准问答总览</option>
          <option value="std_questions">标准问题</option>
          <option value="std_answers">标准答案</option>
        </select>
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
        <!-- 在有已删除项目时显示恢复按钮 -->
        <button 
          v-if="viewMode === 'deleted_only' || (viewMode === 'all' && selectedDeletedItems.length > 0)"
          @click="bulkRestore" 
          class="action-btn success"
          :disabled="selectedDeletedItems.length === 0"
        >
          批量恢复 ({{ selectedDeletedItems.length }})
        </button>
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
    </div>

    <!-- 总览操作栏 -->
    <div class="actions-bar" v-else>
      <div class="overview-info">
        <span class="info-text">总览模式：数据仅供查看，无法编辑</span>
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
            :class="{ 'deleted-row': item.is_deleted }"
          >
            <td class="checkbox-col" v-if="!isOverviewTable">
              <input 
                type="checkbox" 
                :value="item.id" 
                v-model="selectedItems"
              />
            </td>            <td v-for="column in tableColumns" :key="column.key" :class="column.className">
              <div class="cell-content" :class="column.type">
                <span v-if="column.type === 'text'" class="text-content">
                  <template v-if="column.key === 'std_question_body'">
                    {{ formatCellValue(item.std_question_body, column) }}
                  </template>
                  <template v-else>
                    {{ formatCellValue(item[column.key], column) }}
                  </template>
                </span>
                <span v-else-if="column.type === 'number' && column.key === 'scoring_points_count'" class="number-content">
                  {{ item.scoring_points ? item.scoring_points.length : 0 }}
                </span>
                <span v-else-if="column.type === 'number'" class="number-content">
                  {{ item[column.key] || 0 }}
                </span>
                <span v-else-if="column.type === 'date'" class="date-content">
                  {{ formatDate(item[column.key]) }}
                </span>
                <span v-else-if="column.type === 'tags'" class="tags-content">
                  <span 
                    v-for="tag in formatTags(item[column.key])" 
                    :key="tag" 
                    class="tag"
                  >
                    {{ tag }}
                  </span>
                </span>
                <span v-else-if="column.type === 'action' && column.key === 'scoring_points_management'" class="action-content">
                  <button 
                    @click="manageScoringPoints(item)" 
                    class="action-btn small"
                    title="管理得分点"
                  >
                    📊
                  </button>
                </span>
                <span v-else class="default-content">
                  {{ item[column.key] }}
                </span>              
              </div>
            </td>            <td class="actions-col">
              <div class="row-actions" v-if="!isOverviewTable">
                <button 
                  @click="viewItem(item)" 
                  class="action-btn small"
                  title="查看详情"
                >
                  👁️
                </button>
                <!-- 编辑按钮：非删除状态下显示 -->
                <button 
                  v-if="!item.is_deleted"
                  @click="editItem(item)" 
                  class="action-btn small"
                  title="编辑"
                >
                  ✏️
                </button>

                <!-- 标准问题和标准答案的特定操作 -->
                <template v-if="selectedTable === 'std_questions' || selectedTable === 'std_answers'">
                  <!-- 管理得分点按钮 -->
                  <button
                    v-if="selectedTable === 'std_answers' && !item.is_deleted"
                    @click="manageScoringPoints(item)"
                    class="action-btn small"
                    title="管理得分点"
                  >
                    🎯
                  </button>
                  <button
                    v-if="selectedTable === 'std_questions' && !item.is_deleted && item.std_answer_id" 
                    @click="manageScoringPointsForQuestion(item)"
                    class="action-btn small"
                    title="管理关联答案的得分点"
                  >
                    🎯
                  </button>

                  <!-- 删除/恢复操作 -->
                  <template v-if="!item.is_deleted">
                    <button 
                      @click="deleteStdItem(item)" 
                      class="action-btn small danger"
                      title="删除（关联项会同步处理）"
                    >
                      🗑️
                    </button>
                  </template>
                  <template v-else>
                    <button 
                      @click="restoreStdItem(item)" 
                      class="action-btn small success"
                      title="恢复（关联项会同步处理）"
                    >
                      ♻️
                    </button>
                    <button 
                      @click="forceDeleteStdItem(item)" 
                      class="action-btn small danger"
                      title="永久删除（关联项会同步处理）"
                    >
                      💀
                    </button>
                  </template>
                </template>

                <!-- 其他表的通用删除/恢复操作 -->
                <template v-else>
                  <template v-if="!item.is_deleted">
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
              </div>
              <div v-else>
                ---
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
                
                <template v-else-if="column.key === 'expert_answers' && selectedItem.expert_answers_detail">
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
                  </div>                </template>
                
                <!-- 标准答案得分点的特殊显示 -->
                <template v-else-if="column.key === 'scoring_points_count' && selectedItem.scoring_points">
                  <div class="scoring-points-detail">
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
                </template>                  <!-- 其他普通字段的显示 -->
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
        <div class="modal-content">          <form @submit.prevent="saveEdit" class="edit-form">
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
              
              <!-- 普通文本区域 -->
              <textarea 
                v-else-if="column.type === 'text' && column.multiline"
                :id="column.key"
                v-model="editForm[column.key]"
                :rows="3"
                class="form-control"
              ></textarea>
              
              <!-- 普通输入框 -->
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
      </div>    </div>

    <!-- 得分点管理弹窗 -->    <div v-if="showScoringPointsModal" class="modal-overlay" @click="closeScoringPointsModal">
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
            <div v-for="point in scoringPointsData" :key="point.id" class="scoring-point-item">
              <div class="point-header">
                <span class="point-id">得分点 #{{ point.id }}</span>
                <span class="point-order">顺序: {{ point.point_order }}</span>
                <span :class="['point-status', point.is_valid ? 'active' : 'deleted']">
                  {{ point.is_valid ? '有效' : '已删除' }}
                </span>
              </div>
              <div class="point-content">{{ point.answer }}</div>              <div class="point-actions">
                <template v-if="point.is_valid">
                  <button 
                    @click="deleteScoringPoint(point.id)" 
                    class="action-btn small danger"
                    title="删除得分点"
                  >
                    🗑️
                  </button>
                </template>
                <template v-else>
                  <button 
                    @click="restoreScoringPoint(point.id)" 
                    class="action-btn small success"
                    title="恢复得分点"
                  >
                    ♻️
                  </button>
                  <button 
                    @click="forceDeleteScoringPoint(point.id)" 
                    class="action-btn small danger"
                    title="永久删除得分点"
                  >
                    💀
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
import { formatDate, formatTags } from "@/utils/formatters";

// 路由
const route = useRoute();
const router = useRouter();

// 类型定义
interface TableColumn {
  key: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'tags' | 'boolean' | 'action'; // Added 'action'
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
  is_deleted?: boolean;
  [key: string]: any;
}

// 表格配置
const tableConfigs: Record<TableName, TableConfig> = {
  overview_std: {
    columns: [
      { key: "std_question_id", label: "标准问题ID", type: "number", className: "col-id" },
      { key: "std_question_body", label: "标准问题", type: "text", className: "col-text-long", multiline: true },
      { key: "std_question_type", label: "问题类型", type: "text", className: "col-text-short" },
      { key: "std_answer_id", label: "标准答案ID", type: "number", className: "col-id" },
      { key: "std_answer_body", label: "标准答案", type: "text", className: "col-text-long", multiline: true },
      { key: "scoring_points_count", label: "得分点数", type: "number", className: "col-number" },
      { key: "created_at", label: "创建时间", type: "date", className: "col-date" },
      { key: "updated_at", label: "更新时间", type: "date", className: "col-date" },
    ],
    editable: [] // Overview is not editable
  },
  std_questions: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "col-id" },
      { key: "body", label: "问题内容", type: "text", className: "col-text-long", multiline: true },
      { key: "question_type", label: "问题类型", type: "text", className: "col-text-short" },
      { key: "std_answer_id", label: "关联答案ID", type: "number", className: "col-id" },
      { key: "tags", label: "标签", type: "tags", className: "col-tags" },
      { key: "created_at", label: "创建时间", type: "date", className: "col-date" },
      { key: "updated_at", label: "更新时间", type: "date", className: "col-date" },
      { key: "is_deleted", label: "已删除", type: "boolean", className: "col-boolean" },
    ],
    editable: ["body", "question_type", "tags"]
  },
  std_answers: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "col-id" },
      { key: "answer", label: "答案内容", type: "text", className: "col-text-long", multiline: true },
      { key: "scoring_points_count", label: "得分点数", type: "action", className: "col-action" }, // Type changed to action for button
      { key: "tags", label: "标签", type: "tags", className: "col-tags" },
      { key: "created_at", label: "创建时间", type: "date", className: "col-date" },
      { key: "updated_at", label: "更新时间", type: "date", className: "col-date" },
      { key: "is_deleted", label: "已删除", type: "boolean", className: "col-boolean" },
    ],
    editable: ["answer", "tags"]
  }
};

// 响应式数据
const selectedTable = ref<TableName>("overview_std");
const currentDatasetId = ref<number | undefined>(undefined);
const currentDataset = ref<any>(null);
const currentData = ref<DatabaseItem[]>([]);
const selectedItems = ref<number[]>([]); // Stores IDs of selected items
const loading = ref(false);
// const showDeleted = ref(false); // This seems replaced by viewMode
const viewMode = ref<"all" | "deleted_only" | "active_only">("active_only");
const itemsPerPage = ref(20);
const currentPage = ref(1);
const totalItems = ref(0);
const deletedCount = ref(0);

// Refs for modals and selected item state
const selectedItem = ref<DatabaseItem | null>(null);
const showDetailModal = ref(false);
const editForm = ref<any>({});
const showEditModal = ref(false);
const saving = ref(false); // For edit save operation
const showScoringPointsModal = ref(false);
const scoringPointsData = ref<any[]>([]); // For scoring points modal

// Refs for messaging
const message = ref<string | null>(null);
const messageType = ref<'success' | 'error'>('success');

// Computed property for selected deleted items (used for bulk restore button)
const selectedDeletedItems = computed(() => {
  return selectedItems.value.filter(id => {
    const item = currentData.value.find(d => d.id === id);
    return item && item.is_deleted;
  });
});

// Helper function to show messages
const showMessage = (msg: string, type: 'success' | 'error' = 'success', duration: number = 3000) => {
  message.value = msg;
  messageType.value = type;
  setTimeout(() => {
    message.value = null;
  }, duration);
};

// Helper function to determine input type for edit form
const getInputType = (columnType: 'text' | 'number' | 'date' | 'tags' | 'boolean' | 'action') => {
  if (columnType === 'number') return 'number';
  if (columnType === 'date') return 'date';
  // Add other mappings if needed
  return 'text';
};

// Computed Properties
const isOverviewTable = computed(() => selectedTable.value === "overview_std");

const tableColumns = computed(() => {
  return tableConfigs[selectedTable.value]?.columns || [];
});

const editableColumns = computed(() => {
  const config = tableConfigs[selectedTable.value];
  if (!config || !config.editable) return [];
  return config.columns.filter(col => config.editable.includes(col.key));
});

const totalPages = computed(() => {
  if (totalItems.value === 0 || itemsPerPage.value === 0) return 1;
  return Math.ceil(totalItems.value / itemsPerPage.value);
});

// 方法
const goBackToMarketplace = () => {
  router.push('/');
};

const loadDataset = async () => {
  if (!currentDatasetId.value) return;
  
  try {
    currentDataset.value = await datasetService.getDataset(currentDatasetId.value);
  } catch (error) {
    showMessage("加载数据集信息失败", "error");
    console.error("Load dataset error:", error);
  }
};

const loadTableData = async () => {
  loading.value = true;
  selectedItems.value = []; // Clear selection on data load
  try {
    const skip = (currentPage.value - 1) * itemsPerPage.value;
    const limit = itemsPerPage.value;
    
    let includeDeleted = false;
    let deletedOnly = false;
    
    if (viewMode.value === 'all') {
      includeDeleted = true;
    } else if (viewMode.value === 'deleted_only') {
      // includeDeleted = true; // This was redundant, deletedOnly implies includeDeleted in backend/service
      deletedOnly = true;
    }
    
    let result;
    if (selectedTable.value === 'overview_std') {
      result = await databaseService.getStdQuestionsOverview(
        skip,
        limit,
        currentDatasetId.value
      );
    } else {
      // Corrected order of arguments for getTableData
      // Assuming signature: (tableName, skip, limit, datasetId, includeDeleted, deletedOnly)
      // If datasetId is optional and comes after flags, adjust accordingly.
      // For now, placing datasetId before flags as per common patterns.
      result = await databaseService.getTableData(
        selectedTable.value,
        skip,
        limit,
        currentDatasetId.value, // datasetId
        includeDeleted,         // includeDeleted
        deletedOnly             // deletedOnly
      );
    }
    
    currentData.value = result.data;
    totalItems.value = result.total;
    deletedCount.value = result.deletedCount || 0;
  } catch (error) {
    showMessage("加载数据失败", "error");
    console.error("Load data error:", error);
    currentData.value = []; // Ensure data is cleared on error
    totalItems.value = 0;
    deletedCount.value = 0;
  } finally {
    loading.value = false;
  }
};

const refreshData = () => {
  currentPage.value = 1;
  loadTableData();
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
  const deletedItemIds = selectedDeletedItems.value;
  if (!confirm(`确定要恢复选中的 ${deletedItemIds.length} 项吗？`)) return;
  
  try {
    await databaseService.bulkRestore(selectedTable.value, deletedItemIds);
    showMessage(`成功恢复 ${deletedItemIds.length} 项`, "success");
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
    // 查找当前项目以检查删除状态
    const currentItem = currentData.value.find(item => item.id === id);
    
    // 如果项目未被软删除，先软删除
    if (currentItem && !currentItem.is_deleted) {
      await databaseService.deleteItem(selectedTable.value, id);
    }
    
    // 然后强制删除
    await databaseService.forceDeleteItem(selectedTable.value, id);
    showMessage("永久删除成功", "success");
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(itemId => itemId !== id);
    
    loadTableData();
  } catch (error) {
    showMessage("永久删除失败", "error");
  }
};

// 标准问题/答案绑定删除逻辑
const deleteStdItem = async (item: DatabaseItem) => {
  const itemType = selectedTable.value === 'std_questions' ? '标准问题' : '标准答案';
  const bindingType = selectedTable.value === 'std_questions' ? '标准答案' : '标准问题';
  
  if (!confirm(`确定要删除这个${itemType}吗？\n\n注意：删除${itemType}将同时删除关联的${bindingType}！`)) return;
  
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
    // 如果项目未被软删除，先软删除
    if (!item.is_deleted) {
      if (selectedTable.value === 'std_questions') {
        await databaseService.deleteItem('std_questions', item.id);
      } else {
        await databaseService.deleteItem('std_answers', item.id);
      }
    }
    
    // 然后强制删除
    await databaseService.forceDeleteItem(selectedTable.value, item.id);
    showMessage(`${itemType}永久删除成功`, "success");
    
    // 从选中项中移除
    selectedItems.value = selectedItems.value.filter(itemId => itemId !== item.id);
    
    loadTableData();
  } catch (error) {
    showMessage(`${itemType}永久删除失败`, "error");
  }
};

// 得分点管理
const manageScoringPoints = async (stdAnswer: DatabaseItem) => {
  selectedItem.value = stdAnswer;
  
  try {
    // 获取所有得分点（包含已删除的） - 不传递is_valid参数
    const response = await fetch(`/api/std-answers/${stdAnswer.id}/scoring-points`);
    
    if (response.ok) {
      const allPoints = await response.json();
      scoringPointsData.value = allPoints;
    } else {
      console.error("获取得分点失败:", response.status);
      scoringPointsData.value = [];
    }
    
    showScoringPointsModal.value = true;
  } catch (error) {
    console.error("获取得分点数据失败:", error);
    showMessage("获取得分点数据失败", "error");
    scoringPointsData.value = [];
    showScoringPointsModal.value = true;
  }
};

const deleteScoringPoint = async (pointId: number) => {
  if (!confirm("确定要删除这个得分点吗？")) return;
  
  try {
    await fetch(`/api/std-answers/scoring-points/${pointId}`, {
      method: 'DELETE'
    });
    showMessage("得分点删除成功", "success");
    
    // 刷新得分点数据
    if (selectedItem.value) {
      await manageScoringPoints(selectedItem.value);
    }
  } catch (error) {
    showMessage("得分点删除失败", "error");
  }
};

const restoreScoringPoint = async (pointId: number) => {
  try {
    await fetch(`/api/std-answers/scoring-points/${pointId}/restore`, {
      method: 'POST'
    });
    showMessage("得分点恢复成功", "success");
    
    // 刷新得分点数据
    if (selectedItem.value) {
      await manageScoringPoints(selectedItem.value);
    }
  } catch (error) {
    showMessage("得分点恢复失败", "error");
  }
};

const forceDeleteScoringPoint = async (pointId: number) => {
  if (!confirm("确定要永久删除这个得分点吗？此操作不可恢复！")) return;
  
  try {
    // 查找当前得分点以检查删除状态
    const currentPoint = scoringPointsData.value.find(point => point.id === pointId);
    
    // 如果得分点未被软删除，先软删除
    if (currentPoint && !currentPoint.is_deleted) {
      await fetch(`/api/std-answers/scoring-points/${pointId}`, {
        method: 'DELETE'
      });
    }
    
    // 然后强制删除
    await fetch(`/api/std-answers/scoring-points/${pointId}/force-delete`, {
      method: 'DELETE'
    });
    showMessage("得分点永久删除成功", "success");
    
    // 刷新得分点数据
    if (selectedItem.value) {
      await manageScoringPoints(selectedItem.value);
    }
  } catch (error) {
    showMessage("得分点永久删除失败", "error");
  }
};

const closeScoringPointsModal = () => {
  showScoringPointsModal.value = false;
  selectedItem.value = null;
  scoringPointsData.value = [];
};

const manageScoringPointsForQuestion = async (questionItem: DatabaseItem) => {
  if (!questionItem.std_answer_id) {
    showMessage("该标准问题没有关联的标准答案，无法管理得分点。", "error"); // 修正 messageType
    return;
  }
  // 模拟一个标准答案对象，或者如果后端能在获取标准问题时直接返回关联的标准答案对象则更好
  const mockStdAnswer = { id: questionItem.std_answer_id, answer: '关联的标准答案 (ID: ' + questionItem.std_answer_id + ')' };
  await manageScoringPoints(mockStdAnswer);
};

const handleViewModeChange = () => {
  currentPage.value = 1;
  selectedItems.value = []; // Clear selection when view mode changes
  loadTableData();
};

const viewItem = (item: any) => {
  selectedItem.value = item;
  showDetailModal.value = true;
};

const editItem = (item: any) => {
  selectedItem.value = item;
  editForm.value = { ...item };
  showEditModal.value = true;
};

const saveEdit = async () => {
  if (!selectedItem.value) return;
  
  saving.value = true;
  try {
    await databaseService.updateItem(selectedTable.value, selectedItem.value.id, editForm.value);
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

const formatCellValue = (value: any, column: TableColumn): string => {
  if (value === null || typeof value === 'undefined' || value === '') {
    if (selectedTable.value === 'overview_std') {
        // Special handling for overview table to show question body or answer body
        if (column.key === 'std_question_body' && !value) return '(无标准问题)';
        if (column.key === 'std_answer_body' && !value) return '(无标准答案)';
    }
    return '-';
  }

  if (column.type === 'text') {
    if (Array.isArray(value)) {
      if (value.length === 0) return '(空列表)';
      const joinedValue = value.map(v => String(v ?? '-')).join(', ');
      return joinedValue.length > 100 ? joinedValue.substring(0, 97) + '...' : joinedValue;
    }
    const stringValue = String(value);
    const longTextKeys = ['std_question_body', 'std_answer_body', 'answer', 'body', 'title', 'content', 'description'];
    if (longTextKeys.includes(column.key) && stringValue.length > 100) {
      return stringValue.substring(0, 97) + '...';
    }
    return stringValue;
  }
  if (column.type === 'boolean') {
    return value ? '是' : '否';
  }
  if (column.type === 'date') {
    return formatDate(value);
  }
  // For numbers, tags, actions, the template handles direct rendering or specific components
  return String(value);
};

onMounted(() => {
  const datasetIdFromRoute = route.query.dataset_id;
  if (datasetIdFromRoute) {
    currentDatasetId.value = Number(datasetIdFromRoute);
    loadDataset(); // Load dataset info
  }
  loadTableData(); // Initial data load
});

</script>

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
          <option value="raw_questions">原始问题</option>
          <option value="raw_answers">原始答案</option>
          <option value="expert_answers">专家答案</option>
          <option value="std_questions">标准问题</option>
          <option value="std_answers">标准答案</option>
          <option value="overview_std">标准问题总览</option>
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
    <div class="actions-bar" v-if="!isOverviewTable">
      <div class="bulk-actions">
        <button 
          @click="selectAll" 
          class="action-btn"
          :disabled="currentData.length === 0"
        >
          {{ selectedItems.length === currentData.length ? "取消全选" : "全选" }}
        </button>
        <button 
          @click="bulkDelete" 
          class="action-btn danger"
          :disabled="selectedItems.length === 0"
        >
          批量删除 ({{ selectedItems.length }})
        </button>
        <button 
          @click="bulkRestore" 
          class="action-btn success"
          :disabled="selectedItems.length === 0"
        >
          批量恢复 ({{ selectedItems.length }})
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
      <table class="data-table" v-if="currentData.length > 0">        <thead>
          <tr>
            <th class="checkbox-col" v-if="!isOverviewTable">
              <input 
                type="checkbox" 
                :checked="selectedItems.length === currentData.length && currentData.length > 0"
                @change="selectAll"
              />
            </th>
            <th v-for="column in tableColumns" :key="column.key" :class="column.className">
              {{ column.label }}
            </th>
            <th class="actions-col" v-if="!isOverviewTable">操作</th>
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
            </td>
            <td v-for="column in tableColumns" :key="column.key" :class="column.className">
              <div class="cell-content" :class="column.type">
                <span v-if="column.type === 'text'" class="text-content">
                  {{ formatCellValue(item[column.key], column) }}
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
              </div>            </td>
            <td class="actions-col" v-if="!isOverviewTable">              <div class="row-actions">
                <button 
                  @click="viewItem(item)" 
                  class="action-btn small"
                  title="查看详情"
                >
                  📄
                </button>
                <button 
                  v-if="!item.is_deleted"
                  @click="editItem(item)" 
                  class="action-btn small"
                  title="编辑"
                >
                  ✏️
                </button>
                <button 
                  v-if="!item.is_deleted"
                  @click="deleteItem(item.id)" 
                  class="action-btn small danger"
                  title="软删除"
                >
                  🗑️
                </button>
                <button 
                  v-if="item.is_deleted"
                  @click="restoreItem(item.id)" 
                  class="action-btn small success"
                  title="恢复"
                >
                  ♻️
                </button>
                <button 
                  v-if="item.is_deleted"
                  @click="forceDeleteItem(item.id)" 
                  class="action-btn small danger"
                  title="永久删除"
                >
                  ❌
                </button>
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
          <div v-if="selectedItem" class="detail-content">
            <div v-for="(value, key) in selectedItem" :key="key" class="detail-item">
              <strong>{{ key }}:</strong>
              <span class="detail-value">{{ formatDetailValue(value) }}</span>
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
        <div class="modal-content">
          <form @submit.prevent="saveEdit" class="edit-form">
            <div v-for="column in editableColumns" :key="column.key" class="form-group">
              <label :for="column.key">{{ column.label }}:</label>
              <textarea 
                v-if="column.type === 'text' && column.multiline"
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

// 路由
const route = useRoute();
const router = useRouter();

// 类型定义
interface TableColumn {
  key: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'tags' | 'boolean';
  className: string;
  multiline?: boolean;
}

interface TableConfig {
  columns: TableColumn[];
  editable: string[];
}

type TableName = 'raw_questions' | 'raw_answers' | 'expert_answers' | 'std_questions' | 'std_answers' | 'overview_std';

interface DatabaseItem {
  id: number;
  is_deleted?: boolean;
  [key: string]: any;
}

// 响应式数据
const selectedTable = ref<TableName>("raw_questions");
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
const deletedCount = ref(0);

// 弹窗相关
const showDetailModal = ref(false);
const showEditModal = ref(false);
const selectedItem = ref<DatabaseItem | null>(null);
const editForm = ref<Record<string, any>>({});
const saving = ref(false);

// 消息提示
const message = ref("");
const messageType = ref<"success" | "error">("success");

// 表格配置
const tableConfigs: Record<TableName, TableConfig> = {  raw_questions: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "title", label: "标题", type: "text", className: "title-col", multiline: true },
      { key: "author", label: "作者", type: "text", className: "author-col" },
      { key: "votes", label: "投票", type: "text", className: "votes-col" },
      { key: "views", label: "浏览", type: "text", className: "views-col" },
      { key: "tags", label: "标签", type: "tags", className: "tags-col" },
      { key: "issued_at", label: "发布时间", type: "date", className: "date-col" },
    ],
    editable: ["title", "author", "votes", "views"]
  },
  raw_answers: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "question_id", label: "问题ID", type: "number", className: "question-id-col" },
      { key: "answer", label: "答案内容", type: "text", className: "answer-col", multiline: true },
      { key: "answered_by", label: "回答者", type: "text", className: "author-col" },
      { key: "upvotes", label: "赞同", type: "number", className: "votes-col" },
      { key: "answered_at", label: "回答时间", type: "date", className: "date-col" },
    ],
    editable: ["answer", "answered_by", "upvotes"]
  },  expert_answers: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "question_id", label: "问题ID", type: "number", className: "question-id-col" },
      { key: "answer", label: "专家答案", type: "text", className: "answer-col", multiline: true },
      { key: "answered_by", label: "专家ID", type: "number", className: "author-col" },
      { key: "answered_at", label: "回答时间", type: "date", className: "date-col" },
    ],
    editable: ["answer", "answered_by"]
  },  std_questions: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "dataset_id", label: "数据集ID", type: "number", className: "dataset-col" },
      { key: "raw_question_id", label: "原始问题ID", type: "number", className: "question-id-col" },
      { key: "body", label: "问题文本", type: "text", className: "text-col", multiline: true },
      { key: "question_type", label: "问题类型", type: "text", className: "type-col" },
      { key: "version", label: "版本", type: "number", className: "version-col" },
      { key: "created_by", label: "创建者", type: "number", className: "author-col" },
      { key: "is_valid", label: "有效", type: "boolean", className: "valid-col" },
    ],
    editable: ["body", "question_type", "created_by"]
  },  std_answers: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "std_question_id", label: "标准问题ID", type: "number", className: "question-id-col" },
      { key: "answer", label: "答案文本", type: "text", className: "answer-col", multiline: true },
      { key: "version", label: "版本", type: "number", className: "version-col" },
      { key: "answered_by", label: "回答者", type: "number", className: "author-col" },
      { key: "is_valid", label: "有效", type: "boolean", className: "valid-col" },
    ],
    editable: ["answer", "answered_by"]
  },
  overview_std: {
    columns: [
      { key: "id", label: "ID", type: "number", className: "id-col" },
      { key: "text", label: "标准问题", type: "text", className: "title-col", multiline: true },
      { key: "answer_text", label: "标准答案", type: "text", className: "answer-col", multiline: true },
      { key: "raw_questions", label: "原始问题", type: "text", className: "title-col", multiline: true },
      { key: "raw_answers", label: "原始回答", type: "text", className: "answer-col", multiline: true },
      { key: "expert_answers", label: "专家回答", type: "text", className: "answer-col", multiline: true },
      { key: "question_type", label: "问题类型", type: "text", className: "type-col" },
      { key: "created_by", label: "创建者", type: "text", className: "author-col" },
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
    
    let result;
    if (selectedTable.value === 'overview_std') {
      result = await databaseService.getStdQuestionsOverview(
        currentDatasetId.value, 
        skip, 
        limit
      );
    } else {
      result = await databaseService.getTableData(
        selectedTable.value,
        skip,
        limit,
        includeDeleted,
        currentDatasetId.value,
        deletedOnly
      );
    }
    
    currentData.value = result.data;
    totalItems.value = result.total;
    deletedCount.value = result.deletedCount || 0;
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
  if (!confirm(`确定要恢复选中的 ${selectedItems.value.length} 项吗？`)) return;
  
  try {
    await databaseService.bulkRestore(selectedTable.value, selectedItems.value);
    showMessage(`成功恢复 ${selectedItems.value.length} 项`, "success");
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

const formatCellValue = (value: any, column: any) => {
  if (!value) return "";
  
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
      text = value.content || value.answer || value.text || value.title || JSON.stringify(value);
    } else {
      text = String(value);
    }
    
    return text.length > 100 ? text.substring(0, 100) + "..." : text;
  }
  
  return value;
};

const formatDate = (dateString: string) => {
  if (!dateString) return "";
  return new Date(dateString).toLocaleString("zh-CN");
};

const formatDetailValue = (value: any) => {
  if (value === null || value === undefined) return "无";
  if (typeof value === "boolean") return value ? "是" : "否";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
};

const parseTagsValue = (value: any) => {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [value];
    } catch {
      return value.split(",").map(tag => tag.trim()).filter(Boolean);
    }
  }
  return [];
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

// 生命周期
onMounted(async () => {
  // 从路由参数获取数据集ID
  const datasetId = route.query.dataset;
  if (datasetId && !isNaN(Number(datasetId))) {
    currentDatasetId.value = Number(datasetId);
    await loadDataset();
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
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
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
</style>

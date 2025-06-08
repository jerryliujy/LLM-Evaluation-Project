<template>
  <div class="dataset-marketplace">
    <!-- 用户信息头部 -->
    <div class="user-header">
      <div class="user-info">
        <span class="welcome">欢迎，{{ userInfo?.username }}</span>
        <span class="role-badge" :class="userRoleClass">{{ getRoleLabel() }}</span>
      </div>
      <div class="header-actions">
        <button v-if="userInfo?.role === 'admin'" @click="goToHome" class="nav-btn">
          管理控制台
        </button>
        <button @click="logout" class="logout-btn">
          退出登录
        </button>
      </div>
    </div>
      <div class="header">
      <h2>数据库市场</h2>      <div class="header-actions">
        <!-- must use click.stop to avoid handleClickOUtside -->
        <button v-if="userInfo?.role === 'admin'" @click.stop="showCreateModal = true" class="create-btn">
          <span class="btn-icon">🏗️</span>
          <span>手动创建数据库</span>
        </button>
        <button v-if="userInfo?.role === 'admin'" @click="goToDataImportForNew" class="create-btn">
          <span class="btn-icon">📁</span>
          <span>导入创建数据库</span>
        </button>
        <button @click="refreshDatasets" class="refresh-btn" :disabled="loading">
          {{ loading ? "加载中..." : "刷新" }}
        </button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filters">
      <div class="filter-tabs">
        <button 
          :class="['tab-btn', { active: activeTab === 'marketplace' }]"
          @click="switchTab('marketplace')"
        >
          数据库市场
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'my-datasets' }]"
          @click="switchTab('my-datasets')"
        >
          我的数据库
        </button>
      </div>
    </div>

    <!-- 数据集列表 -->
    <div class="datasets-grid" v-if="datasets.length > 0">
      <div 
        v-for="dataset in datasets" 
        :key="dataset.id"        class="dataset-card"
        :class="{ 'my-dataset': isDatasetOwner(dataset) }"
      >
        <div class="card-header">
          <h3 class="dataset-name">{{ dataset.name }}</h3>          <div class="dataset-meta">
            <span class="creator">创建者: {{ dataset.creator_username || 'Unknown' }}</span>
            <span class="visibility">
              {{ dataset.is_public ? '公开' : '私有' }}
            </span>
          </div>
        </div>

        <div class="card-body">
          <p class="dataset-description">{{ dataset.description }}</p>
          
          <div class="dataset-stats">
            <div class="stat-item">
              <span class="stat-label">标准问题:</span>
              <span class="stat-value">{{ dataset.std_questions_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">标准答案:</span>
              <span class="stat-value">{{ dataset.std_answers_count || 0 }}</span>
            </div>
          </div>

          <div class="creation-time">
            创建时间: {{ formatDate(dataset.create_time) }}
          </div>
        </div>

        <div class="card-actions">
          <button 
            @click="enterDataset(dataset)"
            class="action-btn primary"
          >
            进入查看
          </button>
            <button 
            v-if="isDatasetOwner(dataset)"
            @click="goToDataImport(dataset)"
            class="action-btn secondary"
          >
            数据导入
          </button>
          
          <button 
            v-if="isDatasetOwner(dataset)"
            @click.stop="editDataset(dataset)"
            class="action-btn edit"
          >
            编辑
          </button>
          
          <button 
            v-if="isDatasetOwner(dataset)"
            @click="deleteDataset(dataset.id)"
            class="action-btn danger"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="no-datasets">
      <p>{{ activeTab === 'marketplace' ? '暂无公开数据库' : '您还没有创建数据库' }}</p>
    </div>

    <div v-if="loading" class="loading">
      <p>加载中...</p>
    </div>

    <!-- 创建数据库弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeCreateModal">
      <div class="create-modal" @click.stop>
        <div class="modal-header">
          <h3>创建新数据库</h3>
          <button @click="closeCreateModal" class="close-btn">×</button>
        </div>
        <div class="modal-content">
          <form @submit.prevent="createDataset" class="create-form">
            <div class="form-group">
              <label for="dataset-name">数据库名称:</label>
              <input 
                id="dataset-name"
                v-model="createForm.name"
                required
                class="form-control"
                placeholder="输入数据库名称"
              />
            </div>
            
            <div class="form-group">
              <label for="dataset-description">描述:</label>
              <textarea 
                id="dataset-description"
                v-model="createForm.description"
                required
                rows="4"
                class="form-control"
                placeholder="输入数据库描述"
              ></textarea>
            </div>
  
            
            <div class="form-group">
              <label>
                <input 
                  type="checkbox" 
                  v-model="createForm.is_public"
                />
                公开数据库
              </label>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="closeCreateModal" class="cancel-btn">
                取消
              </button>
              <button type="submit" class="save-btn" :disabled="creating">
                {{ creating ? "创建中..." : "创建" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 编辑数据库弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="edit-modal" @click.stop>
        <div class="modal-header">
          <h3>编辑数据库</h3>
          <button @click="closeEditModal" class="close-btn">×</button>
        </div>
        <div class="modal-content">
          <form @submit.prevent="updateDataset" class="edit-form">
            <div class="form-group">
              <label for="edit-dataset-name">数据库名称:</label>
              <input 
                id="edit-dataset-name"
                v-model="editForm.name"
                required
                class="form-control"
              />
            </div>
            
            <div class="form-group">
              <label for="edit-dataset-description">描述:</label>
              <textarea 
                id="edit-dataset-description"
                v-model="editForm.description"
                required
                rows="4"
                class="form-control"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label>
                <input 
                  type="checkbox" 
                  v-model="editForm.is_public"
                />
                公开数据库
              </label>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="closeEditModal" class="cancel-btn">
                取消
              </button>
              <button type="submit" class="save-btn" :disabled="updating">
                {{ updating ? "更新中..." : "更新" }}
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
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { datasetService, type DatasetWithStats, type DatasetCreate } from "@/services/datasetService";
import { authService, type User } from "@/services/authService";

// 路由
const router = useRouter();
const route = useRoute();

// 用户信息
const userInfo = ref<User | null>(null);

// 响应式数据
const datasets = ref<DatasetWithStats[]>([]);
const loading = ref(false);
const activeTab = ref<'marketplace' | 'my-datasets'>('marketplace');

// 弹窗状态
const showCreateModal = ref(false);
const showEditModal = ref(false);
const creating = ref(false);
const updating = ref(false);

// 表单数据
const createForm = ref<DatasetCreate>({
  name: "",
  description: "",
  is_public: true,
});

const editForm = ref<Partial<DatasetCreate> & { id?: number }>({});

// 消息提示
const message = ref("");
const messageType = ref<"success" | "error">("success");

// 方法
const refreshDatasets = async () => {
  loading.value = true;
  try {    if (activeTab.value === 'marketplace') {
      datasets.value = await datasetService.getMarketplace(0, 50);
    } else if (activeTab.value === 'my-datasets') {
      // 获取当前用户的数据集
      datasets.value = await datasetService.getUserDatasets(0, 50);
    }
  } catch (error) {
    showMessage("加载数据库列表失败", "error");
    console.error("Load datasets error:", error);
  } finally {
    loading.value = false;
  }
};

const switchTab = (tab: 'marketplace' | 'my-datasets') => {
  activeTab.value = tab;
  refreshDatasets();
};

const enterDataset = (dataset: DatasetWithStats) => {
  // 跳转到数据库查看页面，传递数据集ID
  router.push({
    name: "DatabaseView",
    params: { id: dataset.id.toString() }
  });
};

const goToDataImport = (dataset: DatasetWithStats) => {
  // 跳转到数据导入页面，传递数据集ID
  router.push({
    name: "DataImport",
    query: { datasetId: dataset.id.toString() }
  });
};

const goToDataImportForNew = () => {
  // 跳转到数据导入页面，不传递数据集ID（创建新数据集）
  router.push({
    name: "DataImport"
  });
};

const createDataset = async () => {
  if (!createForm.value.name || !createForm.value.description) {
    showMessage("请填写完整信息", "error");
    return;
  }

  creating.value = true;
  try {
    await datasetService.createDataset(createForm.value);
    showMessage("数据库创建成功", "success");
    closeCreateModal();
    refreshDatasets();
  } catch (error) {
    showMessage("创建数据库失败", "error");
    console.error("Create dataset error:", error);
  } finally {
    creating.value = false;
  }
};

const editDataset = (dataset: DatasetWithStats) => {
  editForm.value = {
    id: dataset.id,
    name: dataset.name,
    description: dataset.description,
    is_public: dataset.is_public,
  };
  showEditModal.value = true;
};

const updateDataset = async () => {
  if (!editForm.value.id) return;

  updating.value = true;
  try {
    await datasetService.updateDataset(editForm.value.id, editForm.value);
    showMessage("数据库更新成功", "success");
    closeEditModal();
    refreshDatasets();
  } catch (error) {
    showMessage("更新数据库失败", "error");
    console.error("Update dataset error:", error);
  } finally {
    updating.value = false;
  }
};

const deleteDataset = async (id: number) => {
  if (!confirm("确定要删除这个数据库吗？")) return;

  try {
    await datasetService.deleteDataset(id);
    showMessage("数据库删除成功", "success");
    refreshDatasets();
  } catch (error) {
    showMessage("删除数据库失败", "error");
    console.error("Delete dataset error:", error);
  }
};

const closeCreateModal = () => {
  showCreateModal.value = false;
  createForm.value = {
    name: "",
    description: "",
    is_public: true,
  };
};

const closeEditModal = () => {
  showEditModal.value = false;
  editForm.value = {};
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString("zh-CN");
};

const showMessage = (text: string, type: "success" | "error" = "success") => {
  message.value = text;
  messageType.value = type;
  setTimeout(() => {
    message.value = "";
  }, 3000);
};

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.create-modal') && !target.closest('.edit-modal')) {
    showCreateModal.value = false;
    showEditModal.value = false;
  }
};

// 生命周期
// 组件挂载时初始化
onMounted(async () => {
  // 获取用户信息
  try {
    userInfo.value = await authService.getCurrentUser();
  } catch (error) {
    console.error("Get user info error:", error);
    // 如果获取用户信息失败，跳转到登录页
    router.push({ name: 'Login' });
    return;
  }
  
  // 检查URL查询参数中的tab参数
  if (route.query.tab === 'my-datasets') {
    activeTab.value = 'my-datasets';
  }
  
  refreshDatasets();
  
  // 添加点击外部关闭下拉菜单的事件监听器
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  // 清除事件监听器
  document.removeEventListener('click', handleClickOutside);
});

// 用户相关方法
const getRoleLabel = () => {
  const labels = {
    admin: '数据库管理者',
    user: '普通使用者',
    expert: '专家用户'
  };
  return labels[userInfo.value?.role as keyof typeof labels] || '用户';
};

const userRoleClass = computed(() => {
  return {
    'role-admin': userInfo.value?.role === 'admin',
    'role-user': userInfo.value?.role === 'user',
    'role-expert': userInfo.value?.role === 'expert'
  };
});

const goToHome = () => {
  router.push({ name: 'Home' });
};

const logout = () => {
  authService.logout();
  router.push({ name: 'RoleSelection' });
};

// 检查用户是否是数据集的创建者
const isDatasetOwner = (dataset: DatasetWithStats) => {
  return userInfo.value && dataset.created_by === userInfo.value.id;
};
</script>

<style scoped>
.dataset-marketplace {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.user-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.welcome {
  color: #333;
  font-weight: 600;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.role-badge.role-admin {
  background: #007bff;
}

.role-badge.role-user {
  background: #28a745;
}

.role-badge.role-expert {
  background: #ffc107;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.nav-btn {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s ease;
}

.nav-btn:hover {
  background: #138496;
}

.logout-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s ease;
}

.logout-btn:hover {
  background: #c82333;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #eee;
}

.header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.create-btn, .refresh-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.create-btn {
  background-color: #007bff;
  color: white;
}

.create-btn:hover {
  background-color: #0056b3;
}

.refresh-btn {
  background-color: #28a745;
  color: white;
}

.refresh-btn:hover {
  background-color: #1e7e34;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn-icon {
  font-size: 16px;
  line-height: 1;
}

.user-section {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.user-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-input label {
  font-weight: bold;
  min-width: 100px;
}

.current-user {
  font-weight: bold;
  color: #007bff;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.filters {
  margin-bottom: 20px;
}

.filter-tabs {
  display: flex;
  gap: 5px;
}

.tab-btn {
  padding: 10px 20px;
  border: 1px solid #ddd;
  background-color: #f8f9fa;
  cursor: pointer;
  border-radius: 4px 4px 0 0;
  transition: all 0.3s;
}

.tab-btn.active {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.tab-btn:disabled {
  background-color: #e9ecef;
  color: #6c757d;
  cursor: not-allowed;
}

.datasets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.dataset-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: box-shadow 0.3s;
}

.dataset-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.dataset-card.my-dataset {
  border-color: #007bff;
  background-color: #f8f9ff;
}

.card-header {
  margin-bottom: 15px;
}

.dataset-name {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 18px;
}

.dataset-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.creator {
  font-weight: bold;
}

.visibility {
  padding: 2px 6px;
  border-radius: 3px;
  background-color: #e9ecef;
}

.card-body {
  margin-bottom: 15px;
}

.dataset-description {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.4;
}

.dataset-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.stat-label {
  font-size: 11px;
  color: #666;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  color: #007bff;
}

.creation-time {
  font-size: 12px;
  color: #999;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s;
}

.action-btn.primary {
  background-color: #007bff;
  color: white;
}

.action-btn.primary:hover {
  background-color: #0056b3;
}

.action-btn.secondary {
  background-color: #6c757d;
  color: white;
}

.action-btn.secondary:hover {
  background-color: #545b62;
}

.action-btn.edit {
  background-color: #ffc107;
  color: #212529;
}

.action-btn.edit:hover {
  background-color: #e0a800;
}

.action-btn.danger {
  background-color: #dc3545;
  color: white;
}

.action-btn.danger:hover {
  background-color: #c82333;
}

.no-datasets, .loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.create-modal, .edit-modal {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90%;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}

.modal-content {
  padding: 20px;
}

.create-form, .edit-form {
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
  font-weight: bold;
  color: #333;
}

.form-control {
  padding: 8px 12px;
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
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.cancel-btn, .save-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  background-color: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background-color: #545b62;
}

.save-btn {
  background-color: #28a745;
  color: white;
}

.save-btn:hover {
  background-color: #1e7e34;
}

.save-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.message {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  color: white;
  font-weight: bold;
  z-index: 1001;
}

.message.success {
  background-color: #28a745;
}

.message.error {
  background-color: #dc3545;
}

/* 下拉菜单样式 */
/* 美化头部和按钮样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px 32px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.header h2 {
  margin: 0;
  color: white;
  font-size: 28px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.create-btn, .refresh-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.create-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.create-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn-icon {
  font-size: 16px;
  line-height: 1;
}
</style>

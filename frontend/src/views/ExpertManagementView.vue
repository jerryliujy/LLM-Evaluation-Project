<template>
  <div class="expert-management-container">
    <div class="header">
      <h2>专家管理</h2>
      <button @click="showCreateForm = true" class="create-button">
        创建新专家
      </button>
    </div>

    <!-- 创建专家表单 -->
    <div v-if="showCreateForm" class="create-form-overlay">
      <div class="create-form">
        <h3>创建新专家</h3>
        <form @submit.prevent="createExpert">
          <div class="form-group">
            <label for="expertName">姓名:</label>
            <input
              id="expertName"
              v-model="newExpert.name"
              type="text"
              required
              placeholder="请输入专家姓名"
            />
          </div>

          <div class="form-group">
            <label for="expertEmail">邮箱:</label>
            <input
              id="expertEmail"
              v-model="newExpert.email"
              type="email"
              required
              placeholder="请输入专家邮箱"
            />
          </div>

          <div class="form-group">
            <label for="expertPassword">密码:</label>
            <input
              id="expertPassword"
              v-model="newExpert.password"
              type="password"
              required
              placeholder="请输入专家密码"
            />
          </div>

          <div v-if="createError" class="error-message">
            {{ createError }}
          </div>

          <div class="form-actions">
            <button type="button" @click="cancelCreate" class="cancel-button">
              取消
            </button>
            <button type="submit" :disabled="creating" class="submit-button">
              {{ creating ? "创建中..." : "创建" }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 专家列表 -->
    <div class="experts-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="experts.length === 0" class="no-data">暂无专家数据</div>
      <div v-else class="experts-grid">
        <div
          v-for="expert in experts"
          :key="expert.id"
          class="expert-card"
          :class="{ deleted: expert.is_deleted }"
        >
          <div class="expert-info">
            <h4>{{ expert.name }}</h4>
            <p class="email">{{ expert.email }}</p>
            <p class="meta">
              ID: {{ expert.id }} | 创建时间:
              {{ formatDate(expert.created_at) }}
            </p>
            <p v-if="expert.is_deleted" class="deleted-status">已删除</p>
          </div>

          <div class="expert-actions">
            <button
              v-if="!expert.is_deleted"
              @click="deleteExpert(expert.id)"
              class="delete-button"
              :disabled="deleting[expert.id]"
            >
              {{ deleting[expert.id] ? "删除中..." : "删除" }}
            </button>
            <button
              v-else
              @click="restoreExpert(expert.id)"
              class="restore-button"
              :disabled="restoring[expert.id]"
            >
              {{ restoring[expert.id] ? "恢复中..." : "恢复" }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作提示 -->
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { expertService } from "@/services/expertService";
import { Expert, ExpertCreate } from "@/types/expert";

const loading = ref(false);
const creating = ref(false);
const showCreateForm = ref(false);
const createError = ref("");
const message = ref("");
const messageType = ref<"success" | "error">("success");

const experts = ref<Expert[]>([]);
const deleting = reactive<Record<number, boolean>>({});
const restoring = reactive<Record<number, boolean>>({});

const newExpert = ref<ExpertCreate>({
  name: "",
  email: "",
  password: "",
});

const formatDate = (dateString?: string) => {
  if (!dateString) return "未知";
  return new Date(dateString).toLocaleString("zh-CN");
};

const showMessage = (text: string, type: "success" | "error" = "success") => {
  message.value = text;
  messageType.value = type;
  setTimeout(() => {
    message.value = "";
  }, 3000);
};

const loadExperts = async () => {
  loading.value = true;
  try {
    experts.value = await expertService.getAllExperts(true); // 包含已删除的专家
    showMessage("专家数据加载完成");
  } catch (error: any) {
    console.error("Failed to load experts:", error);
    showMessage("加载专家数据失败", "error");
  } finally {
    loading.value = false;
  }
};

const createExpert = async () => {
  if (
    !newExpert.value.name ||
    !newExpert.value.email ||
    !newExpert.value.password
  ) {
    createError.value = "请填写所有必填字段";
    return;
  }

  creating.value = true;
  createError.value = "";

  try {
    const expert = await expertService.createExpert(newExpert.value);
    experts.value.unshift(expert);
    showMessage(`专家 ${expert.name} 创建成功`);
    cancelCreate();
  } catch (error: any) {
    createError.value = error.response?.data?.detail || "创建专家失败";
  } finally {
    creating.value = false;
  }
};

const cancelCreate = () => {
  showCreateForm.value = false;
  createError.value = "";
  newExpert.value = {
    name: "",
    email: "",
    password: "",
  };
};

const deleteExpert = async (expertId: number) => {
  if (!confirm("确定要删除这个专家吗？")) return;

  deleting[expertId] = true;
  try {
    await expertService.deleteExpert(expertId);
    const expert = experts.value.find((e) => e.id === expertId);
    if (expert) {
      expert.is_deleted = true;
    }
    showMessage("专家删除成功");
  } catch (error: any) {
    showMessage("删除专家失败", "error");
  } finally {
    deleting[expertId] = false;
  }
};

const restoreExpert = async (expertId: number) => {
  restoring[expertId] = true;
  try {
    await expertService.restoreExpert(expertId);
    const expert = experts.value.find((e) => e.id === expertId);
    if (expert) {
      expert.is_deleted = false;
    }
    showMessage("专家恢复成功");
  } catch (error: any) {
    showMessage("恢复专家失败", "error");
  } finally {
    restoring[expertId] = false;
  }
};

onMounted(() => {
  loadExperts();
});
</script>

<style scoped>
.expert-management-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header h2 {
  margin: 0;
  color: #333;
}

.create-button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.create-button:hover {
  background-color: #0056b3;
}

.create-form-overlay {
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

.create-form {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 400px;
}

.create-form h3 {
  margin-top: 0;
  margin-bottom: 20px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-button {
  padding: 10px 20px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-button {
  padding: 10px 20px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.experts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.expert-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.expert-card.deleted {
  background-color: #f8f9fa;
  border-color: #dc3545;
}

.expert-info h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.expert-info .email {
  color: #666;
  margin: 5px 0;
}

.expert-info .meta {
  font-size: 12px;
  color: #999;
  margin: 10px 0;
}

.expert-info .deleted-status {
  color: #dc3545;
  font-weight: bold;
  margin: 10px 0;
}

.expert-actions {
  margin-top: 15px;
}

.delete-button {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.restore-button {
  background-color: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.loading,
.no-data {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.message {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  z-index: 1001;
}

.message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>

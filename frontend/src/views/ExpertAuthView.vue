<template>
  <div class="expert-auth-container">
    <div class="auth-card">
      <h2>{{ isLogin ? "专家登录" : "专家注册" }}</h2>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div v-if="!isLogin" class="form-group">
          <label for="name">姓名:</label>
          <input
            id="name"
            v-model="formData.name"
            type="text"
            required
            placeholder="请输入您的姓名"
          />
        </div>

        <div class="form-group">
          <label for="email">邮箱:</label>
          <input
            id="email"
            v-model="formData.email"
            type="email"
            required
            placeholder="请输入邮箱地址"
          />
        </div>

        <div class="form-group">
          <label for="password">密码:</label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            required
            placeholder="请输入密码"
          />
        </div>

        <div v-if="!isLogin" class="form-group">
          <label for="confirmPassword">确认密码:</label>
          <input
            id="confirmPassword"
            v-model="formData.confirmPassword"
            type="password"
            required
            placeholder="请再次输入密码"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading || !isFormValid"
          class="auth-button"
        >
          {{ loading ? "处理中..." : isLogin ? "登录" : "注册" }}
        </button>
      </form>

      <div class="auth-switch">
        <p>
          {{ isLogin ? "还没有账号？" : "已有账号？" }}
          <button type="button" @click="toggleMode" class="switch-button">
            {{ isLogin ? "注册" : "登录" }}
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { expertService } from "@/services/expertService";
import { useExpertStore } from "@/store/expertStore";
import { ExpertCreate, ExpertLogin } from "@/types/expert";

const router = useRouter();
const expertStore = useExpertStore();

const isLogin = ref(true);
const loading = ref(false);
const error = ref("");

const formData = ref({
  name: "",
  email: "",
  password: "",
  confirmPassword: "",
});

const isFormValid = computed(() => {
  if (isLogin.value) {
    return formData.value.email && formData.value.password;
  } else {
    return (
      formData.value.name &&
      formData.value.email &&
      formData.value.password &&
      formData.value.confirmPassword &&
      formData.value.password === formData.value.confirmPassword
    );
  }
});

const toggleMode = () => {
  isLogin.value = !isLogin.value;
  error.value = "";
  formData.value = {
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  };
};

const handleSubmit = async () => {
  if (!isFormValid.value) return;

  loading.value = true;
  error.value = "";

  try {
    if (isLogin.value) {
      // 登录
      const loginData: ExpertLogin = {
        email: formData.value.email,
        password: formData.value.password,
      };

      const response = await expertService.login(loginData);
      expertStore.setExpert(response.expert);

      router.push("/expert-dashboard");
    } else {
      // 注册
      if (formData.value.password !== formData.value.confirmPassword) {
        error.value = "两次输入的密码不一致";
        return;
      }

      const createData: ExpertCreate = {
        name: formData.value.name,
        email: formData.value.email,
        password: formData.value.password,
      };

      const expert = await expertService.createExpert(createData);
      expertStore.setExpert(expert);

      router.push("/expert-dashboard");
    }
  } catch (err: any) {
    error.value =
      err.response?.data?.detail || err.message || "操作失败，请重试";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.expert-auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20px;
}

.auth-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.auth-card h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: #555;
}

.form-group input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  font-size: 14px;
}

.auth-button {
  padding: 12px 24px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.auth-button:hover:not(:disabled) {
  background-color: #0056b3;
}

.auth-button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.auth-switch {
  text-align: center;
  margin-top: 20px;
}

.switch-button {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
  font-size: inherit;
}

.switch-button:hover {
  color: #0056b3;
}
</style>

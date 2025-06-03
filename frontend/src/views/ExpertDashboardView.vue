<template>
  <div class="expert-dashboard">
    <div class="dashboard-header">
      <div class="welcome-section">
        <h2>欢迎，{{ expertStore.expertName }}</h2>
        <p>专家ID: {{ expertStore.currentExpert?.id }}</p>
      </div>
      <button @click="logout" class="logout-button">退出登录</button>
    </div>

    <div class="dashboard-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <h3>我的专家回答</h3>
          <div class="stat-number">{{ stats.expertAnswers }}</div>
          <p>条回答</p>
        </div>

        <div class="stat-card">
          <h3>总投票数</h3>
          <div class="stat-number">{{ stats.totalVotes }}</div>
          <p>票</p>
        </div>

        <div class="stat-card">
          <h3>回答的问题</h3>
          <div class="stat-number">{{ stats.answeredQuestions }}</div>
          <p>个问题</p>
        </div>
      </div>

      <!-- 功能模块 -->
      <div class="feature-grid">
        <router-link to="/expert-answers" class="feature-card">
          <div class="feature-icon">📝</div>
          <h3>管理我的回答</h3>
          <p>查看、编辑和管理您的专家回答</p>
        </router-link>

        <router-link to="/data-import" class="feature-card">
          <div class="feature-icon">📁</div>
          <h3>数据导入</h3>
          <p>导入包含专家回答的问题数据</p>
        </router-link>

        <router-link to="/raw-question-management" class="feature-card">
          <div class="feature-icon">❓</div>
          <h3>问题管理</h3>
          <p>查看和管理原始问题</p>
        </router-link>

        <router-link to="/expert-management" class="feature-card">
          <div class="feature-icon">👥</div>
          <h3>专家管理</h3>
          <p>管理专家账号和权限</p>
        </router-link>
      </div>

      <!-- 最近活动 -->
      <div class="recent-activity">
        <h3>最近活动</h3>
        <div v-if="recentActivities.length === 0" class="no-activity">
          暂无最近活动
        </div>
        <div v-else class="activity-list">
          <div
            v-for="activity in recentActivities"
            :key="activity.id"
            class="activity-item"
          >
            <div class="activity-icon">{{ activity.icon }}</div>
            <div class="activity-content">
              <p class="activity-description">{{ activity.description }}</p>
              <p class="activity-time">{{ formatDate(activity.time) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useExpertStore } from "@/store/expertStore";

const router = useRouter();
const expertStore = useExpertStore();

interface Stats {
  expertAnswers: number;
  totalVotes: number;
  answeredQuestions: number;
}

interface Activity {
  id: number;
  icon: string;
  description: string;
  time: string;
}

const stats = ref<Stats>({
  expertAnswers: 0,
  totalVotes: 0,
  answeredQuestions: 0,
});

const recentActivities = ref<Activity[]>([]);

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString("zh-CN");
};

const logout = () => {
  expertStore.logout();
  router.push("/expert-auth");
};

const loadStats = async () => {
  try {
    // 这里需要调用API获取统计数据
    // 目前模拟数据
    stats.value = {
      expertAnswers: 12,
      totalVotes: 156,
      answeredQuestions: 8,
    };
  } catch (error) {
    console.error("Failed to load stats:", error);
  }
};

const loadRecentActivities = async () => {
  try {
    // 这里需要调用API获取最近活动
    // 目前模拟数据
    recentActivities.value = [
      {
        id: 1,
        icon: "📝",
        description: "回答了关于Docker容器配置的问题",
        time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 2,
        icon: "👍",
        description: "您的回答获得了5个赞",
        time: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 3,
        icon: "📁",
        description: "导入了包含专家回答的数据集",
        time: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
      },
    ];
  } catch (error) {
    console.error("Failed to load recent activities:", error);
  }
};

onMounted(() => {
  // 检查是否已登录
  if (!expertStore.isLoggedIn) {
    router.push("/expert-auth");
    return;
  }

  loadStats();
  loadRecentActivities();
});
</script>

<style scoped>
.expert-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.welcome-section h2 {
  margin: 0 0 5px 0;
  color: #333;
}

.welcome-section p {
  margin: 0;
  color: #666;
}

.logout-button {
  padding: 10px 20px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background-color: #c82333;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-card h3 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
  font-weight: normal;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #007bff;
  margin: 10px 0;
}

.stat-card p {
  margin: 0;
  color: #999;
  font-size: 14px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.feature-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-decoration: none;
  color: inherit;
  transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.feature-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.feature-card h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.feature-card p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.recent-activity {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.recent-activity h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.no-activity {
  text-align: center;
  color: #666;
  padding: 20px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.activity-icon {
  font-size: 20px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 50%;
}

.activity-content {
  flex: 1;
}

.activity-description {
  margin: 0 0 5px 0;
  color: #333;
}

.activity-time {
  margin: 0;
  color: #999;
  font-size: 12px;
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>

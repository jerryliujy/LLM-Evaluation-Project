<template>
  <div class="version-create-container">
    <div class="header">
      <button @click="goBackToDatabase" class="back-btn">
        ← 返回数据库管理
      </button>
      <div class="title-section">
        <h2>创建新版本</h2>
        <p class="subtitle" v-if="currentDataset">
          数据库: {{ currentDataset.name }}
        </p>
      </div>
    </div>    <div class="version-description-section">
      <div class="description-card">
        <h3>版本信息</h3>
        <div class="form-group">
          <label for="version-name">版本名称：</label>
          <input
            id="version-name"
            v-model="versionName"
            placeholder="请输入版本名称，例如：v1.0.0 或 修复问题版本"
            class="form-control"
            required
          />
        </div>
        <div class="form-group">
          <label for="version-description">版本描述：</label>
          <textarea
            id="version-description"
            v-model="versionDescription"
            placeholder="请输入这个版本的描述信息，说明本次更新的内容..."
            rows="3"
            class="form-control"
          ></textarea>
        </div>
        <button @click="createVersionAndStartEdit" class="start-edit-btn" :disabled="!versionName.trim() || creating">
          {{ creating ? "创建中..." : "开始编辑" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { versionService } from '@/services/versionService'
import { datasetService } from '@/services/datasetService'

const router = useRouter()
const route = useRoute()

const datasetId = ref(route.params.datasetId as string)
const versionName = ref('')
const versionDescription = ref('')
const creating = ref(false)
const currentDataset = ref<any>(null)

const goBackToDatabase = () => {
  router.push({ name: 'DatabaseView', params: { id: datasetId.value } })
}

const createVersionAndStartEdit = async () => {
  if (!versionName.value.trim()) return
  
  creating.value = true
  try {
    // 创建新版本
    const newVersion = await versionService.createDatasetVersion(Number(datasetId.value), {
      name: versionName.value.trim(),
      description: versionDescription.value.trim() || undefined
    })
    
    const newVersionId = newVersion.id
    
    // 跳转到编辑界面
    router.push({ 
      name: 'DatabaseVersionEdit', 
      params: { 
        datasetId: datasetId.value,
        versionId: newVersionId
      }
    })
  } catch (error) {
    console.error('创建版本失败:', error)
    alert('创建版本失败，请重试')
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  try {
    // 获取数据库信息
    currentDataset.value = await datasetService.getDataset(Number(datasetId.value))
  } catch (error) {
    console.error('获取数据库信息失败:', error)
  }
})
</script>

<style scoped>
.version-create-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.back-btn {
  padding: 8px 16px;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.back-btn:hover {
  background: #4b5563;
}

.title-section h2 {
  margin: 0;
  color: #1f2937;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  margin: 4px 0 0 0;
  color: #6b7280;
  font-size: 14px;
}

.version-description-section {
  display: flex;
  justify-content: center;
  margin-top: 60px;
}

.description-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  padding: 32px;
  width: 100%;
  max-width: 600px;
}

.description-card h3 {
  margin: 0 0 24px 0;
  color: #1f2937;
  font-size: 18px;
  font-weight: 600;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  transition: border-color 0.2s;
  resize: vertical;
  font-family: inherit;
}

.form-control:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.start-edit-btn {
  width: 100%;
  padding: 12px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.start-edit-btn:hover:not(:disabled) {
  background: #2563eb;
}

.start-edit-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>

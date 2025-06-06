<template>
  <div v-if="visible" class="dialog-overlay" @click="handleClose">
    <div class="dialog-container" @click.stop>
      <div class="dialog-header">
        <h3>问题详情</h3>
        <button class="close-btn" @click="handleClose">&times;</button>
      </div>
        <div class="dialog-body">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>ID:</label>
              <span>{{ question?.id }}</span>
            </div>
            <div class="detail-item">
              <label>标题:</label>
              <span>{{ question?.title }}</span>
            </div>
            <div class="detail-item">
              <label>作者:</label>
              <span>{{ question?.author || '匿名' }}</span>
            </div>
            <div class="detail-item">
              <label>创建时间:</label>
              <span>{{ formatDate(question?.created_at || question?.issued_at) }}</span>
            </div>
            <!-- 概览模式和原始问题模式才显示浏览和点赞数 -->
            <div v-if="(props.viewMode === 'overview' || props.viewMode === 'questions') && question?.view_count !== undefined && question?.view_count !== null" class="detail-item">
              <label>浏览数:</label>
              <span>{{ question.view_count }}</span>
            </div>
            <div v-if="(props.viewMode === 'overview' || props.viewMode === 'questions') && question?.vote_count !== undefined && question?.vote_count !== null" class="detail-item">
              <label>投票数:</label>
              <span>{{ question.vote_count }}</span>
            </div>
          </div>
        </div>

        <!-- 概览模式：只显示问题内容、原始回答和专家回答 -->
        <template v-if="props.viewMode === 'overview'">
          <!-- 问题内容 -->
          <div v-if="question?.body" class="detail-section">
            <h4>问题内容</h4>
            <div class="content-box">
              {{ question.body }}
            </div>
          </div>

          <!-- 原始回答 -->
          <div v-if="question?.raw_answers && question.raw_answers.length > 0" class="detail-section">
            <h4>原始回答 ({{ question.raw_answers.length }})</h4>
            <div class="answers-list">
              <div v-for="answer in question.raw_answers" :key="answer.id" class="answer-item">
                <div class="answer-meta">
                  <span>作者: {{ answer.author || '匿名' }}</span>
                  <span>时间: {{ formatDate(answer.answered_at) }}</span>
                  <span v-if="answer.vote_count !== undefined && answer.vote_count !== null">投票: {{ answer.vote_count }}</span>
                </div>
                <div class="answer-content">
                  {{ answer.content }}
                </div>
              </div>
            </div>
          </div>

          <!-- 专家回答 -->
          <div v-if="question?.expert_answers && question.expert_answers.length > 0" class="detail-section">
            <h4>专家回答 ({{ question.expert_answers.length }})</h4>
            <div class="answers-list">
              <div v-for="answer in question.expert_answers" :key="answer.id" class="answer-item">
                <div class="answer-meta">
                  <span>专家: {{ answer.author || '匿名' }}</span>
                  <span>来源: {{ answer.source }}</span>
                  <span>时间: {{ formatDate(answer.created_at) }}</span>
                </div>
                <div class="answer-content">
                  {{ answer.content }}
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- 非概览模式：显示所有详细信息 -->
        <template v-else>
          <!-- 问题内容 -->
          <div v-if="question?.body" class="detail-section">
            <h4>问题内容</h4>
            <div class="content-box">
              {{ question.body }}
            </div>
          </div>

          <!-- 标签 -->
          <div v-if="question?.tags && question.tags.length > 0" class="detail-section">
            <h4>标签</h4>
            <div class="tags-container">
              <span v-for="tag in question.tags" :key="tag" class="tag">
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- URL -->
          <div v-if="question?.url" class="detail-section">
            <h4>原始链接</h4>
            <a :href="question.url" target="_blank" class="link">{{ question.url }}</a>
          </div>

          <!-- 原始回答 -->
          <div v-if="question?.raw_answers && question.raw_answers.length > 0" class="detail-section">
            <h4>原始回答 ({{ question.raw_answers.length }})</h4>
            <div class="answers-list">
              <div v-for="answer in question.raw_answers" :key="answer.id" class="answer-item">
                <div class="answer-meta">
                  <span>作者: {{ answer.author || '匿名' }}</span>
                  <span>时间: {{ formatDate(answer.answered_at) }}</span>
                  <span v-if="answer.vote_count !== undefined && answer.vote_count !== null">投票: {{ answer.vote_count }}</span>
                </div>
                <div class="answer-content">
                  {{ answer.content }}
                </div>
              </div>
            </div>
          </div>

          <!-- 专家回答 -->
          <div v-if="question?.expert_answers && question.expert_answers.length > 0" class="detail-section">
            <h4>专家回答 ({{ question.expert_answers.length }})</h4>
            <div class="answers-list">
              <div v-for="answer in question.expert_answers" :key="answer.id" class="answer-item">
                <div class="answer-meta">
                  <span>专家: {{ answer.author || '匿名' }}</span>
                  <span>来源: {{ answer.source }}</span>
                  <span>时间: {{ formatDate(answer.created_at) }}</span>
                </div>
                <div class="answer-content">
                  {{ answer.content }}
                </div>
              </div>
            </div>
          </div>

          <!-- 特殊模式下的原始数据展示 -->
          <div v-if="question?.type && question.type !== 'question'" class="detail-section">
            <h4>关联问题信息</h4>
            <div v-if="question.original_data?.question" class="content-box">
              <h5>{{ question.original_data.question.title }}</h5>
              <p v-if="question.original_data.question.body">
                {{ question.original_data.question.body }}
              </p>
            </div>
          </div>
        </template>
      </div>

      <div class="dialog-footer">
        <button @click="handleEdit" class="btn-primary">编辑</button>
        <button @click="handleClose" class="btn-secondary">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RawQuestion } from '@/types/questions'

interface Props {
  visible: boolean
  question: RawQuestion | null
  viewMode?: 'overview' | 'questions' | 'raw-answers' | 'expert-answers'
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'edit', question: RawQuestion): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const handleClose = () => {
  emit('update:visible', false)
}

const handleEdit = () => {
  if (props.question) {
    emit('edit', props.question)
  }
}

const formatDate = (date: string | Date | undefined) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN')
}
</script>

<style scoped>
.dialog-overlay {
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
}

.dialog-container {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e1e5e9;
  background: #f8f9fa;
}

.dialog-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: #e1e5e9;
  color: #333;
}

.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 2px solid #007bff;
  padding-bottom: 4px;
  display: inline-block;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
}

.detail-item label {
  font-weight: 600;
  color: #666;
  font-size: 13px;
  margin-bottom: 4px;
}

.detail-item span {
  color: #333;
  font-size: 14px;
}

.content-box {
  background: #f8f9fa;
  border: 1px solid #e1e5e9;
  border-radius: 4px;
  padding: 16px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: #e7f3ff;
  color: #0366d6;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  border: 1px solid #b3d8ff;
}

.link {
  color: #007bff;
  text-decoration: none;
  word-break: break-all;
}

.link:hover {
  text-decoration: underline;
}

.answers-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.answer-item {
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  overflow: hidden;
}

.answer-meta {
  background: #f8f9fa;
  padding: 12px 16px;
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
  border-bottom: 1px solid #e1e5e9;
}

.answer-content {
  padding: 16px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e1e5e9;
  background: #f8f9fa;
}

.btn-primary {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary:hover {
  background: #545b62;
}
</style>

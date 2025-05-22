<template>
  <div class="raw-question-item">
    <div class="question-header">
        <input
            type="checkbox"
            :checked="store.isSelected('question', question.id)"
            @change="store.toggleSelection('question', question.id)"
        />
        <h3>{{ question.title }} (ID: {{ question.id }})</h3>
        <button @click="confirmDeleteQuestion" class="delete-btn question-delete-btn">删除问题</button>
    </div>
    <div class="question-details">
        <p v_if="question.url"><strong>URL:</strong> <a :href="question.url" target="_blank" rel="noopener noreferrer">{{ question.url }}</a></p>
        <p v_if="question.body"><strong>正文:</strong> {{ question.body }}</p>
        <p>投票: {{ question.vote_count ?? 'N/A' }} | 浏览: {{ question.view_count ?? 'N/A' }}</p>
        <p v_if="question.author">作者: {{ question.author }}</p>
        <p v_if="question.issued_at">发布于: {{ formatDate(question.issued_at) }}</p>
        <p v_if="question.tags && question.tags.length">标签: {{ question.tags.join(', ') }}</p>
    </div>

    <div class="answers-section">
      <h4>原始回答 ({{ question.raw_answers.length }})</h4>
      <div v_if="question.raw_answers.length">
        <RawAnswerItem
          v-for="answer in question.raw_answers"
          :key="`ra-${answer.id}`"
          :answer="answer"
          :questionId="question.id"
        />
      </div>
      <p v-else>无原始回答。</p>
    </div>

    <div class="answers-section">
      <h4>众包回答 ({{ question.expert_answers.length }})</h4>
      <div v_if="question.crowdsourced_answers.length">
        <CrowdsourcedAnswerItem
          v-for="answer in question.expert_answers"
          :key="`ca-${answer.id}`"
          :answer="answer"
          :questionId="question.id"
        />
      </div>
      <p v-else>无众包回答。</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { RawQuestion } from '@/types/questions';
import { useRawQuestionStore } from '@/store/rawQuestionStore';
import RawAnswerItem from './RawAnswerItem.vue';
import CrowdsourcedAnswerItem from './CrowdsourcedAnswerItem.vue';
import { formatDate } from '@/utils/formatters'; // Create this utility

export default defineComponent({
  name: 'RawQuestionItem',
  components: { RawAnswerItem, CrowdsourcedAnswerItem },
  props: {
    question: { type: Object as PropType<RawQuestion>, required: true },
  },
  setup(props) {
    const store = useRawQuestionStore();
    const confirmDeleteQuestion = () => {
      if (confirm(`确定要删除这个问题 (ID: ${props.question.id}) 及其所有回答吗?`)) {
        store.deleteQuestion(props.question);
      }
    };
    return { store, confirmDeleteQuestion, formatDate };
  },
});
</script>

<style scoped>
.raw-question-item { border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; background-color: #fff; }
.question-header { display: flex; align-items: center; margin-bottom: 10px; }
.question-header input[type="checkbox"] { margin-right: 10px; }
.question-header h3 { margin: 0; flex-grow: 1; }
.question-delete-btn { background-color: #ffcccc; border-color: #ffaaaa; }
.question-details p { margin: 4px 0; font-size: 0.9em; color: #333; }
.answers-section { margin-top: 15px; padding-left: 20px; border-left: 3px solid #f0f0f0; }
.answers-section h4 { margin-top: 0; margin-bottom: 10px; }
.delete-btn { padding: 5px 10px; cursor: pointer; }
</style>
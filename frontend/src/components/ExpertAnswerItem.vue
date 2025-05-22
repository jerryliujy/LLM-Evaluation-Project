<template>
  <div class="answer-item crowdsourced-answer-item">
    <input
        type="checkbox"
        :checked="store.isSelected('crowdsourcedAnswer', answer.id)"
        @change="store.toggleSelection('crowdsourcedAnswer', answer.id)"
    />
    <div class="answer-content">
        <p><strong>内容:</strong> {{ answer.content }}</p>
        <p><strong>来源:</strong> {{ answer.source }}</p>
        <p v_if="answer.author">作者: {{ answer.author }}</p>
        <p v_if="answer.vote_count !== undefined">投票: {{ answer.vote_count }}</p>
        <p v_if="answer.created_at">时间: {{ formatDate(answer.created_at) }}</p>
    </div>
    <button @click="confirmDelete" class="delete-btn">删除</button>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { ExpertAnswer } from '@/types/answers';
import { useRawQuestionStore } from '@/store/rawQuestionStore';
import { formatDate } from '@/utils/formatters';

export default defineComponent({
  name: 'ExpertAnswerItem',
  props: {
    answer: { type: Object as PropType<ExpertAnswer>, required: true },
    questionId: { type: Number, required: true },
  },
  setup(props) {
    const store = useRawQuestionStore();
    const confirmDelete = () => {
      if (confirm(`确定要删除这个众包回答 (ID: ${props.answer.id}) 吗?`)) {
        store.deleteCrowdsourcedAnswer(props.answer, props.questionId);
      }
    };
    return { store, confirmDelete, formatDate };
  },
});
</script>
<style scoped>
/* Using same style as RawAnswerItem for consistency, or can be different */
.answer-item { display: flex; align-items: flex-start; border: 1px solid #eef; padding: 8px; margin-bottom: 8px; }
.crowdsourced-answer-item { background: #f0f8ff; } /* Light blueish */
.answer-item input[type="checkbox"] { margin-right: 8px; margin-top: 5px; }
.answer-content { flex-grow: 1; }
.answer-content p { margin: 2px 0; }
.delete-btn { margin-left: auto; padding: 5px 10px; background-color: #ffdddd; border: 1px solid #ffaaaa; cursor: pointer; }
</style>
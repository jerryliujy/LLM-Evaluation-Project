<template>
  <div class="answer-item raw-answer-item">
    <input
      type="checkbox"
      :checked="store.isSelected('rawAnswer', answer.id)"
      @change="store.toggleSelection('rawAnswer', answer.id)"
    />
    <div class="answer-content">
      <p><strong>内容:</strong> {{ answer.answer }}</p>
      <p v-if="answer.answered_by">作者: {{ answer.answered_by }}</p>
      <p v-if="answer.upvotes !== undefined">
        投票: {{ answer.upvotes }}
      </p>
      <p v-if="answer.answered_at">
        时间: {{ formatDate(answer.answered_at) }}
      </p>
    </div>
    <button @click="confirmDelete" class="delete-btn">删除</button>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { RawAnswer } from "@/types/answers";
import { useRawQuestionStore } from "@/store/rawQuestionStore";
import { formatDate } from "@/utils/formatters"; // Helper function

export default defineComponent({
  name: "RawAnswerItem",
  props: {
    answer: { type: Object as PropType<RawAnswer>, required: true },
    questionId: { type: Number, required: true },
  },
  setup(props) {
    const store = useRawQuestionStore();
    const confirmDelete = () => {
      if (confirm(`确定要删除这个原始回答 (ID: ${props.answer.id}) 吗?`)) {
        store.deleteRawAnswer(props.answer, props.questionId);
      }
    };
    return { store, confirmDelete, formatDate };
  },
});
</script>
<style scoped>
.answer-item {
  display: flex;
  align-items: flex-start;
  border: 1px solid #eef;
  padding: 8px;
  margin-bottom: 8px;
  background: #f9f9fd;
}
.answer-item input[type="checkbox"] {
  margin-right: 8px;
  margin-top: 5px;
}
.answer-content {
  flex-grow: 1;
}
.answer-content p {
  margin: 2px 0;
}
.delete-btn {
  margin-left: auto;
  padding: 5px 10px;
  background-color: #ffdddd;
  border: 1px solid #ffaaaa;
  cursor: pointer;
}
</style>

<template>
  <div class="page-container">
    <h1>原始问题与回答管理</h1>
    <RestoreNotification />

    <div class="actions-toolbar">
      <button
        @click="handleDeleteSelected"
        :disabled="!store.hasSelectedItems"
        class="action-btn delete-selected-btn"
      >
        删除选中 ({{ selectedCount }})
      </button>
      <!-- <button @click="navigateToCreate" class="action-btn">创建新问题</button> -->
    </div>

    <div
      v_if="store.isLoading && store.questions.length === 0"
      class="loading-state"
    >
      <p>正在加载问题...</p>
    </div>
    <div v_else-if="store.questions.length === 0" class="empty-state">
      <p>没有可供展示的原始问题。</p>
    </div>
    <div v_else class="questions-list">
      <RawQuestionItem
        v-for="question in store.questions"
        :key="question.id"
        :question="question"
      />
      <button
        @click="store.loadMoreQuestions()"
        v_if="store.hasMore && !store.isLoading"
        class="load-more-btn"
      >
        加载更多
      </button>
      <p
        v_if="store.isLoading && store.questions.length > 0"
        class="loading-state"
      >
        正在加载更多...
      </p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, computed } from "vue";
import { useRawQuestionStore } from "@/store/rawQuestionStore";
import RawQuestionItem from "@/components/RawQuestionItem.vue";
import RestoreNotification from "@/components/RestoreNotification.vue";
// import { useRouter } from 'vue-router'; // If using for navigation

export default defineComponent({
  name: "RawQuestionManagementView",
  components: { RawQuestionItem, RestoreNotification },
  setup() {
    const store = useRawQuestionStore();
    // const router = useRouter(); // For create navigation

    onMounted(() => {
      if (store.questions.length === 0) {
        store.loadInitialQuestions();
      }
    });

    const selectedCount = computed(
      () =>
        store.selectedItemIds.questions.size +
        store.selectedItemIds.rawAnswers.size +
        store.selectedItemIds.expertAnswers.size
    );

    const handleDeleteSelected = () => {
      if (confirm(`确定要删除所有 ${selectedCount.value} 个选中的项目吗?`)) {
        store.deleteSelectedItems();
      }
    };

    // const navigateToCreate = () => {
    //   router.push({ name: 'CreateRawQuestion' }); // Define this route later
    //   alert("创建功能待实现");
    // };

    return {
      store,
      selectedCount,
      handleDeleteSelected,
      // navigateToCreate,
    };
  },
});
</script>

<style scoped>
.page-container {
  max-width: 900px;
  margin: 20px auto;
  padding: 20px;
  font-family: sans-serif;
}
h1 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
}
.actions-toolbar {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
  display: flex;
  gap: 10px;
}
.action-btn {
  padding: 8px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}
.delete-selected-btn {
  background-color: #ff4d4f;
  color: white;
}
.delete-selected-btn:disabled {
  background-color: #f5f5f5;
  color: #ccc;
  cursor: not-allowed;
}
.loading-state,
.empty-state {
  text-align: center;
  color: #777;
  padding: 20px;
}
.questions-list {
  /* styles for the list container if needed */
}
.load-more-btn {
  display: block;
  width: 100%;
  padding: 10px;
  margin-top: 20px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}
.load-more-btn:hover {
  background-color: #40a9ff;
}
</style>

<template>
  <div v_if="store.recentlyDeleted.length > 0" class="restore-panel">
    <h4>最近删除的项目:</h4>
    <ul>
      <li v-for="(item, index) in store.recentlyDeleted" :key="index">
        <span>{{ item.type }} ID: {{ item.id }}</span>
        <button
          @click="store.restoreRecentlyDeletedItem(item)"
          class="restore-btn"
        >
          恢复
        </button>
      </li>
    </ul>
    <button
      @click="store.clearRecentlyDeletedList()"
      v_if="store.recentlyDeleted.length > 0"
    >
      清除列表
    </button>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { useRawQuestionStore } from "@/store/rawQuestionStore";

export default defineComponent({
  name: "RestoreNotification",
  setup() {
    const store = useRawQuestionStore();
    return { store };
  },
});
</script>

<style scoped>
.restore-panel {
  position: fixed;
  bottom: 10px;
  right: 10px;
  width: 300px;
  max-height: 300px;
  overflow-y: auto;
  background-color: #fffbe6; /* Light yellow */
  border: 1px solid #ffe58f;
  border-radius: 4px;
  padding: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}
.restore-panel h4 {
  margin-top: 0;
}
.restore-panel ul {
  list-style-type: none;
  padding: 0;
  margin: 0 0 10px 0;
}
.restore-panel li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px dashed #eee;
}
.restore-panel li:last-child {
  border-bottom: none;
}
.restore-btn {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  padding: 3px 8px;
  cursor: pointer;
}
</style>

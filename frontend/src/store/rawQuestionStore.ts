import { defineStore } from "pinia";
import { RawQuestion } from "@/types/questions";
import { RawAnswer, ExpertAnswer } from "@/types/answers";

interface RecentlyDeletedItem {
  type: "question" | "rawAnswer" | "expertAnswer";
  id: number;
  data: any;
  questionId?: number;
}

export const useRawQuestionStore = defineStore("rawQuestion", {
  state: () => ({
    questions: [] as RawQuestion[],
    isLoading: false,
    currentPage: 0,
    itemsPerPage: 10,
    hasMore: true,
    selectedItemIds: {
      questions: new Set<number>(),
      rawAnswers: new Set<number>(),
      expertAnswers: new Set<number>(),
    },
    recentlyDeleted: [] as RecentlyDeletedItem[],
  }),

  actions: {
    async loadInitialQuestions() {
      this.currentPage = 0;
      this.clearSelections();
      this.loadFromLocalStorage();
      
      // 如果本地没有数据，创建一些示例数据
      if (this.questions.length === 0) {
        await this.loadMoreQuestions();
      }
      this.hasMore = false; // 本地存储模式下不需要分页
    },

    async loadMoreQuestions() {
      if (this.isLoading || !this.hasMore) return;
      this.isLoading = true;

      try {
        // 创建示例数据
        const mockQuestions: RawQuestion[] = [
          {
            id: Date.now() + Math.random(),
            title: "如何在 React 中使用 TypeScript？",
            body: "我想在现有的 React 项目中引入 TypeScript，请问应该如何配置和使用？有什么最佳实践吗？",
            author: "React新手",
            tags: ["javascript", "typescript", "react"],
            issued_at: new Date().toISOString(),
            view_count: 156,
            vote_count: 12,
            raw_answers: [
              {
                id: Date.now() + Math.random() + 1,
                question_id: Date.now() + Math.random(),
                content: "你可以使用 Create React App 的 TypeScript 模板来快速开始...",
                author: "资深开发者",
                vote_count: 8,
                answered_at: new Date().toISOString(),
                is_deleted: false
              }
            ],
            expert_answers: [
              {
                id: Date.now() + Math.random() + 2,
                question_id: Date.now() + Math.random(),
                content: "TypeScript 与 React 结合使用的最佳实践包括：1. 正确定义组件 Props 类型 2. 使用泛型处理状态...",
                source: "官方文档",
                author: "TypeScript 专家",
                created_at: new Date().toISOString(),
                is_deleted: false
              }
            ],
            is_deleted: false,
          },
          {
            id: Date.now() + Math.random() + 100,
            title: "Docker 容器化部署最佳实践",
            body: "项目需要使用 Docker 进行容器化部署，请问有哪些需要注意的事项和最佳实践？",
            author: "DevOps工程师",
            tags: ["docker", "deployment", "devops"],
            issued_at: new Date().toISOString(),
            view_count: 89,
            vote_count: 6,
            raw_answers: [],
            expert_answers: [],
            is_deleted: false,
          },
        ];

        this.questions.push(...mockQuestions);
        this.saveToLocalStorage();
        this.hasMore = false;
        this.currentPage++;
      } catch (error) {
        console.error("Failed to fetch raw questions:", error);
      } finally {
        this.isLoading = false;
      }
    },

    toggleSelection(
      type: "question" | "rawAnswer" | "expertAnswer",
      id: number
    ) {
      const set =
        type === "question"
          ? this.selectedItemIds.questions
          : type === "rawAnswer"
          ? this.selectedItemIds.rawAnswers
          : this.selectedItemIds.expertAnswers;
      if (set.has(id)) {
        set.delete(id);
      } else {
        set.add(id);
      }
    },

    clearSelections() {
      this.selectedItemIds.questions.clear();
      this.selectedItemIds.rawAnswers.clear();
      this.selectedItemIds.expertAnswers.clear();
    },

    deleteQuestion(question: RawQuestion) {
      this.recentlyDeleted.unshift({
        type: "question",
        id: question.id,
        data: JSON.parse(JSON.stringify(question)),
      });

      this.questions = this.questions.filter((q) => q.id !== question.id);
      this.selectedItemIds.questions.delete(question.id);

      if (this.recentlyDeleted.length > 10) this.recentlyDeleted.pop();
    },

    deleteRawAnswer(answer: RawAnswer, questionId: number) {
      this.recentlyDeleted.unshift({
        type: "rawAnswer",
        id: answer.id,
        data: JSON.parse(JSON.stringify(answer)),
        questionId,
      });

      const question = this.questions.find((q) => q.id === questionId);
      if (question) {
        question.raw_answers = question.raw_answers.filter(
          (a) => a.id !== answer.id
        );
      }
      this.selectedItemIds.rawAnswers.delete(answer.id);

      if (this.recentlyDeleted.length > 10) this.recentlyDeleted.pop();
    },

    deleteExpertAnswer(answer: ExpertAnswer, questionId: number) {
      this.recentlyDeleted.unshift({
        type: "expertAnswer",
        id: answer.id,
        data: JSON.parse(JSON.stringify(answer)),
        questionId,
      });

      const question = this.questions.find((q) => q.id === questionId);
      if (question) {
        question.expert_answers = question.expert_answers.filter(
          (a) => a.id !== answer.id
        );
      }
      this.selectedItemIds.expertAnswers.delete(answer.id);

      if (this.recentlyDeleted.length > 10) this.recentlyDeleted.pop();
    },

    deleteSelectedItems() {
      // 删除选中的问题
      const questionIds = Array.from(this.selectedItemIds.questions);
      questionIds.forEach((id) => {
        const question = this.questions.find((q) => q.id === id);
        if (question) {
          this.deleteQuestion(question);
        }
      });

      // 删除选中的原始答案
      const rawAnswerIds = Array.from(this.selectedItemIds.rawAnswers);
      rawAnswerIds.forEach((id) => {
        for (const q of this.questions) {
          const answer = q.raw_answers.find((a) => a.id === id);
          if (answer) {
            this.deleteRawAnswer(answer, q.id);
            break;
          }
        }
      });

      // 删除选中的专家答案
      const expertAnswerIds = Array.from(this.selectedItemIds.expertAnswers);
      expertAnswerIds.forEach((id) => {
        for (const q of this.questions) {
          const answer = q.expert_answers.find((a) => a.id === id);
          if (answer) {
            this.deleteExpertAnswer(answer, q.id);
            break;
          }
        }
      });

      this.clearSelections();
    },

    restoreItem(deletedItem: RecentlyDeletedItem) {
      if (deletedItem.type === "question") {
        const restoredData = deletedItem.data as RawQuestion;
        const index = this.questions.findIndex((q) => q.id === restoredData.id);
        if (index !== -1) {
          this.questions[index] = restoredData;
        } else {
          this.questions.unshift(restoredData);
        }
      } else if (deletedItem.type === "rawAnswer" && deletedItem.questionId) {
        const restoredData = deletedItem.data as RawAnswer;
        const question = this.questions.find(
          (q) => q.id === deletedItem.questionId
        );
        if (question) {
          const index = question.raw_answers.findIndex(
            (a) => a.id === restoredData.id
          );
          if (index !== -1) {
            question.raw_answers[index] = restoredData;
          } else {
            question.raw_answers.push(restoredData);
          }
        }
      } else if (
        deletedItem.type === "expertAnswer" &&
        deletedItem.questionId
      ) {
        const restoredData = deletedItem.data as ExpertAnswer;
        const question = this.questions.find(
          (q) => q.id === deletedItem.questionId
        );
        if (question) {
          const index = question.expert_answers.findIndex(
            (a) => a.id === restoredData.id
          );
          if (index !== -1) {
            question.expert_answers[index] = restoredData;
          } else {
            question.expert_answers.push(restoredData);
          }
        }
      }

      this.recentlyDeleted = this.recentlyDeleted.filter(
        (item) =>
          !(item.id === deletedItem.id && item.type === deletedItem.type)
      );
    },

    clearRecentlyDeleted() {
      this.recentlyDeleted = [];
    },

    deleteSelectedQuestions() {
      const questionIds = Array.from(this.selectedItemIds.questions);
      questionIds.forEach((id) => {
        const question = this.questions.find((q) => q.id === id);
        if (question) {
          this.deleteQuestion(question);
        }
      });
      this.clearSelections();
    },

    addQuestion(question: RawQuestion) {
      this.questions.unshift(question);
      // 保存到本地存储
      this.saveToLocalStorage();
    },

    updateQuestion(updatedQuestion: RawQuestion) {
      const index = this.questions.findIndex((q) => q.id === updatedQuestion.id);
      if (index !== -1) {
        this.questions[index] = updatedQuestion;
        this.saveToLocalStorage();
      }
    },

    addRawAnswer(answer: RawAnswer) {
      const question = this.questions.find((q) => q.id === answer.question_id);
      if (question) {
        question.raw_answers.push(answer);
        this.saveToLocalStorage();
      }
    },

    updateRawAnswer(updatedAnswer: RawAnswer) {
      const question = this.questions.find((q) => q.id === updatedAnswer.question_id);
      if (question) {
        const index = question.raw_answers.findIndex((a) => a.id === updatedAnswer.id);
        if (index !== -1) {
          question.raw_answers[index] = updatedAnswer;
          this.saveToLocalStorage();
        }
      }
    },

    addExpertAnswer(answer: ExpertAnswer) {
      const question = this.questions.find((q) => q.id === answer.question_id);
      if (question) {
        question.expert_answers.push(answer);
        this.saveToLocalStorage();
      }
    },

    updateExpertAnswer(updatedAnswer: ExpertAnswer) {
      const question = this.questions.find((q) => q.id === updatedAnswer.question_id);
      if (question) {
        const index = question.expert_answers.findIndex((a) => a.id === updatedAnswer.id);
        if (index !== -1) {
          question.expert_answers[index] = updatedAnswer;
          this.saveToLocalStorage();
        }
      }
    },

    undoLastDelete() {
      if (this.recentlyDeleted.length > 0) {
        const lastDeleted = this.recentlyDeleted[0];
        this.restoreItem(lastDeleted);
        this.saveToLocalStorage();
      }
    },

    saveToLocalStorage() {
      try {
        const data = {
          questions: this.questions,
          timestamp: Date.now()
        };
        localStorage.setItem('rawQuestionPool', JSON.stringify(data));
      } catch (error) {
        console.error('保存到本地存储失败:', error);
      }
    },

    loadFromLocalStorage() {
      try {
        const stored = localStorage.getItem('rawQuestionPool');
        if (stored) {
          const data = JSON.parse(stored);
          if (data.questions && Array.isArray(data.questions)) {
            this.questions = data.questions;
          }
        }
      } catch (error) {
        console.error('从本地存储加载失败:', error);
      }
    },

  },

  getters: {
    hasSelectedItems(): boolean {
      return (
        this.selectedItemIds.questions.size > 0 ||
        this.selectedItemIds.rawAnswers.size > 0 ||
        this.selectedItemIds.expertAnswers.size > 0
      );
    },

    isSelected(): (
      type: "question" | "rawAnswer" | "expertAnswer",
      id: number
    ) => boolean {
      return (
        type: "question" | "rawAnswer" | "expertAnswer",
        id: number
      ): boolean => {
        const set =
          type === "question"
            ? this.selectedItemIds.questions
            : type === "rawAnswer"
            ? this.selectedItemIds.rawAnswers
            : this.selectedItemIds.expertAnswers;
        return set.has(id);
      };
    },
  },
});

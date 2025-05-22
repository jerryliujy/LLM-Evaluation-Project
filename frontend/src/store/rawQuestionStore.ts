import { defineStore } from 'pinia';
import { RawQuestion } from '@/types/questions';
import { RawAnswer, ExpertAnswer } from '@/types/answers';
import * as service from '@/services/rawQuestionService';

interface RecentlyDeletedItem {
  type: 'question' | 'rawAnswer' | 'expertAnswer';
  id: number;
  data: any; // Store the original data for restoration
  questionId?: number; // For answers, to know where to put them back
}

interface RawQuestionState {
  questions: RawQuestion[];
  isLoading: boolean;
  currentPage: number;
  itemsPerPage: number;
  hasMore: boolean;
  selectedItemIds: {
    questions: Set<number>;
    rawAnswers: Set<number>;
    expertAnswers: Set<number>;
  };
  recentlyDeleted: RecentlyDeletedItem[];
}

export const useRawQuestionStore = defineStore('rawQuestion', {
  state: (): RawQuestionState => ({
    questions: [],
    isLoading: false,
    currentPage: 0,
    itemsPerPage: 10, // Default items per page
    hasMore: true,
    selectedItemIds: {
        questions: new Set(),
        rawAnswers: new Set(),
        expertAnswers: new Set(),
    },
    recentlyDeleted: [],
  }),
  actions: {
    async loadInitialQuestions() {
      this.currentPage = 0;
      this.questions = [];
      this.hasMore = true;
      this.selectedItemIds.questions.clear();
      this.selectedItemIds.rawAnswers.clear();
      this.selectedItemIds.expertAnswers.clear();
      await this.loadMoreQuestions();
    },
    async loadMoreQuestions() {
      if (this.isLoading || !this.hasMore) return;
      this.isLoading = true;
      try {
        const newQuestions = await service.fetchRawQuestions(
          this.currentPage * this.itemsPerPage,
          this.itemsPerPage
        );
        if (newQuestions.length < this.itemsPerPage) {
          this.hasMore = false;
        }
        this.questions.push(...newQuestions);
        this.currentPage++;
      } catch (error) {
        console.error('Failed to fetch raw questions:', error);
        // Consider user feedback e.g. toast notification
      } finally {
        this.isLoading = false;
      }
    },

    // --- Selection ---
    toggleSelection(type: 'question' | 'rawAnswer' | 'expertAnswer', id: number) {
        const set = type === 'question' ? this.selectedItemIds.questions :
                    type === 'rawAnswer' ? this.selectedItemIds.rawAnswers :
                    this.selectedItemIds.expertAnswers;
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

    // --- Deletion ---
    async _deleteItem<T extends {id: number}>(
        item: T,
        itemType: RecentlyDeletedItem['type'],
        deleteFn: (id: number) => Promise<any>,
        questionIdForAnswer?: number
    ) {
        const originalItem = JSON.parse(JSON.stringify(item)); // Deep copy for undo
        try {
            await deleteFn(item.id);
            this.recentlyDeleted.unshift({ type: itemType, id: item.id, data: originalItem, questionId: questionIdForAnswer });
            if (this.recentlyDeleted.length > 10) this.recentlyDeleted.pop(); // Limit undo history

            if (itemType === 'question') {
                this.questions = this.questions.filter(q => q.id !== item.id);
                this.selectedItemIds.questions.delete(item.id);
            } else if (itemType === 'rawAnswer' && questionIdForAnswer) {
                const q = this.questions.find(q => q.id === questionIdForAnswer);
                if (q) q.raw_answers = q.raw_answers.filter(a => a.id !== item.id);
                this.selectedItemIds.rawAnswers.delete(item.id);
            } else if (itemType === 'expertAnswer' && questionIdForAnswer) {
                const q = this.questions.find(q => q.id === questionIdForAnswer);
                if (q) q.expert_answers = q.expert_answers.filter(a => a.id !== item.id);
                this.selectedItemIds.expertAnswers.delete(item.id);
            }
        } catch (error) {
            console.error(`Failed to delete ${itemType} ${item.id}:`, error);
        }
    },
    deleteQuestion(question: RawQuestion) {
        this._deleteItem(question, 'question', service.deleteRawQuestion);
    },
    deleteRawAnswer(answer: RawAnswer, questionId: number) {
        this._deleteItem(answer, 'rawAnswer', service.deleteRawAnswer, questionId);
    },
    deleteExpertAnswer(answer: ExpertAnswer, questionId: number) {
        this._deleteItem(answer, 'expertAnswer', service.deleteExpertAnswer, questionId);
    },
    async deleteSelectedItems() {
        // Questions
        if (this.selectedItemIds.questions.size > 0) {
            const ids = Array.from(this.selectedItemIds.questions);
            await service.deleteMultipleRawQuestions(ids);
            ids.forEach(id => {
                const q = this.questions.find(q => q.id === id);
                if (q) this._deleteItem(q, 'question', async () => {}); // local part of delete
            });
            this.selectedItemIds.questions.clear();
        }
        // Raw Answers
        if (this.selectedItemIds.rawAnswers.size > 0) {
            const ids = Array.from(this.selectedItemIds.rawAnswers);
            await service.deleteMultipleRawAnswers(ids);
             ids.forEach(id => {
                this.questions.forEach(q => {
                    const ans = q.raw_answers.find(a => a.id === id);
                    if(ans) this._deleteItem(ans, 'rawAnswer', async () => {}, q.id);
                });
            });
            this.selectedItemIds.rawAnswers.clear();
        }
        // Expert Answers (similar logic for raw answers)
        if (this.selectedItemIds.expertAnswers.size > 0) {
            const ids = Array.from(this.selectedItemIds.expertAnswers);
            await service.deleteMultipleExpertAnswers(ids);
             ids.forEach(id => {
                this.questions.forEach(q => {
                    const ans = q.expert_answers.find(a => a.id === id);
                    if(ans) this._deleteItem(ans, 'expertAnswer', async () => {}, q.id);
                });
            });
            this.selectedItemIds.expertAnswers.clear();
        }
    },

    // --- Restoration ---
    async restoreRecentlyDeletedItem(deletedItem: RecentlyDeletedItem) {
        try {
            let restoredData;
            if (deletedItem.type === 'question') {
                restoredData = await service.restoreRawQuestion(deletedItem.id);
                // Add/update in this.questions. Could be complex if order matters.
                // For simplicity, just re-fetch or add to top if not too complex.
                // A simple way:
                const index = this.questions.findIndex(q => q.id === restoredData.id);
                if (index !== -1) this.questions[index] = restoredData;
                else this.questions.unshift(restoredData); // Or sort
            } else if (deletedItem.type === 'rawAnswer') {
                restoredData = await service.restoreRawAnswer(deletedItem.id) as RawAnswer;
                const question = this.questions.find(q => q.id === deletedItem.questionId);
                if (question) {
                     const index = question.raw_answers.findIndex(a => a.id === restoredData.id);
                     if (index !== -1) question.raw_answers[index] = restoredData;
                     else question.raw_answers.push(restoredData);
                }
            } else if (deletedItem.type === 'expertAnswer') {
                restoredData = await service.restoreExpertAnswer(deletedItem.id) as ExpertAnswer;
                 const question = this.questions.find(q => q.id === deletedItem.questionId);
                if (question) {
                    const index = question.expert_answers.findIndex(a => a.id === restoredData.id);
                    if (index !== -1) question.expert_answers[index] = restoredData;
                    else question.expert_answers.push(restoredData);
                }
            }
            this.recentlyDeleted = this.recentlyDeleted.filter(item => item.id !== deletedItem.id || item.type !== deletedItem.type);
        } catch (error) {
            console.error(`Failed to restore ${deletedItem.type} ${deletedItem.id}:`, error);
        }
    },
    clearRecentlyDeletedList() {
        this.recentlyDeleted = [];
    }
  },
  getters: {
    hasSelectedItems: (state) => {
        return state.selectedItemIds.questions.size > 0 ||
               state.selectedItemIds.rawAnswers.size > 0 ||
               state.selectedItemIds.expertAnswers.size > 0;
    },
    isSelected: (state) => (type: 'question' | 'rawAnswer' | 'expertAnswer', id: number): boolean => {
        const set = type === 'question' ? state.selectedItemIds.questions :
                    type === 'rawAnswer' ? state.selectedItemIds.rawAnswers :
                    state.selectedItemIds.expertAnswers;
        return set.has(id);
    }
  }
});
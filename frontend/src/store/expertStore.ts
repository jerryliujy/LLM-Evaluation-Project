import { defineStore } from "pinia";
import { Expert } from "@/types/expert";

interface ExpertState {
  currentExpert: Expert | null;
  isAuthenticated: boolean;
  token: string | null;
}

export const useExpertStore = defineStore("expert", {
  state: (): ExpertState => ({
    currentExpert: null,
    isAuthenticated: false,
    token: null,
  }),

  getters: {
    isLoggedIn: (state) =>
      state.isAuthenticated && state.currentExpert !== null,
    expertName: (state) => state.currentExpert?.name || "",
    expertEmail: (state) => state.currentExpert?.email || "",
  },

  actions: {
    setExpert(expert: Expert, token?: string) {
      this.currentExpert = expert;
      this.isAuthenticated = true;
      if (token) {
        this.token = token;
        localStorage.setItem("expert_token", token);
      }
      localStorage.setItem("current_expert", JSON.stringify(expert));
    },

    logout() {
      this.currentExpert = null;
      this.isAuthenticated = false;
      this.token = null;
      localStorage.removeItem("expert_token");
      localStorage.removeItem("current_expert");
    },

    loadFromStorage() {
      const token = localStorage.getItem("expert_token");
      const expertData = localStorage.getItem("current_expert");

      if (token && expertData) {
        try {
          const expert = JSON.parse(expertData);
          this.setExpert(expert, token);
        } catch (error) {
          console.error("Failed to load expert from storage:", error);
          this.logout();
        }
      }
    },
  },
});

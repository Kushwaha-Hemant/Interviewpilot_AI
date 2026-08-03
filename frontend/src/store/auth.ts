"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import { api, setToken } from "@/services/api";
import { needsVerification, type RegisterResult, type User } from "@/types";

interface AuthState {
  user: User | null;
  token: string | null;
  /** False until zustand has read localStorage — guards must wait for this. */
  hydrated: boolean;
  setHydrated: () => void;
  login: (email: string, password: string) => Promise<void>;
  /** Resolves to the raw result so the caller can route to /verify when needed. */
  register: (email: string, password: string, fullName?: string) => Promise<RegisterResult>;
  verifyEmail: (email: string, code: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      hydrated: false,

      setHydrated: () => set({ hydrated: true }),

      login: async (email, password) => {
        const result = await api.login(email, password);
        setToken(result.access_token);
        set({ user: result.user, token: result.access_token });
      },

      register: async (email, password, fullName) => {
        const result = await api.register(email, password, fullName);
        // With verification on, register returns no token — the caller sends the user
        // to /verify and the session begins only after the code is confirmed.
        if (!needsVerification(result)) {
          setToken(result.access_token);
          set({ user: result.user, token: result.access_token });
        }
        return result;
      },

      verifyEmail: async (email, code) => {
        const result = await api.verifyEmail(email, code);
        setToken(result.access_token);
        set({ user: result.user, token: result.access_token });
      },

      logout: () => {
        setToken(null);
        set({ user: null, token: null });
      },

      refresh: async () => {
        if (!get().token) return;
        try {
          set({ user: await api.me() });
        } catch {
          // Token expired or revoked — drop it so the guard redirects to login.
          setToken(null);
          set({ user: null, token: null });
        }
      },
    }),
    {
      name: "interviewpilot.auth",
      partialize: (state) => ({ user: state.user, token: state.token }),
      onRehydrateStorage: () => (state) => {
        // Mirror the persisted token into the slot the plain fetch client reads.
        if (state?.token) setToken(state.token);
        state?.setHydrated();
      },
    },
  ),
);

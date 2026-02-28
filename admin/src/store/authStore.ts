import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  isAuthenticated: boolean
  sessionToken: string | null
  login: (token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      sessionToken: null,
      login: (token: string) => set({ isAuthenticated: true, sessionToken: token }),
      logout: () => set({ isAuthenticated: false, sessionToken: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
)

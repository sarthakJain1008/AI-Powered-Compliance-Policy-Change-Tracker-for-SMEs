/**
 * @module api
 * @description Axios instance and typed API functions for the ComplianceTracker backend.
 * Handles authentication token management, automatic token refresh on 401,
 * and all auth-related API calls.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import Cookies from 'js-cookie'

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  user_id: number
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  is_onboarded?: boolean
  created_at: string
}

export interface MessageResponse {
  message: string
}

interface RegisterData {
  email: string
  password: string
  full_name?: string
  role?: string
}

// ─── Axios Instance ───────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Request Interceptor ──────────────────────────────────────────────────────

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = Cookies.get('access_token')
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error: AxiosError) => Promise.reject(error)
)

// ─── Response Interceptor (Token Refresh) ────────────────────────────────────

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: string) => void
  reject: (reason: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else if (token) {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = Cookies.get('refresh_token')

      if (!refreshToken) {
        clearAuthAndRedirect()
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post<Token>('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        })
        const { access_token, refresh_token: newRefreshToken } = response.data

        Cookies.set('access_token', access_token, {
          secure: true,
          sameSite: 'strict',
          expires: 1,
        })
        Cookies.set('refresh_token', newRefreshToken, {
          secure: true,
          sameSite: 'strict',
          expires: 7,
        })

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }

        processQueue(null, access_token)
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearAuthAndRedirect()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// ─── Helpers ──────────────────────────────────────────────────────────────────

function clearAuthAndRedirect(): void {
  Cookies.remove('access_token')
  Cookies.remove('refresh_token')
  if (typeof window !== 'undefined') {
    window.location.href = '/login'
  }
}

// ─── Auth API ─────────────────────────────────────────────────────────────────

export const authApi = {
  /**
   * Authenticates the user and returns access + refresh tokens.
   */
  async login(email: string, password: string): Promise<Token> {
    const response = await api.post<Token>('/auth/login', { email, password })
    return response.data
  },

  /**
   * Registers a new user account.
   */
  async register(data: RegisterData): Promise<UserResponse> {
    const response = await api.post<UserResponse>('/auth/register', data)
    return response.data
  },

  /**
   * Sends a password reset email to the given address.
   */
  async forgotPassword(email: string): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>('/auth/forgot-password', {
      email,
    })
    return response.data
  },

  /**
   * Resets the user's password using a valid reset token.
   */
  async resetPassword(
    token: string,
    newPassword: string
  ): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>('/auth/reset-password', {
      token,
      new_password: newPassword,
    })
    return response.data
  },

  /**
   * Fetches the current authenticated user's profile.
   */
  async getMe(): Promise<UserResponse> {
    const response = await api.get<UserResponse>('/auth/me')
    return response.data
  },

  /**
   * Logs out the current user by clearing cookies and redirecting to /login.
   */
  logout(): void {
    clearAuthAndRedirect()
  },
}

export default api

'use client'

/**
 * @module useAuth
 * @description Custom React hook for authentication state management.
 * Handles login, logout, and persistent session checking via the /auth/me endpoint.
 */

import { useState, useEffect, useCallback } from 'react'
import Cookies from 'js-cookie'
import { authApi, UserResponse } from '@/lib/api'

interface UseAuthReturn {
  user: UserResponse | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

/**
 * Provides authentication state and actions for the current user session.
 * Checks the stored token on mount and exposes login/logout functionality.
 */
export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const checkAuth = useCallback(async () => {
    const accessToken = Cookies.get('access_token')
    if (!accessToken) {
      setIsLoading(false)
      return
    }

    try {
      const me = await authApi.getMe()
      setUser(me)
    } catch {
      // Token invalid or expired — clear it silently
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    const tokens = await authApi.login(email, password)

    Cookies.set('access_token', tokens.access_token, {
      secure: true,
      sameSite: 'strict',
      expires: 1, // 1 day
    })
    Cookies.set('refresh_token', tokens.refresh_token, {
      secure: true,
      sameSite: 'strict',
      expires: 7, // 7 days
    })

    const me = await authApi.getMe()
    setUser(me)
  }, [])

  const logout = useCallback(() => {
    setUser(null)
    authApi.logout()
  }, [])

  return {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    logout,
  }
}

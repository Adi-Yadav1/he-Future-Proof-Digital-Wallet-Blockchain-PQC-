import React, { createContext, useContext, useEffect, useState } from 'react'
import * as SecureStore from 'expo-secure-store'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const restoreSession = async () => {
      try {
        const userId = await SecureStore.getItemAsync('user_id')
        const username = await SecureStore.getItemAsync('username')
        const walletAddress = await SecureStore.getItemAsync('wallet_address')
        if (userId && username) {
          setUser({ id: userId, username, wallet_address: walletAddress || '' })
        }
      } catch {}
      setLoading(false)
    }
    restoreSession()
  }, [])

  const login = async (userData, userId) => {
    setUser(userData)
    await SecureStore.setItemAsync('user_id', String(userId))
    await SecureStore.setItemAsync('username', userData.username || '')
    if (userData.wallet_address) {
      await SecureStore.setItemAsync('wallet_address', userData.wallet_address)
    }
  }

  const logout = async () => {
    setUser(null)
    await SecureStore.deleteItemAsync('user_id')
    await SecureStore.deleteItemAsync('username')
    await SecureStore.deleteItemAsync('wallet_address')
  }

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

/**
 * Phase 9 — PQC Wallet Mobile API Service
 * Mirrors the same backend endpoints used by the web frontend.
 * Change API_BASE_URL to point to your backend (use your machine's LAN IP
 * when running on a physical device, e.g. http://192.168.1.x:5000)
 */
import axios from 'axios'

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

// Attach user_id header automatically if stored
api.interceptors.request.use(async (config) => {
  try {
    const SecureStore = require('expo-secure-store')
    const userId = await SecureStore.getItemAsync('user_id')
    if (userId) config.headers['X-User-ID'] = userId
  } catch {}
  return config
})

export const authAPI = {
  login: (username, password) => api.post('/login', { username, password }),
  register: (username, password) => api.post('/register', { username, password }),
  getProfile: (userId) => api.get(`/profile/${userId}`),
}

export const blockchainAPI = {
  getBlocks: () => api.get('/blocks'),
  verifyChain: () => api.get('/verify'),
  getExplorer: () => api.get('/explorer'),
  getDemoStats: () => api.get('/demo_stats'),
  getCryptoInfo: () => api.get('/crypto_info'),
  getNetworkMetrics: () => api.get('/network_metrics'),
  getNodeInfo: () => api.get('/node_info'),
  getNetwork: () => api.get('/network'),
  getHealth: () => api.get('/health'),
  getBalance: (walletAddress) => api.get(`/balance/${walletAddress}`),
  getTransactions: (walletAddress) => api.get(`/transactions/${walletAddress}`),
  sendTransaction: (sender, receiver, amount, userId) =>
    api.post('/send_transaction', { sender, receiver, amount, user_id: userId }),
  sendPrivateTransaction: (senderWallet, receiverWallet, amount) =>
    api.post('/private_transaction', { sender_wallet: senderWallet, receiver_wallet: receiverWallet, amount }),
  mineBlock: (userId) => api.post('/mine', userId ? { user_id: userId } : {}),
  mineNow: () => api.post('/mine_now'),
  resetNetwork: () => api.post('/reset_network'),
  simulateTransactions: (count = 5) => api.post('/simulate_transactions', { count }),
  runDemo: () => api.post('/run_demo'),
}

export default api

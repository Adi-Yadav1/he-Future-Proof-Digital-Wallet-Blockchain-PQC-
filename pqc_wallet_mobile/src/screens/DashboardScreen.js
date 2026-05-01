import React, { useState, useEffect } from 'react'
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, RefreshControl, Alert,
} from 'react-native'
import { blockchainAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { getSocket } from '../services/socket'
import { colors, typography, spacing, radius } from '../theme'

export function DashboardScreen({ navigation }) {
  const { user, logout } = useAuth()
  const [balance, setBalance] = useState(0)
  const [demoStats, setDemoStats] = useState(null)
  const [networkMetrics, setNetworkMetrics] = useState(null)
  const [verifyValid, setVerifyValid] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = async () => {
    try {
      const walletRef = user?.wallet_address || user?.id
      const [balRes, statsRes, metricsRes, verifyRes] = await Promise.all([
        walletRef ? blockchainAPI.getBalance(walletRef) : Promise.resolve({ data: { balance: 0 } }),
        blockchainAPI.getDemoStats(),
        blockchainAPI.getNetworkMetrics(),
        blockchainAPI.verifyChain(),
      ])
      setBalance(Number(balRes.data.balance || 0))
      setDemoStats(statsRes.data)
      setNetworkMetrics(metricsRes.data)
      setVerifyValid(verifyRes.data.valid)
    } catch {}
  }

  useEffect(() => {
    loadData().finally(() => setLoading(false))

    // Real-time updates via WebSocket
    const socket = getSocket()
    socket.on('new_block', () => loadData())
    socket.on('network_update', () => loadData())
    return () => {
      socket.off('new_block')
      socket.off('network_update')
    }
  }, [])

  const onRefresh = async () => {
    setRefreshing(true)
    await loadData()
    setRefreshing(false)
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.accent} size="large" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    )
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
    >
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.welcomeText}>Welcome,</Text>
          <Text style={styles.usernameText}>{user?.username}</Text>
        </View>
        <TouchableOpacity onPress={logout} style={styles.logoutBtn}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Balance Card */}
      <View style={styles.balanceCard}>
        <Text style={styles.balanceLabel}>Balance</Text>
        <Text style={styles.balanceValue}>{balance.toFixed(2)}</Text>
        <Text style={styles.balanceCurrency}>PQC</Text>
        <View style={[styles.statusBadge, { backgroundColor: verifyValid ? colors.success + '33' : colors.error + '33' }]}>
          <Text style={{ color: verifyValid ? colors.success : colors.error, fontSize: 12, fontWeight: '700' }}>
            {verifyValid === null ? '⏳ Checking...' : verifyValid ? '✅ Chain Valid' : '❌ Chain Invalid'}
          </Text>
        </View>
      </View>

      {/* Stats Grid */}
      <View style={styles.grid}>
        {[
          { label: 'Blocks', value: demoStats?.total_blocks ?? 0, icon: '📦' },
          { label: 'Transactions', value: demoStats?.total_transactions ?? 0, icon: '💸' },
          { label: 'Wallets', value: demoStats?.total_wallets ?? 0, icon: '👛' },
          { label: 'Difficulty', value: networkMetrics?.difficulty ?? 3, icon: '⛏️' },
        ].map(({ label, value, icon }) => (
          <View key={label} style={styles.statCard}>
            <Text style={styles.statIcon}>{icon}</Text>
            <Text style={styles.statValue}>{value}</Text>
            <Text style={styles.statLabel}>{label}</Text>
          </View>
        ))}
      </View>

      {/* Quick Actions */}
      <View style={styles.actionsCard}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionRow}>
          <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('SendTransaction')}>
            <Text style={styles.actionIcon}>💸</Text>
            <Text style={styles.actionText}>Send</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('PrivateTransaction')}>
            <Text style={styles.actionIcon}>🔒</Text>
            <Text style={styles.actionText}>Private</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('Explorer')}>
            <Text style={styles.actionIcon}>🔍</Text>
            <Text style={styles.actionText}>Explorer</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('Network')}>
            <Text style={styles.actionIcon}>🌐</Text>
            <Text style={styles.actionText}>Network</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Wallet address */}
      <View style={styles.walletCard}>
        <Text style={styles.sectionTitle}>Your Wallet Address</Text>
        <Text style={styles.walletAddress} selectable numberOfLines={2}>
          {user?.wallet_address || 'N/A'}
        </Text>
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, paddingBottom: 40 },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: colors.textMuted, marginTop: spacing.sm },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.lg },
  welcomeText: { ...typography.caption, color: colors.textMuted },
  usernameText: { ...typography.h2, color: colors.textPrimary },
  logoutBtn: { padding: spacing.sm, backgroundColor: colors.surface, borderRadius: radius.sm, borderWidth: 1, borderColor: colors.border },
  logoutText: { color: colors.error, fontWeight: '600', fontSize: 13 },
  balanceCard: {
    backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.lg,
    alignItems: 'center', marginBottom: spacing.md, borderWidth: 1, borderColor: colors.border,
  },
  balanceLabel: { ...typography.label, color: colors.textMuted, marginBottom: spacing.sm },
  balanceValue: { fontSize: 52, fontWeight: '800', color: colors.accent },
  balanceCurrency: { ...typography.h3, color: colors.textMuted, marginBottom: spacing.sm },
  statusBadge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 20 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.md },
  statCard: {
    backgroundColor: colors.surface, flex: 1, minWidth: '45%', borderRadius: radius.md,
    padding: spacing.md, alignItems: 'center', borderWidth: 1, borderColor: colors.border,
  },
  statIcon: { fontSize: 24, marginBottom: 4 },
  statValue: { ...typography.h2, color: colors.textPrimary },
  statLabel: { ...typography.caption, color: colors.textMuted, marginTop: 2 },
  actionsCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.md, borderWidth: 1, borderColor: colors.border },
  sectionTitle: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.md },
  actionRow: { flexDirection: 'row', justifyContent: 'space-around' },
  actionBtn: { alignItems: 'center', flex: 1 },
  actionIcon: { fontSize: 30, marginBottom: 4 },
  actionText: { ...typography.caption, color: colors.textSecondary },
  walletCard: { backgroundColor: colors.surface, borderRadius: radius.md, padding: spacing.md, borderWidth: 1, borderColor: colors.border },
  walletAddress: { ...typography.mono, color: colors.accent, lineHeight: 18 },
})

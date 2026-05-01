import React, { useState, useEffect } from 'react'
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, RefreshControl,
} from 'react-native'
import { blockchainAPI } from '../services/api'
import { getSocket } from '../services/socket'
import { colors, typography, spacing, radius } from '../theme'

export function NetworkScreen() {
  const [nodeInfo, setNodeInfo] = useState(null)
  const [health, setHealth] = useState(null)
  const [networkInfo, setNetworkInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)

  const load = async () => {
    try {
      const [nodeRes, healthRes, netRes] = await Promise.all([
        blockchainAPI.getNodeInfo(),
        blockchainAPI.getHealth(),
        blockchainAPI.getNetwork(),
      ])
      setNodeInfo(nodeRes.data)
      setHealth(healthRes.data)
      setNetworkInfo(netRes.data)
    } catch {}
  }

  useEffect(() => {
    load().finally(() => setLoading(false))
    const socket = getSocket()
    socket.on('connect', () => setWsConnected(true))
    socket.on('disconnect', () => setWsConnected(false))
    socket.on('network_update', () => load())
    setWsConnected(socket.connected)
    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('network_update')
    }
  }, [])

  const onRefresh = async () => {
    setRefreshing(true)
    await load()
    setRefreshing(false)
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    )
  }

  const peers = Array.isArray(nodeInfo?.peers) ? nodeInfo.peers : []

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
    >
      <Text style={styles.title}>Network Monitor</Text>

      {/* WS badge */}
      <View style={[styles.badge, { backgroundColor: wsConnected ? colors.success + '22' : colors.warning + '22' }]}>
        <Text style={{ color: wsConnected ? colors.success : colors.warning, fontWeight: '700' }}>
          {wsConnected ? '🔴 Live (WebSocket)' : '⚪ WebSocket Disconnected'}
        </Text>
      </View>

      {/* Stats */}
      <View style={styles.grid}>
        {[
          { label: 'Node ID', value: nodeInfo?.node_id?.slice(0, 14) + '...' || 'N/A' },
          { label: 'Block Height', value: nodeInfo?.block_height ?? 0 },
          { label: 'Peers', value: networkInfo?.peer_count ?? 0 },
          { label: 'Pending TXs', value: nodeInfo?.pending_transactions ?? 0 },
          { label: 'Health', value: health?.status === 'ok' ? '✅ OK' : '⚠️ Unknown' },
        ].map(({ label, value }) => (
          <View key={label} style={styles.statCard}>
            <Text style={styles.statLabel}>{label}</Text>
            <Text style={styles.statValue} numberOfLines={1}>{String(value)}</Text>
          </View>
        ))}
      </View>

      {/* Peers */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Peer Nodes ({peers.length})</Text>
        {peers.length === 0 ? (
          <Text style={styles.emptyText}>Running in single-node mode</Text>
        ) : (
          peers.map((peer, i) => (
            <View key={i} style={styles.peerRow}>
              <Text style={styles.peerIcon}>🌐</Text>
              <Text style={styles.peerText}>{peer}</Text>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.md, paddingBottom: 40 },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', alignItems: 'center' },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.sm },
  badge: { borderRadius: radius.sm, padding: spacing.sm, alignItems: 'center', marginBottom: spacing.md },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.md },
  statCard: { backgroundColor: colors.surface, flex: 1, minWidth: '45%', borderRadius: radius.md, padding: spacing.md, borderWidth: 1, borderColor: colors.border },
  statLabel: { ...typography.caption, color: colors.textMuted, marginBottom: 4 },
  statValue: { ...typography.h3, color: colors.textPrimary },
  card: { backgroundColor: colors.surface, borderRadius: radius.md, padding: spacing.md, borderWidth: 1, borderColor: colors.border },
  cardTitle: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.md },
  emptyText: { ...typography.body, color: colors.textMuted },
  peerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: 6, borderTopWidth: 1, borderTopColor: colors.border },
  peerIcon: { fontSize: 16 },
  peerText: { ...typography.mono, color: colors.textSecondary },
})

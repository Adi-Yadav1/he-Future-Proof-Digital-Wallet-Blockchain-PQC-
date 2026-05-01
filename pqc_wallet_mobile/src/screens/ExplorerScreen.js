import React, { useState, useEffect } from 'react'
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, RefreshControl,
} from 'react-native'
import { blockchainAPI } from '../services/api'
import { getSocket } from '../services/socket'
import { colors, typography, spacing, radius } from '../theme'

export function ExplorerScreen() {
  const [blocks, setBlocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [verifyInfo, setVerifyInfo] = useState(null)

  const load = async () => {
    try {
      const res = await blockchainAPI.getBlocks()
      setBlocks(Array.isArray(res.data) ? [...res.data].reverse() : [])
    } catch {}
  }

  const verify = async () => {
    try {
      const res = await blockchainAPI.verifyChain()
      setVerifyInfo(res.data)
    } catch {}
  }

  useEffect(() => {
    load().finally(() => setLoading(false))
    const socket = getSocket()
    socket.on('new_block', () => load())
    return () => socket.off('new_block')
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

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.title}>Blockchain Explorer</Text>
        <TouchableOpacity style={styles.verifyBtn} onPress={verify}>
          <Text style={styles.verifyText}>Verify</Text>
        </TouchableOpacity>
      </View>

      {verifyInfo && (
        <View style={[styles.badge, { backgroundColor: verifyInfo.valid ? colors.success + '22' : colors.error + '22' }]}>
          <Text style={{ color: verifyInfo.valid ? colors.success : colors.error, fontWeight: '700' }}>
            {verifyInfo.valid ? '✅ Blockchain Valid' : '❌ Blockchain Invalid'}
          </Text>
        </View>
      )}

      <FlatList
        data={blocks}
        keyExtractor={(b) => String(b.index)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
        renderItem={({ item }) => (
          <View style={styles.blockCard}>
            <View style={styles.blockHeader}>
              <Text style={styles.blockIndex}>Block #{item.index}</Text>
              <Text style={styles.blockTxCount}>{item.transactions_count} txs</Text>
            </View>
            <Text style={styles.blockHash} numberOfLines={1}>🔗 {item.hash}</Text>
            <Text style={styles.blockMeta}>
              ⛏️ {item.miner ? item.miner.substring(0, 16) + '...' : 'N/A'} •{' '}
              {new Date(Number(item.timestamp) * 1000).toLocaleTimeString()}
            </Text>
            {item.transactions && item.transactions.slice(0, 3).map((tx, i) => (
              <View key={i} style={styles.txRow}>
                <Text style={tx.encrypted ? styles.txEncrypted : styles.txNormal}>
                  {tx.encrypted ? '🔒 Private TX' : `${tx.sender?.substring(0, 6)}... → ${tx.amount} PQC`}
                </Text>
              </View>
            ))}
            {(item.transactions_count || 0) > 3 && (
              <Text style={styles.moreText}>+{item.transactions_count - 3} more...</Text>
            )}
          </View>
        )}
        ListEmptyComponent={<Text style={styles.emptyText}>No blocks yet</Text>}
        contentContainerStyle={{ padding: spacing.md, paddingBottom: 40 }}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: spacing.lg, paddingBottom: 0 },
  title: { ...typography.h2, color: colors.textPrimary },
  verifyBtn: { backgroundColor: colors.accent + '22', borderRadius: radius.sm, paddingHorizontal: 12, paddingVertical: 6, borderWidth: 1, borderColor: colors.accent },
  verifyText: { color: colors.accent, fontWeight: '700', fontSize: 13 },
  badge: { marginHorizontal: spacing.md, marginTop: spacing.sm, borderRadius: radius.sm, padding: spacing.sm, alignItems: 'center' },
  blockCard: { backgroundColor: colors.surface, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.border },
  blockHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  blockIndex: { ...typography.h3, color: colors.accent },
  blockTxCount: { ...typography.caption, color: colors.textMuted, backgroundColor: colors.border, paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  blockHash: { ...typography.mono, color: colors.textMuted, marginBottom: 4 },
  blockMeta: { ...typography.caption, color: colors.textMuted, marginBottom: spacing.sm },
  txRow: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 4, marginTop: 4 },
  txNormal: { ...typography.caption, color: colors.textSecondary },
  txEncrypted: { ...typography.caption, color: colors.encrypted },
  moreText: { ...typography.caption, color: colors.textMuted, marginTop: 4 },
  emptyText: { color: colors.textMuted, textAlign: 'center', marginTop: 40 },
})

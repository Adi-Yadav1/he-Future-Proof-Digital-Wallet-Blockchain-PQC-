import React, { useState } from 'react'
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native'
import { blockchainAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { colors, typography, spacing, radius } from '../theme'

export function PrivateTransactionScreen({ navigation }) {
  const { user } = useAuth()
  const [receiverWallet, setReceiverWallet] = useState('')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!receiverWallet.trim() || !amount.trim()) {
      Alert.alert('Missing Fields', 'Receiver wallet and amount are required.')
      return
    }
    const parsedAmount = parseFloat(amount)
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      Alert.alert('Invalid Amount', 'Enter a positive number.')
      return
    }
    setLoading(true)
    try {
      await blockchainAPI.sendPrivateTransaction(
        user.wallet_address, receiverWallet.trim(), parsedAmount
      )
      Alert.alert('🔒 Private Transaction Sent', 'Amount and receiver are encrypted on-chain.', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ])
    } catch (err) {
      Alert.alert('Failed', err?.response?.data?.error || 'Could not send private transaction')
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: colors.bg }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>🔒 Private Transaction</Text>

        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>How it works</Text>
          <Text style={styles.infoText}>
            The receiver address and amount are encrypted using ML-KEM (Kyber512) + AES-256-GCM before being written to the blockchain. Only the receiver can decrypt the payload using their private key.
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>From (Your Wallet)</Text>
          <Text style={styles.addressText} numberOfLines={1}>{user?.wallet_address}</Text>

          <Text style={styles.label}>Receiver Wallet Address</Text>
          <TextInput
            style={styles.input}
            value={receiverWallet}
            onChangeText={setReceiverWallet}
            placeholder="Enter receiver's wallet address"
            placeholderTextColor={colors.textMuted}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <Text style={styles.label}>Amount (PQC)</Text>
          <TextInput
            style={styles.input}
            value={amount}
            onChangeText={setAmount}
            placeholder="0.00"
            placeholderTextColor={colors.textMuted}
            keyboardType="decimal-pad"
          />

          <TouchableOpacity
            style={[styles.sendBtn, loading && styles.btnDisabled]}
            onPress={handleSend}
            disabled={loading}
            activeOpacity={0.85}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.sendBtnText}>Send Private Transaction</Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg, paddingBottom: 40 },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.md },
  infoBox: {
    backgroundColor: colors.encrypted + '22',
    borderRadius: radius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.encrypted + '55',
    marginBottom: spacing.md,
  },
  infoTitle: { ...typography.h3, color: colors.encrypted, marginBottom: spacing.sm },
  infoText: { ...typography.body, color: colors.textSecondary },
  card: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.lg, borderWidth: 1, borderColor: colors.border },
  label: { ...typography.label, color: colors.textMuted, marginBottom: 4, marginTop: spacing.sm },
  addressText: { ...typography.mono, color: colors.textSecondary, marginBottom: spacing.sm },
  input: { backgroundColor: colors.inputBg, borderWidth: 1, borderColor: colors.border, borderRadius: 10, padding: 12, color: colors.textPrimary, fontSize: 15, marginBottom: spacing.sm },
  sendBtn: { backgroundColor: colors.encrypted, borderRadius: 10, padding: 14, alignItems: 'center', marginTop: spacing.md },
  btnDisabled: { opacity: 0.6 },
  sendBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
})

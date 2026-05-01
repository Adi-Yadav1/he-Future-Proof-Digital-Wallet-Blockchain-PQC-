import React, { useState } from 'react'
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native'
import QRCode from 'react-native-qrcode-svg'
import { BarCodeScanner } from 'expo-barcode-scanner'
import { blockchainAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { colors, typography, spacing, radius } from '../theme'

export function SendTransactionScreen({ navigation }) {
  const { user } = useAuth()
  const [receiver, setReceiver] = useState('')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [showScanner, setShowScanner] = useState(false)
  const [showMyQR, setShowMyQR] = useState(false)
  const [hasPermission, setHasPermission] = useState(null)

  const openScanner = async () => {
    const { status } = await BarCodeScanner.requestPermissionsAsync()
    setHasPermission(status === 'granted')
    if (status === 'granted') setShowScanner(true)
    else Alert.alert('Permission Required', 'Camera access is needed to scan QR codes.')
  }

  const handleScan = ({ data }) => {
    setShowScanner(false)
    setReceiver(data)
  }

  const handleSend = async () => {
    if (!receiver.trim() || !amount.trim()) {
      Alert.alert('Missing Fields', 'Receiver address and amount are required.')
      return
    }
    const parsedAmount = parseFloat(amount)
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      Alert.alert('Invalid Amount', 'Enter a positive number.')
      return
    }
    setLoading(true)
    try {
      const res = await blockchainAPI.sendTransaction(
        user.wallet_address, receiver.trim(), parsedAmount, user.id
      )
      Alert.alert('Success', `Transaction submitted!\nNew balance: ${res.data.new_balance} PQC`, [
        { text: 'OK', onPress: () => navigation.goBack() }
      ])
    } catch (err) {
      Alert.alert('Transaction Failed', err?.response?.data?.error || 'Could not send transaction')
    } finally {
      setLoading(false)
    }
  }

  if (showScanner) {
    return (
      <View style={styles.scannerScreen}>
        <BarCodeScanner
          onBarCodeScanned={handleScan}
          style={StyleSheet.absoluteFillObject}
        />
        <View style={styles.scannerOverlay}>
          <Text style={styles.scannerLabel}>Scan receiver's QR code</Text>
          <TouchableOpacity style={styles.cancelBtn} onPress={() => setShowScanner(false)}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    )
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: colors.bg }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Send PQC</Text>

        {/* My QR Code */}
        <TouchableOpacity style={styles.qrToggle} onPress={() => setShowMyQR(v => !v)}>
          <Text style={styles.qrToggleText}>{showMyQR ? 'Hide My QR' : '📤 Show My QR Code'}</Text>
        </TouchableOpacity>
        {showMyQR && user?.wallet_address && (
          <View style={styles.qrContainer}>
            <QRCode value={user.wallet_address} size={180} color={colors.bg} backgroundColor="#fff" />
            <Text style={styles.qrCaption}>Share to receive PQC</Text>
          </View>
        )}

        <View style={styles.card}>
          <Text style={styles.label}>From</Text>
          <Text style={styles.addressText} numberOfLines={1}>{user?.wallet_address}</Text>

          <Text style={styles.label}>To (Receiver Address)</Text>
          <View style={styles.receiverRow}>
            <TextInput
              style={[styles.input, { flex: 1 }]}
              value={receiver}
              onChangeText={setReceiver}
              placeholder="Paste or scan receiver address"
              placeholderTextColor={colors.textMuted}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <TouchableOpacity onPress={openScanner} style={styles.scanBtn}>
              <Text style={styles.scanBtnText}>📷</Text>
            </TouchableOpacity>
          </View>

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
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.sendBtnText}>Send Transaction</Text>}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg, paddingBottom: 40 },
  title: { ...typography.h1, color: colors.textPrimary, marginBottom: spacing.md },
  qrToggle: { alignSelf: 'flex-start', marginBottom: spacing.sm },
  qrToggleText: { color: colors.accent, fontWeight: '600' },
  qrContainer: { alignItems: 'center', backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.md, borderWidth: 1, borderColor: colors.border },
  qrCaption: { ...typography.caption, color: colors.textMuted, marginTop: spacing.sm },
  card: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.lg, borderWidth: 1, borderColor: colors.border },
  label: { ...typography.label, color: colors.textMuted, marginBottom: 4, marginTop: spacing.sm },
  addressText: { ...typography.mono, color: colors.textSecondary, marginBottom: spacing.sm },
  receiverRow: { flexDirection: 'row', gap: spacing.sm, alignItems: 'center', marginBottom: spacing.sm },
  input: { backgroundColor: colors.inputBg, borderWidth: 1, borderColor: colors.border, borderRadius: 10, padding: 12, color: colors.textPrimary, fontSize: 15 },
  scanBtn: { backgroundColor: colors.accent, borderRadius: 10, padding: 12, alignItems: 'center', justifyContent: 'center' },
  scanBtnText: { fontSize: 22 },
  sendBtn: { backgroundColor: colors.accent, borderRadius: 10, padding: 14, alignItems: 'center', marginTop: spacing.md },
  btnDisabled: { opacity: 0.6 },
  sendBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  scannerScreen: { flex: 1 },
  scannerOverlay: { position: 'absolute', bottom: 60, left: 0, right: 0, alignItems: 'center' },
  scannerLabel: { color: '#fff', fontSize: 16, fontWeight: '600', marginBottom: spacing.md, backgroundColor: 'rgba(0,0,0,0.5)', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20 },
  cancelBtn: { backgroundColor: colors.error, borderRadius: 10, paddingHorizontal: 24, paddingVertical: 12 },
  cancelText: { color: '#fff', fontWeight: '700' },
})

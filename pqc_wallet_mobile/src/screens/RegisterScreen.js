import React, { useState } from 'react'
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ActivityIndicator, Alert, KeyboardAvoidingView, Platform, ScrollView,
} from 'react-native'
import { authAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { colors, typography, spacing } from '../theme'

export function RegisterScreen({ navigation }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()

  const handleRegister = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('Error', 'Both fields are required')
      return
    }
    if (password.length < 6) {
      Alert.alert('Weak Password', 'Password must be at least 6 characters')
      return
    }
    setLoading(true)
    try {
      const res = await authAPI.register(username.trim(), password)
      const { user_id, wallet_address } = res.data
      await login(
        { id: String(user_id), username: username.trim(), wallet_address: wallet_address || '' },
        String(user_id)
      )
    } catch (err) {
      Alert.alert('Registration Failed', err?.response?.data?.error || 'Could not create account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.logo}>🛡️</Text>
          <Text style={styles.title}>Create Wallet</Text>
          <Text style={styles.subtitle}>Post-Quantum Secure Account</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Register</Text>

          <Text style={styles.label}>Username</Text>
          <TextInput
            style={styles.input}
            value={username}
            onChangeText={setUsername}
            placeholder="Choose a username"
            placeholderTextColor={colors.textMuted}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <Text style={styles.label}>Password</Text>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            placeholder="Choose a password"
            placeholderTextColor={colors.textMuted}
            secureTextEntry
          />

          <View style={styles.infoBox}>
            <Text style={styles.infoText}>
              ✅ A Dilithium keypair (ML-DSA) and Kyber key (ML-KEM) will be generated for your wallet automatically.
            </Text>
          </View>

          <TouchableOpacity
            style={[styles.btn, loading && styles.btnDisabled]}
            onPress={handleRegister}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Create Account</Text>}
          </TouchableOpacity>

          <TouchableOpacity onPress={() => navigation.navigate('Login')} style={styles.linkBtn}>
            <Text style={styles.linkText}>Already have an account? Login</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { flexGrow: 1, justifyContent: 'center', padding: spacing.lg },
  header: { alignItems: 'center', marginBottom: spacing.xl },
  logo: { fontSize: 56 },
  title: { ...typography.h1, color: colors.textPrimary, marginTop: spacing.sm },
  subtitle: { ...typography.caption, color: colors.textMuted, marginTop: 4 },
  card: { backgroundColor: colors.surface, borderRadius: 16, padding: spacing.lg, borderWidth: 1, borderColor: colors.border },
  cardTitle: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.md },
  label: { ...typography.label, color: colors.textMuted, marginBottom: 4 },
  input: {
    backgroundColor: colors.inputBg, borderWidth: 1, borderColor: colors.border,
    borderRadius: 10, padding: 12, color: colors.textPrimary, marginBottom: spacing.md, fontSize: 15,
  },
  infoBox: { backgroundColor: colors.surfaceAlt, borderRadius: 8, padding: spacing.sm, marginBottom: spacing.md },
  infoText: { ...typography.caption, color: colors.textSecondary },
  btn: { backgroundColor: colors.accent, borderRadius: 10, padding: 14, alignItems: 'center', marginTop: spacing.sm },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  linkBtn: { marginTop: spacing.md, alignItems: 'center' },
  linkText: { color: colors.accent, fontSize: 14 },
})

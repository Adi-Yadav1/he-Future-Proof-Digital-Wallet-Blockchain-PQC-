import React from 'react'
import { NavigationContainer } from '@react-navigation/native'
import { createStackNavigator } from '@react-navigation/stack'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { Text } from 'react-native'
import { useAuth } from '../context/AuthContext'

import { LoginScreen } from '../screens/LoginScreen'
import { RegisterScreen } from '../screens/RegisterScreen'
import { DashboardScreen } from '../screens/DashboardScreen'
import { SendTransactionScreen } from '../screens/SendTransactionScreen'
import { PrivateTransactionScreen } from '../screens/PrivateTransactionScreen'
import { ExplorerScreen } from '../screens/ExplorerScreen'
import { NetworkScreen } from '../screens/NetworkScreen'
import { colors } from '../theme'

const Stack = createStackNavigator()
const Tab = createBottomTabNavigator()

const headerStyle = {
  headerStyle: { backgroundColor: colors.surface, borderBottomColor: colors.border, borderBottomWidth: 1 },
  headerTintColor: colors.textPrimary,
  headerTitleStyle: { fontWeight: '700' },
}

function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ ...headerStyle, headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  )
}

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        ...headerStyle,
        tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border },
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarIcon: ({ color, size }) => {
          const icons = {
            Dashboard: '🏠',
            Explorer: '🔍',
            Network: '🌐',
          }
          return <Text style={{ fontSize: size - 4 }}>{icons[route.name] || '•'}</Text>
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'Dashboard' }} />
      <Tab.Screen name="Explorer" component={ExplorerScreen} options={{ title: 'Explorer' }} />
      <Tab.Screen name="Network" component={NetworkScreen} options={{ title: 'Network' }} />
    </Tab.Navigator>
  )
}

function AppStack() {
  return (
    <Stack.Navigator screenOptions={headerStyle}>
      <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
      <Stack.Screen name="SendTransaction" component={SendTransactionScreen} options={{ title: 'Send PQC' }} />
      <Stack.Screen name="PrivateTransaction" component={PrivateTransactionScreen} options={{ title: 'Private Transaction' }} />
    </Stack.Navigator>
  )
}

export function AppNavigator() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return null  // Splash handled by Expo

  return (
    <NavigationContainer>
      {isAuthenticated ? <AppStack /> : <AuthStack />}
    </NavigationContainer>
  )
}

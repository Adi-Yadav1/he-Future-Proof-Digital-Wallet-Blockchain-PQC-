/**
 * Phase 9 — Mobile socket service
 * Uses socket.io-client to connect to the same Flask-SocketIO backend.
 * Change WS_URL to match your backend LAN IP when testing on a device.
 */
import { io } from 'socket.io-client'
import { API_BASE_URL } from './api'

let _socket = null

export function getSocket() {
  if (!_socket) {
    _socket = io(API_BASE_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
    })
  }
  return _socket
}

export function disconnectSocket() {
  if (_socket) {
    _socket.disconnect()
    _socket = null
  }
}

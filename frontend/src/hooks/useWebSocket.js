import { useRef, useState, useCallback, useEffect } from 'react'

export function useWebSocket(roomId, participantId, participantToken) {
  const wsRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState(null)
  const handlersRef = useRef({})
  const reconnectTimerRef = useRef(null)
  const shouldReconnectRef = useRef(false)

  const connect = useCallback(() => {
    if (!roomId || !participantId) return
    shouldReconnectRef.current = true
    setConnectionError(null)

    // A socket that is still opening, open, or closing must finish its
    // lifecycle before another one is created.
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) return
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws/${roomId}/${participantId}`

    console.log('Connecting to WebSocket:', url)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (wsRef.current !== ws) return
      ws.send(JSON.stringify({ type: 'auth', token: participantToken }))
      setIsConnected(true)
      setConnectionError(null)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      if (wsRef.current !== ws) return
      try {
        const data = JSON.parse(event.data)
        // Call type-specific handler
        if (handlersRef.current[data.type]) {
          handlersRef.current[data.type](data)
        }
        // Call wildcard handler
        if (handlersRef.current['*']) {
          handlersRef.current['*'](data)
        }
      } catch (err) {
        console.error('Failed to parse WS message:', err)
      }
    }

    ws.onclose = (event) => {
      if (wsRef.current !== ws) return
      wsRef.current = null
      setIsConnected(false)
      if (event.code === 4401 || event.code === 4404) {
        shouldReconnectRef.current = false
        setConnectionError(event.code === 4401
          ? 'This room session has expired. Return to the home screen and create or rejoin the room.'
          : 'This room has ended or expired. Return to the home screen to start another conversation.')
        return
      }
      if (!shouldReconnectRef.current) return
      console.log('WebSocket disconnected, will reconnect in 3s...')
      reconnectTimerRef.current = setTimeout(() => {
        reconnectTimerRef.current = null
        if (shouldReconnectRef.current && !wsRef.current) connect()
      }, 3000)
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
    }
  }, [roomId, participantId, participantToken])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    if (wsRef.current) {
      const ws = wsRef.current
      wsRef.current = null
      ws.close()
    }
    setIsConnected(false)
  }, [])

  const send = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected, cannot send')
    }
  }, [])

  const on = useCallback((eventType, handler) => {
    handlersRef.current[eventType] = handler
  }, [])

  const off = useCallback((eventType) => {
    delete handlersRef.current[eventType]
  }, [])

  useEffect(() => {
    return () => disconnect()
  }, [disconnect])

  return { connect, disconnect, send, on, off, isConnected, connectionError }
}

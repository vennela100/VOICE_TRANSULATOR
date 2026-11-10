import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAudioRecorder } from '../hooks/useAudioRecorder'
import { WS_EVENTS, generateMessageId } from '../api/ws'
import PushToTalk from '../components/PushToTalk'
import TranscriptBubble from '../components/TranscriptBubble'
import './Conversation.css'

const LANG_LABELS = {
  hi: 'Hindi',
  en: 'English',
  te: 'Telugu',
  ta: 'Tamil',
  kn: 'Kannada',
  ml: 'Malayalam',
  mr: 'Marathi',
  bn: 'Bengali',
  gu: 'Gujarati',
  pa: 'Punjabi',
  or: 'Odia',
  ur: 'Urdu',
}
const MAX_RECORDING_SECONDS = 28

export default function Conversation() {
  const { roomCode } = useParams()
  const location = useLocation()
  const navigate = useNavigate()

  // Get session info from router state or sessionStorage
  const getSession = () => {
    if (location.state?.roomId) return location.state
    const stored = sessionStorage.getItem('bharatvaani_session')
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed.roomCode === roomCode) return parsed
    }
    return null
  }

  const session = getSession()

  useEffect(() => {
    if (!session) {
      navigate('/', { replace: true })
    }
  }, [session, navigate])

  if (!session) return null

  return <ConversationInner session={session} roomCode={roomCode} />
}

function ConversationInner({ session, roomCode }) {
  const { roomId, participantId, participantToken, participantName, language } = session
  const navigate = useNavigate()

  const [messages, setMessages] = useState({})
  const [messageOrder, setMessageOrder] = useState([])
  const [participants, setParticipants] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState(null)
  const [clarification, setClarification] = useState(null)
  const [pendingAudio, setPendingAudio] = useState(null)
  const [outcome, setOutcome] = useState(null)
  const [showOutcome, setShowOutcome] = useState(false)
  const messagesEndRef = useRef(null)
  const codeCopiedRef = useRef(false)
  const recordingTimerRef = useRef(null)
  const stopInProgressRef = useRef(false)

  const ws = useWebSocket(roomId, participantId, participantToken)
  const recorder = useAudioRecorder()

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messageOrder])

  // Update message state helper
  const updateMessage = useCallback((messageId, updates) => {
    setMessages((prev) => ({
      ...prev,
      [messageId]: { ...(prev[messageId] || {}), id: messageId, ...updates },
    }))
    setMessageOrder((prev) => {
      if (!prev.includes(messageId)) return [...prev, messageId]
      return prev
    })
  }, [])

  // Register WS handlers
  useEffect(() => {
    ws.on(WS_EVENTS.AUDIO_STARTED, (data) => {
      updateMessage(data.message_id, {
        senderId: data.sender_id,
        status: 'processing',
        senderName: data.sender_id === participantId ? participantName : 'Partner',
      })
    })

    ws.on('room.state', (data) => {
      setParticipants(data.participants || [])
      for (const item of data.messages || []) {
        updateMessage(item.message_id, {
          senderId: item.sender_id, senderName: item.sender_id === participantId ? participantName : 'Partner',
          originalText: item.original_text, originalLanguage: item.original_language,
          translatedText: item.translated_text, translatedLanguage: item.translated_language,
          status: item.status, verification: item.verification, confirmed: item.confirmed,
          audioBase64: item.audio_base64, audioFormat: item.audio_format || 'wav',
        })
        if (item.status === 'awaiting_confirmation' && item.sender_id === participantId) {
          setClarification({ messageId: item.message_id,
            prompt: item.verification?.prompt_to_speaker || 'Please confirm the critical detail or re-record.' })
        }
      }
    })

    ws.on(WS_EVENTS.TRANSCRIPT_FINAL, (data) => {
      updateMessage(data.message_id, {
        originalText: data.text,
        originalLanguage: data.language,
        senderId: data.sender_id,
        senderName: data.sender_id === participantId ? participantName : 'Partner',
        status: 'translating',
      })
    })

    ws.on(WS_EVENTS.TRANSLATION_COMPLETED, (data) => {
      updateMessage(data.message_id, {
        translatedText: data.text,
        translatedLanguage: data.target_language,
        verification: data.verification,
        status: 'translated',
      })
    })

    ws.on(WS_EVENTS.AUDIO_READY, (data) => {
      updateMessage(data.message_id, {
        audioBase64: data.audio_base64,
        audioFormat: data.audio_format,
      })
    })

    ws.on(WS_EVENTS.MESSAGE_DELIVERED, (data) => {
      updateMessage(data.message_id, { status: 'delivered', audioError: data.audio_error })
      if (data.sender_id === participantId) {
        setIsProcessing(false)
      }
    })

    ws.on(WS_EVENTS.VERIFICATION_REQUIRED, (data) => {
      setClarification({ messageId: data.message_id, prompt: data.prompt_text })
      updateMessage(data.message_id, { status: 'awaiting_confirmation', verification: data.verification })
      setIsProcessing(false)
    })

    ws.on('verification.pending', (data) => {
      updateMessage(data.message_id, { status: 'awaiting_confirmation', waitingForSpeaker: true })
    })

    ws.on(WS_EVENTS.VERIFICATION_CONFIRMED, (data) => {
      setClarification(null)
      updateMessage(data.message_id, { confirmed: true })
    })

    ws.on(WS_EVENTS.VERIFICATION_REJECTED, (data) => {
      setClarification(null)
      updateMessage(data.message_id, { status: 'rejected' })
    })

    ws.on(WS_EVENTS.MESSAGE_FAILED, (data) => {
      updateMessage(data.message_id, { status: 'error', error: data.error })
      setError(data.error)
      setIsProcessing(false)
    })

    ws.on(WS_EVENTS.ERROR, (data) => {
      if (data.message_id) {
        updateMessage(data.message_id, { status: 'error', error: data.error })
      }
      setError(data.error)
      setIsProcessing(false)
      setTimeout(() => setError(null), 5000)
    })

    ws.on(WS_EVENTS.PARTICIPANT_JOINED, (data) => {
      setParticipants((prev) => [
        ...prev.filter((p) => p.id !== data.participant_id),
        { id: data.participant_id, name: data.name, language: data.language },
      ])
    })

    ws.on(WS_EVENTS.PARTICIPANT_LEFT, (data) => {
      setParticipants((prev) => prev.filter((p) => p.id !== data.participant_id))
    })

    ws.on('session.deleted', () => {
      sessionStorage.removeItem('bharatvaani_session')
      ws.disconnect()
      navigate('/')
    })

    // Connect
    ws.connect()

    return () => ws.disconnect()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Handle push-to-talk
  const handleStartRecording = useCallback(async () => {
    setError(null)
    await recorder.startRecording()
  }, [recorder.startRecording])

  const handleStopRecording = useCallback(async () => {
    if (stopInProgressRef.current) return
    stopInProgressRef.current = true
    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    try {
      const result = await recorder.stopRecording()
      if (!result || !result.base64) {
        setError('No audio recorded. Please try again.')
        return
      }

      setIsProcessing(true)
      const messageId = generateMessageId()
      setPendingAudio({ messageId, base64: result.base64 })

      ws.send({
        type: WS_EVENTS.AUDIO_DATA,
        message_id: messageId,
        audio_base64: result.base64,
      })
    } finally {
      stopInProgressRef.current = false
    }
  }, [recorder.stopRecording, ws.send])

  useEffect(() => {
    if (!recorder.isRecording) return undefined
    recordingTimerRef.current = window.setTimeout(() => {
      recordingTimerRef.current = null
      handleStopRecording()
    }, MAX_RECORDING_SECONDS * 1000)
    return () => {
      if (recordingTimerRef.current) {
        clearTimeout(recordingTimerRef.current)
        recordingTimerRef.current = null
      }
    }
  }, [recorder.isRecording, handleStopRecording])

  const respondToVerification = (confirmed) => {
    if (!clarification) return
    ws.send({ type: confirmed ? WS_EVENTS.VERIFICATION_CONFIRMED : WS_EVENTS.VERIFICATION_REJECTED,
      message_id: clarification.messageId })
    if (!confirmed) setClarification(null)
    else setIsProcessing(true)
  }

  const retryMessage = () => {
    if (!pendingAudio) return
    setError(null); setIsProcessing(true)
    ws.send({ type: WS_EVENTS.AUDIO_DATA, message_id: pendingAudio.messageId,
      audio_base64: pendingAudio.base64 })
  }

  const loadOutcome = async () => {
    try {
      const response = await fetch(`/api/rooms/${roomCode}/outcome`, {
        headers: { Authorization: `Bearer ${participantToken}` },
      })
      if (!response.ok) throw new Error('Could not load outcome card')
      setOutcome(await response.json()); setShowOutcome(true)
    } catch (err) { setError(err.message) }
  }

  const saveOutcome = async () => {
    const response = await fetch(`/api/rooms/${roomCode}/outcome`, { method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${participantToken}` },
      body: JSON.stringify(outcome) })
    if (response.ok) setShowOutcome(false)
    else setError('Could not save outcome card')
  }

  const copyRoomCode = () => {
    navigator.clipboard?.writeText(roomCode)
    codeCopiedRef.current = true
    setError(null)
    // Brief visual feedback
    const btn = document.querySelector('.copy-code-btn')
    if (btn) {
      btn.textContent = 'Copied!'
      setTimeout(() => { btn.textContent = 'Copy' }, 1500)
    }
  }

  const handleLeave = async () => {
    if (!window.confirm('End the session and permanently delete its messages and outcome card?')) return
    await fetch(`/api/rooms/${roomCode}`, {
      method: 'DELETE', headers: { Authorization: `Bearer ${participantToken}` },
    })
    ws.disconnect()
    sessionStorage.removeItem('bharatvaani_session')
    navigate('/')
  }

  const otherParticipant = participants.find((p) => p.id !== participantId)
  const otherLang = otherParticipant ? otherParticipant.language : (language === 'hi' ? 'en' : 'hi')

  return (
    <div className="conversation-page">
      {/* Header */}
      <header className="conv-header">
        <div className="header-left">
          <h2 className="header-title">BharatVaani</h2>
          <div className="room-info">
            <span className="room-code">Room: {roomCode}</span>
            <button className="copy-code-btn" onClick={copyRoomCode}>Copy</button>
          </div>
        </div>
        <div className="header-right">
          <div className="lang-pair">
            <span className="lang-tag own-lang">{LANG_LABELS[language]}</span>
            <span className="lang-arrow">↔</span>
            <span className="lang-tag other-lang">{LANG_LABELS[otherLang]}</span>
          </div>
          <div className={`connection-status ${ws.isConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {ws.isConnected ? 'Connected' : ws.connectionError ? 'Session unavailable' : 'Reconnecting...'}
          </div>
        </div>
      </header>

      {/* Partner info bar */}
      {participants.length > 0 && (
        <div className="partner-bar">
          Partner: {participants.map((p) => `${p.name} (${LANG_LABELS[p.language]})`).join(', ')}
        </div>
      )}

      {/* Error banner */}
      {(ws.connectionError || error || recorder.error) && (
        <div className="error-banner conv-error">
          {ws.connectionError || error || recorder.error}
          {pendingAudio && <button className="retry-btn" onClick={retryMessage}>Retry</button>}
        </div>
      )}

      {clarification && <div className="clarification-banner" role="alert">
        <strong>Check this detail before it is sent</strong><p>{clarification.prompt}</p>
        <button onClick={() => respondToVerification(true)}>Confirm and deliver</button>
        <button className="secondary" onClick={() => respondToVerification(false)}>No, re-record</button>
      </div>}

      {/* Messages area */}
      <div className="messages-area">
        {messageOrder.length === 0 && (
          <div className="empty-state">
            <p className="empty-icon">🎤</p>
            <p>No messages yet.</p>
            <p>Share room code <strong>{roomCode}</strong> with your partner, then tap the mic to start talking!</p>
          </div>
        )}

        {messageOrder.map((msgId) => {
          const msg = messages[msgId]
          if (!msg) return null
          return (
            <TranscriptBubble
              key={msgId}
              message={msg}
              isOwn={msg.senderId === participantId}
            />
          )
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Push to talk */}
      <div className="ptt-container">
        <PushToTalk
          isRecording={recorder.isRecording}
          onStart={handleStartRecording}
          onStop={handleStopRecording}
          disabled={isProcessing || !ws.isConnected}
        />
      </div>

      {/* Leave button */}
      <button className="leave-btn" onClick={handleLeave}>
        End session and delete
      </button>
      <button className="outcome-btn" onClick={loadOutcome}>Conversation outcome card</button>
      {showOutcome && outcome && <div className="outcome-panel">
      <h3>Conversation outcome</h3>
      <p>{outcome.summary_status}</p>
        {(outcome.items || []).map((item, index) => <label className="outcome-row" key={`${item.message_id}-${index}`}>
          <span>{item.kind} · {item.status}</span>
          <input value={item.value || ''} onChange={(event) => setOutcome((old) => ({...old,
            items: old.items.map((entry, i) => i === index ? {...entry, value: event.target.value} : entry)}))} />
        </label>)}
        {['decisions', 'next_steps'].map((key) => <section key={key}>
          <h4>{key === 'decisions' ? 'Decisions' : 'Next steps'}</h4>
          {(outcome[key] || []).map((entry, index) => <label className="outcome-row" key={`${key}-${index}`}>
            <span>{entry.ai_generated ? 'AI-generated · review' : 'Editable'}</span>
            <input value={entry.text || ''} onChange={(event) => setOutcome((old) => ({...old,
              [key]: old[key].map((item, i) => i === index ? {...item, text: event.target.value} : item)}))} />
          </label>)}
        </section>)}
        <button onClick={saveOutcome}>Save edited card</button>
        <button className="secondary" onClick={() => setShowOutcome(false)}>Close</button>
      </div>}
    </div>
  )
}

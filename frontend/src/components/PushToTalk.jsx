import React, { useEffect, useState } from 'react'
import './PushToTalk.css'

export default function PushToTalk({ isRecording, onStart, onStop, disabled }) {
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    let interval = null
    if (isRecording) {
      setSeconds(0)
      interval = setInterval(() => {
        setSeconds((s) => s + 1)
      }, 1000)
    } else {
      setSeconds(0)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isRecording])

  const handleClick = () => {
    if (disabled) return
    if (isRecording) {
      onStop()
    } else {
      onStart()
    }
  }

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="ptt-wrapper">
      <div className="ptt-action-container">
        {/* Animated background rings when recording */}
        {isRecording && (
          <>
            <div className="recording-wave wave-1" />
            <div className="recording-wave wave-2" />
          </>
        )}

        <button
          type="button"
          className={`ptt-main-btn ${isRecording ? 'is-recording' : ''} ${disabled ? 'is-disabled' : ''}`}
          onClick={handleClick}
          disabled={disabled}
          aria-label={isRecording ? 'Stop recording and translate' : 'Start speaking'}
        >
          <div className="ptt-btn-inner">
            {isRecording ? (
              <div className="ptt-icon-recording">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              </div>
            ) : (
              <div className="ptt-icon-mic">
                <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="23"/>
                  <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
              </div>
            )}
            
            <span className="ptt-btn-label">
              {isRecording ? 'Tap to Send' : 'Tap to Talk'}
            </span>
          </div>
        </button>
      </div>

      {/* Recording status with live waveform simulation */}
      {isRecording ? (
        <div className="recording-status-bar">
          <div className="recording-badge">
            <span className="recording-live-dot" />
            <span className="recording-timer">{formatTime(seconds)} / 00:28</span>
          </div>

          <div className="live-waveform" aria-hidden="true">
            <span className="wave-bar bar-1" />
            <span className="wave-bar bar-2" />
            <span className="wave-bar bar-3" />
            <span className="wave-bar bar-4" />
            <span className="wave-bar bar-5" />
            <span className="wave-bar bar-6" />
            <span className="wave-bar bar-7" />
            <span className="wave-bar bar-8" />
          </div>

          <span className="recording-hint">Listening in your language...</span>
        </div>
      ) : (
        <div className="ptt-idle-hint">
          {disabled ? (
            <span className="processing-hint">
              <span className="inline-spinner" /> Processing speech & meaning verification...
            </span>
          ) : (
            <span>Tap once to speak, tap again when finished</span>
          )}
        </div>
      )}
    </div>
  )
}

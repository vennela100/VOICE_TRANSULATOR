import React from 'react'
import './PushToTalk.css'

export default function PushToTalk({ isRecording, onStart, onStop, disabled }) {
  const handleClick = () => {
    if (isRecording) {
      onStop()
    } else {
      onStart()
    }
  }

  return (
    <div className="push-to-talk">
      <button
        className={`ptt-button ${isRecording ? 'recording' : ''} ${disabled ? 'disabled' : ''}`}
        onClick={handleClick}
        disabled={disabled}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      >
        <span className="ptt-icon">{isRecording ? '⏹' : '🎤'}</span>
        <span className="ptt-label">{isRecording ? 'Tap to Send' : 'Tap to Talk'}</span>
      </button>
      {isRecording && (
        <div className="recording-indicator">
          <span className="pulse-dot"></span>
          Recording... (max 28 seconds)
        </div>
      )}
    </div>
  )
}

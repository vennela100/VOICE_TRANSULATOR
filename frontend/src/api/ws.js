// WebSocket event type constants
export const WS_EVENTS = {
  AUDIO_DATA: 'audio_data',
  AUDIO_STARTED: 'audio.started',
  TRANSCRIPT_FINAL: 'transcript.final',
  TRANSLATION_COMPLETED: 'translation.completed',
  AUDIO_READY: 'audio.ready',
  MESSAGE_DELIVERED: 'message.delivered',
  MESSAGE_FAILED: 'message.failed',
  VERIFICATION_REQUIRED: 'verification.required',
  VERIFICATION_CONFIRMED: 'verification.confirmed',
  VERIFICATION_REJECTED: 'verification.rejected',
  PARTICIPANT_JOINED: 'participant_joined',
  PARTICIPANT_LEFT: 'participant_left',
  ERROR: 'error',
  PING: 'ping',
  PONG: 'pong',
}

export function generateMessageId() {
  return crypto.randomUUID ? crypto.randomUUID() : 
    'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9)
}

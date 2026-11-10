import React from 'react'

export const LANGUAGES = [
  { code: 'hi', label: 'हिन्दी', labelEn: 'Hindi', script: 'Devanagari' },
  { code: 'en', label: 'English', labelEn: 'English', script: 'Latin' },
  { code: 'te', label: 'తెలుగు', labelEn: 'Telugu', script: 'Telugu' },
  { code: 'ta', label: 'தமிழ்', labelEn: 'Tamil', script: 'Tamil' },
  { code: 'kn', label: 'ಕನ್ನಡ', labelEn: 'Kannada', script: 'Kannada' },
  { code: 'ml', label: 'മലയാളം', labelEn: 'Malayalam', script: 'Malayalam' },
  { code: 'mr', label: 'मराठी', labelEn: 'Marathi', script: 'Devanagari' },
  { code: 'bn', label: 'বাংলা', labelEn: 'Bengali', script: 'Bengali' },
  { code: 'gu', label: 'ગુજરાતી', labelEn: 'Gujarati', script: 'Gujarati' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ', labelEn: 'Punjabi', script: 'Gurmukhi' },
  { code: 'or', label: 'ଓଡ଼ିଆ', labelEn: 'Odia', script: 'Odia' },
  { code: 'ur', label: 'اردو', labelEn: 'Urdu', script: 'Perso-Arabic' },
]

export default function LanguageSelector({ value, onChange }) {
  return (
    <div className="language-selector-section">
      <div className="section-label-row">
        <label className="section-label">Select Your Spoken Language</label>
        <span className="section-badge">12 Languages Supported</span>
      </div>
      
      <div className="language-grid" role="radiogroup" aria-label="Select your language">
        {LANGUAGES.map((lang) => {
          const isSelected = value === lang.code
          return (
            <button
              key={lang.code}
              type="button"
              role="radio"
              aria-checked={isSelected}
              className={`lang-card ${isSelected ? 'selected' : ''}`}
              onClick={() => onChange(lang.code)}
            >
              <div className="lang-card-header">
                <span className="lang-code-pill">{lang.code.toUpperCase()}</span>
                {isSelected && (
                  <span className="lang-check-icon" aria-hidden="true">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                )}
              </div>
              <span className="lang-card-native">{lang.label}</span>
              <span className="lang-card-en">{lang.labelEn}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

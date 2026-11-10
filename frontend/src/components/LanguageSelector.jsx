import React from 'react'

export const LANGUAGES = [
  { code: 'hi', label: 'हिन्दी', labelEn: 'Hindi' },
  { code: 'en', label: 'English', labelEn: 'English' },
  { code: 'te', label: 'తెలుగు', labelEn: 'Telugu' },
  { code: 'ta', label: 'தமிழ்', labelEn: 'Tamil' },
  { code: 'kn', label: 'ಕನ್ನಡ', labelEn: 'Kannada' },
  { code: 'ml', label: 'മലയാളം', labelEn: 'Malayalam' },
  { code: 'mr', label: 'मराठी', labelEn: 'Marathi' },
  { code: 'bn', label: 'বাংলা', labelEn: 'Bengali' },
  { code: 'gu', label: 'ગુજરાતી', labelEn: 'Gujarati' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ', labelEn: 'Punjabi' },
  { code: 'or', label: 'ଓଡ଼ିଆ', labelEn: 'Odia' },
  { code: 'ur', label: 'اردو', labelEn: 'Urdu' },
]

export default function LanguageSelector({ value, onChange }) {
  return (
    <div className="language-selector">
      <label className="language-label">Your Language</label>
      <div className="language-buttons">
        {LANGUAGES.map((lang) => (
          <button
            key={lang.code}
            type="button"
            className={`language-btn ${value === lang.code ? 'active' : ''}`}
            onClick={() => onChange(lang.code)}
          >
            <span className="lang-native">{lang.label}</span>
            <span className="lang-en">{lang.labelEn}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

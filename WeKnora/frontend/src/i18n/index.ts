import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.ts'
import ruRU from './locales/ru-RU.ts'
import enUS from './locales/en-US.ts'

const messages = {
  'zh-CN': zhCN,
  'en-US': enUS,
  'ru-RU': ruRU
}

// Get saved language from localStorage or use English by default
const savedLocale = localStorage.getItem('locale') || 'en-US'
console.log('i18n initialization with language:', savedLocale)

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en-US',
  globalInjection: true,
  messages
})

export default i18n
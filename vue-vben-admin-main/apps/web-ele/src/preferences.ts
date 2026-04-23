import { defineOverridesPreferences } from '@vben/preferences';

export const overridesPreferences = defineOverridesPreferences({
  app: {
    defaultHomePath: '/dashboard/overview',
    name: import.meta.env.VITE_APP_TITLE,
  },
  copyright: {
    enable: false,
    settingShow: false,
  },
  navigation: {
    split: false,
  },
  theme: {
    mode: 'light',
  },
  widget: {
    globalSearch: false,
    languageToggle: false,
    lockScreen: false,
    notification: false,
    timezone: false,
  },
});

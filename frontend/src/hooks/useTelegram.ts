import { useEffect } from 'react';
import type { TelegramWebApp, TelegramUser } from '../types';

const BG_COLOR = '#0a0e1a';

export function useTelegram() {
  const tg: TelegramWebApp | undefined = window.Telegram?.WebApp;

  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      tg.setHeaderColor(BG_COLOR);
      tg.setBackgroundColor(BG_COLOR);
    }
  }, []);

  const user: TelegramUser | undefined = tg?.initDataUnsafe?.user;
  const haptic = tg?.HapticFeedback;

  return { tg, user, haptic };
}

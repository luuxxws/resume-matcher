import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

export function LanguageToggle() {
  const { i18n } = useTranslation();
  const currentLang = i18n.language?.startsWith('ru') ? 'ru' : 'en';

  const toggleLanguage = () => {
    const newLang = currentLang === 'en' ? 'ru' : 'en';
    i18n.changeLanguage(newLang);
  };

  return (
    <button
      onClick={toggleLanguage}
      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-void-700/50 border border-void-600 hover:border-neon-cyan/30 transition-all duration-200"
      title={currentLang === 'en' ? 'Switch to Russian' : 'Переключить на английский'}
    >
      <div className="flex items-center gap-1">
        <span
          className={clsx(
            'text-sm font-medium transition-colors',
            currentLang === 'en' ? 'text-neon-cyan' : 'text-slate-500'
          )}
        >
          EN
        </span>
        <span className="text-slate-600">/</span>
        <span
          className={clsx(
            'text-sm font-medium transition-colors',
            currentLang === 'ru' ? 'text-neon-cyan' : 'text-slate-500'
          )}
        >
          RU
        </span>
      </div>
      <div
        className={clsx(
          'w-8 h-4 rounded-full relative transition-colors',
          currentLang === 'ru' ? 'bg-neon-cyan/30' : 'bg-void-600'
        )}
      >
        <div
          className={clsx(
            'absolute top-0.5 w-3 h-3 rounded-full bg-neon-cyan transition-all duration-200',
            currentLang === 'ru' ? 'left-4' : 'left-0.5'
          )}
        />
      </div>
    </button>
  );
}

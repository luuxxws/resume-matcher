import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Search, 
  Sparkles, 
  Zap, 
  Loader2,
  Upload,
  FileText,
  X
} from 'lucide-react';
import { api, MatchResponse, MatchRequest } from '../api/client';
import { MatchResults } from './MatchResults';
import clsx from 'clsx';

export function Match() {
  const { t, i18n } = useTranslation();
  const [vacancyText, setVacancyText] = useState('');
  const [topN, setTopN] = useState(10);
  const [useLLM, setUseLLM] = useState(false);
  const [minScore, setMinScore] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<MatchResponse | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  const currentLang = i18n.language?.startsWith('ru') ? 'ru' : 'en';

  // Keyboard shortcut: Ctrl+Enter to submit
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!loading && (vacancyText.trim() || uploadedFile)) {
          formRef.current?.requestSubmit();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [loading, vacancyText, uploadedFile]);

  // Simulate loading progress for better UX
  useEffect(() => {
    if (loading) {
      setLoadingProgress(0);
      const interval = setInterval(() => {
        setLoadingProgress((prev) => {
          // Slow down as we approach 90%
          if (prev >= 90) return prev;
          const increment = prev < 50 ? 8 : prev < 80 ? 3 : 1;
          return Math.min(prev + increment, 90);
        });
      }, 300);
      return () => clearInterval(interval);
    } else {
      // Complete the progress bar when done
      if (loadingProgress > 0) {
        setLoadingProgress(100);
        setTimeout(() => setLoadingProgress(0), 300);
      }
    }
  }, [loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!vacancyText.trim() && !uploadedFile) {
      setError(t('match.errorEmpty'));
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      let response: MatchResponse;
      
      if (uploadedFile) {
        response = await api.matchFile(uploadedFile, { top_n: topN, use_llm: useLLM });
      } else {
        const request: MatchRequest = {
          vacancy_text: vacancyText,
          top_n: topN,
          use_llm: useLLM,
          min_score: minScore,
          lang: currentLang, // Pass language for LLM responses
        };
        response = await api.match(request);
      }
      
      setResults(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to match resumes';
      // Provide more helpful error messages
      if (message.includes('rate limit') || message.includes('429')) {
        setError(currentLang === 'ru' 
          ? 'Превышен лимит запросов Groq API. Попробуйте "Быстрый" режим или подождите несколько минут.'
          : 'Groq API rate limit exceeded. Try "Fast" mode or wait a few minutes.');
      } else if (message.includes('Unknown error')) {
        setError(currentLang === 'ru'
          ? 'Ошибка API. Возможно, превышен лимит запросов. Попробуйте "Быстрый" режим.'
          : 'API error. Rate limit may be exceeded. Try "Fast" mode.');
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setVacancyText('');
    }
  };

  const clearFile = () => {
    setUploadedFile(null);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-2xl font-bold text-white">{t('match.title')}</h1>
        <p className="text-slate-400 mt-1">
          {t('match.subtitle')}
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-void-800/50 border border-void-600/50 rounded-2xl p-6 animate-slide-up">
        <form ref={formRef} onSubmit={handleSubmit} className="space-y-6">
          {/* Vacancy Input */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-300">
                {t('match.vacancyLabel')}
              </label>
              <label className="cursor-pointer">
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <span className="flex items-center gap-2 text-xs text-neon-cyan hover:text-neon-cyan/80 transition-colors">
                  <Upload className="w-4 h-4" />
                  {t('match.uploadFile')}
                </span>
              </label>
            </div>

            {uploadedFile ? (
              <div className="flex items-center gap-3 p-4 bg-neon-cyan/10 border border-neon-cyan/30 rounded-lg">
                <FileText className="w-6 h-6 text-neon-cyan" />
                <div className="flex-1">
                  <p className="text-white font-medium">{uploadedFile.name}</p>
                  <p className="text-slate-400 text-sm">
                    {(uploadedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={clearFile}
                  className="p-2 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <textarea
                value={vacancyText}
                onChange={(e) => setVacancyText(e.target.value)}
                placeholder={t('match.placeholder')}
                rows={10}
                className="textarea-field font-mono text-sm"
              />
            )}
          </div>

          {/* Options */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Top N */}
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                {t('match.resultsToShow')}
              </label>
              <select
                value={topN}
                onChange={(e) => setTopN(Number(e.target.value))}
                className="input-field"
              >
                <option value={5}>Top 5</option>
                <option value={10}>Top 10</option>
                <option value={20}>Top 20</option>
                <option value={50}>Top 50</option>
              </select>
            </div>

            {/* Min Score */}
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                {t('match.minScore')}: {minScore}%
              </label>
              <input
                type="range"
                min={0}
                max={80}
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-full accent-neon-cyan"
              />
            </div>

            {/* LLM Toggle */}
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                {t('match.matchingMode')}
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setUseLLM(false)}
                  className={clsx(
                    'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all',
                    !useLLM
                      ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30'
                      : 'bg-void-700/50 text-slate-400 border border-void-600 hover:border-void-500'
                  )}
                >
                  <Zap className="w-4 h-4 inline mr-1" />
                  {t('match.fast')}
                </button>
                <button
                  type="button"
                  onClick={() => setUseLLM(true)}
                  className={clsx(
                    'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all',
                    useLLM
                      ? 'bg-neon-purple/10 text-neon-purple border border-neon-purple/30'
                      : 'bg-void-700/50 text-slate-400 border border-void-600 hover:border-void-500'
                  )}
                >
                  <Sparkles className="w-4 h-4 inline mr-1" />
                  {t('match.ai')}
                </button>
              </div>
            </div>
          </div>

          {/* Mode Info */}
          <div className={clsx(
            'p-4 rounded-lg border text-sm',
            useLLM 
              ? 'bg-neon-purple/5 border-neon-purple/20 text-slate-400'
              : 'bg-neon-cyan/5 border-neon-cyan/20 text-slate-400'
          )}>
            {useLLM ? (
              <>
                <strong className="text-neon-purple">{t('match.ai')}:</strong> {t('match.aiModeDescription')}
              </>
            ) : (
              <>
                <strong className="text-neon-cyan">{t('match.fast')}:</strong> {t('match.fastModeDescription')}
              </>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 bg-neon-pink/10 border border-neon-pink/30 rounded-lg text-neon-pink">
              {error}
            </div>
          )}

          {/* Submit */}
          <div className="relative">
            {/* Progress bar */}
            {loading && loadingProgress > 0 && (
              <div className="absolute -top-2 left-0 right-0 h-1 bg-void-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-neon-cyan to-neon-purple transition-all duration-300 ease-out"
                  style={{ width: `${loadingProgress}%` }}
                />
              </div>
            )}
            
            <button
              type="submit"
              disabled={loading || (!vacancyText.trim() && !uploadedFile)}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {useLLM ? t('match.aiAnalyzing') : t('match.searching')}
                  {useLLM && loadingProgress > 0 && (
                    <span className="text-void-900/70 text-sm ml-2">
                      {loadingProgress < 90 ? `${loadingProgress}%` : '...'}
                    </span>
                  )}
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  {t('match.findMatching')}
                  <kbd className="hidden sm:inline-flex ml-2 px-1.5 py-0.5 text-xs bg-void-900/30 rounded text-void-900/70">
                    ⌘↵
                  </kbd>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Results */}
      {results && <MatchResults results={results} />}
    </div>
  );
}

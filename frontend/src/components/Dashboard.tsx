import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  FileText, 
  Brain, 
  Database, 
  Search,
  ArrowRight,
  TrendingUp,
  Zap,
  Target
} from 'lucide-react';
import { api, StatsResponse } from '../api/client';
import clsx from 'clsx';

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle: string;
  icon: React.ElementType;
  color: 'cyan' | 'pink' | 'purple' | 'yellow';
  delay: number;
}

function StatCard({ title, value, subtitle, icon: Icon, color, delay }: StatCardProps) {
  const colorClasses = {
    cyan: 'from-neon-cyan/20 to-neon-cyan/5 border-neon-cyan/30 text-neon-cyan',
    pink: 'from-neon-pink/20 to-neon-pink/5 border-neon-pink/30 text-neon-pink',
    purple: 'from-neon-purple/20 to-neon-purple/5 border-neon-purple/30 text-neon-purple',
    yellow: 'from-neon-yellow/20 to-neon-yellow/5 border-neon-yellow/30 text-neon-yellow',
  };

  return (
    <div 
      className={clsx(
        'relative overflow-hidden rounded-xl border bg-gradient-to-br p-6',
        'animate-slide-up opacity-0 [animation-fill-mode:forwards]',
        colorClasses[color]
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 font-medium">{title}</p>
          <p className="text-4xl font-bold mt-2 text-white">{value}</p>
          <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
        </div>
        <div className={clsx(
          'p-3 rounded-lg',
          color === 'cyan' && 'bg-neon-cyan/10',
          color === 'pink' && 'bg-neon-pink/10',
          color === 'purple' && 'bg-neon-purple/10',
          color === 'yellow' && 'bg-neon-yellow/10',
        )}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      
      {/* Decorative corner accent */}
      <div className={clsx(
        'absolute -bottom-8 -right-8 w-24 h-24 rounded-full opacity-20',
        color === 'cyan' && 'bg-neon-cyan',
        color === 'pink' && 'bg-neon-pink',
        color === 'purple' && 'bg-neon-purple',
        color === 'yellow' && 'bg-neon-yellow',
      )} />
    </div>
  );
}

export function Dashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.stats()
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-3xl font-bold text-white">
          {t('dashboard.welcome')} <span className="text-gradient">{t('app.name')}</span>
        </h1>
        <p className="text-slate-400 mt-2">
          {t('dashboard.subtitle')}
        </p>
      </div>

      {/* Stats Grid */}
      {error ? (
        <div className="bg-neon-pink/10 border border-neon-pink/30 rounded-xl p-6 animate-fade-in">
          <p className="text-neon-pink font-medium">{t('dashboard.error.apiUnavailable')}</p>
          <p className="text-slate-400 text-sm mt-1">{error}</p>
          <p className="text-slate-500 text-sm mt-2">
            {t('dashboard.error.backendHint')} <code className="text-neon-cyan">uv run resume-matcher serve</code>
          </p>
        </div>
      ) : loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-36 rounded-xl skeleton" />
          ))}
        </div>
      ) : stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title={t('dashboard.stats.totalResumes')}
            value={stats.total_resumes}
            subtitle={t('dashboard.stats.inDatabase')}
            icon={FileText}
            color="cyan"
            delay={100}
          />
          <StatCard
            title={t('dashboard.stats.withEmbeddings')}
            value={stats.with_embeddings}
            subtitle={t('dashboard.stats.readyForMatching')}
            icon={Brain}
            color="purple"
            delay={200}
          />
          <StatCard
            title={t('dashboard.stats.parsedData')}
            value={stats.with_parsed_data}
            subtitle={t('dashboard.stats.aiExtracted')}
            icon={Database}
            color="pink"
            delay={300}
          />
          <StatCard
            title={t('dashboard.stats.coverage')}
            value={stats.total_resumes > 0 
              ? `${Math.round((stats.with_embeddings / stats.total_resumes) * 100)}%` 
              : '0%'}
            subtitle={t('dashboard.stats.embeddingCoverage')}
            icon={TrendingUp}
            color="yellow"
            delay={400}
          />
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          to="/match"
          className="group relative overflow-hidden rounded-xl bg-void-800/50 border border-void-600/50 p-6 hover:border-neon-cyan/50 transition-all duration-300 animate-slide-up opacity-0 [animation-fill-mode:forwards]"
          style={{ animationDelay: '500ms' }}
        >
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-neon-cyan/10 text-neon-cyan group-hover:scale-110 transition-transform">
              <Search className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white group-hover:text-neon-cyan transition-colors">
                {t('dashboard.actions.matchCandidates')}
              </h3>
              <p className="text-slate-400 text-sm mt-1">
                {t('dashboard.actions.matchDescription')}
              </p>
              <div className="flex items-center gap-2 mt-4 text-neon-cyan text-sm font-medium">
                <span>{t('dashboard.actions.startMatching')}</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>
          
          {/* Hover gradient */}
          <div className="absolute inset-0 bg-gradient-to-r from-neon-cyan/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        </Link>

        <Link
          to="/import"
          className="group relative overflow-hidden rounded-xl bg-void-800/50 border border-void-600/50 p-6 hover:border-neon-purple/50 transition-all duration-300 animate-slide-up opacity-0 [animation-fill-mode:forwards]"
          style={{ animationDelay: '600ms' }}
        >
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-neon-purple/10 text-neon-purple group-hover:scale-110 transition-transform">
              <Zap className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white group-hover:text-neon-purple transition-colors">
                {t('dashboard.actions.importResumes')}
              </h3>
              <p className="text-slate-400 text-sm mt-1">
                {t('dashboard.actions.importDescription')}
              </p>
              <div className="flex items-center gap-2 mt-4 text-neon-purple text-sm font-medium">
                <span>{t('dashboard.actions.importNow')}</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>
          
          <div className="absolute inset-0 bg-gradient-to-r from-neon-purple/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        </Link>
      </div>

      {/* Features */}
      <div className="animate-slide-up opacity-0 [animation-fill-mode:forwards]" style={{ animationDelay: '700ms' }}>
        <h2 className="text-xl font-semibold text-white mb-4">{t('dashboard.howItWorks')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              step: '01',
              title: t('dashboard.steps.import.title'),
              description: t('dashboard.steps.import.description'),
              icon: FileText,
            },
            {
              step: '02',
              title: t('dashboard.steps.vacancy.title'),
              description: t('dashboard.steps.vacancy.description'),
              icon: Target,
            },
            {
              step: '03',
              title: t('dashboard.steps.matches.title'),
              description: t('dashboard.steps.matches.description'),
              icon: Zap,
            },
          ].map((item) => (
            <div
              key={item.step}
              className="relative bg-void-800/30 border border-void-600/30 rounded-xl p-5"
            >
              <div className="absolute -top-3 -left-3 w-8 h-8 rounded-lg bg-void-900 border border-neon-cyan/30 flex items-center justify-center">
                <span className="text-xs font-mono font-bold text-neon-cyan">{item.step}</span>
              </div>
              <item.icon className="w-8 h-8 text-slate-500 mb-3" />
              <h3 className="text-white font-medium">{item.title}</h3>
              <p className="text-slate-500 text-sm mt-1">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Trophy,
  User,
  Mail,
  Briefcase,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Star,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Zap,
  Download,
  FileText,
  Copy,
  Check
} from 'lucide-react';
import { 
  MatchResponse, 
  EmbeddingMatchResponse, 
  LLMMatchResponse,
  MatchedResumeResponse,
  LLMMatchedResumeResponse
} from '../api/client';
import { exportToCSV, exportToPDF, copyToClipboard } from '../utils/export';
import clsx from 'clsx';

function CopyEmailButton({ email }: { email: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const success = await copyToClipboard(email);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="p-1 text-slate-500 hover:text-neon-cyan transition-colors"
      title="Copy email"
    >
      {copied ? (
        <Check className="w-3 h-3 text-neon-cyan" />
      ) : (
        <Copy className="w-3 h-3" />
      )}
    </button>
  );
}

function ScoreRing({ score, color }: { score: number; color: string }) {
  return (
    <div 
      className="score-ring"
      style={{ '--score': score, '--color': color } as React.CSSProperties}
    >
      <div className="score-ring-inner" style={{ color }}>
        {Math.round(score)}
      </div>
    </div>
  );
}

function getScoreColor(score: number): string {
  if (score >= 80) return '#00f5d4'; // cyan
  if (score >= 60) return '#fee440'; // yellow
  if (score >= 40) return '#ff6b35'; // orange
  return '#f72585'; // pink
}

function getMatchLevelColor(level: string): string {
  switch (level.toLowerCase()) {
    case 'excellent': return 'text-neon-cyan';
    case 'good': return 'text-neon-yellow';
    case 'moderate': return 'text-neon-orange';
    default: return 'text-neon-pink';
  }
}

function EmbeddingResultCard({ match, rank }: { match: MatchedResumeResponse; rank: number }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const { candidate } = match;

  return (
    <div 
      className={clsx(
        'bg-void-800/50 border rounded-xl overflow-hidden transition-all duration-300',
        rank === 1 ? 'border-neon-cyan/50 ring-1 ring-neon-cyan/20' : 'border-void-600/50'
      )}
    >
      <div 
        className="p-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          {/* Rank Badge */}
          <div className={clsx(
            'w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg',
            rank === 1 ? 'bg-neon-cyan/20 text-neon-cyan' :
            rank === 2 ? 'bg-neon-purple/20 text-neon-purple' :
            rank === 3 ? 'bg-neon-pink/20 text-neon-pink' :
            'bg-void-700 text-slate-400'
          )}>
            {rank === 1 ? <Trophy className="w-5 h-5" /> : `#${rank}`}
          </div>

          {/* Score */}
          <ScoreRing score={match.similarity_percent} color={getScoreColor(match.similarity_percent)} />

          {/* Info */}
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-white truncate">
              {candidate.name || match.file_name}
            </h3>
            <p className="text-slate-400 text-sm truncate">
              {candidate.position || 'Position not specified'}
            </p>
            {candidate.email && (
              <p className="text-slate-500 text-xs flex items-center gap-1 mt-1">
                <Mail className="w-3 h-3" />
                {candidate.email}
                <CopyEmailButton email={candidate.email} />
              </p>
            )}
          </div>

          {/* Expand */}
          <button className="p-2 text-slate-400 hover:text-white">
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {/* Skills Preview */}
        {candidate.skills.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {candidate.skills.slice(0, 6).map((skill, i) => (
              <span key={i} className="px-2 py-1 text-xs bg-neon-cyan/10 text-neon-cyan rounded">
                {skill}
              </span>
            ))}
            {candidate.skills.length > 6 && (
              <span className="px-2 py-1 text-xs bg-void-700 text-slate-400 rounded">
                +{candidate.skills.length - 6}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-5 pb-5 pt-2 border-t border-void-600/50 space-y-4 animate-fade-in">
          {candidate.summary && (
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{t('results.summary')}</h4>
              <p className="text-slate-300 text-sm">{candidate.summary}</p>
            </div>
          )}
          {candidate.years_experience && (
            <div className="flex items-center gap-2 text-slate-400">
              <Briefcase className="w-4 h-4" />
              <span className="text-sm">{t('results.yearsExperience', { years: candidate.years_experience })}</span>
            </div>
          )}
          <p className="text-xs text-slate-600 font-mono">{match.file_name}</p>
        </div>
      )}
    </div>
  );
}

function LLMResultCard({ match, rank }: { match: LLMMatchedResumeResponse; rank: number }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(rank <= 3);

  return (
    <div 
      className={clsx(
        'bg-void-800/50 border rounded-xl overflow-hidden transition-all duration-300',
        rank === 1 ? 'border-neon-cyan/50 ring-1 ring-neon-cyan/20' : 'border-void-600/50'
      )}
    >
      <div 
        className="p-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          {/* Rank Badge */}
          <div className={clsx(
            'w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg',
            rank === 1 ? 'bg-neon-cyan/20 text-neon-cyan' :
            rank === 2 ? 'bg-neon-purple/20 text-neon-purple' :
            rank === 3 ? 'bg-neon-pink/20 text-neon-pink' :
            'bg-void-700 text-slate-400'
          )}>
            {rank === 1 ? <Trophy className="w-5 h-5" /> : `#${rank}`}
          </div>

          {/* Scores */}
          <div className="flex items-center gap-3">
            <div className="text-center">
              <ScoreRing score={match.combined_score} color={getScoreColor(match.combined_score)} />
              <p className="text-xs text-slate-500 mt-1">{t('results.combined')}</p>
            </div>
            <div className="text-center opacity-60">
              <div className="text-lg font-bold text-white">{match.llm_score}</div>
              <p className="text-xs text-slate-500">{t('results.llm')}</p>
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-white truncate">{match.file_name}</h3>
              <span className={clsx('badge', getMatchLevelColor(match.match_level))}>
                {match.match_level}
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1">{match.explanation.slice(0, 80)}...</p>
          </div>

          {/* Expand */}
          <button className="p-2 text-slate-400 hover:text-white">
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="px-5 pb-5 pt-2 border-t border-void-600/50 space-y-4 animate-fade-in">
          {/* Explanation */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              {t('results.aiAnalysis')}
            </h4>
            <p className="text-slate-300 text-sm leading-relaxed">{match.explanation}</p>
          </div>

          {/* Skills */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Matching Skills */}
            {match.matching_skills.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-neon-cyan uppercase tracking-wider mb-2 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" />
                  {t('results.matchingSkills')}
                </h4>
                <div className="flex flex-wrap gap-1">
                  {match.matching_skills.map((skill, i) => (
                    <span key={i} className="badge badge-cyan">{skill}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Missing Skills */}
            {match.missing_skills.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-neon-pink uppercase tracking-wider mb-2 flex items-center gap-1">
                  <XCircle className="w-3 h-3" />
                  {t('results.missingSkills')}
                </h4>
                <div className="flex flex-wrap gap-1">
                  {match.missing_skills.map((skill, i) => (
                    <span key={i} className="badge badge-pink">{skill}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Strengths & Concerns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strengths */}
            {match.strengths.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-neon-cyan uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Star className="w-3 h-3" />
                  {t('results.strengths')}
                </h4>
                <ul className="space-y-1">
                  {match.strengths.map((item, i) => (
                    <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                      <span className="text-neon-cyan">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Concerns */}
            {match.concerns.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-neon-yellow uppercase tracking-wider mb-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  {t('results.concerns')}
                </h4>
                <ul className="space-y-1">
                  {match.concerns.map((item, i) => (
                    <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                      <span className="text-neon-yellow">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Score Breakdown */}
          <div className="flex items-center gap-6 pt-2 text-sm text-slate-500">
            <span>{t('results.embedding')}: {match.embedding_score_percent.toFixed(1)}%</span>
            <span>{t('results.llm')}: {match.llm_score}/100</span>
            <span>{t('results.combined')}: {match.combined_score.toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}

function isLLMResponse(response: MatchResponse): response is LLMMatchResponse {
  return response.mode === 'llm';
}

export function MatchResults({ results }: { results: MatchResponse }) {
  const { t } = useTranslation();
  const isLLM = isLLMResponse(results);

  const handleExportCSV = () => {
    exportToCSV(results, 'candidates');
  };

  const handleExportPDF = () => {
    const title = isLLM ? (results as LLMMatchResponse).vacancy.job_title : undefined;
    exportToPDF(results, title);
  };

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white">
              {t('results.candidatesFound', { count: results.matches_found })}
            </h2>
            {isLLM ? (
              <span className="badge badge-purple">
                <Sparkles className="w-3 h-3 mr-1" />
                {t('results.aiMode')}
              </span>
            ) : (
              <span className="badge badge-cyan">
                <Zap className="w-3 h-3 mr-1" />
                {t('results.fastMode')}
              </span>
            )}
          </div>
          {!isLLM && (
            <p className="text-slate-500 text-sm">
              {t('results.fromTotal', { total: (results as EmbeddingMatchResponse).total_resumes_in_db })}
            </p>
          )}
        </div>

        {/* Export Buttons */}
        {results.matches_found > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-void-700/50 border border-void-600 rounded-lg text-slate-300 hover:text-white hover:border-neon-cyan/30 transition-colors"
            >
              <Download className="w-4 h-4" />
              CSV
            </button>
            <button
              onClick={handleExportPDF}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-void-700/50 border border-void-600 rounded-lg text-slate-300 hover:text-white hover:border-neon-cyan/30 transition-colors"
            >
              <FileText className="w-4 h-4" />
              PDF
            </button>
          </div>
        )}
      </div>

      {/* Vacancy Summary (LLM mode) */}
      {isLLM && (
        <div className="bg-neon-purple/5 border border-neon-purple/20 rounded-xl p-5">
          <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-neon-purple" />
            {t('results.parsedVacancy')}: {results.vacancy.job_title}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-slate-500 mb-1">{t('results.mustHaveSkills')}:</p>
              <div className="flex flex-wrap gap-1">
                {results.vacancy.must_have_skills.map((skill, i) => (
                  <span key={i} className="badge badge-purple">{skill}</span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">{t('results.niceToHave')}:</p>
              <div className="flex flex-wrap gap-1">
                {results.vacancy.nice_to_have_skills.map((skill, i) => (
                  <span key={i} className="px-2 py-0.5 text-xs bg-void-700 text-slate-400 rounded-full">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>
          {results.vacancy.min_years_experience && (
            <p className="text-slate-400 text-sm mt-2">
              {t('results.minExperience', { years: results.vacancy.min_years_experience })}
            </p>
          )}
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        {isLLM
          ? (results as LLMMatchResponse).matches.map((match, i) => (
              <div 
                key={match.id} 
                className="animate-slide-up opacity-0 [animation-fill-mode:forwards]"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <LLMResultCard match={match} rank={match.rank} />
              </div>
            ))
          : (results as EmbeddingMatchResponse).matches.map((match, i) => (
              <div 
                key={match.id}
                className="animate-slide-up opacity-0 [animation-fill-mode:forwards]"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <EmbeddingResultCard match={match} rank={match.rank} />
              </div>
            ))}
      </div>

      {/* Empty State */}
      {results.matches_found === 0 && (
        <div className="text-center py-12">
          <User className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-400">{t('results.noMatches')}</h3>
          <p className="text-slate-500 mt-1">
            {t('results.noMatchesHint')}
          </p>
        </div>
      )}
    </div>
  );
}

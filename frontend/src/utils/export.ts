/**
 * Export utilities for CSV and PDF generation
 */

import { MatchResponse, EmbeddingMatchResponse, LLMMatchResponse } from '../api/client';

function isLLMResponse(response: MatchResponse): response is LLMMatchResponse {
  return response.mode === 'llm';
}

/**
 * Export match results to CSV
 */
export function exportToCSV(results: MatchResponse, filename: string = 'candidates'): void {
  const isLLM = isLLMResponse(results);
  
  let csvContent = '';
  
  if (isLLM) {
    // LLM mode CSV with detailed analysis
    const headers = [
      'Rank',
      'Candidate',
      'Combined Score',
      'LLM Score',
      'Embedding Score',
      'Match Level',
      'Matching Skills',
      'Missing Skills',
      'Strengths',
      'Concerns',
      'Explanation'
    ];
    csvContent = headers.join(',') + '\n';
    
    const llmResults = results as LLMMatchResponse;
    llmResults.matches.forEach((match) => {
      const row = [
        match.rank,
        `"${match.file_name.replace(/"/g, '""')}"`,
        match.combined_score.toFixed(1),
        match.llm_score,
        match.embedding_score_percent.toFixed(1),
        match.match_level,
        `"${match.matching_skills.join(', ').replace(/"/g, '""')}"`,
        `"${match.missing_skills.join(', ').replace(/"/g, '""')}"`,
        `"${match.strengths.join('; ').replace(/"/g, '""')}"`,
        `"${match.concerns.join('; ').replace(/"/g, '""')}"`,
        `"${match.explanation.replace(/"/g, '""')}"`
      ];
      csvContent += row.join(',') + '\n';
    });
  } else {
    // Embedding mode CSV
    const headers = [
      'Rank',
      'Name',
      'Position',
      'Email',
      'Phone',
      'Similarity %',
      'Skills',
      'Years Experience',
      'File'
    ];
    csvContent = headers.join(',') + '\n';
    
    const embeddingResults = results as EmbeddingMatchResponse;
    embeddingResults.matches.forEach((match) => {
      const row = [
        match.rank,
        `"${(match.candidate.name || 'Unknown').replace(/"/g, '""')}"`,
        `"${(match.candidate.position || '').replace(/"/g, '""')}"`,
        match.candidate.email || '',
        match.candidate.phone || '',
        match.similarity_percent.toFixed(1),
        `"${(match.candidate.skills || []).join(', ').replace(/"/g, '""')}"`,
        match.candidate.years_experience || '',
        `"${match.file_name.replace(/"/g, '""')}"`
      ];
      csvContent += row.join(',') + '\n';
    });
  }
  
  // Create and download file
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

/**
 * Export match results to PDF (HTML-based)
 */
export function exportToPDF(results: MatchResponse, vacancyTitle?: string): void {
  const isLLM = isLLMResponse(results);
  const date = new Date().toLocaleDateString();
  
  let htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Candidate Match Report</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; color: #1a1a2e; line-height: 1.6; }
    .header { border-bottom: 3px solid #00f5d4; padding-bottom: 20px; margin-bottom: 30px; }
    .header h1 { font-size: 28px; color: #1a1a2e; }
    .header p { color: #666; margin-top: 5px; }
    .meta { display: flex; gap: 30px; margin-top: 15px; font-size: 14px; color: #666; }
    .vacancy-box { background: #f0f9ff; border-left: 4px solid #00f5d4; padding: 15px 20px; margin-bottom: 30px; }
    .vacancy-box h3 { color: #1a1a2e; margin-bottom: 10px; }
    .skills-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    .skill { background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 4px; font-size: 12px; }
    .candidate { border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 20px; page-break-inside: avoid; }
    .candidate-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }
    .candidate-rank { background: #00f5d4; color: #1a1a2e; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; }
    .candidate-info h3 { font-size: 18px; color: #1a1a2e; }
    .candidate-info p { color: #666; font-size: 14px; }
    .score-badge { font-size: 24px; font-weight: bold; color: #00f5d4; }
    .section { margin-top: 15px; }
    .section h4 { font-size: 12px; text-transform: uppercase; color: #666; margin-bottom: 8px; letter-spacing: 0.5px; }
    .section p { font-size: 14px; color: #374151; }
    .strengths { color: #059669; }
    .concerns { color: #dc2626; }
    .missing { color: #dc2626; }
    .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 12px; color: #999; }
    @media print { body { padding: 20px; } .candidate { page-break-inside: avoid; } }
  </style>
</head>
<body>
  <div class="header">
    <h1>📋 Candidate Match Report</h1>
    <p>Generated by Resume Matcher AI</p>
    <div class="meta">
      <span>📅 ${date}</span>
      <span>👥 ${results.matches_found} candidates</span>
      <span>🔍 ${isLLM ? 'AI Mode' : 'Fast Mode'}</span>
    </div>
  </div>
`;

  if (isLLM) {
    const llmResults = results as LLMMatchResponse;
    
    // Vacancy summary
    htmlContent += `
  <div class="vacancy-box">
    <h3>📌 ${llmResults.vacancy.job_title || vacancyTitle || 'Position'}</h3>
    ${llmResults.vacancy.min_years_experience ? `<p>Minimum ${llmResults.vacancy.min_years_experience} years experience</p>` : ''}
    <div class="skills-list">
      ${llmResults.vacancy.must_have_skills.map(s => `<span class="skill">${s}</span>`).join('')}
    </div>
  </div>
`;
    
    // Candidates
    llmResults.matches.forEach((match) => {
      htmlContent += `
  <div class="candidate">
    <div class="candidate-header">
      <div style="display: flex; gap: 15px; align-items: center;">
        <div class="candidate-rank">#${match.rank}</div>
        <div class="candidate-info">
          <h3>${match.file_name}</h3>
          <p>${match.match_level.toUpperCase()} match</p>
        </div>
      </div>
      <div class="score-badge">${match.combined_score.toFixed(0)}%</div>
    </div>
    
    <div class="section">
      <h4>AI Analysis</h4>
      <p>${match.explanation}</p>
    </div>
    
    ${match.matching_skills.length > 0 ? `
    <div class="section">
      <h4>✅ Matching Skills</h4>
      <div class="skills-list">
        ${match.matching_skills.map(s => `<span class="skill">${s}</span>`).join('')}
      </div>
    </div>
    ` : ''}
    
    ${match.missing_skills.length > 0 ? `
    <div class="section">
      <h4>❌ Missing Skills</h4>
      <p class="missing">${match.missing_skills.join(', ')}</p>
    </div>
    ` : ''}
    
    ${match.strengths.length > 0 ? `
    <div class="section">
      <h4>💪 Strengths</h4>
      <ul style="margin-left: 20px;">
        ${match.strengths.map(s => `<li class="strengths">${s}</li>`).join('')}
      </ul>
    </div>
    ` : ''}
    
    ${match.concerns.length > 0 ? `
    <div class="section">
      <h4>⚠️ Concerns</h4>
      <ul style="margin-left: 20px;">
        ${match.concerns.map(s => `<li class="concerns">${s}</li>`).join('')}
      </ul>
    </div>
    ` : ''}
  </div>
`;
    });
  } else {
    const embeddingResults = results as EmbeddingMatchResponse;
    
    embeddingResults.matches.forEach((match) => {
      htmlContent += `
  <div class="candidate">
    <div class="candidate-header">
      <div style="display: flex; gap: 15px; align-items: center;">
        <div class="candidate-rank">#${match.rank}</div>
        <div class="candidate-info">
          <h3>${match.candidate.name || match.file_name}</h3>
          <p>${match.candidate.position || 'Position not specified'}</p>
          ${match.candidate.email ? `<p>📧 ${match.candidate.email}</p>` : ''}
        </div>
      </div>
      <div class="score-badge">${match.similarity_percent.toFixed(0)}%</div>
    </div>
    
    ${match.candidate.summary ? `
    <div class="section">
      <h4>Summary</h4>
      <p>${match.candidate.summary}</p>
    </div>
    ` : ''}
    
    ${match.candidate.skills && match.candidate.skills.length > 0 ? `
    <div class="section">
      <h4>Skills</h4>
      <div class="skills-list">
        ${match.candidate.skills.slice(0, 15).map(s => `<span class="skill">${s}</span>`).join('')}
        ${match.candidate.skills.length > 15 ? `<span class="skill">+${match.candidate.skills.length - 15} more</span>` : ''}
      </div>
    </div>
    ` : ''}
  </div>
`;
    });
  }

  htmlContent += `
  <div class="footer">
    Generated by Resume Matcher • ${date} • ${results.matches_found} candidates analyzed
  </div>
</body>
</html>
`;

  // Open in new window for printing
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  }
}

/**
 * Copy text to clipboard with feedback
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      return true;
    } catch {
      return false;
    } finally {
      document.body.removeChild(textarea);
    }
  }
}

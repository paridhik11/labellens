/**
 * ui/js/ask-panel.js
 * Shared presentation for cited answers (P3 public, D5 professional).
 *
 * This file only draws one AnswerResponse, abstention or AI job. It holds no data and no corpus: the caller says
 * which module it serves ("public" or "professional") and passes the response it got for that module.
 *
 * Rules from docs/AI_ANSWER.md and docs/UI_NOTES_AI_ANSWER.md:
 * - Panel 1 is the instant extractive answer (or abstention with the closest passages). Always first.
 * - Panel 2 is the optional AI answer from "Ask AI (about 40 s)". If result.fallback_reason is set it shows
 *   passages with a notice, never an error. Nothing here says a label complies.
 * - An abstention shows no answer text. Score and threshold only when not null.
 * - No em dashes.
 */

(function() {
  const esc = (s) => window.LabelLensData.escapeHtml(s);

  const FALLBACK_TEXT = {
    model_unavailable: 'The AI model is not available here. Showing the closest passages.',
    timeout: 'The AI took too long. Showing the closest passages.',
    verification_failed: 'The AI answer did not pass the citation checks. Showing the closest passages.',
  };

  /** Title of one citation. A DailyMed label chunk is titled "<medicine>: <section>": show the section only. */
  function citationTitle(s) {
    if (s.source_type === 'label_section') {
      const t = String(s.title || '');
      const i = t.indexOf(': ');
      return 'Label section: ' + (i >= 0 ? t.slice(i + 2) : t);
    }
    return (s.section ? '21 CFR ' + s.section + ': ' : '') + (s.title || '');
  }

  /** True when the top score is under the gate: nothing relevant was found, so the passages are weak guesses. */
  function lowConfidence(d) {
    return d.score !== null && d.score !== undefined && d.threshold !== null && d.threshold !== undefined && d.score < d.threshold;
  }

  function sourcesHtml(sources) {
    if (!sources || !sources.length) return '';
    return `
      <div style="border-top: 1px solid var(--color-border); padding-top: 12px; margin-top: 12px;">
        <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Citations (${sources.length})</div>
        <div class="flex-col" style="gap: 10px;">
          ${sources.map(s => `
            <div style="background: #ffffff; border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px;" data-testid="citation">
              <div class="flex-between">
                <div class="flex-row" style="gap: 6px;">
                  <span class="badge badge-teal">${esc(s.source_type || 'cfr')}</span>
                  <span class="font-semibold text-xs">${esc(citationTitle(s))}</span>
                </div>
                ${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-secondary" style="font-size: 0.75rem; padding: 2px 8px;">${s.source_type === 'label_section' ? 'View in label' : 'View regulation'} &rarr;</a>` : ''}
              </div>
              ${s.quote ? `<div style="font-style: italic; font-size: 0.825rem; margin-top: 8px; border-left: 2px solid var(--color-primary-teal); padding-left: 10px;">"${esc(s.quote)}"</div>` : ''}
              <div class="text-xs text-muted" style="margin-top: 6px;">Source: ${esc(s.source || '')} | Chunk: <code>${esc(s.chunk_id || '')}</code></div>
            </div>`).join('')}
        </div>
      </div>`;
  }

  /** One AnswerResponse: a cited answer, or an abstention (no answer text) with optional closest passages. */
  function answerHtml(a) {
    const d = a || {};
    if (d.abstained === true) {
      const bits = [];
      if (d.score_name) bits.push(`Metric: <strong>${esc(d.score_name)}</strong>`);
      if (d.score !== null && d.score !== undefined && !Number.isNaN(d.score)) bits.push(`Score: <strong>${esc(d.score)}</strong>`);
      if (d.threshold !== null && d.threshold !== undefined && !Number.isNaN(d.threshold)) bits.push(`Threshold: <strong>${esc(d.threshold)}</strong>`);
      return `
        <div class="notice-banner notice-warning" data-testid="abstained" style="margin-bottom: 0;">
          <div class="notice-icon">i</div>
          <div style="flex: 1;">
            <div class="flex-between">
              <div class="notice-title">Abstained: <code>${esc(d.reason || 'abstained')}</code></div>
              <span class="badge badge-warning">No answer generated</span>
            </div>
            <div class="notice-text" style="margin-top: 6px;">${esc(d.message || '')}</div>
            ${bits.length ? `<div class="text-xs font-mono" style="margin-top: 10px;">${bits.join(' | ')}</div>` : ''}
            ${(d.sources || []).length ? (lowConfidence(d)
              ? `<details data-testid="low-confidence-passages" style="margin-top: 10px;"><summary class="text-xs font-semibold" style="cursor: pointer;">Show closest passages (low confidence)</summary>${sourcesHtml(d.sources)}</details>`
              : `<div class="text-xs font-semibold" style="margin-top: 10px;">Closest passages (not an answer, a person should check them):</div>${sourcesHtml(d.sources)}`) : ''}
          </div>
        </div>`;
    }
    return `
      <div style="background: var(--color-primary-teal-subtle); border: 1px solid var(--color-primary-teal-light); border-radius: var(--radius-md); padding: 16px;" data-testid="answer">
        <div class="flex-between" style="margin-bottom: 8px;">
          <div class="font-semibold text-sm" style="color: var(--color-primary-teal);">Answer from the cited text</div>
          ${d.based_on ? `<span class="text-xs text-muted">Basis: <strong>${esc(d.based_on)}</strong></span>` : ''}
        </div>
        <div style="font-size: 0.95rem; line-height: 1.55;">${esc(d.answer || '')}</div>
        ${sourcesHtml(d.sources)}
      </div>`;
  }

  /** Panel 2: the AI job, in any state. */
  function aiPanelHtml(job) {
    const j = job || {};
    let body;
    if (j.state === 'queued' || j.state === 'processing') {
      const pct = Math.round((j.progress || 0) * 100);
      body = `
        <div data-testid="ai-running">
          <div class="text-sm">${esc(j.message || 'The AI answer is being prepared (about 40 s).')}</div>
          <div style="width: 100%; max-width: 320px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 12px 0 4px; overflow: hidden;">
            <div style="width: ${pct}%; height: 100%; background: var(--color-primary-blue);"></div>
          </div>
          <div class="text-xs text-muted">${esc(j.state)} | ${pct}% | job <code>${esc(j.job_id)}</code>. You can keep reading the passages above.</div>
        </div>`;
    } else if (j.state === 'failed') {
      body = `<div class="notice-banner notice-danger" data-testid="ai-failed" style="margin-bottom: 0;"><div class="notice-icon">!</div><div>
        <div class="notice-title">Search is not available right now</div>
        <div class="notice-text">${esc((j.error || {}).message || 'The AI answer job failed.')} The passages above are still shown.</div></div></div>`;
    } else {
      const r = j.result || {};
      const notice = r.fallback_reason
        ? `<div class="notice-banner notice-warning" data-testid="ai-fallback" style="margin-bottom: 12px;"><div class="notice-icon">i</div><div class="notice-text">${esc(FALLBACK_TEXT[r.fallback_reason] || 'Showing the closest passages.')}</div></div>`
        : '';
      body = `
        ${notice}
        ${answerHtml(r.answer)}
        <div class="text-xs text-muted" style="margin-top: 8px;" data-testid="ai-note">
          ${r.model_used ? 'AI-generated, supported by the cited text only. Check the quotes. Not a compliance determination.' : 'No model answer was used.'}
          Model: <code>${esc(r.model || 'none')}</code>${r.latency_s !== undefined ? ' | ' + esc(r.latency_s) + ' s' : ''}
        </div>`;
    }
    return `
      <div class="card" style="margin-top: 16px;" data-testid="ai-panel">
        <div class="card-header-clean flex-between"><span class="font-semibold text-sm">AI answer (optional)</span><span class="badge badge-purple">AI</span></div>
        ${body}
      </div>`;
  }

  /** True when a payload is an ask job envelope (mock ai_accepted, ai_job_done, ai_job_fallback_timeout). */
  function isAskJob(d) {
    return !!(d && d.kind === 'ask' && d.job_id);
  }

  window.LabelLensAsk = { answerHtml, aiPanelHtml, sourcesHtml, isAskJob, FALLBACK_TEXT };
})();

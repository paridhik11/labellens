/**
 * ui/js/render-d8.js
 * Renderer for Screen D8: Export (Download Package)
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Mark drafts clearly: DRAFT watermark on unreviewed exports, QR only on published.
 * - Never invent data.
 * - No em dashes.
 */

(function() {
  function escapeHtml(str) {
    if (window.LabelLensData && window.LabelLensData.escapeHtml) {
      return window.LabelLensData.escapeHtml(str);
    }
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function renderScreenD8(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};
    const isDraft = safeData.draft_watermark === true || state === 'draft' || safeData.status !== 'published';
    const pdf = safeData.pdf || {};
    const svg = safeData.svg || {};
    const report = safeData.report || {};
    const qr = safeData.qr || null;

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Export Package</h2>
          <div class="text-xs text-muted">Version: <code>${escapeHtml(safeData.version_id || 'lbv_0003')}</code> | Label: <code>${escapeHtml(safeData.label_id || '')}</code></div>
        </div>
        <div class="flex-row">
          <span class="badge ${isDraft ? 'badge-draft' : 'badge-teal'}">
            ${isDraft ? 'DRAFT EXPORT' : 'PUBLISHED RELEASE'}
          </span>
        </div>
      </div>

      ${isDraft ? `
        <div class="notice-banner notice-warning">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">DRAFT Artifacts (Unpublished)</div>
            <div class="notice-text">Draft generated for review. Not a compliance determination. Exports include a mandatory watermark. QR code is suppressed until approval.</div>
          </div>
        </div>
      ` : `
        <div class="notice-banner notice-teal" style="background: var(--color-primary-teal-subtle); border-color: var(--color-primary-teal-light);">
          <div class="notice-icon" style="color: var(--color-primary-teal);">✓</div>
          <div>
            <div class="notice-title" style="color: var(--color-primary-teal);">Approved &amp; Published</div>
            <div class="notice-text">This label package has been verified and approved. Production artwork files and live verification QR code are available below.</div>
          </div>
        </div>
      `}

      <div class="grid-three-col" style="margin-top: 20px;">
        <!-- Card 1: Print-ready PDF -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Print PDF</span>
            <span class="badge badge-blue">PDF</span>
          </div>
          <div class="text-xs text-muted" style="margin-bottom: 12px;">Vector artwork with embedded fonts and crop marks.</div>
          <div class="text-xs font-mono" style="word-break: break-all; margin-bottom: 16px;">
            ${escapeHtml(pdf.url || 'files/label.pdf')}
          </div>
          <button class="btn btn-sm btn-primary" type="button" style="width: 100%;">Download PDF</button>
        </div>

        <!-- Card 2: Production SVG -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Vector SVG</span>
            <span class="badge badge-purple">SVG</span>
          </div>
          <div class="text-xs text-muted" style="margin-bottom: 12px;">Scalable graphics with standard slot layers.</div>
          <div class="text-xs font-mono" style="word-break: break-all; margin-bottom: 16px;">
            ${escapeHtml(svg.url || 'files/label.svg')}
          </div>
          <button class="btn btn-sm btn-secondary" type="button" style="width: 100%;">Download SVG</button>
        </div>

        <!-- Card 3: Audit Compliance Report -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Audit Report</span>
            <span class="badge badge-teal">PDF</span>
          </div>
          <div class="text-xs text-muted" style="margin-bottom: 12px;">Cryptographic findings and regulatory citations.</div>
          <div class="text-xs font-mono" style="word-break: break-all; margin-bottom: 16px;">
            ${escapeHtml(report.url || 'files/report.pdf')}
          </div>
          <button class="btn btn-sm btn-secondary" type="button" style="width: 100%;">Download Report</button>
        </div>
      </div>

      <!-- QR Code Section -->
      ${qr ? `
        <div class="card" style="margin-top: 20px;">
          <div class="card-header-clean font-semibold text-sm">Published Label Verification QR Code</div>
          <div class="flex-row" style="gap: 20px; align-items: center;">
            <div style="background: #ffffff; border: 2px solid #0f172a; padding: 12px; border-radius: var(--radius-md); font-family: monospace; font-size: 0.75rem; text-align: center;">
              <div style="font-size: 2rem;">▦</div>
              <span>[QR: ${escapeHtml(qr.qr_payload || qr.url)}]</span>
            </div>
            <div>
              <div class="font-semibold text-sm">Public Verification Page</div>
              <div class="text-xs text-muted" style="margin-top: 2px;">
                URL: <code>${escapeHtml(qr.url || '')}</code> | Published: ${escapeHtml(qr.published_at || '')}
              </div>
              <div class="text-xs text-muted" style="margin-top: 6px;">
                Tied to Review Record: <code>${escapeHtml(qr.review_id || '')}</code>
              </div>
            </div>
          </div>
        </div>
      ` : ''}
    `;
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D8 Export'] = renderScreenD8;
  window.LabelLensRenderers['D8'] = renderScreenD8;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD8 };
  }
})();

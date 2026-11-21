/**
 * ui/js/render-d6.js
 * Renderer for Screen D6: Changes ("Change impact", Mockup Panel 4)
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Structured form (field, old value, new value) is the MAIN way to enter a change.
 * - Typed text is a convenience only.
 * - Mark all drafts clearly: DRAFT watermark and required disclaimer.
 * - Deterministic templates only. Never invent GTIN or UDI-DI.
 * - Barcode decision (KEEP, REGENERATE, NEEDS_INPUT) must be visible.
 * - Side by side current against draft revision preview, and timeline.
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

  function renderTestBadge(val) {
    if (window.LabelLensData && window.LabelLensData.renderTestBadge) {
      return window.LabelLensData.renderTestBadge(val);
    }
    return '';
  }

  /** Switch the screen to another mock state through the state switcher so the payload is loaded too. */
  function gotoState(label) {
    if (window.LabelLensStateSwitcher) window.LabelLensStateSwitcher.setScreen('D6 Changes', label);
  }

  function renderScreenD6(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};
    const apiMode = window.LabelLensData.CONFIG.mode === 'api';
    // Live means this payload came from the API (or from a step done here), not from a mock sample.
    const liveData = apiMode && !!(meta && meta.source === 'api');
    const dflt = (v) => (apiMode && !liveData ? '' : v);
    const stateStr = String(state || '').toLowerCase();

    // 1. Loading State (202 Job envelope: generateArtwork)
    if (stateStr === 'loading' || (safeData.state && safeData.state === 'processing') || stateStr.includes('generate_loading')) {
      const progressPct = Math.round((safeData.progress || 0.6) * 100);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 650px; margin: 20px auto;">
          <div class="flex-between" style="margin-bottom: 16px;">
            <span class="badge badge-purple">Job: ${escapeHtml(safeData.job_id || 'job_gen_0001')}</span>
            <span class="badge badge-teal">Status: ${escapeHtml(safeData.state || 'processing')}</span>
          </div>
          <div style="font-size: 2.5rem; margin-bottom: 12px;"><svg class="icon icon-xl" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/></svg></div>
          <h3>Generating Deterministic Artwork Draft</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">${escapeHtml(safeData.message || 'Rendering draft and running self-check')}</p>
          
          <div style="width: 100%; max-width: 360px; height: 10px; background: #e2e8f0; border-radius: 99px; margin: 24px auto 10px auto; overflow: hidden;">
            <div style="width: ${progressPct}%; height: 100%; background: var(--color-draft-purple); transition: width 0.3s ease;"></div>
          </div>
          <div class="text-xs text-muted font-semibold">${progressPct}% completed</div>

          <div class="text-xs text-muted" style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--color-border);">
            Applying deterministic template constraints and embedding mandatory DRAFT watermark band.
          </div>
        </div>
      `;
      return;
    }

    // 2. Identifier Required / Needs Input State (422 / 409 NeedsInput)
    if (stateStr.includes('needs_input') || safeData.error === 'needs_input' || (safeData.barcode_decision && safeData.barcode_decision.decision === 'NEEDS_INPUT')) {
      const bc = safeData.barcode_decision || {};
      container.innerHTML = `
        <div class="notice-banner notice-warning" style="max-width: 800px; margin: 0 auto 20px auto;">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Identifier Required: Allocation Needed</div>
            <div class="notice-text">${escapeHtml(safeData.message || 'This change needs a new UDI-DI. Enter the allocated identifier; LabelLens never creates one.')}</div>
          </div>
        </div>

        <div class="card" style="max-width: 800px; margin: 0 auto; padding: 24px;">
          <div class="flex-between" style="border-bottom: 1px solid var(--color-border); padding-bottom: 12px; margin-bottom: 16px;">
            <div>
              <h3>Barcode Decision: <span class="badge badge-warning" style="font-size: 0.85rem;">NEEDS_INPUT</span></h3>
              <div class="text-xs text-muted" style="margin-top: 4px;">Task ID: <code>${escapeHtml(safeData.task ? safeData.task.task_id : 'tsk_0001')}</code> : ${escapeHtml(safeData.task ? safeData.task.title : 'enter allocated identifier')}</div>
            </div>
            <span class="badge badge-blue">Symbology: ${escapeHtml(bc.symbology || 'GS1_DataMatrix')}</span>
          </div>

          <div style="background-color: var(--color-bg-subtle); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--color-border); margin-bottom: 20px;">
            <div class="text-xs font-semibold text-muted">Reason for New Identifier:</div>
            <div class="text-sm font-semibold" style="margin-top: 4px; color: var(--color-text-main);">
              ${escapeHtml(bc.reason || 'Model change ED-100 to ED-200 needs a new device identifier')}
            </div>
            <div class="text-xs text-muted" style="margin-top: 8px;">
              Previous Barcode Payload: <code style="word-break: break-all;">${escapeHtml(bc.old_payload || '(01)00000000000000(17)280331(10)LOT0001(21)SN0001')}</code> ${renderTestBadge(bc.old_payload)}
            </div>
          </div>

          <div style="border: 1px solid #fed7aa; background-color: #fff7ed; padding: 16px; border-radius: var(--radius-md); margin-bottom: 20px;">
            <div class="font-semibold text-sm" style="color: #9a3412;">System Policy: No Invented Identifiers</div>
            <p class="text-xs" style="color: #c2410c; margin-top: 4px; line-height: 1.4;">
              LabelLens never creates or guesses GTIN or UDI-DI values. An authorized labeler must provide the real GS1 identifier allocated in the company database or GS1 GEPIR registry.
            </p>
          </div>

          <div class="form-group" style="margin-bottom: 16px;">
            <label class="text-xs font-semibold text-muted" style="display: block; margin-bottom: 6px;">
              Enter Allocated Primary UDI-DI / GTIN (14 numeric digits):
            </label>
            <div class="flex-row" style="gap: 8px;">
              <input type="text" id="inputAllocatedUdi" placeholder="00000000000000" style="flex: 1; padding: 8px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); font-family: monospace; font-size: 0.9rem;" value="00000000000000">
              <button class="btn btn-primary" type="button" id="btnSubmitUdi">Submit Identifier</button>
            </div>
            <div class="text-xs text-muted" style="margin-top: 6px;">Sample test placeholder shown above. [TEST] badge applied automatically.</div>
          </div>
        </div>
      `;
      return;
    }

    // 3. Generated Draft Artwork State (GeneratedArtwork schema)
    if (stateStr.includes('draft artwork') || safeData.artwork_id || safeData.artifact_sha256) {
      const bc = safeData.barcode_decision || {};
      const changeLog = safeData.change_log || [];
      const layoutProblems = safeData.layout_problems || [];
      const size = safeData.size_mm || { w: 100, h: 60 };

      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Generated Draft Artwork</h2>
            <div class="text-xs text-muted">Artwork ID: <code>${escapeHtml(safeData.artwork_id || 'art_0001')}</code> : Version: <code>${escapeHtml(safeData.version_id || 'lbv_exampledevice_carton_l3')}</code></div>
          </div>
          <div class="flex-row" style="gap: 8px;">
            <span class="badge badge-draft">DRAFT</span>
            ${renderTestBadge(safeData)}
            <span class="badge badge-purple">Template: ${escapeHtml(safeData.template_id || 'tpl_exampledevice_carton')} (v${safeData.template_version || 1})</span>
          </div>
        </div>

        <!-- Mandatory DRAFT Banner -->
        <div class="notice-banner notice-warning" style="margin-bottom: 20px;">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">DRAFT : Not for Production</div>
            <div class="notice-text">${escapeHtml(safeData.disclaimer || 'Draft generated for review. Not a compliance determination.')}</div>
          </div>
        </div>

        <div class="grid-two-col">
          <!-- Left: Artwork Visual Preview Canvas -->
          <div class="card">
            <div class="card-header-clean flex-between">
              <span class="font-semibold text-sm">Artwork Preview (${size.w} x ${size.h} mm)</span>
              <span class="badge badge-draft">WATERMARK APPLIED</span>
            </div>

            <!-- Physical mm container with DRAFT watermark -->
            <div style="position: relative; width: 100%; aspect-ratio: 100 / 60; background: #ffffff; border: 2px dashed var(--color-draft-purple); border-radius: var(--radius-md); overflow: hidden; padding: 12px; box-sizing: border-box;">
              <!-- Diagonal Draft Watermark Overlay -->
              <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; pointer-events: none; z-index: 10;">
                <span style="font-size: 3.5rem; font-weight: 900; color: rgba(147, 51, 234, 0.12); transform: rotate(-25deg); text-transform: uppercase; letter-spacing: 6px;">DRAFT</span>
              </div>

              <!-- Top 9mm Reserved Watermark Band representation -->
              <div style="position: absolute; top: 0; left: 0; right: 0; height: 15%; background: rgba(239, 68, 68, 0.08); border-bottom: 1px dashed rgba(239, 68, 68, 0.4); display: flex; align-items: center; padding-left: 8px; font-size: 0.65rem; color: #dc2626; font-weight: 700;">
                DRAFT WATERMARK BAND (TOP 9mm)
              </div>

              <!-- Label Content Simulation -->
              <div style="position: relative; z-index: 5; height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding-top: 14%;">
                <div>
                  <div style="font-weight: 800; font-size: 0.9rem;">ExampleDevice™ Angiographic Catheter</div>
                  <div style="font-size: 0.72rem; color: var(--color-text-muted); margin-top: 2px;">Model: ED-100 | Ref: 987654</div>
                  <div style="font-size: 0.72rem; margin-top: 6px;">
                    Sterilization: <strong>Gamma irradiation</strong>
                    <span style="border: 1px solid #1e293b; padding: 1px 4px; font-size: 0.65rem; font-weight: 700; margin-left: 6px;">STERILE R</span>
                  </div>
                </div>

                <div class="flex-between" style="border-top: 1px solid #e2e8f0; padding-top: 6px;">
                  <div style="font-size: 0.65rem; font-family: monospace;">
                    (01)00000000000000<br>
                    (17)280331(10)LOT0001(21)SN0001
                  </div>
                  <div style="width: 36px; height: 36px; border: 1px solid #0f172a; display: flex; align-items: center; justify-content: center; font-size: 0.6rem; font-weight: bold; background: #0f172a; color: white;">
                    2D
                  </div>
                </div>
              </div>
            </div>

            <!-- Artifact Downloads -->
            <div class="flex-between" style="margin-top: 16px;">
              <span class="text-xs text-muted">Generated Artifacts:</span>
              <div class="flex-row" style="gap: 8px;">
                <a href="${escapeHtml(safeData.svg_url || '#')}" class="btn btn-secondary btn-sm" download>Download SVG</a>
                <a href="${escapeHtml(safeData.pdf_url || '#')}" class="btn btn-secondary btn-sm" download>Download PDF</a>
              </div>
            </div>
          </div>

          <!-- Right: Self-check, Barcode Decision & Change Log -->
          <div class="flex-col" style="gap: 16px;">
            <!-- Barcode Decision Card -->
            <div class="card">
              <div class="card-header-clean flex-between">
                <span class="font-semibold text-sm">Barcode Decision</span>
                <span class="badge ${bc.decision === 'KEEP' ? 'badge-teal' : (bc.decision === 'REGENERATE' ? 'badge-blue' : 'badge-warning')}">${escapeHtml(bc.decision || 'KEEP')}</span>
              </div>
              <div class="text-xs text-muted">${escapeHtml(bc.reason || 'Encoded data unchanged; sterilization is printed text and a symbol only')}</div>
              <div class="text-xs font-mono" style="margin-top: 8px; background: var(--color-bg-subtle); padding: 6px; border-radius: var(--radius-sm);">
                Payload: ${escapeHtml(bc.new_payload || bc.old_payload || '')} ${renderTestBadge(bc.new_payload || bc.old_payload)}
              </div>
            </div>

            <!-- Self Check Result Card -->
            <div class="card">
              <div class="card-header-clean flex-between">
                <span class="font-semibold text-sm">Self-Check Result</span>
                <span class="badge badge-teal">${layoutProblems.length === 0 ? 'PASSED (0 findings)' : layoutProblems.length + ' Finding(s)'}</span>
              </div>
              <div class="text-xs text-muted">Check ID: <code>${escapeHtml(safeData.self_check_id || 'chk_0003')}</code></div>
              <div class="text-xs text-muted" style="margin-top: 4px; word-break: break-all;">
                SHA-256: <code>${escapeHtml(safeData.artifact_sha256 || '')}</code>
              </div>
            </div>

            <!-- Change Log Card -->
            <div class="card">
              <div class="card-header-clean font-semibold text-sm">Deterministic Change Log</div>
              <div class="flex-col" style="gap: 8px;">
                ${changeLog.map(entry => `
                  <div style="background: var(--color-bg-subtle); padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); font-size: 0.75rem;">
                    <div class="flex-between">
                      <span class="font-semibold text-purple">Field: ${escapeHtml(entry.field)}</span>
                      <span class="text-muted text-xs">${escapeHtml(entry.at || '')}</span>
                    </div>
                    <div style="margin-top: 4px;">
                      <span class="text-muted">Changed:</span> <code>${escapeHtml(entry.old_value)}</code> &rarr; <strong>${escapeHtml(entry.new_value)}</strong>
                    </div>
                    <div class="text-muted text-xs" style="margin-top: 4px;">
                      Rule: <code>${escapeHtml((entry.rules_fired || []).join(', '))}</code>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>

            <!-- Action buttons -->
            <div class="flex-between" style="margin-top: 8px;">
              <button class="btn btn-secondary btn-sm" type="button" id="btnGoToChangesForm">Back to Changes</button>
              <button class="btn btn-primary btn-sm" type="button" id="btnGoToReviewFromDraft">Proceed to Review &amp; Approval &rarr;</button>
            </div>
          </div>
        </div>
      `;

      const reviewBtn = container.querySelector('#btnGoToReviewFromDraft');
      if (reviewBtn) {
        reviewBtn.addEventListener('click', () => {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'D7 Review' }
          }));
        });
      }

      const backBtn = container.querySelector('#btnGoToChangesForm');
      if (backBtn) {
        backBtn.addEventListener('click', () => {
          gotoState('success (assessment)');
        });
      }
      return;
    }

    // 4. Affected list only state (AffectedLabelsResponse schema)
    if (safeData.items && !safeData.change) {
      const items = safeData.items || [];
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Affected Labels Across Packaging Hierarchy</h2>
            <div class="text-xs text-muted">Change ID: <code>${escapeHtml(safeData.change_id || 'chg_0002')}</code></div>
          </div>
          <span class="badge badge-blue">${items.length} Affected Item(s)</span>
        </div>

        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Impacted Label Components</div>
          <div class="flex-col" style="gap: 12px;">
            ${items.map(it => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 14px;">
                <div class="flex-between">
                  <div>
                    <span class="font-semibold text-sm">${escapeHtml(it.title)}</span>
                    <span class="badge badge-purple text-xs" style="margin-left: 6px;">${escapeHtml(it.item_kind)}</span>
                  </div>
                  <span class="badge ${it.suggestion === 'edit_required' ? 'badge-danger' : (it.suggestion === 'no_change' ? 'badge-teal' : 'badge-warning')}">
                    ${escapeHtml(it.suggestion.replace('_', ' '))}
                  </span>
                </div>
                <div class="text-xs text-muted" style="margin-top: 6px;">${escapeHtml(it.description)}</div>
                <div class="text-xs text-muted" style="margin-top: 4px;">
                  Target: <code>${escapeHtml(it.label_id)}</code> (${escapeHtml(it.version_id)})
                  ${it.slot_id ? ` : Slot: <code>${escapeHtml(it.slot_id)}</code>` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
      return;
    }

    // 5. Standard Change Assessment View (Assess / Confirm / Returned / Rejected)
    const change = safeData.change || safeData;
    const affected = safeData.affected || [];
    const citations = safeData.citations || [];
    const isConfirmed = change.parse_state === 'confirmed' || safeData.checklist_complete === true;
    const isReturned = stateStr.includes('returned') || change.status === 'returned';
    const isRejected = stateStr.includes('rejected') || change.closed === true;
    const needsHumanReview = safeData.needs_human_review || (stateStr.includes('needs_review') && !stateStr.includes('needs_input'));

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Change Impact Assessment</h2>
          <div class="text-xs text-muted">Automated assessment of proposed label modifications across packaging hierarchy.</div>
        </div>
        <div class="flex-row" style="gap: 8px;">
          <span class="badge badge-blue">Change ID: ${escapeHtml(change.change_id || 'chg_0002')}</span>
          <span class="badge ${isRejected ? 'badge-danger' : (isReturned ? 'badge-warning' : (isConfirmed ? 'badge-teal' : 'badge-draft'))}">
            ${isRejected ? 'REJECTED (CLOSED)' : (isReturned ? 'RETURNED' : (isConfirmed ? 'CONFIRMED' : 'DRAFT'))}
          </span>
        </div>
      </div>

      <!-- Returned Notice Banner -->
      ${isReturned ? `
        <div class="notice-banner notice-warning" style="margin-bottom: 16px;">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Change Returned by Reviewer</div>
            <div class="notice-text">Reviewer feedback received (Review ID: ${escapeHtml(change.latest_review_id || 'rev_0002')}). Please review comments, adjust structured fields, and re-assess.</div>
          </div>
        </div>
      ` : ''}

      <!-- Rejected Notice Banner -->
      ${isRejected ? `
        <div class="notice-banner notice-danger" style="margin-bottom: 16px;">
          <div class="notice-icon">x</div>
          <div>
            <div class="notice-title">Change Rejected and Closed</div>
            <div class="notice-text">This change request was rejected (Review ID: ${escapeHtml(change.latest_review_id || 'rev_0004')}). Terminal state: no further drafts can be published.</div>
          </div>
        </div>
      ` : ''}

      <!-- Needs Human Review Banner -->
      ${needsHumanReview ? `
        <div class="notice-banner notice-warning" style="margin-bottom: 16px;">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">NEEDS HUMAN REVIEW</div>
            <div class="notice-text">${escapeHtml(needsHumanReview)}</div>
          </div>
        </div>
      ` : ''}

      <!-- STRUCTURED FORM (MAIN WAY TO ENTER A CHANGE) -->
      <div class="card" style="margin-bottom: 20px; border: 2px solid var(--color-primary-blue); background-color: #f8fafc;">
        <div class="card-header-clean flex-between">
          <span class="font-semibold text-sm" style="color: var(--color-primary-blue);">
            Structured Change Specification (Primary Method)
          </span>
          <span class="badge badge-blue">Main Entry</span>
        </div>

        <form id="formStructuredChange" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 8px;">
          <div>
            <label class="text-xs font-semibold text-muted" style="display: block; margin-bottom: 4px;">Target Field:</label>
            <input type="text" id="changeField" class="form-control text-sm" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: var(--radius-sm);" value="${escapeHtml(change.field || dflt('sterilization'))}" ${isRejected ? 'disabled' : ''}>
          </div>
          <div>
            <label class="text-xs font-semibold text-muted" style="display: block; margin-bottom: 4px;">Current / Old Value:</label>
            <input type="text" id="changeOldVal" class="form-control text-sm" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: var(--radius-sm);" value="${escapeHtml(change.old_value || dflt('Ethylene oxide (EO)'))}" ${isRejected ? 'disabled' : ''}>
          </div>
          <div>
            <label class="text-xs font-semibold text-muted" style="display: block; margin-bottom: 4px;">Proposed New Value:</label>
            <input type="text" id="changeNewVal" class="form-control text-sm" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: var(--radius-sm);" value="${escapeHtml(change.new_value || dflt('Gamma irradiation'))}" ${isRejected ? 'disabled' : ''}>
          </div>
        </form>
        ${apiMode ? `
          <div class="flex-row" style="gap: 8px; margin-top: 10px;">
            <button class="btn btn-primary btn-sm" type="button" id="btnAssessChange" data-testid="assess-btn">Assess change</button>
            <span class="text-xs text-muted" id="d6AssessNote" data-testid="assess-note">${liveData ? '' : 'Type the field and the new value. The checklist below is a mock sample until you assess.'}</span>
          </div>` : ''}

        <!-- Typed text convenience field -->
        <div style="margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--color-border);">
          <div class="flex-between">
            <label class="text-xs font-semibold text-muted">Free-text Description (Convenience Only):</label>
            <span class="text-xs text-muted">Parser: <code>${escapeHtml(safeData.parser || 'mock')}</code></span>
          </div>
          <input type="text" class="form-control text-xs" style="width: 100%; padding: 6px 8px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); margin-top: 4px; color: var(--color-text-muted);" value="${escapeHtml(change.raw_text || dflt('Update the sterilization method from ethylene oxide (EO) to gamma irradiation.'))}" ${isRejected ? 'disabled' : ''}>
        </div>
      </div>

      <div class="grid-two-col">
        <!-- Left: Affected Items Checklist -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Affected Items Checklist (${affected.length})</span>
            <span class="badge ${isConfirmed ? 'badge-teal' : 'badge-warning'}">
              ${isConfirmed ? 'Checklist Complete' : 'Confirmation Pending'}
            </span>
          </div>

          <div class="flex-col" style="gap: 12px; margin-top: 8px;">
            ${affected.map(item => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
                <div class="flex-between">
                  <div>
                    <span class="font-semibold text-sm">${escapeHtml(item.title)}</span>
                    <span class="badge badge-purple text-xs" style="margin-left: 4px;">${escapeHtml(item.item_kind)}</span>
                  </div>
                  <span class="badge ${item.suggestion === 'edit_required' ? 'badge-danger' : (item.suggestion === 'no_change' ? 'badge-teal' : 'badge-warning')}">
                    ${escapeHtml(item.suggestion.replace('_', ' '))}
                  </span>
                </div>
                <div class="text-xs text-muted" style="margin-top: 4px;">${escapeHtml(item.description)}</div>

                <!-- Decision Toggle Row -->
                <div class="flex-between" style="margin-top: 8px; padding-top: 6px; border-top: 1px dashed var(--color-border);">
                  <span class="text-xs text-muted">
                    Decision: <strong>${escapeHtml(item.user_decision || 'pending')}</strong>
                  </span>
                  <div class="flex-row" style="gap: 4px;">
                    <button class="btn btn-sm ${item.user_decision === 'confirmed' ? 'btn-primary' : 'btn-secondary'} btn-decision-confirm" style="font-size: 0.7rem; padding: 2px 8px;" type="button" ${isRejected ? 'disabled' : ''}>Confirm</button>
                    <button class="btn btn-sm ${item.user_decision === 'dismissed' ? 'btn-primary' : 'btn-secondary'} btn-decision-dismiss" style="font-size: 0.7rem; padding: 2px 8px;" type="button" ${isRejected ? 'disabled' : ''}>Dismiss</button>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>

          <!-- Regulatory Citations Accordion/List -->
          ${citations.length > 0 ? `
            <div style="margin-top: 20px; border-top: 1px solid var(--color-border); padding-top: 12px;">
              <div class="font-semibold text-xs text-muted" style="margin-bottom: 8px;">Supporting Regulatory Citations (${citations.length})</div>
              ${citations.map(c => `
                <div style="background: var(--color-bg-subtle); padding: 8px 10px; border-radius: var(--radius-sm); border: 1px solid var(--color-border); margin-bottom: 6px; font-size: 0.72rem;">
                  <div class="flex-between font-semibold">
                    <span style="color: var(--color-primary-blue);">21 CFR ${escapeHtml(c.section || '')}</span>
                    <span class="badge badge-blue text-xs">${escapeHtml(c.source || 'FDA')}</span>
                  </div>
                  <div class="text-muted" style="margin-top: 2px; font-style: italic;">"${escapeHtml(c.quote || '')}"</div>
                </div>
              `).join('')}
            </div>
          ` : ''}
        </div>

        <!-- Right: Side-by-side Revision Preview, Barcode Decision & Timeline -->
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Label Revision Preview</div>

          <!-- Side-by-side Comparison -->
          <div class="grid-two-col" style="gap: 12px; margin-top: 8px;">
            <!-- Current L2 -->
            <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px; background: #ffffff;">
              <div class="flex-between" style="margin-bottom: 8px;">
                <span class="badge badge-blue">Current L2</span>
              </div>
              <div class="text-xs font-semibold">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin: 4px 0;">Method: Ethylene oxide (EO)</div>
              <div style="border: 1px solid #334155; padding: 2px 4px; display: inline-block; font-size: 0.7rem; font-weight: 700; margin-top: 8px;">STERILE EO</div>
            </div>

            <!-- Draft L3 with DRAFT Watermark -->
            <div style="border: 2px dashed var(--color-draft-purple); border-radius: var(--radius-md); padding: 12px; background-color: var(--color-draft-purple-bg); position: relative;">
              <div class="flex-between" style="margin-bottom: 8px;">
                <span class="badge badge-purple">Draft L3</span>
                <span class="badge badge-draft">DRAFT</span>
              </div>
              <div class="text-xs font-semibold">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin: 4px 0;">Method: Gamma irradiation</div>
              <div style="border: 1px solid #334155; padding: 2px 4px; display: inline-block; font-size: 0.7rem; font-weight: 700; margin-top: 8px;">STERILE R</div>

              <div class="text-xs" style="color: var(--color-draft-purple); font-size: 0.68rem; margin-top: 10px; font-weight: 600;">
                Draft generated for review. Not a compliance determination.
              </div>
            </div>
          </div>

          <!-- Barcode Decision Section -->
          <div style="margin-top: 20px; background-color: var(--color-bg-subtle); padding: 12px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
            <div class="flex-between">
              <span class="font-semibold text-xs">Barcode Decision:</span>
              <span class="badge badge-teal">KEEP</span>
            </div>
            <div class="text-xs text-muted" style="margin-top: 4px;">
              Encoded data (GTIN, expiry, lot, serial) does not change, so the barcode payload is kept intact.
            </div>
          </div>

          <!-- Change Timeline Stepper -->
          <div style="margin-top: 24px;">
            <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Change Lifecycle Timeline:</div>
            <div class="timeline-stepper">
              <div class="timeline-step ${!isConfirmed ? 'active' : ''}">
                <div class="timeline-dot"></div>
                <span>Draft</span>
              </div>
              <div class="timeline-line"></div>
              <div class="timeline-step ${isConfirmed ? 'active' : ''}">
                <div class="timeline-dot"></div>
                <span>Checked</span>
              </div>
              <div class="timeline-line"></div>
              <div class="timeline-step">
                <div class="timeline-dot"></div>
                <span>Reviewed</span>
              </div>
              <div class="timeline-line"></div>
              <div class="timeline-step">
                <div class="timeline-dot"></div>
                <span>Published</span>
              </div>
            </div>
          </div>

          <!-- Action buttons footer -->
          <div class="flex-between" style="margin-top: 24px; padding-top: 12px; border-top: 1px solid var(--color-border);">
            <button class="btn btn-secondary btn-sm" type="button" id="btnGoToEvidence">View Evidence &rarr;</button>
            <div class="flex-row" style="gap: 8px;">
              ${!isConfirmed ? `
                <button class="btn btn-primary btn-sm" type="button" id="btnConfirmChecklist" ${isRejected ? 'disabled' : ''}>Confirm All Items</button>
              ` : `
                <button class="btn btn-primary btn-sm" type="button" id="btnGenerateDraftArtwork" ${isRejected ? 'disabled' : ''}>Generate Draft Artwork &rarr;</button>
              `}
            </div>
          </div>
        </div>
      </div>
    `;

    // Interactivity bindings
    const evidenceBtn = container.querySelector('#btnGoToEvidence');
    if (evidenceBtn) {
      evidenceBtn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
          detail: { screen: 'D5 Evidence' }
        }));
      });
    }

    const assessBtn = container.querySelector('#btnAssessChange');
    if (assessBtn) {
      assessBtn.addEventListener('click', async () => {
        const note = container.querySelector('#d6AssessNote');
        const field = container.querySelector('#changeField').value.trim();
        const value = container.querySelector('#changeNewVal').value.trim();
        const pid = (window.LabelLensData.CONFIG.ids || {}).product_id;
        if (!pid) { note.textContent = 'No live product yet: upload a label in Upload first (or open with ?product=...).'; return; }
        if (!field || !value) { note.textContent = 'Fill the target field and the new value.'; return; }
        note.textContent = 'Assessing...';
        try {
          const res = await window.LabelLensActions.assessChange(pid, [{ field, new_value: value }]);
          window.LabelLensData.setIds({ change_id: res.change.change_id });
          window.LabelLensData.setDataSource('api', 'assessChange');
          renderScreenD6(container, 'success (assessment)', { source: 'api' }, res);
        } catch (e) { note.textContent = 'Assess failed: ' + e.message; }
      });
    }

    // Per-item decisions (live only): remembered here, sent with "Confirm All Items".
    const decisions = {};
    const items = safeData.affected || [];
    container.querySelectorAll('.btn-decision-confirm').forEach((b, i) => b.addEventListener('click', () => {
      if (items[i]) decisions[items[i].impact_id] = 'confirmed';
      b.classList.add('btn-primary'); const o = b.nextElementSibling; if (o) o.classList.remove('btn-primary');
    }));
    container.querySelectorAll('.btn-decision-dismiss').forEach((b, i) => b.addEventListener('click', () => {
      if (items[i]) decisions[items[i].impact_id] = 'dismissed';
      b.classList.add('btn-primary'); const o = b.previousElementSibling; if (o) o.classList.remove('btn-primary');
    }));

    const confirmBtn = container.querySelector('#btnConfirmChecklist');
    if (confirmBtn) {
      confirmBtn.addEventListener('click', async () => {
        if (!apiMode) { gotoState('success (confirmed change)'); return; }
        const note = container.querySelector('#d6AssessNote');
        const changeId = (safeData.change || {}).change_id;
        if (!liveData || !changeId) { if (note) note.textContent = 'Assess a change first: this checklist is a mock sample.'; return; }
        const list = items.map(i => ({ impact_id: i.impact_id, user_decision: decisions[i.impact_id] || 'confirmed' }));
        if (note) note.textContent = 'Confirming...';
        try {
          const res = await window.LabelLensActions.confirmChange(changeId, list);
          renderScreenD6(container, 'success (confirmed change)', { source: 'api' }, res);
        } catch (e) { if (note) note.textContent = 'Confirm failed: ' + e.message; }
      });
    }

    const generateBtn = container.querySelector('#btnGenerateDraftArtwork');
    if (generateBtn) {
      generateBtn.addEventListener('click', async () => {
        if (window.LabelLensData.CONFIG.mode !== 'api') {
          gotoState('success (draft artwork)');
          return;
        }
        const override = window.LabelLensData.CONFIG.ids || {};
        const changeId = override.change_id || (safeData.change || {}).change_id;
        const labelId = override.label_id || ((safeData.affected || [])[0] || {}).label_id;
        let note = container.querySelector('#d6GenNote');
        if (!note) {
          generateBtn.parentElement.insertAdjacentHTML('afterend', '<div class="text-xs text-muted" id="d6GenNote" style="margin-top: 8px;"></div>');
          note = container.querySelector('#d6GenNote');
        }
        if (!changeId || !labelId) { note.textContent = 'This sample has no change id or label id.'; return; }
        generateBtn.disabled = true;
        note.textContent = 'Generating the draft (the API plans first, then renders a job)...';
        try {
          const artwork = await window.LabelLensActions.generate(changeId, labelId, (j) => renderScreenD6(container, 'loading', null, j));
          // Later screens (review, export, print check) now point at the version that was just generated.
          window.LabelLensData.CONFIG.ids = Object.assign({}, window.LabelLensData.CONFIG.ids, {
            version_id: artwork.version_id, label_id: artwork.label_id, artwork_id: artwork.artwork_id, change_id: artwork.change_id });
          renderScreenD6(container, 'success (draft artwork)', null, artwork);
        } catch (e) {
          renderScreenD6(container, state, meta, data);
          const n = container.querySelector('#btnGenerateDraftArtwork');
          if (n) n.parentElement.insertAdjacentHTML('afterend', '<div class="notice-banner notice-danger" data-testid="generate-error" style="margin-top: 10px;"><div class="notice-icon">!</div><div class="notice-text">' + escapeHtml(e.message) + '</div></div>');
        }
      });
    }
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D6 Changes'] = renderScreenD6;
  window.LabelLensRenderers['D6'] = renderScreenD6;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD6 };
  }
})();

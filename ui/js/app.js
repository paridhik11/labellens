/**
 * ui/js/app.js
 * Application logic for LabelLens static UI.
 * Connects navigation, views, and rendering of mock payloads.
 * 
 * Hard rules:
 * - Never invent data. All displayed values originate from mock payloads.
 * - Public medicine and professional device workspaces remain separate.
 * - Test identifiers labelled TEST.
 * - Drafts marked with DRAFT watermark and disclaimer.
 * - No em dashes.
 */

(function() {
  let activeModule = 'portal'; // 'portal', 'public', or 'professional'
  let activeScreen = 'D4 Inspect';

  function init() {
    setupNav();
    setupPortalCards();
    setupScreenListeners();

    // Default view: portal (two clear entry points)
    showModule('portal');
  }

  function setupNav() {
    const navPortal = document.getElementById('navPortal');
    const navPublic = document.getElementById('navPublic');
    const navProfessional = document.getElementById('navProfessional');

    if (navPortal) {
      navPortal.addEventListener('click', (e) => {
        e.preventDefault();
        showModule('portal');
      });
    }
    if (navPublic) {
      navPublic.addEventListener('click', (e) => {
        e.preventDefault();
        showModule('public', 'P2 Product information');
      });
    }
    if (navProfessional) {
      navProfessional.addEventListener('click', (e) => {
        e.preventDefault();
        showModule('professional', 'D4 Inspect');
      });
    }

    // Sidebar navigation in professional workspace
    const sidebarLinks = document.querySelectorAll('.sidebar-link[data-screen]');
    sidebarLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const screen = link.dataset.screen;
        switchProfessionalScreen(screen);
      });
    });

    // Public sub-tabs (P1, P2, P3)
    const publicTabs = document.querySelectorAll('.public-nav-btn[data-screen]');
    publicTabs.forEach(btn => {
      btn.addEventListener('click', () => {
        const screen = btn.dataset.screen;
        switchPublicScreen(screen);
      });
    });
  }

  function setupPortalCards() {
    const cardPublic = document.getElementById('portalEntryPublic');
    const cardProfessional = document.getElementById('portalEntryProfessional');

    if (cardPublic) {
      cardPublic.addEventListener('click', () => {
        showModule('public', 'P2 Product information');
      });
    }
    if (cardProfessional) {
      cardProfessional.addEventListener('click', () => {
        showModule('professional', 'D4 Inspect');
      });
    }
  }

  function setupScreenListeners() {
    // Listen for mock state changes dispatched by state-switcher.js
    window.addEventListener('labellens:state-changed', (e) => {
      const { screen, state, meta, data } = e.detail;
      renderScreenPayload(screen, state, meta, data);
    });

    // Listen for screen switch initiated from dev state switcher dropdown
    window.addEventListener('labellens:screen-navigated', (e) => {
      const screen = e.detail.screen;
      if (screen.startsWith('P')) {
        showModule('public', screen);
      } else {
        showModule('professional', screen);
      }
    });
  }

  function showModule(moduleName, targetScreen = null) {
    activeModule = moduleName;

    const portalView = document.getElementById('viewPortal');
    const publicView = document.getElementById('viewPublic');
    const professionalView = document.getElementById('viewProfessional');
    const userBadge = document.getElementById('headerUserBadge');

    const navPortal = document.getElementById('navPortal');
    const navPublic = document.getElementById('navPublic');
    const navProfessional = document.getElementById('navProfessional');

    // Reset active nav links
    [navPortal, navPublic, navProfessional].forEach(el => el && el.classList.remove('active'));

    // Hide all views
    if (portalView) portalView.classList.add('hidden');
    if (publicView) publicView.classList.add('hidden');
    if (professionalView) professionalView.classList.add('hidden');

    if (moduleName === 'portal') {
      if (portalView) portalView.classList.remove('hidden');
      if (navPortal) navPortal.classList.add('active');
      if (userBadge) userBadge.classList.add('hidden');
    } else if (moduleName === 'public') {
      if (publicView) publicView.classList.remove('hidden');
      if (navPublic) navPublic.classList.add('active');
      if (userBadge) userBadge.classList.add('hidden');
      const screen = targetScreen || 'P2 Product information';
      switchPublicScreen(screen);
    } else if (moduleName === 'professional') {
      if (professionalView) professionalView.classList.remove('hidden');
      if (navProfessional) navProfessional.classList.add('active');
      if (userBadge) userBadge.classList.remove('hidden');
      const screen = targetScreen || 'D4 Inspect';
      switchProfessionalScreen(screen);
    }
  }

  function switchPublicScreen(screenName) {
    activeScreen = screenName;

    // Update public nav tab styles
    const publicTabs = document.querySelectorAll('.public-nav-btn[data-screen]');
    publicTabs.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.screen === screenName);
    });

    // Notify state switcher to adapt its states
    if (window.LabelLensStateSwitcher) {
      window.LabelLensStateSwitcher.setScreen(screenName);
    } else {
      window.dispatchEvent(new CustomEvent('labellens:screen-changed', {
        detail: { screen: screenName }
      }));
    }
  }

  function switchProfessionalScreen(screenName) {
    activeScreen = screenName;

    // Update sidebar active link
    const sidebarLinks = document.querySelectorAll('.sidebar-link[data-screen]');
    sidebarLinks.forEach(link => {
      link.classList.toggle('active', link.dataset.screen === screenName);
    });

    // Notify state switcher to adapt its states
    if (window.LabelLensStateSwitcher) {
      window.LabelLensStateSwitcher.setScreen(screenName);
    } else {
      window.dispatchEvent(new CustomEvent('labellens:screen-changed', {
        detail: { screen: screenName }
      }));
    }
  }

  /**
   * Render screen payload into corresponding view.
   */
  function renderScreenPayload(screen, state, meta, data) {
    if (screen.startsWith('P')) {
      renderPublicPayload(screen, state, meta, data);
    } else {
      renderProfessionalPayload(screen, state, meta, data);
    }
  }

  /**
   * Public screens renderer: P1, P2, P3
   */
  function renderPublicPayload(screen, state, meta, data) {
    const container = document.getElementById('publicDynamicContent');
    if (!container) return;

    if (screen === 'P1 Scan and Understand') {
      if (state.includes('loading')) {
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 40px;">
            <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job ID: ${escapeHtml(data.job_id || 'job_0001')}</div>
            <h3>Scanning medication package...</h3>
            <p class="text-muted text-sm" style="margin-top: 8px;">Kind: ${escapeHtml(data.kind || 'public_scan')} | State: <strong>${escapeHtml(data.state || 'processing')}</strong></p>
            <div style="width: 240px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 20px auto; overflow: hidden;">
              <div style="width: 65%; height: 100%; background: var(--color-primary-teal);"></div>
            </div>
          </div>
        `;
      } else if (state.includes('failed')) {
        container.innerHTML = `
          <div class="notice-banner notice-danger">
            <div class="notice-icon">!</div>
            <div>
              <div class="notice-title">Scan failed</div>
              <div class="notice-text">${escapeHtml(data.error && data.error.message ? data.error.message : 'The image could not be processed. Please capture clear lighting with no glare.')}</div>
            </div>
          </div>
        `;
      } else {
        // Idle screen
        container.innerHTML = `
          <div style="text-align: center; max-width: 600px; margin: 0 auto 24px auto;">
            <h2>Understand your label</h2>
            <p class="text-muted text-sm" style="margin-top: 8px;">Scan or upload a photo to extract and explain key information from a medical product label.</p>
            <div class="flex-row" style="justify-content: center; gap: 12px; margin-top: 16px;">
              <button class="btn btn-primary" type="button">Use camera</button>
              <button class="btn btn-secondary" type="button">Upload image</button>
            </div>
          </div>

          <div class="viewfinder-card" style="max-width: 680px; margin: 0 auto;">
            <div class="viewfinder-reticle reticle-tl"></div>
            <div class="viewfinder-reticle reticle-tr"></div>
            <div class="viewfinder-reticle reticle-bl"></div>
            <div class="viewfinder-reticle reticle-br"></div>
            <div style="color: #94a3b8; text-align: center;">
              <div style="font-size: 2rem; margin-bottom: 8px;">📷</div>
              <div class="font-semibold text-sm">Align medication packaging within the frame</div>
              <div class="text-xs text-muted" style="margin-top: 4px;">Capture all sides if needed (front, back, and both sides).</div>
            </div>
          </div>
        `;
      }
      return;
    }

    if (screen === 'P2 Product information') {
      if (state === 'empty') {
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 48px;">
            <h3>No reference label found</h3>
            <p class="text-muted text-sm" style="margin-top: 8px;">We could not match this package against official FDA drug labels in 21 CFR 201, 208, or 211.</p>
            <div style="margin-top: 16px;">
              <button class="btn btn-secondary" onclick="switchPublicScreen('P1 Scan and Understand')">Scan another side</button>
            </div>
          </div>
        `;
        return;
      }

      if (state === 'needs_review') {
        const candidates = data.candidates || [];
        container.innerHTML = `
          <div class="notice-banner notice-warning">
            <div class="notice-icon">i</div>
            <div>
              <div class="notice-title">Multiple candidates found</div>
              <div class="notice-text">The scan matched more than one reference label. Please select the product packaging in your hand.</div>
            </div>
          </div>

          <div class="card">
            <h3>Candidate reference labels (${candidates.length})</h3>
            <div style="margin-top: 16px; display: flex; flex-direction: column; gap: 12px;">
              ${candidates.map(c => `
                <div class="card" style="border: 1px solid var(--color-border); padding: 14px; display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <div class="font-semibold">${escapeHtml(c.product_name)}</div>
                    <div class="text-xs text-muted">${escapeHtml(c.dosage_form)} | ${escapeHtml(c.manufacturer || '')}</div>
                  </div>
                  <div class="flex-row">
                    <span class="badge badge-teal">Match: ${Math.round((c.match_confidence || 0) * 100)}%</span>
                    <button class="btn btn-sm btn-primary">Select</button>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
        return;
      }

      // Normal Success State (Panel 2 from mockup)
      const cand = (data.candidates && data.candidates[0]) || {};
      const photoData = cand.read_from_photo || {};
      const refData = cand.from_reference_label || {};
      const sources = data.sources || [];

      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px; align-items: flex-start;">
          <div>
            <h2>Product information</h2>
            <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
              <span style="font-size: 1.1rem; font-weight: 700; color: var(--color-text-dark);">${escapeHtml(cand.product_name || 'ExampleMed 10 mg')}</span>
              <span class="badge badge-teal">Reference match found</span>
            </div>
            <div class="text-xs text-muted" style="margin-top: 2px;">${escapeHtml(cand.dosage_form || 'Film-coated tablets')} | ${escapeHtml(cand.active_substance || 'Example substance')}</div>
          </div>
          <div>
            <span class="text-xs text-muted">Confidence: <strong>${Math.round((cand.match_confidence || 0.94) * 100)}%</strong></span>
          </div>
        </div>

        <div class="tab-group">
          <button class="tab-btn active">Summary</button>
          <button class="tab-btn">Ingredients</button>
          <button class="tab-btn">Warnings</button>
          <button class="tab-btn">Sources</button>
        </div>

        <div class="grid-three-col">
          <!-- Card 1: Read from your photo -->
          <div class="card">
            <div class="card-header-clean flex-row">
              <span style="color: var(--color-primary-teal); font-weight: 700;">📷</span>
              <span class="font-semibold text-sm">Read from your photo</span>
            </div>
            <div class="kv-table">
              ${Object.entries(photoData).map(([k, v]) => `
                <div class="kv-row">
                  <span class="kv-label">${escapeHtml(k)}</span>
                  <span class="kv-value">${escapeHtml(String(v))}</span>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Card 2: From reference label -->
          <div class="card">
            <div class="card-header-clean flex-row">
              <span style="color: var(--color-primary-teal); font-weight: 700;">📄</span>
              <span class="font-semibold text-sm">From the reference label</span>
            </div>
            <div class="kv-table">
              ${Object.entries(refData).map(([k, v]) => `
                <div class="kv-row">
                  <span class="kv-label">${escapeHtml(k)}</span>
                  <span class="kv-value">${escapeHtml(String(v))}</span>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Card 3: Ask about this label teaser -->
          <div class="card">
            <div class="card-header-clean flex-row">
              <span style="color: var(--color-primary-teal); font-weight: 700;">💬</span>
              <span class="font-semibold text-sm">Ask about this label</span>
            </div>
            <div style="background-color: var(--color-bg-subtle); padding: 10px; border-radius: var(--radius-md); font-size: 0.85rem; margin-bottom: 12px;">
              ${escapeHtml(data.summary || 'ExampleMed 10 mg is a film-coated tablet containing an example substance. It is supplied in packs of 28 tablets.')}
            </div>
            ${sources.length > 0 ? `
              <div class="text-xs" style="margin-top: 8px;">
                <span class="font-semibold text-muted">Cited Regulatory Basis:</span>
                <div style="color: var(--color-text-dark); margin-top: 2px;">21 CFR ${escapeHtml(sources[0].section || '')} - ${escapeHtml(sources[0].title || '')}</div>
              </div>
            ` : ''}
            <div style="margin-top: 16px;">
              <button class="btn btn-sm btn-primary" style="width: 100%;" onclick="switchPublicScreen('P3 Ask about this label')">Ask questions about this medicine</button>
            </div>
          </div>
        </div>

        <div class="flex-between" style="margin-top: 24px;">
          <button class="btn btn-secondary btn-sm" onclick="switchPublicScreen('P1 Scan and Understand')">Scan another side</button>
          <a class="btn btn-primary btn-sm" href="${escapeHtml(cand.reference_label_url || '#')}" target="_blank">View reference source</a>
        </div>
      `;
      return;
    }

    if (screen === 'P3 Ask about this label') {
      const isAbstained = data.abstained === true;
      container.innerHTML = `
        <div class="card" style="max-width: 800px; margin: 0 auto;">
          <div class="card-header-clean flex-between">
            <div>
              <h3>Ask about this label</h3>
              <div class="text-xs text-muted">Questions are answered only using retrieved evidence from 21 CFR 201, 208, 211 and matched reference labels.</div>
            </div>
            <span class="badge badge-teal">Medicine Q&A</span>
          </div>

          <div style="margin: 16px 0;">
            <div class="flex-row" style="background: var(--color-bg-subtle); padding: 6px 12px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
              <input type="text" value="${isAbstained ? 'Can I give half of this tablet to my 5-year-old child?' : 'What is the required expiration date standard for this drug packaging?'}" style="flex: 1; border: none; background: transparent; outline: none; font-size: 0.9rem;" readonly>
              <button class="btn btn-sm btn-primary">Ask</button>
            </div>
          </div>

          ${isAbstained ? `
            <div class="notice-banner notice-warning" style="margin-top: 16px;">
              <div class="notice-icon">i</div>
              <div>
                <div class="notice-title">Abstained: ${escapeHtml(data.reason || 'out_of_scope')}</div>
                <div class="notice-text">${escapeHtml(data.message || 'I can only explain what the packaging label says.')}</div>
                <div class="text-xs font-mono" style="margin-top: 8px; opacity: 0.85;">
                  Rule: ${escapeHtml(data.score_name || 'rule')} | Score: ${data.score !== null ? data.score : 'null'} | Threshold: ${data.threshold !== null ? data.threshold : 'null'}
                </div>
              </div>
            </div>
          ` : `
            <div style="background-color: var(--color-primary-teal-subtle); border: 1px solid var(--color-primary-teal-light); border-radius: var(--radius-md); padding: 16px; margin-top: 16px;">
              <div class="font-semibold text-sm" style="color: var(--color-primary-teal); margin-bottom: 6px;">Answer backed by official evidence:</div>
              <div style="font-size: 0.925rem; line-height: 1.5; color: var(--color-text-dark);">${escapeHtml(data.answer || '')}</div>
              
              <div style="margin-top: 14px; border-top: 1px solid rgba(11, 125, 126, 0.2); padding-top: 10px;">
                <div class="text-xs font-semibold text-muted">Basis: ${escapeHtml(data.based_on || '21 CFR 211.137')}</div>
                ${(data.sources || []).map(s => `
                  <div class="text-xs" style="margin-top: 4px; color: var(--color-text-muted);">
                    <strong>${escapeHtml(s.section || '')} ${escapeHtml(s.title || '')}:</strong> 
                    <span style="font-style: italic;">"${escapeHtml(s.quote || '')}"</span>
                  </div>
                `).join('')}
              </div>
            </div>
          `}
        </div>
      `;
    }
  }

  /**
   * Professional screens renderer: D1 through D10
   */
  function renderProfessionalPayload(screen, state, meta, data) {
    const container = document.getElementById('professionalDynamicContent');
    if (!container) return;

    if (screen === 'D4 Inspect') {
      renderScreenD4(container, state, data);
    } else if (screen === 'D6 Changes') {
      renderScreenD6(container, state, data);
    } else if (screen === 'D1 Products') {
      renderScreenD1(container, state, data);
    } else {
      // General handler for D2, D3, D5, D7, D8, D9, D10
      renderGenericProfessionalScreen(container, screen, state, meta, data);
    }
  }

  /**
   * Screen D4: Inspect ("Label review", Mockup Panel 3)
   */
  function renderScreenD4(container, state, data) {
    const findings = data.findings || [];
    const criticalFinding = findings.find(f => f.severity === 'critical') || findings[0];

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Label review · Demo device</h2>
          <div class="flex-row" style="margin-top: 4px; gap: 8px;">
            <span class="text-xs text-muted">Version:</span>
            <span class="badge badge-blue">Product P1</span>
            <span class="badge badge-purple">Artwork L2</span>
          </div>
        </div>
        <div class="flex-row">
          <span class="badge ${data.passed ? 'badge-teal' : 'badge-danger'}">
            ${data.passed ? 'Passed Inspection' : 'Needs Review'}
          </span>
        </div>
      </div>

      <div class="grid-two-col">
        <!-- Left: Simulated Device Label with Bounding Box -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Device Label Artwork</span>
            <span class="badge badge-test">(01)00000000000000 [TEST]</span>
          </div>

          <div class="label-canvas-box" style="background: #ffffff; border: 2px solid #334155;">
            <div>
              <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin-top: 2px;">Sterile Medical Device | Single use only</div>
              <div class="flex-row" style="margin-top: 8px; gap: 12px;">
                <span style="border: 1px solid #0f172a; padding: 2px 6px; font-size: 0.75rem; font-weight: 700;">STERILE EO</span>
                <span style="border: 1px solid #0f172a; padding: 2px 6px; font-size: 0.75rem; font-weight: 700;">REF ED-100</span>
              </div>
            </div>

            <div style="margin: 20px 0;">
              <!-- Bounding Box Orange Reticle around Expiry -->
              <div class="label-bbox-highlight" style="display: inline-block;">
                <span class="text-xs font-semibold" style="color: #ea580c; display: block;">EXP 2028-04-30</span>
              </div>
            </div>

            <div>
              <div class="label-bbox-highlight" style="display: inline-block; padding: 6px;">
                <div class="font-mono text-xs font-semibold" style="letter-spacing: 2px;">|| | |||| | ||||| |||| |</div>
                <div class="font-mono text-xs" style="color: #64748b; margin-top: 2px;">(01)12345678901234 [TEST]</div>
              </div>
              <div class="text-xs text-muted" style="margin-top: 10px;">
                Example Devices Ltd | Sample City, Country
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Findings and Observed vs Reference -->
        <div class="flex-col" style="gap: 16px;">
          ${criticalFinding ? `
            <div class="notice-banner notice-danger" style="margin-bottom: 0;">
              <div class="notice-icon">!</div>
              <div style="flex: 1;">
                <div class="flex-between">
                  <span class="notice-title">${escapeHtml(criticalFinding.kind.replace('_', ' '))}</span>
                  <span class="badge badge-danger">Needs review</span>
                </div>
                <div class="notice-text" style="margin-top: 4px;">${escapeHtml(criticalFinding.message)}</div>
              </div>
            </div>

            <div class="card">
              <div class="card-header-clean font-semibold text-sm">Observed vs reference</div>
              <div class="kv-table">
                <div class="kv-row">
                  <span class="kv-label">Printed on label</span>
                  <span class="kv-value"><span class="badge badge-danger">${escapeHtml(criticalFinding.observed || '2028-04-30')}</span></span>
                </div>
                <div class="kv-row">
                  <span class="kv-label">From barcode (reference)</span>
                  <span class="kv-value"><span class="badge badge-danger">${escapeHtml(criticalFinding.expected || '2028-03-31')}</span></span>
                </div>
              </div>

              ${criticalFinding.citations && criticalFinding.citations.length > 0 ? `
                <div style="margin-top: 14px; background: var(--color-bg-subtle); padding: 10px; border-radius: var(--radius-md);">
                  <div class="text-xs font-semibold text-muted">Retrieved Regulatory Requirement:</div>
                  <div class="text-xs" style="margin-top: 2px;">21 CFR ${escapeHtml(criticalFinding.citations[0].section || '')} - ${escapeHtml(criticalFinding.citations[0].title || '')}</div>
                </div>
              ` : ''}
            </div>
          ` : `
            <div class="card" style="text-align: center; padding: 32px;">
              <div style="color: var(--color-success-text); font-size: 2rem;">✓</div>
              <div class="font-semibold" style="margin-top: 8px;">All label checks passed</div>
              <div class="text-xs text-muted" style="margin-top: 4px;">Extraction confirmed against 21 CFR 801 requirements.</div>
            </div>
          `}

          <div class="flex-between" style="margin-top: 8px;">
            <button class="btn btn-primary" type="button">Confirm extraction</button>
            <button class="btn btn-secondary" type="button">Export report</button>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Screen D6: Changes ("Change impact", Mockup Panel 4)
   */
  function renderScreenD6(container, state, data) {
    const change = data.change || {};
    const affected = data.affected || [];

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Change impact</h2>
          <div class="text-xs text-muted" style="margin-top: 2px;">Automated assessment of proposed label modifications across packaging hierarchy.</div>
        </div>
        <span class="badge badge-blue">Change ID: ${escapeHtml(change.change_id || 'chg_0002')}</span>
      </div>

      <!-- Proposed Change Hero Card -->
      <div class="card" style="margin-bottom: 20px; background-color: #f8fafc;">
        <div class="flex-row" style="gap: 12px;">
          <div style="background-color: var(--color-info-blue-bg); color: var(--color-info-blue-text); padding: 8px; border-radius: var(--radius-md); font-size: 1.25rem;">📄</div>
          <div>
            <div class="font-semibold text-sm">Proposed change: sterilization method</div>
            <div class="text-sm text-muted" style="margin-top: 2px;">${escapeHtml(change.raw_text || 'Update the sterilization method from ethylene oxide (EO) to gamma irradiation.')}</div>
          </div>
        </div>
      </div>

      <div class="grid-two-col">
        <!-- Left: Affected Items Checklist -->
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Affected items (${affected.length})</div>
          <div class="flex-col" style="gap: 10px;">
            ${affected.map(item => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <div class="font-semibold text-sm">${escapeHtml(item.title)}</div>
                  <div class="text-xs text-muted">${escapeHtml(item.description)}</div>
                </div>
                <div>
                  <span class="badge ${item.suggestion === 'edit_required' ? 'badge-danger' : (item.suggestion === 'no_change' ? 'badge-teal' : 'badge-warning')}">
                    ${escapeHtml(item.suggestion.replace('_', ' '))} &gt;
                  </span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Right: Side-by-side Revision Preview with DRAFT watermark -->
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Label revision preview</div>
          
          <div class="grid-two-col" style="gap: 12px;">
            <!-- Current L2 -->
            <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px;">
              <div class="flex-between" style="margin-bottom: 8px;">
                <span class="badge badge-blue">Current L2</span>
              </div>
              <div class="text-xs font-semibold">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin: 4px 0;">Sterilized using ethylene oxide (EO).</div>
              <div style="border: 1px solid #334155; padding: 2px 4px; display: inline-block; font-size: 0.7rem; font-weight: 700; margin-top: 8px;">STERILE EO</div>
            </div>

            <!-- Draft L3 with DRAFT mark -->
            <div style="border: 2px dashed var(--color-draft-purple); border-radius: var(--radius-md); padding: 12px; background-color: var(--color-draft-purple-bg); position: relative;">
              <div class="flex-between" style="margin-bottom: 8px;">
                <span class="badge badge-purple">Draft L3</span>
                <span class="badge badge-draft">DRAFT</span>
              </div>
              <div class="text-xs font-semibold">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin: 4px 0;">Sterilized using gamma irradiation.</div>
              <div style="border: 1px solid #334155; padding: 2px 4px; display: inline-block; font-size: 0.7rem; font-weight: 700; margin-top: 8px;">STERILE R</div>
              
              <div class="text-xs" style="color: var(--color-draft-purple); font-size: 0.68rem; margin-top: 10px; font-weight: 600;">
                Draft generated for review. Not a compliance determination.
              </div>
            </div>
          </div>

          <!-- Change Timeline -->
          <div style="margin-top: 24px;">
            <div class="text-xs font-semibold text-muted">Change timeline</div>
            <div class="timeline-stepper">
              <div class="timeline-step active">
                <div class="timeline-dot"></div>
                <span>Draft</span>
              </div>
              <div class="timeline-line"></div>
              <div class="timeline-step">
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

          <div class="flex-between" style="margin-top: 20px;">
            <button class="btn btn-secondary btn-sm" type="button">View evidence</button>
            <div>
              <button class="btn btn-primary btn-sm" type="button">Create review task</button>
              <div class="text-xs text-muted" style="margin-top: 2px; text-align: right;">Human approval before publication.</div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Screen D1: Products List
   */
  function renderScreenD1(container, state, data) {
    const products = data.items || [];
    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Products</h2>
          <div class="text-xs text-muted">Medical device product families and active label versions.</div>
        </div>
        <button class="btn btn-sm btn-primary">+ Register product</button>
      </div>

      ${products.length === 0 ? `
        <div class="card" style="text-align: center; padding: 48px;">
          <h3>No products registered yet</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Register your first medical device product family to manage label versions and templates.</p>
        </div>
      ` : `
        <div class="card">
          <div class="kv-table">
            ${products.map(p => `
              <div class="kv-row" style="padding: 12px 0;">
                <div>
                  <div class="font-semibold">${escapeHtml(p.name)}</div>
                  <div class="text-xs text-muted">ID: ${escapeHtml(p.product_id)} | Primary UDI-DI: <span class="badge badge-test">${escapeHtml(p.primary_di || '00000000000000 [TEST]')}</span></div>
                </div>
                <div class="flex-row">
                  <span class="badge badge-teal">${p.label_count || 1} labels</span>
                  <button class="btn btn-sm btn-secondary" onclick="switchProfessionalScreen('D4 Inspect')">Inspect</button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `}
    `;
  }

  /**
   * Generic Professional Renderer for D2, D3, D5, D7, D8, D9, D10
   */
  function renderGenericProfessionalScreen(container, screen, state, meta, data) {
    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>${escapeHtml(screen)}</h2>
          <div class="text-xs text-muted">Mock response contract: <code>${escapeHtml(meta.operationId || 'none')}</code></div>
        </div>
        <span class="badge badge-blue">State: ${escapeHtml(state)}</span>
      </div>

      <div class="card">
        <div class="card-header-clean flex-between">
          <span class="font-semibold text-sm">Response Payload (Schema: ${escapeHtml(meta.schema || 'Object')})</span>
          <span class="text-xs text-muted">File: <code>${escapeHtml(meta.file || '')}</code></span>
        </div>
        <pre class="font-mono text-xs" style="background: #0f172a; color: #38bdf8; padding: 16px; border-radius: var(--radius-md); overflow-x: auto; max-height: 480px;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>
      </div>
    `;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Initialize once loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

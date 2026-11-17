/**
 * ui/js/data.js
 * Central data loading module for LabelLens UI.
 * 
 * Hard rules:
 * - Never invent data. All mock representations come from src/api/mock/index.json.
 * - All screen data loading happens through loadScreen(screen, state).
 * - Keep public medicine and professional device workflows separate.
 * - No em dashes.
 */

const CONFIG = {
  mode: 'mock', // 'mock' or 'api'
  mockIndexUrl: '/src/api/mock/index.json',
  mockBaseUrl: '/src/api/mock/',
  apiBaseUrl: 'http://localhost:8000',
  currentUserHeader: 'usr_demo_editor'
};

const DEMO_BANNER_TEXT = 'DEMO MODE: Sample data for course evaluation. Not for clinical use.';
const PUBLIC_NOTICE_TEXT = 'Authenticity not verified. Based on a reference label match.';

// Cached mock index data
let mockIndexCache = null;

/**
 * Fetch and cache the mock index file.
 * Supports relative path fallbacks if served from nested directories.
 * @returns {Promise<Object>} Mock index object containing list of mocks.
 */
async function getMockIndex() {
  if (mockIndexCache) {
    return mockIndexCache;
  }
  const candidateUrls = [
    CONFIG.mockIndexUrl,
    '../../src/api/mock/index.json',
    '../src/api/mock/index.json',
    'src/api/mock/index.json'
  ];

  let lastError = null;
  for (const url of candidateUrls) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        mockIndexCache = await response.json();
        if (url.includes('src/api/mock/index.json')) {
          CONFIG.mockBaseUrl = url.replace('index.json', '');
        }
        return mockIndexCache;
      }
    } catch (err) {
      lastError = err;
    }
  }

  console.error('Error fetching mock index from candidates', candidateUrls, lastError);
  throw lastError || new Error('Failed to load mock index.');
}

/**
 * Normalize screen string to match index.json screens.
 * Accepts: 'D4', 'D4 Inspect', 'P2', 'P2 Product information', etc.
 * @param {string} screenInput
 * @returns {string} Normalized screen name in index.json
 */
function normalizeScreenName(screenInput) {
  if (!screenInput) return '';
  const trimmed = screenInput.trim();
  const index = mockIndexCache;
  if (!index || !index.mocks) return trimmed;

  // Exact match
  const exact = index.mocks.find(m => m.screen.toLowerCase() === trimmed.toLowerCase());
  if (exact) return exact.screen;

  // Prefix match like 'D4' matching 'D4 Inspect' or 'P2' matching 'P2 Product information'
  const prefixMatch = index.mocks.find(m => {
    const parts = m.screen.split(' ');
    return parts[0].toLowerCase() === trimmed.toLowerCase();
  });
  if (prefixMatch) return prefixMatch.screen;

  return trimmed;
}

/**
 * Query all available mock states and variants for a specific screen.
 * Used by the state switcher to show ONLY states that exist for this screen.
 * @param {string} screen
 * @returns {Promise<Array<Object>>} Array of available state items with metadata.
 */
async function getStatesForScreen(screen) {
  const index = await getMockIndex();
  const screenName = normalizeScreenName(screen);

  const matched = index.mocks.filter(m => m.screen === screenName);

  // Derive human-readable labels for state variants
  const items = matched.map((item, idx) => {
    let label = item.state;
    const filepath = item.file || '';
    const filename = filepath.split('/').pop().replace('.json', '');

    // Clarify distinct variants with the same base state
    if (filepath.includes('extraction_needs_review')) {
      label = 'needs_review (extraction)';
    } else if (filepath.includes('extraction_success')) {
      label = 'success (extraction)';
    } else if (filepath.includes('extraction_confirmed')) {
      label = 'success (confirmed extraction)';
    } else if (filepath.includes('recheck_failed_check')) {
      label = 'failed_check (recheck)';
    } else if (filepath.includes('recheck_success')) {
      label = 'success (recheck)';
    } else if (filepath.includes('failed_check')) {
      label = 'failed_check';
    } else if (filepath.includes('abstained_out_of_scope')) {
      label = 'abstained (out of scope)';
    } else if (filepath.includes('abstained_low_confidence')) {
      label = 'abstained (low confidence)';
    } else if (filepath.includes('abstained_no_evidence')) {
      label = 'abstained (no evidence)';
    } else if (filepath.includes('abstained_needs_human_check')) {
      label = 'abstained (needs human check)';
    } else if (filepath.includes('assess_needs_review')) {
      label = 'needs_review (assessment)';
    } else if (filepath.includes('assess_success')) {
      label = 'success (assessment)';
    } else if (filepath.includes('confirm_success')) {
      label = 'success (confirmed change)';
    } else if (filepath.includes('affected_success')) {
      label = 'success (affected labels)';
    } else if (filepath.includes('generate_needs_input')) {
      label = 'needs_review (needs input)';
    } else if (filepath.includes('generate_loading')) {
      label = 'loading (generate)';
    } else if (filepath.includes('generated_success')) {
      label = 'success (draft artwork)';
    } else if (filepath.includes('change_returned')) {
      label = 'returned (change)';
    } else if (filepath.includes('change_rejected')) {
      label = 'rejected (change)';
    } else if (filepath.includes('self_approval_forbidden')) {
      label = 'failed (self approval forbidden)';
    } else if (filepath.includes('history/success')) {
      label = 'success (audit)';
    } else if (filepath.includes('label_versions')) {
      label = 'success (label versions)';
    } else if (filepath.includes('product_detail')) {
      label = 'success (product detail)';
    } else if (filepath.includes('publish_success')) {
      label = 'success (published)';
    } else if (filepath.includes('export/draft')) {
      label = 'success (draft export)';
    } else if (filepath.includes('export/approved')) {
      label = 'approved (export)';
    } else if (filepath.includes('review/approved')) {
      label = 'approved (review)';
    } else if (filepath.includes('review/returned')) {
      label = 'returned (review)';
    }

    return {
      screen: item.screen,
      state: item.state,
      label: label,
      file: item.file,
      operationId: item.operationId,
      status: item.status,
      schema: item.schema,
      id: `${item.state}_${filename}_${idx}`
    };
  });

  // Handle special case for P1 Scan and Understand idle empty state (per SCREENS.md: no request yet)
  if (screenName === 'P1 Scan and Understand') {
    items.unshift({
      screen: screenName,
      state: 'empty',
      label: 'empty (idle)',
      file: null,
      operationId: 'none',
      status: 200,
      schema: 'none',
      id: 'empty_idle'
    });
  }

  return items;
}

/**
 * Load mock data or live API data for a screen in a given state.
 * 
 * @param {string} screen - Name or code of the screen (e.g. 'D4 Inspect', 'P2')
 * @param {string} state - Desired state or label (e.g. 'success', 'failed_check', 'needs_review', etc.)
 * @param {Object} [options] - Optional filters like specific file or operationId
 * @returns {Promise<Object>} Object containing screen metadata, mock payload, and HTTP status.
 */
async function loadScreen(screen, state, options = {}) {
  if (CONFIG.mode === 'mock') {
    const index = await getMockIndex();
    const screenName = normalizeScreenName(screen);

    // Look for exact file match if passed in options
    if (options.file) {
      const match = index.mocks.find(m => m.file === options.file);
      if (match) {
        const payload = await fetchMockPayload(match);
        if (options.label) {
          payload.label = options.label;
        } else if (state) {
          payload.label = state;
        }
        return payload;
      }
    }

    // Special case: P1 idle empty state
    if (screenName === 'P1 Scan and Understand' && state === 'empty') {
      return {
        screen: screenName,
        state: 'empty',
        file: null,
        status: 200,
        operationId: 'none',
        schema: 'none',
        data: { message: 'Idle scan screen. Ready to capture or upload.' }
      };
    }

    const available = await getStatesForScreen(screenName);

    // Find best match by label or state
    let target = available.find(item => item.label.toLowerCase() === state.toLowerCase());
    if (!target) {
      target = available.find(item => item.state.toLowerCase() === state.toLowerCase());
    }
    if (!target) {
      // Partial search
      target = available.find(item => item.label.toLowerCase().includes(state.toLowerCase()) || 
                                      (item.file && item.file.toLowerCase().includes(state.toLowerCase())));
    }

    if (!target) {
      console.warn(`No mock found for screen "${screenName}" with state "${state}". Falling back to first available.`);
      target = available[0];
    }

    if (!target || !target.file) {
      return {
        screen: screenName,
        state: state,
        file: null,
        status: 200,
        data: null
      };
    }

    return fetchMockPayload(target);

  } else if (CONFIG.mode === 'api') {
    // API mode placeholder
    console.warn('API mode is not yet connected to the backend. Set CONFIG.mode = "mock" to use mock contracts.');
    throw new Error('API mode not implemented yet. Please switch CONFIG.mode to "mock".');
  } else {
    throw new Error(`Unsupported mode in CONFIG.mode: ${CONFIG.mode}`);
  }
}

/**
 * Helper to fetch a single mock JSON file.
 * @param {Object} mockEntry - Mock metadata entry
 * @returns {Promise<Object>}
 */
async function fetchMockPayload(mockEntry) {
  const url = `${CONFIG.mockBaseUrl}${mockEntry.file}`;
  try {
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to fetch mock file ${url}: ${res.status}`);
    }
    const jsonData = await res.json();
    return {
      screen: mockEntry.screen,
      state: mockEntry.state,
      label: mockEntry.label || mockEntry.state,
      file: mockEntry.file,
      status: mockEntry.status,
      operationId: mockEntry.operationId,
      schema: mockEntry.schema,
      data: jsonData
    };
  } catch (err) {
    console.error(`Error loading mock payload from ${url}:`, err);
    throw err;
  }
}

/**
 * Safe HTML escaping helper.
 * @param {*} str
 * @returns {string} Escaped HTML string
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Checks if a value or object represents a test identifier.
 * Matches test_data: true or all-zero placeholder (00000000000000).
 * @param {*} val
 * @returns {boolean}
 */
function isTestIdentifier(val) {
  if (val === null || val === undefined) return false;
  if (typeof val === 'string') {
    return val.includes('00000000000000') || val === 'test_data';
  }
  if (typeof val === 'object') {
    if (val.test_data === true) return true;
    for (const k of Object.keys(val)) {
      if (typeof val[k] === 'string' && val[k].includes('00000000000000')) {
        return true;
      }
    }
  }
  return false;
}

/**
 * Renders a visible TEST badge when item is test data or contains test placeholder.
 * @param {*} val
 * @returns {string} HTML badge or empty string
 */
function renderTestBadge(val) {
  if (isTestIdentifier(val)) {
    return '<span class="badge badge-test">[TEST]</span>';
  }
  return '';
}

// Attach to window for global access
window.LabelLensData = {
  CONFIG,
  DEMO_BANNER_TEXT,
  PUBLIC_NOTICE_TEXT,
  escapeHtml,
  isTestIdentifier,
  renderTestBadge,
  getMockIndex,
  getStatesForScreen,
  loadScreen,
  normalizeScreenName
};

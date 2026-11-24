// Checks ui/js/ask-panel.js without a browser: abstain text, folded low-confidence passages, label citation titles.
const fs = require('fs');
const path = require('path');
global.window = { LabelLensData: { escapeHtml: (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;') } };
eval(fs.readFileSync(path.join(__dirname, '..', 'js', 'ask-panel.js'), 'utf8'));
const ask = global.window.LabelLensAsk;
const labelSource = { source_type: 'label_section', chunk_id: 'c1', source: 'DailyMed', section: 'dosage/42229-5/7', title: 'Metoprolol Tartrate: 2.1 Hypertension', url: 'https://dailymed.nlm.nih.gov/x', quote: 'Take with food.' };
const failures = [];
const check = (name, ok) => { if (!ok) failures.push(name); };

const gated = ask.answerHtml({ abstained: true, reason: 'needs_human_check', message: 'This label does not seem to answer that.', score_name: 'e5b_top_score', score: 0.0164, threshold: 0.02, sources: [labelSource] });
check('gate message shown', gated.includes('This label does not seem to answer that.'));
check('no language model text', !/language model/i.test(gated));
check('passages folded in a closed details', /<details[^>]*>/.test(gated) && !/<details[^>]*open/.test(gated));
check('toggle text', gated.includes('Show closest passages (low confidence)'));
check('label section title', gated.includes('Label section: 2.1 Hypertension'));
check('no 21 CFR prefix on label sections', !gated.includes('21 CFR'));
check('view in label action', gated.includes('View in label') && !gated.includes('View regulation'));

const above = ask.answerHtml({ abstained: true, reason: 'needs_human_check', message: 'No language model is running, so only the closest passages are shown.', score: 0.032, threshold: 0.02, sources: [labelSource] });
check('above gate passages not folded', !above.includes('<details'));

const reg = ask.sourcesHtml([{ source_type: 'cfr', chunk_id: 'r1', source: 'eCFR', section: '201.57', title: 'Specific requirements', url: 'https://ecfr.gov/x', quote: 'q' }]);
check('regulation keeps 21 CFR and View regulation', reg.includes('21 CFR 201.57') && reg.includes('View regulation') && !reg.includes('View in label'));

if (failures.length) { console.log('FAIL: ' + failures.join('; ')); process.exit(1); }
console.log('ask-panel checks: all passed');

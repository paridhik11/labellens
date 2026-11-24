// Checks ui/js/ask-panel.js without a browser: abstain text, folded low-confidence passages, label citation titles.
const fs = require('fs');
const path = require('path');
global.window = { LabelLensData: { escapeHtml: (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;') } };
eval(fs.readFileSync(path.join(__dirname, '..', 'js', 'ask-panel.js'), 'utf8'));
const ask = global.window.LabelLensAsk;
const labelSource = { source_type: 'label_section', chunk_id: 'c1', source: 'DailyMed', section: 'dosage/42229-5/7', title: 'Metoprolol Tartrate: 2.1 Hypertension', url: 'https://dailymed.nlm.nih.gov/x', quote: 'Take with food.' };
const failures = [];
const check = (name, ok) => { if (!ok) failures.push(name); };

const NOMATCH = /This label doesn(?:'|&#39;)t seem to answer that\./;
const gated = ask.answerHtml({ abstained: true, reason: 'needs_human_check', message: "This label doesn't seem to answer that.", score_name: 'e5b_top_score', score: 0.0164, threshold: 0.02, sources: [labelSource] });
check('gate miss headline', NOMATCH.test(gated));
check('gate kind', ask.abstainKind({ reason: 'needs_human_check', score: 0.0164, threshold: 0.02, sources: [labelSource] }) === 'gate');
check('no language model text', !/language model/i.test(gated));
check('no Abstained word', !/Abstained/.test(gated));
check('passages folded in a closed details', /<details[^>]*>/.test(gated) && !/<details[^>]*open/.test(gated));
check('toggle text', gated.includes('Show closest passages (low confidence)'));
check('label section title', gated.includes('Label section: 2.1 Hypertension'));
check('no 21 CFR prefix on label sections', !gated.includes('21 CFR'));
check('view in label action', gated.includes('View in label') && !gated.includes('View regulation'));
check('score only in the details line', /data-testid="answer-details"[^>]*>Details: e5b_top_score 0\.0164, gate 0\.0200/.test(gated));

// model off, score above the label gate (the metoprolol "how to store it" case): passages, never "Abstained"
const above = ask.answerHtml({ abstained: true, reason: 'needs_human_check', message: 'No language model is running, so only the closest passages are shown.', score_name: 'e5b_top_score', score: 0.0328, threshold: 0.02, sources: [labelSource] });
check('above gate passages not folded', !above.includes('<details'));
check('above gate headline', above.includes('Closest passages from the label'));
check('above gate no Abstained', !/Abstained/.test(above) && !NOMATCH.test(above));
check('above gate kind', ask.abstainKind({ reason: 'needs_human_check', score: 0.0328, threshold: 0.02, sources: [labelSource] }) === 'passages');
check('above gate score small', /Details: e5b_top_score 0\.0328/.test(above));

// curated product: no gate (threshold null), model off: passages
const curated = ask.answerHtml({ abstained: true, reason: 'needs_human_check', score_name: 'e5b_top_score', score: 0.012, threshold: null, sources: [labelSource] });
check('curated no gate shows passages', curated.includes('Closest passages from the label') && !/Abstained/.test(curated));

// regulation passages with the model off
const regOff = ask.answerHtml({ abstained: true, reason: 'needs_human_check', score_name: 'e5b_top_score', score: 0.04, threshold: 0.0315, sources: [{ source_type: 'cfr', chunk_id: 'r1', source: 'eCFR', section: '801.18', title: 'Format of dates', quote: 'q' }] });
check('regulation passages headline', regOff.includes('Closest regulation passages'));

// scope rule
const scope = ask.answerHtml({ abstained: true, reason: 'out_of_scope', score_name: 'scope_rule', score: null, threshold: null, message: 'I can only explain what the regulation text says.' });
check('scope message', scope.includes('I can only explain') && !/Abstained/.test(scope));

const reg = ask.sourcesHtml([{ source_type: 'cfr', chunk_id: 'r1', source: 'eCFR', section: '201.57', title: 'Specific requirements', url: 'https://ecfr.gov/x', quote: 'q' }]);
check('regulation keeps 21 CFR and View regulation', reg.includes('21 CFR 201.57') && reg.includes('View regulation') && !reg.includes('View in label'));

if (failures.length) { console.log('FAIL: ' + failures.join('; ')); process.exit(1); }
console.log('ask-panel checks: all passed');

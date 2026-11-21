# ruff: noqa: E501  (one HTML string; its lines are not wrapped)
"""One small static HTML page for the public medicine mode (Step 25a). No build step, no external files.

It calls two API operations: matchMedicine (name to reference product) and askPublic (question answered from that
product's chunks). Text from the API is inserted with textContent, never as HTML.
"""

MEDICINE_PAGE = """<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width'>
<title>Medicine information</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:50rem;margin:2rem auto;padding:0 1rem;color:#1b1f23}
input{font:inherit;padding:.4rem;width:70%}button{font:inherit;padding:.4rem .8rem}
.banner{background:#fff7e0;border:1px solid #e3c766;padding:.6rem .9rem;border-radius:6px;margin:1rem 0}
blockquote{margin:.4rem 0;padding-left:.8rem;border-left:3px solid #c9d1d9;color:#444}
dt{font-weight:600;margin-top:.5rem}dd{margin:0}.muted{color:#666}h2{font-size:1.1rem;margin-top:1.5rem}</style>
<body><h1>Medicine information</h1>
<div class=banner>Authenticity not verified. Based on a reference label match. This is not medical advice.</div>
<p>Type the product name as printed on the pack. Only 30 reference labels are loaded.</p>
<form id=f><input id=name placeholder="for example: Childrens Ibuprofen" required> <button>Find reference label</button></form>
<div id=out></div>
<script>
const out=document.getElementById('out');
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e}
function passages(title,items){if(!items||!items.length)return;out.append(el('h2',title));
 for(const p of items){const b=el('blockquote',p.quote);b.append(el('div',p.title+' ('+p.chunk_id+')','muted'));out.append(b)}}
document.getElementById('f').onsubmit=async ev=>{ev.preventDefault();out.replaceChildren(el('p','Looking ...'));
 const r=await fetch('/public/match',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({product_name:document.getElementById('name').value})});
 const d=await r.json();out.replaceChildren();
 if(!r.ok){out.append(el('p',d.message||'Something went wrong'));return}
 if(!d.candidates.length){out.append(el('p',d.message));out.append(el('p','Score '+d.score+' is below the threshold '+d.threshold,'muted'));return}
 const c=d.candidates[0];out.append(el('h2',c.product_name+' ('+d.outcome.replace('_',' ')+', confidence '+c.match_confidence.toFixed(2)+')'));
 const dl=el('dl');for(const [k,v] of Object.entries(c.from_reference_label)){dl.append(el('dt',k));dl.append(el('dd',v))}
 if(c.not_in_corpus.length){dl.append(el('dt','Not in the reference text'));dl.append(el('dd',c.not_in_corpus.join(', ')))}
 out.append(dl);const s=d.sections;passages('Summary',s.summary);passages('Ingredients',s.ingredients);
 passages('Warnings',s.warnings);
 out.append(el('h2','Sources'));for(const x of s.sources){const a=el('a',x.url);a.href=x.url;out.append(a)}
 const q=el('form');q.append(el('h2','Ask about this product'));
 const qi=el('input');qi.placeholder='for example: what are the warnings';qi.required=true;q.append(qi);
 q.append(el('button','Ask'));const ans=el('div');q.append(ans);out.append(q);
 q.onsubmit=async e2=>{e2.preventDefault();ans.replaceChildren(el('p','Looking ...'));
  const rr=await fetch('/public/ask',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({question:qi.value,product_id:c.product_id})});const a=await rr.json();ans.replaceChildren();
  ans.append(el('p',a.abstained?a.message:a.answer));for(const p of (a.sources||[])){const b=el('blockquote',p.quote);b.append(el('div',p.title,'muted'));ans.append(b)}}
};
</script></body></html>"""

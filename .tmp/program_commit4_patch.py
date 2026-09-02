from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

repls = []

old = "var APP_BUILD = '2026-09-02·sha:program-base-v1';"
new = "var APP_BUILD = '2026-09-02·sha:program-outings-readonly-v1';"
repls.append((old, new, 'APP_BUILD'))

marker = "\nfunction renderProgramScreen(){\n"
helpers = r'''
function _programOutingDestinationLabel(o){
  o=o||{};
  var labels=Array.isArray(o.visitLabels) ? o.visitLabels.filter(Boolean) : [];
  if(labels.length) return labels.join(' + ');
  return 'Destination à préciser';
}
function _programOutingParticipantsLabel(o){
  if(o && o.participants===null) return 'Tout le groupe';
  var count=(o && Array.isArray(o.participants)) ? o.participants.length : 0;
  if(!count) return 'Sous-groupe · à préciser';
  return 'Sous-groupe · '+count+' voyageur'+(count>1?'s':'');
}
function _programRenderOutingCard(slot){
  if(!slot || !slot.outing) return '';
  var o=slot.outing;
  var destination=_programOutingDestinationLabel(o);
  var mode=o.primaryTransportMode || 'Transport à préciser';
  var acts=Array.isArray(slot.activities) ? slot.activities : [];
  return '<div style="position:relative;margin-top:12px;padding-left:18px">'
    +'<div aria-hidden="true" style="position:absolute;left:4px;top:-10px;bottom:18px;width:1px;background:rgba(45,106,79,.22)"></div>'
    +'<div aria-hidden="true" style="position:absolute;left:4px;top:22px;width:10px;height:1px;background:rgba(45,106,79,.22)"></div>'
    +'<div class="info-card" style="padding:14px 15px;background:var(--accent-pale);border:1px solid rgba(45,106,79,.12)">'
      +'<div style="display:flex;align-items:center;gap:8px;min-width:0">'
        +'<span style="display:flex;align-items:center;justify-content:center;flex:0 0 27px;width:27px;height:27px;border-radius:50%;background:rgba(45,106,79,.10);color:var(--accent-deep)">'+svgIcon('arrow-left-right',14)+'</span>'
        +'<div style="min-width:0;flex:1;font-size:15px;font-weight:700;color:var(--ink);line-height:1.25">Excursion · '+escHtml(destination)+'</div>'
      +'</div>'
      +'<div style="font-size:11.5px;color:var(--ink-muted);margin:7px 0 0 35px">'+escHtml(mode)+' · Aller-retour</div>'
      +'<div style="font-size:11.5px;color:var(--ink-muted);margin:3px 0 0 35px">'+escHtml(_programOutingParticipantsLabel(o))+'</div>'
      +(acts.length?'<div style="margin:11px 0 0 35px">'+acts.map(_programActivityRow).join('')+'</div>':'')
    +'</div>'
  +'</div>';
}
function _programRenderOutings(day){
  var outings=(day && Array.isArray(day.outings)) ? day.outings : [];
  if(!outings.length) return '';
  return '<div style="margin-top:12px">'+outings.map(_programRenderOutingCard).join('')+'</div>';
}
'''
repls.append((marker, '\n'+helpers+marker, 'Programme outing helpers'))

old = "      +_programRenderBase(programDay)\n      +'<div style=\"font-size:11.5px;color:var(--ink-subtle);text-align:center;margin-top:18px\">Excursions, autres activités et déplacements — commits suivants</div>'"
new = "      +_programRenderBase(programDay)\n      +_programRenderOutings(programDay)\n      +'<div style=\"font-size:11.5px;color:var(--ink-subtle);text-align:center;margin-top:18px\">Autres activités et déplacements — commits suivants</div>'"
repls.append((old, new, 'Programme outing rendering'))

for old, new, label in repls:
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {n}')
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Programme commit 4 patch applied successfully')

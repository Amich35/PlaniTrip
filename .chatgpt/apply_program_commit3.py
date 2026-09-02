from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: expected 1 match, got {c}')
    s=s.replace(old,new,1)

replace_once("var APP_BUILD = '2026-09-02·sha:program-shell-v1';","var APP_BUILD = '2026-09-02·sha:program-base-v1';",'APP_BUILD')

anchor = "function renderProgramScreen(){\n  var dates=_programTripDates();"
helpers = r'''function _programActivityRow(item){
  if(!item) return '';
  var t=(S.actTimeStart&&S.actTimeStart[item.actKey]) || (S.actTime&&S.actTime[item.actKey]) || '';
  return '<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-top:1px solid rgba(29,29,31,.06)">'
    +(t?'<div style="flex:0 0 42px;font-size:11px;font-weight:600;color:var(--ink-muted);padding-top:1px">'+escHtml(t)+'</div>':'<div style="flex:0 0 8px"></div>')
    +'<div style="min-width:0;flex:1;font-size:13.5px;font-weight:600;color:var(--ink);line-height:1.35">'+escHtml(item.title||'Activité')+'</div>'
  +'</div>';
}
function _programActivitiesBlock(title,items){
  if(!items || !items.length) return '';
  return '<div class="info-card" style="padding:12px 16px;margin-top:10px">'
    +'<div style="font-size:11px;font-weight:700;color:var(--ink-muted);letter-spacing:.04em;text-transform:uppercase;padding-bottom:4px">'+escHtml(title)+'</div>'
    +items.map(_programActivityRow).join('')
  +'</div>';
}
function _programRenderBase(day){
  if(!day || !day.base) return '';
  var b=day.base;
  var tonight=b.tonightCity;
  var from=b.transitionFromCity;

  if(b.confidence==='transition' && tonight && from){
    var fromActs=(day.otherActivities||[]).filter(function(a){ return a.ck===from.ck; });
    var toActs=(day.baseActivities||[]).filter(function(a){ return a.ck===tonight.ck; });
    return '<div class="info-card" style="padding:16px;margin-top:2px">'
      +'<div style="display:flex;align-items:center;gap:8px;color:var(--ink)"><span style="font-size:20px;font-weight:750;letter-spacing:-.35px">'+escHtml(from.label)+'</span><span style="color:var(--ink-subtle)">'+svgIcon('arrow-right',16)+'</span><span style="font-size:20px;font-weight:750;letter-spacing:-.35px">'+escHtml(tonight.label)+'</span></div>'
      +'<div style="font-size:12px;color:var(--ink-muted);margin-top:4px">Journée de transition · Nuit à '+escHtml(tonight.label)+'</div>'
      +(fromActs.length?'<div style="margin-top:12px"><div style="font-size:11px;font-weight:700;color:var(--ink-muted);letter-spacing:.04em;text-transform:uppercase">'+escHtml(from.label)+'</div>'+fromActs.map(_programActivityRow).join('')+'</div>':'')
      +(toActs.length?'<div style="margin-top:12px"><div style="font-size:11px;font-weight:700;color:var(--ink-muted);letter-spacing:.04em;text-transform:uppercase">'+escHtml(tonight.label)+'</div>'+toActs.map(_programActivityRow).join('')+'</div>':'')
    +'</div>';
  }

  if(tonight && (b.confidence==='strict' || b.confidence==='ambiguous')){
    var baseCard='<div class="info-card" style="padding:16px;margin-top:2px">'
      +'<div style="font-size:22px;font-weight:750;letter-spacing:-.4px;color:var(--ink)">'+escHtml(tonight.label)+'</div>'
      +'<div style="display:flex;align-items:center;gap:5px;font-size:12px;color:var(--ink-muted);margin-top:4px">'+svgIcon('bed',13)+' Base · nuit'+(b.confidence==='ambiguous'?' · à confirmer':'')+'</div>'
    +'</div>';
    return baseCard+_programActivitiesBlock('Activités à '+tonight.label,day.baseActivities||[]);
  }

  return '<div class="info-card" style="padding:16px;margin-top:2px">'
    +'<div style="font-size:18px;font-weight:700;color:var(--ink)">Base à préciser</div>'
    +'<div style="font-size:12px;color:var(--ink-muted);margin-top:4px">Aucune ville de nuit fiable pour cette date.</div>'
  +'</div>';
}

function renderProgramScreen(){
  var dates=_programTripDates();'''
replace_once(anchor,helpers,'program render helper insertion')

old = "  var selected=new Date(programDate+'T12:00:00');\n  var selectedLabel=selected.toLocaleDateString('fr-FR',{weekday:'long',day:'numeric',month:'long',year:'numeric'});\n  selectedLabel=selectedLabel.charAt(0).toUpperCase()+selectedLabel.slice(1);"
new = old + "\n  var programDay=buildProgramDay(programDate);"
replace_once(old,new,'program day build')

old_placeholder = "    +'<div id=\"programSwipeBody\" style=\"padding:22px 16px 34px;min-height:360px;touch-action:pan-y\">'\n      +'<div style=\"font-size:12px;color:var(--ink-muted);text-transform:capitalize;margin-bottom:10px\">'+selectedLabel+'</div>'\n      +'<div class=\"info-card\" style=\"padding:22px;text-align:center;color:var(--ink-muted)\">Contenu à venir — commits suivants</div>'\n    +'</div>'"
new_placeholder = "    +'<div id=\"programSwipeBody\" style=\"padding:22px 16px 34px;min-height:360px;touch-action:pan-y\">'\n      +'<div style=\"font-size:12px;color:var(--ink-muted);text-transform:capitalize;margin-bottom:10px\">'+selectedLabel+'</div>'\n      +_programRenderBase(programDay)\n      +'<div style=\"font-size:11.5px;color:var(--ink-subtle);text-align:center;margin-top:18px\">Excursions, autres activités et déplacements — commits suivants</div>'\n    +'</div>'"
replace_once(old_placeholder,new_placeholder,'replace placeholder with base')

p.write_text(s,encoding='utf-8')
print('Program commit 3 patch applied')

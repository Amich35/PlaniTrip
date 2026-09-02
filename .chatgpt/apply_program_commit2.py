from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, got {count}')
    s = s.replace(old, new, 1)

replace_once(
    "var APP_BUILD = '2026-09-02·sha:program-hard-reset-cache-v1';",
    "var APP_BUILD = '2026-09-02·sha:program-shell-v1';",
    'APP_BUILD'
)

program_code = r'''// Etape 5 (Programme) — commit 2 : coquille de navigation jour par jour.
// programDate reste volontairement en memoire uniquement : aucune persistence dans S/NAV_STATE_KEYS.
var programDate = null;

function _programTripDates(){
  if(!CURRENT_TRIP || !CURRENT_TRIP.start_date || !CURRENT_TRIP.end_date) return [];
  var start = String(CURRENT_TRIP.start_date).slice(0,10);
  var end = String(CURRENT_TRIP.end_date).slice(0,10);
  if(!/^\d{4}-\d{2}-\d{2}$/.test(start) || !/^\d{4}-\d{2}-\d{2}$/.test(end) || start>end) return [];
  var out=[];
  var d=new Date(start+'T12:00:00');
  var guard=0;
  while(guard<1000){
    var iso=toLocalISODate(d);
    if(iso>end) break;
    out.push(iso);
    if(iso===end) break;
    d.setDate(d.getDate()+1);
    guard++;
  }
  return out;
}
function _programInitialDate(){
  var dates=_programTripDates();
  if(!dates.length) return null;
  var today=toLocalISODate(new Date());
  if(today<dates[0]) return dates[0];
  if(today>dates[dates.length-1]) return dates[dates.length-1];
  return today;
}
function openProgramScreen(){
  var initial=_programInitialDate();
  if(!initial){ alert('Les dates du voyage sont nécessaires pour ouvrir le Programme.'); return; }
  programDate=initial; // reset uniquement a l'entree dans Programme
  S.tab='program';
  renderContent();
}
function closeProgramScreen(){
  S.tab='today';
  renderContent();
}
function setProgramDate(dateStr){
  var dates=_programTripDates();
  if(dates.indexOf(dateStr)===-1) return;
  programDate=dateStr;
  renderContent();
}
function changeProgramDay(delta){
  var dates=_programTripDates();
  var i=dates.indexOf(programDate);
  if(i<0) return;
  var ni=i+delta;
  if(ni<0 || ni>=dates.length) return;
  programDate=dates[ni];
  renderContent();
}
function _programDayLabel(dateStr){
  var d=new Date(dateStr+'T12:00:00');
  var wd=d.toLocaleDateString('fr-FR',{weekday:'short'}).replace('.','');
  var day=d.getDate();
  var month=d.toLocaleDateString('fr-FR',{month:'short'}).replace('.','');
  return {weekday:wd, day:day, month:month};
}
function renderProgramScreen(){
  var dates=_programTripDates();
  if(!dates.length){
    return '<div class="section"><button onclick="closeProgramScreen()" style="border:0;background:none;color:var(--accent);font-size:15px;padding:0 0 14px;cursor:pointer">‹ Retour</button><div class="section-title">Programme</div><div class="info-card" style="margin-top:16px;padding:18px">Dates du voyage indisponibles.</div></div>';
  }
  if(dates.indexOf(programDate)===-1) programDate=_programInitialDate(); // garde-fou, jamais un reset de rerender valide
  var today=toLocalISODate(new Date());
  var todayInTrip=dates.indexOf(today)>-1;
  var dayButtons=dates.map(function(ds){
    var l=_programDayLabel(ds), active=ds===programDate;
    return '<button type="button" data-program-date="'+ds+'" onclick="setProgramDate(\''+ds+'\')" style="flex:0 0 auto;min-width:58px;padding:8px 9px;border-radius:16px;border:'+(active?'1.5px solid var(--accent)':'1px solid rgba(29,29,31,0.08)')+';background:'+(active?'var(--accent)':'var(--parchment)')+';color:'+(active?'#fff':'var(--ink)')+';font-family:-apple-system,BlinkMacSystemFont,sans-serif;cursor:pointer;text-align:center"><span style="display:block;font-size:10px;text-transform:uppercase;letter-spacing:.04em;opacity:.72">'+l.weekday+'</span><span style="display:block;font-size:17px;font-weight:700;line-height:1.15;margin-top:1px">'+l.day+'</span><span style="display:block;font-size:10px;opacity:.72">'+l.month+'</span></button>';
  }).join('');
  var selected=new Date(programDate+'T12:00:00');
  var selectedLabel=selected.toLocaleDateString('fr-FR',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
  selectedLabel=selectedLabel.charAt(0).toUpperCase()+selectedLabel.slice(1);
  return '<div style="min-height:100%">'
    +'<div style="padding:16px 16px 10px;display:flex;align-items:center;justify-content:space-between;gap:12px">'
      +'<div><button type="button" onclick="closeProgramScreen()" style="display:block;border:0;background:none;color:var(--accent);font-size:15px;padding:0 0 5px;cursor:pointer;font-family:-apple-system,BlinkMacSystemFont,sans-serif">‹ Retour</button><div style="font-size:26px;font-weight:700;letter-spacing:-.6px;color:var(--ink)">Programme</div></div>'
      +(todayInTrip && programDate!==today ? '<button type="button" onclick="setProgramDate(\''+today+'\')" style="border:1px solid rgba(45,106,79,.18);background:var(--accent-pale);color:var(--accent-deep);font-size:12px;font-weight:600;padding:8px 11px;border-radius:16px;cursor:pointer">Aujourd’hui</button>' : '')
    +'</div>'
    +'<div id="programDayStrip" style="position:sticky;top:0;z-index:20;display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;padding:8px 16px 10px;background:rgba(248,246,242,.96);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid rgba(29,29,31,.06)">'+dayButtons+'</div>'
    +'<div id="programSwipeBody" style="padding:22px 16px 34px;min-height:360px;touch-action:pan-y">'
      +'<div style="font-size:12px;color:var(--ink-muted);text-transform:capitalize;margin-bottom:10px">'+selectedLabel+'</div>'
      +'<div class="info-card" style="padding:22px;text-align:center;color:var(--ink-muted)">Contenu à venir — commits suivants</div>'
    +'</div>'
  +'</div>';
}
function _programAfterRender(){
  if(S.tab!=='program') return;
  var strip=document.getElementById('programDayStrip');
  var selected=strip && strip.querySelector('[data-program-date="'+programDate+'"]');
  if(strip && selected){
    strip.scrollLeft=Math.max(0,selected.offsetLeft-(strip.clientWidth-selected.offsetWidth)/2);
  }
  var body=document.getElementById('programSwipeBody');
  if(!body) return;
  var sx=null, sy=null;
  body.addEventListener('touchstart',function(e){
    if(!e.touches || e.touches.length!==1) return;
    if(e.target && e.target.closest && e.target.closest('button,a,input,select,textarea')) return;
    sx=e.touches[0].clientX; sy=e.touches[0].clientY;
  },{passive:true});
  body.addEventListener('touchend',function(e){
    if(sx===null || !e.changedTouches || !e.changedTouches.length){ sx=null; sy=null; return; }
    var dx=e.changedTouches[0].clientX-sx;
    var dy=e.changedTouches[0].clientY-sy;
    sx=null; sy=null;
    if(Math.abs(dx)<50 || Math.abs(dx)<=Math.abs(dy)*1.2) return;
    changeProgramDay(dx<0 ? 1 : -1);
  },{passive:true});
}

'''
replace_once('function syncActiveNavTab(){', program_code + 'function syncActiveNavTab(){', 'program helpers insertion')

old_nav = "  var activeId = (S.tab==='country'||S.tab==='cityDetail'||S.tab==='archived-countries'||S.tab==='archived-cities'||S.tab==='archived-activities'||S.tab==='archived-movements'||S.tab==='manage-countries') ? 'countries' : (S.tab==='documents'||S.tab==='journal'||S.tab==='access-management'||S.tab==='my-account') ? 'more' : S.tab;"
new_nav = "  var activeId = S.tab==='program' ? 'today' : (S.tab==='country'||S.tab==='cityDetail'||S.tab==='archived-countries'||S.tab==='archived-cities'||S.tab==='archived-activities'||S.tab==='archived-movements'||S.tab==='manage-countries') ? 'countries' : (S.tab==='documents'||S.tab==='journal'||S.tab==='access-management'||S.tab==='my-account') ? 'more' : S.tab;"
replace_once(old_nav, new_nav, 'nav mapping')

replace_once(
    "  else if(S.tab==='today')html=renderToday();\n  else if(S.tab==='countries')html=renderCountriesScreen();",
    "  else if(S.tab==='today')html=renderToday();\n  else if(S.tab==='program')html=renderProgramScreen();\n  else if(S.tab==='countries')html=renderCountriesScreen();",
    'render dispatch'
)

replace_once(
    "  document.getElementById('mainContent').innerHTML=html;\n  document.querySelectorAll('.day-badge[data-actkey]')",
    "  document.getElementById('mainContent').innerHTML=html;\n  if(S.tab==='program') requestAnimationFrame(_programAfterRender);\n  document.querySelectorAll('.day-badge[data-actkey]')",
    'post render hook'
)

old_diag = "      +'<button onclick=\"hardResetLocalTripCache()\" style=\"width:100%;padding:9px;margin-top:8px;border-radius:var(--r12);border:1.5px solid var(--red-muted);background:transparent;color:var(--red-muted);cursor:pointer;font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px;font-weight:600\">Reinitialiser tout le cache local (test)</button>'"
new_diag = old_diag + "\n      +'<button onclick=\"openProgramScreen()\" style=\"width:100%;padding:10px;margin-top:8px;border-radius:var(--r12);border:1px solid rgba(45,106,79,.25);background:var(--accent-pale);color:var(--accent-deep);cursor:pointer;font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:13px;font-weight:600\">Ouvrir Programme (test)</button>'"
replace_once(old_diag, new_diag, 'diagnostic entry button')

p.write_text(s, encoding='utf-8')
print('Program commit 2 patch applied successfully')

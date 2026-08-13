from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old = """function saveDateChange(){
  var val = document.getElementById('dateChangeInput').value;
  setActivityDate(_dateChangeActKey, val);
  document.getElementById('dateChangeModal').classList.remove('open');
}"""
new = """async function saveDateChange(){
  var input = document.getElementById('dateChangeInput');
  var val = input ? input.value : '';
  var actKey = _dateChangeActKey;
  var prevHadDate = !!(S.actDate && Object.prototype.hasOwnProperty.call(S.actDate, actKey));
  var prevDate = prevHadDate ? S.actDate[actKey] : undefined;
  var btn = document.querySelector('#dateChangeModal button[onclick=\"saveDateChange()\"]');
  if(!sb || !CURRENT_TRIP || !CURRENT_TRIP.id){ alert('Connexion requise pour enregistrer cette date.'); return; }
  if(btn){ btn.disabled=true; btn.textContent='…'; }
  setActivityDate(actKey, val, {sync:false});
  try{
    if(_isCustomStableKey(actKey)) await _syncActivityState(actKey, CURRENT_TRIP.id);
    else await _syncPlanningBlobs(actKey, CURRENT_TRIP.id);
  }catch(e){
    console.error('[PlaniTrip] saveDateChange sync:', e);
    if(!S.actDate) S.actDate={};
    if(prevHadDate) S.actDate[actKey]=prevDate; else delete S.actDate[actKey];
    save(); renderContent();
    alert('Impossible d’enregistrer cette date pour le moment.');
    if(btn){ btn.disabled=false; btn.textContent='Enregistrer'; }
    return;
  }
  document.getElementById('dateChangeModal').classList.remove('open');
  if(btn){ btn.disabled=false; btn.textContent='Enregistrer'; }
}"""
assert s.count(old) == 1, f'saveDateChange count={s.count(old)}'
s = s.replace(old, new, 1)

old1 = "onchange=\"event.stopPropagation();setActivityDate(\\'" + "'+jsStrEsc(k)+'" + "\\',this.value)\""
new1 = "onchange=\"event.stopPropagation();saveInlineActivityDate(this,\\'" + "'+jsStrEsc(k)+'" + "\\')\""
assert s.count(old1) == 1, f'builtin inline date count={s.count(old1)}'
s = s.replace(old1, new1, 1)

old2 = "onchange=\"event.stopPropagation();setActivityDate(\\'" + "'+jsStrEsc(ck2)+'" + "\\',this.value)\""
new2 = "onchange=\"event.stopPropagation();saveInlineActivityDate(this,\\'" + "'+jsStrEsc(ck2)+'" + "\\')\""
assert s.count(old2) == 1, f'custom inline date count={s.count(old2)}'
s = s.replace(old2, new2, 1)

anchor = "function setActivityDate(actKey, dateVal, opts){"
helper = """async function saveInlineActivityDate(input, actKey){
  if(!input || input.dataset.syncing==='1') return;
  var val = input.value;
  var prevHadDate = !!(S.actDate && Object.prototype.hasOwnProperty.call(S.actDate, actKey));
  var prevDate = prevHadDate ? S.actDate[actKey] : undefined;
  if(!sb || !CURRENT_TRIP || !CURRENT_TRIP.id){
    input.value = prevHadDate ? prevDate : '';
    alert('Connexion requise pour enregistrer cette date.');
    return;
  }
  input.dataset.syncing='1'; input.disabled=true;
  setActivityDate(actKey, val, {sync:false});
  try{
    if(_isCustomStableKey(actKey)) await _syncActivityState(actKey, CURRENT_TRIP.id);
    else await _syncPlanningBlobs(actKey, CURRENT_TRIP.id);
  }catch(e){
    console.error('[PlaniTrip] inline date sync:', e);
    if(!S.actDate) S.actDate={};
    if(prevHadDate) S.actDate[actKey]=prevDate; else delete S.actDate[actKey];
    save(); renderContent();
    alert('Impossible d’enregistrer cette date pour le moment.');
  }finally{
    input.dataset.syncing='0'; input.disabled=false;
  }
}

"""
assert s.count(anchor) == 1, f'setActivityDate anchor count={s.count(anchor)}'
s = s.replace(anchor, helper + anchor, 1)

p.write_text(s, encoding='utf-8')

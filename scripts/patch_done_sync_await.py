from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
start=s.find('function toggleAct(k){')
end=s.find('function toggleFavorite(k){', start)
assert start>=0 and end>start, f'toggleAct bounds not found: {start}, {end}'
old=s[start:end]
assert old.count("__planitrip__done")==1, f'unexpected done sync shape: {old.count("__planitrip__done")}'
new="""var _doneSyncInFlight = {};
async function toggleAct(k){
  if(_doneSyncInFlight[k]) return;
  if(!S.done) S.done={};
  var prevHadDone = Object.prototype.hasOwnProperty.call(S.done,k);
  var prevDone = S.done[k];
  var wasUndone = !S.done[k];
  S.done[k]=!S.done[k];
  save();
  renderContent();
  // P1-A : conserver l'UI optimistic, mais attendre réellement Supabase et rollbacker en cas d'échec.
  if(sb && CURRENT_TRIP && CURRENT_TRIP.id){
    _doneSyncInFlight[k]=true;
    try{
      if(_isCustomStableKey(k)){
        await _syncActivityState(k, CURRENT_TRIP.id);
      } else {
        var r = await sb.from('activity_details').upsert(
          {trip_id:CURRENT_TRIP.id,detail_key:'__planitrip__done',data:S.done,updated_at:new Date().toISOString()},
          {onConflict:'trip_id,detail_key'}
        );
        if(r && r.error) throw r.error;
      }
    }catch(e){
      console.error('[PlaniTrip] sync done:',e);
      if(prevHadDone) S.done[k]=prevDone; else delete S.done[k];
      save(); renderContent();
      alert('Impossible de modifier le statut Fait pour le moment.');
      return;
    }finally{
      delete _doneSyncInFlight[k];
    }
  }
  // Peak moment: animate the check if just completed
  if(wasUndone && S.done[k]){
    setTimeout(function(){
      var card = document.querySelector('[data-detail="'+CSS.escape(k)+'"]')
        || document.querySelector('.act-check-btn[data-actkey="'+CSS.escape(k)+'"]');
      if(card){
        var actCard = card.closest ? card.closest('.act-card') : null;
        if(actCard){ actCard.classList.add('just-done'); setTimeout(function(){ actCard.classList.remove('just-done'); }, 700); }
      }
    }, 30);
  }
}
"""
s=s[:start]+new+s[end:]
assert s.count('async function toggleAct(k)')==1
assert s.count('var _doneSyncInFlight = {}')==1
p.write_text(s,encoding='utf-8')

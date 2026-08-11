from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
def once(a,b,label):
    global s
    n=s.count(a)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(a,b,1)
old="""function syncDeletedActs(){
  if(sb && CURRENT_TRIP){
    sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:'__planitrip__deletedActs',data:S.deletedActs,updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error(\"[PlaniTrip] sync error:\",_r.error); });
  }
}
"""
new="""function _deletedActDetailKey(actKey){ return '__planitrip__deletedAct__'+encodeURIComponent(actKey||''); }
function syncDeletedAct(actKey, isDeleted){
  if(!sb || !CURRENT_TRIP || !actKey) return Promise.resolve(null);
  return sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:_deletedActDetailKey(actKey),data:{actKey:actKey,deleted:!!isDeleted},updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] sync deleted act:',_r.error); return _r; });
}
function syncDeletedActs(){
  // P0.8-C : migration/compatibilité vers un marqueur par activité ; plus aucun full-blob write.
  if(sb && CURRENT_TRIP){
    return Promise.all(Object.keys(S.deletedActs||{}).filter(function(k){return !!S.deletedActs[k];}).map(function(k){ return syncDeletedAct(k,true); }));
  }
  return Promise.resolve([]);
}
"""
once(old,new,'syncDeletedActs')
once("""    } else {
      if(!S.deletedActs) S.deletedActs={};
      S.deletedActs[cityKey+'_'+index]=true;
      S.trash[cityKey].push({_builtinIndex:index, _cityKey:cityKey});
    }
""","""    } else {
      if(!S.deletedActs) S.deletedActs={};
      var _builtinDeletedKey = cityKey+'_'+index;
      S.deletedActs[_builtinDeletedKey]=true;
      S.trash[cityKey].push({_builtinIndex:index, _cityKey:cityKey});
      syncDeletedAct(_builtinDeletedKey,true);
    }
""",'built-in archive marker')
once("""  } else {
    // Restore built-in
    if(S.deletedActs) delete S.deletedActs[item._cityKey+'_'+item._builtinIndex];
    save(); renderContent();
  }
  syncDeletedActs();
""","""  } else {
    // Restore built-in
    var _builtinRestoreKey = item._cityKey+'_'+item._builtinIndex;
    if(S.deletedActs) delete S.deletedActs[_builtinRestoreKey];
    syncDeletedAct(_builtinRestoreKey,false);
    save(); renderContent();
  }
  syncDeletedActs();
""",'built-in restore marker')
once("""  var _detailFieldRows = [];
  var _cityTrashRows = [];
  Object.values(latest).forEach(function(row){
""","""  var _detailFieldRows = [];
  var _cityTrashRows = [];
  var _deletedActRows = [];
  Object.values(latest).forEach(function(row){
""",'deleted act collector init')
once("""    } else if(row.detail_key === '__planitrip__deletedActs'){
      if(row.data && typeof row.data === 'object'){ S.deletedActs = row.data; }
""","""    } else if(row.detail_key.indexOf('__planitrip__deletedAct__')===0){
      if(row.data && typeof row.data === 'object' && row.data.actKey){ _deletedActRows.push(row.data); }
    } else if(row.detail_key === '__planitrip__deletedActs'){
      if(row.data && typeof row.data === 'object'){ S.deletedActs = row.data; }
""",'deleted act loader branch')
once("""  // P0.8-C : dès que des lignes granulaires existent, elles deviennent autoritaires.
  if(_cityTrashRows.length){
""","""  // P0.8-C : les marqueurs granulaires deletedAct deviennent autoritaires dès qu'ils existent.
  if(_deletedActRows.length){
    var _da = {};
    _deletedActRows.forEach(function(m){ if(m && m.actKey && m.deleted) _da[m.actKey]=true; });
    S.deletedActs = _da;
  }
  // P0.8-C : dès que des lignes granulaires existent, elles deviennent autoritaires.
  if(_cityTrashRows.length){
""",'deleted act overlay')
p.write_text(s,encoding='utf-8')

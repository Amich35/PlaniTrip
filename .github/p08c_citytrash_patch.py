from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
def once(a,b,label):
    global s
    n=s.count(a)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(a,b,1)
old="""function syncCityTrash(){
  // S.cityTrash n'était jusque-là stocké que localement (gros blob) : une suppression de ville
  // pouvait \"réussir\" (ville bien cachée) tout en perdant l'entrée de corbeille correspondante
  // si l'écriture locale était interrompue (iOS). Synchronisé comme deletedActs/deletedCities.
  if(sb && CURRENT_TRIP){
    sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:'__planitrip__cityTrash',data:S.cityTrash,updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error(\"[PlaniTrip] sync error:\",_r.error); });
  }
}
"""
new="""function _cityTrashDetailKey(t){
  if(!t) return '';
  return '__planitrip__cityTrash__'+encodeURIComponent(t.countryId||'')+'__'+encodeURIComponent(t.cityName||'');
}
function syncCityTrashEntry(t){
  if(!sb || !CURRENT_TRIP || !t) return Promise.resolve(null);
  return sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:_cityTrashDetailKey(t),data:t,updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] sync city trash entry:',_r.error); return _r; });
}
function removeCityTrashEntry(t){
  if(!sb || !CURRENT_TRIP || !t) return Promise.resolve(null);
  return sb.from('activity_details').delete().eq('trip_id',CURRENT_TRIP.id).eq('detail_key',_cityTrashDetailKey(t)).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] remove city trash entry:',_r.error); return _r; });
}
function syncCityTrash(){
  // P0.8-C : une ligne par ville archivée. Le blob historique reste en lecture uniquement.
  if(sb && CURRENT_TRIP){ return Promise.all((S.cityTrash||[]).map(function(t){ return syncCityTrashEntry(t); })); }
  return Promise.resolve([]);
}
"""
once(old,new,'syncCityTrash')
once("""  S.cityTrash.splice(idx,1);
  save();
  renderContent();
  syncDeletedActs(); syncCityOrder(t.countryId); syncDeletedCities(); syncCityTrash();
""","""  S.cityTrash.splice(idx,1);
  save();
  renderContent();
  syncDeletedActs(); syncCityOrder(t.countryId); syncDeletedCities(); removeCityTrashEntry(t); syncCityTrash();
""",'restore city trash removal')
once("""    if(idx>-1) S.cityTrash.splice(idx,1);
    var countryId = t.countryId;
    syncCityTrash();
""","""    if(idx>-1) S.cityTrash.splice(idx,1);
    var countryId = t.countryId;
    removeCityTrashEntry(t); syncCityTrash();
""",'permanent city trash removal')
once("""  var _detailFieldRows = [];
  Object.values(latest).forEach(function(row){
""","""  var _detailFieldRows = [];
  var _cityTrashRows = [];
  Object.values(latest).forEach(function(row){
""",'city trash collector init')
once("""    } else if(row.detail_key === '__planitrip__cityTrash'){
      if(row.data && Array.isArray(row.data)){ S.cityTrash = row.data; }
""","""    } else if(row.detail_key.indexOf('__planitrip__cityTrash__')===0){
      if(row.data && typeof row.data === 'object'){ _cityTrashRows.push(row.data); }
    } else if(row.detail_key === '__planitrip__cityTrash'){
      if(row.data && Array.isArray(row.data)){ S.cityTrash = row.data; }
""",'city trash loader branch')
once("""  // P0.8-A/5A : overlay granulaire après les fiches complètes legacy.
""","""  // P0.8-C : dès que des lignes granulaires existent, elles deviennent autoritaires.
  if(_cityTrashRows.length){
    var _ctByKey = {};
    _cityTrashRows.forEach(function(t){ if(t && t.countryId && t.cityName) _ctByKey[t.countryId+'||'+t.cityName]=t; });
    S.cityTrash = Object.values(_ctByKey);
  }
  // P0.8-A/5A : overlay granulaire après les fiches complètes legacy.
""",'city trash overlay')
p.write_text(s,encoding='utf-8')

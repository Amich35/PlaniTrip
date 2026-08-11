from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8')
def once(a,b,label):
    global s
    n=s.count(a)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(a,b,1)
old="""function syncDeletedCities(){
  if(sb && CURRENT_TRIP){
    sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:'__planitrip__deletedCities',data:S.deletedCities,updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error(\"[PlaniTrip] sync error:\",_r.error); });
  }
}
"""
new="""function _deletedCityDetailKey(countryId, cityName){ return '__planitrip__deletedCity__'+encodeURIComponent(countryId||'')+'__'+encodeURIComponent(cityName||''); }
function syncDeletedCity(countryId, cityName, isDeleted){
  if(!sb || !CURRENT_TRIP || !countryId || !cityName) return Promise.resolve(null);
  return sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:_deletedCityDetailKey(countryId,cityName),data:{countryId:countryId,cityName:cityName,deleted:!!isDeleted},updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] sync deleted city:',_r.error); return _r; });
}
function syncDeletedCities(){
  // P0.8-C : migration/compatibilité vers un marqueur par ville ; plus aucun full-blob write.
  if(sb && CURRENT_TRIP){
    return Promise.all(Object.keys(S.deletedCities||{}).filter(function(k){return !!S.deletedCities[k];}).map(function(k){
      var p=k.indexOf('||'); if(p<0) return Promise.resolve(null);
      return syncDeletedCity(k.slice(0,p),k.slice(p+2),true);
    }));
  }
  return Promise.resolve([]);
}
"""
once(old,new,'syncDeletedCities')
once("""  if(!S.deletedCities) S.deletedCities={};
  S.deletedCities[countryId+'||'+cityName] = true;
""","""  if(!S.deletedCities) S.deletedCities={};
  S.deletedCities[countryId+'||'+cityName] = true;
  syncDeletedCity(countryId,cityName,true);
""",'city archive marker')
once("""  unmarkDeletedTombstone('cities', t.countryId+'||'+t.cityName);
  if(S.deletedCities) delete S.deletedCities[t.countryId+'||'+t.cityName];
""","""  unmarkDeletedTombstone('cities', t.countryId+'||'+t.cityName);
  if(S.deletedCities) delete S.deletedCities[t.countryId+'||'+t.cityName];
  syncDeletedCity(t.countryId,t.cityName,false);
""",'city restore marker')
once("""  var _detailFieldRows = [];
  var _cityTrashRows = [];
  var _deletedActRows = [];
  Object.values(latest).forEach(function(row){
""","""  var _detailFieldRows = [];
  var _cityTrashRows = [];
  var _deletedActRows = [];
  var _deletedCityRows = [];
  Object.values(latest).forEach(function(row){
""",'deleted city collector init')
once("""    } else if(row.detail_key === '__planitrip__deletedCities'){
      if(row.data && typeof row.data === 'object'){ S.deletedCities = row.data; }
""","""    } else if(row.detail_key.indexOf('__planitrip__deletedCity__')===0){
      if(row.data && typeof row.data === 'object' && row.data.countryId && row.data.cityName){ _deletedCityRows.push(row.data); }
    } else if(row.detail_key === '__planitrip__deletedCities'){
      if(row.data && typeof row.data === 'object'){ S.deletedCities = row.data; }
""",'deleted city loader branch')
once("""  // P0.8-C : les marqueurs granulaires deletedAct deviennent autoritaires dès qu'ils existent.
  if(_deletedActRows.length){
""","""  // P0.8-C : les marqueurs granulaires deletedCity deviennent autoritaires dès qu'ils existent.
  if(_deletedCityRows.length){
    var _dc = {};
    _deletedCityRows.forEach(function(m){ if(m && m.countryId && m.cityName && m.deleted) _dc[m.countryId+'||'+m.cityName]=true; });
    S.deletedCities = _dc;
  }
  // P0.8-C : les marqueurs granulaires deletedAct deviennent autoritaires dès qu'ils existent.
  if(_deletedActRows.length){
""",'deleted city overlay')
p.write_text(s,encoding='utf-8')

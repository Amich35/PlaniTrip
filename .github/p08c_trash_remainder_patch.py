from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# 1) City trash: never delete the granular row on restore. Persist an explicit negative marker
# so the legacy __planitrip__cityTrash blob can never resurrect a restored city after reload.
old="""function removeCityTrashEntry(t){
  if(!sb || !CURRENT_TRIP || !t) return Promise.resolve(null);
  return sb.from('activity_details').delete().eq('trip_id',CURRENT_TRIP.id).eq('detail_key',_cityTrashDetailKey(t)).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] remove city trash entry:',_r.error); return _r; });
}"""
new="""function removeCityTrashEntry(t){
  if(!sb || !CURRENT_TRIP || !t) return Promise.resolve(null);
  // P0.8-C : conserver une ligne négative explicite. Si on DELETE la dernière ligne
  // granulaire, le blob legacy __planitrip__cityTrash redevient autoritaire au reload.
  var marker={countryId:t.countryId,cityName:t.cityName,_cityTrashRemoved:true};
  return sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:_cityTrashDetailKey(t),data:marker,updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] remove city trash entry:',_r.error); return _r; });
}"""
if s.count(old)!=1:
    raise SystemExit('removeCityTrashEntry anchor mismatch: '+str(s.count(old)))
s=s.replace(old,new,1)

old2="""  if(_cityTrashRows.length){
    var _ctByKey = {};
    _cityTrashRows.forEach(function(t){ if(t && t.countryId && t.cityName) _ctByKey[t.countryId+'||'+t.cityName]=t; });
    S.cityTrash = Object.values(_ctByKey);
  }"""
new2="""  if(_cityTrashRows.length){
    var _ctByKey = {};
    _cityTrashRows.forEach(function(t){
      if(!t || !t.countryId || !t.cityName) return;
      var _ctKey=t.countryId+'||'+t.cityName;
      if(t._cityTrashRemoved) delete _ctByKey[_ctKey];
      else _ctByKey[_ctKey]=t;
    });
    S.cityTrash = Object.values(_ctByKey);
  }"""
if s.count(old2)!=1:
    raise SystemExit('city trash loader anchor mismatch: '+str(s.count(old2)))
s=s.replace(old2,new2,1)

# 2) Empty-day activity view. Locate the unique empty-state literal, then the Add activity
# button in the same HTML expression and append the same Corbeille helper used by normal days.
needle='Aucune activité prévue ce jour'
pos=s.find(needle)
if pos<0:
    raise SystemExit('empty-day literal not found')
if s.find(needle,pos+1)>=0:
    raise SystemExit('empty-day literal is not unique')
start=max(0,pos-1800); end=min(len(s),pos+3000)
chunk=s[start:end]
if 'activityTrashButtonHTML(ck)' in chunk:
    raise SystemExit('empty-day trash button already present')
# The empty-state contains one Add activity button. Inject immediately after its closing button
# while staying inside the existing HTML concatenation.
addpos=chunk.find('openAddActivityModal')
if addpos<0:
    raise SystemExit('empty-day Add activity button not found nearby')
closepos=chunk.find('</button>',addpos)
if closepos<0:
    raise SystemExit('empty-day Add activity closing button not found')
insert_at=start+closepos+len('</button>')
# Source is inside a JS string expression. Continue the expression by closing/reopening through + helper +.
s=s[:insert_at]+"'+activityTrashButtonHTML(ck)+'"+s[insert_at:]

p.write_text(s,encoding='utf-8')

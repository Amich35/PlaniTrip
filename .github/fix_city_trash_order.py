from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
block="""  // P0.8-C : invariant de cohérence. Une entrée de Corbeille ville n'est valide que
  // si la ville est encore marquée archivée. Nettoie notamment les reliquats du blob legacy
  // après une restauration effectuée avant les marqueurs négatifs granulaires.
  if(Array.isArray(S.cityTrash)){
    S.cityTrash = S.cityTrash.filter(function(t){
      return !!(t && t.countryId && t.cityName && S.deletedCities && S.deletedCities[t.countryId+'||'+t.cityName]);
    });
  }
"""
if s.count(block)!=1: raise SystemExit('invariant block count='+str(s.count(block)))
s=s.replace(block,'',1)
anchor="""  if(_cityTrashRows.length){
    var _ctByKey = {};
    _cityTrashRows.forEach(function(t){
      if(!t || !t.countryId || !t.cityName) return;
      var _ctKey=t.countryId+'||'+t.cityName;
      if(t._cityTrashRemoved) delete _ctByKey[_ctKey];
      else _ctByKey[_ctKey]=t;
    });
    S.cityTrash = Object.values(_ctByKey);
  }
"""
if s.count(anchor)!=1: raise SystemExit('overlay anchor count='+str(s.count(anchor)))
moved=anchor+"""  // P0.8-C : invariant après overlay granulaire cityTrash (ordre autoritaire).
  if(Array.isArray(S.cityTrash)){
    S.cityTrash = S.cityTrash.filter(function(t){
      return !!(t && t.countryId && t.cityName && S.deletedCities && S.deletedCities[t.countryId+'||'+t.cityName]);
    });
  }
"""
s=s.replace(anchor,moved,1)
p.write_text(s,encoding='utf-8')

from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
anchor="""  if(_deletedCityRows.length){
    var _dc = {};
    _deletedCityRows.forEach(function(m){ if(m && m.countryId && m.cityName && m.deleted) _dc[m.countryId+'||'+m.cityName]=true; });
    S.deletedCities = _dc;
  }
"""
replacement=anchor+"""  // P0.8-C : invariant de cohérence. Une entrée de Corbeille ville n'est valide que
  // si la ville est encore marquée archivée. Nettoie notamment les reliquats du blob legacy
  // après une restauration effectuée avant les marqueurs négatifs granulaires.
  if(Array.isArray(S.cityTrash)){
    S.cityTrash = S.cityTrash.filter(function(t){
      return !!(t && t.countryId && t.cityName && S.deletedCities && S.deletedCities[t.countryId+'||'+t.cityName]);
    });
  }
"""
if s.count(anchor)!=1:
    raise SystemExit('deleted city reconciliation anchor mismatch: '+str(s.count(anchor)))
s=s.replace(anchor,replacement,1)
p.write_text(s,encoding='utf-8')

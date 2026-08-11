from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(a,b,label):
    global s
    n=s.count(a)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 occurrence, got {n}')
    s=s.replace(a,b,1)

once("""function deleteCityConfirm(countryId, cityName){
  showConfirm('Archiver '+cityName+' ? Tu pourras la restaurer à tout moment depuis la Corbeille. Ses activités, dépenses et entrées de carnet liées seront aussi archivées.', function(){
    deleteCity(countryId, cityName);
  }, 'Archiver');
}
function deleteCity(countryId, cityName){
""","""function deleteCityConfirm(countryId, cityName){
  showConfirm('Archiver '+cityName+' ? Tu pourras la restaurer à tout moment depuis la Corbeille. Ses activités, dépenses et entrées de carnet restent conservées.', function(){
    archiveCitySoft(countryId, cityName);
  }, 'Archiver');
}
async function archiveCitySoft(countryId, cityName){
  if(!sb || !CURRENT_TRIP){ alert('Connexion requise pour archiver cette ville.'); return; }
  if(!S.cityTrash) S.cityTrash=[];
  if(!S.deletedCities) S.deletedCities={};
  var c = COUNTRIES.find(function(x){return x.id===countryId;});
  if(!c) return;
  var idx = c.cities.findIndex(function(ci){return ci.city===cityName;});
  if(idx===-1) return;
  var cityObj = c.cities[idx];
  var existing = S.cityTrash.find(function(t){return t.countryId===countryId && t.cityName===cityName;});
  var entry = existing || {id:Date.now(),countryId:countryId,cityName:cityName,index:idx,cityObj:cityObj,_softArchived:true,journalEntries:[],expenses:[]};
  entry._softArchived = true;
  var trashRes = await syncCityTrashEntry(entry);
  if(trashRes && trashRes.error){ alert('Impossible d’archiver la ville pour le moment.'); return; }
  var markerRes = await syncDeletedCity(countryId,cityName,true);
  if(markerRes && markerRes.error){ await removeCityTrashEntry(entry); alert('Impossible d’archiver la ville pour le moment.'); return; }
  if(!existing) S.cityTrash.push(entry);
  S.deletedCities[countryId+'||'+cityName] = true;
  rebuildCountriesFromState(); save(); renderContent();
}
async function restoreCitySoft(trashId){
  var idx = S.cityTrash.findIndex(function(t){return t.id===trashId;});
  if(idx===-1) return;
  var t = S.cityTrash[idx];
  if(!t || !t._softArchived) return;
  if(!sb || !CURRENT_TRIP){ alert('Connexion requise pour restaurer cette ville.'); return; }
  var markerRes = await syncDeletedCity(t.countryId,t.cityName,false);
  if(markerRes && markerRes.error){ alert('Impossible de restaurer la ville pour le moment.'); return; }
  var trashRes = await removeCityTrashEntry(t);
  if(trashRes && trashRes.error){ await syncDeletedCity(t.countryId,t.cityName,true); alert('Impossible de restaurer la ville pour le moment.'); return; }
  if(S.deletedCities) delete S.deletedCities[t.countryId+'||'+t.cityName];
  S.cityTrash.splice(idx,1);
  rebuildCountriesFromState(); save(); renderContent();
}
function deleteCity(countryId, cityName){
""","city confirm + soft functions")

once("""function restoreCity(trashId){
  var idx = S.cityTrash.findIndex(function(t){return t.id===trashId;});
  if(idx===-1) return;
  var t = S.cityTrash[idx];
  var c = COUNTRIES.find(function(x){return x.id===t.countryId;});
""","""function restoreCity(trashId){
  var idx = S.cityTrash.findIndex(function(t){return t.id===trashId;});
  if(idx===-1) return;
  var t = S.cityTrash[idx];
  if(t && t._softArchived){ restoreCitySoft(trashId); return; }
  var c = COUNTRIES.find(function(x){return x.id===t.countryId;});
""","restore soft dispatch")

p.write_text(s,encoding='utf-8')

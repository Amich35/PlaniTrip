from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker="""function effectiveTripCountries() {
  if (CURRENT_TRIP && CURRENT_TRIP.countries && CURRENT_TRIP.countries.length > 0) return CURRENT_TRIP.countries;
  return BUILT_IN_COUNTRIES.map(function(c){ return c.name; });
}

"""
helper="""function effectiveTripCountries() {
  if (CURRENT_TRIP && CURRENT_TRIP.countries && CURRENT_TRIP.countries.length > 0) return CURRENT_TRIP.countries;
  return BUILT_IN_COUNTRIES.map(function(c){ return c.name; });
}

// P0.8-B — mutation serveur autoritaire des pays actifs/archivés.
// Relit le serveur avant chaque tentative et vérifie après écriture : deux appareils
// qui modifient des pays différents convergent au lieu de réécrire une snapshot locale.
async function _setTripCountryArchived(countryName, shouldArchive){
  if(!sb || !CURRENT_TRIP) return {ok:false, offline:true};
  var lastError = null;
  for(var attempt=0; attempt<3; attempt++){
    var read = await sb.from('trips').select('countries,archived_countries').eq('id',CURRENT_TRIP.id).maybeSingle();
    if(read.error || !read.data){ lastError = read.error || new Error('Voyage introuvable'); continue; }
    var active = Array.isArray(read.data.countries) ? read.data.countries.slice() : [];
    var archived = Array.isArray(read.data.archived_countries) ? read.data.archived_countries.slice() : [];
    if(shouldArchive){
      active = active.filter(function(n){ return n!==countryName; });
      if(archived.indexOf(countryName)===-1) archived.push(countryName);
    } else {
      archived = archived.filter(function(n){ return n!==countryName; });
      if(active.indexOf(countryName)===-1) active.push(countryName);
    }
    active = Array.from(new Set(active));
    archived = Array.from(new Set(archived));
    var upd = await sb.from('trips').update({countries:active, archived_countries:archived}).eq('id',CURRENT_TRIP.id);
    if(upd.error){ lastError = upd.error; continue; }
    var verify = await sb.from('trips').select('countries,archived_countries').eq('id',CURRENT_TRIP.id).maybeSingle();
    if(verify.error || !verify.data){ lastError = verify.error || new Error('Vérification impossible'); continue; }
    var vActive = Array.isArray(verify.data.countries) ? verify.data.countries : [];
    var vArchived = Array.isArray(verify.data.archived_countries) ? verify.data.archived_countries : [];
    var ok = shouldArchive
      ? (vActive.indexOf(countryName)===-1 && vArchived.indexOf(countryName)!==-1)
      : (vActive.indexOf(countryName)!==-1 && vArchived.indexOf(countryName)===-1);
    if(ok){
      CURRENT_TRIP.countries = vActive.slice();
      CURRENT_TRIP.archived_countries = vArchived.slice();
      return {ok:true};
    }
    lastError = new Error('Conflit concurrent');
  }
  return {ok:false, error:lastError};
}

"""
if s.count(marker)!=1: raise SystemExit(f'helper marker match={s.count(marker)}')
s=s.replace(marker,helper,1)
old_archive="""function archiveCurrentCountry(countryId) {
  var c = countryId ? COUNTRIES.find(function(co){return co.id===countryId;}) : getC();
  if(!c) return;
  if(COUNTRIES.length <= 1){ alert(\"Impossible de supprimer le dernier pays.\"); return; }
  showConfirm('Supprimer ' + c.name + ' ? Tu pourras le restaurer à tout moment depuis la Corbeille.', function(){
    if(!S.archivedCountryData) S.archivedCountryData = {};
    S.archivedCountryData[c.id] = JSON.parse(JSON.stringify(c));
    var i = COUNTRIES.findIndex(function(co){ return co.id===c.id; });
    COUNTRIES.splice(i,1);
    if(S.deletedCountryIds.indexOf(c.id)===-1) S.deletedCountryIds.push(c.id);
    if(S.countryOrder) S.countryOrder=[];
    S.country = COUNTRIES[0].id;
    save(); S.tab='countries'; renderContent();

    if (typeof sb !== 'undefined' && sb && typeof CURRENT_TRIP !== 'undefined' && CURRENT_TRIP) {
      var activeCountries = effectiveTripCountries().filter(function(name){return name !== c.name;});
      var archivedCountries = (CURRENT_TRIP.archived_countries || []).concat([c.name]);
      sb.from('trips').update({ countries: activeCountries, archived_countries: archivedCountries }).eq('id', CURRENT_TRIP.id).then(function(res){
        if (res.error) console.error('[PlaniTrip] erreur archivage:', res.error);
        else { CURRENT_TRIP.countries = activeCountries; CURRENT_TRIP.archived_countries = archivedCountries; }
      });
    }
  }, 'Archiver');
}
"""
new_archive="""function archiveCurrentCountry(countryId) {
  var c = countryId ? COUNTRIES.find(function(co){return co.id===countryId;}) : getC();
  if(!c) return;
  if(COUNTRIES.length <= 1){ alert(\"Impossible de supprimer le dernier pays.\"); return; }
  showConfirm('Supprimer ' + c.name + ' ? Tu pourras le restaurer à tout moment depuis la Corbeille.', async function(){
    if (typeof sb !== 'undefined' && sb && typeof CURRENT_TRIP !== 'undefined' && CURRENT_TRIP) {
      try{
        var serverResult = await _setTripCountryArchived(c.name, true);
        if(!serverResult.ok){
          console.error('[PlaniTrip] erreur archivage:', serverResult.error);
          alert(\"Impossible d'archiver ce pays pour le moment. Réessaie avec une connexion active.\");
          return;
        }
      }catch(e){
        console.error('[PlaniTrip] erreur archivage:', e);
        alert(\"Impossible d'archiver ce pays pour le moment. Réessaie avec une connexion active.\");
        return;
      }
    }
    if(!S.archivedCountryData) S.archivedCountryData = {};
    S.archivedCountryData[c.id] = JSON.parse(JSON.stringify(c));
    var i = COUNTRIES.findIndex(function(co){ return co.id===c.id; });
    if(i!==-1) COUNTRIES.splice(i,1);
    if(S.deletedCountryIds.indexOf(c.id)===-1) S.deletedCountryIds.push(c.id);
    if(S.countryOrder) S.countryOrder=[];
    S.country = COUNTRIES[0] ? COUNTRIES[0].id : null;
    save(); S.tab='countries'; renderContent();
  }, 'Archiver');
}
"""
if s.count(old_archive)!=1: raise SystemExit(f'archive match={s.count(old_archive)}')
s=s.replace(old_archive,new_archive,1)
old_restore="""function restoreCountry(countryName) {
  if(!S.archivedCountryData) S.archivedCountryData = {};
  var entry = null;
  Object.keys(S.archivedCountryData).forEach(function(k){
    if(S.archivedCountryData[k].name === countryName) entry = S.archivedCountryData[k];
  });
  if(entry){
    var idx = S.deletedCountryIds.indexOf(entry.id);
    if(idx!==-1) S.deletedCountryIds.splice(idx,1);
    delete S.archivedCountryData[entry.id];
    var builtIn = ['jp','kh','th','la','vn','id','ph'].indexOf(entry.id) !== -1;
    if(!builtIn){
      if(!S.customCountries) S.customCountries=[];
      if(!S.customCountries.find(function(cc){return cc.id===entry.id;})) S.customCountries.push(entry);
    }
    rebuildCountriesFromState();
  }
  save();

  if (typeof sb !== 'undefined' && sb && typeof CURRENT_TRIP !== 'undefined' && CURRENT_TRIP) {
    var archivedCountries = (CURRENT_TRIP.archived_countries || []).filter(function(name){return name !== countryName;});
    var activeCountries = effectiveTripCountries().concat([countryName]);
    sb.from('trips').update({ countries: activeCountries, archived_countries: archivedCountries }).eq('id', CURRENT_TRIP.id).then(function(res){
      if (!res.error) { CURRENT_TRIP.countries = activeCountries; CURRENT_TRIP.archived_countries = archivedCountries; }
      S.tab='archived-countries'; save(); renderContent();
    });
  } else {
    S.tab='archived-countries'; save(); renderContent();
  }
}
"""
new_restore="""async function restoreCountry(countryName) {
  if (typeof sb !== 'undefined' && sb && typeof CURRENT_TRIP !== 'undefined' && CURRENT_TRIP) {
    try{
      var serverResult = await _setTripCountryArchived(countryName, false);
      if(!serverResult.ok){
        console.error('[PlaniTrip] erreur restauration pays:', serverResult.error);
        alert(\"Impossible de restaurer ce pays pour le moment. Réessaie avec une connexion active.\");
        return;
      }
    }catch(e){
      console.error('[PlaniTrip] erreur restauration pays:', e);
      alert(\"Impossible de restaurer ce pays pour le moment. Réessaie avec une connexion active.\");
      return;
    }
  }
  if(!S.archivedCountryData) S.archivedCountryData = {};
  var entry = null;
  Object.keys(S.archivedCountryData).forEach(function(k){
    if(S.archivedCountryData[k].name === countryName) entry = S.archivedCountryData[k];
  });
  if(entry){
    var idx = S.deletedCountryIds.indexOf(entry.id);
    if(idx!==-1) S.deletedCountryIds.splice(idx,1);
    delete S.archivedCountryData[entry.id];
    var builtIn = ['jp','kh','th','la','vn','id','ph'].indexOf(entry.id) !== -1;
    if(!builtIn){
      if(!S.customCountries) S.customCountries=[];
      if(!S.customCountries.find(function(cc){return cc.id===entry.id;})) S.customCountries.push(entry);
    }
    rebuildCountriesFromState();
  }
  save();
  S.tab='archived-countries'; save(); renderContent();
}
"""
if s.count(old_restore)!=1: raise SystemExit(f'restore match={s.count(old_restore)}')
s=s.replace(old_restore,new_restore,1)
p.write_text(s,encoding='utf-8')

from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(a,b,label):
    global s
    n=s.count(a)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(a,b,1)

def allrep(a,b,label,min_count=1):
    global s
    n=s.count(a)
    if n<min_count: raise SystemExit(f'{label}: expected >= {min_count}, got {n}')
    s=s.replace(a,b)

# Helpers de visibilité : le marqueur partagé masque aussi les custom sans toucher à leur identité/table Supabase.
anchor="""function getCustomActivityKey(cityKey, activity, fallbackIndex){
  if(activity && activity._sid) return cityKey+'_sid_'+activity._sid;
  return cityKey+'_c'+fallbackIndex; // legacy — uniquement si pas encore synchronisé
}
"""
insert=anchor+"""function isActivityArchived(actKey){ return !!(S.deletedActs && S.deletedActs[actKey]); }
function countVisibleCustomActs(cityKey){
  var n=0; (S.customActs[cityKey]||[]).forEach(function(a,i){ if(!isActivityArchived(getCustomActivityKey(cityKey,a,i))) n++; });
  return n;
}
"""
once(anchor,insert,'visibility helpers')

# Corbeille activité granulaire, une entrée par actKey.
anchor2="""function syncDeletedAct(actKey, isDeleted){
  if(!sb || !CURRENT_TRIP || !actKey) return Promise.resolve(null);
  return sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:_deletedActDetailKey(actKey),data:{actKey:actKey,deleted:!!isDeleted},updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] sync deleted act:',_r.error); return _r; });
}
"""
insert2=anchor2+"""function _activityTrashDetailKey(actKey){ return '__planitrip__activityTrash__'+encodeURIComponent(actKey||''); }
function _trashItemActKey(cityKey,item){
  if(!item) return '';
  if(item._archiveActKey) return item._archiveActKey;
  if(item._builtinIndex!==undefined) return (item._cityKey||cityKey)+'_'+item._builtinIndex;
  if(item._sid) return cityKey+'_sid_'+item._sid;
  return '';
}
function syncActivityTrashMarker(cityKey,actKey,item,archived){
  if(!sb || !CURRENT_TRIP || !cityKey || !actKey) return Promise.resolve(null);
  return sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:_activityTrashDetailKey(actKey),data:{cityKey:cityKey,actKey:actKey,archived:!!archived,item:item||null},updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] sync activity trash:',_r.error); return _r; });
}
"""
once(anchor2,insert2,'activity trash helpers')

# Nouveau soft archive, utilisé uniquement depuis le geste Archiver. Le chemin skipConfirm reste legacy pour Move-to-city.
anchor3="""async function deleteActivity(cityKey, index, isCustom, actName, opts) {
"""
soft="""async function archiveActivitySoft(cityKey,index,isCustom,actName){
  if(!sb || !CURRENT_TRIP){ alert('Connexion requise pour archiver cette activité.'); return; }
  if(!S.trash) S.trash={}; if(!S.trash[cityKey]) S.trash[cityKey]=[];
  if(!S.deletedActs) S.deletedActs={};
  var act = isCustom ? (S.customActs[cityKey]||[])[index] : null;
  // Les custom legacy _cN restent sur l'ancien chemin : pas de migration aveugle ici.
  if(isCustom && (!act || !act._sid)) return {legacyRequired:true};
  var actKey = isCustom ? getCustomActivityKey(cityKey,act,index) : cityKey+'_'+index;
  var item;
  if(isCustom){
    item = JSON.parse(JSON.stringify(act));
    item._wasCustom=true;
  } else {
    item = {_builtinIndex:index,_cityKey:cityKey};
  }
  item._softArchived=true;
  item._archiveActKey=actKey;
  var trashRes=await syncActivityTrashMarker(cityKey,actKey,item,true);
  if(trashRes && trashRes.error){ alert('Impossible d’archiver cette activité pour le moment.'); return; }
  var markerRes=await syncDeletedAct(actKey,true);
  if(markerRes && markerRes.error){ await syncActivityTrashMarker(cityKey,actKey,item,false); alert('Impossible d’archiver cette activité pour le moment.'); return; }
  if(!S.trash[cityKey].some(function(x){return _trashItemActKey(cityKey,x)===actKey;})) S.trash[cityKey].push(item);
  S.deletedActs[actKey]=true;
  // Aucune suppression de activities/activity_details/favorites, aucun changement de _sid.
  save(); renderContent();
}
async function restoreActivitySoft(cityKey,trashIndex){
  if(!S.trash || !S.trash[cityKey] || !S.trash[cityKey][trashIndex]) return;
  var item=S.trash[cityKey][trashIndex];
  var actKey=_trashItemActKey(cityKey,item);
  if(!item._softArchived || !actKey) return;
  if(!sb || !CURRENT_TRIP){ alert('Connexion requise pour restaurer cette activité.'); return; }
  var markerRes=await syncDeletedAct(actKey,false);
  if(markerRes && markerRes.error){ alert('Impossible de restaurer cette activité pour le moment.'); return; }
  var trashRes=await syncActivityTrashMarker(cityKey,actKey,item,false);
  if(trashRes && trashRes.error){ await syncDeletedAct(actKey,true); alert('Impossible de restaurer cette activité pour le moment.'); return; }
  if(S.deletedActs) delete S.deletedActs[actKey];
  S.trash[cityKey].splice(trashIndex,1);
  save(); renderContent();
}
"""+anchor3
once(anchor3,soft,'soft archive functions')

old_end="""  if(_skipConfirm){ _doDelete(); } else { showConfirm('Archiver '+label+' ? Tu pourras la restaurer à tout moment depuis la Corbeille.', _doDelete, 'Archiver'); }
}
"""
new_end="""  if(_skipConfirm){ _doDelete(); } else { showConfirm('Archiver '+label+' ? Tu pourras la restaurer à tout moment depuis la Corbeille.', function(){
    var _a=isCustom ? (S.customActs[cityKey]||[])[index] : null;
    // Legacy _cN : conserver le flow historique, sans inventer de clé stable.
    if(isCustom && (!_a || !_a._sid)){ _doDelete(); return; }
    archiveActivitySoft(cityKey,index,isCustom,actName);
  }, 'Archiver'); }
}
"""
once(old_end,new_end,'archive dispatch')

old_restore="""function restoreActivity(cityKey, trashIndex) {
  if(!S.trash||!S.trash[cityKey]) return;
  const item = S.trash[cityKey].splice(trashIndex,1)[0];
"""
new_restore="""function restoreActivity(cityKey, trashIndex) {
  if(!S.trash||!S.trash[cityKey]) return;
  var _peek=S.trash[cityKey][trashIndex];
  if(_peek && _peek._softArchived){ restoreActivitySoft(cityKey,trashIndex); return; }
  const item = S.trash[cityKey].splice(trashIndex,1)[0];
"""
once(old_restore,new_restore,'restore dispatch')

old_perm="""  showConfirm('Supprimer définitivement cette activité ? Cette action est irréversible.', function(){
    S.trash[cityKey].splice(trashIndex,1);
    save();
    renderContent();
  }, 'Supprimer définitivement');
"""
new_perm="""  showConfirm('Supprimer définitivement cette activité ? Cette action est irréversible.', function(){
    var _item=S.trash[cityKey][trashIndex];
    var _actKey=_trashItemActKey(cityKey,_item);
    S.trash[cityKey].splice(trashIndex,1);
    // Le marqueur deleted reste vrai : suppression logique définitive, données physiques conservées par sécurité.
    if(_item && _item._softArchived && _actKey) syncActivityTrashMarker(cityKey,_actKey,_item,false);
    save();
    renderContent();
  }, 'Supprimer définitivement');
"""
once(old_perm,new_perm,'permanent soft trash removal')

# Loader : collecter les entrées de corbeille granulaires et neutraliser les copies locales obsolètes avec archived:false.
once("""  var _deletedActRows = [];
  var _deletedCityRows = [];
""","""  var _deletedActRows = [];
  var _deletedCityRows = [];
  var _activityTrashRows = [];
""",'loader init')
once("""    } else if(row.detail_key.indexOf('__planitrip__deletedAct__')===0){
      if(row.data && typeof row.data === 'object' && row.data.actKey){ _deletedActRows.push(row.data); }
""","""    } else if(row.detail_key.indexOf('__planitrip__activityTrash__')===0){
      if(row.data && typeof row.data === 'object' && row.data.cityKey && row.data.actKey){ _activityTrashRows.push(row.data); }
    } else if(row.detail_key.indexOf('__planitrip__deletedAct__')===0){
      if(row.data && typeof row.data === 'object' && row.data.actKey){ _deletedActRows.push(row.data); }
""",'loader branch')
marker="""  // P0.8-C : les marqueurs granulaires deletedAct deviennent autoritaires dès qu'ils existent.
  if(_deletedActRows.length){
    var _da = {};
    _deletedActRows.forEach(function(m){ if(m && m.actKey && m.deleted) _da[m.actKey]=true; });
    S.deletedActs = _da;
  }
"""
overlay=marker+"""  // P0.8-C : corbeille activité partagée. archived:false retire aussi une vieille copie locale.
  if(_activityTrashRows.length){
    if(!S.trash) S.trash={};
    _activityTrashRows.forEach(function(m){
      if(!S.trash[m.cityKey]) S.trash[m.cityKey]=[];
      S.trash[m.cityKey]=S.trash[m.cityKey].filter(function(it){ return _trashItemActKey(m.cityKey,it)!==m.actKey; });
      if(m.archived && m.item){
        m.item._softArchived=true; m.item._archiveActKey=m.actKey;
        S.trash[m.cityKey].push(m.item);
      }
    });
  }
"""
once(marker,overlay,'trash overlay')

# Principales vues : les custom archivées sont masquées sans les retirer de S.customActs.
once("""        var ck2=getCustomActivityKey(ck, ca, origIdx);
        var cDateVal = getActivityDate(ck2, c.id, city.city, slotIdx, order.length);
""","""        var ck2=getCustomActivityKey(ck, ca, origIdx);
        if(isActivityArchived(ck2)) return null;
        var cDateVal = getActivityDate(ck2, c.id, city.city, slotIdx, order.length);
""",'main custom render')
once("""    var k = isBase ? (ck+'_'+origIdx) : getCustomActivityKey(ck, customs[origIdx], origIdx);
    var d = getActivityDate(k, countryId, cityName, slotIdx, order.length);
""","""    var k = isBase ? (ck+'_'+origIdx) : getCustomActivityKey(ck, customs[origIdx], origIdx);
    if(isActivityArchived(k)) return;
    var d = getActivityDate(k, countryId, cityName, slotIdx, order.length);
""",'date counts')
allrep("""const cityTotal=visibleBase+(S.customActs[ck]||[]).length;""","""const cityTotal=visibleBase+countVisibleCustomActs(ck);""",'city totals',1)
allrep("""const cityTotal = visibleBase + (S.customActs[ck]||[]).length;""","""const cityTotal = visibleBase + countVisibleCustomActs(ck);""",'city totals spaced',0)
once("""    (S.customActs[ck]||[]).forEach(function(ca,i){ getActCategory(getCustomActivityKey(ck,ca,i),ca.n,ca.m).forEach(function(cat){ if(cat) presentCats[cat]=true; }); });
""","""    (S.customActs[ck]||[]).forEach(function(ca,i){ var _k=getCustomActivityKey(ck,ca,i); if(isActivityArchived(_k)) return; getActCategory(_k,ca.n,ca.m).forEach(function(cat){ if(cat) presentCats[cat]=true; }); });
""",'category chips')
once("""      (S.customActs[ck]||[]).forEach(function(ca,i){
        items.push({
          k:getCustomActivityKey(ck,ca,i), countryId:c.id, flag:c.flag, country:c.name, city:_cityDisplayName(ck,city),
""","""      (S.customActs[ck]||[]).forEach(function(ca,i){
        var _searchK=getCustomActivityKey(ck,ca,i); if(isActivityArchived(_searchK)) return;
        items.push({
          k:_searchK, countryId:c.id, flag:c.flag, country:c.name, city:_cityDisplayName(ck,city),
""",'search custom filter')

p.write_text(s,encoding='utf-8')

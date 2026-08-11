from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
old="""function syncActOrder(){
  if(sb && CURRENT_TRIP){
    sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:'__planitrip__actOrder',data:S.order,updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error(\"[PlaniTrip] sync error:\",_r.error); });
  }
}
"""
new="""function syncActOrder(ck){
  if(sb && CURRENT_TRIP && ck){
    sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id,detail_key:'__planitrip__actOrder__'+ck,data:(S.order[ck]||[]),updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error(\"[PlaniTrip] sync act order:\",_r.error); });
  }
}
"""
if s.count(old)!=1: raise SystemExit(f'syncActOrder match={s.count(old)}')
s=s.replace(old,new,1)
if s.count('syncActOrder();')!=2: raise SystemExit(f'call count={s.count("syncActOrder();")}')
s=s.replace('syncActOrder();','syncActOrder(ck);')
old_loader="""    } else if(row.detail_key === '__planitrip__actOrder'){
      if(row.data && typeof row.data === 'object'){ S.order = row.data; }
    } else if(row.detail_key === '__planitrip__cityOrder'){
"""
new_loader="""    } else if(row.detail_key === '__planitrip__actOrder'){
      if(row.data && typeof row.data === 'object'){ S.order = row.data; }
    } else if(row.detail_key.indexOf('__planitrip__actOrder__')===0){
      var _orderCk = row.detail_key.slice('__planitrip__actOrder__'.length);
      if(_orderCk && Array.isArray(row.data)){ S.order[_orderCk] = row.data; }
    } else if(row.detail_key === '__planitrip__cityOrder'){
"""
if s.count(old_loader)!=1: raise SystemExit(f'loader match={s.count(old_loader)}')
s=s.replace(old_loader,new_loader,1)
p.write_text(s,encoding='utf-8')

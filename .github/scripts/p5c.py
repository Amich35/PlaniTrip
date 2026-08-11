from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
start = s.index('async function geocodePinForActivity(')
end = s.index('// Rattrapage : géocode en arrière-plan', start)
block = s[start:end]
old = "      if(sb && CURRENT_TRIP){\n        sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id, detail_key:actKey, data:window._customDetails[actKey], updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] sync error:',_r.error); });\n      }\n"
if block.count(old) != 1:
    raise SystemExit(f'geocode writer match count={block.count(old)}')
new = "      if(sb && CURRENT_TRIP){\n        if(!_isTransientLegacyCustomKey(actKey)){\n          // La paire lat/lng est atomique : jamais de latitude d'un write + longitude d'un autre.\n          _syncDetailField(actKey, '_geo', {lat:lat,lng:lng}, CURRENT_TRIP.id).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] sync detail geo:',_r.error); });\n        } else {\n          sb.from('activity_details').upsert({trip_id:CURRENT_TRIP.id, detail_key:actKey, data:window._customDetails[actKey], updated_at:new Date().toISOString()},{onConflict:'trip_id,detail_key'}).then(function(_r){ if(_r&&_r.error) console.error('[PlaniTrip] sync error:',_r.error); });\n        }\n      }\n"
block = block.replace(old, new, 1)
s = s[:start] + block + s[end:]
old_overlay = "    window._customDetails[_dfActKey][_dfField] = _dfValue;\n    if(_dfField === 'tag') window._customDetails[_dfActKey]._userTag = true;\n"
if s.count(old_overlay) != 1:
    raise SystemExit(f'overlay match count={s.count(old_overlay)}')
new_overlay = "    if(_dfField === '_geo' && _dfValue && typeof _dfValue === 'object'){\n      window._customDetails[_dfActKey].lat = _dfValue.lat;\n      window._customDetails[_dfActKey].lng = _dfValue.lng;\n    } else {\n      window._customDetails[_dfActKey][_dfField] = _dfValue;\n    }\n    if(_dfField === 'tag') window._customDetails[_dfActKey]._userTag = true;\n"
s = s.replace(old_overlay, new_overlay, 1)
p.write_text(s, encoding='utf-8')

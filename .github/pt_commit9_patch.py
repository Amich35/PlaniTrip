from pathlib import Path

path = Path('index.html')
s = path.read_text(encoding='utf-8')

old_build = "var APP_BUILD = '2026-09-04·sha:program-outing-existing-activity-v1';"
new_build = "var APP_BUILD = '2026-09-06·sha:program-activity-edit-v1';"
assert s.count(old_build) == 1, f'APP_BUILD anchor count={s.count(old_build)}'
assert 'function openDetail(' in s, 'openDetail editor entry point missing'

old = """function _programActivityRow(item,compact){
  if(!item) return '';
  var t=(S.actTimeStart&&S.actTimeStart[item.actKey]) || (S.actTime&&S.actTime[item.actKey]) || '';
  var spacing=compact===true ? 'padding:0' : 'padding:10px 0;border-top:1px solid rgba(29,29,31,.06)';
  return '<div style=\"display:flex;align-items:flex-start;gap:10px;'+spacing+'\">'
"""
new = """function _programOpenActivityFromRow(el){
  if(!el) return;
  var actKey='', title='', ck='';
  try{
    actKey=decodeURIComponent(el.getAttribute('data-program-act-key')||'');
    title=decodeURIComponent(el.getAttribute('data-program-act-title')||'')||'Activité';
    ck=decodeURIComponent(el.getAttribute('data-program-city-key')||'');
  }catch(e){ return; }
  if(!actKey||!ck) return;
  openDetail(actKey,title,ck);
}
function _programActivityRow(item,compact){
  if(!item) return '';
  var t=(S.actTimeStart&&S.actTimeStart[item.actKey]) || (S.actTime&&S.actTime[item.actKey]) || '';
  var spacing=compact===true ? 'padding:0' : 'padding:10px 0;border-top:1px solid rgba(29,29,31,.06)';
  var canOpen=!!(item.actKey&&item.ck);
  var action=canOpen
    ? ' role=\"button\" tabindex=\"0\" data-program-act-key=\"'+encodeURIComponent(item.actKey)+'\" data-program-act-title=\"'+encodeURIComponent(item.title||'Activité')+'\" data-program-city-key=\"'+encodeURIComponent(item.ck)+'\" onclick=\"_programOpenActivityFromRow(this)\" onkeydown=\"if(event.key===\\'Enter\\'||event.key===\\' \\'){event.preventDefault();_programOpenActivityFromRow(this)}\"'
    : '';
  return '<div'+action+' style=\"display:flex;align-items:flex-start;gap:10px;'+spacing+(canOpen?';cursor:pointer':'')+'\">'
"""
assert s.count(old) == 1, f'program row anchor count={s.count(old)}'

s = s.replace(old_build, new_build, 1)
s = s.replace(old, new, 1)

assert s.count("function _programOpenActivityFromRow(el){") == 1
assert s.count('onclick="_programOpenActivityFromRow(this)"') == 1
assert s.count(new_build) == 1

path.write_text(s, encoding='utf-8')
print('commit9 patch applied safely')

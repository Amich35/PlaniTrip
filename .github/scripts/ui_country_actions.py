from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 match, got {n}')
    s=s.replace(old,new,1)

# 1) Country swipe = archive, not delete; compact single-action width.
old="""    return '<div class=\"swipe-wrap\" style=\"border-radius:var(--r22)\"><div class=\"swipe-delete-bg\" style=\"border-radius:0 var(--r22) var(--r22) 0\" onclick=\"archiveCurrentCountry(\\''+c.id+'\\')\">'+svgIcon('trash-2',15)+' Supprimer</div>'
"""
new="""    return '<div class=\"swipe-wrap\" style=\"border-radius:var(--r22)\"><div class=\"swipe-delete-bg country-archive-bg\" style=\"width:112px;border-radius:0 var(--r22) var(--r22) 0;align-items:center;justify-content:center;gap:6px;background:var(--red-muted);color:#fff;font-size:12px;font-weight:600\" onclick=\"archiveCurrentCountry(\\''+c.id+'\\')\">'+svgIcon('archive',16)+' <span>Archiver</span></div>'
"""
once(old,new,'country swipe label')

# 2) Swipe distance = actual action width. Activities keep 160 because their bg is 160px.
old="""    } else {
      var base = _swipeState.wasOpen ? -160 : 0;
      dxRaw = Math.min(0, Math.max(-160, base + dx));
    }
"""
new="""    } else {
      var _swipeWrap = el.parentNode;
      var _swipeDeleteBg = _swipeWrap ? _swipeWrap.querySelector('.swipe-delete-bg') : null;
      var _swipeLeftMax = (_swipeDeleteBg && _swipeDeleteBg.offsetWidth) ? _swipeDeleteBg.offsetWidth : 160;
      var base = _swipeState.wasOpen ? -_swipeLeftMax : 0;
      dxRaw = Math.min(0, Math.max(-_swipeLeftMax, base + dx));
    }
"""
once(old,new,'swipe move width')

old="""    if(_swipeState.dx < -50){
      el.style.transform = 'translateX(-160px)';
      el.dataset.swipeOpen = '1';
"""
new="""    if(_swipeState.dx < -50){
      var _openWidth = (delBg && delBg.offsetWidth) ? delBg.offsetWidth : 160;
      el.style.transform = 'translateX(-'+_openWidth+'px)';
      el.dataset.swipeOpen = '1';
"""
once(old,new,'swipe end width')

# 3) Wording of reversible action in confirmation modal.
old="""  showConfirm('Supprimer ' + c.name + ' ? Tu pourras le restaurer à tout moment depuis la Corbeille.', async function(){
"""
new="""  showConfirm('Archiver ' + c.name + ' ? Tu pourras le restaurer à tout moment depuis la Corbeille.', async function(){
"""
once(old,new,'archive confirmation wording')

p.write_text(s,encoding='utf-8')

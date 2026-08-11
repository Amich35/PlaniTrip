from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
old="""    var allowRight = !!el.dataset.actKey;
    var dxRaw;
    if(dx>=0){
      dxRaw = allowRight ? Math.min(90, dx) : 0;
    } else {
      var _swipeWrap = el.parentNode;
      var _swipeDeleteBg = _swipeWrap ? _swipeWrap.querySelector('.swipe-delete-bg') : null;
      var _swipeLeftMax = (_swipeDeleteBg && _swipeDeleteBg.offsetWidth) ? _swipeDeleteBg.offsetWidth : 160;
      var base = _swipeState.wasOpen ? -_swipeLeftMax : 0;
      dxRaw = Math.min(0, Math.max(-_swipeLeftMax, base + dx));
    }
"""
new="""    var allowRight = !!el.dataset.actKey;
    var _swipeWrap = el.parentNode;
    var _swipeDeleteBg = _swipeWrap ? _swipeWrap.querySelector('.swipe-delete-bg') : null;
    var _swipeLeftMax = (_swipeDeleteBg && _swipeDeleteBg.offsetWidth) ? _swipeDeleteBg.offsetWidth : 160;
    var dxRaw;
    if(_swipeState.wasOpen){
      // Une carte deja ouverte suit le doigt de -largeur vers 0 lors d'un geste droite.
      dxRaw = Math.min(0, Math.max(-_swipeLeftMax, -_swipeLeftMax + dx));
    } else if(dx>=0){
      dxRaw = allowRight ? Math.min(90, dx) : 0;
    } else {
      dxRaw = Math.min(0, Math.max(-_swipeLeftMax, dx));
    }
"""
if s.count(old)!=1: raise SystemExit(f'move block matches={s.count(old)}')
s=s.replace(old,new,1)
old2="""  } else if(_swipeState.wasOpen){
    el.style.transform = '';
    el.dataset.swipeOpen = '';
    snapBg(false);
    e.preventDefault();
  }
"""
new2="""  } else if(_swipeState.wasOpen){
    // Un simple tap sur une carte ouverte ne doit plus refermer l'action.
    var _keepOpenWidth = (delBg && delBg.offsetWidth) ? delBg.offsetWidth : 160;
    el.style.transform = 'translateX(-'+_keepOpenWidth+'px)';
    el.dataset.swipeOpen = '1';
    snapBg(true);
    e.preventDefault();
  }
"""
if s.count(old2)!=1: raise SystemExit(f'end tap block matches={s.count(old2)}')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')

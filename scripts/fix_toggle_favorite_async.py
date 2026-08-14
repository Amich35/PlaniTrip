from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
old='function toggleFavorite(k){'
assert s.count(old)==1, f'toggleFavorite plain count={s.count(old)}'
s=s.replace(old,'async function toggleFavorite(k){',1)
assert s.count('async function toggleFavorite(k){')==1
p.write_text(s,encoding='utf-8')

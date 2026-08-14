from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# 1) "Tous" must be an explicit persisted state, not absence of state.
old="if(day === 'Tous') delete S.activeDay[ck]; else S.activeDay[ck] = day;"
new="S.activeDay[ck] = day;"
assert s.count(old)==1, f'setActiveDay target count={s.count(old)}'
s=s.replace(old,new,1)

# Invalid stale date also becomes an explicit no-filter state.
old="delete S.activeDay[ck];\n    try{"
new="S.activeDay[ck] = 'Tous';\n    try{"
assert s.count(old)==1, f'invalid activeDay cleanup target count={s.count(old)}'
s=s.replace(old,new,1)

# 2) Category state must no longer filter activities invisibly.
old="    if(!S.activeCategory) S.activeCategory={};\n    const activeCat = S.activeCategory[ck]||'Tous';\n"
assert s.count(old)==1, f'activeCat declaration count={s.count(old)}'
s=s.replace(old,'',1)

for old in [
    "        if(activeCat!=='Tous' && getActCategory(k,a.n,a.m).indexOf(activeCat)===-1) return null;\n",
    "        if(activeCat!=='Tous' && caCat.indexOf(activeCat)===-1) return null;\n",
]:
    assert s.count(old)==1, f'category filtering target count={s.count(old)}: {old!r}'
    s=s.replace(old,'',1)

# Remove the category filter UI block and render only the date row.
start_marker="    // Filtres horizontaux par catégorie — uniquement les catégories réellement présentes dans cette ville\n"
end_marker="    var _activeDay = S.activeDay && S.activeDay[ck] ? S.activeDay[ck] : 'Tous';\n"
start=s.find(start_marker)
end=s.find(end_marker,start)
assert start>=0 and end>start, f'category filter UI bounds not found: {start}, {end}'
old_block=s[start:end]
assert "categoryFilterHTML" in old_block and "renderDayTabs(ck)" in old_block, 'unexpected filter UI block shape'
new_block="""    // Filtre unique : dates. Le filtre catégorie a été retiré volontairement.
    var dayTabsHTML = renderDayTabs(ck);
    var filterBarHTML = '';
    if(dayTabsHTML){
      var calIcon = '<span class=\"cf-filter-icon\">'+svgIcon('calendar',15)+'</span>';
      filterBarHTML = '<div class=\"city-filters-sticky\"><div class=\"cf-filter-card\"><div class=\"cf-filter-row\">'+calIcon+dayTabsHTML+'</div></div></div>';
    }

"""
s=s[:start]+new_block+s[end:]

# Update obsolete comment: there is no category masking anymore.
s=s.replace("      // Distinguer : jour vraiment vide vs activités masquées par filtre catégorie\n", "      // Vérifier si cette date ne contient réellement aucune activité.\n", 1)

# Validation invariants.
assert s.count("S.activeDay[ck] = day;")>=1
assert "if(day === 'Tous') delete S.activeDay[ck]" not in s
assert "const activeCat = S.activeCategory[ck]||'Tous';" not in s
assert "if(activeCat!=='Tous'" not in s
assert "var categoryFilterHTML = '';" not in s
assert "setCityCategory(\\'" not in s  # no rendered category buttons
p.write_text(s,encoding='utf-8')

# Viktória és Zsolt esküvője · Bali, 2026. október 10.

Statikus fotó- és videógaléria GitHub Pages-en, a zsotte.com/eskuvo/ címen.
Az oldal keresők elől rejtett (noindex), a CV oldal nem linkel rá, csak a link birtokában érhető el.

## Új képek, videók hozzáadása

1. Tedd az eredeti fájlokat az `originals/` mappába. Almappák szerint csoportosít a galéria
   (pl. `originals/Szertartás`, `originals/Vacsora`). Ez a mappa nem kerül fel a GitHubra.
2. Futtasd: `python3 tools/build_media.py` (kell hozzá Python, Pillow és ffmpeg).
3. Képaláírások, videócímek, dátum, helyszín, bevezető szöveg: `media.json`.
   Újrafuttatáskor ezek megmaradnak.
4. Commit és push.

## Zene

A jelenlegi `assets/music.mp3` egy saját generálású, jogdíjmentes zongorás háttérzene
(`tools/make_music.py`). Cseréhez írd felül ugyanezen a néven, vagy írd át a `media.json`
`info.music` mezőjét. Üres mezőnél a zene gomb eltűnik.

## Közzététel

A `main` ágra csak pull requesten át kerülhet változás. Az `eskuvo/` mappán dolgozz egy külön ágon, nyiss PR-t, és a merge után a GitHub Pages pár percen belül frissíti az oldalt.

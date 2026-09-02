# Fonts

Self-hosted so the page makes **zero third-party requests**. A Google Fonts
`<link>` would log every visitor's IP address with Google, and this page exists
to be sent to recruiters and hiring managers.

| File | Family | Version | Source |
|---|---|---|---|
| `archivo-latin-var.woff2` | Archivo | v25 | Google Fonts, latin subset, variable `wght 100..900` |
| `jetbrains-mono-latin-var.woff2` | JetBrains Mono | v24 | Google Fonts, latin subset, variable `wght 100..800` |

Both are licensed under the **SIL Open Font License 1.1**; the full licence text
of each is next to the font it covers (`OFL-Archivo.txt`,
`OFL-JetBrainsMono.txt`), which is what the OFL requires when the files are
redistributed. Upstream projects: <https://github.com/Omnibus-Type/Archivo> and
<https://github.com/JetBrains/JetBrainsMono>.

Two files, not the six the build spec estimated: both families are **variable**
fonts on Google Fonts, so one file per family carries every weight the design
uses. 75 kB total instead of the roughly 120 kB six static cuts would have cost,
and one fewer request each.

To refresh a subset later, take the URL out of the Google Fonts CSS API rather
than guessing at the path:

    curl -A 'Mozilla/5.0 ... Chrome/120' \
      'https://fonts.googleapis.com/css2?family=Archivo:wght@100..900&display=swap'

The `latin` block is the one whose `unicode-range` starts `U+0000-00FF`.

## Three characters this page cannot lose

The copy needs exactly three non-ASCII characters, and each is a silent failure
if a future subset drops it: the text does not break, it switches mid-line to a
fallback font.

| Character | Codepoint | Where it appears |
|---|---|---|
| Middle dot `·` | U+00B7 | role line and every org line |
| En dash `–` | U+2013 | every year range |
| E acute `é` | U+00E9 | the name itself, in the `h1` and the `title` |

All three sit inside the woff2 latin subset, which declares `U+0000-00FF` and
`U+2000-206F`. The first two were verified against the upstream TTF's `cmap`
(U+00B7 -> glyph 574, U+2013 -> glyph 593); U+00E9 falls in the same declared
`U+0000-00FF` block. If you ever narrow the subset, check these three first --
and note that the `é` is the one a reader would actually notice, because it is
in the name at the top of the page.

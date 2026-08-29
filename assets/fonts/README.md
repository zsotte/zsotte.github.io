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

## Two characters this page cannot lose

The copy needs exactly two non-ASCII characters, and both are silent failures if
a future subset drops them: the text does not break, it switches mid-line to a
fallback font.

| Character | Codepoint | Where it appears |
|---|---|---|
| Middle dot `·` | U+00B7 | role line and every org line |
| En dash `–` | U+2013 | every year range |

Both were verified in the shipped files, not assumed: the upstream TTF's `cmap`
maps U+00B7 to glyph 574 and U+2013 to glyph 593, and the woff2 latin subset
declares `U+0000-00FF` and `U+2000-206F`, which cover them. If you ever narrow
the subset, check these two first.

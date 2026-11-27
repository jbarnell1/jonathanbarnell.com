# jonathanbarnell.com

My portfolio site. One static page, no framework.

- `template.html` is the page: markup, CSS and a little JavaScript.
- `build.py` holds the project list for the shelf and writes the site into `docs/`.
- `docs/` is what GitHub Pages serves at https://jonathanbarnell.com.

To change the page, edit `template.html` or the project list in `build.py`, then run:

```
python build.py
```

Commit the result, including `docs/`.

Nothing on the page loads from a third party. The fonts (`fonts/`, Red Hat Display and Red Hat Text
under the SIL Open Font License) and three.js (`vendor/`, MIT) are served from the site itself, and
`static/` holds the icons that are copied to the site root.

Three helper scripts need Playwright with Chromium:

- `check.py` tests the built site: sideways overflow at eight widths, headlines over two lines,
  console errors, third-party requests, where links into the page land, project links, and the page
  with script turned off. Add `shots` for one screenshot per section at three widths.
- `assets.py` regenerates the still string art picture and the PNG icons.
- `og.py` regenerates the link preview image.

Every project on the shelf has its own address, for example `https://jonathanbarnell.com/#p-highlights`.

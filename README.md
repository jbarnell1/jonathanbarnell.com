# jonathanbarnell.com

My portfolio site. One static page, no framework.

- `template.html` is the page: markup, CSS and a little JavaScript.
- `build.py` holds the project list for the shelf and writes the site into `docs/`.
- `docs/` is what GitHub Pages serves at https://jonathanbarnell.com.

To change the page, edit `template.html` or the project list in `build.py`, then run:

```
python build.py
```

Commit the result, including `docs/`. `og.py` regenerates the link preview image and needs Playwright.

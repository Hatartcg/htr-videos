# Otaku Haven home-slider banners (1440x810)

Style approved on 11 Nov 2026 (OP-18 + Delta Reign): dark background, pink OH lines/dots, OH logo top-left,
product + feathered key art on the left, text block on the right (English kicker, big Anton title, code pill,
big Arabic status in Cairo 900 pink: «طلب مسبق» / «قريباً» / «متوفر الآن», date pill).
No HTR branding, no yellow.

Render:
1. Copy into one folder: banner.html, shot.cjs, fetch/font_cairo.ttf, fetch/font_anton.ttf, fetch/bn_ohlogo.png (as ohlogo.png),
   and the art/product files referenced in the `V` object (htr-store public/releases/<id>-art.webp, -box.webp, …).
2. Add an entry to `V` in banner.html (glow, art, artpos, artop, kick, title, ts, code, ar, date, prods[{src,left,top,h,rot}]).
   Put the English date inside <b>…</b> (it is bidi-isolated).
3. Edit the list in shot.cjs and run `node shot.cjs` → oh-<id>.png. Look at it: nothing may overlap the text block.
4. Save as JPEG (Salla rejects webp uploads) and push to fetch/oh_slider_<id>.jpg in this repo (public, CORS-enabled raw URL).

Upload (Salla theme editor, s.salla.sa/themes → published theme «تخصيص» → «صور متحركة»):
- Delete the old image of the slot (trash icon), then in the page run JS: load the raw.githubusercontent URL with
  `new Image()` + crossOrigin='anonymous', draw to a canvas, `toBlob('image/jpeg')` → File; find the empty
  `s-uploader` (shadowRoot `.filepond--item` count 0), set its `input[type=file]`.files via DataTransfer and dispatch `change`.
  (fetch() to GitHub is blocked by Salla's CSP; the <img> route works.)
- Fill «ادخل الرابط» with the product/search link, then «حفظ التغييرات». Check otakkuhaveen.com/ar shows it.

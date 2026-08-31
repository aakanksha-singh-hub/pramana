# Pramana — public site

`index.html` is the entire site. One file, no build step, no server, no
database. Every result is inlined at build time, so it works offline and from
`file://` as well as from a host.

## Preview locally

Double-click `index.html`, or:

    open web/site/index.html

## Deploy (about 60 seconds, no account needed)

1. Go to **https://app.netlify.com/drop**
2. Drag the **`web/site` folder** (not the file) onto the page
3. You get a public URL immediately, e.g. `https://<random-name>.netlify.app`
4. Optional: claim the site to rename it to something like `pramana.netlify.app`

Vercel, Cloudflare Pages, GitHub Pages and Surge all work the same way — it is
a static folder with one file in it.

## Rebuild after new results

    make site

Regenerates `index.html` from whatever is in `results/`.

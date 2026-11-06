"""Public website file allowlist shared by private preflight and Pages verifier."""
# Hard allowlist: no source code, private .env, dealer data, source media,
# downloaded RSR directories, CI fixtures, or private rights ledgers copied.
HTML = (
    "index.html", "catalog.html", "contact.html", "explore.html",
    "experience-lab.html", "studio.html", "showroom.html",
    "operations-lab.html", "portfolio.html", "ffl-finder.html",
)
ASSETS = (
    "assets/approved-media-manifest.json",
    "assets/approved-media-viewer.js",
    "assets/area33-logo-dark.svg",
    "assets/area33-logo-light.svg",
    "assets/catalog-public.json",
    "assets/catalog-shards-contract.mjs",
    "assets/catalog-static-contract.mjs",
    "assets/catalog.css",
    "assets/catalog.js",
    "assets/ecosystem.css",
    "assets/experience-lab.css",
    "assets/experience-lab.js",
    "assets/ffl-public.json",
    "assets/operations-lab.css",
    "assets/operations-lab.js",
    "assets/passport-public.json",
    "assets/portfolio-compare.css",
    "assets/portfolio-compare.js",
    "assets/public-directories.js",
    "assets/public-discovery.css",
    "assets/showroom-contract.mjs",
    "assets/showroom-public.json",
    "assets/showroom.css",
    "assets/showroom.js",
    "assets/site-polish.css",
)
STATIC = HTML + ASSETS



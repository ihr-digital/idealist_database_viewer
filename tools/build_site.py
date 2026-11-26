#!/usr/bin/env python3
"""Build the GitHub Pages site: the viewer with a collection of databases built in.

Usage:  python3 tools/build_site.py [pages/site.json] [_site]

Reads the site config (title, short title, subtitle and a list of databases
with paths to their .TEX and optional .DEF and .LAY files, relative to the
config file), then writes to the output folder:

  index.html            the viewer, with the config embedded as
                        <script type="application/json" id="collection">
  data/...              the database files, copied as they are
  data/....tex.gz       a gzipped copy of each .TEX, which the page fetches
                        when the browser can unpack it (smaller download)
  .nojekyll             tells GitHub Pages to serve the files as they are

Preview locally with:  python3 -m http.server -d _site
"""
import gzip
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "<script>\n{"  # start of the viewer's main script


def main():
    config_path = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "pages" / "site.json")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "_site")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    src = config_path.parent

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for db in config["databases"]:
        for key in ("tex", "def", "lay"):
            if db.get(key):
                target = out / db[key]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src / db[key], target)
        gz = db["tex"] + ".gz"
        with open(src / db["tex"], "rb") as f, gzip.open(out / gz, "wb", compresslevel=9) as g:
            shutil.copyfileobj(f, g)
        db["gz"] = gz
        print(f"{db['id']}: {db['tex']} {(src / db['tex']).stat().st_size:,} bytes, gzipped {(out / gz).stat().st_size:,}")

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    if html.count(MARKER) != 1:
        sys.exit("Could not find the viewer's main <script> in index.html")
    embedded = json.dumps(config, ensure_ascii=False, indent=1).replace("</", "<\\/")
    html = html.replace(MARKER, f'<script type="application/json" id="collection">\n{embedded}\n</script>\n{MARKER}')
    (out / "index.html").write_text(html, encoding="utf-8")
    (out / ".nojekyll").write_text("")
    print(f"Site written to {out}")


if __name__ == "__main__":
    main()

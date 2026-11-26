# Idealist Database Viewer

A single-page application for reading legacy **Blackwell Idealist** databases, built around the databases held by the Institute of Historical Research's Centre for Metropolitan History (CMH).

Idealist was a 1990s free-text database package for Windows. Its `.TEX` files are a proprietary binary format that modern software can't open. This viewer decodes them in the browser and turns them into searchable, browsable records. A small Python script does the same job on the command line and writes JSON.

**Published site:** the viewer is deployed on GitHub Pages with two databases built in: the Seculars and Regulars databases behind Virginia Davis, *Clergy in the Late Middle Ages* (CMH, 2000). See [Published site](#published-site-github-pages).

> 📄 **File format reference: [`docs/FORMAT.md`](docs/FORMAT.md)**
> Read it for the byte-level layout of every file in an Idealist database (`.TEX`, `.DEF`, `.LAY`, `.CMD`, `.LST`, `.ROT`, `.TRM`, `.OCC`, `.DIR`), how field ids are derived from field names, and what is still unknown. Start there if you need to write your own reader or check what the viewer is doing.

## Contents

| Path | What it is |
| --- | --- |
| [`index.html`](index.html) | The viewer. One self-contained HTML file with no dependencies and no build step. |
| [`tools/idealist_decode.py`](tools/idealist_decode.py) | Command-line decoder: `.TEX` file in, JSON out. Python 3 standard library only. |
| [`docs/FORMAT.md`](docs/FORMAT.md) | **The file format reference.** Every Idealist file type, as far as it is known. |
| [`tools/build_site.py`](tools/build_site.py) | Builds the GitHub Pages site from `index.html` and `pages/site.json`. |
| [`pages/`](pages) | The published site's config (`site.json`) and its databases (`data/`). |
| [`.github/workflows/pages.yml`](.github/workflows/pages.yml) | Builds and deploys the site on every push to `main`. |

The only database files in the repository are the two published ones under `pages/data/`. Elsewhere, `.gitignore` keeps Idealist data files out. To use the viewer on another database, you need your own copy.

## The files in an Idealist database

A database is a folder of files sharing one base name. Using the Regulars database as the example:

| File | Size | What it holds | Viewer | Decoder |
| --- | --- | --- | --- | --- |
| `Regulars.tex` | 3.1 MB | **The records.** Binary. Every stored record, including superseded copies of edited records. | **Required** | **Required** |
| `Regulars.def` | 1 KB | **Definition file.** Plain text. Record types and their field names in stored order, plus each field's data type, font and entry rules. | Optional: field names | `--def` |
| `Regulars.lay` | 1 KB | **Layout file.** Plain text. The data-entry form: the label and position of every field box. | Optional: friendlier labels | `--lay` |
| `Regulars.cmd` | 22 bytes | **Command file.** Plain text. Idealist commands run when the database opens (here `SearchFindAllRecords()`). | Skipped | Not used |
| `Regulars.rot` | 44 KB | **Record table.** Binary. Maps record handles to offsets in the `.tex` file, for current records only. | Skipped | Not used |
| `Regulars.trm` | 384 KB | **Term index.** Binary. The indexed words, in 4 KB pages. | Skipped | Not used |
| `Regulars.dir` | 1 KB | **Term directory.** Binary. Points into the pages of the `.trm` file. | Skipped | Not used |
| `Regulars.occ` | 463 KB | **Occurrence lists.** Binary. Which records each indexed word occurs in. | Skipped | Not used |

The four index files (`.rot`, `.trm`, `.dir`, `.occ`) are only Idealist's own search index. Everything they contain can be rebuilt from the `.tex` file, so neither tool reads them. Their layouts, as far as they are understood, are in [`docs/FORMAT.md`](docs/FORMAT.md#index-files).

Some databases also come with two plain-text list files, as Seculars does:

| File | What it holds | Viewer | Decoder |
| --- | --- | --- | --- |
| `Stopword.lst` | The stop-word list: words left out of the index. A copy of it is stored in the `.tex` header, and the viewer shows it on the File tab. | Not needed | Not used |
| `Synonym.lst` | Synonym groups for Idealist's search (e.g. `"color" colour`). The Seculars copy is Blackwell's generic sample list, not specific to the database. | Not needed | Not used |

Some installations have no per-database `.def` and use one `IDEALIST.DEF` shared by every database instead. The CMH project's shared `IDEALIST.DEF` is built into the viewer.

## Databases it has been tested with

| Database | Record types | Records | Files available |
| --- | --- | --- | --- |
| **CMH Gazetteer of Markets and Fairs** (e.g. `ESSEX.TEX`) | defined in the shared CMH `IDEALIST.DEF` | 334 stored in the Essex file | `.TEX`; definitions built in |
| **Regulars** (`Regulars.tex`, January 1995) | `Monks` (14 fields) | 10,717 current + 894 superseded | All eight files listed above |
| **Seculars** (`Seculars.tex`, January 1995) | `Move` (17 fields) | 20,246 current + 2,416 superseded | All except `.lay`, plus `Stopword.lst` and `Synonym.lst` |

Regulars and Seculars are the two databases behind Virginia Davis, *Clergy in the Late Middle Ages: A Register of Clergy Ordained in the Diocese of London Based on Episcopal Ordination Lists 1361–1539* (London, Centre for Metropolitan History, 2000). Both are published on the [project site](#published-site-github-pages).

The Regulars database records ordinations of members of religious orders (Augustinian, Benedictine, Dominican, Carmelite, Franciscan and others) between 1361 and 1537. The register references name London bishops from Sudbury to Stokesley. Its `Monks` fields are:

| Field (`.def`) | Form label (`.lay`) | Type | Field id |
| --- | --- | --- | --- |
| `Forename` | Forename | Text (max 20 chars) | `0x3d7b` |
| `Surname` | Surname | Text | `0x18eb` |
| `O_Level` | Ordained as | Text | `0x1f56` |
| `Worddate` | Date of ordination | Text | `0x3589` |
| `House` | House | Text | `0x074f` |
| `Rel_Order` | Religious Order | Text | `0x6fc8` |
| `Diocese` | Diocese | Text | `0x1f3f` |
| `Personid` | Personid | Number | `0x35a6` |
| `Place` | Place of Ordination | Wrapped text | `0x06a7` |
| `Ord_Bp` | Ordaining Bishop | Wrapped text | `0x0f48` |
| `Ceremony` | Ceremony Number | Number | `0x3d41` |
| `Ref` | Register Reference | Text | `0x0184` |
| `Year` | Year | Number | `0x030c` |
| `Footnotes` | Footnotes | Wrapped text | `0x7fd1` |

`Regulars.def` also defines a `Default` record type with a single `Text` field. No records use it.

The Seculars database records ordinations of secular clergy between 1361 and 1537. It has no `.lay` file, so fields are named from `Seculars.def`. Its `Move` fields, in stored order:

| Field (`.def`) | Type | Field id | | Field (`.def`) | Type | Field id |
| --- | --- | --- | --- | --- | --- | --- |
| `Surname` | Text | `0x18eb` | | `Footnotes` | Text | `0x7fd1` |
| `Forename` | Text | `0x3d7b` | | `Personid` | Number | `0x35a6` |
| `Diocese` | Text | `0x1f3f` | | `Education` | Text | `0x7d64` |
| `Homeplace` | Text | `0x72c7` | | `Year` | Number | `0x030c` |
| `Ordained` | Text | `0x3c2e` | | `Reference` | Text | `0x6f53` |
| `Worddate` | Text | `0x3589` | | `Ceremony` | Number | `0x3d41` |
| `Titlecode` | Number | `0x6bb9` | | `Place` | Text | `0x06a7` |
| `Title` | Text | `0x0685` | | `Ordainer` | Text | `0x3c38` |
| `Original` | Text | `0x3dee` | | | | |

Fields shared with Regulars (`Forename`, `Surname`, `Diocese`, `Worddate`, `Personid`, `Place`, `Ceremony`, `Year`, `Footnotes`) have the same ids in both, because ids come from names. `Personid` appears to link records of the same person.

## Using the viewer

1. Open `index.html` in a current desktop or mobile browser. You can double-click the file; it needs no web server and works offline.
2. Choose **Open files**, or drag files onto the page. The simplest way is to **select every file in the database folder**: the viewer picks out the `.tex`, uses the `.def` and `.lay`, and skips the rest. At minimum you need the `.tex` file.
3. Browse, search and export.

Files are read locally in the browser. Nothing is uploaded anywhere. A database the size of Regulars (3 MB, 11,600 records) opens in a second or two.

### Field names: definition and layout files

Idealist stores field ids, not field names, in the `.TEX` file. Names come from two optional sources:

- **Definition file (`.DEF`)**: the field's internal name, such as `O_Level` or `Ord_Bp` (underscores are shown as spaces). The CMH project's `IDEALIST.DEF` is built in, so CMH databases get names without extra files.
- **Layout file (`.LAY`)**: the label shown on Idealist's data-entry form, such as *Ordained as* or *Ordaining Bishop*. When a layout is loaded, its labels take precedence over definition names.

Names you type on the **Fields** tab override both. Without either file, fields are shown as *Field 1*, *Field 2* … .

Loaded `.DEF` and `.LAY` files are remembered in this browser (`localStorage`). Next time you only need to open the `.tex`. **Forget loaded .DEF and .LAY files** on the Fields tab clears them. You can also load them after the database with **Load .DEF or .LAY files**.

Definitions and layouts are matched to the database by record type name (`Monks`). Fields are matched by name hash, which needs neither file to list fields in any particular order. If fewer than half of a definition's hashes match and the field counts agree, the viewer falls back to matching definition names by position. The **Fields** tab reports which method was used and shows the definition and form label for each field.

### Tabs

- **Browse**: a record list and a detail card. Search across all fields or one field; use `"quotes"` for phrases. Short values in a record have a **filter** button that narrows the list to records sharing that value; filters appear as removable chips. **Hide empty fields** tidies the detail card. Arrow keys move through the list. **Show superseded copies** includes old versions of edited records (see below). A record that has several stored copies shows buttons to switch between them.
- **Table**: the records as a sortable table (the first 2,000 rows are drawn; the CSV copy includes all of them). Copy it as CSV, or copy the records as JSON.
- **Fields**: every field with its id, type, definition, form label, fill rate, number of distinct values and an example. Here you can rename fields, choose which fields make up a record's title and which gives its subtitle, and pick the table columns. Labels can be exported and imported as JSON (**Copy labels as JSON**, **Paste labels…**). These settings are saved per record type in this browser.
- **File**: header details, counts of current and superseded records per document type, the database's stop-word list, a summary of the file format, and the definition and layout files that are loaded.

The viewer picks a title field automatically: the short, almost always filled text field with the most distinct values (for Regulars, *Surname*, with *Forename* as the subtitle). Change it on the Fields tab.

If a database holds more than one document type, a selector next to the search box switches between them.

### Superseded copies

When a record was edited and re-saved, Idealist kept the old copy in the `.TEX` file and flagged it as superseded. Old copies aren't linked to the current record, so the viewer pairs them heuristically: same title and at least half of their filled values in common. Treat these pairings as a guide, not a certainty. (The `.ROT` file lists only current records, which confirms which copy is current but doesn't link the old ones.)

### Browser requirements

Any recent version of Chrome, Edge, Firefox or Safari. The page uses `TextDecoder('windows-1252')`, `<dialog>` and the Clipboard API. If the browser blocks clipboard access (some do for `file://` pages), the copy buttons say so.

## Command-line decoder

```bash
python3 tools/idealist_decode.py Regulars.tex regulars.json --def Regulars.def --lay Regulars.lay
```

- With no output file, the JSON is printed to standard output.
- By default only current records are written. Add `--all` to include superseded copies; each record has `"current": true` or `false`.
- `--def FILE` adds each field's definition name as `"name"`; `--lay FILE` adds its form label as `"label"`. Both are optional.

Each record looks like this:

```json
{
 "offset": 651,
 "current": true,
 "doctype": "Monks",
 "fields": [
  {"field": "0x3d7b", "type": "text", "value": "Edward", "name": "Forename", "label": "Forename"},
  {"field": "0x1f56", "type": "text", "value": "Deacon", "name": "O_Level", "label": "Ordained as"},
  {"field": "0x030c", "type": "number", "value": 1504.0, "name": "Year", "label": "Year"}
 ]
}
```

Numbers (`#` type) have two implied decimal places, so they come out as floats (`1504.0`); integers (`I` type) come out as integers.

## Published site (GitHub Pages)

The repository deploys a public site with the Seculars and Regulars databases built in, under the heading *Virginia Davis, Clergy in the Late Middle Ages: A Register of Clergy Ordained in the Diocese of London Based on Episcopal Ordination Lists 1361–1539 (London, Centre for Metropolitan History, 2000)*.

- **Switching databases:** buttons under the heading switch between *Secular clergy* and *Regular clergy*. Each database is downloaded the first time it is chosen, then kept in memory, so switching back is instant. The current tab is kept.
- **Links:** the database is in the URL, so links can point straight at one: `?db=seculars` or `?db=regulars`, optionally followed by a tab (`#browse`, `#table`, `#fields`, `#file`).
- **Download size:** the build stores a gzipped copy of each `.tex` (Seculars 6.7 MB → 0.9 MB, Regulars 3.2 MB → 0.3 MB). Browsers that can unpack gzip (all current ones) fetch that; others fetch the original.
- Everything else (search, table, fields, CSV/JSON export) works as in the standalone viewer. *Open files* is hidden.

### How it is built

[`pages/site.json`](pages/site.json) lists the heading, a short title for the browser tab, a subtitle, and each database's id, button label, description and file paths (relative to `pages/`):

```json
{
 "title": "Virginia Davis, Clergy in the Late Middle Ages: …",
 "short": "Clergy in the Late Middle Ages: …",
 "subtitle": "The original Idealist databases, searchable in your browser.",
 "databases": [
  {"id": "seculars", "label": "Secular clergy", "description": "Seculars database",
   "tex": "data/seculars/Seculars.tex", "def": "data/seculars/Seculars.def"},
  {"id": "regulars", "label": "Regular clergy", "description": "…",
   "tex": "data/regulars/Regulars.tex", "def": "data/regulars/Regulars.def", "lay": "data/regulars/Regulars.lay"}
 ]
}
```

The first database listed opens by default. Only `.tex`, `.def` and `.lay` files are published; the index files aren't needed.

[`tools/build_site.py`](tools/build_site.py) copies `index.html` into `_site/`, embeds the config in it as `<script type="application/json" id="collection">`, copies the data files and writes the gzipped copies. The viewer switches to collection mode only when that embedded config is present, so `index.html` on its own is unchanged.

The workflow in [`.github/workflows/pages.yml`](.github/workflows/pages.yml) runs the build and deploys `_site/` on every push to `main`, or by hand from the Actions tab. The repository's **Settings → Pages → Source** must be set to **GitHub Actions**.

To preview the site locally:

```bash
python3 tools/build_site.py
```

```bash
python3 -m http.server -d _site
```

Then open http://localhost:8000. (Opening `_site/index.html` directly from disk won't work, because browsers block `fetch` on `file://` pages.)

To publish a different set of databases, edit `pages/site.json` and put the files under `pages/data/`.

## Limitations

The format was reverse-engineered from three 1995 Idealist databases (the CMH Gazetteer, Regulars and Seculars). Other versions of Idealist may differ. Unrecognised field types are shown as text if printable, otherwise as hex. If a file doesn't open, the **File** tab reports how many bytes weren't recognised as records. See [`docs/FORMAT.md`](docs/FORMAT.md#open-questions) for what is still unknown.

## Licence

GNU General Public License v3.0. See [`LICENSE`](LICENSE).

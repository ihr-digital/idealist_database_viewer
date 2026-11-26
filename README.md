# Idealist Database Viewer

A single-page application for reading legacy **Blackwell Idealist** databases, built around the databases held by the Institute of Historical Research's Centre for Metropolitan History (CMH).

Idealist was a 1990s free-text database package for Windows. Its `.TEX` files are a proprietary binary format that modern software can't open. This viewer decodes them in the browser and turns them into searchable, browsable records. A small Python script does the same job on the command line and writes JSON.

## Contents

| Path | What it is |
| --- | --- |
| [`index.html`](index.html) | The viewer. One self-contained HTML file with no dependencies and no build step. |
| [`tools/idealist_decode.py`](tools/idealist_decode.py) | Command-line decoder: `.TEX` file in, JSON out. Python 3 standard library only. |
| [`docs/FORMAT.md`](docs/FORMAT.md) | What is known of the Idealist file formats (`.TEX`, `.DEF` and the index files). |

No database files are included. You need your own `.TEX` file.

## Using the viewer

1. Open `index.html` in a current desktop or mobile browser. You can double-click the file; it needs no web server and works offline.
2. Choose **Open files**, or drag files onto the page:
   - the database's **`.TEX`** file, which holds the records (required);
   - optionally its **`.DEF`** definition file, which supplies the real field names.
3. Browse, search and export.

Files are read locally in the browser. Nothing is uploaded anywhere.

### Field names and definition files

Idealist stores field ids, not field names, in the `.TEX` file. The names come from a definition file:

- The CMH project's `IDEALIST.DEF` is built into the viewer, so CMH databases get proper field names without extra files.
- For other databases, load their `.DEF` (for example `Regulars.def`) with the database or from the **Fields** tab. Loaded definition files are remembered in this browser (`localStorage`) and can be forgotten again from the Fields tab.
- Without a matching definition, fields are shown as *Field 1*, *Field 2* … and you can name them yourself.

The viewer matches a definition to the database by record type name, then matches fields by name hash. If fewer than half the hashes match and the field counts agree, it falls back to matching by position. The **Fields** tab reports which method was used.

The index files (`.TRM`, `.OCC`, `.ROT`, `.DIR`) aren't needed.

### Tabs

- **Browse**: a record list and a detail card. Search across all fields or one field; use `"quotes"` for phrases. Short values in a record have a **filter** button that narrows the list to records sharing that value; filters appear as removable chips. **Hide empty fields** tidies the detail card. Arrow keys move through the list. **Show superseded copies** includes old versions of edited records (see below). A record that has several stored copies shows buttons to switch between them.
- **Table**: the records as a sortable table (the first 2,000 rows are drawn; the CSV copy includes all of them). Copy it as CSV, or copy the records as JSON.
- **Fields**: every field with its id, type, definition, fill rate, distinct values and an example. Here you can rename fields, choose which fields make up a record's title and which gives its subtitle, and pick the table columns. Labels can be exported and imported as JSON (**Copy labels as JSON**, **Paste labels…**). These settings are saved per record type in this browser.
- **File**: header details, counts of current and superseded records per document type, the database's stop-word list, a summary of the file format and the definition files that are loaded.

If a database holds more than one document type, a selector next to the search box switches between them.

### Superseded copies

When a record was edited and re-saved, Idealist kept the old copy in the `.TEX` file and flagged it as superseded. Old copies aren't linked to the current record, so the viewer pairs them heuristically: same title and at least half of their filled values in common. Treat these pairings as a guide, not a certainty.

### Browser requirements

Any recent version of Chrome, Edge, Firefox or Safari. The page uses `TextDecoder('windows-1252')`, `<dialog>` and the Clipboard API. If the browser blocks clipboard access (some do for `file://` pages), the copy buttons say so.

## Command-line decoder

```bash
python3 tools/idealist_decode.py DATABASE.TEX out.json
```

- With no output file, the JSON is printed to standard output.
- By default only current records are written. Add `--all` to include superseded copies; each record has `"current": true` or `false`.

Each record looks like this (ids and values are illustrative):

```json
{
 "offset": 1234,
 "current": true,
 "doctype": "Market",
 "fields": [
  {"field": "0x1d4b", "type": "line of text", "value": "Chelmsford"},
  {"field": "0x0a31", "type": "number", "value": 12.5}
 ]
}
```

The script doesn't read `.DEF` files, so fields are identified by id. To map ids to names, see the field-id hash in [`docs/FORMAT.md`](docs/FORMAT.md#field-ids), or copy labels as JSON from the viewer's Fields tab.

## Limitations

The format was reverse-engineered from a single 1995 Idealist project. Other versions of Idealist may differ. Unrecognised field types are shown as text if printable, otherwise as hex. If a file doesn't open, the **File** tab reports how many bytes weren't recognised as records.

## Licence

GNU General Public License v3.0. See [`LICENSE`](LICENSE).

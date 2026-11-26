# Idealist file formats

What is known of the files written by Blackwell's Idealist for Windows. Everything here was reverse-engineered from three 1995 databases: the CMH Gazetteer of Markets and Fairs (`ESSEX.TEX` with the shared CMH `IDEALIST.DEF`), and the Regulars (all eight files) and Seculars (all but `.LAY`, plus `Stopword.lst` and `Synonym.lst`) databases behind Virginia Davis, *Clergy in the Late Middle Ages* (CMH, 2000). Other versions of Idealist may differ. Both the viewer (`index.html`) and the decoder (`tools/idealist_decode.py`) implement what is described here.

**Contents:** [Overview](#overview) · [`.TEX`](#tex-records) · [Field ids](#field-ids) · [`.DEF`](#def-definition-files) · [`.LAY`](#lay-layout-files) · [`.CMD`](#cmd-command-files) · [`.LST`](#lst-stop-word-and-synonym-lists) · [Index files](#index-files) · [Open questions](#open-questions)

## Overview

An Idealist database is a set of files sharing one base name. Extensions may be upper or lower case (`ESSEX.TEX`, `Regulars.tex`).

| File | Format | Contents | Needed to read records? |
| --- | --- | --- | --- |
| `.TEX` | Binary | The records | **Yes** |
| `.DEF` | Text | Record types, field names and field definitions. May be one shared `IDEALIST.DEF` instead of one per database. | Only for field names |
| `.LAY` | Text | Data-entry form layout: field labels and positions | Only for form labels |
| `.CMD` | Text | Commands run when the database opens | No |
| `Stopword.lst` | Text | Stop words; copied into the `.TEX` header | No |
| `Synonym.lst` | Text | Synonym groups for searching | No |
| `.ROT` | Binary | Record handle → `.TEX` offset | No |
| `.TRM` | Binary | Term (word) index, in 4 KB pages | No |
| `.DIR` | Binary | Directory into the `.TRM` pages | No |
| `.OCC` | Binary | Occurrence (posting) lists | No |

All binary integers are little-endian unless stated otherwise. Text files use Windows-1252 and CRLF line endings.

## `.TEX`: records

### File header

| Offset | Size | Contents |
| --- | --- | --- |
| 0 | 4 | Magic `iWin` |
| 6 | 2 | `0x04E4` (1252) in Regulars; probably the Windows code page |
| 8 | 6 | Date stamp (text, NUL-padded), e.g. `Jan95` |
| 46 | 2 | Length of the stop-word list (587 in Regulars and Seculars) |
| 64 | varies | Stop-word list: a copy of `Stopword.lst` (see [`.LST`](#lst-stop-word-and-synonym-lists)) |

The other header bytes are not understood (see [Open questions](#open-questions)).

Records follow the stop-word list, packed back to back (in Regulars, from offset 651 to the end of the file with no gaps). There is no record count or table of offsets in the `.TEX` file, so readers find the first record by scanning forward from offset 64 for a valid record header (see [Finding records](#finding-records)).

### Record header (8 bytes)

| Offset | Type | Contents |
| --- | --- | --- |
| 0 | `u16` | Low 16 bits of this record's own file offset (a consistency check) |
| 2 | `u16` | Record length in bytes, header included |
| 4 | `u16` | Flags: `0x0000` current, `0x8000` superseded |
| 6 | `u16` | Number of fields plus one |

### Fields

Fields follow the header, each as:

| Type | Contents |
| --- | --- |
| `u16` | Field id (see [Field ids](#field-ids)) |
| `u16` | Type code |
| `u16` | Value length *n* |
| *n* bytes | Value |

The list ends with a field whose id is `0`. Its value is the **document-type name** (a record type from the `.DEF` file, e.g. `Monks`), NUL-terminated.

Every record carries the full template for its document type, empty fields included (length 0). Fields are stored in the order the `.DEF` file lists them.

### Type codes

The low byte of the type code is an ASCII letter:

| Letter | Code | Meaning | `.DEF` name |
| --- | --- | --- | --- |
| `W` | `0x2057` | Wrapped text | `Wrapped text` |
| `T` | `0x2054` | Text | `Text` |
| `L` | `0x004C` | Line of text | `Line of text` |
| `#` | `0x0323` | Number (two implied decimals) | `Number` |
| `I` | `0x0749` | Integer | `Integer` |
| `D` | — | Date (seen in definitions; decoded as text) | |
| `N` | — | Name (seen in definitions; decoded as text) | |

**Numbers and integers** are 6 bytes: `05`, then a 24-bit **big-endian** value, then `00 00`. For `#` numbers, divide the value by 100. Example from Regulars: `05 02 4b 80 00 00` → `0x024B80` = 150400 → year 1504. An empty number has length 0.

**Text** is Windows-1252 with CRLF line breaks. Byte `0x0E` is a soft-wrap marker; it is removed (along with a preceding space, which is replaced by a single space).

Unknown types: the viewer shows the value as text if it is printable, otherwise as hex bytes.

### Superseded records

Idealist never rewrites a record in place. When a record is edited, the new version is appended and the old copy stays in the file with flag `0x8000`. Superseded copies carry no link to their replacement. The viewer pairs them heuristically: same title and at least half of their filled values in common. Regulars holds 894 superseded copies alongside 10,717 current records.

### Finding records

A position *q* holds a valid record header when all of these hold:

- the first `u16` equals `q & 0xFFFF`;
- the flags are `0x0000` or `0x8000`;
- the length is at least 14 and the record fits in the file;
- the field count is between 1 and 4000;
- walking the fields from *q* + 8 reaches a field id of `0` without any field running past the end of the record.

Readers scan forward byte by byte until the test passes, read the record, then jump by its length. If the test fails at the expected position, they resume scanning. Bytes skipped this way are counted on the viewer's File tab.

## Field ids

A field id is a 16-bit hash of the field's name in the definition file:

1. Upper-case the name.
2. If it is one or two characters long, the id is the characters themselves, low byte first: `M1` → `0x314D`.
3. Otherwise start with `h = 0` and, for each character, `h = ((h << 1) XOR char) & 0xFFFF`.

In Python:

```python
def field_id(name):
    s = name.upper()
    if len(s) <= 2:
        return ord(s[0]) | ((ord(s[1]) if len(s) > 1 else 0) << 8)
    h = 0
    for c in s:
        h = ((h << 1) ^ ord(c)) & 0xFFFF
    return h
```

Examples from Regulars: `Forename` → `0x3D7B`, `Ref` → `0x0184`, `Footnotes` → `0x7FD1`. All 14 of its field ids match their `.DEF` names this way.

Because the id depends only on the name, a `.DEF` or `.LAY` file can be matched to a `.TEX` file without relying on field order. Hash collisions are possible. When fewer than half of a database's field ids match the hashed names from its definition and the field counts agree, the viewer assigns names by position instead.

## `.DEF`: definition files

Plain text in INI-like sections. An installation may have a single shared `IDEALIST.DEF`, or each database may have its own (for example `Regulars.def`).

### `[records]`

One line per document type: the type name, then its field names in stored order, separated by spaces.

```
[records]
Default Text
Monks Forename Surname O_Level Worddate House Rel_Order Diocese Personid Place Ord_Bp Ceremony Ref Year Footnotes
```

A type can be defined without any records using it (Regulars' `Default` has none).

### `[fields]`

One line per field, sorted by name: the name, then `key=value` attributes or bare flags. A field name used by several record types is defined once.

```
[fields]
Ceremony Font="Courier" Points=10 Type="Number"
Forename Font="Courier New" MaxChars=20 Points=12 Type="Text"
Place Font="Courier" Points=10 Type="Wrapped text"
```

Attributes seen so far:

| Attribute | Meaning |
| --- | --- |
| `Type` | Data type: `Wrapped text`, `Text`, `Line of text`, `Number`, `Integer` (see [Type codes](#type-codes)) |
| `Font`, `Points` | Display font and size |
| `MaxChars` | Maximum length |
| `Format` | Display format |
| `Uppercase`, `InitialCaps` | Case conversion on entry |
| `Mandatory` | Field must be filled |

The viewer shows underscores in field names as spaces.

## `.LAY`: layout files

Plain text describing the data-entry form for each record type. Seen in Regulars (`Regulars.lay`).

```
:Monks
	"Forename"	3 6 80 26 Font="Times New Roman" Points=10
	{Forename}	62 8 131 22 Border
	"Ordained as "	5 122 103 27
	{O_Level}	79 123 115 21 Border
```

- A line starting with `:` begins a record type (`:Default`, `:Monks`).
- Each following line is indented with a tab and has the form *item* TAB *x y width height* [*attributes*]:
  - `"text"` is static text on the form (a label). It may be empty (`""`) or have leading or trailing spaces.
  - `{Field}` is a field box, named as in the `.DEF` file.
- Attributes seen: `Font="…"`, `Points=n` on text; `Border` on field boxes. Coordinates appear to be in pixels or dialog units from the form's top-left.

In Regulars every field box is directly preceded by its label, so the viewer and decoder take **the nearest non-empty static text before a field box** as that field's label. This turns internal names into the wording users saw:

| `.DEF` name | `.LAY` label |
| --- | --- |
| `O_Level` | Ordained as |
| `Worddate` | Date of ordination |
| `Rel_Order` | Religious Order |
| `Place` | Place of Ordination |
| `Ord_Bp` | Ordaining Bishop |
| `Ceremony` | Ceremony Number |
| `Ref` | Register Reference |

A form whose labels sit somewhere other than just before their boxes (say, all labels first) would need matching by position instead; none has been seen yet.

## `.CMD`: command files

Plain text holding Idealist commands, apparently run when the database is opened. `Regulars.cmd` holds a single command with no line ending:

```
SearchFindAllRecords()
```

It has no bearing on the data. `Seculars.cmd` is identical.

## `.LST`: stop-word and synonym lists

Seen with Seculars. Both are plain text with CRLF line endings and fixed names rather than the database's base name.

**`Stopword.lst`** lists the words left out of the index, one or more per line (`can cannot`), with blank lines between initial letters. The `.TEX` header holds a byte-for-byte copy of it: in Seculars, the 587 bytes from offset 64 to the first record at 651 are identical to `Stopword.lst`, and 587 is the `u16` at header offset 46. Regulars has the same 587-byte list.

**`Synonym.lst`** holds one synonym group per line: a quoted head term followed by its synonyms, quoting any that contain spaces:

```
"bbc" "british broadcasting corporation"
"centre" center
gray grey
```

The Seculars copy is evidently Blackwell's generic sample list (BBC, Blackwell Science, colours, Düsseldorf), not specific to the database. It has no bearing on the records.

## Index files

These four files make up Idealist's full-text index. They can be rebuilt from the `.TEX` file, and neither tool reads them; the viewer searches the decoded text directly. What has been established, from Regulars and Seculars:

### `.ROT`: record table

An array of `u32` offsets into the `.TEX` file, indexed by record handle. Unused handles are `0`.

`Regulars.rot` is 45,056 bytes = 11,264 slots. Its 10,717 non-zero entries are exactly the offsets of the 10,717 current records; superseded copies are not listed. `Seculars.rot` likewise has 20,480 slots, of which 20,246 hold exactly its current records. Entries are not in file order; how handles are allocated is not known.

### `.TRM`: term index

Fixed 4,096-byte pages (`Regulars.trm` is 96 pages, `Seculars.trm` 216). Page 0 is a header (`00 20 08 00 …` in Regulars, `00 20 0a 00 …` in Seculars). The other pages begin with a short header and hold packed term entries; the term text is not stored as plain strings, so the encoding is not yet decoded. Earlier notes describe the pages as a B-tree of *term + field id* keys.

### `.DIR`: term directory

An array of `u16` values: a variable number of slots, then 6 trailing values. In `Regulars.dir` (518 values) there are 512 slots holding page numbers into the `.TRM` file (1–47), then `15 15 5 6 7 8`. In `Seculars.dir` (1,286 values) there are 1,280 slots (page numbers 2–107), then `13 13 5 6 7 8`. Runs of repeated values suggest several hash or prefix slots share one page, as in an extendible-hashing directory. The trailing values are not understood.

### `.OCC`: occurrence lists

A chain of blocks, each starting with its total size as a `u32`. Walking the sizes covers `Regulars.occ` exactly (6,679 blocks), and `Seculars.occ` too (14,661 blocks). Block sizes follow the series 32, 80, 176, 368, 752, 1520, 3056, 6128, 12272 (each is twice the previous plus 16), so a list that outgrows its block is presumably moved to the next size up. Bytes 4–5 of a block hold a `u16` (likely a count) and bytes 6–7 are usually `0x8000` (6,556 of 6,679 blocks); the rest appears to be compressed record references.

## Open questions

- `.TEX` header bytes other than the magic, the `0x04E4` word, the date and the stop-list length. In both Regulars and Seculars: `u16 0x028C` (652) at 54 and `u16 0x01D2` (466) at 56; the first record starts at 651 (64 + 587). They differ in the `u32` at offset 26 (`0x2E1A7851` and `0xB8055DCB`), the `u16` at 58 (3 and 1) and the 4 bytes at 60.
- The `D` (date) and `N` (name) field types: their codes and storage have not been seen in a `.TEX` file.
- The entry encoding in `.TRM` pages and `.OCC` blocks, the `.OCC` block header, and the trailing values in `.DIR`.
- How `.ROT` record handles are allocated.
- Whether `.LAY` coordinates are pixels or dialog units, and what other attributes exist.
- Other `.CMD` commands.

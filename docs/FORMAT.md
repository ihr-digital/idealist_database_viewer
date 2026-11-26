# Idealist file formats

What is known of the files written by Blackwell's Idealist for Windows. Everything here was reverse-engineered from one 1995 CMH project; other versions may differ. Both the viewer (`index.html`) and the decoder (`tools/idealist_decode.py`) implement what is described here.

An Idealist database is a set of files sharing one base name:

| File | Contents | Needed to read records? |
| --- | --- | --- |
| `.TEX` | The records themselves | Yes |
| `.DEF` | Record types and field definitions (may be one shared `IDEALIST.DEF`) | Only for field names |
| `.ROT` | Maps record handles to offsets in the `.TEX` file | No |
| `.TRM` | B-tree of term + field-id keys (the word index) | No |
| `.OCC` | Posting lists for the terms | No |
| `.DIR` | Hash directory | No |

All integers are little-endian unless stated otherwise.

## `.TEX`: records

### File header

| Offset | Size | Contents |
| --- | --- | --- |
| 0 | 4 | Magic `iWin` |
| 8 | 6 | Date stamp (text, NUL-padded) |
| 64 | varies | Stop-word list: words left out of the index, separated by CRLF |

Records follow the stop-word list, packed back to back. There is no record count or table of offsets, so readers find the first record by scanning forward from offset 64 for a valid record header (see [Finding records](#finding-records)).

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

The list ends with a field whose id is `0`. Its value is the **document-type name** (for example a record type from the `.DEF` file), NUL-terminated.

Every record carries the full template for its document type, empty fields included (length 0).

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

**Numbers and integers** are 6 bytes: `05`, then a 24-bit **big-endian** value, then `00 00`. For `#` numbers, divide the value by 100.

**Text** is Windows-1252 with CRLF line breaks. Byte `0x0E` is a soft-wrap marker; it is removed (along with a preceding space, which is replaced by a single space).

Unknown types: the viewer shows the value as text if it is printable, otherwise as hex bytes.

### Superseded records

Idealist never rewrites a record in place. When a record is edited, the new version is appended and the old copy stays in the file with flag `0x8000`. Superseded copies carry no link to their replacement. The viewer pairs them heuristically: same title and at least half of their filled values in common.

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

Hash collisions are possible. When fewer than half of a database's field ids match the hashed names from its definition and the field counts agree, the viewer assigns names by position instead.

## `.DEF`: definition files

Plain text in INI-like sections. An installation may have a single shared `IDEALIST.DEF`, or each database may have its own (for example `Regulars.def`).

### `[records]`

One line per document type: the type name, then its field names in stored order, separated by spaces.

```
[records]
Book Author Title Date City Publisher Contents
```

### `[fields]`

One line per field: the name, then `key=value` attributes or bare flags.

```
[fields]
Volume Font="Arial" Points=10 Type="Number"
Zip Font="Arial" Points=10 Type="Text"
Year_Of_Charter_M3 Font="Arial" MaxChars=4 Points=10 Type="Number"
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

## Index files

`.ROT`, `.TRM`, `.OCC` and `.DIR` make up Idealist's full-text index. Their layouts have only been sketched (see the table at the top) and aren't needed: the viewer searches the decoded text directly.

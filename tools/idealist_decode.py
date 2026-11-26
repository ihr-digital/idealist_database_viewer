#!/usr/bin/env python3
"""Decode an Idealist .TEX database file into JSON.

Usage:  python3 idealist_decode.py DATABASE.TEX [out.json] [--all]
                                   [--def FILE.DEF] [--lay FILE.LAY]

By default only current records are written (flag 0x0000). With --all,
superseded/deleted copies (flag 0x8000) are included and marked.

--def adds each field's name from a definition file (.DEF) and --lay adds
its label from a layout file (.LAY). Fields are matched by name hash.

Record layout (little-endian):
  u16 self-offset (low 16 bits of file position), u16 length,
  u16 flags (0x8000 = superseded), u16 number of fields + 1,
  then fields: u16 field-id, u16 type, u16 length, bytes[length]
  until field-id 0.
Types (low byte is a letter): W 0x2057 wrapped text, T 0x2054 text,
L 0x004C line of text, # 0x0323 number (x100), I 0x0749 integer.
Numbers: 6 bytes = 0x05, 24-bit big-endian value, 0x00 0x00.
Text: Windows-1252, CRLF line breaks, 0x0E soft-wrap marker.
See docs/FORMAT.md for the full description.
"""
import json
import re
import struct
import sys

# The low byte of a type code is a letter.
TYPES = {"W": "wrapped text", "T": "text", "L": "line of text", "#": "number", "I": "integer", "D": "date", "N": "name"}


def type_name(typ):
    return TYPES.get(chr(typ & 0xFF), hex(typ))


def field_id(name):
    """Field ids are a 16-bit hash of the upper-cased field name; names of 1-2 characters are stored as the characters."""
    s = name.upper()
    if len(s) <= 2:
        return ord(s[0]) | ((ord(s[1]) if len(s) > 1 else 0) << 8)
    h = 0
    for c in s:
        h = ((h << 1) ^ ord(c)) & 0xFFFF
    return h


def read_text(path):
    return open(path, encoding="cp1252", errors="replace").read()


def parse_def(text):
    """Return {record type: [field names in stored order]} from a .DEF file's [records] section."""
    types, section = {}, ""
    for line in text.splitlines():
        line = line.strip()
        if re.fullmatch(r"\[.+\]", line):
            section = line[1:-1].lower()
        elif line and section == "records":
            name, *fields = line.split()
            types[name] = fields
    return types


def parse_lay(text):
    """Return {record type: {field name: label}} from a .LAY file. A field's label is the nearest non-empty static text before it."""
    types, cur, last = {}, None, ""
    for line in text.splitlines():
        if line.startswith(":"):
            cur, last = types.setdefault(line[1:].strip(), {}), ""
            continue
        m = re.match(r'\s*(?:"([^"]*)"|\{([^}]*)\})\s+-?\d+\s+-?\d+\s+-?\d+\s+-?\d+', line)
        if cur is None or not m:
            continue
        if m.group(1) is not None:
            last = m.group(1).strip().rstrip(":").strip() or last
        else:
            cur[m.group(2).strip()] = last
            last = ""
    return types


def lookup(table, doctype):
    """Case-insensitive lookup of a record type."""
    return next((v for k, v in table.items() if k.lower() == doctype.lower()), None)


def is_header(d, q):
    """Valid if the self-offset matches and the fields walk cleanly to a field-id 0 terminator."""
    if q + 14 > len(d):
        return False
    lo, ln, fl, nf = struct.unpack_from("<HHHH", d, q)
    if lo != q & 0xFFFF or fl not in (0, 0x8000) or ln < 14 or q + ln > len(d) or not 1 <= nf <= 4000:
        return False
    p, end = q + 8, q + ln
    while p + 6 <= end:
        tag, _, n = struct.unpack_from("<HHH", d, p)
        if p + 6 + n > end:
            return False
        if tag == 0:
            return True
        p += 6 + n
    return False


def decode_value(typ, b):
    if chr(typ & 0xFF) in "#I" and len(b) == 6:
        n = int.from_bytes(b[1:4], "big")
        return n / 100 if chr(typ & 0xFF) == "#" else n
    s = b.decode("cp1252", errors="replace").replace("\r\n", "\n")
    return s.replace(" \x0e", " ").replace("\x0e", " ")


def records(d):
    q = 0
    while q < len(d) - 12 and not is_header(d, q):
        q += 1
    while q < len(d) - 12:
        if not is_header(d, q):
            q += 1
            continue
        _, ln, fl, _ = struct.unpack_from("<HHHH", d, q)
        end, p, fields, doctype = min(q + ln, len(d)), q + 8, [], ""
        while p + 6 <= end:
            tag, typ, n = struct.unpack_from("<HHH", d, p)
            if tag == 0:
                doctype = d[p + 6:p + 6 + n].split(b"\0")[0].decode("cp1252")
                break
            val = decode_value(typ, d[p + 6:p + 6 + n]) if n else ""
            fields.append({"field": f"0x{tag:04x}", "type": type_name(typ), "value": val})
            p += 6 + n
        yield {"offset": q, "current": fl == 0, "doctype": doctype, "fields": fields}
        q += ln


def option(args, name):
    """Remove '--name VALUE' from args and return VALUE (or None)."""
    if name in args:
        i = args.index(name)
        if i + 1 >= len(args):
            sys.exit(f"{name} needs a file name")
        value = args[i + 1]
        del args[i:i + 2]
        return value
    return None


def main():
    args = sys.argv[1:]
    def_path, lay_path = option(args, "--def"), option(args, "--lay")
    show_all = "--all" in args
    args = [a for a in args if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    defs = parse_def(read_text(def_path)) if def_path else {}
    lays = parse_lay(read_text(lay_path)) if lay_path else {}
    data = open(args[0], "rb").read()
    recs = [r for r in records(data) if r["current"] or show_all]
    for r in recs:
        names = {f"0x{field_id(n):04x}": n for n in lookup(defs, r["doctype"]) or []}
        labels = {f"0x{field_id(n):04x}": l for n, l in (lookup(lays, r["doctype"]) or {}).items() if l}
        for f in r["fields"]:
            if f["field"] in names:
                f["name"] = names[f["field"]]
            if f["field"] in labels:
                f["label"] = labels[f["field"]]
    out = json.dumps(recs, ensure_ascii=False, indent=1)
    if len(args) > 1:
        open(args[1], "w", encoding="utf-8").write(out)
        print(f"{len(recs)} records written to {args[1]}")
    else:
        print(out)


if __name__ == "__main__":
    main()

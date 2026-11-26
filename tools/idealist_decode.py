#!/usr/bin/env python3
"""Decode an Idealist .TEX database file into JSON.

Usage:  python3 idealist_decode.py DATABASE.TEX [out.json] [--all]

By default only current records are written (flag 0x0000). With --all,
superseded/deleted copies (flag 0x8000) are included and marked.

Record layout (little-endian):
  u16 self-offset (low 16 bits of file position), u16 length,
  u16 flags (0x8000 = superseded), u16 number of fields + 1,
  then fields: u16 field-id, u16 type, u16 length, bytes[length]
  until field-id 0.
Types (low byte is a letter): W 0x2057 wrapped text, T 0x2054 text,
L 0x004C line of text, # 0x0323 number (x100), I 0x0749 integer.
Numbers: 6 bytes = 0x05, 24-bit big-endian value, 0x00 0x00.
Text: Windows-1252, CRLF line breaks, 0x0E soft-wrap marker.
"""
import json
import struct
import sys

# The low byte of a type code is a letter.
TYPES = {"W": "wrapped text", "T": "text", "L": "line of text", "#": "number", "I": "integer", "D": "date", "N": "name"}


def type_name(typ):
    return TYPES.get(chr(typ & 0xFF), hex(typ))


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


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    data = open(args[0], "rb").read()
    recs = [r for r in records(data) if r["current"] or "--all" in sys.argv]
    out = json.dumps(recs, ensure_ascii=False, indent=1)
    if len(args) > 1:
        open(args[1], "w", encoding="utf-8").write(out)
        print(f"{len(recs)} records written to {args[1]}")
    else:
        print(out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Le um arquivo intermediario WPS (Fortran unformatted, big-endian) e lista os
campos com nivel, unidade, min, max e media.

Uso: check_intermediate.py ECMWF:2026-08-29_00
"""
import struct
import sys

import numpy as np


def records(f):
    while True:
        head = f.read(4)
        if len(head) < 4:
            return
        n = struct.unpack(">i", head)[0]
        data = f.read(n)
        f.read(4)
        yield data


def read_fields(path):
    rows = []
    with open(path, "rb") as f:
        it = records(f)
        for version in it:
            hdr = next(it)
            hdate = hdr[:24].decode().strip()
            field = hdr[60:69].decode().strip()
            units = hdr[69:94].decode().strip()
            xlvl, nx, ny, iproj = struct.unpack(">fiii", hdr[140:156])
            next(it)  # projecao
            next(it)  # flag de vento
            a = np.frombuffer(next(it), dtype=">f4").reshape(ny, nx)
            rows.append((field, xlvl, units, float(a.min()), float(a.max()), float(a.mean()), nx, ny, hdate))
    rows.sort(key=lambda r: (r[0], -r[1]))
    return rows


def main(path):
    rows = read_fields(path)
    print("%-10s %9s %-8s %12s %12s %12s  grade  data" % ("campo", "nivel", "unid", "min", "max", "media"))
    for r in rows:
        print("%-10s %9.0f %-8s %12.4f %12.4f %12.4f  %dx%d %s" % r)
    print("total de registros:", len(rows))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])

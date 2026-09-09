#!/usr/bin/env python3
# check_intermediate.py ECMWF:2026-08-29_00
# lista campos de um intermediario WPS (fortran unformatted big endian) com min/max/media
import struct
import sys
import numpy as np

f = open(sys.argv[1], "rb")


def rec():
    h = f.read(4)
    if len(h) < 4:
        return None
    n = struct.unpack(">i", h)[0]
    d = f.read(n)
    f.read(4)
    return d


rows = []
while rec() is not None:
    hdr = rec()
    hdate = hdr[:24].decode().strip()
    field = hdr[60:69].decode().strip()
    units = hdr[69:94].decode().strip()
    xlvl, nx, ny, iproj = struct.unpack(">fiii", hdr[140:156])
    rec()
    rec()
    a = np.frombuffer(rec(), dtype=">f4").reshape(ny, nx)
    rows.append((field, xlvl, units, a.min(), a.max(), a.mean(), nx, ny, hdate))

rows.sort(key=lambda r: (r[0], -r[1]))
print("%-10s %9s %-8s %12s %12s %12s" % ("campo", "nivel", "unid", "min", "max", "media"))
for r in rows:
    print("%-10s %9.0f %-8s %12.4f %12.4f %12.4f  %dx%d %s" % r)
print(len(rows), "registros")

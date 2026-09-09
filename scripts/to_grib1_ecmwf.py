#!/usr/bin/env python3
# to_grib1_ecmwf.py entrada.simple.grib2 saida.grib1
# grib2 do ECMWF open data (ja em grid_simple) -> grib1 tabela 128 para a Vtable.ECMWF do WPS
import sys
import eccodes as ec

SFC = {"sp", "msl", "2t", "2d", "10u", "10v", "skt", "lsm", "sd", "z"}
PL = {"t", "u", "v", "r", "z", "gh"}
# a Vtable espera esses com tipo de nivel 1, nivel 0 (eccodes poria 102/105)
LEVEL1 = {"msl", "2t", "2d", "10u", "10v"}
# (shortName, nivel) -> (param grib1, topo cm, base cm)
SOIL = {
    ("sot", 1): (139, 0, 7), ("sot", 2): (170, 7, 28), ("sot", 3): (183, 28, 100), ("sot", 4): (236, 100, 255),
    ("vsw", 1): (39, 0, 7), ("vsw", 2): (40, 7, 28), ("vsw", 3): (41, 28, 100), ("vsw", 4): (42, 100, 255),
}

src, dst = sys.argv[1], sys.argv[2]

# skt em grib1 serve de molde pros campos de solo (sot/vsw nao tem equivalente grib1 no eccodes)
tpl = None
with open(src, "rb") as fi:
    while tpl is None:
        gid = ec.codes_grib_new_from_file(fi)
        if gid is None:
            sys.exit("sem skt no arquivo")
        if ec.codes_get(gid, "shortName") == "skt":
            ec.codes_set(gid, "edition", 1)
            tpl = ec.codes_clone(gid)
        ec.codes_release(gid)

n = 0
with open(src, "rb") as fi, open(dst, "wb") as fo:
    while True:
        gid = ec.codes_grib_new_from_file(fi)
        if gid is None:
            break
        sn = ec.codes_get(gid, "shortName")
        lt = ec.codes_get_long(gid, "typeOfFirstFixedSurface")
        lev = ec.codes_get(gid, "level")
        if (sn, lev) in SOIL:
            par, top, bot = SOIL[(sn, lev)]
            vals = ec.codes_get_values(gid)
            ec.codes_release(gid)
            gid = ec.codes_clone(tpl)
            ec.codes_set(gid, "indicatorOfParameter", par)
            ec.codes_set(gid, "table2Version", 128)
            ec.codes_set(gid, "indicatorOfTypeOfLevel", 112)
            ec.codes_set(gid, "topLevel", top)
            ec.codes_set(gid, "bottomLevel", bot)
            ec.codes_set(gid, "bitsPerValue", 16)
            ec.codes_set_values(gid, vals)
        elif (lt == 100 and sn in PL) or (lt in (1, 101, 103) and sn in SFC):
            ec.codes_set(gid, "edition", 1)
            if sn in LEVEL1:
                ec.codes_set(gid, "indicatorOfTypeOfLevel", 1)
                ec.codes_set(gid, "level", 0)
        else:
            ec.codes_release(gid)
            continue
        ec.codes_write(gid, fo)
        ec.codes_release(gid)
        n += 1
print(n, "mensagens")

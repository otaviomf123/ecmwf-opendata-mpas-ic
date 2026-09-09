#!/usr/bin/env python3
"""Converte o GRIB2 do ECMWF open data (passo 0h) para GRIB1 tabela 128,
no formato que a Vtable.ECMWF do WPS espera.

Uso: to_grib1_ecmwf.py entrada.grib2 saida.grib1

A entrada deve estar em packing grid_simple (ver make_ic.sh). Campos exportados:
  niveis de pressao: t u v r z gh
  superficie: sp msl 2t 2d 10u 10v skt lsm sd z
  solo: sot/vsw (4 camadas) -> stl1-4 / swvl1-4
"""
import sys
import eccodes as ec

WANT_SFC = {"sp", "msl", "2t", "2d", "10u", "10v", "skt", "lsm", "sd", "z"}
WANT_PL = {"t", "u", "v", "r", "z", "gh"}
# A Vtable.ECMWF pede estes campos com tipo de nivel 1 (superficie) e nivel 0;
# o eccodes, por padrao, gravaria 102 (msl) e 105 (altura acima do solo).
SFC_AS_LEVEL1 = {"msl", "2t", "2d", "10u", "10v"}
# (shortName, nivel) -> (parametro GRIB1, topo cm, base cm)
SOIL = {
    ("sot", 1): (139, 0, 7), ("sot", 2): (170, 7, 28), ("sot", 3): (183, 28, 100), ("sot", 4): (236, 100, 255),
    ("vsw", 1): (39, 0, 7), ("vsw", 2): (40, 7, 28), ("vsw", 3): (41, 28, 100), ("vsw", 4): (42, 100, 255),
}


def surface_template(path):
    """Mensagem GRIB1 de superficie (skt) usada como molde para os campos de solo."""
    with open(path, "rb") as fi:
        while True:
            gid = ec.codes_grib_new_from_file(fi)
            if gid is None:
                raise SystemExit("campo skt nao encontrado em %s" % path)
            if ec.codes_get(gid, "shortName") == "skt":
                ec.codes_set(gid, "edition", 1)
                tpl = ec.codes_clone(gid)
                ec.codes_release(gid)
                return tpl
            ec.codes_release(gid)


def main(src, dst):
    template = surface_template(src)
    n_out = 0
    with open(src, "rb") as fi, open(dst, "wb") as fo:
        while True:
            gid = ec.codes_grib_new_from_file(fi)
            if gid is None:
                break
            sn = ec.codes_get(gid, "shortName")
            lt = ec.codes_get_long(gid, "typeOfFirstFixedSurface")
            lev = ec.codes_get(gid, "level")
            keep = (lt == 100 and sn in WANT_PL) or (lt in (1, 101, 103) and sn in WANT_SFC) or (sn, lev) in SOIL
            if not keep:
                ec.codes_release(gid)
                continue
            if (sn, lev) in SOIL:
                par, top, bot = SOIL[(sn, lev)]
                vals = ec.codes_get_values(gid)
                ec.codes_release(gid)
                gid = ec.codes_clone(template)
                ec.codes_set(gid, "indicatorOfParameter", par)
                ec.codes_set(gid, "table2Version", 128)
                ec.codes_set(gid, "indicatorOfTypeOfLevel", 112)
                ec.codes_set(gid, "topLevel", top)
                ec.codes_set(gid, "bottomLevel", bot)
                ec.codes_set(gid, "bitsPerValue", 16)
                ec.codes_set_values(gid, vals)
            else:
                ec.codes_set(gid, "edition", 1)
                if sn in SFC_AS_LEVEL1:
                    ec.codes_set(gid, "indicatorOfTypeOfLevel", 1)
                    ec.codes_set(gid, "level", 0)
            ec.codes_write(gid, fo)
            ec.codes_release(gid)
            n_out += 1
    ec.codes_release(template)
    print("mensagens escritas:", n_out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])

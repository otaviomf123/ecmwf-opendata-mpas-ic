#!/bin/bash
# make_ic.sh YYYYMMDD HH [dir_saida]
# RES: 0p25 (padrao) ou 0p1
# WPS_DIR: dir do WPS (ungrib.exe); ECCODES_BIN: dir com grib_set e python com eccodes
set -euo pipefail

DATE=${1:?YYYYMMDD}
HH=${2:?HH}
RES=${RES:-0p25}
HERE=$(cd "$(dirname "$0")/.." && pwd)
WPS_DIR=${WPS_DIR:-$HOME/WPS}
ECCODES_BIN=${ECCODES_BIN:-$(dirname "$(command -v grib_set)")}
OUT=${3:-$HERE/data}/${DATE}${HH}

# 0p25 vem num arquivo so; 0p1 vem separado em niveis de pressao (-pl) e superficie (-sfc)
case $RES in
    0p25) PARTS="" ;;
    0p1) PARTS="-pl -sfc"; OUT=${OUT}_0p1 ;;
    *) echo "RES deve ser 0p25 ou 0p1" >&2; exit 1 ;;
esac

URL=https://storage.googleapis.com/ecmwf-open-data/${DATE}/${HH}z/ifs/${RES}/oper
BASE=ecmwf_oper_${DATE}_${HH}z_0h
mkdir -p "$OUT" && cd "$OUT"

fetch() { curl -sS -f -o "$2.part" "$1" && mv "$2.part" "$2"; }

RAW=""
for p in ${PARTS:-""}; do
    for ext in grib2 index; do
        [ -s $BASE$p.$ext ] || fetch "$URL/${DATE}${HH}0000-0h-oper-fc$p.$ext" $BASE$p.$ext
    done
    RAW="$RAW $BASE$p.grib2"
done

# ungrib nao le CCSDS
[ -s $BASE.simple.grib2 ] || "$ECCODES_BIN/grib_set" -r -s packingType=grid_simple $RAW $BASE.simple.grib2
"$ECCODES_BIN/python" "$HERE/scripts/to_grib1_ecmwf.py" $BASE.simple.grib2 $BASE.grib1

rm -rf ungrib && mkdir ungrib && cd ungrib
cp "$HERE/vtables/Vtable.ECMWF" Vtable
ln -sf ../$BASE.grib1 GRIBFILE.AAA
sed "s/@DATE@/${DATE:0:4}-${DATE:4:2}-${DATE:6:2}_${HH}:00:00/g" "$HERE/templates/namelist.wps" > namelist.wps
"$WPS_DIR/ungrib.exe" > ungrib.stdout 2>&1
tail -1 ungrib.log
"$ECCODES_BIN/python" "$HERE/scripts/check_intermediate.py" ECMWF:* | tail -1

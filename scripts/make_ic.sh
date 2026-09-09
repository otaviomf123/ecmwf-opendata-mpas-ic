#!/bin/bash
# make_ic.sh YYYYMMDD HH [dir_saida]
# WPS_DIR: dir do WPS (ungrib.exe); ECCODES_BIN: dir com grib_set e python com eccodes
set -euo pipefail

DATE=${1:?YYYYMMDD}
HH=${2:?HH}
HERE=$(cd "$(dirname "$0")/.." && pwd)
WPS_DIR=${WPS_DIR:-$HOME/WPS}
ECCODES_BIN=${ECCODES_BIN:-$(dirname "$(command -v grib_set)")}
OUT=${3:-$HERE/data}/${DATE}${HH}

URL=https://storage.googleapis.com/ecmwf-open-data/${DATE}/${HH}z/ifs/0p25/oper
BASE=ecmwf_oper_${DATE}_${HH}z_0h
mkdir -p "$OUT" && cd "$OUT"

[ -s $BASE.grib2 ] || curl -sS -o $BASE.grib2 "$URL/${DATE}${HH}0000-0h-oper-fc.grib2"
[ -s $BASE.index ] || curl -sS -o $BASE.index "$URL/${DATE}${HH}0000-0h-oper-fc.index"

# ungrib nao le CCSDS
[ -s $BASE.simple.grib2 ] || "$ECCODES_BIN/grib_set" -r -s packingType=grid_simple $BASE.grib2 $BASE.simple.grib2
"$ECCODES_BIN/python" "$HERE/scripts/to_grib1_ecmwf.py" $BASE.simple.grib2 $BASE.grib1

rm -rf ungrib && mkdir ungrib && cd ungrib
cp "$HERE/vtables/Vtable.ECMWF" Vtable
ln -sf ../$BASE.grib1 GRIBFILE.AAA
sed "s/@DATE@/${DATE:0:4}-${DATE:4:2}-${DATE:6:2}_${HH}:00:00/g" "$HERE/templates/namelist.wps" > namelist.wps
"$WPS_DIR/ungrib.exe" > ungrib.stdout 2>&1
tail -1 ungrib.log
python3 "$HERE/scripts/check_intermediate.py" ECMWF:* | tail -1

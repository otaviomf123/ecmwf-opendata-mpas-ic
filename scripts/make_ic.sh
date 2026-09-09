#!/bin/bash
# Gera o intermediario WPS (ungrib) de uma analise do ECMWF open data (IFS 0.25 graus,
# passo 0h) usando a Vtable.ECMWF padrao do WPS.
#
# Uso: make_ic.sh YYYYMMDD HH [dir_saida]
#
# Variaveis de ambiente (opcionais):
#   WPS_DIR      diretorio do WPS compilado (ungrib.exe)
#   ECCODES_BIN  diretorio com grib_set e python com eccodes (ex.: bin de um env conda)
#   OUT_ROOT     raiz de saida (padrao: ./data)
set -euo pipefail

DATE=${1:?informe a data YYYYMMDD}
HH=${2:?informe a hora 00/06/12/18}
HERE=$(cd "$(dirname "$0")/.." && pwd)
WPS_DIR=${WPS_DIR:-$HOME/WPS}
ECCODES_BIN=${ECCODES_BIN:-$(dirname "$(command -v grib_set)")}
OUT_ROOT=${3:-${OUT_ROOT:-$HERE/data}}

URL=https://storage.googleapis.com/ecmwf-open-data/${DATE}/${HH}z/ifs/0p25/oper
RAW=ecmwf_oper_${DATE}_${HH}z_0h.grib2
BASE=${RAW%.grib2}
B=$OUT_ROOT/${DATE}${HH}
mkdir -p "$B" && cd "$B"

echo "[1/4] download"
[ -s "$RAW" ] || curl -sS -o "$RAW" "$URL/${DATE}${HH}0000-0h-oper-fc.grib2"
[ -s "$BASE.index" ] || curl -sS -o "$BASE.index" "$URL/${DATE}${HH}0000-0h-oper-fc.index"

echo "[2/4] CCSDS -> grid_simple"
[ -s "$BASE.simple.grib2" ] || "$ECCODES_BIN/grib_set" -r -s packingType=grid_simple "$RAW" "$BASE.simple.grib2"

echo "[3/4] GRIB2 -> GRIB1 (tabela 128)"
"$ECCODES_BIN/python" "$HERE/scripts/to_grib1_ecmwf.py" "$BASE.simple.grib2" "$BASE.grib1"

echo "[4/4] ungrib"
rm -rf ungrib && mkdir ungrib && cd ungrib
cp "$HERE/vtables/Vtable.ECMWF" Vtable
ln -sf "../$BASE.grib1" GRIBFILE.AAA
sed "s/@DATE@/${DATE:0:4}-${DATE:4:2}-${DATE:6:2}_${HH}:00:00/g" "$HERE/templates/namelist.wps" > namelist.wps
"$WPS_DIR/ungrib.exe" > ungrib.stdout 2>&1
tail -1 ungrib.log
python3 "$HERE/scripts/check_intermediate.py" ECMWF:* | tail -1
echo "intermediario em $B/ungrib"

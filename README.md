# ecmwf-opendata-mpas-ic

Condicao inicial para o MPAS/MONAN a partir do ECMWF open data (analise IFS a
0,25 grau), processada pelo `ungrib` do WPS com a `Vtable.ECMWF` padrao.

O open data e distribuido em GRIB2 com dois detalhes que impedem o uso direto no
`ungrib`:

1. A compressao e CCSDS (DRS template 42), que o WPS (testado com 4.6) nao le.
   O `ungrib` termina sem erro e gera um intermediario vazio.
2. A `Vtable.ECMWF` foi escrita para GRIB1 tabela 128. Com o GRIB2 reempacotado o
   `ungrib` so reconhece TT, UU, VV, RH, GHT, PSFC, PMSL e LANDSEA. Solo (`sot`,
   `vsw`, tipo de nivel 151), SKINTEMP, neve e orografia ficam de fora.

A solucao adotada converte o arquivo para GRIB1 com codigos da tabela 128 usando o
eccodes. A Vtable nao e alterada. Dois cuidados na conversao:

- `msl`, `2t`, `2d`, `10u`, `10v` sao gravados com tipo de nivel 1 e nivel 0, como a
  Vtable espera (o eccodes gravaria 102 e 105).
- `sot` e `vsw` viram `stl1-4` e `swvl1-4` (parametros 139/170/183/236 e 39/40/41/42,
  tipo de nivel 112, camadas 0-7, 7-28, 28-100 e 100-255 cm).

## Requisitos

- WPS compilado (`ungrib.exe`)
- eccodes com a interface Python (`grib_set` e `import eccodes`)
- Python 3 com numpy
- curl

## Uso

```bash
export WPS_DIR=/caminho/para/WPS
export ECCODES_BIN=/caminho/para/env/bin   # onde estao grib_set e python com eccodes
scripts/make_ic.sh 20260829 00
```

Etapas executadas:

1. download de `<data><hora>0000-0h-oper-fc.grib2` do bucket publico
   `storage.googleapis.com/ecmwf-open-data` (sem credencial)
2. `grib_set -r -s packingType=grid_simple`
3. `scripts/to_grib1_ecmwf.py` (GRIB2 para GRIB1 tabela 128)
4. `ungrib.exe` com `vtables/Vtable.ECMWF` e `templates/namelist.wps`

Saida em `data/<data><hora>/ungrib/ECMWF:<AAAA-MM-DD_HH>`. Para conferir o
conteudo:

```bash
scripts/check_intermediate.py data/2026082900/ungrib/ECMWF:2026-08-29_00
```

## Campos no intermediario

Grade regular 0,25 grau, 1440 x 721, 88 registros.

| grupo | campos |
| --- | --- |
| 3D, 14 niveis (1000 a 10 hPa) | TT, UU, VV, RH, HGT |
| superficie | PSFC, PMSL, SKINTEMP, LANDSEA, SOILHGT, SNOW, TT/UU/VV/RH a 2 m e 10 m |
| solo, 4 camadas | ST000007, ST007028, ST028100, ST100289, SM000007, SM007028, SM028100, SM100289 |

Nao existem no open data: SST e SEAICE. O `init_atmosphere_model` usa SKINTEMP
como SST quando SST nao esta presente e deixa a fracao de gelo em zero quando nao
ha arquivo `SEAICE_FRACTIONAL`. O arquivo original traz `sithick` (espessura de
gelo), que pode servir de base para um campo SEAICE se necessario.

## namelist.init_atmosphere

Ver `templates/namelist.init_atmosphere.snippet`:

- `config_met_prefix = 'ECMWF'`
- `config_nfglevels = 15`
- `config_nfgsoillevels = 4`
- `config_fg_interval = 21600`
- `config_use_spechumd = false`

## Limitacoes

- O open data e um produto reduzido: 14 niveis de pressao e 0,25 grau. A analise
  completa do IFS (137 niveis de modelo, ~9 km) so esta disponivel pelo MARS.
- A umidade relativa do IFS em niveis de pressao sai do intervalo 0-100 %
  (aproximadamente -5 a 112 %), como acontece com o ERA5.
- Apenas o passo 0h e tratado. Para condicoes de contorno seria preciso repetir
  a conversao nos passos seguintes e ajustar `interval_seconds`.

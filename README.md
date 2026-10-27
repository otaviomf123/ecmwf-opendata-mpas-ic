# ecmwf-opendata-mpas-ic

Scripts para gerar condicao inicial do MPAS/MONAN a partir do ECMWF open data
(analise IFS a 0.25 ou 0.1 grau, passo 0h) com o ungrib do WPS e a Vtable.ECMWF
padrao.

O grib2 do open data nao entra direto no ungrib por dois motivos:

- vem comprimido em CCSDS (DRS template 42) e o WPS 4.6 nao le. O ungrib roda
  sem erro e o intermediario sai vazio.
- a Vtable.ECMWF do WPS foi feita para GRIB1 tabela 128. Com o grib2 reempacotado
  ela so pega TT, UU, VV, RH, GHT, PSFC, PMSL e LANDSEA. Solo (sot/vsw, tipo de
  nivel 151), skt, neve e orografia ficam de fora.

Entao o arquivo e convertido para GRIB1 tabela 128 com o eccodes e a Vtable fica
como esta. Na conversao msl, 2t, 2d, 10u e 10v sao gravados com tipo de nivel 1 e
nivel 0 (a Vtable espera assim, o eccodes poria 102/105) e sot/vsw viram
stl1-4/swvl1-4 (139/170/183/236 e 39-42, tipo de nivel 112, camadas
0-7/7-28/28-100/100-255 cm).

## Como usar

Precisa de WPS compilado, eccodes com python (grib_set e import eccodes, que ja
traz numpy) e curl.

```
export WPS_DIR=/caminho/do/WPS
export ECCODES_BIN=/caminho/do/env/bin
scripts/make_ic.sh 20260829 00            # 0.25 grau
RES=0p1 scripts/make_ic.sh 20261027 00    # 0.1 grau
```

O script baixa o grib2 do bucket storage.googleapis.com/ecmwf-open-data (sem
credencial), reempacota com grib_set, converte com scripts/to_grib1_ecmwf.py e
roda o ungrib. A saida fica em data/2026082900/ungrib/ECMWF:2026-08-29_00 (a 0.1
grau o diretorio recebe o sufixo _0p1: data/2026102700_0p1/...). O terceiro
argumento troca o diretorio base data/.

Para listar os campos do intermediario com min/max:

```
scripts/check_intermediate.py data/2026082900/ungrib/ECMWF:2026-08-29_00
```

## Resolucoes

- 0p25: grade 1440x721, um arquivo por passo (`-0h-oper-fc.grib2`, ~140 MB).
  Disponivel desde o inicio do open data.
- 0p1: grade 3600x1801, dois arquivos por passo (`-0h-oper-fc-pl.grib2` com os
  niveis de pressao, ~360 MB, e `-0h-oper-fc-sfc.grib2` com superficie e solo,
  ~80 MB). O bucket passou a ter o 0p1 em 20/10/2026 06 UTC; datas anteriores
  so a 0.25. O grib_set recebe os dois arquivos e grava um so reempacotado.

Nas duas resolucoes o 0h traz os mesmos campos usados aqui. O 0p1 tem extras
(100u/100v, mucape, rajada, radiacao, nuvens) que o conversor ignora.

## O que sai

88 registros na grade regular da resolucao escolhida:

- 14 niveis de pressao (1000 a 10 hPa): TT, UU, VV, RH, HGT
- superficie: PSFC, PMSL, SKINTEMP, LANDSEA, SOILHGT, SNOW e TT/UU/VV/RH em 2m/10m
- solo em 4 camadas: ST000007 ST007028 ST028100 ST100289 e SM000007 SM007028 SM028100 SM100289

Tamanho do intermediario: 349 MB a 0.25 grau, 2.2 GB a 0.1 grau.

Nao tem SST nem SEAICE no open data. O init_atmosphere_model usa SKINTEMP no
lugar da SST e deixa xice = 0 quando nao encontra o arquivo SEAICE_FRACTIONAL.
Se precisar de gelo, o grib2 original traz sithick (espessura, nao fracao).

No namelist.init_atmosphere: config_met_prefix = 'ECMWF', config_nfglevels = 15,
config_nfgsoillevels = 4, config_fg_interval = 21600, config_use_spechumd = false
(ver templates/).

Observacoes: o open data tem so 14 niveis de pressao (a analise completa do IFS
so via MARS); o RH do IFS em niveis de pressao passa de 100% e fica um pouco
negativo em alguns pontos, igual ao ERA5; so o passo 0h e tratado. Em GRIB1 a
mensagem tem no maximo 16 MB, o que a 0.1 grau cabe porque o open data usa ate
16 bits por valor.

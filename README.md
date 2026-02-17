# Detecção Automática de Mudas de Eucalipto em Imagens Aéreas

Este projeto apresenta uma solução para identificar automaticamente mudas de eucalipto
em imagens aéreas RGB georreferenciadas no formato **GeoTIFF (.tif)**, gerando como saída
geometrias georreferenciadas e estatísticas descritivas da área analisada.

---

## Objetivo

- Receber uma imagem **RGB georreferenciada (GeoTIFF)**  
- Identificar automaticamente a presença de mudas de eucalipto  
- Retornar:
  - Um arquivo **GeoJSON** com a localização das mudas
  - Um arquivo **JSON** com estatísticas do resultado

---

## Entrada

- Arquivo: `*.tif`
- Tipo: Imagem RGB georreferenciada
- Sistema de referência: definido no próprio raster (ex: `EPSG:32722`)

---

## Saídas

### GeoJSON ('*_eucaliptos.geojson')
Contém pontos georreferenciados representando as mudas identificadas.

### JSON ('*_statics.json')
Arquivo JSON com métricas da detecção.

Campos:

  - total_plants: número total de mudas identificadas

  - area_analyzed_ha: área analisada (hectares)

  - plants_per_hectare: média de mudas por hectare

  - crs: sistema de referência espacial

## Execução:
  - Via Python: python main.py caminho/para/imagem.tif

  - Via Docker: docker run --rm -v $(pwd):/app challenge-bem-agro caminho/para/imagem.tif 

## Melhorias:
 - Melhorar a metodologia de detecção, podendo implementar tecnologia de tratamento de imagem (CNNs, filtros, etc) para facilitar a detecçao das árvores. 

 - Métodos para detecção de sombras e mudança de cores (relacionado ao tópico anterior)
 
 - Para informações sobre a homogeneidade do plantio, métricas da distância dos centróides e tamanho das 'manchas' poderiam fornecer este tipo de dado, porém pode conter ruido por falhas do método de detecção, sendo secundários para a implementação neste momento. 


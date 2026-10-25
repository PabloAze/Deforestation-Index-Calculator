# Deforestation Index Calculator

Aplicação Streamlit para carregar um GeoTIFF, visualizar uma composição RGB e calcular resultados demonstrativos usando NDVI e o filtro passa-alta Laplaciano.

## Funcionalidades

- Upload de arquivos `.tif` e `.tiff` pela interface.
- Exibição de dimensões, CRS, resolução, área por pixel e contagem de pixels válidos e inválidos.
- Composição RGB com as bandas 3, 2 e 1, com ajuste de contraste pelos percentis 2 e 98.
- Visualização do NDVI e da magnitude do Laplaciano.
- Campos para ajustar os limiares dos dois processamentos.
- Contagem de pixels classificados, estimativa de área em m² e km², percentual do raster total e percentual dos pixels válidos.

Os processamentos têm finalidade representativa em testes controlados. As áreas calculadas correspondem às máscaras produzidas pelos limiares escolhidos.

## Executar com Docker

Na raiz do projeto, construa a imagem:

```bash
docker build -t deforestation-index-calculator .
```

Inicie o container expondo a porta 8501:

```bash
docker run --rm -p 8501:8501 deforestation-index-calculator
```

Abra <http://localhost:8501> no navegador e envie um arquivo GeoTIFF pela interface.

O Dockerfile usa `python:3.12-slim`, instala `libexpat1` (dependência de sistema usada pelo Rasterio), instala os pacotes de `requirements.txt` e inicia o Streamlit em `0.0.0.0:8501`. Para reconstruir a imagem sem usar camadas de dependências em cache:

```bash
docker build --no-cache -t deforestation-index-calculator .
```

O arquivo é processado em memória durante a sessão. A aplicação não lê automaticamente das pastas `Input`, `Output` ou `Imagens`, nem grava os resultados nelas. Essas pastas são excluídas do contexto Docker pelo `.dockerignore`.

## Entradas esperadas

- GeoTIFF com pelo menos quatro bandas: vermelho na banda 3 e infravermelho próximo (NIR) na banda 4 para o NDVI.
- CRS projetado com unidades em metros, necessário para apresentar as áreas em m² e km².
- A visualização RGB e o Laplaciano usam as bandas 3 (vermelho), 2 (verde) e 1 (azul).

Os valores padrão dos limiares são `0,2` para NDVI e `30,0` para Laplaciano. A interface permite alterá-los após carregar um arquivo.

## Processamentos no backend

### NDVI

O módulo `src/ndviCalc.py` lê as bandas vermelha e NIR e calcula, para cada pixel válido:

```text
NDVI = (NIR - vermelho) / (NIR + vermelho)
```

Pixels com valores inválidos, não finitos ou denominador igual a zero são excluídos. A máscara de pixels potencialmente sem vegetação inclui os pixels cujo NDVI é **menor** que o limiar definido pelo usuário (padrão `0,2`). O resultado é visualizado com a paleta `RdYlGn`.

### Passa-alta Laplaciano

O módulo `src/passa_alta.py` recebe a composição RGB preparada por `src/rgb.py`. Cada banda é normalizada independentemente usando os percentis 2 e 98 dos pixels válidos. Em seguida, usa o maior valor entre os canais RGB como intensidade e aplica uma vizinhança 3×3:

```text
-1  -1  -1
-1   8  -1
-1  -1  -1
```

A magnitude é o valor absoluto da resposta do filtro. A máscara inclui os pixels válidos cuja magnitude é **maior ou igual** ao limiar definido (padrão `30,0`). A imagem do resultado usa a paleta `inferno`.

### Métricas de área

`src/fileHandler.py` centraliza as métricas calculadas a partir de cada máscara. A área de um pixel é `abs(resolução_x × resolução_y)`; a área classificada é o número de pixels da máscara multiplicado por essa área. A conversão para km² divide o valor em m² por 1.000.000.

- **Percentual da área total:** pixels classificados divididos por todos os pixels do raster.
- **Percentual dos pixels válidos:** pixels classificados divididos pelos pixels válidos para aquele processamento.

Pixels inválidos não entram na máscara classificada. Cada processamento usa seus próprios critérios de validade; por isso, a quantidade de pixels válidos pode variar entre a informação geral do arquivo e as análises.

## Estrutura do projeto

```text
.
├── Dockerfile
├── requirements.txt
└── src/
    ├── main.py          # Interface Streamlit e coordenação do fluxo
    ├── fileHandler.py   # Validação do GeoTIFF e métricas de área
    ├── rgb.py           # Preparação da composição RGB
    ├── ndviCalc.py      # Cálculo e visualização do NDVI
    └── passa_alta.py    # Filtro Laplaciano e classificação por limiar
```

import numpy as np
import matplotlib.pyplot as plt
from fileHandler import calcular_metricas_area

def processar_ndvi(src, limiar=0.2, banda_red=3, banda_nir=4):
    """
    Calcula o NDVI e estima a área potencialmente sem vegetação.

    Parâmetros:
        src: raster aberto pelo Rasterio.
        limiar: valor abaixo do qual o pixel será classificado.
        banda_red: índice Rasterio da banda vermelha.
        banda_nir: índice Rasterio da banda NIR.

    Retorna:
        Dicionário com imagem, máscaras e métricas.
    """

    if src.count < max(banda_red, banda_nir):
        raise ValueError("O raster não possui as bandas necessárias.")

    # Lê as bandas originais
    red = src.read(banda_red).astype(np.float32)
    nir = src.read(banda_nir).astype(np.float32)

    # Identifica pixels válidos nas duas bandas
    mascara_valida = (
        (src.read_masks(banda_red) > 0)
        & (src.read_masks(banda_nir) > 0)
        & np.isfinite(red)
        & np.isfinite(nir)
    )

    denominador = nir + red

    mascara_valida &= (
        np.isfinite(denominador)
        & (denominador != 0)
    )

    # Calcula o NDVI apenas nos pixels válidos
    ndvi = np.full(red.shape, np.nan, dtype=np.float32)

    ndvi[mascara_valida] = (
        (nir[mascara_valida] - red[mascara_valida])
        / denominador[mascara_valida]
    )

    # Classifica pixels abaixo do limiar
    mascara_sem_vegetacao = (
        mascara_valida & (ndvi < limiar)
    )

    metricas_area = calcular_metricas_area(
        src,
        mascara_valida,
        mascara_sem_vegetacao,
    )
    if metricas_area["pixels_validos"] == 0:
        raise ValueError(
            "Não existem pixels válidos para calcular o NDVI."
        )

    # Gera a imagem colorida para o st.image()
    fig, ax = plt.subplots(figsize=(10, 7))

    imagem = ax.imshow(
        ndvi,
        cmap="RdYlGn",
        vmin=-1,
        vmax=1
    )

    fig.colorbar(imagem, ax=ax, label="NDVI")
    ax.set_title("Índice de Vegetação (NDVI)")
    ax.axis("off")

    fig.tight_layout()
    fig.canvas.draw()

    imagem_rgb = np.asarray(
        fig.canvas.buffer_rgba()
    )[:, :, :3].copy()

    plt.close(fig)

    return {
        "imagem": imagem_rgb,
        "mascara_valida": mascara_valida,
        "mascara_sem_vegetacao": mascara_sem_vegetacao,
        **metricas_area,
        # Aliases mantidos para compatibilidade com quem usa o retorno atual.
        "total_pixels": metricas_area["pixels_totais"],
        "area_raster_km2": metricas_area["area_total_km2"],
        "area_classificada_ha": metricas_area["area_classificada_m2"] / 10_000,
        "percentual_classificado": metricas_area["percentual_area_valida"],
        "limiar": limiar,
        "resolucao": src.res,
    }

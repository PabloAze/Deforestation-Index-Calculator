import numpy as np
import matplotlib.pyplot as plt

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

    if src.crs is None or not src.crs.is_projected:
        raise ValueError(
            "É necessário um CRS projetado para calcular a área."
        )

    unidade = src.crs.linear_units.lower()

    if unidade not in ("metre", "meter", "metres", "meters"):
        raise ValueError(
            "O cálculo da área exige resolução em metros."
        )

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

    pixels_validos = np.count_nonzero(mascara_valida)

    if pixels_validos == 0:
        raise ValueError(
            "Não existem pixels válidos para calcular o NDVI."
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

    quantidade_pixels = np.count_nonzero(
        mascara_sem_vegetacao
    )

    # Cálculo das áreas
    area_pixel = abs(src.res[0] * src.res[1])

    total_pixels = ndvi.size
    area_raster = total_pixels * area_pixel
    area_valida = pixels_validos * area_pixel
    area_classificada = quantidade_pixels * area_pixel

    percentual_sem_vegetacao = (
        quantidade_pixels / pixels_validos
    ) * 100

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
        "ndvi": ndvi,
        "imagem": imagem_rgb,
        "mascara_valida": mascara_valida,
        "mascara_sem_vegetacao": mascara_sem_vegetacao,
        "total_pixels": total_pixels,
        "pixels_validos": pixels_validos,
        "pixels_invalidos": total_pixels - pixels_validos,
        "pixels_classificados": quantidade_pixels,
        "area_raster_km2": area_raster / 1_000_000,
        "area_valida_km2": area_valida / 1_000_000,
        "area_pixel_m2": area_pixel,
        "area_classificada_m2": area_classificada,
        "area_classificada_ha": area_classificada / 10_000,
        "area_classificada_km2": area_classificada / 1_000_000,
        "percentual_classificado": percentual_sem_vegetacao,
        "limiar": limiar,
        "resolucao": src.res,
    }

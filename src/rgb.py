import numpy as np

def generate_composicao(
    src,
    banda_red=3,
    banda_green=2,
    banda_blue=1,
    percentil_min=2,
    percentil_max=98,
):
    """
    Gera uma imagem RGB a partir de um raster aberto pelo Rasterio.

    Retorna:
        Tupla com a imagem RGB uint8 e a máscara de pixels válidos.
    """

    # Leitura das bandas
    red = src.read(banda_red).astype(np.float32)
    green = src.read(banda_green).astype(np.float32)
    blue = src.read(banda_blue).astype(np.float32)

    # Pixels válidos nas três bandas
    mascara_valida = (
        (src.read_masks(banda_red) > 0)
        & (src.read_masks(banda_green) > 0)
        & (src.read_masks(banda_blue) > 0)
        & np.isfinite(red)
        & np.isfinite(green)
        & np.isfinite(blue)
    )

    if not np.any(mascara_valida):
        raise ValueError(
            "Não existem pixels RGB válidos para visualizar."
        )

    def normalizar(banda):
        valores = banda[mascara_valida]

        minimo, maximo = np.percentile(
            valores,
            [percentil_min, percentil_max]
        )

        # Evita divisão por zero
        if maximo <= minimo:
            resultado = np.zeros(banda.shape, dtype=np.uint8)
        else:
            normalizada = (banda[mascara_valida] - minimo) / (maximo - minimo)
            resultado = np.zeros(banda.shape, dtype=np.uint8)
            resultado[mascara_valida] = (
                np.clip(normalizada, 0, 1) * 255
            ).astype(np.uint8)

        return resultado

    # Ajuste de contraste independente para cada banda
    red = normalizar(red)
    green = normalizar(green)
    blue = normalizar(blue)

    # Combina as bandas na ordem RGB
    imagem_rgb = np.dstack((red, green, blue))

    # Exibe pixels inválidos em preto
    imagem_rgb[~mascara_valida] = 0

    return imagem_rgb, mascara_valida


def generate(
    src,
    banda_red=3,
    banda_green=2,
    banda_blue=1,
    percentil_min=2,
    percentil_max=98,
):
    """Gera uma imagem RGB, mantendo a interface simples para outros usos."""
    imagem_rgb, _ = generate_composicao(
        src,
        banda_red=banda_red,
        banda_green=banda_green,
        banda_blue=banda_blue,
        percentil_min=percentil_min,
        percentil_max=percentil_max,
    )
    return imagem_rgb

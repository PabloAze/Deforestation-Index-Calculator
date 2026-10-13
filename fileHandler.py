import rasterio, numpy as np

def validar_geotiff(src):
    # Verifica se a imagem possui bandas
    if src.count == 0:
        raise ValueError("O arquivo não possui bandas.")

    # Lê a máscara de validade de todas as bandas.
    # True representa um pixel válido naquela banda.
    mascaras = src.read_masks() > 0

    # Considera válido um pixel que possui dados
    # válidos em todas as bandas.
    mascara_valida = np.all(mascaras, axis=0)

    # Quantidade total de pixels espaciais
    total_pixels = src.width * src.height

    # Contagem de pixels válidos e inválidos
    pixels_validos = np.count_nonzero(mascara_valida)
    pixels_invalidos = total_pixels - pixels_validos

    # Percentuais
    percentual_validos = (
        pixels_validos / total_pixels * 100
    )
    percentual_invalidos = (
        pixels_invalidos / total_pixels * 100
    )

    # Metadados
    informacoes = {
        "width": src.width,
        "height": src.height,
        "bands": src.count,
        "res": src.res,
        "crs": str(src.crs),
        "total_pixels": total_pixels,
        "valid_pixels": pixels_validos,
        "invalid_pixels": pixels_invalidos,
        "valid_percentual": percentual_validos,
        "invalid_percentual": percentual_invalidos,
        "valid_mask": mascara_valida,
    }

    if pixels_validos == 0:
        raise ValueError(
            "A imagem não possui pixels válidos."
        )

    return informacoes

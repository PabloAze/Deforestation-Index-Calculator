
import numpy as np
import matplotlib.pyplot as plt
from fileHandler import calcular_metricas_area
import rgb as rgb_utils


def processar_laplaciano(
    src,
    limiar=30.0,
    banda_azul=1,
    banda_verde=2,
    banda_vermelha=3,
    imagem_rgb=None,
    mascara_valida=None,
):
    """
    Aplica o filtro passa-alta Laplaciano sobre uma composição RGB.

    Etapas:
    1. Valida as bandas de entrada.
    2. Identifica pixels válidos no GeoTIFF.
    3. Converte as bandas para uma imagem RGB uint8.
    4. Calcula o Laplaciano manualmente com NumPy.
    5. Gera uma máscara dos pixels cuja resposta supera o limiar.
    6. Retorna a imagem e as máscaras para processamento posterior.

    O limiar é aplicado à magnitude absoluta do Laplaciano.
    """

    # 1. Validar as bandas de entrada
    bandas = [banda_azul, banda_verde, banda_vermelha]

    if min(bandas) < 1 or max(bandas) > src.count:
        raise ValueError(
            f"As bandas solicitadas devem estar entre 1 e {src.count}."
        )

    if limiar < 0:
        raise ValueError("O limiar não pode ser negativo.")

    # 2. Reutilizar a composição RGB já calculada pela interface quando possível.
    if (imagem_rgb is None) != (mascara_valida is None):
        raise ValueError(
            "A imagem RGB e sua máscara válida devem ser informadas juntas."
        )

    if imagem_rgb is None:
        imagem_rgb, mascara_valida = rgb_utils.generate_composicao(
            src,
            banda_red=banda_vermelha,
            banda_green=banda_verde,
            banda_blue=banda_azul,
        )
    else:
        imagem_rgb = np.asarray(imagem_rgb)
        mascara_valida = np.asarray(mascara_valida, dtype=bool)

    if imagem_rgb.shape != (src.height, src.width, 3):
        raise ValueError("A imagem RGB deve corresponder às dimensões do GeoTIFF.")
    if mascara_valida.shape != (src.height, src.width):
        raise ValueError("A máscara válida deve corresponder às dimensões do GeoTIFF.")

    # 3. Obter o canal V do modelo HSV.
    # V equivale ao maior valor entre os canais RGB.
    canal_v = np.max(imagem_rgb, axis=2).astype(np.float32)

    # 5. Aplicar manualmente o Laplaciano 3x3:
    #
    # -1  -1  -1
    # -1   8  -1
    # -1  -1  -1
    #
    # O preenchimento replica os valores das bordas.
    imagem_padded = np.pad(
        canal_v,
        pad_width=1,
        mode="edge"
    )

    centro = imagem_padded[1:-1, 1:-1]

    vizinhos = (
        imagem_padded[:-2, :-2]
        + imagem_padded[:-2, 1:-1]
        + imagem_padded[:-2, 2:]
        + imagem_padded[1:-1, :-2]
        + imagem_padded[1:-1, 2:]
        + imagem_padded[2:, :-2]
        + imagem_padded[2:, 1:-1]
        + imagem_padded[2:, 2:]
    )

    resposta = (8 * centro) - vizinhos

    # Considerar a magnitude da resposta, independentemente do sinal
    magnitude = np.abs(resposta)

    # 6. Classificar pixels, excluindo pixels inválidos
    mascara_laplaciano = (
        mascara_valida
        & (magnitude >= limiar)
    )

    metricas_area = calcular_metricas_area(
        src,
        mascara_valida,
        mascara_laplaciano,
    )
    if metricas_area["pixels_validos"] == 0:
        raise ValueError(
            "O GeoTIFF não possui pixels válidos nas bandas selecionadas."
        )

    # 7. Gerar a imagem visual do filtro
    magnitude_visual = np.ma.masked_where(
        ~mascara_valida,
        magnitude
    )

    valores_magnitude = magnitude[mascara_valida]
    maximo_visual = max(
        float(np.percentile(valores_magnitude, 99)),
        1.0
    )

    fig, ax = plt.subplots(figsize=(10, 7))

    imagem_plot = ax.imshow(
        magnitude_visual,
        cmap="inferno",
        vmin=0,
        vmax=maximo_visual
    )

    fig.colorbar(
        imagem_plot,
        ax=ax,
        label="Magnitude do Laplaciano"
    )

    ax.set_title("Filtro passa-alta Laplaciano")
    ax.axis("off")
    fig.tight_layout()

    fig.canvas.draw()

    imagem_saida = np.asarray(
        fig.canvas.buffer_rgba()
    )[:, :, :3].copy()

    plt.close(fig)

    # 8. Retornar os resultados
    return {
        "imagem": imagem_saida,
        "mascara_valida": mascara_valida,
        "mascara_laplaciano": mascara_laplaciano,
        **metricas_area,
        "limiar": limiar,
    }

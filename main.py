import os
import rasterio
import numpy as np
import cv2
import geopandas as gpd
from shapely.geometry import Point
import json
import argparse

def treat_image(img):
    treated_image = cv2.normalize(
            img,
            None,
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX).astype(np.uint8)
    
    treated_image = cv2.medianBlur(treated_image, 3)
    return treated_image

# --- Segmentação por limiar (threshold) e remoção de ruído morfológico ---
def detect_plants(treated_image, threshold):
    binary = cv2.inRange(treated_image, 0, threshold)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    return cv2.connectedComponentsWithStats(binary)

# Caminhos
parser = argparse.ArgumentParser(
    description="Detecção automática de mudas de eucalipto em imagens GeoTIFF"
)

parser.add_argument(
    "input",
    type=str,
    help="Caminho para o arquivo GeoTIFF (.tif)"
)
parser.add_argument("--threshold", type=int, default=110)
parser.add_argument("--min-area-m2", type=float, default=0.4)

args = parser.parse_args()
path_img = args.input
threshold = args.threshold
min_area_m2 = args.min_area_m2

if not os.path.exists(path_img):
    raise FileNotFoundError(f"Arquivo não encontrado: {path_img}")
    
# Caminhos para os outputs   
base = os.path.splitext(os.path.basename(path_img))[0]
geojson_out = f"{base}_eucaliptos.geojson"
stats_out = f"{base}_statistics.json"

# Ler a Imagem com Rasterio (Preservando Geo-dados)
with rasterio.open(path_img) as src:

    transform = src.transform  # Matriz para converter pixel -> coordenadas reais
    pixel_width  = transform.a  
    pixel_height = abs(transform.e)
    pixel_area_m2 = pixel_width * pixel_height #Area total de um pixel

    crs = src.crs # Sistema de coordenadas

    # Ler imagem. Rasterio retorna (Bandas, Altura, Largura)
    img_array = src.read() 
    
    # Transpor eixos: (C, H, W) -> (H, W, C)
    img_array = np.moveaxis(img_array, 0, -1)

# Utiliza a soma dos pixels RGB para diferencias as arvores
## Em testes, produziu o melhor resultado, porem definitivamente pode ser melhorado
base_image = np.sum(img_array[:,:,:3], axis=2)

# Normalize e suaviza os pixels
treated_image = treat_image(base_image)

# --- Componentes conectados COM estatísticas ---
num_labels, labels, stats, centroids = detect_plants(treated_image, threshold)

# Filtragem dos componentes por area (elimina ruido) e cor (elimina as bordas pretas)
## Alguns outros filtros como de frequencia, homogeneidade etc poderiam melhorar a eficiencia do algoritimo, sobretudo para as sombras.
n_plants = 0
points = []
min_area = min_area_m2/pixel_area_m2  # Conversão de área mínima (m² → pixels)
for label in range(1, num_labels):
    area = stats[label, cv2.CC_STAT_AREA]
    if area < min_area:
        continue

    mask = (labels == label)
    black_ratio = np.sum(treated_image[mask] < 20) / mask.sum()
    if black_ratio > 0.9:
        continue

    n_plants += 1
    
    # Coleta as coordenadas das mudas encontradas
    cx, cy = centroids[label]
    row = int(cy)
    col = int(cx)

    x_geo, y_geo = rasterio.transform.xy(transform, row, col)
    points.append(Point(x_geo, y_geo))


# Salvando as mudas encontradas em um geojson
gdf = gpd.GeoDataFrame(
    {"id": range(len(points))},
    geometry=points,
    crs=crs
)
gdf.to_file(geojson_out, driver="GeoJSON")


# Calcula e salva as estatisticas em JSON
num_pixels = np.count_nonzero(np.sum(img_array, axis=2))
area_ha= num_pixels * pixel_area_m2/10000
plants_per_ha = n_plants / area_ha if area_ha > 0 else 0
stats = {
    "total_plants": int(n_plants),
    "area_analyzed_ha": float(round(area_ha, 4)),
    "plants_per_hectare": float(round(plants_per_ha, 2)),
    "crs": str(crs),
}

print(f"Mudas detectadas: {n_plants}")
print(f"Área analisada (ha): {area_ha:.2f}")
print(f"Plantas por hectare: {plants_per_ha:.2f}")

with open(stats_out, "w") as f:
    json.dump(stats, f, indent=4)

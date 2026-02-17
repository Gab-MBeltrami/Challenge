import os
import rasterio
import numpy as np
import cv2
import geopandas as gpd
from shapely.geometry import Point
import json

# Caminhos
DATAPATH = os.getcwd() + '/Desafio_BemAgro/dados/'
sample = 'sample1.tif'
path_img = DATAPATH + sample


# 2. Ler a Imagem com Rasterio (Preservando Geo-dados)

with rasterio.open(path_img) as src:

    transform = src.transform  # Matriz para converter pixel -> coordenadas reais
    pixel_width  = transform.a  
    pixel_height = abs(transform.e)
    pixel_area_m2 = pixel_width * pixel_height

    crs = src.crs              # Sistema de coordenadas
    print(crs)
    # Ler imagem. Rasterio retorna (Bandas, Altura, Largura)
    img_array = src.read() 
    
    # Transpor eixos: (C, H, W) -> (H, W, C)
    img_array = np.moveaxis(img_array, 0, -1)
    
    print(img_array.shape)
    

R = np.sum(img_array[:,:,:3], axis=2)

R = cv2.normalize(
    R,
    None,
    alpha=0,
    beta=255,
    norm_type=cv2.NORM_MINMAX
).astype(np.uint8)

R = cv2.medianBlur(R, 3)


# --- Threshold + limpeza ---

binary = cv2.inRange(R, 0, 110)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

# --- Componentes conectados COM estatísticas ---
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)

# --- Preparar imagem original para desenhar ---
img_vis = img_array[:, :, :3].copy()
img_vis = cv2.normalize(img_vis, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

count = 0
min_area = 0.4	/pixel_area_m2
areas = stats[:, cv2.CC_STAT_AREA]
print("Área mínima encontrada:", areas.min())
print("Área máxima encontrada:", areas.max())
print("Área mínima:", min_area)


points = []

for label in range(1, num_labels):
    area = stats[label, cv2.CC_STAT_AREA]
    if area < min_area:
        continue

    mask = (labels == label)

    mean_intensity = R[mask].mean()
    black_ratio = np.sum(R[mask] < 20) / mask.sum()
    if black_ratio > 0.9:
        continue

    count += 1
    cx, cy = centroids[label]

    row = int(cy)
    col = int(cx)

    x_geo, y_geo = rasterio.transform.xy(transform, row, col)
    points.append(Point(x_geo, y_geo))

    cv2.circle(img_vis, (int(cx), int(cy)), 3, (255,0,0), -1)

gdf = gpd.GeoDataFrame(
    {"id": range(len(points))},
    geometry=points,
    crs=crs
)
gdf.to_file("eucaliptos.geojson", driver="GeoJSON")

print("Árvores contadas:", count)
num_pixels = np.count_nonzero(np.sum(img_array, axis=2))
area_ha= num_pixels * pixel_area_m2/10000
plants_per_ha = count/area_ha
print(f"Area estimada: {area_ha:.2f} ha")
stats = {
    "total_plants": int(count),
    "area_analyzed_ha": float(round(area_ha, 4)),
    "plants_per_hectare": float(round(plants_per_ha, 2)),
    "crs": str(crs),
}
with open("statistics.json", "w") as f:
    json.dump(stats, f, indent=4)

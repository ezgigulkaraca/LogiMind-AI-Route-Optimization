import streamlit as st
import pandas as pd
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import plotly.graph_objects as go

# Sayfa Yapılandırması ve Kurumsal Tema
st.set_page_config(page_title="LogiMind - Lojistik Optimizasyon Sistemi", layout="wide")

st.title("LogiMind: Akıllı Rota ve Yük Optimizasyon Platformu")
st.write("KOBIEler ve lojistik sağlayıcıları için operasyonel maliyetleri ve karbon salınımını minimize eden karar destek sistemi.")

# Kontrol Paneli (Sidebar)
st.sidebar.header("Sistem Parametreleri")
arac_sayisi = st.sidebar.slider("Aktif Arac Sayisi", min_value=1, max_value=5, value=3)
arac_kapasitesi = st.sidebar.slider("Arac Kapasitesi (KG)", min_value=10, max_value=50, value=25)

# Sipariş Veri Modeli
data_dict = {
    "Musteri_Adi": ["Depo (Merkez)", "Musteri A", "Musteri B", "Musteri C", "Musteri D", "Musteri E", "Musteri F", "Musteri G", "Musteri H", "Musteri I"],
    "X_Koordinati": [0, 5, -3, 12, 8, -6, 2, 14, -2, 7],
    "Y_Koordinati": [0, 10, 8, 2, -4, -5, 15, -1, -9, 7],
    "Talep_KG": [0, 3, 5, 4, 2, 6, 3, 5, 2, 4]
}
df = pd.DataFrame(data_dict)

# Veri Tablosu Gösterimi
st.subheader("Mevcut Siparis ve Dagitim Verileri")
st.dataframe(df, use_container_width=True)

# Mesafe Matrisi Hesaplama Fonksiyonu
def mesafe_matrisi_olustur(x_coords, y_coords):
    num_points = len(x_coords)
    matrix = np.zeros((num_points, num_points))
    for i in range(num_points):
        for j in range(num_points):
            matrix[i][j] = int(np.hypot(x_coords[i] - x_coords[j], y_coords[i] - y_coords[j]) * 10)
    return matrix

# Optimizasyon Tetikleyici
if st.button("Rotalari Optimize Et", type="primary"):
    
    toplam_talep = df["Talep_KG"].sum()
    toplam_kapasite = arac_sayisi * arac_kapasitesi
    
    if toplam_talep > toplam_kapasite:
        st.error(f"Hata: Yetersiz Kapasite. Toplam Talep: {toplam_talep} KG, Secilen Aracların Toplam Kapasitesi: {toplam_kapasite} KG. Lutfen Arac Sayisini veya Kapasitesini artirin.")
    else:
        with st.spinner("Yapay zeka optimizasyon motoru calistiriliyor..."):
            try:
                # OR-Tools Model Kurulumu
                mesafeler = mesafe_matrisi_olustur(df["X_Koordinati"].tolist(), df["Y_Koordinati"].tolist())
                manager = pywrapcp.RoutingIndexManager(len(mesafeler), arac_sayisi, 0)
                routing = pywrapcp.RoutingModel(manager)

                def distance_callback(from_index, to_index):
                    return mesafeler[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]
                    
                transit_callback_index = routing.RegisterTransitCallback(distance_callback)
                routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

                def demand_callback(from_index):
                    return int(df["Talep_KG"].iloc[manager.IndexToNode(from_index)])
                    
                demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
                routing.AddDimensionWithVehicleCapacity(
                    demand_callback_index,
                    0,
                    [arac_kapasitesi] * arac_sayisi,
                    True,
                    "Capacity"
                )

                search_parameters = pywrapcp.DefaultRoutingSearchParameters()
                search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

                # COZUM ASAMASI
                solution = routing.SolveWithParameters(search_parameters)

                if solution:
                    st.success("Rotalar basariyla optimize edildi!")
                    
                    # Performans Metrikleri Paneli
                    col1, col2, col3, col4 = st.columns(4)
                    
                    eski_mesafe = float(df["X_Koordinati"].abs().sum() + df["Y_Koordinati"].abs().sum()) * 1.5
                    yeni_mesafe = 0
                    rotalar = {}
                    
                    for vehicle_id

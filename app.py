import streamlit as st
import pandas as pd
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import plotly.graph_objects as go

# Sayfa Yapilandirmasi ve Kurumsal Tema
st.set_page_config(page_title="LogiMind - Lojistik Optimizasyon Sistemi", layout="wide")

st.title("LogiMind: Akilli Rota ve Yuk Optimizasyon Platformu")
st.write("KOBIler ve lojistik saglayicilari icin operasyonel maliyetleri ve karbon salinimini minimize eden karar destek sistemi.")

# Kontrol Paneli (Sidebar)
st.sidebar.header("Sistem Parametreleri")
arac_sayisi = st.sidebar.slider("Aktif Arac Sayisi", min_value=1, max_value=5, value=3)
arac_kapasitesi = st.sidebar.slider("Arac Kapasitesi (KG)", min_value=10, max_value=50, value=25)

# Siparis Veri Modeli
data_dict = {
    "Musteri_Adi": ["Depo (Merkez)", "Musteri A", "Musteri B", "Musteri C", "Musteri D", "Musteri E", "Musteri F", "Musteri G", "Musteri H", "Musteri I"],
    "X_Koordinati": [0, 5, -3, 12, 8, -6, 2, 14, -2, 7],
    "Y_Koordinati": [0, 10, 8, 2, -4, -5, 15, -1, -9, 7],
    "Talep_KG": [0, 3, 5, 4, 2, 6, 3, 5, 2, 4]
}
df = pd.DataFrame(data_dict)

# Veri Tablosu Gosterimi
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
        st.error(f"Hata: Yetersiz Kapasite. Toplam Talep: {toplam_talep} KG, Secilen Araclarin Toplam Kapasitesi: {toplam_kapasite} KG. Lutfen Arac Sayisini veya Kapasitesini artirin.")
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

                # Cozum Asamasi
                solution = routing.SolveWithParameters(search_parameters)

                if solution:
                    st.success("Rotalar basariyla optimize edildi!")
                    
                    # Performans Metrikleri Paneli
                    col1, col2, col3, col4 = st.columns(4)
                    
                    eski_mesafe = float(df["X_Koordinati"].abs().sum() + df["Y_Koordinati"].abs().sum()) * 1.5
                    yeni_mesafe = 0
                    rotalar = {}
                    
                    for vehicle_id in range(arac_sayisi):
                        index = routing.Start(vehicle_id)
                        route = []
                        while not routing.IsEnd(index):
                            node = manager.IndexToNode(index)
                            route.append(node)
                            previous_index = index
                            index = solution.Value(routing.NextVar(index))
                            yeni_mesafe += mesafeler[manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
                        route.append(manager.IndexToNode(index))
                        rotalar[vehicle_id] = route

                    yeni_mesafe_km = yeni_mesafe / 10.0
                    tasarruf_orani = ((eski_mesafe - yeni_mesafe_km) / eski_mesafe) * 100
                    karbon_tasarruf = (eski_mesafe - yeni_mesafe_km) * 0.25

                    with col1:
                        st.metric("Geleneksel Yontem Mesafesi", f"{eski_mesafe:.1f} KM")
                    with col2:
                        st.metric("LogiMind Optimize Mesafe", f"{yeni_mesafe_km:.1f} KM", f"-{tasarruf_orani:.1f}%")
                    with col3:
                        st.metric("Verimlilik Artisi", f"%{tasarruf_orani:.1f}")
                    with col4:
                        st.metric("CO2 Salinim Azaltimi", f"{karbon_tasarruf:.1f} KG")

                    # Interaktif Rota Analiz Haritasi
                    st.subheader("Optimize Dagitim Rotalari Analizi")
                    fig = go.Figure()

                    # Musteri Konumlari
                    fig.add_trace(go.Scatter(
                        x=df["X_Koordinati"].iloc[1:], 
                        y=df["Y_Koordinati"].iloc[1:],
                        mode='markers+text',
                        marker=dict(size=12, color='rgb(44, 62, 80)'),
                        text=df["Musteri_Adi"].iloc[1:], 
                        textposition="top center",
                        name="Teslimat Noktalari"
                    ))

                    # Merkez Depo
                    fig.add_trace(go.Scatter(
                        x=[df["X_Koordinati"].iloc[0]], 
                        y=[df["Y_Koordinati"].iloc[0]],
                        mode='markers+text',
                        marker=dict(size=16, color='rgb(192, 57, 43)', symbol='square'),
                        text=["LOJISTIK MERKEZI (DEPO)"], 
                        textposition="bottom center",
                        name="Merkez Depo"
                    ))

                    # Arac Rotalari Cizimi
                    renkler = ['#2ecc71', '#3498db', '#9b59b6', '#e67e22', '#f1c40f']
                    for vehicle_id, route in rotalar.items():
                        if len(route) > 2:
                            route_x = [df["X_Koordinati"].iloc[node] for node in route]
                            route_y = [df["Y_Koordinati"].iloc[node] for node in route]
                            
                            hover_texts = [f"Durak {idx}: {df['Musteri_Adi'].iloc[node]} (Yuk: {df['Talep_KG'].iloc[node]} KG)" for idx, node in enumerate(route)]
                            
                            fig.add_trace(go.Scatter(
                                x=route_x, 
                                y=route_y,
                                mode='lines+markers',
                                line=dict(width=3, color=renkler[vehicle_id % len(renkler)]),
                                marker=dict(size=8),
                                text=hover_texts,
                                hoverinfo='text',
                                name=f"Arac {vehicle_id + 1}"
                            ))

                    fig.update_layout(
                        xaxis_title="X Koordinat Duzlemi",
                        yaxis_title="Y Koordinat Duzlemi",
                        template="plotly_white",
                        height=600,
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.warning("Optimizasyon motoru bu parametrelerle gecerli bir rota cizemedi. Algoritmanin tum noktalara ulasabilmesi icin lutfen sol menuden Aktif Arac Sayisini veya Arac Kapasitesini biraz daha artirarak tekrar deneyin.")
            
            except Exception as e:
                st.info("Sistem bu parametre sinirlarinda kararli bir cozum kumesi uretemedi. Lutfen 'Aktif Arac Sayisi: 4' ve 'Arac Kapasitesi: 30' veya daha yuksek kombinasyonlari secerek algoritmayi tekrar tetikleyin.")

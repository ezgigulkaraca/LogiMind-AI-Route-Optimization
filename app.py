import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import itertools
import random
import google.generativeai as genai

# =========================
# API KEY
# =========================
API_KEY = "AIzaSyAXA7edsGE5ggJrQo5wT2CO2pe2BSbEoKc"

genai.configure(api_key=API_KEY)

# EN STABİL MODEL
model = genai.GenerativeModel("gemini-1.5-flash")

# =========================
# APP
# =========================
st.set_page_config(page_title="LogiMind AI", layout="wide")

st.title("LogiMind - AI Rota Optimizasyonu")

arac_sayisi = st.sidebar.slider("Araç Sayısı", 1, 5, 2)
arac_kapasitesi = st.sidebar.slider("Kapasite", 5, 50, 15)
trafik = st.sidebar.slider("Trafik", 1.0, 2.0, 1.0)

musteriler = {
    "A": (5, 10, 3),
    "B": (-3, 8, 5),
    "C": (12, 2, 4),
    "D": (8, -4, 2),
    "E": (-6, -5, 6)
}

def mesafe(p1, p2):
    return np.hypot(p1[0]-p2[0], p1[1]-p2[1]) * trafik

def gemini_analiz(text):
    try:
        response = model.generate_content(text)
        return response.text
    except Exception as e:
        return str(e)

secili = st.multiselect("Müşteriler", list(musteriler.keys()), default=list(musteriler.keys()))

data = [{"name":"Depo","x":0,"y":0,"demand":0}]
for m in secili:
    x,y,d = musteriler[m]
    data.append({"name":m,"x":x,"y":y,"demand":d})

df = pd.DataFrame(data)
st.dataframe(df)

if st.button("Optimize Et"):

    toplam = df["demand"].sum()
    kapasite = arac_sayisi * arac_kapasitesi

    if toplam > kapasite:
        st.error("Kapasite yetersiz")
        st.stop()

    rotalar = {i: [] for i in range(arac_sayisi)}
    yuk = {i: 0 for i in range(arac_sayisi)}

    for m in data[1:]:
        best = None

        for a in range(arac_sayisi):
            if yuk[a] + m["demand"] <= arac_kapasitesi:
                last = (0,0) if not rotalar[a] else (rotalar[a][-1]["x"], rotalar[a][-1]["y"])
                d = mesafe(last, (m["x"], m["y"]))

                if best is None or d < best[0]:
                    best = (d,a)

        a = best[1]
        rotalar[a].append(m)
        yuk[a] += m["demand"]

    fig = go.Figure()
    colors = ["red","blue","green","orange","purple"]

    toplam_mesafe = 0

    for a in range(arac_sayisi):
        if not rotalar[a]:
            continue

        best_route = None
        best_cost = float("inf")

        for perm in itertools.permutations(rotalar[a]):
            path = [(0,0)] + [(p["x"],p["y"]) for p in perm] + [(0,0)]
            cost = sum(mesafe(path[i], path[i+1]) for i in range(len(path)-1))

            if cost < best_cost:
                best_cost = cost
                best_route = perm

        toplam_mesafe += best_cost

        x = [0] + [p["x"] for p in best_route] + [0]
        y = [0] + [p["y"] for p in best_route] + [0]

        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            name=f"Araç {a+1}",
            line=dict(color=colors[a%len(colors)], width=3)
        ))

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("AI Analiz")

    prompt = f"""
    Lojistik sistemi analiz et:

    Araç sayısı: {arac_sayisi}
    Toplam mesafe: {toplam_mesafe}
    Trafik: {trafik}

    3 maddede yorumla.
    """

    st.write(gemini_analiz(prompt))

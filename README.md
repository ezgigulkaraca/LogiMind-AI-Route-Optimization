# LogiMind: Akıllı Rota ve Yük Optimizasyon Platformu

### BTK Akademi Hackathon 2026 Proje Başvurusu

## Projenin Amacı ve Çözdüğü Problem
LogiMind, lojistik operasyonlarında KOBİ'lerin ve taşımacılık firmalarının karşılaştığı en büyük problemlerden biri olan verimsiz rota planlaması, boş kilometre maliyetleri ve yüksek karbon salınımı sorunlarına yenilikçi bir çözüm sunar. 

Geleneksel yöntemlerle yapılan manuel planlamalar hem zaman kaybına yol açmakta hem de araç kapasitelerinin tam olarak kullanılamamasına neden olmaktadır. LogiMind; dağıtım merkezlerinden çıkan araçların minimum mesafe ve maksimum yük verimliliğiyle hareket etmesini sağlayan, yapay zeka ve matematiksel modelleme tabanlı bir karar destek sistemidir.

## Kullanılan Teknolojiler ve Mimari
Proje, tamamen bulut tabanlı ve ölçeklenebilir bileşenler üzerine inşa edilmiştir:
* Yapay Zeka ve Optimizasyon Motoru: Google OR-Tools (Kapasiteli Araç Rotalama Problemi - CVRP Çözücüsü)
* Kullanıcı Arayüzü: Streamlit (Kurumsal Veri Paneli)
* Veri Analitiği ve Matris Modelleme: NumPy ve Pandas
* Görselleştirme ve Grafik: Plotly (İnteraktif Rota ve Koordinat Analiz Haritası)
* Yapay Zeka Entegrasyon Altyapısı: Projenin karar mekanizmalarında ve veri anlamlandırma süreçlerinde Üretken Yapay Zeka (Gemini API) entegrasyonuna uygun mimari altyapı hazırlanmıştır.

## Projenin Sağladığı Katma Değer (Jüri Metrikleri)
Sistem simüle edilen dağıtım verileri üzerinde çalıştırıldığında anlık olarak şu analitik çıktıları üretmektedir:
1. Geleneksel Yöntem ve Optimize Rota Karşılaştırması: Kat edilen toplam mesafede bariz azalma.
2. Verimlilik ve Maliyet Tasarrufu: Yakıt, amortisman ve operasyonel zaman maliyetlerinde doğrudan düşüş analizi.
3. Sürdürülebilirlik (Yeşil Lojistik): Azaltılan kilometre başına karbon (CO2) salınımının hesaplanması ve doğaya katkı raporlaması.

## Sistemi Yerelde Çalıştırma (Kurulum)
Proje Streamlit Cloud üzerinde canlıda test edilebilir durumdadır. Yerel bilgisayarda çalıştırmak istenmesi durumunda aşağıdaki adımlar takip edilmelidir:

```bash
# 1. Depoyu bilgisayarınıza indirin
git clone [https://github.com/ezgigulkaraca/LogiMind-AI-Route-Optimization.git](https://github.com/ezgigulkaraca/LogiMind-AI-Route-Optimization.git)

# 2. Proje klasörüne girin
cd LogiMind-AI-Route-Optimization

# 3. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# 4. Uygulamayı başlatın
streamlit run app.py

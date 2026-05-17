import google.generativeai as genai

genai.configure(api_key="AIzaSyAXA7edsGE5ggJrQo5wT2CO2pe2BSbEoKc")

for m in genai.list_models():
    print(m.name)

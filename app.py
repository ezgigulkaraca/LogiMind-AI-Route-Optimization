import google.generativeai as genai

genai.configure(api_key="API_KEYİN")

for m in genai.list_models():
    print(m.name)

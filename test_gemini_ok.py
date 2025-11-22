import google.generativeai as genai

# ---- Your Gemini API Key ----
API_KEY = "AIzaSyCEnhrsImFXuDgm2i9r6aNIHTofyj_iPWg"

# ---- Configure the Client ----
genai.configure(api_key=API_KEY)

print("Using API key prefix:", API_KEY[:8] + "********")

print("\nListing models that support generateContent...\n")

# ---- List models ----
models = genai.list_models()

for m in models:
    methods = getattr(m, "supported_generation_methods", [])
    if "generateContent" in methods:
        print("✅", m.name)

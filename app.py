import streamlit as st
import google.generativeai as genai
from PIL import Image

# പേജ് സജ്ജീകരണം
st.set_page_config(page_title="AI Dress Pattern Maker", layout="wide")
st.title("👗 AI Dress Pattern & Cutting Generator")
st.write("വസ്ത്രത്തിന്റെ ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക. AI നിങ്ങൾക്ക് ആവശ്യമായ കട്ടിംഗ് പാറ്റേൺ തയ്യാറാക്കി നൽകും.")

# ഡിപ്ലോയ് ചെയ്യുമ്പോൾ API Key സുരക്ഷിതമായി എടുക്കാൻ
api_key = ""
try:
    # Streamlit Secrets-ൽ നിന്നും API Key എടുക്കുന്നു
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # Secrets ലഭ്യമല്ലെങ്കിൽ സൈഡ്‌ബാറിൽ നൽകാം
    api_key = st.sidebar.text_input("നിങ്ങളുടെ Gemini API Key നൽകുക:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    uploaded_file = st.file_uploader("വസ്ത്രത്തിന്റെ ഫോട്ടോ ഇവിടെ അപ്‌ലോഡ് ചെയ്യുക (JPG/PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="അപ്‌ലോഡ് ചെയ്ത ഡിസൈൻ", width=400)

        if st.button("പാറ്റേൺ ഡ്രോയിംഗ് തയ്യാറാക്കുക"):
            with st.spinner("AI പാറ്റേൺ തയ്യാറാക്കുന്നു... ദയവായി കാത്തിരിക്കുക."):
                prompt = """
                You are an expert AI fashion designer and master pattern maker. 
                Your ONLY job is to analyze the uploaded dress photo and create a precise pattern drafting guide.
                Please provide:
                1. Pattern Pieces List: A list of all 2D fabric pieces required (e.g., Front Bodice, Back Skirt, Sleeves).
                2. Cutting & Stitching Instructions: Step-by-step tailoring guide.
                3. Pattern Drawing (SVG): Generate clean SVG code representing the 2D flat pattern shapes for cutting this exact dress. Include measurement indicators if possible. Wrap the SVG code in ```xml ... ``` block.
                Do not discuss anything outside of dressmaking, stitching, and pattern drafting.
                """
                try:
                    response = model.generate_content([prompt, image])
                    st.subheader("തയ്യൽ നിർദ്ദേശങ്ങളും പാറ്റേൺ ഡ്രോയിംഗും:")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"ഒരു പിശക് സംഭവിച്ചു: {e}")
else:
    st.sidebar.warning("ടൂൾ പ്രവർത്തിക്കാൻ ദയവായി API Key നൽകുക അല്ലെങ്കിൽ Streamlit Secrets-ൽ സെറ്റ് ചെയ്യുക.")

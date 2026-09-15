import streamlit as st
import google.generativeai as genai
from PIL import Image
import re

# പേജ് സജ്ജീകരണം
st.set_page_config(page_title="AI Dress Pattern Maker", layout="wide")
st.title("👗 Custom AI Dress Pattern Maker")
st.write("വസ്ത്രത്തിന്റെ ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക. ഇതിന് ആവശ്യമായ അളവുകൾ നൽകിയാൽ മലയാളത്തിൽ നിർദ്ദേശങ്ങളും കട്ടിംഗ് പാറ്റേണും ലഭിക്കും.")

# വിവരങ്ങൾ സൂക്ഷിച്ചു വെക്കാൻ (Session State)
if 'needed_measurements' not in st.session_state:
    st.session_state.needed_measurements = []
if 'user_measurements' not in st.session_state:
    st.session_state.user_measurements = {}

# API Key സജ്ജീകരണം
api_key = ""
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = st.sidebar.text_input("നിങ്ങളുടെ Gemini API Key നൽകുക:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Gemini 2.5 Flash മോഡൽ ഉപയോഗിക്കുന്നു
    model = genai.GenerativeModel('gemini-2.5-flash')

    uploaded_file = st.file_uploader("വസ്ത്രത്തിന്റെ ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക (JPG/PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="നിങ്ങൾ നൽകിയ ഡിസൈൻ", width=300)

        # ഘട്ടം 1: എന്തൊക്കെ അളവുകൾ വേണമെന്ന് AI-യോട് ചോദിക്കുക
        if st.button("ഏതൊക്കെ അളവുകൾ വേണമെന്ന് കണ്ടെത്തുക"):
            with st.spinner("വസ്ത്രം വിശകലനം ചെയ്യുന്നു... ദയവായി കാത്തിരിക്കുക."):
                prompt1 = """
                Analyze this dress photo. Reply ONLY with a comma-separated list of body measurements required to tailor this specific dress. 
                For example: Chest, Waist, Hip, Total Length, Shoulder. 
                Give the output in English and do not include any extra sentences.
                """
                try:
                    response1 = model.generate_content([prompt1, image])
                    measurements_str = response1.text.strip()
                    # AI നൽകിയ അളവുകളുടെ ലിസ്റ്റ് വേർതിരിക്കുന്നു
                    st.session_state.needed_measurements = [m.strip() for m in measurements_str.split(',') if m.strip()]
                except Exception as e:
                    st.error(f"ഒരു പിശക് സംഭവിച്ചു: {e}")

        # ഘട്ടം 2: അളവുകൾ നൽകാനും പാറ്റേൺ തയ്യാറാക്കാനും
        if st.session_state.needed_measurements:
            st.subheader("താഴെ പറയുന്ന അളവുകൾ നൽകുക (ഉദാ: 34 inch അല്ലെങ്കിൽ 86 cm):")
            
            # AI കണ്ടെത്തിയ അളവുകൾക്ക് ഇൻപുട്ട് ബോക്സുകൾ ഉണ്ടാക്കുന്നു
            for m in st.session_state.needed_measurements:
                st.session_state.user_measurements[m] = st.text_input(f"{m}:")

            if st.button("പാറ്റേൺ തയ്യാറാക്കുക"):
                with st.spinner("നിങ്ങളുടെ അളവുകൾ വെച്ച് പാറ്റേൺ തയ്യാറാക്കുന്നു..."):
                    # ഉപഭോക്താവ് നൽകിയ അളവുകൾ ഒരുമിച്ചു ചേർക്കുന്നു
                    measurements_text = ", ".join([f"{k}: {v}" for k, v in st.session_state.user_measurements.items() if v])
                    
                    prompt2 = f"""
                    You are an expert AI fashion designer and master pattern maker. 
                    I have uploaded a dress photo and here are the user's specific body measurements: {measurements_text}.
                    
                    Your ONLY job is to create a precise pattern drafting guide based on these EXACT measurements.
                    
                    CRITICAL INSTRUCTION: All textual responses, including the Pattern Pieces List and Cutting & Stitching Instructions, MUST be entirely in Malayalam language (Malayalam script). Do not use Manglish.
                    
                    Please provide:
                    1. പാറ്റേൺ പീസുകളുടെ ലിസ്റ്റ് (Pattern Pieces List): All 2D fabric pieces required, explained in Malayalam.
                    2. കട്ടിംഗ് & തയ്യൽ നിർദ്ദേശങ്ങൾ (Cutting & Stitching Instructions): Step-by-step tailoring guide customized to the provided measurements, completely in Malayalam. Explain how much fabric to cut.
                    3. പാറ്റേൺ ഡ്രോയിംഗ് (SVG): Generate clean SVG code representing the 2D flat pattern shapes for cutting this exact dress. 
                       Incorporate the user's measurements directly into the SVG drawing as text labels. Wrap the SVG code in ```xml ... ``` block.
                    
                    Do not discuss anything outside of dressmaking, stitching, and pattern drafting.
                    """
                    try:
                        response2 = model.generate_content([prompt2, image])
                        response_text = response2.text
                        
                        st.subheader("നിങ്ങളുടെ അളവുകൾ പ്രകാരമുള്ള കട്ടിംഗ് നിർദ്ദേശങ്ങളും പാറ്റേൺ ഡ്രോയിംഗും:")
                        st.markdown(response_text)
                        
                        # ടെക്സ്റ്റിൽ നിന്നും SVG കോഡ് മാത്രം കണ്ടെത്തി വേർതിരിക്കുന്നു
                        svg_match = re.search(r'(<svg.*?</svg>)', response_text, re.DOTALL | re.IGNORECASE)
                        if svg_match:
                            svg_content = svg_match.group(1)
                            st.success("SVG പാറ്റേൺ തയ്യാറാണ്!")
                            
                            # SVG ഡൗൺലോഡ് ചെയ്യാനുള്ള ബട്ടൺ
                            st.download_button(
                                label="📥 പാറ്റേൺ ഡ്രോയിംഗ് ഡൗൺലോഡ് ചെയ്യുക (Download SVG)",
                                data=svg_content,
                                file_name="dress_pattern.svg",
                                mime="image/svg+xml"
                            )
                        else:
                            st.warning("ഡൗൺലോഡ് ചെയ്യാനുള്ള SVG ഫയൽ കണ്ടെത്താനായില്ല.")
                            
                    except Exception as e:
                        st.error(f"ഒരു പിശക് സംഭവിച്ചു: {e}")
else:
    st.sidebar.warning("ടൂൾ പ്രവർത്തിക്കാൻ ദയവായി API Key നൽകുക അല്ലെങ്കിൽ Streamlit Secrets-ൽ സെറ്റ് ചെയ്യുക.")

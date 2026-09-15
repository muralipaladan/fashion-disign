import streamlit as st
from google import genai
from PIL import Image
import re
import json
import weasyprint

# --- 1. MODERN UI CONFIGURATION ---
st.set_page_config(
    page_title="Smart AI Tailor Studio", 
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 10px;}
    .sub-header { font-size: 1rem; color: #64748B; text-align: center; margin-bottom: 30px; }
    .fabric-badge { background-color: #dcfce7; color: #166534; padding: 10px 15px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 1.1rem; border: 1px solid #bbf7d0; margin-bottom: 20px;}
    .svg-container { background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 20px; overflow-x: auto;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Two-Step Smart AI: 1. Analyze Design ➔ 2. Generate A3 PDF Pattern</div>', unsafe_allow_html=True)

# --- 2. SIDEBAR & CREDENTIALS ---
with st.sidebar:
    st.header("⚙️ API Configuration")
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter Gemini 2.5 Flash API Key", type="password")
    
    if st.button("🔄 Reset App"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if not api_key:
    st.info("👋 തുടരാൻ ദയവായി ഇടതുവശത്ത് നിങ്ങളുടെ Gemini API Key നൽകുക.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 3. STATE MANAGEMENT ---
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "dress_data" not in st.session_state:
    st.session_state.dress_data = None
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# --- 4. MAIN WORKSPACE ---
col_img, col_act = st.columns([1, 1.8])

with col_img:
    st.markdown("### 📸 1. അപ്‌ലോഡ് (Upload Design)")
    uploaded_file = st.file_uploader("വസ്ത്രത്തിന്റെ ഫോട്ടോ നൽകുക", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if uploaded_file:
        if st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.analysis_done = False
            st.session_state.dress_data = None
            st.session_state.last_uploaded_file = uploaded_file.name
            
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Design", use_container_width=True)

with col_act:
    if uploaded_file and not st.session_state.analysis_done:
        st.markdown("### 🔍 2. ഡിസൈൻ വിശകലനം (AI Analysis)")
        st.info("ഫോട്ടോ വിശകലനം ചെയ്ത് അളവുകൾ കണ്ടെത്താൻ താഴെ ക്ലിക്ക് ചെയ്യുക.")
        
        if st.button("✨ ഡിസൈൻ അനലൈസ് ചെയ്യുക", type="primary"):
            with st.spinner("AI വസ്ത്രം തിരിച്ചറിയുന്നു..."):
                try:
                    analysis_prompt = """
                    Analyze the uploaded dress photo. Identify the dress type, estimate fabric (in meters), and list the STANDARD basic measurements required.
                    Return ONLY a valid JSON object:
                    {
                        "dress_name_ml": "വസ്ത്രത്തിന്റെ പേര്",
                        "dress_name_en": "Dress Name",
                        "estimated_fabric": "2.5 മീറ്റർ",
                        "measurements_needed": {"Shoulder": 14.0, "Chest": 36.0, "Waist": 32.0, "Length": 40.0}
                    }
                    """
                    response = client.models.generate_content(model="gemini-2.5-flash", contents=[analysis_prompt, image])
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state.dress_data = json.loads(raw_json)
                    st.session_state.analysis_done = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Analysis failed. Error: {e}")

    # --- STEP 2: PDF GENERATION ---
    if st.session_state.analysis_done and st.session_state.dress_data:
        data = st.session_state.dress_data
        
        st.markdown(f"### 📏 {data.get('dress_name_ml')} ({data.get('dress_name_en')})")
        st.markdown(f'<div class="fabric-badge">🧵 ഈ വസ്ത്രം തയ്ക്കാൻ ഏകദേശം {data.get("estimated_fabric")} തുണി ആവശ്യമാണ്.</div>', unsafe_allow_html=True)
        
        with st.form("measurement_form"):
            user_measurements = {}
            cols = st.columns(3)
            for i, (m_name, m_default) in enumerate(data.get("measurements_needed", {}).items()):
                col_index = i % 3
                with cols[col_index]:
                    user_measurements[m_name] = st.number_input(m_name, value=float(m_default), step=0.5)
            
            st.markdown("---")
            submit_btn = st.form_submit_button("✂️ A3 PDF പാറ്റേൺ തയ്യാറാക്കുക")
            
        if submit_btn:
            with st.spinner("അളവുകൾ വെച്ച് A3 PDF ഡ്രോയിംഗ് തയ്യാറാക്കുന്നു (ഇതിന് അല്പം സമയമെടുക്കും)..."):
                try:
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    svg_prompt = f"""
                    You are a precise Vector CAD Engine. Generate a NON-OVERLAPPING SVG cutting layout.
                    Dress Type: {data.get('dress_name_en')}
                    Measurements: {meas_str}
                    RULES:
                    1. Output `<svg viewBox="0 0 1400 900" width="100%" height="100%" style="background:#ffffff;">`
                    2. Divide into strict non-overlapping horizontal panels.
                    3. Draw Black solid lines for cutting, Red dashed for sewing, Green dashed for FOLD.
                    4. Output ONLY the raw SVG code inside an XML block, followed by cutting instructions in Malayalam.
                    """
                    
                    image = Image.open(uploaded_file)
                    svg_response = client.models.generate_content(model="gemini-2.5-flash", contents=[svg_prompt, image])
                    output_text = svg_response.text
                    
                    svg_match = re.search(r"<svg[\s\S]*?<\/svg>", output_text)
                    instructions = re.sub(r"```[\s\S]*?

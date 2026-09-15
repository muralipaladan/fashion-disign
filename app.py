import streamlit as st
from google import genai
from PIL import Image
import re
import json

# --- 1. MODERN UI CONFIGURATION ---
st.set_page_config(
    page_title="Smart AI Tailor Studio", 
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 10px;}
    .sub-header { font-size: 1rem; color: #64748B; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-weight: bold; }
    .fabric-badge { background-color: #dcfce7; color: #166534; padding: 10px 15px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 1.1rem; border: 1px solid #bbf7d0; margin-bottom: 20px;}
    .svg-container { background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 20px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Two-Step Smart AI: 1. Analyze Design ➔ 2. Generate Pattern</div>', unsafe_allow_html=True)

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

# --- 3. STATE MANAGEMENT (For 2-Step Process) ---
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
        # പുതിയ ഫയൽ വന്നാൽ സ്റ്റേറ്റ് റീസെറ്റ് ചെയ്യുക
        if st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.analysis_done = False
            st.session_state.dress_data = None
            st.session_state.last_uploaded_file = uploaded_file.name
            
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Design", use_container_width=True)

with col_act:
    if uploaded_file and not st.session_state.analysis_done:
        st.markdown("### 🔍 2. ഡിസൈൻ വിശകലനം (AI Analysis)")
        st.info("ഫോട്ടോ വിശകലനം ചെയ്ത് വസ്ത്രത്തിന്റെ തരം, ആവശ്യമായ തുണി, എടുക്കേണ്ട അളവുകൾ എന്നിവ കണ്ടെത്താൻ താഴെ ക്ലിക്ക് ചെയ്യുക.")
        
        if st.button("✨ ഡിസൈൻ അനലൈസ് ചെയ്യുക", type="primary"):
            with st.spinner("AI വസ്ത്രം തിരിച്ചറിയുന്നു..."):
                try:
                    # PROMPT 1: JSON Analysis Only
                    analysis_prompt = """
                    Analyze the uploaded dress photo. You are an expert AI tailor.
                    Identify the dress type, estimate the fabric required (in meters), and list the STANDARD basic measurements required to stitch this specific dress.
                    
                    Return ONLY a valid JSON object in the following format. Do NOT add markdown blocks, backticks, or extra text.
                    {
                        "dress_name_ml": "വസ്ത്രത്തിന്റെ പേര് മലയാളത്തിൽ",
                        "dress_name_en": "Dress Name in English",
                        "estimated_fabric": "ആവശ്യമായ തുണി (e.g., 2.5 മീറ്റർ)",
                        "measurements_needed": {
                            "Shoulder": 14.0,
                            "Chest": 36.0,
                            "Waist": 32.0,
                            "Length": 40.0
                        }
                    }
                    """
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[analysis_prompt, image]
                    )
                    
                    # Clean response text to ensure JSON parsing works
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    dress_data = json.loads(raw_json)
                    
                    st.session_state.dress_data = dress_data
                    st.session_state.analysis_done = True
                    st.rerun() # Refresh to show step 2
                    
                except Exception as e:
                    st.error(f"Analysis failed. Please ensure the image is clear. Error: {e}")

    # --- STEP 2: SHOW DYNAMIC FORM & GENERATE PATTERN ---
    if st.session_state.analysis_done and st.session_state.dress_data:
        data = st.session_state.dress_data
        
        st.markdown(f"### 📏 {data.get('dress_name_ml', 'വസ്ത്രം')} ({data.get('dress_name_en', 'Dress')})")
        st.markdown(f'<div class="fabric-badge">🧵 ഈ വസ്ത്രം തയ്ക്കാൻ ഏകദേശം {data.get("estimated_fabric", "2 മീറ്റർ")} തുണി ആവശ്യമാണ്.</div>', unsafe_allow_html=True)
        
        st.write("താഴെ പറയുന്ന അളവുകൾ (Inches) കൃത്യമായി നൽകുക:")
        
        # Dynamic Form based on AI suggested measurements
        with st.form("measurement_form"):
            user_measurements = {}
            cols = st.columns(3)
            
            # Create inputs dynamically
            for i, (m_name, m_default) in enumerate(data.get("measurements_needed", {}).items()):
                col_index = i % 3
                with cols[col_index]:
                    user_measurements[m_name] = st.number_input(m_name, value=float(m_default), step=0.5)
            
            st.markdown("---")
            submit_btn = st.form_submit_button("✂️ കട്ടിംഗ് ഡയഗ്രം വരയ്ക്കുക (Generate SVG Layout)")
            
        if submit_btn:
            with st.spinner("അളവുകൾ വെച്ച് A3 കാൻവാസിൽ ഡ്രോയിംഗ് തയ്യാറാക്കുന്നു..."):
                try:
                    # PROMPT 2: SVG Generation using user's dynamic inputs
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    svg_prompt = f"""
                    You are a precise Vector CAD Engine. Generate a NON-OVERLAPPING SVG cutting layout.
                    
                    Dress Type: {data.get('dress_name_en')}
                    Provided Measurements: {meas_str}
                    
                    RULES:
                    1. Output `<svg viewBox="0 0 1600 900" style="background:#ffffff;">`
                    2. Divide into strict non-overlapping horizontal panels based on the parts needed for this dress.
                    3. Draw Black solid lines for cutting, Red dashed for sewing (1.5" allowance), Green dashed for FOLD.
                    4. Output ONLY the raw SVG code inside an XML block, followed by cutting instructions in Malayalam.
                    """
                    
                    image = Image.open(uploaded_file)
                    svg_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[svg_prompt, image]
                    )
                    
                    output_text = svg_response.text
                    svg_match = re.search(r"<svg[\s\S]*?<\/svg>", output_text)
                    
                    if svg_match:
                        svg_code = svg_match.group(0)
                        st.success("✅ ഡയഗ്രം വിജയകരമായി തയ്യാറാക്കി!")
                        
                        st.markdown('<div class="svg-container">', unsafe_allow_html=True)
                        st.components.v1.html(svg_code, height=750, scrolling=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        st.download_button(
                            label="📥 ഡയഗ്രം ഡൗൺലോഡ് ചെയ്യുക (SVG)",
                            data=svg_code,
                            file_name="Smart_Tailor_Pattern.svg",
                            mime="image/svg+xml"
                        )
                    else:
                        st.error("⚠️ ഡയഗ്രം ജനറേറ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല.")
                        
                    # മുമ്പ് വന്നിരുന്ന unterminated string literal എറർ ഇവിടെ പരിഹരിച്ചിട്ടുണ്ട്
                    instructions = re.sub(r"```[\s\S]*?```", "", output_text).strip()
                    if instructions:
                        with st.expander("✂️ തയ്യൽ നിർദ്ദേശങ്ങൾ (കൂടുതൽ വായിക്കാൻ ക്ലിക്ക് ചെയ്യുക)", expanded=True):
                            st.markdown(instructions)
                            
                except Exception as e:
                    st.error(f"ഡയഗ്രം വരയ്ക്കുന്നതിൽ പിഴവ് സംഭവിച്ചു: {e}")

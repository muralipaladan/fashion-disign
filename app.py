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
    .svg-container { background-color: white; border-radius: 12px; padding: 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 20px; overflow: hidden; border: 1px solid #e2e8f0;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio (Pro A3 Version)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Perfectly Scaled A3 Print-Ready Cutting Patterns</div>', unsafe_allow_html=True)

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
        
        if st.button("✨ ഡിസൈൻ അനലൈസ് ചെയ്യുക", type="primary"):
            with st.spinner("AI വസ്ത്രം തിരിച്ചറിയുന്നു..."):
                try:
                    analysis_prompt = """
                    Analyze the uploaded dress photo. Identify the dress type, estimate the fabric required (in meters), and list the STANDARD basic measurements required to stitch this specific dress.
                    Return ONLY a valid JSON object.
                    {
                        "dress_name_ml": "വസ്ത്രത്തിന്റെ പേര്",
                        "dress_name_en": "Dress Name",
                        "estimated_fabric": "2.5 മീറ്റർ",
                        "measurements_needed": { "Shoulder": 14.0, "Chest": 36.0, "Waist": 32.0, "Length": 40.0, "Armhole": 16.0 }
                    }
                    """
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[analysis_prompt, image]
                    )
                    
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state.dress_data = json.loads(raw_json)
                    st.session_state.analysis_done = True
                    st.rerun() 
                    
                except Exception as e:
                    st.error(f"Analysis failed. Error: {e}")

    # --- STEP 2: SHOW DYNAMIC FORM & GENERATE PERFECT A3 SCALED PATTERN ---
    if st.session_state.analysis_done and st.session_state.dress_data:
        data = st.session_state.dress_data
        
        st.markdown(f"### 📏 {data.get('dress_name_ml', 'വസ്ത്രം')} ({data.get('dress_name_en', 'Dress')})")
        st.markdown(f'<div class="fabric-badge">🧵 ഈ വസ്ത്രം തയ്ക്കാൻ ഏകദേശം {data.get("estimated_fabric", "2 മീറ്റർ")} തുണി ആവശ്യമാണ്.</div>', unsafe_allow_html=True)
        
        with st.form("measurement_form"):
            user_measurements = {}
            cols = st.columns(3)
            
            for i, (m_name, m_default) in enumerate(data.get("measurements_needed", {}).items()):
                col_index = i % 3
                with cols[col_index]:
                    user_measurements[m_name] = st.number_input(m_name, value=float(m_default), step=0.5)
            
            st.markdown("---")
            submit_btn = st.form_submit_button("✂️ Generate Perfect A3 Scaled Pattern")
            
        if submit_btn:
            with st.spinner("കൃത്യമായ സ്കെയിലിൽ A3 ലേഔട്ട് വരയ്ക്കുന്നു... (ഇതിന് അല്പം സമയമെടുത്തേക്കാം)"):
                try:
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    # STRICT MATHEMATICAL PROMPT FOR A3 SCALE
                    svg_prompt = f"""
                    You are a Master Pattern Drafter producing a strict mathematical CAD vector drawing.
                    Draft a Print-Ready A3 Landscape sewing pattern for: {data.get('dress_name_en')}.
                    Measurements: {meas_str}
                    
                    CRITICAL MATHEMATICAL SCALING & LAYOUT RULES:
                    1. HTML & SVG SIZE: Use an A3 Landscape HTML template. The SVG must be `<svg viewBox="0 0 1600 1100" width="100%" height="100%" style="background:#ffffff; font-family: Arial, sans-serif;">`.
                    2. SCALE FACTOR: 1 Inch = 20 SVG units. 
                       - Example: If Top Length is 15", draw it 300 units long (15 * 20).
                       - Example: If Shoulder half is 7", draw it 140 units wide (7 * 20).
                       You MUST mathematically apply this 1:20 multiplier to ALL drawing paths (d="M...").
                    3. TEXT SIZE: Set `font-size="16"` for measurements and `font-size="22"` for titles. NEVER use massive text. Position text beautifully next to the lines.
                    4. GRID PLACEMENT (NO OVERLAPPING):
                       Draw the parts starting at these exact origin coordinates to ensure they are spaced out across the A3 sheet:
                       - FRONT BODICE starts at X=100, Y=100. (Fold line goes down along X=100)
                       - BACK BODICE starts at X=500, Y=100. (Fold line goes down along X=500)
                       - SLEEVE starts at X=900, Y=100.
                       - SKIRT / FLARE starts at X=1200, Y=100.
                    5. Include cutting lines (solid black #000, 2px), sewing lines (dashed red #d32f2f, 1.5px), and Fold lines (dashed green #2e7d32, 3px). Add explicit text labels (e.g., 'Chest: 10.5"').
                    
                    Output ONLY the valid HTML code starting with `<!DOCTYPE html>` inside an `html` code block.
                    """
                    
                    image = Image.open(uploaded_file)
                    svg_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[svg_prompt, image]
                    )
                    
                    output_text = svg_response.text
                    html_match = re.search(r"```html\s*(<!DOCTYPE html>[\s\S]*?)```", output_text, re.IGNORECASE)
                    
                    if not html_match:
                        html_match = re.search(r"(<!DOCTYPE html>[\s\S]*?</html>)", output_text, re.IGNORECASE)

                    if html_match:
                        html_code = html_match.group(1)
                        st.success("✅ Perfect A3 പാറ്റേൺ തയ്യാർ! ഡൗൺലോഡ് ചെയ്ത് പ്രിന്റ് ചെയ്യാം.")
                        
                        st.markdown('<div class="svg-container">', unsafe_allow_html=True)
                        st.components.v1.html(html_code, height=850, scrolling=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        col_dl, col_info = st.columns([1, 1])
                        with col_dl:
                            st.download_button(
                                label="📥 Download A3 Pattern (HTML/PDF format)",
                                data=html_code,
                                file_name="A3_Smart_Tailor_Pattern.html",
                                mime="text/html"
                            )
                        with col_info:
                            st.info("💡 ഡൗൺലോഡ് ചെയ്ത ഫയൽ ബ്രൗസറിൽ ഓപ്പൺ ചെയ്ത് `Print -> Paper Size: A3 -> Landscape` നൽകി സേവ് ചെയ്യാം.")

                    else:
                        st.error("⚠️ ഡയഗ്രം ജനറേറ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
                        
                except Exception as e:
                    st.error(f"ഡയഗ്രം വരയ്ക്കുന്നതിൽ പിഴവ് സംഭവിച്ചു: {e}")

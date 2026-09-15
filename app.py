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
    .svg-container { background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 20px; border: 1px solid #e2e8f0;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio (Pro A3 Grid Version)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Table Layout: Zero Overlapping & Downloadable A3 Print</div>', unsafe_allow_html=True)

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

    # --- STEP 2: SHOW DYNAMIC FORM & GENERATE A3 TABLE GRID PATTERN ---
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
            submit_btn = st.form_submit_button("✂️ Generate Table Layout Pattern")
            
        if submit_btn:
            with st.spinner("ടേബിൾ ലേഔട്ടിൽ വെവ്വേറെ പാറ്റേണുകൾ തയ്യാറാക്കുന്നു..."):
                try:
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    # STRICT HTML GRID PROMPT (THE PERMANENT FIX)
                    svg_prompt = f"""
                    You are a Master Pattern Drafter. Generate a mathematically perfect, STRICTLY NON-OVERLAPPING Print-Ready A3 layout for: {data.get('dress_name_en')}.
                    Measurements: {meas_str}
                    
                    PERMANENT FOOLPROOF SOLUTION (HTML GRID TABLE):
                    Do NOT draw all pieces in a single giant SVG. Instead, you MUST create an HTML document with a CSS Grid (2x2 Table) where each garment piece has its own completely separate `<svg>` canvas.

                    RULES:
                    1. HTML & CSS Structure: 
                       Start with `<!DOCTYPE html><html><head><style>`
                       `@page {{ size: A3 landscape; margin: 1cm; }}`
                       `body {{ font-family: Arial, sans-serif; background: white; margin: 0; padding: 20px; }}`
                       `.grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; width: 100%; }}`
                       `.grid-item {{ border: 2px solid #cbd5e1; padding: 20px; border-radius: 8px; position: relative; }}`
                       `.title-bar {{ background: #f1f5f9; padding: 10px; font-weight: bold; font-size: 18px; margin-bottom: 10px; border-bottom: 2px solid #cbd5e1; }}`
                       `</style></head><body><div class="grid-container">`

                    2. Generate 4 `<div class="grid-item">` blocks. Inside each block:
                       - Add a `<div class="title-bar">` with the Piece Name and Scale (e.g., "FRONT BODICE | Scale: 1 Inch = 20 Units").
                       - Add an independent `<svg viewBox="0 0 1000 1200" width="100%" height="450">`.

                    3. The 4 blocks MUST be:
                       - Block 1: Front Bodice
                       - Block 2: Back Bodice
                       - Block 3: Sleeves
                       - Block 4: Skirt / Lower section

                    4. Scaling & Coordinate Math:
                       - Apply a scale of 1 Inch = 20 SVG units. (e.g. 15" length = 300 units).
                       - Because each piece has its OWN isolated SVG now, start drawing EVERY piece from local `x=50, y=50`. NO HUGE TRANSLATE OFFSETS NEEDED.
                       
                    5. Text Placement (Prevent Overlap):
                       - Place measurement text logically. Use `dx="20"` or `dy="-15"` in `<text>` tags to keep text completely away from the path lines.
                       - Text size should be `font-size="16"`.
                       
                    6. Colors: Black 2px for cutting line, Red dashed 1.5px for sewing, Green dashed 3px for Fold lines.

                    Output ONLY valid HTML starting with `<!DOCTYPE html>` containing the CSS Grid and SVGs inside an `html` code block.
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
                        st.success("✅ ടേബിൾ ലേഔട്ട് തയ്യാർ! ഓരോ പാറ്റേണും വെവ്വേറെ ബോക്സുകളിലാണ്.")
                        
                        st.markdown('<div class="svg-container">', unsafe_allow_html=True)
                        st.components.v1.html(html_code, height=900, scrolling=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        col_dl, col_info = st.columns([1, 1])
                        with col_dl:
                            st.download_button(
                                label="📥 Download A3 Pattern (HTML/PDF format)",
                                data=html_code,
                                file_name="A3_Table_Layout_Pattern.html",
                                mime="text/html"
                            )
                        with col_info:
                            st.info("💡 ഡൗൺലോഡ് ചെയ്ത ഫയൽ ബ്രൗസറിൽ ഓപ്പൺ ചെയ്ത് `Print -> Paper Size: A3 -> Landscape` നൽകി സേവ് ചെയ്യാം.")

                    else:
                        st.error("⚠️ ഡയഗ്രം ജനറേറ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
                        
                except Exception as e:
                    st.error(f"ഡയഗ്രം വരയ്ക്കുന്നതിൽ പിഴവ് സംഭവിച്ചു: {e}")

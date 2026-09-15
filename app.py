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
    .svg-container { background-color: white; border-radius: 12px; padding: 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 20px; overflow: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio (Pro Version)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">2-Step AI: Accurate Dimension Marking & PDF Ready Output</div>', unsafe_allow_html=True)

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
                    Return ONLY a valid JSON object. No markdown, no extra text.
                    {
                        "dress_name_ml": "വസ്ത്രത്തിന്റെ പേര്",
                        "dress_name_en": "Dress Name",
                        "estimated_fabric": "2.5 മീറ്റർ",
                        "measurements_needed": { "Shoulder": 14.0, "Chest": 36.0, "Waist": 32.0, "Length": 40.0 }
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

    # --- STEP 2: SHOW DYNAMIC FORM & GENERATE PDF-READY PATTERN ---
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
            submit_btn = st.form_submit_button("✂️ Smart Pattern തയ്യാറാക്കുക (With Dimensions)")
            
        if submit_btn:
            with st.spinner("കൃത്യമായ അളവുകൾ രേഖപ്പെടുത്തിയ ഡയഗ്രം തയ്യാറാക്കുന്നു..."):
                try:
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    # STRICT PROMPT FOR MEASUREMENTS AND HTML
                    svg_prompt = f"""
                    You are a precise Master Tailor and Vector CAD Engine. Generate a fully marked, Print-Ready cutting layout for a {data.get('dress_name_en')}.
                    Measurements: {meas_str}
                    
                    CRITICAL REQUIREMENTS (DO NOT IGNORE):
                    1. NON-OVERLAPPING PANELS: Draw Front, Back, Sleeves, etc., in separate X-coordinate spaces so they NEVER overlap.
                    2. DIMENSION LABELS: EVERY SINGLE EDGE (shoulder, armhole, chest width, waist, bottom, full length) MUST have a text label showing its exact calculated measurement in inches (e.g., 'Chest: 10.5"', 'Shoulder: 7"').
                    3. DIMENSION LINES: Draw thin lines/arrows pointing to the edges to show what the measurement refers to.
                    4. SEAM ALLOWANCE: Show stitching lines in red dashed strokes and include 1.5" seam allowance in calculations.
                    5. FOLD LINES: Mark "On Fold" clearly with green dashed lines.
                    6. OUTPUT FORMAT: Generate a complete HTML document (starting with `<!DOCTYPE html>`) that includes the SVG (viewBox="0 0 1600 1200") and a CSS `@media print` query setting the page to Landscape. 
                    
                    Output ONLY the raw HTML code inside an `html` code block. No explanations before or after.
                    """
                    
                    image = Image.open(uploaded_file)
                    svg_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[svg_prompt, image]
                    )
                    
                    output_text = svg_response.text
                    html_match = re.search(r"```html\s*(<!DOCTYPE html>[\s\S]*?)```", output_text, re.IGNORECASE)
                    
                    if not html_match:
                        # Fallback if AI didn't use markdown block properly
                        html_match = re.search(r"(<!DOCTYPE html>[\s\S]*?</html>)", output_text, re.IGNORECASE)

                    if html_match:
                        html_code = html_match.group(1)
                        st.success("✅ അളവുകൾ അടയാളപ്പെടുത്തിയ പാറ്റേൺ തയ്യാർ!")
                        
                        # Displaying the generated HTML/SVG
                        st.markdown('<div class="svg-container">', unsafe_allow_html=True)
                        st.components.v1.html(html_code, height=800, scrolling=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        # Provide HTML file for downloading (Which can be easily printed as PDF)
                        col_dl, col_info = st.columns([1, 1])
                        with col_dl:
                            st.download_button(
                                label="📥 Download Print-Ready Pattern (HTML/PDF format)",
                                data=html_code,
                                file_name="Smart_Tailor_Pattern.html",
                                mime="text/html"
                            )
                        with col_info:
                            st.info("💡 ഡൗൺലോഡ് ചെയ്ത ഫയൽ ബ്രൗസറിൽ ഓപ്പൺ ചെയ്ത് `Ctrl + P` (അല്ലെങ്കിൽ Print) നൽകിയാൽ കൃത്യമായ PDF ആയി സേവ് ചെയ്യാം.")

                    else:
                        st.error("⚠️ ഡയഗ്രം ജനറേറ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
                        
                except Exception as e:
                    st.error(f"ഡയഗ്രം വരയ്ക്കുന്നതിൽ പിഴവ് സംഭവിച്ചു: {e}")

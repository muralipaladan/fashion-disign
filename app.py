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

st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 10px;}
    .sub-header { font-size: 1rem; color: #64748B; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-weight: bold; }
    .fabric-badge { background-color: #dcfce7; color: #166534; padding: 10px 15px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 1.1rem; border: 1px solid #bbf7d0; margin-bottom: 20px;}
    .svg-container { background-color: transparent; padding: 0; margin-top: 10px; border-radius: 12px; overflow: hidden; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio (Interactive Pro Version)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Animated Zoom, Interactive Cards & Savable Layouts</div>', unsafe_allow_html=True)

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
    st.info("👋 തുടരാൻ ദയവായി ഇടതുവശത്ത് API Key നൽകുക.")
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
                    
                    # എറർ വന്നിരുന്ന വരി ഇവിടെ പരിഹരിച്ചിട്ടുണ്ട്
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    
                    st.session_state.dress_data = json.loads(raw_json)
                    st.session_state.analysis_done = True
                    st.rerun() 
                    
                except Exception as e:
                    st.error(f"Analysis failed. Error: {e}")

    # --- STEP 2: GENERATE INTERACTIVE ANIMATED HTML ---
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
            submit_btn = st.form_submit_button("✨ ഇന്ററാക്ടീവ് പാറ്റേൺ തയ്യാറാക്കുക (Interactive View)")
            
        if submit_btn:
            with st.spinner("ആനിമേഷനും സൂം ഫീച്ചറുമുള്ള ഇന്ററാക്ടീവ് ആപ്പ് തയ്യാറാക്കുന്നു..."):
                try:
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    # PROMPT FOR INTERACTIVE HTML WITH JS/CSS ANIMATIONS
                    interactive_prompt = f"""
                    You are an Expert UI Developer and Master Tailor. Create a standalone, highly interactive HTML5 application for tailoring patterns.
                    Dress: {data.get('dress_name_en')} | Measurements: {meas_str}
                    
                    CRITICAL REQUIREMENTS (Interactive UI & SVG):
                    1. The output MUST be a complete `<!DOCTYPE html>` file with embedded CSS and JavaScript.
                    2. CSS Styling:
                       - Create a beautiful grid of cards (`.grid-container`).
                       - Each card (`.pattern-card`) should have a subtle shadow, rounded corners, and a hover animation (`transform: scale(1.03); transition: 0.3s; cursor: pointer;`).
                       - Create a Fullscreen Modal (`.modal`) with a dark overlay, which is hidden by default. When active, it displays the clicked SVG in large, full-screen view. Include a smooth fade-in animation.
                    3. JavaScript Logic:
                       - Add an `onclick` event to each card that opens the `.modal`.
                       - The JS must copy the clicked SVG into the modal body and display the title.
                       - Add a Close button (`&times;`) to exit the modal.
                    4. SVG Content & Scaling (NO OVERLAPPING):
                       - Create 4 separate `<div class="pattern-card">` elements.
                       - Inside each card, add an `<svg viewBox="0 0 1000 1200">`.
                       - Apply a scale of 1 Inch = 20 SVG units for paths.
                       - Draw Front Bodice, Back Bodice, Sleeve, and Skirt in their respective separate cards.
                       - Since they are in separate SVGs, start paths at local `(x=50, y=50)`.
                       - Add explicit dimension text (`font-size="20"`, `fill="#334155"`) next to the lines. Use `dx/dy` offsets to prevent text overlapping lines.
                    
                    Output ONLY valid HTML code inside an `html` code block. No markdown chatter.
                    """
                    
                    image = Image.open(uploaded_file)
                    svg_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[interactive_prompt, image]
                    )
                    
                    output_text = svg_response.text
                    html_match = re.search(r"```html\s*(<!DOCTYPE html>[\s\S]*?)```", output_text, re.IGNORECASE)
                    
                    if not html_match:
                        html_match = re.search(r"(<!DOCTYPE html>[\s\S]*?</html>)", output_text, re.IGNORECASE)

                    if html_match:
                        html_code = html_match.group(1)
                        st.success("✅ ഇന്ററാക്ടീവ് വ്യൂ തയ്യാർ! കാർഡുകളിൽ ക്ലിക്ക് ചെയ്ത് സൂം ചെയ്ത് കാണാം.")
                        
                        # Displaying interactive HTML inside Streamlit
                        st.markdown('<div class="svg-container">', unsafe_allow_html=True)
                        st.components.v1.html(html_code, height=800, scrolling=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        # Downloadable Standalone HTML App
                        col_dl, col_info = st.columns([1, 1])
                        with col_dl:
                            st.download_button(
                                label="📥 സിസ്റ്റത്തിൽ സേവ് ചെയ്യുക (Interactive App File)",
                                data=html_code,
                                file_name="Interactive_Tailor_Pattern.html",
                                mime="text/html"
                            )
                        with col_info:
                            st.info("💡 ഫയൽ ഡൗൺലോഡ് ചെയ്ത ശേഷം ഡബിൾ ക്ലിക്ക് ചെയ്താൽ ഇത് ഒരു ആപ്പ് പോലെ ബ്രൗസറിൽ വർക്ക് ചെയ്യും.")

                    else:
                        st.error("⚠️ ഫയൽ ജനറേറ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
                        
                except Exception as e:
                    st.error(f"പിഴവ് സംഭവിച്ചു: {e}")

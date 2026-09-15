import streamlit as st
from google import genai
from PIL import Image
import re
import json

# --- 1. MODERN UI CONFIGURATION ---
st.set_page_config(
    page_title="Smart AI Tailor Studio (Interactive)", 
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Streamlit UI
st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 10px;}
    .sub-header { font-size: 1rem; color: #64748B; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-weight: bold; }
    .fabric-badge { background-color: #dcfce7; color: #166534; padding: 10px 15px; border-radius: 8px; font-weight: bold; text-align: center; font-size: 1.1rem; border: 1px solid #bbf7d0; margin-bottom: 20px;}
    .svg-container { background-color: #f8fafc; border-radius: 12px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 20px; border: 1px solid #e2e8f0;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio (Interactive View)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Hover to Zoom & Click for Fullscreen Details | Downloadable Interactive File</div>', unsafe_allow_html=True)

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

    # --- STEP 2: SHOW DYNAMIC FORM & GENERATE INTERACTIVE HTML ---
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
            submit_btn = st.form_submit_button("✂️ Generate Interactive Pattern")
            
        if submit_btn:
            with st.spinner("ഇന്ററാക്റ്റീവ് ആനിമേറ്റഡ് ഫയൽ തയ്യാറാക്കുന്നു..."):
                try:
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    # PROMPT FOR INTERACTIVE HTML WITH JS AND CSS MODALS
                    interactive_prompt = f"""
                    You are a Master Pattern Drafter and a Frontend Web Developer. Generate an INTERACTIVE HTML file for: {data.get('dress_name_en')}.
                    Measurements: {meas_str}
                    
                    CRITICAL REQUIREMENTS FOR THE HTML CODE:
                    1. Create a beautiful responsive Grid (`display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;`).
                    2. Generate 4 separate `<div class="card" onclick="openModal(this)">` blocks (Front, Back, Sleeve, Skirt).
                    3. INSIDE EACH CARD, place an independent `<svg viewBox="-20 -20 600 800" width="100%" height="300px">`. 
                       - Start drawing paths near 0,0 since each SVG is independent. Use 1 inch = 15 units scale.
                       - Add text labels with exact measurements alongside the paths.
                    
                    4. CSS ANIMATION (HOVER & ZOOM):
                       Embed CSS styles in the `<head>`:
                       `.card {{ background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; width: 350px; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}`
                       `.card:hover {{ transform: scale(1.05); border-color: #3b82f6; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }}`
                       `.card-title {{ font-size: 18px; font-weight: bold; color: #1e293b; text-align: center; margin-bottom: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }}`
                       
                    5. JAVASCRIPT FULLSCREEN MODAL:
                       Embed a Fullscreen Modal in the HTML body and JavaScript to open it:
                       ```html
                       <div id="myModal" style="display:none; position:fixed; z-index:100; left:0; top:0; width:100%; height:100%; background-color:rgba(0,0,0,0.9);">
                           <span onclick="closeModal()" style="position:absolute; top:20px; right:40px; color:white; font-size:40px; font-weight:bold; cursor:pointer;">&times;</span>
                           <div id="modal-content" style="margin: 5% auto; background: white; padding: 30px; width: 90%; height: 85%; border-radius: 10px; display: flex; justify-content: center; align-items: center; overflow: hidden;">
                           </div>
                       </div>
                       <script>
                           function openModal(element) {{
                               document.getElementById("myModal").style.display = "block";
                               // Copy the inner HTML of the clicked card (the Title + SVG) into the modal
                               document.getElementById("modal-content").innerHTML = element.innerHTML;
                               // Make the cloned SVG large inside the modal
                               var svg = document.getElementById("modal-content").getElementsByTagName("svg")[0];
                               svg.style.height = "100%";
                               svg.style.width = "100%";
                           }}
                           function closeModal() {{
                               document.getElementById("myModal").style.display = "none";
                           }}
                       </script>

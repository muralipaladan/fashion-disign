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
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio (Pro View)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Guaranteed Interactive Zoom Layout</div>', unsafe_allow_html=True)

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
                    
                    raw_json = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state.dress_data = json.loads(raw_json)
                    st.session_state.analysis_done = True
                    st.rerun() 
                    
                except Exception as e:
                    st.error(f"Analysis failed. Error: {e}")

    # --- STEP 2: GENERATE SVGs & INJECT INTO PYTHON HTML TEMPLATE ---
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
            submit_btn = st.form_submit_button("✨ ഇന്ററാക്ടീവ് പാറ്റേൺ തയ്യാറാക്കുക")
            
        if submit_btn:
            with st.spinner("ഡയഗ്രമുകൾ തയ്യാറാക്കുന്നു... (ഇതിന് അല്പം സമയമെടുത്തേക്കാം)"):
                try:
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    # PROMPT: ASK ONLY FOR SVG BLOCKS (Reduces AI Load = Prevents Blank Screens)
                    svg_prompt = f"""
                    You are a Master Pattern Drafter. Draw 4 SEPARATE mathematical SVG cutting diagrams for {data.get('dress_name_en')}.
                    Measurements: {meas_str}
                    
                    CRITICAL INSTRUCTIONS:
                    1. Output EXACTLY 4 `<svg>` elements. Do NOT write HTML, JS, or CSS. ONLY SVGs.
                    2. Draw the Front Bodice, Back Bodice, Sleeve, and Skirt separately.
                    3. Each SVG must use `<svg viewBox="0 0 1000 1200" xmlns="http://www.w3.org/2000/svg">`.
                    4. SCALE: 1 Inch = 20 Units. (e.g., 15" = 300 units). Start drawing from x=50, y=50 in EVERY SVG.
                    5. Include clear text measurements (font-size="22", dx="20") next to the lines.
                    6. DO NOT use placeholders. You MUST draw the `<path>` elements completely.
                    
                    Provide the 4 SVGs sequentially.
                    """
                    
                    image = Image.open(uploaded_file)
                    svg_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[svg_prompt, image]
                    )
                    
                    output_text = svg_response.text
                    
                    # പൈത്തൺ ഉപയോഗിച്ച് 4 ചിത്രങ്ങളും വേർതിരിച്ചെടുക്കുന്നു
                    svgs = re.findall(r"<svg[\s\S]*?<\/svg>", output_text, re.IGNORECASE)
                    
                    if len(svgs) > 0:
                        front_svg = svgs[0] if len(svgs) > 0 else "<svg><text x='50' y='50'>Front Panel Missing</text></svg>"
                        back_svg = svgs[1] if len(svgs) > 1 else "<svg><text x='50' y='50'>Back Panel Missing</text></svg>"
                        sleeve_svg = svgs[2] if len(svgs) > 2 else "<svg><text x='50' y='50'>Sleeve Panel Missing</text></svg>"
                        skirt_svg = svgs[3] if len(svgs) > 3 else "<svg><text x='50' y='50'>Skirt Panel Missing</text></svg>"
                        
                        # --- INTERACTIVE HTML TEMPLATE (HARDCODED IN PYTHON) ---
                        interactive_html = f"""
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                        <meta charset="UTF-8">
                        <title>Interactive Smart Pattern</title>
                        <style>
                            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
                            .title-main {{ text-align: center; color: #1e293b; margin-bottom: 30px; font-size: 24px; font-weight: bold; }}
                            .grid-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; padding: 10px; }}
                            .card {{ background: white; border-radius: 12px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; text-align: center; }}
                            .card:hover {{ transform: scale(1.02); box-shadow: 0 10px 15px rgba(0,0,0,0.1); border-color: #3b82f6; }}
                            .card h3 {{ margin: 0 0 15px 0; color: #334155; font-size: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; }}
                            .card svg {{ width: 100%; height: auto; max-height: 350px; pointer-events: none; }}
                            
                            /* Modal Styling */
                            .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(15, 23, 42, 0.9); backdrop-filter: blur(5px); }}
                            .modal-content {{ background-color: white; margin: 2% auto; padding: 20px; border-radius: 12px; width: 90%; max-width: 900px; height: 85%; position: relative; display: flex; flex-direction: column; }}
                            .close {{ position: absolute; right: 20px; top: 15px; color: #ef4444; font-size: 35px; font-weight: bold; cursor: pointer; line-height: 1; }}
                            .close:hover {{ color: #b91c1c; }}
                            .modal-svg-container {{ flex-grow: 1; overflow: auto; display: flex; justify-content: center; align-items: center; background: #f8fafc; border-radius: 8px; margin-top: 15px; border: 1px solid #cbd5e1; }}
                            .modal-svg-container svg {{ width: 100%; height: 100%; max-height: 700px; }}
                            .zoom-hint {{ text-align: center; color: #64748b; font-size: 14px; margin-top: 10px; }}
                        </style>
                        </head>
                        <body>

                        <div class="title-main">✂️ Interactive Pattern Layout (Click on a card to Zoom)</div>

                        <div class="grid-container">
                            <div class="card" onclick="openModal(this)">
                                <h3>FRONT BODICE</h3>
                                {front_svg}
                            </div>
                            <div class="card" onclick="openModal(this)">
                                <h3>BACK BODICE</h3>
                                {back_svg}
                            </div>
                            <div class="card" onclick="openModal(this)">
                                <h3>SLEEVE (Cut 2)</h3>
                                {sleeve_svg}
                            </div>
                            <div class="card" onclick="openModal(this)">
                                <h3>SKIRT / BOTTOM</h3>
                                {skirt_svg}
                            </div>
                        </div>

                        <!-- The Modal -->
                        <div id="myModal" class="modal">
                            <div class="modal-content">
                                <span class="close" onclick="closeModal()">&times;</span>
                                <h2 id="modal-title" style="margin:0; color:#1e293b; font-size: 20px;">Pattern View</h2>
                                <div id="modal-body" class="modal-svg-container"></div>
                                <div class="zoom-hint">Scroll to zoom in/out (if supported by browser)</div>
                            </div>
                        </div>

                        <script>
                            function openModal(cardElement) {{
                                // Get the title and SVG from the clicked card
                                const title = cardElement.querySelector('h3').innerText;
                                const svgCode = cardElement.querySelector('svg').outerHTML;
                                
                                // Set them in the modal
                                document.getElementById('modal-title').innerText = title + " (Detailed View)";
                                document.getElementById('modal-body').innerHTML = svgCode;
                                
                                // Show the modal
                                document.getElementById('myModal').style.display = 'block';
                            }}

                            function closeModal() {{
                                document.getElementById('myModal').style.display = 'none';
                                document.getElementById('modal-body').innerHTML = '';
                            }}
                            
                            // Close modal when clicking outside the content box
                            window.onclick = function(event) {{
                                const modal = document.getElementById('myModal');
                                if (event.target == modal) {{
                                    closeModal();
                                }}
                            }}
                        </script>

                        </body>
                        </html>
                        """
                        
                        st.success("✅ ഇന്ററാക്ടീവ് വ്യൂ തയ്യാർ! താഴെ കാണുന്ന കാർഡുകളിൽ ക്ലിക്ക് ചെയ്ത് സൂം ചെയ്ത് അളവുകൾ കാണാം.")
                        
                        # Display inside Streamlit
                        st.components.v1.html(interactive_html, height=750, scrolling=True)

                        # Download File
                        col_dl, col_info = st.columns([1, 1])
                        with col_dl:
                            st.download_button(
                                label="📥 സിസ്റ്റത്തിൽ സേവ് ചെയ്യുക (Interactive App File)",
                                data=interactive_html,
                                file_name="Interactive_Tailor_Pattern.html",
                                mime="text/html"
                            )
                        with col_info:
                            st.info("💡 ഈ ഫയൽ ഡൗൺലോഡ് ചെയ്ത് ഫോൾഡറിൽ സൂക്ഷിക്കാം. ഇന്റർനെറ്റ് ഇല്ലാതെ തന്നെ പിന്നീട് ഉപയോഗിക്കാം.")

                    else:
                        st.error("⚠️ ഡയഗ്രം വരയ്ക്കാൻ AI-ക്ക് കഴിഞ്ഞില്ല. ഫോട്ടോ ഒന്നുകൂടി അപ്‌ലോഡ് ചെയ്ത് ശ്രമിക്കുക.")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        st.error("⏳ API ലിമിറ്റ് കഴിഞ്ഞിരിക്കുന്നു. ദയവായി ഒരു മിനിറ്റ് കാത്തിരുന്ന ശേഷം വീണ്ടും ശ്രമിക്കുക.")
                    else:
                        st.error(f"പിഴവ് സംഭവിച്ചു: {e}")

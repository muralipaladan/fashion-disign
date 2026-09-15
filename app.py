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
st.markdown('<div class="sub-header">Beautifully Scaled & Naturally Spaced Layouts</div>', unsafe_allow_html=True)

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

    # --- STEP 2: GENERATE BEAUTIFUL SVGs ---
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
            submit_btn = st.form_submit_button("✨ മനോഹരമായ ലേഔട്ട് തയ്യാറാക്കുക")
            
        if submit_btn:
            with st.spinner("അളവുകൾ വെച്ച് മനോഹരമായ ഡയഗ്രമുകൾ തയ്യാറാക്കുന്നു..."):
                try:
                    meas_str = ", ".join([f"{k}: {v}\"" for k, v in user_measurements.items()])
                    
                    # PROMPT: BEAUTIFUL, NATURAL SPACING & LARGER SCALE
                    svg_prompt = f"""
                    You are a Master Pattern Drafter and UI/UX Designer. Draw 4 SEPARATE, BEAUTIFUL, and NATURALLY SPACED mathematical SVG cutting diagrams for {data.get('dress_name_en')}.
                    Measurements: {meas_str}
                    
                    CRITICAL INSTRUCTIONS FOR A BEAUTIFUL LAYOUT (NO OVERLAPPING TEXT):
                    1. Output EXACTLY 4 `<svg>` elements. ONLY SVGs. Do not output anything else.
                    2. Use `<svg viewBox="0 0 800 1000" xmlns="http://www.w3.org/2000/svg">` for each.
                    3. SCALE UP: Use 1 Inch = 25 SVG Units. This makes the drawing larger and fills the canvas nicely. Start drawing from roughly x=150, y=150 to center it.
                    4. NATURAL TEXT SPACING (CRUCIAL): 
                       - NEVER cluster text in one spot.
                       - Distribute dimension labels logically around the perimeter of the shape.
                       - Push text away from the lines using large absolute coordinates or offsets (e.g., if a line is at x=200, put the text at x=100 or x=300).
                       - Use `font-size="20"` and clear colors (`fill="#1e293b"`).
                    5. Add a bold, centered Title at the very top of the SVG canvas (`<text x="400" y="60" text-anchor="middle" font-size="26" font-weight="bold">TITLE</text>`).
                    6. Draw Front Bodice, Back Bodice, Sleeve, and Skirt separately in the 4 SVGs. Use solid black for cut lines, dashed red for seams.
                    """
                    
                    image = Image.open(uploaded_file)
                    svg_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[svg_prompt, image]
                    )
                    
                    output_text = svg_response.text
                    svgs = re.findall(r"<svg[\s\S]*?<\/svg>", output_text, re.IGNORECASE)
                    
                    if len(svgs) > 0:
                        front_svg = svgs[0] if len(svgs) > 0 else "<svg><text x='150' y='150'>Front Panel Missing</text></svg>"
                        back_svg = svgs[1] if len(svgs) > 1 else "<svg><text x='150' y='150'>Back Panel Missing</text></svg>"
                        sleeve_svg = svgs[2] if len(svgs) > 2 else "<svg><text x='150' y='150'>Sleeve Panel Missing</text></svg>"
                        skirt_svg = svgs[3] if len(svgs) > 3 else "<svg><text x='150' y='150'>Skirt Panel Missing</text></svg>"
                        
                        interactive_html = f"""
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                        <meta charset="UTF-8">
                        <title>Beautiful Pattern Layout</title>
                        <style>
                            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
                            .title-main {{ text-align: center; color: #0f172a; margin-bottom: 30px; font-size: 26px; font-weight: bold; letter-spacing: 0.5px; }}
                            .grid-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; padding: 10px; }}
                            .card {{ background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; cursor: pointer; transition: all 0.3s ease; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
                            .card:hover {{ transform: translateY(-5px) scale(1.02); box-shadow: 0 12px 20px rgba(0,0,0,0.1); border-color: #3b82f6; }}
                            .card h3 {{ margin: 0 0 15px 0; color: #1e293b; font-size: 18px; width: 100%; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; }}
                            .card svg {{ width: 100%; height: auto; max-height: 400px; pointer-events: none; }}
                            
                            .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(15, 23, 42, 0.95); backdrop-filter: blur(8px); }}
                            .modal-content {{ background-color: #ffffff; margin: 2% auto; padding: 30px; border-radius: 16px; width: 92%; max-width: 1000px; height: 85%; position: relative; display: flex; flex-direction: column; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }}
                            .close {{ position: absolute; right: 25px; top: 20px; color: #ef4444; font-size: 40px; font-weight: bold; cursor: pointer; line-height: 1; transition: color 0.2s; }}
                            .close:hover {{ color: #991b1b; }}
                            .modal-svg-container {{ flex-grow: 1; overflow: hidden; display: flex; justify-content: center; align-items: center; background: #f8fafc; border-radius: 12px; margin-top: 20px; border: 1px solid #cbd5e1; padding: 20px; }}
                            .modal-svg-container svg {{ width: 100%; height: 100%; object-fit: contain; }}
                            .zoom-hint {{ text-align: center; color: #64748b; font-size: 15px; margin-top: 15px; font-weight: 500; }}
                        </style>
                        </head>
                        <body>

                        <div class="title-main">✂️ Beautiful Pattern Layout (Click to Expand)</div>

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
                                <h3>SLEEVE</h3>
                                {sleeve_svg}
                            </div>
                            <div class="card" onclick="openModal(this)">
                                <h3>SKIRT / LOWER</h3>
                                {skirt_svg}
                            </div>
                        </div>

                        <div id="myModal" class="modal">
                            <div class="modal-content">
                                <span class="close" onclick="closeModal()">&times;</span>
                                <h2 id="modal-title" style="margin:0; color:#0f172a; font-size: 24px; font-weight: bold;">Pattern View</h2>
                                <div id="modal-body" class="modal-svg-container"></div>
                                <div class="zoom-hint">Perfectly Scaled Vector Diagram</div>
                            </div>
                        </div>

                        <script>
                            function openModal(cardElement) {{
                                const title = cardElement.querySelector('h3').innerText;
                                const svgCode = cardElement.querySelector('svg').outerHTML;
                                document.getElementById('modal-title').innerText = title + " (Detailed Cut)";
                                document.getElementById('modal-body').innerHTML = svgCode;
                                document.getElementById('myModal').style.display = 'block';
                            }}
                            function closeModal() {{
                                document.getElementById('myModal').style.display = 'none';
                                document.getElementById('modal-body').innerHTML = '';
                            }}
                            window.onclick = function(event) {{
                                const modal = document.getElementById('myModal');
                                if (event.target == modal) {{ closeModal(); }}
                            }}
                        </script>

                        </body>
                        </html>
                        """
                        
                        st.success("✅ മനോഹരമായ ഇന്ററാക്ടീവ് വ്യൂ തയ്യാർ! കാർഡുകളിൽ ക്ലിക്ക് ചെയ്ത് കാണുക.")
                        
                        st.components.v1.html(interactive_html, height=750, scrolling=True)

                        col_dl, col_info = st.columns([1, 1])
                        with col_dl:
                            st.download_button(
                                label="📥 സിസ്റ്റത്തിൽ സേവ് ചെയ്യുക (Interactive App)",
                                data=interactive_html,
                                file_name="Beautiful_Tailor_Pattern.html",
                                mime="text/html"
                            )
                        with col_info:
                            st.info("💡 ഫയൽ ഡൗൺലോഡ് ചെയ്ത് ഫോൾഡറിൽ സൂക്ഷിക്കാം. ഇന്റർനെറ്റ് ഇല്ലാതെ തന്നെ പ്രവർത്തിക്കും.")

                    else:
                        st.error("⚠️ ഡയഗ്രം വരയ്ക്കാൻ കഴിഞ്ഞില്ല. വീണ്ടും ശ്രമിക്കുക.")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        st.error("⏳ API ലിമിറ്റ് കഴിഞ്ഞിരിക്കുന്നു. ദയവായി ഒരു മിനിറ്റ് കാത്തിരുന്ന ശേഷം വീണ്ടും ശ്രമിക്കുക.")
                    else:
                        st.error(f"പിഴവ് സംഭവിച്ചു: {e}")

import streamlit as st
from google import genai
from PIL import Image
import re

# --- 1. MODERN UI CONFIGURATION ---
st.set_page_config(
    page_title="Smart AI Tailor Studio", 
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern look
st.markdown("""
    <style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; text-align: center; }
    .sub-header { font-size: 1.1rem; color: #64748B; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-size: 1.1rem; font-weight: bold; }
    .svg-container { background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">✂️ Smart AI Tailor Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload a design & get a precise, foolproof 2D cutting layout</div>', unsafe_allow_html=True)

# --- 2. SIDEBAR & CREDENTIALS ---
with st.sidebar:
    st.header("⚙️ Settings & API")
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter Gemini 2.5 Flash API Key", type="password", help="Get this from Google AI Studio")
    
    st.markdown("---")
    st.header("📏 Body Measurements (Inches)")
    dress_type = st.selectbox("Garment Type", ["Auto-detect (Smart)", "A-Line Kurti", "Straight Kurti", "Blouse", "Shirt", "Trousers"])
    
    col1, col2 = st.columns(2)
    with col1:
        shoulder = st.number_input("Shoulder", value=14.0, step=0.5)
        chest = st.number_input("Chest/Bust", value=36.0, step=0.5)
        waist = st.number_input("Waist", value=32.0, step=0.5)
        hip = st.number_input("Hip", value=38.0, step=0.5)
    with col2:
        top_len = st.number_input("Top Length", value=15.0, step=0.5)
        full_len = st.number_input("Full Length", value=42.0, step=0.5)
        sleeve_len = st.number_input("Sleeve Length", value=16.0, step=0.5)
        armhole = st.number_input("Armhole", value=16.0, step=0.5)

if not api_key:
    st.info("👋 Welcome! Please enter your Gemini API Key in the sidebar to start generating patterns.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- 3. MAIN WORKSPACE (TABS) ---
tab1, tab2 = st.tabs(["🖼️ Design Upload & Generation", "📖 How to use this tool"])

with tab1:
    col_img, col_act = st.columns([1, 2])
    
    with col_img:
        st.markdown("### 1. Upload Design")
        uploaded_file = st.file_uploader("Drop your dress photo here", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Target Design", use_container_width=True)
            
    with col_act:
        st.markdown("### 2. Generate Pattern")
        if st.button("🚀 Analyze & Generate AI Pattern", type="primary"):
            if not uploaded_file:
                st.error("⚠️ Please upload a dress image first.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔍 Analyzing design and fabric ease...")
                progress_bar.progress(30)
                
                try:
                    # STRICT FOOLPROOF PROMPT
                    prompt = f"""
                    You are a highly precise Vector CAD Engine for tailoring.
                    Generate a COMPLETE and STRICTLY NON-OVERLAPPING SVG cutting layout.

                    Inputs:
                    - Type: {dress_type}
                    - Measurements: Shoulder {shoulder}", Chest {chest}", Waist {waist}", Hip {hip}", Bodice {top_len}", Total Length {full_len}", Sleeve {sleeve_len}".

                    SVG STRUCTURE RULES (MUST FOLLOW STRICTLY):
                    1. Use `<svg viewBox="0 0 1600 900" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff; font-family:sans-serif;">`
                    2. Divide the canvas into 4 FIXED bounding boxes. NO path should exceed its box.
                       - Box 1 (Front): X from 50 to 400
                       - Box 2 (Back): X from 450 to 800
                       - Box 3 (Sleeve): X from 850 to 1200
                       - Box 4 (Skirt/Bottom): X from 1250 to 1550
                    3. For each part:
                       - Draw a dashed green line on the left edge denoting "FOLD LINE".
                       - Draw the solid black cutting line (include 1.5" seam allowance).
                       - Draw a red dashed inner stitching line.
                       - Add text labels showing calculated dimensions (e.g., Chest/4 + 1.5).
                    4. Add a title at the top of each box (e.g., "FRONT (Cut 1 on Fold)").
                    5. Output ONLY the raw SVG code inside an xml codeblock. Do not add any conversational text before or after the SVG. Add Malayalam cutting instructions below the SVG inside a markdown block.
                    """
                    
                    status_text.text("📐 Drafting geometric vector paths...")
                    progress_bar.progress(60)

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[prompt, image]
                    )
                    
                    status_text.text("✨ Finalizing layout...")
                    progress_bar.progress(90)
                    
                    output_text = response.text
                    svg_match = re.search(r"<svg[\s\S]*?<\/svg>", output_text)
                    
                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()

                    if svg_match:
                        svg_code = svg_match.group(0)
                        
                        st.success("✅ Pattern generated successfully!")
                        st.markdown('<div class="svg-container">', unsafe_allow_html=True)
                        st.components.v1.html(svg_code, height=750, scrolling=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        st.download_button(
                            label="📥 Download HD Pattern (SVG)",
                            data=svg_code,
                            file_name="Smart_Tailor_Pattern.svg",
                            mime="image/svg+xml"
                        )
                    else:
                        st.error("⚠️ Failed to generate precise geometry. Try again.")
                        with st.expander("Show AI Raw Output"):
                            st.code(output_text)

                    # Instructions
                    instructions = re.sub(r"```[\s\S]*?```", "", output_text).strip()
                    if instructions:
                        with st.expander("✂️ Malayalam Cutting Instructions (Click to expand)", expanded=True):
                            st.markdown(instructions)

                except Exception as e:
                    st.error(f"An error occurred: {e}")

with tab2:
    st.markdown("""
    ### എങ്ങനെ ഉപയോഗിക്കാം?
    1. **API Key നൽകുക:** ഇടതുവശത്ത് നിങ്ങളുടെ Google Gemini API Key നൽകുക.
    2. **അളവുകൾ നൽകുക:** തയ്ക്കാൻ ഉദ്ദേശിക്കുന്ന വ്യക്തിയുടെ കൃത്യമായ അളവുകൾ ഇൻപുട്ട് ചെയ്യുക.
    3. **ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക:** ഏതുതരം വസ്ത്രമാണോ തയ്ക്കേണ്ടത്, അതിന്റെ ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക.
    4. **Generate ബട്ടൺ അമർത്തുക:** AI കൃത്യമായ കണക്കുകൂട്ടലുകൾ നടത്തി ഓവർലാപ്പ് ഇല്ലാത്ത കട്ടിംഗ് ലേഔട്ട് നിർമ്മിച്ചു നൽകും.
    
    *പ്രത്യേക ശ്രദ്ധയ്ക്ക്:* സീം അലവൻസ് (തയ്യൽതുമ്പ് - 1.5 ഇഞ്ച്) ഉൾപ്പെടെയുള്ള അളവുകളാണ് ഡയഗ്രമിൽ കാണിക്കുക.
    """)

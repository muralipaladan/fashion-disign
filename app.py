import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import re

# പേജ് കോൺഫിഗറേഷൻ (A3 വൈഡ് വ്യൂവിന് അനുയോജ്യമായി)
st.set_page_config(
    page_title="AI Tailor Pattern Drafter (A3 Sheet)", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("✂️ AI ഡ്രസ്സ് കട്ടിംഗ് പാറ്റേൺ ജനറേറ്റർ (A3 ഷീറ്റ് ലേഔട്ട്)")
st.write("വസ്ത്രത്തിന്റെ ചിത്രവും അളവുകളും നൽകി ഓവർലാപ്പില്ലാത്ത കൃത്യമായ A3 കട്ടിംഗ് ഡയഗ്രം നേടുക.")

# API കീ ലോഡ് ചെയ്യുന്നു
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key നൽകുക", type="password")

if not api_key:
    st.warning("തുടരാൻ ദയവായി നിങ്ങളുടെ Gemini API Key നൽകുക.")
    st.stop()

# Gemini 2.5 Flash ക്ലയന്റ് കോൺഫിഗറേഷൻ
client = genai.Client(api_key=api_key)

# സൈഡ്‌ബാർ - അളവുകൾ
st.sidebar.header("📏 ശരീര അളവുകൾ (Inches)")
dress_type = st.sidebar.selectbox(
    "വസ്ത്രത്തിന്റെ തരം", 
    ["Auto-detect from Photo", "Kurti / Kameez", "Frock / Anarkali", "Blouse", "Shirt", "Pants / Trouser"]
)

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    shoulder = st.number_input("Shoulder Width", value=14.0, step=0.5)
    chest = st.number_input("Chest / Bust", value=36.0, step=0.5)
    waist = st.number_input("Waist", value=32.0, step=0.5)
    hip = st.number_input("Hip", value=38.0, step=0.5)

with col_s2:
    bodice_len = st.number_input("Bodice / Top Length", value=15.0, step=0.5)
    full_length = st.number_input("Full Length", value=42.0, step=0.5)
    sleeve_length = st.number_input("Sleeve Length", value=16.0, step=0.5)
    armhole = st.number_input("Armhole Round", value=16.0, step=0.5)

# പ്രധാന വിൻഡോ - ചിത്രം അപ്‌ലോഡ്
uploaded_file = st.file_uploader("വസ്ത്രത്തിന്റെ ഡിസൈൻ ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="അപ്‌ലോഡ് ചെയ്ത മോഡൽ", width=260)

if st.button("✂️ A3 കട്ടിംഗ് പാറ്റേൺ തയ്യാറാക്കുക", type="primary"):
    if not uploaded_file:
        st.error("ദയവായി ഒരു ഡ്രസ്സ് ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക.")
        st.stop()

    with st.spinner("Gemini 2.5 Flash A3 ഷീറ്റിലേക്ക് ഓവർലാപ്പില്ലാത്ത ലേഔട്ട് തയ്യാറാക്കുന്നു..."):
        try:
            # കൃത്യമായ A3 ഗ്രിഡ് പ്ലാനിംഗ് നൽകുന്ന എൻജിനീയറിംഗ് പ്രോംപ്റ്റ്
            prompt = f"""
            You are a professional Master Pattern Drafter and Vector CAD Designer.
            Analyze the uploaded dress photo and draft a complete, clean, NON-OVERLAPPING sewing cutting diagram inside an A3 LANDSCAPE sheet format.

            INPUT MEASUREMENTS (Inches):
            - Dress Type: {dress_type}
            - Shoulder Width: {shoulder}" (Half: {shoulder/2}")
            - Chest/Bust: {chest}" (Quarter: {chest/4}" + Ease 1.5" = {chest/4 + 1.5}")
            - Waist: {waist}" (Quarter: {waist/4}" + Ease 1.5" = {waist/4 + 1.5}")
            - Hip: {hip}" (Quarter: {hip/4}" + Ease 1.5" = {hip/4 + 1.5}")
            - Top/Bodice Length: {bodice_len}" (+ Seam Allowance 1.5" = {bodice_len + 1.5}")
            - Full Length: {full_length}"
            - Sleeve Length: {sleeve_length}" (+ Hem fold 1.5" = {sleeve_length + 1.5}")
            - Armhole: {armhole}"

            CRITICAL A3 CANVAS & NON-OVERLAPPING GRID RULES:
            1. Canvas: SVG viewBox="0 0 1400 950" with a crisp white background (#ffffff) and subtle border.
            2. The sheet is divided strictly into 4 SEPARATE, NON-INTERSECTING PANELS across the page:
               - PANEL 1 (x: 40 to 350, y: 80 to 750): FRONT BODICE. Left edge is the FOLD LINE (bold green dashed stroke).
               - PANEL 2 (x: 380 to 690, y: 80 to 750): BACK BODICE. Left edge is FOLD LINE (bold green dashed stroke).
               - PANEL 3 (x: 720 to 1030, y: 80 to 750): SLEEVE BLOCK (Cut 2). Center vertical line marked as grain/fold.
               - PANEL 4 (x: 1060 to 1370, y: 80 to 750): SKIRT FLARE / LOWER PANEL (Cut on fold).
            3. STRICT CONSTRAINT: NO element or path from one panel must ever cross into another panel's X coordinates.
            4. VISUAL STYLES:
               - Cutting Edge: Solid Dark Slate Line (#0f172a, stroke-width 2.5)
               - Stitching Line (Inner Seam Margin): Red Dashed Line (#dc2626, stroke-dasharray="5,4", stroke-width 1.5)
               - Fold / Grain Line: Green Dashed Line (#16a34a, stroke-width 2.5)
               - Dimension Markers: Thin arrows (#475569) with clear numerical labels in inches.
            5. Clear title tags above each panel: e.g., '1. FRONT BODICE (Cut 1 on fold)'.
            6. Bottom Legend Area (y: 800 to 920): Fabric spreading table details, seam allowance guide (1.5" side seam, 0.5" neck/armhole, 1.5" hem fold).

            OUTPUT:
            1. Standalone valid SVG code starting with `<svg viewBox="0 0 1400 950"` wrapped in ```xml ... ```.
            2. Step-by-step cutting instructions in Malayalam explaining how to fold the fabric and cut each piece safely.
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image]
            )
            output_text = response.text

            # SVG വേർതിരിച്ചെടുക്കുന്നു
            svg_match = re.search(r"<svg[\s\S]*?<\/svg>", output_text)

            if svg_match:
                svg_code = svg_match.group(0)
                
                # വെളുത്ത ബാക്ക്‌ഗ്രൗണ്ട് പൂർണ്ണമായി ഉറപ്പാക്കുന്നു
                if 'style="background' not in svg_code:
                    svg_code = svg_code.replace('<svg', '<svg style="background-color: #ffffff; border-radius: 8px;"', 1)

                st.subheader("📐 A3 പ്രിന്റബിൾ കട്ടിംഗ് പാറ്റേൺ ലേഔട്ട്")
                
                # വിസ്താരമുള്ള A3 കാൻവാസ് ഡിസ്‌പ്ലേ
                st.components.v1.html(
                    f"""
                    <div style="width: 100%; overflow-x: auto; background-color: #f1f5f9; padding: 15px; border-radius: 10px;">
                        {svg_code}
                    </div>
                    """, 
                    height=780, 
                    scrolling=True
                )

                # A3 SVG ഡൗൺലോഡ് ബട്ടൺ
                col_d1, col_d2 = st.columns([1, 4])
                with col_d1:
                    st.download_button(
                        label="📥 A3 പാറ്റേൺ ഡൗൺലോഡ് ചെയ്യുക (SVG)",
                        data=svg_code,
                        file_name="A3_Tailor_Cutting_Pattern.svg",
                        mime="image/svg+xml"
                    )

            else:
                st.warning("SVG കോഡ് വേർതിരിച്ചെടുക്കാൻ കഴിഞ്ഞില്ല. ലഭിച്ച മറുപടി താഴെ നൽകുന്നു:")
                st.code(output_text)

            # മലയാളത്തിലുള്ള നിർദ്ദേശങ്ങൾ
            st.subheader("📝 കട്ടിംഗ് & തയ്യൽ നിർദ്ദേശങ്ങൾ (Cutting Guide)")
            instructions = re.sub(r"```[\s\S]*?```", "", output_text).strip()
            st.markdown(instructions)

        except Exception as e:
            st.error(f"പ്രശ്നം സംഭവിച്ചു: {e}")

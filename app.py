import streamlit as st
import google.generativeai as genai
from PIL import Image
import re

# പേജ് കോൺഫിഗറേഷൻ
st.set_page_config(page_title="AI Tailor Pattern Drafter", layout="wide")

st.title("✂️ AI ഡ്രസ്സ് കട്ടിംഗ് പാറ്റേൺ ജനറേറ്റർ")
st.write("വസ്ത്രത്തിന്റെ ചിത്രവും അളവുകളും നൽകി തയ്യൽ കട്ടിംഗ് ഡയഗ്രം (SVG) നേടുക.")

# API കീ ലോഡ് ചെയ്യുന്നു
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key നൽകുക", type="password")

if not api_key:
    st.warning("തുടരാൻ ദയവായി Gemini API Key നൽകുക.")
    st.stop()

genai.configure(api_key=api_key)

# സൈഡ്‌ബാർ - ഇൻപുട്ട് അളവുകൾ (ഇഞ്ചിൽ)
st.sidebar.header("ശരീര അളവുകൾ (Inches)")
dress_type = st.sidebar.selectbox("വസ്ത്രത്തിന്റെ തരം", ["Custom (Auto-detect)", "Kurti / Kameez", "Blouse", "Shirt", "Pants / Trouser"])
shoulder = st.sidebar.number_input("Shoulder Width", value=14.0, step=0.5)
chest = st.sidebar.number_input("Chest / Bust", value=36.0, step=0.5)
waist = st.sidebar.number_input("Waist", value=32.0, step=0.5)
hip = st.sidebar.number_input("Hip", value=38.0, step=0.5)
full_length = st.sidebar.number_input("Full Length", value=42.0, step=0.5)
sleeve_length = st.sidebar.number_input("Sleeve Length", value=16.0, step=0.5)
armhole = st.sidebar.number_input("Armhole Circumference", value=16.0, step=0.5)

# പ്രധാന വിൻഡോ - ചിത്രം അപ്‌ലോഡ്
uploaded_file = st.file_uploader("ഡിസൈൻ കാണിക്കുന്ന ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="അപ്‌ലോഡ് ചെയ്ത വസ്ത്രം", width=300)

if st.button("കട്ടിംഗ് പാറ്റേൺ തയ്യാറാക്കുക", type="primary"):
    if not uploaded_file:
        st.error("ദയവായി ഒരു ഡ്രസ്സ് ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക.")
        st.stop()

    with st.spinner("AI ഡിസൈൻ വിശകലനം ചെയ്ത് പാറ്റേൺ വരയ്ക്കുന്നു..."):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            You are an expert master tailor and pattern drafting software.
            Analyze the uploaded dress photo and create a precise 2D sewing cutting pattern diagram.

            Selected Type: {dress_type}
            Measurements (Inches):
            - Shoulder: {shoulder}
            - Chest/Bust: {chest}
            - Waist: {waist}
            - Hip: {hip}
            - Full Length: {full_length}
            - Sleeve Length: {sleeve_length}
            - Armhole: {armhole}

            Tasks:
            1. Calculate necessary standard tailor allowances (Ease: +1.5 to 2 inch, Seam allowance: 1.5 inch, Hem fold: 1.5 to 2 inch).
            2. Generate a valid, clean, self-contained SVG diagram (width 1000px, height 700px, with viewBox).
            3. Draw the layout representing folded fabric (On-fold lines).
            4. Include:
               - Front Panel (with Neckline and Armhole depth marked)
               - Back Panel
               - Sleeve Cutting Block
            5. Add visible dimension text labels (measurements in inches), dotted lines for seam allowances, and cutting directions.
            6. Add a brief textual note explaining the step-by-step cutting instructions in Malayalam below the SVG.

            Return the raw SVG code inside ```xml ... ``` or ```html ... ``` code block.
            """

            response = model.generate_content([prompt, image])
            output_text = response.text

            # SVG വേർതിരിച്ചെടുക്കുന്നു
            svg_match = re.search(r"<svg[\s\S]*?<\/svg>", output_text)

            if svg_match:
                svg_code = svg_match.group(0)
                st.subheader("📐 തുണി വെട്ടേണ്ട ഡയഗ്രം (Cutting Pattern Layout)")
                st.components.v1.html(svg_code, height=650, scrolling=True)

                # SVG ഡൗൺലോഡ് ചെയ്യാനുള്ള ബട്ടൺ
                st.download_button(
                    label="ഡയഗ്രം SVG ആയി ഡൗൺലോഡ് ചെയ്യുക",
                    data=svg_code,
                    file_name="pattern_layout.svg",
                    mime="image/svg+xml"
                )
            else:
                st.warning("SVG കോഡ് വേർതിരിച്ചെടുക്കാൻ കഴിഞ്ഞില്ല. AI മറുപടി താഴെ നൽകുന്നു:")
                st.code(output_text)

            # നിർദ്ദേശങ്ങൾ കാണിക്കുക
            st.subheader("📝 കട്ടിംഗ് നിർദ്ദേശങ്ങൾ (Instructions)")
            # SVG ഭാഗം ഒഴിവാക്കി ബാക്കി നിർദ്ദേശങ്ങൾ മാത്രം കാണിക്കുന്നു
            instructions = re.sub(r"```[\s\S]*?```", "", output_text).strip()
            st.markdown(instructions)

        except Exception as e:
            st.error(f"പ്രശ്നം സംഭവിച്ചു: {e}")

import streamlit as st
import requests
import io
import os
from PIL import Image

# ==========================================
# IMAGE GENERATOR AI
# ==========================================

st.set_page_config(
    page_title="Image Generator AI",
    page_icon="🎨",
    layout="wide"
)

# ==========================================
# PAGE DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #10131f, #20283c);
    color: white;
}

h1, h2, h3, p, label {
    color: white !important;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 45px;
    font-weight: bold;
}

div[data-testid="stFileUploader"] {
    border: 1px dashed #7c8db5;
    border-radius: 12px;
    padding: 12px;
}

.hero {
    padding: 22px;
    border-radius: 18px;
    background: linear-gradient(120deg, #303b65, #5b347c);
    margin-bottom: 20px;
}

.small-text {
    color: #c9d2e8;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================

st.markdown("""
<div class="hero">
    <h1>🎨 Image Generator AI</h1>
    <p class="small-text">
        Create images from prompts and edit your photos with AI.
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# CONFIGURATION
# ==========================================

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

# Select a model available to your Hugging Face account.
DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"

API_URL = "https://router.huggingface.co/hf-inference/models/"

# ==========================================
# SESSION STATE
# ==========================================

if "generated_image" not in st.session_state:
    st.session_state.generated_image = None

if "image_history" not in st.session_state:
    st.session_state.image_history = []

if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""

# ==========================================
# AI IMAGE REQUEST
# ==========================================

def generate_image(prompt, uploaded_image=None):
    if not HF_TOKEN:
        st.error(
            "HF_TOKEN is missing. Add your Hugging Face "
            "access token to Streamlit Secrets."
        )
        return None

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 4
        }
    }

    # This request uses the text-to-image endpoint.
    # Image editing needs a model/provider that explicitly
    # supports image-to-image or instruction-based editing.
    if uploaded_image is not None:
        st.warning(
            "This model request is text-to-image. "
            "Uploading a photo here does not automatically edit it. "
            "Connect an image-editing model to enable photo modification."
        )

    url = API_URL + DEFAULT_MODEL

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=180
        )

        if response.status_code != 200:
            try:
                details = response.json()
            except ValueError:
                details = response.text[:1000]

            st.error(
                f"Image service error ({response.status_code}): "
                f"{details}"
            )
            return None

        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        return image

    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
    except requests.exceptions.RequestException as exc:
        st.error(f"Network error: {exc}")
    except Exception as exc:
        st.error(f"Could not process the generated image: {exc}")

    return None

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("⚙️ Settings")

    page = st.radio(
        "Choose a tool",
        [
            "Text to Image",
            "Image Editor",
            "My Creations",
            "About"
        ]
    )

    st.divider()

    st.caption("Model")
    st.code(DEFAULT_MODEL)

    st.caption("AI service requires an available model and access.")

# ==========================================
# TEXT TO IMAGE
# ==========================================

if page == "Text to Image":

    st.subheader("✨ Create an Image")

    prompt = st.text_area(
        "Describe the image you want",
        placeholder=(
            "Example: A realistic full-body portrait of a woman "
            "wearing a red saree, standing in a beautiful garden, "
            "natural light, detailed photography..."
        ),
        height=130,
        key="text_prompt"
    )

    negative_prompt = st.text_input(
        "Avoid (optional)",
        placeholder="Example: blurry, low quality, distorted hands"
    )

    aspect_ratio = st.selectbox(
        "Image size",
        ["512 × 512", "768 × 768", "1024 × 1024"]
    )

    generate_button = st.button(
        "🚀 Generate Image",
        type="primary"
    )

    if generate_button:
        if not prompt.strip():
            st.warning("Please enter an image description first.")
        else:
            final_prompt = prompt.strip()

            if negative_prompt.strip():
                final_prompt += (
                    ". Avoid the following: "
                    + negative_prompt.strip()
                )

            with st.spinner("Generating your image..."):
                result = generate_image(final_prompt)

            if result is not None:
                st.session_state.generated_image = result
                st.session_state.last_prompt = final_prompt
                st.session_state.image_history.append({
                    "prompt": final_prompt,
                    "image": result.copy()
                })

    if st.session_state.generated_image is not None:
        st.divider()
        st.subheader("🖼️ Your Generated Image")

        st.image(
            st.session_state.generated_image,
            use_container_width=True
        )

        image_bytes = io.BytesIO()
        st.session_state.generated_image.save(
            image_bytes,
            format="PNG"
        )

        st.download_button(
            "📥 Download PNG",
            data=image_bytes.getvalue(),
            file_name="image_generator_ai.png",
            mime="image/png"
        )

        st.info(
            "The size selector is currently an interface option; "
            "the selected dimensions are not yet sent to the model."
        )

# ==========================================
# IMAGE EDITOR
# ==========================================

elif page == "Image Editor":

    st.subheader("🖌️ AI Photo Editor")

    st.write(
        "Upload a photo and describe the changes you want. "
        "This screen is prepared for an image-editing model."
    )

    uploaded_file = st.file_uploader(
        "Upload your image",
        type=["png", "jpg", "jpeg", "webp"]
    )

    if uploaded_file:
        try:
            original = Image.open(uploaded_file).convert("RGB")

            st.image(
                original,
                caption="Original Image",
                use_container_width=True
            )

            edit_prompt = st.text_area(
                "What should be changed?",
                placeholder=(
                    "Example: Change the background to a beach. "
                    "Keep the person's face and clothing unchanged."
                ),
                height=120
            )

            st.warning(
                "Photo editing is not connected yet. "
                "A compatible image-editing model or provider is "
                "required; a text-to-image model cannot guarantee "
                "modifications to the uploaded photo."
            )

            if st.button("🖌️ Prepare Edit Request"):
                if not edit_prompt.strip():
                    st.warning("Please describe your requested changes.")
                else:
                    st.session_state["edit_prompt"] = edit_prompt
                    st.session_state["original_upload"] = (
                        uploaded_file.getvalue()
                    )
                    st.info(
                        "Your edit request is ready. Connect a compatible "
                        "image-editing model to generate the modified image."
                    )

        except Exception:
            st.error("Could not open this image. Try another file.")

# ==========================================
# MY CREATIONS
# ==========================================

elif page == "My Creations":

    st.subheader("📚 My Creations")

    if not st.session_state.image_history:
        st.info("Your generated images will appear here.")
    else:
        for index, item in enumerate(
            reversed(st.session_state.image_history),
            start=1
        ):
            with st.expander(f"Creation {index}"):
                st.write(item["prompt"])
                st.image(
                    item["image"],
                    use_container_width=True
                )

                buffer = io.BytesIO()
                item["image"].save(buffer, format="PNG")

                st.download_button(
                    "Download Image",
                    data=buffer.getvalue(),
                    file_name=f"creation_{index}.png",
                    mime="image/png",
                    key=f"download_{index}"
                )

# ==========================================
# ABOUT
# ==========================================

elif page == "About":

    st.subheader("ℹ️ About Image Generator AI")

    st.write("""
    Image Generator AI is a Streamlit application for AI image creation.

    Features:
    - Text-to-image interface
    - Prompt-based image generation
    - Image preview and PNG download
    - Creation history during the current session
    - Image upload interface for a future editing integration

    Image generation depends on model availability, account permissions,
    service limits, and the configured Hugging Face token.

    Uploaded images and creation history are not permanently saved
    by this application.
    """)

st.divider()

st.caption(
    "Image Generator AI | Built with Python and Streamlit"
)

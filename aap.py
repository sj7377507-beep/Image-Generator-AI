import streamlit as st
import requests
import urllib.parse
import random
import io
import time
from PIL import Image

# ==========================================
# IMAGE-GENERATOR-AI
# Version 1.0
# ==========================================

st.set_page_config(
    page_title="Image Generator AI",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CSS ----------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #101322, #20263b);
    color: white;
}

h1, h2, h3, p, label {
    color: white !important;
}

.hero {
    padding: 28px;
    border-radius: 20px;
    text-align: center;
    background: linear-gradient(120deg, #4530a8, #a33bb5);
    margin-bottom: 24px;
}

.hero h1 {
    font-size: 38px;
    font-weight: 800;
}

.hero p {
    font-size: 16px;
}

.stButton button {
    width: 100%;
    min-height: 45px;
    border-radius: 12px;
    font-weight: bold;
}

.card {
    padding: 18px;
    border: 1px solid #414761;
    border-radius: 16px;
    background: rgba(255,255,255,0.04);
    margin-bottom: 14px;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------

if "history" not in st.session_state:
    st.session_state.history = []

if "generated_image" not in st.session_state:
    st.session_state.generated_image = None

if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""


# ---------------- HEADER ----------------

st.markdown("""
<div class="hero">
    <h1>🎨 Image Generator AI</h1>
    <p>Create images from your imagination using text prompts.</p>
    <p>Generate • Preview • Download</p>
</div>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("⚙️ Settings")

    image_size = st.selectbox(
        "Image Size",
        [
            "512 × 512",
            "768 × 768",
            "1024 × 1024",
            "1024 × 768",
            "768 × 1024"
        ],
        index=1
    )

    quality = st.selectbox(
        "Generation Style",
        [
            "Realistic Photography",
            "Digital Art",
            "Anime",
            "Cinematic",
            "Fantasy",
            "3D Render"
        ]
    )

    number_of_images = st.selectbox(
        "Number of Images",
        [1, 2, 3, 4],
        index=0
    )

    st.divider()

    st.info(
        "This app uses an external image-generation "
        "service. Availability and speed depend on "
        "that service."
    )

    if st.button("🗑️ Clear Image History"):
        st.session_state.history = []
        st.session_state.generated_image = None
        st.session_state.last_prompt = ""
        st.rerun()


# ---------------- PROMPT ----------------

st.subheader("✨ Describe Your Image")

prompt = st.text_area(
    "Enter your prompt",
    placeholder=(
        "Example: A beautiful landscape with mountains, "
        "a lake, golden sunset, realistic photography..."
    ),
    height=120,
    key="prompt_input"
)

negative_prompt = st.text_input(
    "Negative Prompt (Optional)",
    placeholder="Example: blurry, low quality, distorted"
)

enhance_prompt = st.checkbox(
    "Automatically enhance the prompt",
    value=True
)


# ---------------- IMAGE SIZE ----------------

width_height = {
    "512 × 512": (512, 512),
    "768 × 768": (768, 768),
    "1024 × 1024": (1024, 1024),
    "1024 × 768": (1024, 768),
    "768 × 1024": (768, 1024)
}

width, height = width_height[image_size]


# ---------------- GENERATION FUNCTION ----------------

def generate_image(
    user_prompt,
    width,
    height,
    seed,
    style,
    negative_prompt
):
    """
    Requests an image from a public image-generation
    endpoint. This service is external to Streamlit.
    """

    final_prompt = user_prompt.strip()

    if style != "Realistic Photography":
        final_prompt += f", {style} style"

    if negative_prompt.strip():
        final_prompt += (
            ", avoid: " + negative_prompt.strip()
        )

    prompt_encoded = urllib.parse.quote(
        final_prompt,
        safe=""
    )

    url = (
        f"https://image.pollinations.ai/prompt/"
        f"{prompt_encoded}"
    )

    params = {
        "width": width,
        "height": height,
        "seed": seed,
        "nologo": "true"
    }

    headers = {
        "User-Agent": "Image-Generator-AI/1.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=(20, 240)
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type", ""
    ).lower()

    if "image" not in content_type:
        raise ValueError(
            "The service did not return an image. "
            "Please try again later."
        )

    image = Image.open(
        io.BytesIO(response.content)
    ).convert("RGB")

    return image


# ---------------- GENERATE BUTTON ----------------

col1, col2 = st.columns([3, 1])

with col1:
    generate_clicked = st.button(
        "🎨 Generate Image",
        type="primary",
        use_container_width=True
    )

with col2:
    random_seed = st.button(
        "🔄 New Seed",
        use_container_width=True
    )

if random_seed:
    st.session_state["current_seed"] = random.randint(
        1, 2_000_000_000
    )

if "current_seed" not in st.session_state:
    st.session_state["current_seed"] = random.randint(
        1, 2_000_000_000
    )


# ---------------- RUN GENERATION ----------------

if generate_clicked:

    if not prompt.strip():
        st.warning(
            "Please enter a description before generating."
        )

    else:
        current_seed = st.session_state["current_seed"]

        final_prompt = prompt.strip()

        if enhance_prompt:
            final_prompt += (
                ", highly detailed, good composition, "
                "professional quality, beautiful lighting"
            )

        st.session_state.last_prompt = final_prompt

        with st.spinner(
            "🎨 Creating your image... Please wait."
        ):
            progress = st.progress(10)

            try:
                images = []

                for index in range(number_of_images):

                    progress.progress(
                        int(10 + 80 * (index + 1)
                            / number_of_images)
                    )

                    seed = current_seed + index

                    image = generate_image(
                        final_prompt,
                        width,
                        height,
                        seed,
                        quality,
                        negative_prompt
                    )

                    images.append(image)

                progress.progress(100)

                st.session_state.generated_image = images

                for image in images:
                    st.session_state.history.append({
                        "prompt": final_prompt,
                        "image": image.copy(),
                        "seed": current_seed
                    })

                st.success("Image generation completed!")

            except requests.exceptions.Timeout:
                st.error(
                    "The image service took too long. "
                    "Please try again."
                )

            except requests.exceptions.RequestException as e:
                st.error(
                    "The image service is unavailable "
                    "or returned an error."
                )
                st.caption(str(e))

            except Exception as e:
                st.error("Unable to generate the image.")
                st.caption(str(e))


# ---------------- DISPLAY IMAGE ----------------

if st.session_state.generated_image:

    st.divider()
    st.subheader("🖼️ Your Generated Images")

    images = st.session_state.generated_image

    columns = st.columns(
        min(len(images), 2)
    )

    for index, image in enumerate(images):

        with columns[index % len(columns)]:

            st.image(
                image,
                caption=f"Generated Image {index + 1}",
                use_container_width=True
            )

            buffer = io.BytesIO()

            image.save(
                buffer,
                format="PNG"
            )

            st.download_button(
                label="⬇️ Download PNG",
                data=buffer.getvalue(),
                file_name=(
                    f"image_generator_{index + 1}.png"
                ),
                mime="image/png",
                key=f"download_{index}_{len(images)}"
            )


# ---------------- IMAGE UPLOAD ----------------

st.divider()

st.subheader("🖼️ Upload an Existing Image")

uploaded_file = st.file_uploader(
    "Choose a photo to preview",
    type=["png", "jpg", "jpeg", "webp"]
)

if uploaded_file:

    uploaded_image = Image.open(
        uploaded_file
    ).convert("RGB")

    st.image(
        uploaded_image,
        caption="Uploaded Image",
        use_container_width=True
    )

    st.info(
        "Image-to-image AI editing will be added in "
        "the next version. Uploading a photo here "
        "does not yet apply AI modifications."
    )

    output_buffer = io.BytesIO()

    uploaded_image.save(
        output_buffer,
        format="PNG"
    )

    st.download_button(
        "⬇️ Download Uploaded Image",
        data=output_buffer.getvalue(),
        file_name="uploaded_image.png",
        mime="image/png"
    )


# ---------------- HISTORY ----------------

st.divider()
st.subheader("🕘 Recent Generation History")

if st.session_state.history:

    for index, item in enumerate(
        reversed(st.session_state.history[-5:])
    ):
        with st.expander(
            f"Image {len(st.session_state.history) - index}"
        ):
            st.write("Prompt:", item["prompt"])
            st.write("Seed:", item["seed"])

            st.image(
                item["image"],
                use_container_width=True
            )

else:
    st.caption(
        "Your generated images will appear here."
    )


# ---------------- FOOTER ----------------

st.divider()

st.markdown(
    "<center>🎨 Image-Generator-AI · Version 1.0"
    "</center>",
    unsafe_allow_html=True
)


import io
import re

import streamlit as st
from groq import Groq
from gtts import gTTS

st.set_page_config(
    page_title="AI Multimodal Story Studio",
    page_icon="📖",
    layout="wide"
)

st.title("📖 AI Multimodal Story Studio")
st.write("Create, read and listen to AI-generated stories.")

# Retrieve API key from Streamlit Secrets
try:
    api_key = st.secrets["GROQ_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("GROQ_API_KEY is not configured.")
    st.stop()

client = Groq(api_key=api_key)

# Use the Groq model that worked in Colab
MODEL_NAME = "openai/gpt-oss-120b"

language_codes = {
    "English": "en",
    "Urdu": "ur",
    "Hindi": "hi",
    "Arabic": "ar"
}


def generate_story(topic, genre, audience, length, language):
    word_counts = {
        "Short": 200,
        "Medium": 500,
        "Long": 900
    }

    target_words = word_counts[length]

    prompt = f"""
    Write an original, engaging story.

    Topic: {topic}
    Genre: {genre}
    Audience: {audience}
    Language: {language}
    Approximate length: {target_words} words

    Requirements:
    - Include an interesting title.
    - Introduce memorable characters.
    - Create an engaging beginning and conflict.
    - End with a satisfying conclusion.
    - Use age-appropriate content.
    - Write entirely in the requested language.
    - Return only the story and title.
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a creative storyteller."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8,
        max_completion_tokens=3000
    )

    story = response.choices[0].message.content

    if not story:
        raise ValueError("The model returned an empty story.")

    return story


def generate_audio(story, language):
    clean_story = re.sub(r"[#*_`]", "", story)

    tts = gTTS(
        text=clean_story,
        lang=language_codes[language],
        slow=False
    )

    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    return audio_buffer.getvalue()


# Store results across Streamlit reruns
if "story" not in st.session_state:
    st.session_state.story = None

if "audio" not in st.session_state:
    st.session_state.audio = None


with st.sidebar:
    st.header("Story Settings")

    topic = st.text_area(
        "Story Topic",
        placeholder="A young scientist builds a robot"
    )

    genre = st.selectbox(
        "Genre",
        [
            "Fantasy",
            "Adventure",
            "Mystery",
            "Science Fiction",
            "Horror",
            "Educational",
            "Comedy"
        ]
    )

    audience = st.selectbox(
        "Target Audience",
        ["Children", "Teenagers", "Adults"]
    )

    length = st.radio(
        "Story Length",
        ["Short", "Medium", "Long"]
    )

    language = st.selectbox(
        "Language",
        list(language_codes.keys())
    )

    generate_button = st.button(
        "✨ Generate Story & Voice",
        type="primary",
        use_container_width=True
    )


if generate_button:
    # Clear previous results
    st.session_state.story = None
    st.session_state.audio = None

    if not topic.strip():
        st.warning("Please enter a story topic.")
    else:
        try:
            with st.spinner("Generating your story..."):
                story = generate_story(
                    topic,
                    genre,
                    audience,
                    length,
                    language
                )

                st.session_state.story = story

            with st.spinner("Creating voice narration..."):
                audio = generate_audio(story, language)
                st.session_state.audio = audio

            st.success("Story and narration generated!")

        except Exception as e:
            st.error(f"Generation error: {e}")


# Display generated story
if st.session_state.story:
    st.subheader("📚 Your Generated Story")
    st.markdown(st.session_state.story)

    st.download_button(
        label="Download Story Text",
        data=st.session_state.story,
        file_name="my_story.txt",
        mime="text/plain"
    )

# Display audio if available
if st.session_state.audio:
    st.subheader("🎧 Listen to Your Story")

    st.audio(
        st.session_state.audio,
        format="audio/mp3"
    )

    st.download_button(
        label="Download MP3 Narration",
        data=st.session_state.audio,
        file_name="my_story.mp3",
        mime="audio/mpeg"
    )

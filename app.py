import streamlit as st
import os
import tempfile
import time
from pipeline import GameAnalysisPipeline
from utils.config_manager import ConfigManager

# Load Config
config = ConfigManager().config

st.set_page_config(page_title="Basketball Video Analysis", page_icon="🏀")

st.title("🏀 Basketball Video Analysis")
st.write("Upload a basketball game video to detect players, ball, passes, and generate tactical views.")

# Sidebar configuration
st.sidebar.header("Settings")
# We could expose config settings here
conf_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.5)

uploaded_file = st.file_uploader("Choose a video...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Save uploaded file to a temporary file
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())

    st.video(tfile.name)
    st.write("Video uploaded successfully!")

    if st.button("Start Analysis"):
        st.write("Initializing pipeline...")

        # Create a progress placeholder
        progress_text = "Operation in progress. Please wait..."
        my_bar = st.progress(0, text=progress_text)

        # Setup paths
        input_path = tfile.name
        output_dir = "output_videos"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"analyzed_{os.path.basename(input_path)}")

        # Run Pipeline
        try:
            pipeline = GameAnalysisPipeline()
            # We assume pipeline.run takes time.
            # In a real app, we'd want callbacks to update progress.
            # For now, we just run it synchronously.

            with st.spinner('Running AI models... This may take a while depending on video length.'):
                pipeline.run(input_path, output_path)

            my_bar.progress(100, text="Analysis Complete!")
            st.success("Analysis Complete!")

            # Display Output
            st.subheader("Analyzed Video")
            # Note: Streamlit might have issues playing some AVI codecs.
            # Ideally we'd convert to MP4 (H.264) for web display using ffmpeg.
            st.video(output_path)

            # Download Button
            with open(output_path, "rb") as file:
                btn = st.download_button(
                    label="Download Analyzed Video",
                    data=file,
                    file_name="analyzed_basketball.avi",
                    mime="video/x-msvideo"
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")

else:
    st.info("Please upload a video file to get started.")

st.markdown("---")
st.markdown("Built with ❤️ using YOLO, OpenCV, and Streamlit.")

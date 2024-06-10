import streamlit as st
import audio_pr_stream as ap
import os
import tempfile
import zipfile
import io

def process_uploaded_files(uploaded_files, output_dir):
    for uploaded_file in uploaded_files:
        file_path = os.path.join(output_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        ap.process_audio_file(file_path, sources, 'umxhq', 'cpu', output_dir)

def create_directory_structure(output_dir, zip_buffer):
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, output_dir)
            zip_buffer.write(file_path, arcname=relative_path)

def main():
    st.title("Tokoroten Audio Processing")

    sources = []
    if st.checkbox('vocals'):
        sources.append('vocals')
    if st.checkbox('drums'):
        sources.append('drums')
    if st.checkbox('bass'):
        sources.append('bass')
    if st.checkbox('other'):
        sources.append('other')

    uploaded_files = st.file_uploader("Choose files to process", accept_multiple_files=True)
    
    if st.button("Process") and uploaded_files:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)

            try:
                process_uploaded_files(uploaded_files, output_dir)

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    create_directory_structure(output_dir, zip_file)

                zip_buffer.seek(0)
                st.download_button(
                    label="Download ZIP",
                    data=zip_buffer,
                    file_name="processed_files.zip",
                    mime="application/zip"
                )
                st.success("Processing completed successfully!")
            except Exception as e:
                st.error(f"An error occurred during processing: {e}")

if __name__ == '__main__':
    main()
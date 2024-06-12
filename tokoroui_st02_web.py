import streamlit as st
import audio_pr_stream as ap
import os
import tempfile
import zipfile
import io
import shutil

def process_files(uploaded_files, output_dir, sources):
    for uploaded_file in uploaded_files:
        file_path = os.path.join(output_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if uploaded_file.name.endswith(('.wav', '.mp3')):
            ap.process_audio_file(file_path, sources, 'umxhq', 'cpu', output_dir)

def rename_and_move_files(source_dir, zip_file):
    valid_extensions = ['.wav', '.mp3', '.pdf']
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f)) and any(f.endswith(ext) for ext in valid_extensions)]
    
    for file_name in files:
        base_name, ext = os.path.splitext(file_name)
        new_base_name = base_name
        if base_name.count('X') < 2 and base_name.startswith('0'):
            new_base_name = base_name.lstrip('0') + 'X'
            new_file_name = new_base_name + ext
        elif base_name.count('X') == 1:
            new_file_name = file_name
        else:
            continue
        
        song_number = ''.join([char for char in new_base_name if char.isdigit() or char == 'X'])
        target_dir = os.path.join(song_number, '')
        
        file_path = os.path.join(source_dir, file_name)
        zip_file.write(file_path, arcname=os.path.join(target_dir, new_file_name))

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
                process_files(uploaded_files, output_dir, sources)

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    rename_and_move_files(output_dir, zip_file)

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
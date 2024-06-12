import streamlit as st
import audio_pr_stream as ap
import os
import tempfile
import zipfile
import io
import shutil

def process_files(input_folder, output_dir, sources):
    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)
        if file_name.endswith(('.wav', '.mp3')):
            ap.process_audio_file(file_path, sources, 'umxhq', 'cpu', output_dir)
        elif file_name.endswith('.pdf'):
            shutil.copy(file_path, output_dir)

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

    input_folder = st.text_input("Enter the path of the input folder")

    if input_folder:
        if st.button("Process"):
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = os.path.join(temp_dir, "output")
                os.makedirs(output_dir, exist_ok=True)

                try:
                    process_files(input_folder, output_dir, sources)

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
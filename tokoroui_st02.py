import streamlit as st
import audio_pr_stream as ap
import os
import shutil
import dropbox

def cleanup_directory(directory):
    try:
        shutil.rmtree(directory)
        st.write(f"Deleted directory: {directory}")
    except Exception as e:
        st.write(f"Failed to delete directory {directory}: {e}")

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        st.write(f"Created directory: {directory}")
    else:
        st.write(f"Directory already exists: {directory}")

def download_from_dropbox(link):
    dbx = dropbox.Dropbox(st.secrets["DB_ACCESS_TOKEN"])
    path = link.replace('https://www.dropbox.com', '').replace('?dl=0', '')
    _, f = dbx.files_download(path)
    file_path = os.path.join('/tmp', os.path.basename(path))
    with open(file_path, 'wb') as out:
        out.write(f.content)
    return file_path

def main():
    st.title("Tokoroten Audio and Document Processing")

    input_link = st.text_input("Dropbox link to the input folder")
    if input_link:
        input_dir = download_from_dropbox(input_link)
    else:
        input_dir = None

    # ユーザーのためにサーバー上に一時ディレクトリを作成
    output_dir = '/tmp/output'
    ensure_directory_exists(output_dir)

    sources = []
    if st.checkbox('vocals'):
        sources.append('vocals')
    if st.checkbox('drums'):
        sources.append('drums')
    if st.checkbox('bass'):
        sources.append('bass')
    if st.checkbox('other'):
        sources.append('other')

    if st.button("Run") and input_dir:
        try:
            for file_name in os.listdir(input_dir):
                if file_name.endswith(('.wav', '.mp3')):
                    file_path = os.path.join(input_dir, file_name)
                    audio_data, sample_rate = ap.load_audio_file(file_path)
                    ap.process_audio_file(file_path, sources, 'umxhq', 'cpu', output_dir)
            st.success("All files processed and moved successfully!")
            cleanup_directory('/tmp/output') # サーバー上の一時ディレクトリを削除
        except Exception as e:
            st.error(f"Error during processing: {e}")

if __name__ == '__main__':
    main()


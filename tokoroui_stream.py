import streamlit as st
import audio_pr_stream as ap
import os

def main():
    st.title("Tokoroten Audio Processing")

    uploaded_file = st.file_uploader("ファイルをアップロードしてください", type=['wav', 'mp3'])
    if uploaded_file is not None:
        # ファイル保存
        file_path = os.path.join("temp_dir", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # オプション選択
        sources = []
        if st.checkbox('vocals'):
            sources.append('vocals')
        if st.checkbox('drums'):
            sources.append('drums')
        if st.checkbox('bass'):
            sources.append('bass')
        if st.checkbox('other'):
            sources.append('other')

        if st.button("Run"):
            try:
                ap.process_audio_file_with_click_track(uploaded_file, sources, 'umxl', 'cpu', "output_dir", "click_sample_path")
                st.success("処理が完了しました！")
            except Exception as e:
                st.error(f"処理中にエラーが発生しました: {e}")

if __name__ == '__main__':
    main()

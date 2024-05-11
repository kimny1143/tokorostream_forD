import streamlit as st
import audio_pr_stream as ap
import os
import shutil

def rename_and_move_files(source_dir, target_base_dir):
    # 対象のファイル拡張子
    valid_extensions = ['.wav', '.mp3', '.pdf']
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f)) and any(f.endswith(ext) for ext in valid_extensions)]
    
    for file_name in files:
        # 楽曲番号の取得とファイル名の更新
        base_name, ext = os.path.splitext(file_name)
        new_base_name = base_name.lstrip('0') + 'X'
        new_file_name = new_base_name + ext
        
        song_number = ''.join([char for char in new_base_name if char.isdigit() or char == 'X'])
        target_dir = os.path.join(target_base_dir, song_number)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Created directory: {target_dir}")

        shutil.move(os.path.join(source_dir, file_name), os.path.join(target_dir, new_file_name))
        print(f"Moved and renamed {file_name} to {new_file_name} in {target_dir}")

def main():
    st.title("Tokoroten Audio and Document Processing")

    input_dir = st.text_input("入力フォルダのパスを入力してください")
    output_dir = st.text_input("出力フォルダのパスを入力してください")
    target_base_dir = st.text_input("目的のベースフォルダのパスを入力してください")

    sources = []
    if st.checkbox('vocals'):
        sources.append('vocals')
    if st.checkbox('drums'):
        sources.append('drums')
    if st.checkbox('bass'):
        sources.append('bass')
    if st.checkbox('other'):
        sources.append('other')

    if st.button("Run") and input_dir and output_dir and target_base_dir:
        try:
            # 音声ファイルの処理
            for file_name in os.listdir(input_dir):
                if file_name.endswith(('.wav', '.mp3')):
                    file_path = os.path.join(input_dir, file_name)
                    ap.process_audio_file_with_click_track(file_path, sources, 'umxl', 'cpu', output_dir, "click_sample_path")
            
            # ファイルの改名と移動
            rename_and_move_files(input_dir, target_base_dir)  # 入力フォルダのファイルを直接移動
            rename_and_move_files(output_dir, target_base_dir)  # 出力フォルダのファイルも移動
            st.success("すべてのファイルの処理と移動が完了しました！")
        except Exception as e:
            st.error(f"処理中にエラーが発生しました: {e}")

if __name__ == '__main__':
    main()

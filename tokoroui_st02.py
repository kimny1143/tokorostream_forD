import streamlit as st
import audio_pr_stream as ap
import os
import shutil

def ensure_directory_exists(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")  # 確認用の出力
        else:
            print(f"Directory already exists: {directory}")  # 既に存在する場合の出力
    except Exception as e:
        print(f"Failed to create directory {directory}: {e}")  # エラー発生時の出力


def rename_and_move_files(source_dir, target_base_dir):
    valid_extensions = ['.wav', '.mp3', '.pdf']
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f)) and any(f.endswith(ext) for ext in valid_extensions)]
    
    for file_name in files:
        base_name, ext = os.path.splitext(file_name)
        new_base_name = base_name # ファイル名の変更がない場合は元のファイル名を使用
        if base_name.count('X') < 2 and base_name.startswith('0'):
            # '0'で始まるが'X'が1つ以下のファイル名を改名
            new_base_name = base_name.lstrip('0') + 'X'
            new_file_name = new_base_name + ext
        elif base_name.count('X') == 1:
            # 既に適切な形式のファイル名はそのまま使用
            new_file_name = file_name
        else:
            # 命名規則に合わないファイルやXが2回以上あるファイルはスキップ
            continue
        
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
        ensure_directory_exists(output_dir)
        try:
            for file_name in os.listdir(input_dir):
                if file_name.endswith(('.wav', '.mp3')):
                    file_path = os.path.join(input_dir, file_name)
                    audio_data, sample_rate = ap.load_audio_file(file_path)
                    ap.process_audio_file(file_path, sources, 'umxhq', 'cpu', output_dir)
                
            rename_and_move_files(input_dir, target_base_dir)
            rename_and_move_files(output_dir, target_base_dir)
            st.success("すべてのファイルの処理と移動が完了しました！")
        except Exception as e:
            st.error(f"処理中にエラーが発生しました: {e}")

if __name__ == '__main__':
    main()

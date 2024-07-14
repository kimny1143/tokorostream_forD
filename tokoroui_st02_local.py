import streamlit as st
import audio_pr_stream as ap  # Ensure this moduleは正しくインポートされていることを確認してください
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
        new_base_name = base_name  # ファイル名の変更がない場合は元のファイル名を使用
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

def process_audio_files(input_files, output_dir, target_base_dir, sources):
    ensure_directory_exists(output_dir)
    try:
        for input_file in input_files:
            file_path = os.path.join(output_dir, input_file.name)
            with open(file_path, 'wb') as f:
                f.write(input_file.getbuffer())

            if input_file.name.endswith(('.wav', '.mp3')):
                try:
                    audio_data, sample_rate = ap.load_audio_file(file_path)
                    ap.process_audio_file(file_path, sources, 'umxhq', 'cpu', output_dir)
                except Exception as e:
                    st.error(f"Error processing audio file {file_path}: {e}")

        rename_and_move_files(output_dir, target_base_dir)
        return "すべてのファイルの処理と移動が完了しました！"
    except Exception as e:
        st.error(f"処理中にエラーが発生しました: {e}")
    return None

def move_files_to_target(output_dir, target_dir):
    try:
        for file_name in os.listdir(output_dir):
            shutil.move(os.path.join(output_dir, file_name), os.path.join(target_dir, file_name))
        return f"ファイルが {output_dir} から {target_dir} に移動されました！"
    except Exception as e:
        return f"ファイル移動中にエラーが発生しました: {e}"

def main():
    st.title("Tokoroten Audio and Document Processing")

    # アプリケーションのルートディレクトリに `output` フォルダを自動生成
    root_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(root_dir, "output")
    ensure_directory_exists(output_dir)
    target_base_dir = output_dir

    st.write(f"出力フォルダ: {output_dir}")
    st.write(f"目的のベースフォルダ: {target_base_dir}")

    input_files = st.file_uploader("入力ファイルを選択してください", accept_multiple_files=True, type=['wav', 'mp3', 'pdf'])

    sources = []
    if st.checkbox('vocals'):
        sources.append('vocals')
    if st.checkbox('drums'):
        sources.append('drums')
    if st.checkbox('bass'):
        sources.append('bass')
    if st.checkbox('other'):
        sources.append('other')

    if st.button("Run") and input_files:
        result = process_audio_files(input_files, output_dir, target_base_dir, sources)
        if result:
            st.success(result)

            # ファイルを移動するためのターゲットディレクトリを選択
            target_dir = st.text_input("ファイルを移動するターゲットディレクトリを入力してください")
            if target_dir and st.button("Move Files"):
                move_result = move_files_to_target(output_dir, target_dir)
                if "エラー" in move_result:
                    st.error(move_result)
                else:
                    st.success(move_result)

if __name__ == '__main__':
    main()

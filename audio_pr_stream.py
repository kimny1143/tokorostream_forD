import os
import sys
import logging
import torch
import torch.hub
import soundfile as sf
import numpy as np
import openunmix
import librosa
import audioread
import scipy.signal
from madmom.features.beats import RNNBeatProcessor, DBNBeatTrackingProcessor


logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def convert_mp3_to_wav(input_mp3, output_wav):
    try:
        with audioread.audio_open(input_mp3) as source:
            data = []
            for buffer in source.read_data():
                data.append(np.frombuffer(buffer, dtype='<i2'))  # Adjust dtype based on source format
            audio_data = np.concatenate(data)

            # Reshape the data according to the number of channels
            audio_data = audio_data.reshape(-1, source.channels)

            sf.write(output_wav, audio_data, source.samplerate, format='WAV', subtype='PCM_16')
        logging.info(f"Converted MP3 to WAV: {input_mp3} -> {output_wav}")
    except Exception as e:
        logging.error(f"Error during MP3 to WAV conversion: {e}")
        raise

def resample_audio(input_file, target_sr=44100):
    data, original_sr = sf.read(input_file, always_2d=True)
    if original_sr != target_sr:
        # リサンプリング
        if data.shape[1] == 1:  # モノラル
            resampled_data = librosa.resample(data[:, 0], orig_sr=original_sr, target_sr=target_sr)
        else:  # ステレオ
            resampled_data_stereo = [librosa.resample(data[:, ch], orig_sr=original_sr, target_sr=target_sr) for ch in range(data.shape[1])]
            resampled_data = np.stack(resampled_data_stereo, axis=-1)

        return resampled_data, target_sr
    else:
        return data, original_sr


def load_audio_file(uploaded_file):
    try:
        logging.info(f"Loading audio file")

        # ファイルの内容をメモリに読み込む
        file_content = uploaded_file.read()

        # ファイルの形式に応じて処理
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension == "mp3":
            # MP3ファイルの場合、一時的にWAVに変換
            temp_wav = convert_mp3_to_wav(file_content)
            audio_data, sample_rate = resample_audio(temp_wav)
        else:
            # WAVファイルの場合、直接読み込む
            audio_data, sample_rate = resample_audio(file_content)

        # ステレオチェックと変換
        if audio_data.ndim == 1:  # モノラルの場合
            audio_data = np.stack([audio_data, audio_data])

        return audio_data, sample_rate

    except Exception as e:
        logging.error(f"Error loading audio file: {e}")
        return None, None
 

# Code for adding tempo detection and click track generation to the audio_processing.py file

def detect_tempo(file_path):
    """
    Detect the tempo of the audio file using Madmom.

    Parameters:
    file_path (str): Path to the audio file.

    Returns:
    float: Detected tempo in beats per minute (BPM).
    """
    try:
        logging.info(f"Detecting tempo for file: {file_path}")
        proc = DBNBeatTrackingProcessor(fps=100)
        act = RNNBeatProcessor()(file_path)
        beats = proc(act)

        # Calculate the BPM
        if len(beats) > 1:
            intervals = np.diff(beats)
            tempo = 60.0 / np.mean(intervals)
        else:
            tempo = 0.0

        logging.info(f"Detected tempo: {tempo} BPM")
        return tempo
    except Exception as e:
        logging.error(f"Error detecting tempo for file {file_path}: {e}")
        return None
    
# Revised code for generating a click track with an audible click sound at each beat


def generate_click_track_with_sample(sample_path, file_path, output_dir, sample_rate=44100):
    # スクリプトのディレクトリを基準にデフォルトクリックファイルのパスを構築
    base_path = os.path.dirname(os.path.abspath(__file__))
    default_sample_path = os.path.join(base_path, 'default_click.wav')

    # デフォルトのクリックファイルの存在チェック
    if not os.path.exists(default_sample_path):
        print("Default click file not found:", default_sample_path)
        return None

    # サンプルパスが指定されていない場合はデフォルトを使用
    if not sample_path:
        sample_path = default_sample_path

    # 以下、クリックトラックの生成処理...

# Example usage in process_audio_file function:

def process_audio_file_with_click_track(file_path, sources, model, device, output_dir, click_sample_path):
    try:
        audio_data, sample_rate = load_audio_file(file_path)
        if audio_data is None:
            raise Exception(f"Error loading audio file {file_path}")
        
        audio_data = audio_data.T  # transpose the audio data
        audio_tensor = torch.from_numpy(audio_data).float().to(device)  # convert to Float here
        audio_tensor = audio_tensor[None, ...]  # add batch dimension
        separator = torch.hub.load('sigsep/open-unmix-pytorch', model, device=device)
        estimates = separator(audio_tensor)  # no need to convert to Double here

        source_names = ['vocals', 'drums', 'bass', 'other']
        for i, source_name in enumerate(source_names):
            if source_name in sources:
                source_audio = estimates[0, i, :, :].detach().cpu().numpy()  # convert to numpy
                output_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_{source_name}.wav"
                output_path = os.path.join(output_dir, output_filename)
                sf.write(output_path, source_audio.T, sample_rate)

        # クリックトラックの生成と保存
        click_track_file = generate_click_track_with_sample(click_sample_path, file_path, output_dir, sample_rate)
        if click_track_file:
            logging.info(f"Click track saved as {click_track_file}")
    except Exception as e:
        error_message = f"Error processing file {file_path}: {e}"
        logging.error(error_message)
        raise Exception(error_message)  # これにより、Streamlit GUI にもエラーが表示されます。

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
import tempfile
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
            audio_data = audio_data.reshape(-1, source.channels)
            sf.write(output_wav, audio_data, source.samplerate, format='WAV', subtype='PCM_16')
        logging.info(f"Converted MP3 to WAV: {input_mp3} -> {output_wav}")
    except Exception as e:
        logging.error(f"Error during MP3 to WAV conversion: {e}")
        raise

def resample_audio(input_file, target_sr=44100):
    data, original_sr = sf.read(input_file, always_2d=True)
    if original_sr != target_sr:
        if data.shape[1] == 1:
            resampled_data = librosa.resample(data[:, 0], orig_sr=original_sr, target_sr=target_sr)
        else:
            resampled_data_stereo = [librosa.resample(data[:, ch], orig_sr=original_sr, target_sr=target_sr) for ch in range(data.shape[1])]
            resampled_data = np.stack(resampled_data_stereo, axis=-1)
        return resampled_data, target_sr
    else:
        return data, original_sr
    

def load_audio_file(file_path):
    try:
        logging.info(f"Loading audio file {file_path}")
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".mp3":
            temp_wav = tempfile.mktemp(suffix='.wav')
            convert_mp3_to_wav(file_path, temp_wav)
            audio_data, sample_rate = resample_audio(temp_wav)
            os.remove(temp_wav)
        else:
            audio_data, sample_rate = resample_audio(file_path)
        if audio_data.ndim == 1:
            audio_data = np.stack([audio_data, audio_data], axis=1)
        return audio_data, sample_rate
    except Exception as e:
        logging.error(f"Error loading audio file: {e}")
        raise

def process_audio_file(file_path, sources, model, device, output_dir):
    try:
        audio_data, sample_rate = load_audio_file(file_path)
        if audio_data is None:
            raise Exception(f"Error loading audio file {file_path}")
        
        # 楽曲番号を取得し、必要に応じて改名
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        ext = os.path.splitext(file_path)[1]

        # 先頭の「0」を取り除く
        if base_name.startswith('0'):
            base_name = base_name.lstrip('0')

        # 「X」がまだなければ、楽曲番号の直後に追加
        if 'X' not in base_name:
            base_name += 'X'


        audio_data = audio_data.T  # transpose the audio data
        audio_tensor = torch.from_numpy(audio_data).float().to(device)  # convert to Float here
        audio_tensor = audio_tensor[None, ...]  # add batch dimension
        separator = torch.hub.load('sigsep/open-unmix-pytorch', model, device=device)
        estimates = separator(audio_tensor)  # no need to convert to Double here

        for i, source_name in enumerate(['vocals', 'drums', 'bass', 'other']):
            if source_name in sources:
                source_audio = estimates[0, i, :].detach().cpu().numpy()  # convert to numpy
                output_filename = f"{base_name}_{source_name}{ext}"
                output_path = os.path.join(output_dir, output_filename)
                sf.write(output_path, source_audio.T, sample_rate)
    except Exception as e:
        error_message = f"Error processing file {file_path}: {e}"
        logging.error(error_message)
        raise Exception(error_message)  # Report the error through Streamlit GUI

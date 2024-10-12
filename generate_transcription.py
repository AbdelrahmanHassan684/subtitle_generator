# Importing necessary libraries to perform the task
from pydub import AudioSegment
import os
from concurrent.futures import ThreadPoolExecutor
from ratelimit import limits, sleep_and_retry
from open_ai_utils import convert_audio_text, get_openai_response

FILE_NAME = '53.mp3' # Change this to the name of your audio file



CALLS = 50
PERIOD = 60
TIME_FOR_EACH_CHUNK = 10 * 1000  # TIMES 1000 because pydub works in milliseconds
# Convert chunk to text
LANGUAGE = 'ar'
@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def process_chunk(i, chunk):
    """
    Processes an individual chunk of audio by exporting it, converting to text, and removing the file.
    
    Args:
    i (int): The index of the chunk.
    chunk (AudioSegment): The audio chunk to be processed.
    
    Returns:
    tuple: A tuple containing the index of the chunk and the transcribed text.
    """
    # Export chunk to WAV format
    chunk.export(f'chunk{i}.wav', format='wav')

    # Assuming convert_audio_text is a function that converts audio to text
    text = convert_audio_text(f'chunk{i}.wav', language=LANGUAGE)
    
    # Remove the temporary chunk file
    os.remove(f'chunk{i}.wav')

    # Return the chunk index and associated text
    return i, text

def transcribe_audio(file_path):
    """
    Transcribes the given audio file into text by splitting it into chunks and processing them in parallel.
    
    Args:
    file_path (str): The path of the audio file to be transcribed.
    
    Returns:
    dict: A dictionary mapping each chunk index to its transcribed text.
    """
    # Load the audio file
    sound = AudioSegment.from_mp3(file_path)

    # Split audio into chunks
    chunks = [sound[i:i + TIME_FOR_EACH_CHUNK] for i in range(0, len(sound), TIME_FOR_EACH_CHUNK)]

    # Dictionary to store the text for each timestamp
    text_time_stamp = {}

    # Using ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        # Submit tasks to process audio chunks
        futures = [executor.submit(process_chunk, i, chunk) for i, chunk in enumerate(chunks)]
        
        # Record results in the text_time_stamp dictionary
        for future in futures:
            i, text = future.result()
            text_time_stamp[i] = text

    # Return the dictionary with timestamps and transcribed text
    return text_time_stamp

text_time_stamp = transcribe_audio(FILE_NAME)

# Converting the transcribed text dictionary to a string
dict_message = str(text_time_stamp)

# Assuming get_openai_response is a function that sends a request to OpenAI and gets a response
response = get_openai_response(dict_message)
print(response)

# Extracting the dictionary part from the response
dict_start = response.find('{')
dict_end = response.find('}')
response = response[dict_start:dict_end+1]

# Cleaning up the response string by removing unnecessary characters
response = response.replace('\n', '')  # Removing new lines
response = response.replace('  ', '')  # Removing extra spaces
response = response.replace('\\n', '') # Removing escaped new lines
response = response.replace('\\', '')  # Removing backslashes
response = response.replace('\'', '')  # Removing single quotes

# Parsing the cleaned response string to reconstruct the dictionary
response_2 = {}
k = 0  # Index for the new dictionary
for i in range(0, len(response)):
    if response[i].isdigit() and response[i+1] == ':':
        # Finding the next number followed by a colon to get the text in between
        for j in range(i+2, len(response)):
            if response[j].isdigit() and response[j+1] == ':':
                response_2[k] = response[i+2:j-1].strip()  # Adding the text to the new dictionary
                k += 1  # Incrementing the index
                break

from datetime import timedelta

def format_srt_time(milliseconds):
    """
    Converts milliseconds to SRT (SubRip Text) time format.

    Args:
    milliseconds (int): Time in milliseconds.

    Returns:
    str: Time in SRT format (HH:MM:SS,mmm).
    """
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(milliseconds):03}'

def create_srt_file(text_time_stamp, file_name='transcription2.srt'):
    """
    Creates an SRT file from a dictionary of timestamps and text.

    Args:
    text_time_stamp (dict): Dictionary with timestamps (as keys) and transcribed text (as values).
    file_name (str): Name of the file to be created. Defaults to 'transcription2.srt'.
    """
    with open(file_name, 'w') as file:
        for i, text in text_time_stamp.items():
            # Calculating the start and end times for each subtitle
            start_time = i * TIME_FOR_EACH_CHUNK  # Assuming TWO_SECONDS_MS is the time for each chunk
            end_time = (i + 1) * TIME_FOR_EACH_CHUNK

            # Formatting times for SRT standard
            start_time_srt = format_srt_time(start_time)
            end_time_srt = format_srt_time(end_time)

            # Writing the subtitle number, time range, and text to the file
            file.write(f'{i+1}\n')  # Subtitle number
            file.write(f'{start_time_srt} --> {end_time_srt}\n')  # Time range
            file.write(f'{text}\n\n')  # Subtitle text

# After your existing code to generate text_time_stamp dictionary
create_srt_file(response_2)
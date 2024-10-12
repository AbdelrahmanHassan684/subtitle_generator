from openai import OpenAI
import re
import uuid

client = OpenAI()

# load the assistant_id and thread_id from file if exists
try:
    with open('assistant_id.txt', 'r') as f:
        assistant_id = f.readline().strip()
        thread_id = f.readline().strip()
    my_assistant = client.beta.assistants.retrieve(assistant_id)
    my_thread = client.beta.threads.retrieve(thread_id)
except:

    # Step 1: Create an Assistant

    instructions = "You are a professional translator from Egyptian Arabic to English. The user will give you phrases from an Egyptian series. The phrases are transcriped using AI so it may contain misspelling or hallucination. Consider the context. Translate any phrase to English directly without asking any questions."
    my_assistant = client.beta.assistants.create(model='gpt-3.5-turbo', instructions=instructions)

    my_thread = client.beta.threads.create()

    assistant_id, thread_id = my_assistant.id, my_thread.id

    # write assistant_id and thread_id to file
    with open('assistant_id.txt', 'w') as f:
        f.write(assistant_id)
        f.write('\n')
        f.write(thread_id)

def get_openai_response(messages):
    # Step 3: Add a Message to a Thread
    my_thread_message = client.beta.threads.messages.create(
    thread_id=my_thread.id,
    role="user",
    content=messages,
    )

    # Step 4: Run the Assistant
    my_run = client.beta.threads.runs.create(
    thread_id=my_thread.id,
    assistant_id=my_assistant.id,
    )

    # Step 5: Periodically retrieve the Run to check on its status to see if it has moved to completed
    while my_run.status != "completed":
        keep_retrieving_run = client.beta.threads.runs.retrieve(
            thread_id=my_thread.id,
            run_id=my_run.id
        )

        if keep_retrieving_run.status == "completed":
            print("\n")
            break

    # Step 6: Retrieve the Messages added by the Assistant to the Thread
    all_messages = client.beta.threads.messages.list(
    thread_id=my_thread.id
    )
    return all_messages.data[0].content[0].text.value


def convert_audio_text(audio_path, language='', prompt=''):
    # use OPENAI API to convert audio to text
    file = open(audio_path, "rb")
    print('file', file)
    transcript = client.audio.transcriptions.create(model="whisper-1", file=file, language=language, prompt=prompt)
    return transcript

def convert_text_audio(text):
    # use OPENAI API to convert text to audio
    response = client.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input=text,
    )

    file_name = str(uuid.uuid4()) + ".mp3"
    response.stream_to_file(file_name)
    return file_name

    
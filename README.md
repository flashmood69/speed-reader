# Speed Reader App
![ss](https://github.com/flashmood69/speed-reader/blob/main/docs/speed-reader.png)

## Description
This application helps users practice speed reading. It can load text from files or generate text using an AI model based on user prompts. It features a timer, WPM calculation, and text highlighting capabilities.

## Features

### File Loading
- Users can load text files (`.txt`) into the application. The content is displayed for reading practice.

### Text Generation (AI)
- Users can enter a prompt to generate text using a local Large Language Model (LLM).
- The generated text is displayed in the reading area.

You can download a model based on Google's Gemma architecture at
[huggingface.co/lmstudio-community/gemma-3-1B-it-qat-GGUF/resolve/main/gemma-3-1B-it-QAT-Q4_0.gguf](https://huggingface.co/lmstudio-community/gemma-3-1B-it-qat-GGUF/resolve/main/gemma-3-1B-it-QAT-Q4_0.gguf).

Gemma is provided under and subject to the Gemma Terms of Use found at [ai.google.dev/gemma/terms](https://ai.google.dev/gemma/terms).

The default path for the model is `resources/models/tiny.gguf`.

### Highlighting
- Words can be highlighted sequentially based on a selected Words Per Minute (WPM) rate.
- Highlighting color and language for stop-word differentiation can be selected.

### Reading Timer
- Tracks reading time with start, pause, stop, and reset controls.
- Calculates and displays WPM upon stopping the timer.

### Sound
- Optional background sound (e.g., white noise) can be played during reading sessions.

## Installation

1.  **Install dependencies:**
    It's recommended to create a `requirements.txt` file listing all necessary packages. You can then install them using:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Installing `llama-cpp-python`:**
    This library can sometimes require specific installation steps depending on your system configuration (CPU/GPU, OS). If the standard `pip install llama-cpp-python` or installation via `requirements.txt` fails, try these alternatives:

    *   **For CPU-only (using pre-built wheels):**
        ```bash
        pip install llama-cpp-python --prefer-binary --force-reinstall --no-cache-dir --extra-index-url=https://abetlen.github.io/llama-cpp-python/whl/cpu
        ```
    *   **Building from source (requires C++ compiler/CMake):**
        ```bash
        pip install llama-cpp-python --force-reinstall --no-cache-dir --config-settings=cmake.args="-DCMAKE_BUILD_TYPE=Release"
        ```

3.  **Download NLTK data:**
    The application requires NLTK's stopwords. It attempts to download them automatically to the `resources/corpora/stopwords` directory upon first run if they are not found.

4.  **Configuration:**
    Create a `config.json` file in the root directory, specifying the path to your LLM model file (`.gguf`), sound file, WPM options, etc.

# 🌐 Language Translation Tool

**CodeAlpha — Artificial Intelligence Internship, Task 1**

A modern desktop application built with Python and CustomTkinter that translates text between 100+ languages using the Google Translate service.

## Features
- Simple user interface to enter text and choose **source** and **target** languages
- **Auto Detect** for the source language
- **Automatic fallback**: if Google Translate refuses a request (rate limit / network issue), the app retries and then switches to the free MyMemory Translation API
- Sends the text to the translation API and displays the result clearly
- **⇄ Swap** source and target languages
- **📋 Copy** the translation to the clipboard
- **🔊 Text-to-Speech** — listen to the translation (via gTTS)
- Modern UI with **dark / light mode** toggle
- Character counter (5000 max) and non-blocking UI (API calls run in a background thread)
- Shortcut: `Ctrl + Enter` to translate

## Tech Stack
- Python 3
- CustomTkinter (modern GUI)
- [deep-translator](https://pypi.org/project/deep-translator/) — Google Translate API wrapper
- [gTTS](https://pypi.org/project/gTTS/) — Google Text-to-Speech

## How to Run
```bash
git clone https://github.com/<your-username>/CodeAlpha_LanguageTranslator.git
cd CodeAlpha_LanguageTranslator
pip install -r requirements.txt
python app.py
```
> An internet connection is required for translation and text-to-speech.

## How It Works
1. The user enters text and selects the languages.
2. The app maps the language names to ISO codes (e.g. `Arabic → ar`).
3. `GoogleTranslator(source, target).translate(text)` sends the request to the API.
4. The translated response is shown in the output box, ready to copy or listen to.

## Screenshot
_Add a screenshot of the app here._

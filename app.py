"""
Language Translation Tool - CodeAlpha AI Internship (Task 1)

A modern desktop app (CustomTkinter) where the user types text, picks a source
and target language, and gets the translation from the Google Translate API
(via deep-translator), with an automatic fallback to the free MyMemory API.
Extras: swap languages, copy to clipboard, text-to-speech, dark/light mode.
"""

import os
import sys
import time
import subprocess
import tempfile
import threading

import requests
import customtkinter as ctk
from deep_translator import GoogleTranslator

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# ------------------------------------------------------------------ settings
MAX_CHARS = 5000
AUTO_DETECT = "Auto Detect"
ACCENT = "#6C5CE7"
ACCENT_HOVER = "#5A4BD1"
FONT = "Segoe UI"
GREEN = ("#00996f", "#55efc4")   # (light mode, dark mode)
YELLOW = ("#b37400", "#fdcb6e")
RED = ("#d63031", "#ff6b6b")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# {"english": "en", "arabic": "ar", ...}  (static list, no internet needed)
_LANGS = GoogleTranslator().get_supported_languages(as_dict=True)
NAME_TO_CODE = {name.title(): code for name, code in _LANGS.items()}
LANGUAGE_NAMES = sorted(NAME_TO_CODE.keys())

# ------------------------------------------------------------ translation API
MYMEMORY_URL = "https://api.mymemory.translated.net/get"
MYMEMORY_CHUNK = 450  # MyMemory free API accepts ~500 characters per request


def _chunks(text: str, size: int):
    """Split text into pieces of at most `size` characters, on word boundaries."""
    piece = ""
    for w in text.split(" "):
        if piece and len(piece) + len(w) + 1 > size:
            yield piece
            piece = w
        else:
            piece = f"{piece} {w}" if piece else w
    if piece:
        yield piece


def translate_mymemory(text: str, source: str, target: str) -> str:
    """Backup translation API (MyMemory) - free, no API key needed."""
    src = "autodetect" if source == "auto" else source
    results = []
    for piece in _chunks(text, MYMEMORY_CHUNK):
        resp = requests.get(MYMEMORY_URL,
                            params={"q": piece, "langpair": f"{src}|{target}"},
                            timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if int(data.get("responseStatus", 200)) != 200:
            raise RuntimeError(data.get("responseDetails", "MyMemory error"))
        results.append(data["responseData"]["translatedText"])
    return " ".join(results)


def translate_text(text: str, source: str, target: str):
    """
    Try Google Translate first (retrying once), then fall back to MyMemory if
    Google refuses the request (e.g. 'too many requests').
    Returns (translated_text, service_name).
    """
    last_error = None
    for _ in range(2):
        try:
            return GoogleTranslator(source=source, target=target).translate(text), "Google"
        except Exception as exc:
            last_error = exc
            time.sleep(1.5)
    try:
        return translate_mymemory(text, source, target), "MyMemory"
    except Exception as exc:
        raise RuntimeError(f"Google: {last_error}\n\nMyMemory: {exc}") from exc


# ---------------------------------------------------------------------- GUI
class TranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Language Translator")
        self.geometry("1000x620")
        self.minsize(780, 520)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_language_bar()
        self._build_panels()
        self._build_status_bar()

        self.bind("<Control-Return>", lambda e: self.translate())

    # ---------- layout ----------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="🌐  Language Translator",
                     font=(FONT, 28, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Translate text between 100+ languages instantly",
                     font=(FONT, 14), text_color="gray60").grid(row=1, column=0, sticky="w")

        self.mode_switch = ctk.CTkSwitch(header, text="Dark mode",
                                         command=self.toggle_mode,
                                         progress_color=ACCENT)
        self.mode_switch.select()
        self.mode_switch.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_language_bar(self):
        bar = ctk.CTkFrame(self, corner_radius=16)
        bar.grid(row=1, column=0, sticky="ew", padx=30, pady=10)
        bar.grid_columnconfigure((0, 2), weight=1)

        self.source_box = ctk.CTkComboBox(bar, values=[AUTO_DETECT] + LANGUAGE_NAMES,
                                          height=40, corner_radius=10,
                                          font=(FONT, 14), dropdown_font=(FONT, 13),
                                          button_color=ACCENT, button_hover_color=ACCENT_HOVER,
                                          border_color=ACCENT)
        self.source_box.set(AUTO_DETECT)
        self.source_box.grid(row=0, column=0, sticky="ew", padx=(15, 10), pady=15)

        ctk.CTkButton(bar, text="⇄", width=50, height=40, corner_radius=20,
                      font=(FONT, 20, "bold"), fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self.swap_languages).grid(row=0, column=1, pady=15)

        self.target_box = ctk.CTkComboBox(bar, values=LANGUAGE_NAMES,
                                          height=40, corner_radius=10,
                                          font=(FONT, 14), dropdown_font=(FONT, 13),
                                          button_color=ACCENT, button_hover_color=ACCENT_HOVER,
                                          border_color=ACCENT)
        self.target_box.set("Arabic")
        self.target_box.grid(row=0, column=2, sticky="ew", padx=(10, 15), pady=15)

    def _build_panels(self):
        panels = ctk.CTkFrame(self, fg_color="transparent")
        panels.grid(row=2, column=0, sticky="nsew", padx=30, pady=10)
        panels.grid_columnconfigure((0, 1), weight=1, uniform="p")
        panels.grid_rowconfigure(0, weight=1)

        # --- input card ---
        left = ctk.CTkFrame(panels, corner_radius=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text="Enter text", font=(FONT, 15, "bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(14, 4))
        self.input_text = ctk.CTkTextbox(left, font=(FONT, 16), wrap="word",
                                         corner_radius=12, border_width=0)
        self.input_text.grid(row=1, column=0, sticky="nsew", padx=14)
        self.input_text.bind("<KeyRelease>", self.update_counter)

        left_bottom = ctk.CTkFrame(left, fg_color="transparent")
        left_bottom.grid(row=2, column=0, sticky="ew", padx=14, pady=12)
        left_bottom.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(left_bottom, text="Clear", width=80, height=36,
                      fg_color="transparent", border_width=1, border_color="gray50",
                      text_color=("gray20", "gray85"), hover_color=("gray85", "gray25"),
                      command=self.clear).grid(row=0, column=0)
        self.counter = ctk.CTkLabel(left_bottom, text=f"0 / {MAX_CHARS}",
                                    text_color="gray60", font=(FONT, 12))
        self.counter.grid(row=0, column=1, sticky="e", padx=10)
        self.translate_btn = ctk.CTkButton(left_bottom, text="Translate  →", height=36,
                                           width=130, font=(FONT, 14, "bold"),
                                           fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                           command=self.translate)
        self.translate_btn.grid(row=0, column=2)

        # --- output card ---
        right = ctk.CTkFrame(panels, corner_radius=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text="Translation", font=(FONT, 15, "bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(14, 4))
        self.output_text = ctk.CTkTextbox(right, font=(FONT, 16), wrap="word",
                                          corner_radius=12, border_width=0,
                                          state="disabled")
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=14)

        right_bottom = ctk.CTkFrame(right, fg_color="transparent")
        right_bottom.grid(row=2, column=0, sticky="ew", padx=14, pady=12)
        right_bottom.grid_columnconfigure(0, weight=1)

        self.speak_btn = ctk.CTkButton(right_bottom, text="🔊  Listen", width=110, height=36,
                                       fg_color="transparent", border_width=1,
                                       border_color=ACCENT, text_color=("gray20", "gray85"),
                                       hover_color=("gray85", "gray25"), command=self.speak)
        self.speak_btn.grid(row=0, column=1, padx=(0, 8))
        if not TTS_AVAILABLE:
            self.speak_btn.configure(state="disabled")

        ctk.CTkButton(right_bottom, text="📋  Copy", width=110, height=36,
                      fg_color="transparent", border_width=1, border_color=ACCENT,
                      text_color=("gray20", "gray85"), hover_color=("gray85", "gray25"),
                      command=self.copy_output).grid(row=0, column=2)

    def _build_status_bar(self):
        self.status = ctk.CTkLabel(self, text="Ready  •  Ctrl+Enter to translate",
                                   font=(FONT, 12), text_color="gray60", anchor="w")
        self.status.grid(row=3, column=0, sticky="ew", padx=32, pady=(0, 12))

    # ---------- helpers ----------
    def set_status(self, text, color=("gray40", "gray60")):
        self.status.configure(text=text, text_color=color)

    def get_input(self) -> str:
        return self.input_text.get("1.0", "end").strip()

    def get_output(self) -> str:
        return self.output_text.get("1.0", "end").strip()

    def set_output(self, text: str):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")

    def update_counter(self, _event=None):
        n = len(self.get_input())
        self.counter.configure(text=f"{n} / {MAX_CHARS}",
                               text_color=RED if n > MAX_CHARS else "gray60")

    @staticmethod
    def lang_code(name: str):
        """Return the language code for a (possibly typed) language name."""
        return NAME_TO_CODE.get(name.strip().title())

    # ---------- actions ----------
    def toggle_mode(self):
        ctk.set_appearance_mode("dark" if self.mode_switch.get() else "light")

    def swap_languages(self):
        src, tgt = self.source_box.get(), self.target_box.get()
        if src == AUTO_DETECT:
            self.set_status("Pick a source language first (not Auto Detect) to swap.", YELLOW)
            return
        self.source_box.set(tgt)
        self.target_box.set(src)
        out = self.get_output()
        if out:
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", out)
            self.set_output("")
            self.update_counter()

    def translate(self):
        text = self.get_input()
        if not text:
            self.set_status("Please enter some text to translate.", YELLOW)
            return
        if len(text) > MAX_CHARS:
            self.set_status(f"Text must be under {MAX_CHARS} characters.", RED)
            return

        src_name = self.source_box.get()
        source = "auto" if src_name == AUTO_DETECT else self.lang_code(src_name)
        target = self.lang_code(self.target_box.get())
        if source is None or target is None:
            self.set_status("Please choose a valid language from the list.", RED)
            return

        self.translate_btn.configure(state="disabled", text="Translating...")
        self.set_status("Translating...")

        # run the API call in a background thread so the window doesn't freeze
        def worker():
            try:
                result, service = translate_text(text, source, target)
                self.after(0, self.on_translated, result, service, None)
            except Exception as exc:
                self.after(0, self.on_translated, None, None, exc)

        threading.Thread(target=worker, daemon=True).start()

    def on_translated(self, result, service, error):
        self.translate_btn.configure(state="normal", text="Translate  →")
        if error:
            self.set_status("Translation failed. Check your internet and try again in a minute.",
                            RED)
            print("Translation error:", error)
            return
        self.set_output(result or "")
        self.set_status(f"✓ Translated to {self.target_box.get()}  (via {service})", GREEN)

    def copy_output(self):
        out = self.get_output()
        if not out:
            self.set_status("Nothing to copy yet.", YELLOW)
            return
        self.clipboard_clear()
        self.clipboard_append(out)
        self.set_status("✓ Translation copied to clipboard", GREEN)

    def speak(self):
        out = self.get_output()
        if not out:
            self.set_status("Translate something first.", YELLOW)
            return
        lang = self.lang_code(self.target_box.get())
        self.set_status("Generating audio...")

        def worker():
            try:
                path = os.path.join(tempfile.gettempdir(), "translation_tts.mp3")
                gTTS(text=out, lang=lang).save(path)
                self.after(0, self.play_audio, path, None)
            except Exception as exc:
                self.after(0, self.play_audio, None, exc)

        threading.Thread(target=worker, daemon=True).start()

    def play_audio(self, path, error):
        if error:
            self.set_status("Text-to-speech isn't available for this language right now.",
                            RED)
            return
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        self.set_status("🔊 Playing audio")

    def clear(self):
        self.input_text.delete("1.0", "end")
        self.set_output("")
        self.update_counter()
        self.set_status("Ready  •  Ctrl+Enter to translate")


if __name__ == "__main__":
    TranslatorApp().mainloop()

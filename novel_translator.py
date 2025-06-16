import re
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
from novel_analyzer import NovelAnalyzer
from translator import NovelTranslator
from dotenv import load_dotenv
import json5 # json yerine json5 kullanıldı

class NovelTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Roman Çeviri Asistanı")
        self.root.geometry("1200x800")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize variables and lists first
        self.available_languages = {
            "English": "en",
            "Türkçe": "tr",
            "Deutsch": "de",
            "Français": "fr",
            "Español": "es",
            "Italiano": "it",
            "Português": "pt",
            "Русский": "ru",
            "日本語": "ja",
            "中文": "zh",
            "한국어": "ko",
            "العربية": "ar",
            "हिन्दी": "hi"
        }

        self.available_countries = {
            "United States (English)": "US",
            "United Kingdom (English)": "UK",
            "Canada (English)": "CA",
            "Australia (English)": "AU",
            "India (English)": "IN",
            "Ireland (English)": "IE",
            "South Africa (English)": "ZA",
            "Türkiye (Türkçe)": "TR",
            "Germany (Deutsch)": "DE",
            "France (Français)": "FR",
            "Spain (Español)": "ES",
            "Mexico (Español)": "MX",
            "Argentina (Español)": "AR",
            "Italy (Italiano)": "IT",
            "Portugal (Português)": "PT",
            "Brazil (Português)": "BR",
            "Russia (Русский)": "RU",
            "Japan (日本語)": "JP",
            "China (中文)": "CN",
            "South Korea (한국어)": "KR",
            "Egypt (العربية)": "EG",
            "Saudi Arabia (العربية)": "SA",
            "India (हिन्दी)": "IN"
        }
        
        self.available_genres = [
            "Roman",
            "Kara Roman",
            "Polisiye",
            "Bilim Kurgu",
            "Fantastik",
            "Tarihi",
            "Macera",
            "Romantik",
            "Gerilim",
            "Korku",
            "Biyografi",
            "Otobiyografi",
            "Deneme",
            "Öykü",
            "Şiir",
            "Tiyatro",
            "Çocuk",
            "Gençlik",
            "Mizah",
            "Felsefe",
            "Bilim",
            "Distopik",
            "Ütopik",
            "Psikolojik",
            "Sosyolojik",
            "Folklorik",
            "Mitolojik",
            "Epik",
            "Lirik",
            "Didaktik",
            "Satirik",
            "Pastoral",
            "Dramatik",
            "Trajik",
            "Komedi",
            "Absürd",
            "Varoluşçu",
            "Postmodern",
            "Gotik",
            "Neo-Noir",
            "Cyberpunk",
            "Steampunk",
            "Alternatif Tarih",
            "Büyülü Gerçekçilik",
            "Akıcı Roman",
            "Deneysel",
            "Belgesel",
            "Anı",
            "Günlük",
            "Mektup"
        ]
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        
        # Initialize components
        self.analyzer = NovelAnalyzer()
        # Initialize translator with a default target country (e.g., "US")
        # API key is now handled internally by NovelTranslator based on AI_MODEL env var
        self.translator = NovelTranslator(target_country=os.getenv("TARGET_COUNTRY", "US")) 
        self.stop_event = threading.Event()
        self.novel_sections = [] # Initialize novel_sections here
        self.translated_sections = [] # Initialize translated_sections here
        self.back_translated_sections = [] # Initialize back_translated_sections here
        self.novel_analyzed = False # Track if novel has been analyzed
        self.selected_character_name = None
        self.characters = {} # Initialize characters dictionary
        self.cultural_context = {} # Initialize cultural context
        self.main_themes = {} # Initialize main themes
        self.setting_atmosphere = {} # Initialize setting and atmosphere
        self.original_detected_language_code = None # Initialize original_detected_language_code
        
        # Create Input and Analysis section
        input_analysis_frame = ttk.LabelFrame(self.main_frame, text="Input and Analysis", padding="5")
        input_analysis_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Create Input section
        self.create_input_section(input_analysis_frame, 0)
        
        # Create Analysis section
        self.create_analysis_section(input_analysis_frame, 1)
        
        # Create UI sections
        self.create_translation_section()
        # self.create_style_guide_section() # Removed style guide section
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Translation progress display
        self.progress_text = scrolledtext.ScrolledText(self.main_frame, height=5, state='disabled')
        self.progress_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar["variable"] = self.progress_var
        self.progress_bar["maximum"] = 100
        
    def create_input_section(self, frame, column):
        input_frame = ttk.LabelFrame(frame, text="Input", padding="5")
        input_frame.grid(row=0, column=column, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # File selection
        ttk.Button(input_frame, text="Select Novel File", command=self.load_novel).grid(row=0, column=0, padx=5, pady=5)
        self.file_path_var = tk.StringVar()
        ttk.Label(input_frame, textvariable=self.file_path_var).grid(row=0, column=1, padx=5, pady=5)
        
        # Novel details
        details_frame = ttk.Frame(input_frame)
        details_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Genre selection
        ttk.Label(details_frame, text="Genre:").grid(row=0, column=0, padx=5, pady=2)
        self.genre_var = tk.StringVar()
        genre_combo = ttk.Combobox(details_frame, textvariable=self.genre_var, 
                                 values=self.available_genres, state="readonly")
        genre_combo.grid(row=0, column=1, padx=5, pady=2)
        
        # Language selection
        ttk.Label(details_frame, text="Target Language:").grid(row=3, column=0, padx=5, pady=2)
        self.target_language_var = tk.StringVar(value="English")
        language_combo = ttk.Combobox(details_frame, textvariable=self.target_language_var, 
                                    values=list(self.available_languages.keys()), state="readonly")
        language_combo.grid(row=3, column=1, padx=5, pady=2)

        # Target Country selection
        ttk.Label(details_frame, text="Target Country:").grid(row=4, column=0, padx=5, pady=2)
        self.target_country_var = tk.StringVar(value="United States (English)") # Default to US
        country_combo = ttk.Combobox(details_frame, textvariable=self.target_country_var, 
                                     values=list(self.available_countries.keys()), state="readonly")
        country_combo.grid(row=4, column=1, padx=5, pady=2)
        
        # Add spinbox for retries
        ttk.Label(details_frame, text="Number of Retries:").grid(row=5, column=0, padx=5, pady=2)
        self.retries_var = tk.IntVar(value=3)
        retries_spinbox = ttk.Spinbox(details_frame, from_=1, to=10, textvariable=self.retries_var, width=5)
        retries_spinbox.grid(row=5, column=1, padx=5, pady=2)
        
    def create_analysis_section(self, frame, column):
        analysis_frame = ttk.LabelFrame(frame, text="Analysis", padding="5")
        analysis_frame.grid(row=0, column=column, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        analyze_button = ttk.Button(analysis_frame, text="Romanı Analiz Et", command=self.analyze_novel)
        analyze_button.grid(row=0, column=0, columnspan=3, pady=5, sticky="ew")

        novel_details_editor_button = ttk.Button(analysis_frame, text="Roman Detaylarını Düzenle", command=self.show_novel_details_editor)
        novel_details_editor_button.grid(row=1, column=0, pady=5, padx=2, sticky="ew")

        section_editor_button = ttk.Button(analysis_frame, text="Bölümleri Düzenle", command=self.show_section_editor)
        section_editor_button.grid(row=1, column=1, pady=5, padx=2, sticky="ew")

        character_editor_button = ttk.Button(analysis_frame, text="Karakterleri Düzenle", command=self.show_character_editor)
        character_editor_button.grid(row=1, column=2, pady=5, padx=2, sticky="ew")

        ttk.Label(analysis_frame, text="Analiz Özeti:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD, width=50, height=5)
        self.analysis_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
    def create_translation_section(self):
        translation_outer_frame = ttk.LabelFrame(self.main_frame, text="Translation and Verification", padding="5")
        translation_outer_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Use a PanedWindow for resizable text areas
        paned_window = ttk.PanedWindow(translation_outer_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Original Text Area
        original_text_frame = ttk.LabelFrame(paned_window, text="Original Text", padding="5")
        paned_window.add(original_text_frame, weight=1)
        self.original_text_display = scrolledtext.ScrolledText(original_text_frame, height=25, state='disabled', wrap=tk.WORD)
        self.original_text_display.pack(fill=tk.BOTH, expand=True)
        
        # Translated Text Area
        translated_text_frame = ttk.LabelFrame(paned_window, text="Translated Text", padding="5")
        paned_window.add(translated_text_frame, weight=1)
        self.translation_text = scrolledtext.ScrolledText(translated_text_frame, height=25, state='disabled', wrap=tk.WORD)
        self.translation_text.pack(fill=tk.BOTH, expand=True)
        
        # Back-Translation Text Area
        back_translation_text_frame = ttk.LabelFrame(paned_window, text="Back-Translation (for verification)", padding="5")
        paned_window.add(back_translation_text_frame, weight=1)
        self.back_translation_text = scrolledtext.ScrolledText(back_translation_text_frame, height=25, state='disabled', wrap=tk.WORD)
        self.back_translation_text.pack(fill=tk.BOTH, expand=True)
        
        # Translation buttons
        button_frame = ttk.Frame(translation_outer_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Edit Prompts", command=self.show_prompt_editor).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Translate", command=self.translate_novel).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Save Translation", command=self.save_translation).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Save Back-Translation", command=self.save_back_translation).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Save Style Guide", command=self.save_style_guide).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Import Style Guide", command=self.import_style_guide).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Stop Translation", command=self.stop_translation_process).pack(side=tk.LEFT, padx=5, pady=5)
        
    # Removed create_style_guide_section and update_style_guide_display methods
        
    def load_novel(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            
    def analyze_novel(self):
        if not self.file_path_var.get():
            messagebox.showerror("Error", "Please select a novel file first!")
            return
            
        try:
            genre = self.genre_var.get()
            # characters = self.characters_var.get() # Kaldırıldı ve tamamen kaldırılıyor
            
            if not genre:
                messagebox.showerror("Error", "Please select a genre!")
                return
                
            # Karakter girişi gerekliliği kaldırıldı, AI hallediyor
            # if not self.characters_var.get() and not self.char_file_path_var.get():
            #     messagebox.showerror("Hata", "Lütfen karakterleri dosya ile veya manuel olarak sağlayın!")
            #     return
                
            with open(self.file_path_var.get(), 'r', encoding='utf-8') as file:
                content = file.read()
                
            analysis_summary, self.novel_sections, self.cultural_context, self.main_themes, self.setting_atmosphere, error_message = self.analyzer.analyze(content, genre, "") # Karakter girişi artık AI'dan geliyor
            
            # Store character information
            self.characters = self.analyzer.get_characters()
            
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, analysis_summary)
            
            print(f"DEBUG: analyze_novel received error_message: {error_message}") # Hata mesajını konsola yazdır

            if error_message:
                messagebox.showerror("Analiz Hatası", f"Bir hata oluştu: {error_message}")

            # Store the detected original language
            self.original_detected_language_code = self.analyzer.get_detected_language()
            print(f"DEBUG: Detected original language: {self.original_detected_language_code}")

            if error_message:
                messagebox.showerror("Analiz Hatası", f"Bir hata oluştu: {error_message}")

            # Stil rehberini AI ile oluştur
            self._update_translation_progress("Stil Rehberi AI'ye soruluyor...\n")
            print("DEBUG: Calling generate_style_guide_with_ai from analyze_novel.")
            # Get selected target country code
            selected_country_name = self.target_country_var.get()
            target_country_code = self.available_countries.get(selected_country_name, "US") # Default to US if not found

            self.translator.generate_style_guide_with_ai(
                genre,
                self.characters,
                self.cultural_context,
                self.main_themes,
                self.setting_atmosphere,
                self.original_detected_language_code, # Kaynak dil
                self.available_languages[self.target_language_var.get()], # Hedef dil
                target_country_code, # Hedef ülke
                lambda msg: self._update_translation_progress(msg),
                max_retries=self.retries_var.get() # Arayüzden alınan tekrar sayısını ekle
            )
            print("DEBUG: generate_style_guide_with_ai call completed.")
            self._update_translation_progress("Stil Rehberi AI tarafından güncellendi.\n")

            self.status_var.set("Novel analysis complete. Ready for translation.")
            if not error_message:
                messagebox.showinfo("Analysis Complete", "Novel analysis complete. You can now proceed with translation.")
            
            self.novel_analyzed = True
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Analiz sırasında beklenmeyen bir hata oluştu: {str(e)}")
            self.status_var.set("Analysis failed.")
            
    def translate_novel(self):
        if not self.file_path_var.get():
            messagebox.showerror("Error", "Please select a novel file first!")
            return

        try:
            genre = self.genre_var.get()
            max_retries = self.retries_var.get()

            if not genre:
                messagebox.showerror("Error", "Please select a genre!")
                return

            with open(self.file_path_var.get(), 'r', encoding='utf-8') as file:
                content = file.read()

            self.status_var.set("Ready for translation.")

            # Clear previous translation and translated sections for a new translation
            self.translation_text.delete(1.0, tk.END)
            self.translated_sections = [] # Initialize as empty, will be populated during translation
            self.back_translated_sections = [] # Initialize back-translated sections as empty
            self.stop_event.clear()

            if not self.novel_sections:
                messagebox.showwarning("Translation Error", "No translatable sections found in the novel. Please check the input file.")
                self.status_var.set("Translation failed: No sections to translate.")
                return
            
            print(f"DEBUG: Before translation, self.novel_sections has {len(self.novel_sections)} sections.")

            # Get selected target country code
            selected_country_name = self.target_country_var.get()
            target_country_code = self.available_countries.get(selected_country_name, "US") # Default to US if not found

            # Update the translator's target_country
            self.translator.target_country = target_country_code
            
            # Start translation in a background thread
            threading.Thread(target=self._run_translation_in_background, args=(max_retries, target_country_code), daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def stop_translation_process(self):
        self.stop_event.set()
        self.status_var.set("Translation stopped.")
        messagebox.showinfo("Translation Stopped", "Translation process has been stopped.")

    def _run_translation_in_background(self, max_retries, target_country_code):
        try:
            total_sections = len(self.novel_sections)
            for current_section_index, section in enumerate(self.novel_sections):
                if self.stop_event.is_set():
                    break
                    
                original_text = section["text"]
                section_type = section["type"]
                
                # Only update progress text, status bar will be handled by _update_translation_progress
                self._update_translation_progress(f"Bölüm {current_section_index + 1}/{total_sections} ({section_type}) çevriliyor...\n", current_section_index + 1, total_sections)

                # Translate the section
                translation_result = self.translator.translate_section(
                    section,
                    self.genre_var.get(),
                    json5.dumps(self.characters), # Kullanıcının düzenlediği karakter bilgilerini kullan
                    json5.dumps(self.cultural_context),
                    json5.dumps(self.main_themes),
                    json5.dumps(self.setting_atmosphere),
                    self.original_detected_language_code, # Kaynak dil bilgisini ekle
                    self.available_languages[self.target_language_var.get()],
                    target_country_code, # Pass target_country_code here
                    lambda msg: self._update_translation_progress(msg, current_section_index + 1, total_sections), # Pass current section info
                    self.stop_event,
                    max_retries
                )
                
                # Debugging için döndürülen değerin tipini ve uzunluğunu kontrol et
                print(f"DEBUG: translate_section returned type: {type(translation_result)}, length: {len(translation_result) if isinstance(translation_result, (list, tuple)) else 'N/A'}")

                # Beklendiği gibi tam olarak iki değer döndüğünden emin ol
                if not isinstance(translation_result, tuple) or len(translation_result) != 2:
                    raise ValueError(f"translate_section metodu beklenmeyen sayıda değer döndürdü: {translation_result}")
                
                translated_text, stages = translation_result
                
                # Append the translated section to the list
                self.translated_sections.append({"type": section_type, "text": translated_text, "stages": stages})
                
                # Perform back-translation
                back_translated = self.translator.back_translate(
                    translated_text,
                    self.available_languages[self.target_language_var.get()],
                    self.analyzer.get_detected_language(),
                    lambda msg: self._update_translation_progress(msg, current_section_index + 1, total_sections) # Pass current section info
                )
                
                # Geri çevrilmiş metni listeye ekle
                self.back_translated_sections.append({"type": section_type, "text": back_translated})

                # Update the display (ensure this runs in the main Tkinter thread)
                self.root.after(0, self._append_translated_chapter, original_text, translated_text, back_translated)
                
                # Update progress after section is fully processed
                progress_percent = ((current_section_index + 1) / total_sections) * 100
                self.progress_var.set(progress_percent)
                # Status bar update is now solely handled by _update_translation_progress
                self._update_translation_progress(f"Bölüm {current_section_index + 1}/{total_sections} tamamlandı.\n\n", current_section_index + 1, total_sections)
                
        except Exception as e:
            self._update_translation_progress(f"Çeviri sırasında hata oluştu: {str(e)}\n", 0, 0) # Hata durumunda 0/0 gönder
        finally:
            self.status_var.set("Çeviri tamamlandı.")
            self.progress_var.set(100) # Ensure progress bar is 100% at the end
            messagebox.showinfo("Çeviri Tamamlandı", "Çeviri başarıyla tamamlandı!")

    def _update_translation_progress(self, message, current_section=0, total_sections=0):
        self.progress_text.config(state='normal')
        
        # Add section progress to the message if available
        if total_sections > 0:
            progress_info = f"({current_section}/{total_sections})"
            # Check if message already contains progress info to avoid duplication
            if not re.search(r'\(\d+/\d+\)', message):
                message = f"{progress_info} {message}"
        
        self.progress_text.insert(tk.END, message.strip() + "\n") # Ensure each message ends with a newline
        self.progress_text.see(tk.END)
        self.progress_text.config(state='disabled')
        
        # Update status bar with overall progress only if it's not the the initial "translating" message
        # and not the final "completed" or "error" message.
        if total_sections > 0 and "çevriliyor" not in message.lower() and not ("tamamlandı" in message.lower() or "hata" in message.lower()):
            overall_percent = int((current_section / total_sections) * 100)
            self.status_var.set(f"Çeviri devam ediyor: Bölüm {current_section}/{total_sections} (%{overall_percent})")
        elif "tamamlandı" in message.lower() or "hata" in message.lower():
            self.status_var.set(message.strip()) # Set final status message
        elif "çevriliyor" in message.lower(): # For the initial "translating" message, just show the section info without percentage
            self.status_var.set(f"Çeviri devam ediyor: Bölüm {current_section}/{total_sections} ({message.split('(')[1].split(')')[0]})")
        
    def _append_translated_chapter(self, original_text, translated_text, back_translated_text=""):
        print(f"DEBUG: _append_translated_chapter called.")
        print(f"DEBUG: original_text (first 50 chars): {original_text[:50]}...")
        print(f"DEBUG: translated_text (first 50 chars): {translated_text[:50]}...")
        print(f"DEBUG: back_translated_text (first 50 chars): {back_translated_text[:50]}...")

        self.root.update_idletasks() # GUI'yi hemen güncelle

        # Display original text
        self.original_text_display.config(state='normal')
        self.original_text_display.delete(1.0, tk.END)
        self.original_text_display.insert(tk.END, original_text + "\n\n")
        self.original_text_display.config(state='disabled')
        self.original_text_display.see(tk.END)
        
        self.root.update_idletasks() # GUI'yi hemen güncelle

        # Display translated text
        self.translation_text.config(state='normal')
        self.translation_text.delete(1.0, tk.END)
        self.translation_text.insert(tk.END, translated_text + "\n\n")
        self.translation_text.config(state='disabled')
        self.translation_text.see(tk.END)
        
        self.root.update_idletasks() # GUI'yi hemen güncelle

        # Display back-translated text
        self.back_translation_text.config(state='normal')
        self.back_translation_text.delete(1.0, tk.END)
        self.back_translation_text.insert(tk.END, back_translated_text + "\n\n")
        self.back_translation_text.config(state='disabled')
        self.back_translation_text.see(tk.END)
        
        self.root.update_idletasks() # GUI'yi hemen güncelle
            
    def save_translation(self):
        print(f"DEBUG: save_translation called. self.translated_sections has {len(self.translated_sections)} sections.")
        if not self.translated_sections:
            messagebox.showwarning("Save Warning", "No translated content to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    for section in self.translated_sections:
                        file.write(section["text"] + "\n\n")
                self.status_var.set(f"Translation saved to: {os.path.basename(file_path)}")
                messagebox.showinfo("Save Complete", "Translation saved successfully!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save translation: {str(e)}")

    def save_back_translation(self):
        """Geri çevrilmiş metni kaydeder."""
        if not self.back_translated_sections:
            messagebox.showwarning("Save Warning", "No back-translated content to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Back-Translation"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    for section in self.back_translated_sections:
                        file.write(section["text"] + "\n\n") # Her bölümü arasına iki yeni satır ekleyerek yaz
                self.status_var.set(f"Back-translation saved to: {os.path.basename(file_path)}")
                messagebox.showinfo("Save Complete", "Back-translation saved successfully!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save back-translation: {str(e)}")

    def save_style_guide(self):
        """Stil rehberini JSON formatında kaydeder."""
        if not self.translator.style_guide:
            messagebox.showwarning("Save Warning", "No style guide content to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Style Guide"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json5.dump(self.translator.style_guide, file, ensure_ascii=False, indent=2)
                self.status_var.set(f"Style guide saved to: {os.path.basename(file_path)}")
                messagebox.showinfo("Save Complete", "Style guide saved successfully!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save style guide: {str(e)}")

    def import_style_guide(self):
        """Stil rehberini JSON formatından içe aktarır."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Style Guide"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    imported_style_guide = json5.load(file)
                
                if not isinstance(imported_style_guide, dict):
                    raise ValueError("Geçersiz stil rehberi verisi!")
                
                self.translator.style_guide.update(imported_style_guide)
                self.status_var.set(f"Style guide imported from: {os.path.basename(file_path)}")
                messagebox.showinfo("Import Complete", "Style guide imported successfully!")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import style guide: {str(e)}")

    def show_character_editor(self):
        """Karakter düzenleme penceresini gösterir"""
        if not self.novel_analyzed:
            messagebox.showwarning("Uyarı", "Önce romanı analiz etmelisiniz!")
            return
            
        # Yeni pencere oluştur
        char_window = tk.Toplevel(self.root)
        char_window.title("Karakter Düzenleme")
        char_window.geometry("1000x800")
        
        # Ana frame
        main_frame = ttk.Frame(char_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Karakter listesi
        list_frame = ttk.LabelFrame(main_frame, text="Karakterler", padding="5")
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Karakter listesi için scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Karakter listesi
        self.char_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=30)
        self.char_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.char_listbox.yview)
        
        # Karakter detayları
        details_frame = ttk.LabelFrame(main_frame, text="Karakter Detayları", padding="5")
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Notebook (sekmeli arayüz) oluştur
        notebook = ttk.Notebook(details_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Temel Bilgiler sekmesi
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Temel Bilgiler")
        
        # İsim
        ttk.Label(basic_frame, text="İsim:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.char_name_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Rol
        ttk.Label(basic_frame, text="Rol:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_role_var = tk.StringVar()
        role_combo = ttk.Combobox(basic_frame, textvariable=self.char_role_var, 
                                values=["Ana Karakter", "Yan Karakter", "Belirtilen Karakter"],
                                state="readonly")
        role_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Geçiş Sayısı
        ttk.Label(basic_frame, text="Geçiş Sayısı:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_mentions_var = tk.StringVar()
        ttk.Label(basic_frame, textvariable=self.char_mentions_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Notlar
        ttk.Label(basic_frame, text="Notlar:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_notes_text = scrolledtext.ScrolledText(basic_frame, height=5)
        self.char_notes_text.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Meslek (Yeni Alan)
        ttk.Label(basic_frame, text="Meslek:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_occupation_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.char_occupation_var).grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Lakap (Yeni Alan)
        ttk.Label(basic_frame, text="Lakap:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_nickname_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.char_nickname_var).grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Motivasyon
        ttk.Label(basic_frame, text="Motivasyon:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_motivation_text = scrolledtext.ScrolledText(basic_frame, height=3)
        self.char_motivation_text.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Çatışmalar
        ttk.Label(basic_frame, text="Çatışmalar:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_conflicts_text = scrolledtext.ScrolledText(basic_frame, height=3)
        self.char_conflicts_text.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Özellikler sekmesi
        traits_frame = ttk.Frame(notebook)
        notebook.add(traits_frame, text="Özellikler")
        
        # Kişilik Özellikleri
        ttk.Label(traits_frame, text="Kişilik Özellikleri:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_personality_text = scrolledtext.ScrolledText(traits_frame, height=3)
        self.char_personality_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Duygu Durumları
        ttk.Label(traits_frame, text="Duygu Durumları:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_emotions_text = scrolledtext.ScrolledText(traits_frame, height=3)
        self.char_emotions_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Konuşma Tarzı
        ttk.Label(traits_frame, text="Konuşma Tarzı:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_speech_text = scrolledtext.ScrolledText(traits_frame, height=3)
        self.char_speech_text.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # İlişkiler sekmesi
        relationships_frame = ttk.Frame(notebook)
        notebook.add(relationships_frame, text="İlişkiler")
        
        # Arkadaşlar
        ttk.Label(relationships_frame, text="Arkadaşlar:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_friends_text = scrolledtext.ScrolledText(relationships_frame, height=3)
        self.char_friends_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Düşmanlar
        ttk.Label(relationships_frame, text="Düşmanlar:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_enemies_text = scrolledtext.ScrolledText(relationships_frame, height=3)
        self.char_enemies_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Aile
        ttk.Label(relationships_frame, text="Aile:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_family_text = scrolledtext.ScrolledText(relationships_frame, height=3)
        self.char_family_text.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Romantik İlişkiler
        ttk.Label(relationships_frame, text="Romantik İlişkiler:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_romantic_text = scrolledtext.ScrolledText(relationships_frame, height=3)
        self.char_romantic_text.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Gelişim sekmesi
        development_frame = ttk.Frame(notebook)
        notebook.add(development_frame, text="Karakter Gelişimi")
        
        # Başlangıç
        ttk.Label(development_frame, text="Başlangıç:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_beginning_text = scrolledtext.ScrolledText(development_frame, height=3)
        self.char_beginning_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Orta
        ttk.Label(development_frame, text="Orta:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_middle_text = scrolledtext.ScrolledText(development_frame, height=3)
        self.char_middle_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Son
        ttk.Label(development_frame, text="Son:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_end_text = scrolledtext.ScrolledText(development_frame, height=3)
        self.char_end_text.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Karakter Yay Tipi
        ttk.Label(development_frame, text="Karakter Yay Tipi:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_arc_type_var = tk.StringVar()
        arc_type_combo = ttk.Combobox(development_frame, textvariable=self.char_arc_type_var, 
                                      values=["Klasik", "Trajik", "Düz", "Dairesel"],
                                      state="readonly")
        arc_type_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Örnekler sekmesi
        examples_frame = ttk.Frame(notebook)
        notebook.add(examples_frame, text="Örnekler")
        
        # Diyalog örnekleri
        ttk.Label(examples_frame, text="Diyalog Örnekleri:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_dialogues_text = scrolledtext.ScrolledText(examples_frame, height=5)
        self.char_dialogues_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Düşünce örnekleri
        ttk.Label(examples_frame, text="Düşünce Örnekleri:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_thoughts_text = scrolledtext.ScrolledText(examples_frame, height=5)
        self.char_thoughts_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Butonlar
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Kaydet", command=self.save_character_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Yeni Karakter", command=self.add_new_character).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Karakteri Sil", command=self.delete_character).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Dışa Aktar", command=self.export_characters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İçe Aktar", command=self.import_characters).pack(side=tk.LEFT, padx=5)
        
        # Karakterleri listeye ekle
        self.update_character_list()
        
        # Listbox seçim olayını bağla
        self.char_listbox.bind('<<ListboxSelect>>', self.on_character_select)

        # Karakterler varsa ilk karakteri otomatik seç
        if self.analyzer.characters:
            print(f"DEBUG: show_character_editor - Characters available for edit: {list(self.analyzer.characters.keys())}") # Debug
            self.char_listbox.selection_set(0)
            self.char_listbox.activate(0)
            self.on_character_select(None) # Detayları yüklemek için manuel çağrı
        else:
            print("DEBUG: show_character_editor - No characters found for edit.") # Debug
            self.selected_character_name = None # Karakter yoksa seçimi sıfırla

    def update_character_list(self):
        """Karakter listesini günceller"""
        self.char_listbox.delete(0, tk.END)
        for char_name in self.analyzer.characters.keys():
            self.char_listbox.insert(tk.END, char_name)
            
    def on_character_select(self, event):
        """Karakter seçildiğinde detayları gösterir"""
        print(f"DEBUG: on_character_select called. Event: {event}") # Debug: Fonksiyon çağrısını izle
        selection = self.char_listbox.curselection()
        print(f"DEBUG: on_character_select - current selection: {selection}") # Debug: Seçimi göster
        if not selection:
            print("DEBUG: on_character_select - No selection, returning.") # Debug: Seçim yoksa
            return
            
        char_name = self.char_listbox.get(selection[0])
        self.selected_character_name = char_name # Seçilen karakter adını kaydet
        print(f"DEBUG: on_character_select - self.selected_character_name set to: {self.selected_character_name}") # Debug: Ayarlanan karakter adını göster
        char_data = self.analyzer.characters[char_name]
        
        # Temel bilgileri doldur
        self.char_name_var.set(char_data.get("name", "")) # .get() ile güvenli erişim
        self.char_role_var.set(char_data.get("role", "Yan Karakter")) # .get() ile güvenli erişim
        self.char_mentions_var.set(str(char_data.get("mentions", 0))) # .get() ile güvenli erişim
        self.char_notes_text.delete(1.0, tk.END)
        self.char_notes_text.insert(1.0, char_data.get("notes", "")) # .get() ile güvenli erişim
        
        # Yeni alanları doldur (Meslek ve Lakap)
        self.char_occupation_var.set(char_data.get("occupation", ""))
        self.char_nickname_var.set(char_data.get("nickname", ""))

        self.char_motivation_text.delete(1.0, tk.END)
        self.char_motivation_text.insert(1.0, char_data.get("motivation", ""))
        
        self.char_conflicts_text.delete(1.0, tk.END)
        self.char_conflicts_text.insert(1.0, ", ".join(char_data.get("conflicts", [])))
        
        # Karakter Yay Tipi doldur
        self.char_arc_type_var.set(char_data.get("arc_type", "Klasik"))
        
        # Özellikleri doldur
        traits = char_data.get("traits", {}) # Varsayılan olarak boş sözlük döndür
        self.char_personality_text.delete(1.0, tk.END)
        self.char_personality_text.insert(1.0, ", ".join(traits.get("personality", []))) # .get() ile güvenli erişim
        
        self.char_emotions_text.delete(1.0, tk.END)
        self.char_emotions_text.insert(1.0, ", ".join(traits.get("emotions", []))) # .get() ile güvenli erişim
        
        self.char_speech_text.delete(1.0, tk.END)
        self.char_speech_text.insert(1.0, ", ".join(traits.get("speech_style", []))) # .get() ile güvenli erişim
        
        # İlişkileri doldur
        relationships = char_data.get("relationships", {}) # Varsayılan olarak boş sözlük döndür
        self.char_friends_text.delete(1.0, tk.END)
        self.char_friends_text.insert(1.0, ", ".join(relationships.get("friends", []))) # .get() ile güvenli erişim
        
        self.char_enemies_text.delete(1.0, tk.END)
        self.char_enemies_text.insert(1.0, ", ".join(relationships.get("enemies", []))) # .get() ile güvenli erişim
        
        self.char_family_text.delete(1.0, tk.END)
        self.char_family_text.insert(1.0, ", ".join(relationships.get("family", []))) # .get() ile güvenli erişim
        
        self.char_romantic_text.delete(1.0, tk.END)
        self.char_romantic_text.insert(1.0, ", ".join(relationships.get("romantic", []))) # .get() ile güvenli erişim
        
        # Gelişimi doldur
        development = char_data.get("development", {}) # Varsayılan olarak boş sözlük döndür
        self.char_beginning_text.delete(1.0, tk.END)
        self.char_beginning_text.insert(1.0, ", ".join(development.get("beginning", []))) # .get() ile güvenli erişim
        
        self.char_middle_text.delete(1.0, tk.END)
        self.char_middle_text.insert(1.0, ", ".join(development.get("middle", []))) # .get() ile güvenli erişim
        
        self.char_end_text.delete(1.0, tk.END)
        self.char_end_text.insert(1.0, ", ".join(development.get("end", []))) # .get() ile güvenli erişim

        # Örnekleri doldur
        self.char_dialogues_text.delete(1.0, tk.END)
        self.char_dialogues_text.insert(1.0, "\n".join(char_data.get("key_dialogues", [])))
        
        self.char_thoughts_text.delete(1.0, tk.END)
        self.char_thoughts_text.insert(1.0, "\n".join(char_data.get("key_thoughts", [])))

    def save_character_changes(self):
        """Karakter değişikliklerini kaydeder"""
        print(f"DEBUG: save_character_changes called. self.selected_character_name: {self.selected_character_name}") # Debug: Kaydetme anındaki karakter adını göster
        if self.selected_character_name is None:
            messagebox.showwarning("Uyarı", "Lütfen bir karakter seçin!")
            return
            
        old_name = self.selected_character_name # Seçili karakter adını buradan al
        new_name = self.char_name_var.get().strip() # Boşlukları temizle
        
        if not new_name:
            messagebox.showerror("Hata", "Karakter adı boş bırakılamaz!")
            return
        
        # Karakter bilgilerini güncelle
        # Eğer isim değiştiyse, sözlükteki anahtarı güncelle
        if old_name != new_name and new_name in self.analyzer.characters:
            messagebox.showerror("Hata", f"'{new_name}' adında bir karakter zaten var. Lütfen farklı bir isim girin.")
            return

        # Karakter verilerini al
        char_data = self.analyzer.characters.pop(old_name) # Eski anahtarla kaldır
        
        char_data["name"] = new_name
        char_data["role"] = self.char_role_var.get()
        char_data["notes"] = self.char_notes_text.get(1.0, tk.END).strip()
        
        # Yeni alanları güncelle (Meslek ve Lakap)
        char_data["occupation"] = self.char_occupation_var.get().strip()
        char_data["nickname"] = self.char_nickname_var.get().strip()

        char_data["motivation"] = self.char_motivation_text.get(1.0, tk.END).strip()
        char_data["conflicts"] = [c.strip() for c in self.char_conflicts_text.get(1.0, tk.END).strip().split(',') if c.strip()]
        char_data["arc_type"] = self.char_arc_type_var.get()
        
        # Özellikleri güncelle
        if "traits" not in char_data:
            char_data["traits"] = {}
        char_data["traits"]["personality"] = [p.strip() for p in self.char_personality_text.get(1.0, tk.END).strip().split(',') if p.strip()]
        char_data["traits"]["emotions"] = [e.strip() for e in self.char_emotions_text.get(1.0, tk.END).strip().split(',') if e.strip()]
        char_data["traits"]["speech_style"] = [s.strip() for s in self.char_speech_text.get(1.0, tk.END).strip().split(',') if s.strip()]
        
        # İlişkileri güncelle
        if "relationships" not in char_data:
            char_data["relationships"] = {}
        char_data["relationships"]["friends"] = [f.strip() for f in self.char_friends_text.get(1.0, tk.END).strip().split(',') if f.strip()]
        char_data["relationships"]["enemies"] = [e.strip() for e in self.char_enemies_text.get(1.0, tk.END).strip().split(',') if e.strip()]
        char_data["relationships"]["family"] = [f.strip() for f in self.char_family_text.get(1.0, tk.END).strip().split(',') if f.strip()]
        char_data["relationships"]["romantic"] = [r.strip() for r in self.char_romantic_text.get(1.0, tk.END).strip().split(',') if r.strip()]
        
        # Gelişimi güncelle
        if "development" not in char_data:
            char_data["development"] = {}
        char_data["development"]["beginning"] = [b.strip() for b in self.char_beginning_text.get(1.0, tk.END).strip().split(',') if b.strip()]
        char_data["development"]["middle"] = [m.strip() for m in self.char_middle_text.get(1.0, tk.END).strip().split(',') if m.strip()]
        char_data["development"]["end"] = [e.strip() for e in self.char_end_text.get(1.0, tk.END).strip().split(',') if e.strip()]
        
        # Diyalog ve düşünce örneklerini güncelle
        char_data["key_dialogues"] = [d.strip() for d in self.char_dialogues_text.get(1.0, tk.END).strip().split('\n') if d.strip()]
        char_data["key_thoughts"] = [t.strip() for t in self.char_thoughts_text.get(1.0, tk.END).strip().split('\n') if t.strip()]
        
        # Yeni anahtarla ekle
        self.analyzer.characters[new_name] = char_data
        self.selected_character_name = new_name # Seçimi yeni isme taşı
            
        # Listeyi güncelle ve yeni seçimi yeniden yap
        self.update_character_list()
        # Yeni seçimin indeksini bul ve seçimi yap
        try:
            new_index = list(self.analyzer.characters.keys()).index(new_name)
            self.char_listbox.selection_clear(0, tk.END) # Mevcut seçimi temizle
            self.char_listbox.selection_set(new_index)
            self.char_listbox.activate(new_index)
            self.char_listbox.see(new_index)
        except ValueError:
            pass # Karakter listede bulunamazsa hata verme, zaten güncellenmiştir.

        messagebox.showinfo("Bilgi", "Karakter bilgileri kaydedildi!")

    def add_new_character(self):
        """Yeni karakter ekler"""
        # Form alanlarını temizle
        self.char_name_var.set("")
        self.char_role_var.set("Yan Karakter")
        self.char_mentions_var.set("0")
        self.char_notes_text.delete(1.0, tk.END)
        
        # Yeni alanları temizle (Meslek ve Lakap)
        self.char_occupation_var.set("")
        self.char_nickname_var.set("")

        self.char_motivation_text.delete(1.0, tk.END)
        self.char_conflicts_text.delete(1.0, tk.END)
        self.char_arc_type_var.set("Klasik")
        
        # Özellikleri temizle
        self.char_personality_text.delete(1.0, tk.END)
        self.char_emotions_text.delete(1.0, tk.END)
        self.char_speech_text.delete(1.0, tk.END)
        
        # İlişkileri temizle
        self.char_friends_text.delete(1.0, tk.END)
        self.char_enemies_text.delete(1.0, tk.END)
        self.char_family_text.delete(1.0, tk.END)
        self.char_romantic_text.delete(1.0, tk.END)
        
        # Gelişimi temizle
        self.char_beginning_text.delete(1.0, tk.END)
        self.char_middle_text.delete(1.0, tk.END)
        self.char_end_text.delete(1.0, tk.END)
        
        # Örnekleri temizle
        self.char_dialogues_text.delete(1.0, tk.END)
        self.char_thoughts_text.delete(1.0, tk.END)
        
        # Yeni bir boş karakter ekle
        new_character_name = "Yeni Karakter"
        i = 1
        while new_character_name in self.analyzer.characters:
            new_character_name = f"Yeni Karakter ({i})"
            i += 1
            
        self.analyzer.characters[new_character_name] = {
            "name": new_character_name,
            "role": "Yan Karakter",
            "mentions": 0,
            "notes": "",
            "occupation": "", # Yeni alan
            "nickname": "", # Yeni alan
            "personality": [],
            "emotions": [],
            "speech_style": [],
            "background": "",
            "motivation": "",
            "conflicts": [],
            "relationships": {
                "friends": [],
                "enemies": [],
                "family": [],
                "romantic": []
            },
            "development": {
                "beginning": [],
                "middle": [],
                "end": []
            },
            "arc_type": "Klasik",
            "key_dialogues": [],
            "key_thoughts": []
        }
        
        self.update_character_list()
        # Yeni eklenen karakteri seç
        self.char_listbox.selection_set(list(self.analyzer.characters.keys()).index(new_character_name))
        self.char_listbox.activate(list(self.analyzer.characters.keys()).index(new_character_name))
        self.on_character_select(None) # Yeni karakterin detaylarını yükle
        self.selected_character_name = new_character_name # Yeni karakteri seçili olarak ayarla
        messagebox.showinfo("Bilgi", f"'{new_character_name}' adında yeni karakter eklendi!")

    def delete_character(self):
        """Seçili karakteri siler"""
        selection = self.char_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir karakter seçin!")
            return
            
        char_name_to_delete = self.char_listbox.get(selection[0])
        if messagebox.askyesno("Silme Onayı", f"'{char_name_to_delete}' karakterini silmek istediğinizden emin misiniz?"):
            if char_name_to_delete in self.analyzer.characters:
                del self.analyzer.characters[char_name_to_delete]
            
            self.update_character_list()
            # Form alanlarını temizle
            self.char_name_var.set("")
            self.char_role_var.set("")
            self.char_mentions_var.set("")
            self.char_notes_text.delete(1.0, tk.END)
            
            # Yeni alanları temizle (Meslek ve Lakap)
            self.char_occupation_var.set("")
            self.char_nickname_var.set("")

            self.char_motivation_text.delete(1.0, tk.END)
            self.char_conflicts_text.delete(1.0, tk.END)
            self.char_arc_type_var.set("")
            
            # Özellikleri temizle
            self.char_personality_text.delete(1.0, tk.END)
            self.char_emotions_text.delete(1.0, tk.END)
            self.char_speech_text.delete(1.0, tk.END)
            
            # İlişkileri temizle
            self.char_friends_text.delete(1.0, tk.END)
            self.char_enemies_text.delete(1.0, tk.END)
            self.char_family_text.delete(1.0, tk.END)
            self.char_romantic_text.delete(1.0, tk.END)
            
            # Gelişimi temizle
            self.char_beginning_text.delete(1.0, tk.END)
            self.char_middle_text.delete(1.0, tk.END)
            self.char_end_text.delete(1.0, tk.END)
            
            # Örnekleri temizle
            self.char_dialogues_text.delete(1.0, tk.END)
            self.char_thoughts_text.delete(1.0, tk.END)
            
            self.selected_character_name = None # Seçimi sıfırla
            messagebox.showinfo("Bilgi", "Karakter başarıyla silindi!")

    def show_novel_details_editor(self):
        """Roman detaylarını düzenleme penceresini gösterir"""
        if not self.novel_analyzed:
            messagebox.showwarning("Uyarı", "Önce romanı analiz etmelisiniz!")
            return
            
        # Yeni pencere oluştur
        details_window = tk.Toplevel(self.root)
        details_window.title("Roman Detaylarını Düzenle")
        details_window.geometry("1000x800")
        
        # Ana frame
        main_frame = ttk.Frame(details_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook (sekmeli arayüz) oluştur
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Kültürel Bağlam sekmesi
        cultural_frame = ttk.Frame(notebook)
        notebook.add(cultural_frame, text="Kültürel Bağlam")
        self._create_cultural_context_tab(cultural_frame)
        
        # Temalar ve Motifler sekmesi
        themes_frame = ttk.Frame(notebook)
        notebook.add(themes_frame, text="Temalar ve Motifler")
        self._create_themes_motifs_tab(themes_frame)
        
        # Mekan ve Atmosfer sekmesi
        setting_frame = ttk.Frame(notebook)
        notebook.add(setting_frame, text="Mekan ve Atmosfer")
        self._create_setting_atmosphere_tab(setting_frame)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Kaydet", command=self._save_novel_details_from_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Dışa Aktar", command=self.export_novel_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İçe Aktar", command=self.import_novel_details).pack(side=tk.LEFT, padx=5)
        
        # Mevcut detayları yükle
        self._load_novel_details_to_editor()

    def _create_cultural_context_tab(self, parent_frame):
        sub_frame = ttk.Frame(parent_frame, padding="10")
        sub_frame.pack(fill=tk.BOTH, expand=True)

        labels = [
            "Tarihsel Dönem:", "Sosyal Normlar:", "Politik İklim:",
            "Kültürel Referanslar (virgülle ayırın):", "Deyimler/Atasözleri (virgülle ayırın):",
            "Özel Gelenekler (virgülle ayırın):", "Dilsel Nüanslar:"
        ]
        text_vars = [
            "historical_period_var", "social_norms_var", "political_climate_var",
            "cultural_references_text", "idioms_sayings_text",
            "specific_customs_text", "language_nuances_text"
        ]

        self.cultural_context_fields = {}
        for i, label_text in enumerate(labels):
            ttk.Label(sub_frame, text=label_text).grid(row=i*2, column=0, sticky=tk.W, padx=5, pady=2)
            if "(virgülle ayırın)" in label_text or "Dilsel Nüanslar" in label_text:
                text_widget = scrolledtext.ScrolledText(sub_frame, height=3, wrap=tk.WORD)
                text_widget.grid(row=i*2+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
                self.cultural_context_fields[text_vars[i]] = text_widget
            else:
                entry_var = tk.StringVar()
                entry_widget = ttk.Entry(sub_frame, textvariable=entry_var)
                entry_widget.grid(row=i*2+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
                self.cultural_context_fields[text_vars[i]] = entry_var
        sub_frame.grid_columnconfigure(1, weight=1)

    def _create_themes_motifs_tab(self, parent_frame):
        sub_frame = ttk.Frame(parent_frame, padding="10")
        sub_frame.pack(fill=tk.BOTH, expand=True)

        labels = [
            "Ana Temalar (virgülle ayırın):", "Alt Temalar (virgülle ayırın):",
            "Tekrarlayan Motifler (virgülle ayırın):", "Ahlaki Dersler (virgülle ayırın):"
        ]
        text_vars = [
            "main_themes_text", "sub_themes_text",
            "recurring_motifs_text", "moral_lessons_text"
        ]

        self.themes_motifs_fields = {}
        for i, label_text in enumerate(labels):
            ttk.Label(sub_frame, text=label_text).grid(row=i*2, column=0, sticky=tk.W, padx=5, pady=2)
            text_widget = scrolledtext.ScrolledText(sub_frame, height=4, wrap=tk.WORD)
            text_widget.grid(row=i*2+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
            self.themes_motifs_fields[text_vars[i]] = text_widget
        sub_frame.grid_columnconfigure(1, weight=1)

    def _create_setting_atmosphere_tab(self, parent_frame):
        sub_frame = ttk.Frame(parent_frame, padding="10")
        sub_frame.pack(fill=tk.BOTH, expand=True)

        labels = [
            "Ana Konumlar (virgülle ayırın):", "Zaman Dilimi:", "Coğrafi Özellikler:",
            "Sosyal Çevre:", "Hakim Atmosfer:", "Anahtar Unsurlar (virgülle ayırın):"
        ]
        text_vars = [
            "main_locations_text", "time_period_var", "geographical_features_var",
            "social_environment_var", "prevailing_atmosphere_var", "key_elements_text"
        ]

        self.setting_atmosphere_fields = {}
        for i, label_text in enumerate(labels):
            ttk.Label(sub_frame, text=label_text).grid(row=i*2, column=0, sticky=tk.W, padx=5, pady=2)
            if "(virgülle ayırın)" in label_text:
                text_widget = scrolledtext.ScrolledText(sub_frame, height=3, wrap=tk.WORD)
                text_widget.grid(row=i*2+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
                self.setting_atmosphere_fields[text_vars[i]] = text_widget
            else:
                entry_var = tk.StringVar()
                entry_widget = ttk.Entry(sub_frame, textvariable=entry_var)
                entry_widget.grid(row=i*2+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
                self.setting_atmosphere_fields[text_vars[i]] = entry_var
        sub_frame.grid_columnconfigure(1, weight=1)

    def _load_novel_details_to_editor(self):
        """Roman detaylarını düzenleme penceresindeki alanlara yükler."""
        # Kültürel Bağlam
        if self.cultural_context:
            self.cultural_context_fields["historical_period_var"].set(self.cultural_context.get("historical_period", ""))
            self.cultural_context_fields["social_norms_var"].set(self.cultural_context.get("social_norms", ""))
            self.cultural_context_fields["political_climate_var"].set(self.cultural_context.get("political_climate", ""))
            
            self.cultural_context_fields["cultural_references_text"].delete(1.0, tk.END)
            self.cultural_context_fields["cultural_references_text"].insert(tk.END, ", ".join(self.cultural_context.get("cultural_references", [])))
            
            self.cultural_context_fields["idioms_sayings_text"].delete(1.0, tk.END)
            self.cultural_context_fields["idioms_sayings_text"].insert(tk.END, ", ".join(self.cultural_context.get("idioms_sayings", [])))
            
            self.cultural_context_fields["specific_customs_text"].delete(1.0, tk.END)
            self.cultural_context_fields["specific_customs_text"].insert(tk.END, ", ".join(self.cultural_context.get("specific_customs", [])))
            
            self.cultural_context_fields["language_nuances_text"].delete(1.0, tk.END)
            self.cultural_context_fields["language_nuances_text"].insert(tk.END, self.cultural_context.get("language_nuances", ""))

        # Ana Temalar ve Motifler
        if self.main_themes:
            self.themes_motifs_fields["main_themes_text"].delete(1.0, tk.END)
            self.themes_motifs_fields["main_themes_text"].insert(tk.END, ", ".join(self.main_themes.get("main_themes", [])))
            
            self.themes_motifs_fields["sub_themes_text"].delete(1.0, tk.END)
            self.themes_motifs_fields["sub_themes_text"].insert(tk.END, ", ".join(self.main_themes.get("sub_themes", [])))
            
            self.themes_motifs_fields["recurring_motifs_text"].delete(1.0, tk.END)
            self.themes_motifs_fields["recurring_motifs_text"].insert(tk.END, ", ".join(self.main_themes.get("recurring_motifs", [])))
            
            self.themes_motifs_fields["moral_lessons_text"].delete(1.0, tk.END)
            self.themes_motifs_fields["moral_lessons_text"].insert(tk.END, ", ".join(self.main_themes.get("moral_lessons", [])))

        # Ortam ve Atmosfer
        if self.setting_atmosphere:
            self.setting_atmosphere_fields["main_locations_text"].delete(1.0, tk.END)
            self.setting_atmosphere_fields["main_locations_text"].insert(tk.END, ", ".join(self.setting_atmosphere.get("main_locations", [])))
            
            self.setting_atmosphere_fields["time_period_var"].set(self.setting_atmosphere.get("time_period", ""))
            self.setting_atmosphere_fields["geographical_features_var"].set(self.setting_atmosphere.get("geographical_features", ""))
            self.setting_atmosphere_fields["social_environment_var"].set(self.setting_atmosphere.get("social_environment", ""))
            self.setting_atmosphere_fields["prevailing_atmosphere_var"].set(self.setting_atmosphere.get("prevailing_atmosphere", ""))
            
            self.setting_atmosphere_fields["key_elements_text"].delete(1.0, tk.END)
            self.setting_atmosphere_fields["key_elements_text"].insert(tk.END, ", ".join(self.setting_atmosphere.get("key_elements", [])))

    def _save_novel_details_from_editor(self):
        """Düzenleme penceresindeki alanlardan roman detaylarını kaydeder."""
        # Kültürel Bağlam
        self.cultural_context["historical_period"] = self.cultural_context_fields["historical_period_var"].get()
        self.cultural_context["social_norms"] = self.cultural_context_fields["social_norms_var"].get()
        self.cultural_context["political_climate"] = self.cultural_context_fields["political_climate_var"].get()
        
        self.cultural_context["cultural_references"] = [item.strip() for item in self.cultural_context_fields["cultural_references_text"].get(1.0, tk.END).strip().split(',') if item.strip()]
        self.cultural_context["idioms_sayings"] = [item.strip() for item in self.cultural_context_fields["idioms_sayings_text"].get(1.0, tk.END).strip().split(',') if item.strip()]
        self.cultural_context["specific_customs"] = [item.strip() for item in self.cultural_context_fields["specific_customs_text"].get(1.0, tk.END).strip().split(',') if item.strip()]
        self.cultural_context["language_nuances"] = self.cultural_context_fields["language_nuances_text"].get(1.0, tk.END).strip()

        # Ana Temalar ve Motifler
        self.main_themes["main_themes"] = [item.strip() for item in self.themes_motifs_fields["main_themes_text"].get(1.0, tk.END).strip().split(',') if item.strip()]
        self.main_themes["sub_themes"] = [item.strip() for item in self.themes_motifs_fields["sub_themes_text"].get(1.0, tk.END).strip().split(',') if item.strip()]
        self.main_themes["recurring_motifs"] = [item.strip() for item in self.themes_motifs_fields["recurring_motifs_text"].get(1.0, tk.END).strip().split(',') if item.strip()]
        self.main_themes["moral_lessons"] = [item.strip() for item in self.themes_motifs_fields["moral_lessons_text"].get(1.0, tk.END).strip().split(',') if item.strip()]

        # Ortam ve Atmosfer
        self.setting_atmosphere["main_locations"] = [item.strip() for item in self.setting_atmosphere_fields["main_locations_text"].get(1.0, tk.END).strip().split(',') if item.strip()]
        self.setting_atmosphere["time_period"] = self.setting_atmosphere_fields["time_period_var"].get()
        self.setting_atmosphere["geographical_features"] = self.setting_atmosphere_fields["geographical_features_var"].get()
        self.setting_atmosphere["social_environment"] = self.setting_atmosphere_fields["social_environment_var"].get()
        self.setting_atmosphere["prevailing_atmosphere"] = self.setting_atmosphere_fields["prevailing_atmosphere_var"].get()
        self.setting_atmosphere["key_elements"] = [item.strip() for item in self.setting_atmosphere_fields["key_elements_text"].get(1.0, tk.END).strip().split(',') if item.strip()]

        messagebox.showinfo("Kaydedildi", "Roman detayları başarıyla kaydedildi!")

    def export_characters(self):
        """Karakterleri JSON formatında dışa aktarır"""
        if not self.analyzer.characters:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak karakter bulunamadı!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Karakterleri Dışa Aktar"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json5.dump(self.analyzer.characters, file, ensure_ascii=False, indent=2)
                messagebox.showinfo("Başarılı", "Karakterler başarıyla dışa aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma sırasında hata oluştu: {str(e)}")

    def import_characters(self):
        """JSON formatındaki karakterleri içe aktarır"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Karakterleri İçe Aktar"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    imported_characters = json5.load(file)
                
                if not isinstance(imported_characters, dict):
                    raise ValueError("Geçersiz karakter verisi!")
                
                # Mevcut karakterlerle birleştir
                self.analyzer.characters.update(imported_characters)
                
                # Listeyi güncelle
                self.update_character_list()
                messagebox.showinfo("Başarılı", "Karakterler başarıyla içe aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"İçe aktarma sırasında hata oluştu: {str(e)}")

    def export_novel_details(self):
        """Roman detaylarını JSON formatında dışa aktarır"""
        if not self.novel_analyzed:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak roman detayı bulunamadı!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Roman Detaylarını Dışa Aktar"
        )
        
        if file_path:
            try:
                details = {
                    "cultural_context": self.analyzer.cultural_context,
                    "main_themes": self.analyzer.main_themes,
                    "setting_atmosphere": self.analyzer.setting_atmosphere
                }
                with open(file_path, 'w', encoding='utf-8') as file:
                    json5.dump(details, file, ensure_ascii=False, indent=2)
                messagebox.showinfo("Başarılı", "Roman detayları başarıyla dışa aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma sırasında hata oluştu: {str(e)}")

    def import_novel_details(self):
        """JSON formatındaki roman detaylarını içe aktarır"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Roman Detaylarını İçe Aktar"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    imported_details = json5.load(file)
                
                if not isinstance(imported_details, dict):
                    raise ValueError("Geçersiz roman detayı verisi!")
                
                # Mevcut detaylarla birleştir
                self.analyzer.cultural_context.update(imported_details.get("cultural_context", {}))
                self.analyzer.main_themes.update(imported_details.get("main_themes", {}))
                self.analyzer.setting_atmosphere.update(imported_details.get("setting_atmosphere", {}))
                
                # Detayları yükle
                self._load_novel_details_to_editor()
                messagebox.showinfo("Başarılı", "Roman detayları başarıyla içe aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"İçe aktarma sırasında hata oluştu: {str(e)}")

    def show_prompt_editor(self):
        prompt_window = tk.Toplevel(self.root)
        prompt_window.title("Edit Prompts")
        prompt_window.geometry("800x600")  # Increased window size
        
        # Create a frame for the prompt editor
        prompt_frame = ttk.Frame(prompt_window, padding="10")
        prompt_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a notebook (tabbed interface)
        notebook = ttk.Notebook(prompt_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs for each prompt
        translation_tab = ttk.Frame(notebook)
        line_edit_tab = ttk.Frame(notebook)
        cultural_tab = ttk.Frame(notebook)
        
        notebook.add(translation_tab, text="Translation Prompt")
        notebook.add(line_edit_tab, text="Line Editing Prompt")
        notebook.add(cultural_tab, text="Cultural Localization Prompt")
        
        # Add text areas for editing prompts in each tab
        translation_prompt_text = scrolledtext.ScrolledText(translation_tab, wrap=tk.WORD, width=80, height=20)
        translation_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        translation_prompt_text.insert(tk.END, self.translator.initial_prompt)
        
        line_edit_prompt_text = scrolledtext.ScrolledText(line_edit_tab, wrap=tk.WORD, width=80, height=20)
        line_edit_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        line_edit_prompt_text.insert(tk.END, self.translator.line_edit_prompt)
        
        cultural_prompt_text = scrolledtext.ScrolledText(cultural_tab, wrap=tk.WORD, width=80, height=20)
        cultural_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cultural_prompt_text.insert(tk.END, self.translator.cultural_prompt)
        
        # Add buttons for Export, Import, and Reset to Default
        button_frame = ttk.Frame(prompt_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Export", command=lambda: self.export_prompts(translation_prompt_text.get("1.0", tk.END), line_edit_prompt_text.get("1.0", tk.END), cultural_prompt_text.get("1.0", tk.END))).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Import", command=lambda: self.import_prompts(translation_prompt_text, line_edit_prompt_text, cultural_prompt_text)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Default", command=lambda: self.reset_prompts(translation_prompt_text, line_edit_prompt_text, cultural_prompt_text)).pack(side=tk.LEFT, padx=5)
        
        # Add a Save button to update the prompts
        ttk.Button(button_frame, text="Save", command=lambda: self.save_prompts(translation_prompt_text.get("1.0", tk.END), line_edit_prompt_text.get("1.0", tk.END), cultural_prompt_text.get("1.0", tk.END))).pack(side=tk.LEFT, padx=5)
        
    def export_prompts(self, translation_prompt, line_edit_prompt, cultural_prompt):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            prompts = {
                "translation_prompt": translation_prompt,
                "line_edit_prompt": line_edit_prompt,
                "cultural_prompt": cultural_prompt
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json5.dump(prompts, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Export", "Prompts exported successfully!")
        
    def import_prompts(self, translation_prompt_text, line_edit_prompt_text, cultural_prompt_text):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                prompts = json5.load(f)
            translation_prompt_text.delete("1.0", tk.END)
            translation_prompt_text.insert(tk.END, prompts.get("translation_prompt", ""))
            line_edit_prompt_text.delete("1.0", tk.END)
            line_edit_prompt_text.insert(tk.END, prompts.get("line_edit_prompt", ""))
            cultural_prompt_text.delete("1.0", tk.END)
            cultural_prompt_text.insert(tk.END, prompts.get("cultural_prompt", ""))
            messagebox.showinfo("Import", "Prompts imported successfully!")
        
    def reset_prompts(self, translation_prompt_text, line_edit_prompt_text, cultural_prompt_text):
        translation_prompt_text.delete("1.0", tk.END)
        translation_prompt_text.insert(tk.END, self.translator.initial_prompt)
        line_edit_prompt_text.delete("1.0", tk.END)
        line_edit_prompt_text.insert(tk.END, self.translator.line_edit_prompt)
        cultural_prompt_text.delete("1.0", tk.END)
        cultural_prompt_text.insert(tk.END, self.translator.cultural_prompt)
        messagebox.showinfo("Reset", "Prompts reset to default successfully!")
        
    def save_prompts(self, translation_prompt, line_edit_prompt, cultural_prompt):
        self.translator.initial_prompt = translation_prompt
        self.translator.line_edit_prompt = line_edit_prompt
        self.translator.cultural_prompt = cultural_prompt
        messagebox.showinfo("Save", "Prompts saved successfully!")

    def show_section_editor(self):
        if not self.novel_sections:
            messagebox.showinfo("Bilgi", "Önce romanı analiz etmelisiniz!")
            return

        section_window = tk.Toplevel(self.root)
        section_window.title("Bölümleri Düzenle")
        section_window.geometry("1000x600")

        # Create main frame
        main_frame = ttk.Frame(section_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create listbox for sections
        list_frame = ttk.LabelFrame(main_frame, text="Bölümler", padding="5")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Add scrollbar to listbox
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.section_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=30)
        self.section_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.section_listbox.yview)

        # Create text area for editing section content
        edit_frame = ttk.LabelFrame(main_frame, text="Bölüm İçeriği", padding="5")
        edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.section_text = scrolledtext.ScrolledText(edit_frame, wrap=tk.WORD, width=60, height=30)
        self.section_text.pack(fill=tk.BOTH, expand=True)

        # Create buttons frame below the section text
        button_frame = ttk.Frame(edit_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Bölüm Ekle", command=self.add_section).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Bölüm Sil", command=self.delete_section).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Değişiklikleri Kaydet", command=self.save_sections).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Dışa Aktar", command=self.export_sections).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İçe Aktar", command=self.import_sections).pack(side=tk.LEFT, padx=5)

        # Populate listbox with sections
        self.update_section_listbox()

        # Bind listbox selection event
        self.section_listbox.bind('<<ListboxSelect>>', self.on_section_select)

    def update_section_listbox(self):
        self.section_listbox.delete(0, tk.END)
        for i, section in enumerate(self.novel_sections, 1):
            section_type = section.get("type", "Bilinmeyen")
            self.section_listbox.insert(tk.END, f"{i}. {section_type}")

    def on_section_select(self, event):
        if not self.section_listbox.curselection():
            return
        
        index = self.section_listbox.curselection()[0]
        section = self.novel_sections[index]
        
        self.section_text.delete("1.0", tk.END)
        self.section_text.insert("1.0", section["text"])

    def add_section(self):
        # Create a new section
        new_section = {
            "type": "Yeni Bölüm",
            "text": ""
        }
        self.novel_sections.append(new_section)
        self.update_section_listbox()
        self.section_listbox.selection_set(len(self.novel_sections) - 1)
        self.section_listbox.see(len(self.novel_sections) - 1)

    def delete_section(self):
        if not self.section_listbox.curselection():
            messagebox.showwarning("Uyarı", "Lütfen silinecek bölümü seçin!")
            return
        
        index = self.section_listbox.curselection()[0]
        del self.novel_sections[index]
        self.update_section_listbox()
        self.section_text.delete("1.0", tk.END)

    def save_sections(self):
        if not self.section_listbox.curselection():
            return
        
        index = self.section_listbox.curselection()[0]
        self.novel_sections[index]["text"] = self.section_text.get("1.0", tk.END).strip()
        messagebox.showinfo("Bilgi", "Değişiklikler kaydedildi!")

    def export_sections(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json5.dump(self.novel_sections, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Bilgi", "Bölümler başarıyla dışa aktarıldı!")

    def import_sections(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.novel_sections = json5.load(f)
                self.update_section_listbox()
                messagebox.showinfo("Bilgi", "Bölümler başarıyla içe aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"İçe aktarma sırasında hata oluştu: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NovelTranslatorApp(root)
    root.mainloop()

import re
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
from novel_analyzer import NovelAnalyzer
from translator import NovelTranslator
from dotenv import load_dotenv
import json5 # json yerine json5 kullanıldı

PROMPT_FILE = "prompts.json"

class NovelTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x800")
        
        load_dotenv()

        self.ui_texts = {}
        self.app_languages = {}
        self.current_app_language_var = tk.StringVar()
        self.current_app_language = ""
        
        self._load_languages_from_files()

        if not self.current_app_language:
            print("UYARI: Dil dosyaları yüklenemedi veya varsayılan dil ayarlanamadı. İngilizce'ye dönülüyor.")
            self.ui_texts["en"] = {
                "_language_name_": "English", "app_title": "Novel Translation Assistant - Language Error",
                "app_language_label": "App Language:", "select_novel_file_button": "Select Novel File",
            }
            self.app_languages = {"English": "en"}
            self.current_app_language = "en"
            self.current_app_language_var.set("English")
        
        self.current_app_language_var.trace_add("write", self._on_language_change)
        
        self.available_languages = {
            "English": "en", "Türkçe": "tr", "Deutsch": "de", "Français": "fr", "Español": "es",
            "Italiano": "it", "Português": "pt", "Русский": "ru", "日本語": "ja", "中文": "zh",
            "한국어": "ko", "العربية": "ar", "हिन्दी": "hi"
        }
        self.available_countries = {
            "United States (English)": "US", "United Kingdom (English)": "UK", "Canada (English)": "CA",
            "Australia (English)": "AU", "India (English)": "IN", "Ireland (English)": "IE",
            "South Africa (English)": "ZA", "Türkiye (Türkçe)": "TR", "Germany (Deutsch)": "DE",
            "France (Français)": "FR", "Spain (Español)": "ES", "Mexico (Español)": "MX",
            "Argentina (Español)": "AR", "Italy (Italiano)": "IT", "Portugal (Português)": "PT",
            "Brazil (Português)": "BR", "Russia (Русский)": "RU", "Japan (日本語)": "JP",
            "China (中文)": "CN", "South Korea (한국어)": "KR", "Egypt (العربية)": "EG",
            "Saudi Arabia (العربية)": "SA"
        }
        self.available_genres = [
            "Roman", "Kara Roman", "Polisiye", "Bilim Kurgu", "Fantastik", "Tarihi", "Macera", "Romantik",
            "Gerilim", "Korku", "Biyografi", "Otobiyografi", "Deneme", "Öykü", "Şiir", "Tiyatro", "Çocuk",
            "Gençlik", "Mizah", "Felsefe", "Bilim", "Distopik", "Ütopik", "Psikolojik", "Sosyolojik",
            "Folklorik", "Mitolojik", "Epik", "Lirik", "Didaktik", "Satirik", "Pastoral", "Dramatik",
            "Trajik", "Komedi", "Absürd", "Varoluşçu", "Postmodern", "Gotik", "Neo-Noir", "Cyberpunk",
            "Steampunk", "Alternatif Tarih", "Büyülü Gerçekçilik", "Akıcı Roman", "Deneysel", "Belgesel",
            "Anı", "Günlük", "Mektup"
        ]
        
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        
        self.analyzer = NovelAnalyzer()
        self.translator = NovelTranslator(target_country=os.getenv("TARGET_COUNTRY", "US")) 
        self.stop_event = threading.Event()
        self.novel_sections = []
        self.translated_sections = []
        self.back_translated_sections = []
        self.novel_analyzed = False
        self.selected_character_name = None
        self.characters = {}
        self.cultural_context = {}
        self.main_themes = {}
        self.setting_atmosphere = {}
        self.original_detected_language_code = None
        
        # UI_TEXTS YÜKLENDİKTEN SONRA FRAME BAŞLIĞINI AYARLA
        lang_texts_init = self.ui_texts.get(self.current_app_language, self.ui_texts.get("en", {}))
        self.input_analysis_frame = ttk.LabelFrame(self.main_frame, text=lang_texts_init.get("input_analysis_frame_title", "Input & Analysis"), padding="5")
        self.input_analysis_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.create_input_section(self.input_analysis_frame, 0)
        self.create_analysis_section(self.input_analysis_frame, 1)
        self.create_translation_section()
        
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.progress_text = scrolledtext.ScrolledText(self.main_frame, height=5, state='disabled')
        self.progress_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar["variable"] = self.progress_var
        self.progress_bar["maximum"] = 100
        
        self.load_prompts_from_file()
        self.update_ui_texts() # Ensure UI texts are updated after everything is initialized
        
    def _load_languages_from_files(self):
        lang_dir = "lang"
        self.ui_texts = {}
        self.app_languages = {}
        default_lang_code = "en"
        first_available_lang_name = None

        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)
            print(f"'{lang_dir}' klasörü oluşturuldu. Lütfen dil dosyalarını buraya ekleyin (örn: en.json, tr.json).")
            self.ui_texts["en"] = {"_language_name_": "English", "app_title": "Novel Translator (No Lang Files)"}
            self.app_languages["English"] = "en"
            self.current_app_language_var.set("English")
            self.current_app_language = "en"
            return

        for filename in os.listdir(lang_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]
                filepath = os.path.join(lang_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json5.load(f)
                        lang_name = data.get("_language_name_", lang_code.capitalize())
                        self.ui_texts[lang_code] = data
                        self.app_languages[lang_name] = lang_code
                        if first_available_lang_name is None:
                            first_available_lang_name = lang_name
                        if lang_code == "tr":
                            default_lang_code = "tr"
                except Exception as e:
                    print(f"Dil dosyası yüklenirken hata ({filepath}): {e}")
        
        if not self.app_languages:
            print("UYARI: Geçerli dil dosyası bulunamadı. Temel İngilizce kullanılıyor.")
            self.ui_texts["en"] = {"_language_name_": "English", "app_title": "Novel Translator (Lang Error)"}
            self.app_languages["English"] = "en"
            self.current_app_language_var.set("English")
            self.current_app_language = "en"
        else:
            if default_lang_code == "tr" and "Türkçe" in self.app_languages:
                 self.current_app_language_var.set("Türkçe")
                 self.current_app_language = "tr"
            elif first_available_lang_name:
                self.current_app_language_var.set(first_available_lang_name)
                self.current_app_language = self.app_languages[first_available_lang_name]
            else: # Fallback if "English" key is somehow missing but other files exist
                fallback_lang_name = list(self.app_languages.keys())[0]
                self.current_app_language_var.set(fallback_lang_name)
                self.current_app_language = self.app_languages[fallback_lang_name]


    def _on_language_change(self, *args):
        selected_lang_display_name = self.current_app_language_var.get()
        if selected_lang_display_name in self.app_languages:
            self.current_app_language = self.app_languages[selected_lang_display_name]
            self.update_ui_texts()
        else:
            print(f"Hata: Seçilen dil '{selected_lang_display_name}' app_languages içinde bulunamadı.")

    def update_ui_texts(self):
        lang_texts = self.ui_texts.get(self.current_app_language, self.ui_texts.get("en", {}))

        self.root.title(lang_texts.get("app_title", "Novel Translator"))
        
        if hasattr(self, 'select_novel_button'):
            self.select_novel_button.config(text=lang_texts.get("select_novel_file_button", "Select Novel File"))
        if hasattr(self, 'app_language_label_widget'):
            self.app_language_label_widget.config(text=lang_texts.get("app_language_label", "App Language:"))
        
        if hasattr(self, 'input_analysis_frame'):
            self.input_analysis_frame.config(text=lang_texts.get("input_analysis_frame_title", "Input & Analysis"))
        if hasattr(self, 'input_frame_widget'):
            self.input_frame_widget.config(text=lang_texts.get("input_frame_title", "Input"))
        if hasattr(self, 'analysis_frame_widget'):
            self.analysis_frame_widget.config(text=lang_texts.get("analysis_frame_title", "Analysis"))
        if hasattr(self, 'translation_outer_frame_widget'):
            self.translation_outer_frame_widget.config(text=lang_texts.get("translation_verification_frame_title", "Translation & Verification"))
        if hasattr(self, 'original_text_frame_widget'):
            self.original_text_frame_widget.config(text=lang_texts.get("original_text_frame_title", "Original Text"))
        if hasattr(self, 'translated_text_frame_widget'):
            self.translated_text_frame_widget.config(text=lang_texts.get("translated_text_frame_title", "Translated Text"))
        if hasattr(self, 'back_translation_text_frame_widget'):
            self.back_translation_text_frame_widget.config(text=lang_texts.get("back_translation_frame_title", "Back-Translation"))

        if hasattr(self, 'genre_label_widget'):
            self.genre_label_widget.config(text=lang_texts.get("genre_label", "Genre:"))
        if hasattr(self, 'target_language_label_widget'):
            self.target_language_label_widget.config(text=lang_texts.get("target_language_label", "Target Language:"))
        if hasattr(self, 'target_country_label_widget'):
            self.target_country_label_widget.config(text=lang_texts.get("target_country_label", "Target Country:"))
        if hasattr(self, 'retries_label_widget'):
            self.retries_label_widget.config(text=lang_texts.get("retries_label", "Retries:"))

        if hasattr(self, 'analyze_button_widget'):
            self.analyze_button_widget.config(text=lang_texts.get("analyze_novel_button", "Analyze Novel"))
        if hasattr(self, 'novel_details_editor_button_widget'):
            self.novel_details_editor_button_widget.config(text=lang_texts.get("edit_novel_details_button", "Edit Novel Details"))
        if hasattr(self, 'section_editor_button_widget'):
            self.section_editor_button_widget.config(text=lang_texts.get("edit_sections_button", "Edit Sections"))
        if hasattr(self, 'character_editor_button_widget'):
            self.character_editor_button_widget.config(text=lang_texts.get("edit_characters_button", "Edit Characters"))
        if hasattr(self, 'analysis_summary_label_widget'):
            self.analysis_summary_label_widget.config(text=lang_texts.get("analysis_summary_label", "Analysis Summary:"))

        if hasattr(self, 'edit_style_guide_prompt_button_widget'):
            self.edit_style_guide_prompt_button_widget.config(text=lang_texts.get("edit_style_guide_prompt_button", "Edit Style Guide Prompts"))
        if hasattr(self, 'edit_analysis_prompt_button_widget'):
            self.edit_analysis_prompt_button_widget.config(text=lang_texts.get("edit_analysis_prompt_button", "Edit Analysis Prompts"))
        if hasattr(self, 'edit_prompts_button_widget'):
            self.edit_prompts_button_widget.config(text=lang_texts.get("edit_prompts_button", "Edit Translation Prompts"))
        if hasattr(self, 'translate_button_widget'):
            self.translate_button_widget.config(text=lang_texts.get("translate_button", "Translate"))
        if hasattr(self, 'save_translation_button_widget'):
            self.save_translation_button_widget.config(text=lang_texts.get("save_translation_button", "Save Translation"))
        if hasattr(self, 'save_back_translation_button_widget'):
            self.save_back_translation_button_widget.config(text=lang_texts.get("save_back_translation_button", "Save Back-Translation"))
        if hasattr(self, 'save_style_guide_button_widget'):
            self.save_style_guide_button_widget.config(text=lang_texts.get("save_style_guide_button", "Save Style Guide"))
        if hasattr(self, 'view_style_guide_button_widget'):
            self.view_style_guide_button_widget.config(text=lang_texts.get("view_style_guide_button", "View Style Guide"))
        if hasattr(self, 'import_style_guide_button_widget'):
            self.import_style_guide_button_widget.config(text=lang_texts.get("import_style_guide_button", "Import Style Guide"))
        if hasattr(self, 'stop_translation_button_widget'):
            self.stop_translation_button_widget.config(text=lang_texts.get("stop_translation_button", "Stop Translation"))
            
        if hasattr(self, 'char_window') and self.char_window.winfo_exists():
            self.char_window.title(lang_texts.get("character_editor_title", "Character Editor"))
            if hasattr(self, 'char_list_frame_widget'): self.char_list_frame_widget.config(text=lang_texts.get("characters_label", "Characters"))
            if hasattr(self, 'char_details_frame_widget'): self.char_details_frame_widget.config(text=lang_texts.get("character_details_label", "Details"))
            if hasattr(self, 'char_notebook_widget'):
                self.char_notebook_widget.tab(self.char_basic_frame_tab, text=lang_texts.get("basic_info_tab", "Basic Info"))
                self.char_notebook_widget.tab(self.char_traits_frame_tab, text=lang_texts.get("traits_tab", "Traits"))
                self.char_notebook_widget.tab(self.char_relationships_frame_tab, text=lang_texts.get("relationships_tab", "Relationships"))
                self.char_notebook_widget.tab(self.char_development_frame_tab, text=lang_texts.get("character_development_tab", "Development"))
                self.char_notebook_widget.tab(self.char_examples_frame_tab, text=lang_texts.get("examples_tab", "Examples"))
            if hasattr(self.char_window, 'char_save_button'): self.char_window.char_save_button.config(text=lang_texts.get("save_button", "Save"))
            if hasattr(self.char_window, 'char_new_button'): self.char_window.char_new_button.config(text=lang_texts.get("new_character_button", "New"))
            if hasattr(self.char_window, 'char_delete_button'): self.char_window.char_delete_button.config(text=lang_texts.get("delete_character_button", "Delete"))
            if hasattr(self.char_window, 'char_export_button'): self.char_window.char_export_button.config(text=lang_texts.get("export_button", "Export"))
            if hasattr(self.char_window, 'char_import_button'): self.char_window.char_import_button.config(text=lang_texts.get("import_button", "Import"))

        if hasattr(self, 'details_novel_window_widget') and self.details_novel_window_widget.winfo_exists():
            self.details_novel_window_widget.title(lang_texts.get("edit_novel_details_title", "Edit Novel Details"))
            if hasattr(self, 'details_novel_notebook_widget'):
                self.details_novel_notebook_widget.tab(self.cultural_frame_tab, text=lang_texts.get("cultural_context_tab", "Cultural Context"))
                self.details_novel_notebook_widget.tab(self.themes_frame_tab, text=lang_texts.get("themes_motifs_tab", "Themes & Motifs"))
                self.details_novel_notebook_widget.tab(self.setting_frame_tab, text=lang_texts.get("setting_atmosphere_tab", "Setting & Atmosphere"))
            if hasattr(self.details_novel_window_widget, 'save_button'): self.details_novel_window_widget.save_button.config(text=lang_texts.get("save_button", "Save"))
            if hasattr(self.details_novel_window_widget, 'export_button'): self.details_novel_window_widget.export_button.config(text=lang_texts.get("export_button", "Export"))
            if hasattr(self.details_novel_window_widget, 'import_button'): self.details_novel_window_widget.import_button.config(text=lang_texts.get("import_button", "Import"))
        
        if hasattr(self, 'prompt_window_widget') and self.prompt_window_widget.winfo_exists():
            self.prompt_window_widget.title(lang_texts.get("edit_prompts_title", "Edit Translation Prompts"))
            if hasattr(self, 'prompt_notebook_widget'):
                self.prompt_notebook_widget.tab(self.translation_tab_widget, text=lang_texts.get("translation_prompt_tab", "Initial Translation"))
                self.prompt_notebook_widget.tab(self.line_edit_tab_widget, text=lang_texts.get("line_editing_prompt_tab", "Line Editing"))
                self.prompt_notebook_widget.tab(self.cultural_tab_widget, text=lang_texts.get("cultural_localization_prompt_tab", "Cultural Localization"))
                if hasattr(self, 'back_translation_tab_widget'):
                    self.prompt_notebook_widget.tab(self.back_translation_tab_widget, text=lang_texts.get("back_translation_prompt_tab", "Back-Translation Prompt"))
            if hasattr(self.prompt_window_widget, 'export_button'): self.prompt_window_widget.export_button.config(text=lang_texts.get("export_button", "Export"))
            if hasattr(self.prompt_window_widget, 'import_button'): self.prompt_window_widget.import_button.config(text=lang_texts.get("import_button", "Import"))
            if hasattr(self.prompt_window_widget, 'reset_button'): self.prompt_window_widget.reset_button.config(text=lang_texts.get("reset_to_default_button", "Reset Defaults"))
            if hasattr(self.prompt_window_widget, 'save_button'): self.prompt_window_widget.save_button.config(text=lang_texts.get("save_button", "Save"))

        if hasattr(self, 'section_window_widget') and self.section_window_widget.winfo_exists():
            self.section_window_widget.title(lang_texts.get("edit_sections_title", "Edit Sections"))
            if hasattr(self, 'sections_list_frame_widget'): self.sections_list_frame_widget.config(text=lang_texts.get("sections_label", "Sections"))
            if hasattr(self, 'section_edit_frame_widget'): self.section_edit_frame_widget.config(text=lang_texts.get("section_content_label", "Content"))
            if hasattr(self.section_window_widget, 'add_button'): self.section_window_widget.add_button.config(text=lang_texts.get("add_section_button", "Add"))
            if hasattr(self.section_window_widget, 'delete_button'): self.section_window_widget.delete_button.config(text=lang_texts.get("delete_section_button", "Delete"))
            if hasattr(self.section_window_widget, 'save_button'): self.section_window_widget.save_button.config(text=lang_texts.get("save_changes_button", "Save Changes"))
            if hasattr(self.section_window_widget, 'export_button'): self.section_window_widget.export_button.config(text=lang_texts.get("export_button", "Export"))
            if hasattr(self.section_window_widget, 'import_button'): self.section_window_widget.import_button.config(text=lang_texts.get("import_button", "Import"))

        if hasattr(self, 'analysis_prompt_window_widget') and self.analysis_prompt_window_widget.winfo_exists():
            self.analysis_prompt_window_widget.title(lang_texts.get("edit_analysis_prompts_title", "Edit Analysis Prompts"))
            if hasattr(self, 'analysis_prompt_notebook_widget'):
                self.analysis_prompt_notebook_widget.tab(self.character_analysis_tab_widget, text=lang_texts.get("character_analysis_tab", "Character Analysis"))
                self.analysis_prompt_notebook_widget.tab(self.cultural_context_analysis_tab_widget, text=lang_texts.get("cultural_context_analysis_tab", "Cultural Context"))
                self.analysis_prompt_notebook_widget.tab(self.themes_motifs_analysis_tab_widget, text=lang_texts.get("themes_motifs_analysis_tab", "Themes & Motifs"))
                self.analysis_prompt_notebook_widget.tab(self.setting_atmosphere_analysis_tab_widget, text=lang_texts.get("setting_atmosphere_analysis_tab", "Setting & Atmosphere"))
            if hasattr(self.analysis_prompt_window_widget, 'export_button'): self.analysis_prompt_window_widget.export_button.config(text=lang_texts.get("export_button", "Export"))
            if hasattr(self.analysis_prompt_window_widget, 'import_button'): self.analysis_prompt_window_widget.import_button.config(text=lang_texts.get("import_button", "Import"))
            if hasattr(self.analysis_prompt_window_widget, 'reset_button'): self.analysis_prompt_window_widget.reset_button.config(text=lang_texts.get("reset_to_default_button", "Reset Defaults"))
            if hasattr(self.analysis_prompt_window_widget, 'save_button'): self.analysis_prompt_window_widget.save_button.config(text=lang_texts.get("save_button", "Save"))

        if hasattr(self, 'style_guide_prompt_window_widget') and self.style_guide_prompt_window_widget.winfo_exists():
            self.style_guide_prompt_window_widget.title(lang_texts.get("edit_style_guide_prompts_title", "Edit Style Guide Prompts"))
            if hasattr(self, 'style_guide_notebook_widget'):
                self.style_guide_notebook_widget.tab(self.style_guide_generation_tab_widget, text=lang_texts.get("style_guide_generation_tab", "Generation"))
                self.style_guide_notebook_widget.tab(self.style_guide_update_tab_widget, text=lang_texts.get("style_guide_update_tab", "Update"))
            if hasattr(self.style_guide_prompt_window_widget, 'export_button'): self.style_guide_prompt_window_widget.export_button.config(text=lang_texts.get("export_button", "Export"))
            if hasattr(self.style_guide_prompt_window_widget, 'import_button'): self.style_guide_prompt_window_widget.import_button.config(text=lang_texts.get("import_button", "Import"))
            if hasattr(self.style_guide_prompt_window_widget, 'reset_button'): self.style_guide_prompt_window_widget.reset_button.config(text=lang_texts.get("reset_to_default_button", "Reset Defaults"))
            if hasattr(self.style_guide_prompt_window_widget, 'save_button'): self.style_guide_prompt_window_widget.save_button.config(text=lang_texts.get("save_button", "Save"))
            
        if hasattr(self, 'style_guide_viewer_window_widget') and self.style_guide_viewer_window_widget.winfo_exists():
            self.style_guide_viewer_window_widget.title(lang_texts.get("view_style_guide_title", "View Style Guide"))
            if hasattr(self.style_guide_viewer_window_widget, 'close_button'): 
                 self.style_guide_viewer_window_widget.close_button.config(text=lang_texts.get("close_button", "Close"))

    def load_prompts_from_file(self):
        if os.path.exists(PROMPT_FILE):
            try:
                with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
                    data = json5.load(f)
                
                if "all_translator_prompts" in data:
                    self.translator.set_all_prompts(data["all_translator_prompts"])
                # Fallback for older structure if "all_translator_prompts" is not present
                elif "translation_prompts" in data or "style_guide_prompts" in data:
                    # Initialize with defaults from translator to ensure all keys are present
                    current_prompts = self.translator.get_all_prompts(default=True)
                    if "translation_prompts" in data:
                        tp = data["translation_prompts"]
                        current_prompts["initial_translation"] = tp.get("translation_prompt", current_prompts["initial_translation"])
                        current_prompts["line_edit"] = tp.get("line_edit_prompt", current_prompts["line_edit"])
                        current_prompts["cultural_localization"] = tp.get("cultural_prompt", current_prompts["cultural_localization"])
                        current_prompts["back_translation"] = tp.get("back_translation_prompt", current_prompts["back_translation"])
                    if "style_guide_prompts" in data:
                        sgp = data["style_guide_prompts"]
                        current_prompts["style_guide_generation"] = sgp.get("style_guide_generation", current_prompts["style_guide_generation"])
                        current_prompts["style_guide_update"] = sgp.get("style_guide_update", current_prompts["style_guide_update"])
                    self.translator.set_all_prompts(current_prompts)

                if "all_analyzer_prompts" in data:
                    self.analyzer.set_all_prompts(data["all_analyzer_prompts"])
                elif "analysis_prompts" in data: # Fallback for old structure
                    self.analyzer.set_all_prompts(data["analysis_prompts"])
                    
            except Exception as e:
                print(f"Prompt dosyası yüklenirken hata: {e}")

    def save_prompts_to_file(self):
        data = {
            "all_translator_prompts": self.translator.get_all_prompts(),
            "all_analyzer_prompts": self.analyzer.get_all_prompts()
        }
        try:
            with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
                json5.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Prompt dosyası kaydedilirken hata: {e}")

    def create_input_section(self, frame, column):
        current_lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.input_frame_widget = ttk.LabelFrame(frame, text=current_lang_texts.get("input_frame_title", "Input"), padding="5")
        self.input_frame_widget.grid(row=0, column=column, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.app_language_label_widget = ttk.Label(self.input_frame_widget, text=current_lang_texts.get("app_language_label", "App Language:"))
        self.app_language_label_widget.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        app_language_combo = ttk.Combobox(self.input_frame_widget, textvariable=self.current_app_language_var,
                                          values=list(self.app_languages.keys()) if self.app_languages else ["English"], 
                                          state="readonly", width=15)
        app_language_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        if not self.app_languages:
            app_language_combo.config(state="disabled")

        self.select_novel_button = ttk.Button(self.input_frame_widget, text=current_lang_texts.get("select_novel_file_button", "Select Novel File"), command=self.load_novel)
        self.select_novel_button.grid(row=1, column=0, padx=5, pady=5)
        self.file_path_var = tk.StringVar()
        ttk.Label(self.input_frame_widget, textvariable=self.file_path_var).grid(row=1, column=1, padx=5, pady=5)
        
        details_frame = ttk.Frame(self.input_frame_widget)
        details_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.genre_label_widget = ttk.Label(details_frame, text=current_lang_texts.get("genre_label", "Genre:"))
        self.genre_label_widget.grid(row=0, column=0, padx=5, pady=2)
        self.genre_var = tk.StringVar()
        genre_combo = ttk.Combobox(details_frame, textvariable=self.genre_var, 
                                 values=self.available_genres, state="readonly")
        genre_combo.grid(row=0, column=1, padx=5, pady=2)
        
        self.target_language_label_widget = ttk.Label(details_frame, text=current_lang_texts.get("target_language_label", "Target Language:"))
        self.target_language_label_widget.grid(row=3, column=0, padx=5, pady=2)
        self.target_language_var = tk.StringVar(value="English")
        language_combo = ttk.Combobox(details_frame, textvariable=self.target_language_var, 
                                    values=list(self.available_languages.keys()), state="readonly")
        language_combo.grid(row=3, column=1, padx=5, pady=2)

        self.target_country_label_widget = ttk.Label(details_frame, text=current_lang_texts.get("target_country_label", "Target Country:"))
        self.target_country_label_widget.grid(row=4, column=0, padx=5, pady=2)
        self.target_country_var = tk.StringVar(value="United States (English)")
        country_combo = ttk.Combobox(details_frame, textvariable=self.target_country_var, 
                                     values=list(self.available_countries.keys()), state="readonly")
        country_combo.grid(row=4, column=1, padx=5, pady=2)
        
        self.retries_label_widget = ttk.Label(details_frame, text=current_lang_texts.get("retries_label", "Retries:"))
        self.retries_label_widget.grid(row=5, column=0, padx=5, pady=2)
        self.retries_var = tk.IntVar(value=3)
        retries_spinbox = ttk.Spinbox(details_frame, from_=1, to=10, textvariable=self.retries_var, width=5)
        retries_spinbox.grid(row=5, column=1, padx=5, pady=2)
        
    def create_analysis_section(self, frame, column):
        current_lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.analysis_frame_widget = ttk.LabelFrame(frame, text=current_lang_texts.get("analysis_frame_title", "Analysis"), padding="5")
        self.analysis_frame_widget.grid(row=0, column=column, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.analyze_button_widget = ttk.Button(self.analysis_frame_widget, text=current_lang_texts.get("analyze_novel_button", "Analyze Novel"), command=self.analyze_novel)
        self.analyze_button_widget.grid(row=0, column=0, columnspan=3, pady=5, sticky="ew")

        self.novel_details_editor_button_widget = ttk.Button(self.analysis_frame_widget, text=current_lang_texts.get("edit_novel_details_button", "Edit Novel Details"), command=self.show_novel_details_editor)
        self.novel_details_editor_button_widget.grid(row=1, column=0, pady=5, padx=2, sticky="ew")

        self.section_editor_button_widget = ttk.Button(self.analysis_frame_widget, text=current_lang_texts.get("edit_sections_button", "Edit Sections"), command=self.show_section_editor)
        self.section_editor_button_widget.grid(row=1, column=1, pady=5, padx=2, sticky="ew")

        self.character_editor_button_widget = ttk.Button(self.analysis_frame_widget, text=current_lang_texts.get("edit_characters_button", "Edit Characters"), command=self.show_character_editor)
        self.character_editor_button_widget.grid(row=1, column=2, pady=5, padx=2, sticky="ew")

        self.analysis_summary_label_widget = ttk.Label(self.analysis_frame_widget, text=current_lang_texts.get("analysis_summary_label", "Analysis Summary:"))
        self.analysis_summary_label_widget.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.analysis_text = scrolledtext.ScrolledText(self.analysis_frame_widget, wrap=tk.WORD, width=50, height=5)
        self.analysis_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
    def create_translation_section(self):
        current_lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.translation_outer_frame_widget = ttk.LabelFrame(self.main_frame, text=current_lang_texts.get("translation_verification_frame_title", "Translation & Verification"), padding="5")
        self.translation_outer_frame_widget.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        paned_window = ttk.PanedWindow(self.translation_outer_frame_widget, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        self.original_text_frame_widget = ttk.LabelFrame(paned_window, text=current_lang_texts.get("original_text_frame_title", "Original Text"), padding="5")
        paned_window.add(self.original_text_frame_widget, weight=1)
        self.original_text_display = scrolledtext.ScrolledText(self.original_text_frame_widget, height=25, state='disabled', wrap=tk.WORD)
        self.original_text_display.pack(fill=tk.BOTH, expand=True)
        
        self.translated_text_frame_widget = ttk.LabelFrame(paned_window, text=current_lang_texts.get("translated_text_frame_title", "Translated Text"), padding="5")
        paned_window.add(self.translated_text_frame_widget, weight=1)
        self.translation_text = scrolledtext.ScrolledText(self.translated_text_frame_widget, height=25, state='disabled', wrap=tk.WORD)
        self.translation_text.pack(fill=tk.BOTH, expand=True)
        
        self.back_translation_text_frame_widget = ttk.LabelFrame(paned_window, text=current_lang_texts.get("back_translation_frame_title", "Back-Translation"), padding="5")
        paned_window.add(self.back_translation_text_frame_widget, weight=1)
        self.back_translation_text = scrolledtext.ScrolledText(self.back_translation_text_frame_widget, height=25, state='disabled', wrap=tk.WORD)
        self.back_translation_text.pack(fill=tk.BOTH, expand=True)
        
        button_frame = ttk.Frame(self.translation_outer_frame_widget)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.edit_style_guide_prompt_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("edit_style_guide_prompt_button", "Edit Style Guide Prompts"), command=self.show_style_guide_prompt_editor)
        self.edit_style_guide_prompt_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.edit_analysis_prompt_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("edit_analysis_prompt_button", "Edit Analysis Prompts"), command=self.show_analysis_prompt_editor)
        self.edit_analysis_prompt_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.edit_prompts_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("edit_prompts_button", "Edit Translation Prompts"), command=self.show_prompt_editor)
        self.edit_prompts_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.translate_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("translate_button", "Translate"), command=self.translate_novel)
        self.translate_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.save_translation_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("save_translation_button", "Save Translation"), command=self.save_translation)
        self.save_translation_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.save_back_translation_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("save_back_translation_button", "Save Back-Translation"), command=self.save_back_translation)
        self.save_back_translation_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.save_style_guide_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("save_style_guide_button", "Save Style Guide"), command=self.save_style_guide)
        self.save_style_guide_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.view_style_guide_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("view_style_guide_button", "View Style Guide"), command=self.show_style_guide_viewer)
        self.view_style_guide_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.import_style_guide_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("import_style_guide_button", "Import Style Guide"), command=self.import_style_guide)
        self.import_style_guide_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_translation_button_widget = ttk.Button(button_frame, text=current_lang_texts.get("stop_translation_button", "Stop Translation"), command=self.stop_translation_process)
        self.stop_translation_button_widget.pack(side=tk.LEFT, padx=5, pady=5)
        
    def load_novel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            self.file_path_var.set(file_path)
            self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            
    def analyze_novel(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.file_path_var.get():
            messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("select_novel_file_error", "Please select a novel file first!"))
            return
            
        try:
            genre = self.genre_var.get()
            if not genre:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("select_genre_error", "Please select a genre!"))
                return
                
            with open(self.file_path_var.get(), 'r', encoding='utf-8') as file:
                content = file.read()
                
            analysis_summary, self.novel_sections, self.cultural_context, self.main_themes, self.setting_atmosphere, error_message = self.analyzer.analyze(content, genre, "")
            
            self.characters = self.analyzer.get_characters()
            self.analysis_text.delete(1.0, tk.END)
            
            localized_summary = analysis_summary # Placeholder, actual localization happens below
            summary_replacements = {
                "Roman Analizi:": lang_texts.get("analyzer_summary_title", "Novel Analysis:"),
                "Tespit Edilen Dil:": lang_texts.get("analyzer_detected_language_label", "Detected Language:"),
                "Tespit Edilen Tür:": lang_texts.get("analyzer_detected_genre_label", "Detected Genre:"),
                "Tespit Edilen Karakterler:": lang_texts.get("analyzer_detected_characters_label", "Detected Characters:"),
                "Kültürel Bağlam:": lang_texts.get("analyzer_cultural_context_label", "Cultural Context:"),
                "Ana Temalar ve Motifler:": lang_texts.get("analyzer_main_themes_label", "Main Themes & Motifs:"),
                "Ortam ve Atmosfer:": lang_texts.get("analyzer_setting_atmosphere_label", "Setting & Atmosphere:"),
                "Bölüm Sayısı:": lang_texts.get("analyzer_section_count_label", "Number of Sections:"),
                "UYARI: Analiz sırasında bazı hatalar oluştu:": lang_texts.get("analyzer_warning_header", "WARNING: Some errors occurred during analysis:")
            }
            for eng, loc in summary_replacements.items():
                localized_summary = localized_summary.replace(eng, loc)
            self.analysis_text.insert(tk.END, localized_summary)
            
            if error_message:
                localized_error_message = error_message # Placeholder
                error_prefixes = {
                    "AI Karakter analizi hatası:": lang_texts.get("analyzer_char_error_prefix", "AI Character analysis error:"),
                    "AI Kültürel Bağlam analizi hatası:": lang_texts.get("analyzer_cultural_error_prefix", "AI Cultural Context analysis error:"),
                    "AI Temalar ve Motifler analizi hatası:": lang_texts.get("analyzer_themes_error_prefix", "AI Themes & Motifs analysis error:"),
                    "AI Ortam ve Atmosfer analizi hatası:": lang_texts.get("analyzer_setting_error_prefix", "AI Setting & Atmosphere analysis error:"),
                }
                specific_error_found = False
                for eng_prefix, loc_prefix in error_prefixes.items():
                    if error_message.startswith(eng_prefix):
                        specific_error_detail = error_message[len(eng_prefix):].strip()
                        localized_error_message = f"{loc_prefix} {specific_error_detail}"
                        specific_error_found = True
                        break
                if not specific_error_found:
                     localized_error_message = lang_texts.get("analyzer_generic_error_message", "An analysis error occurred: {error}").format(error=error_message)
                messagebox.showerror(lang_texts.get("analysis_error_title", "Analysis Error"), localized_error_message)

            self.original_detected_language_code = self.analyzer.get_detected_language()
            
            self._update_translation_progress(lang_texts.get("style_guide_ai_query_progress", "Querying AI for Style Guide..."))
            selected_country_name = self.target_country_var.get()
            target_country_code = self.available_countries.get(selected_country_name, "US")

            self.translator.generate_style_guide_with_ai(
                genre, self.characters, self.cultural_context, self.main_themes, self.setting_atmosphere,
                self.original_detected_language_code, self.available_languages[self.target_language_var.get()],
                target_country_code, lambda msg: self._update_translation_progress(msg),
                max_retries=self.retries_var.get()
            )
            self._update_translation_progress(lang_texts.get("style_guide_updated_by_ai_progress", "Style Guide updated by AI."))

            self.status_var.set(lang_texts.get("analysis_complete_status", "Novel analysis complete. Ready for translation."))
            if not error_message:
                messagebox.showinfo(lang_texts.get("analysis_complete_title", "Analysis Complete"), lang_texts.get("analysis_complete_message", "Analysis is complete."))
            self.novel_analyzed = True
        except Exception as e:
            messagebox.showerror(lang_texts.get("analysis_error_title", "Analysis Error"), f"{lang_texts.get('unexpected_analysis_error', 'An unexpected error occurred during analysis')}: {str(e)}")
            self.status_var.set(lang_texts.get("analysis_failed_status", "Analysis failed."))
            
    def translate_novel(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.file_path_var.get():
            messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("select_novel_file_error", "Please select a novel file first!"))
            return
        try:
            genre = self.genre_var.get()
            max_retries = self.retries_var.get()
            if not genre:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("select_genre_error", "Please select a genre!"))
                return

            self.status_var.set(lang_texts.get("ready_for_translation_status", "Ready for translation."))
            self.translation_text.delete(1.0, tk.END)
            self.translated_sections = []
            self.back_translated_sections = []
            self.stop_event.clear()

            if not self.novel_sections:
                messagebox.showwarning(lang_texts.get("translation_error_title", "Translation Error"), lang_texts.get("no_translatable_sections_warning", "No translatable sections found. Please analyze the novel first."))
                self.status_var.set(lang_texts.get("translation_failed_no_sections_status", "Translation failed: No sections."))
                return
            
            selected_country_name = self.target_country_var.get()
            target_country_code = self.available_countries.get(selected_country_name, "US")
            self.translator.target_country = target_country_code
            
            threading.Thread(target=self._run_translation_in_background, args=(max_retries, target_country_code), daemon=True).start()
        except Exception as e:
            messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), f"{lang_texts.get('generic_error_occurred', 'An error occurred')}: {str(e)}")

    def stop_translation_process(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.stop_event.set()
        self.status_var.set(lang_texts.get("translation_stopped_status", "Translation stopped by user."))
        messagebox.showinfo(lang_texts.get("translation_stopped_title", "Translation Stopped"), lang_texts.get("translation_stopped_message", "Translation process has been stopped."))

    def _run_translation_in_background(self, max_retries, target_country_code):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        try:
            total_sections = len(self.novel_sections)
            for current_section_index, section in enumerate(self.novel_sections):
                if self.stop_event.is_set(): break
                original_text = section["text"]
                section_type = section["type"]
                
                progress_message_template = lang_texts.get("translating_section_progress", "Translating section {current}/{total} ({type})...")
                self._update_translation_progress(progress_message_template.format(current=current_section_index + 1, total=total_sections, type=section_type), current_section_index + 1, total_sections)

                translation_result, stages = self.translator.translate_section(
                    section, self.genre_var.get(), json5.dumps(self.characters),
                    json5.dumps(self.cultural_context), json5.dumps(self.main_themes), json5.dumps(self.setting_atmosphere),
                    self.original_detected_language_code, self.available_languages[self.target_language_var.get()],
                    target_country_code, lambda msg: self._update_translation_progress(msg, current_section_index + 1, total_sections),
                    self.stop_event, max_retries
                )
                
                self.translated_sections.append({"type": section_type, "text": translation_result, "stages": stages})
                
                back_translated = self.translator.back_translate(
                    translation_result, self.available_languages[self.target_language_var.get()],
                    self.analyzer.get_detected_language(),
                    lambda msg: self._update_translation_progress(msg, current_section_index + 1, total_sections)
                )
                self.back_translated_sections.append({"type": section_type, "text": back_translated})
                self.root.after(0, self._append_translated_chapter, original_text, translation_result, back_translated)
                
                progress_percent = ((current_section_index + 1) / total_sections) * 100
                self.progress_var.set(progress_percent)
                completed_message_template = lang_texts.get("section_completed_progress", "Section {current}/{total} completed.")
                self._update_translation_progress(completed_message_template.format(current=current_section_index + 1, total=total_sections), current_section_index + 1, total_sections)
        except Exception as e:
            error_message_template = lang_texts.get("translation_error_progress", "Error during translation: {error}")
            self._update_translation_progress(error_message_template.format(error=str(e)), 0, 0)
        finally:
            if not self.stop_event.is_set(): # Only show completion if not stopped
                self.status_var.set(lang_texts.get("translation_complete_status", "Translation complete."))
                self.progress_var.set(100)
                messagebox.showinfo(lang_texts.get("translation_complete_title", "Translation Complete"), lang_texts.get("translation_complete_message", "The translation process has finished."))

    def _update_translation_progress(self, message, current_section=0, total_sections=0):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.progress_text.config(state='normal')
        
        # Simplified message processing for now, assuming messages from translator.py are already somewhat localized or generic
        processed_message = message.strip()
        
        # Add section progress if applicable
        if total_sections > 0 and current_section > 0:
             if not re.search(r'\(\d+/\d+\)', processed_message) and not processed_message.startswith("Section") and not processed_message.startswith("Bölüm"): # Avoid double progress
                progress_info = f"({current_section}/{total_sections}) "
                processed_message = progress_info + processed_message
        
        self.progress_text.insert(tk.END, processed_message + "\n")
        self.progress_text.see(tk.END)
        self.progress_text.config(state='disabled')
        
        # Status bar update
        if total_sections > 0 and current_section > 0 and current_section <= total_sections:
            overall_percent = int((current_section / total_sections) * 100)
            # Use a generic status bar message or a more specific one if the message indicates a step
            status_template = lang_texts.get("translation_in_progress_status_bar", "Translation in progress: Section {current}/{total} ({percent}%)")
            self.status_var.set(status_template.format(current=current_section, total=total_sections, percent=overall_percent))
        elif message: # For messages not tied to section progress (e.g., "Style guide updated")
            self.status_var.set(message.strip())


    def _append_translated_chapter(self, original_text, translated_text, back_translated_text=""):
        self.root.update_idletasks()
        self.original_text_display.config(state='normal')
        self.original_text_display.delete(1.0, tk.END)
        self.original_text_display.insert(tk.END, original_text + "\n\n")
        self.original_text_display.config(state='disabled')
        self.original_text_display.see(tk.END)
        
        self.translation_text.config(state='normal')
        self.translation_text.delete(1.0, tk.END)
        self.translation_text.insert(tk.END, translated_text + "\n\n")
        self.translation_text.config(state='disabled')
        self.translation_text.see(tk.END)
        
        self.back_translation_text.config(state='normal')
        self.back_translation_text.delete(1.0, tk.END)
        self.back_translation_text.insert(tk.END, back_translated_text + "\n\n")
        self.back_translation_text.config(state='disabled')
        self.back_translation_text.see(tk.END)
        self.root.update_idletasks()
            
    def save_translation(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.translated_sections:
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("no_translated_content_to_save_warning", "No translated content to save."))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], title=lang_texts.get("save_translation_dialog_title", "Save Translation"))
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    for section in self.translated_sections:
                        file.write(section["text"] + "\n\n")
                self.status_var.set(lang_texts.get("translation_saved_to_status", "Translation saved to: {filename}").format(filename=os.path.basename(file_path)))
                messagebox.showinfo(lang_texts.get("save_complete_title", "Save Complete"), lang_texts.get("save_complete_message", "File saved successfully."))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("failed_to_save_translation_error", "Failed to save translation: {error}").format(error=str(e)))

    def save_back_translation(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.back_translated_sections:
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("no_back_translated_content_to_save_warning", "No back-translated content to save."))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], title=lang_texts.get("save_back_translation_dialog_title", "Save Back-Translation"))
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    for section in self.back_translated_sections:
                        file.write(section["text"] + "\n\n")
                self.status_var.set(lang_texts.get("back_translation_saved_to_status", "Back-translation saved to: {filename}").format(filename=os.path.basename(file_path)))
                messagebox.showinfo(lang_texts.get("save_complete_title", "Save Complete"), lang_texts.get("back_translation_saved_message", "Back-translation saved successfully."))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("failed_to_save_back_translation_error", "Failed to save back-translation: {error}").format(error=str(e)))

    def save_style_guide(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.translator.style_guide or not any(self.translator.style_guide.values()): # Check if style guide is empty or all values are empty
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("no_style_guide_content_to_save_warning", "No style guide content to save."))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], title=lang_texts.get("save_style_guide_dialog_title", "Save Style Guide"))
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json5.dump(self.translator.style_guide, file, ensure_ascii=False, indent=2)
                self.status_var.set(lang_texts.get("style_guide_saved_to_status", "Style guide saved to: {filename}").format(filename=os.path.basename(file_path)))
                messagebox.showinfo(lang_texts.get("save_complete_title", "Save Complete"), lang_texts.get("style_guide_saved_message", "Style guide saved successfully."))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("failed_to_save_style_guide_error", "Failed to save style guide: {error}").format(error=str(e)))

    def import_style_guide(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")], title=lang_texts.get("import_style_guide_dialog_title", "Import Style Guide"))
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    imported_style_guide = json5.load(file)
                if not isinstance(imported_style_guide, dict):
                    raise ValueError(lang_texts.get("invalid_style_guide_data_error", "Invalid style guide data!"))
                self.translator.style_guide.update(imported_style_guide)
                self.status_var.set(lang_texts.get("style_guide_imported_from_status", "Style guide imported from: {filename}").format(filename=os.path.basename(file_path)))
                messagebox.showinfo(lang_texts.get("import_complete_title", "Import Complete"), lang_texts.get("style_guide_imported_message", "Style guide imported successfully."))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("failed_to_import_style_guide_error", "Failed to import style guide: {error}").format(error=str(e)))

    def show_character_editor(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.novel_analyzed:
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("analyze_first_warning", "Please analyze the novel first!"))
            return
        self.char_window = tk.Toplevel(self.root) 
        self.char_window.title(lang_texts.get("character_editor_title", "Character Editor"))
        self.char_window.geometry("1000x800")
        
        main_frame = ttk.Frame(self.char_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.char_list_frame_widget = ttk.LabelFrame(main_frame, text=lang_texts.get("characters_label", "Characters"), padding="5")
        self.char_list_frame_widget.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(self.char_list_frame_widget)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.char_listbox = tk.Listbox(self.char_list_frame_widget, yscrollcommand=scrollbar.set, width=30)
        self.char_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.char_listbox.yview)
        
        self.char_details_frame_widget = ttk.LabelFrame(main_frame, text=lang_texts.get("character_details_label", "Details"), padding="5")
        self.char_details_frame_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.char_notebook_widget = ttk.Notebook(self.char_details_frame_widget)
        self.char_notebook_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.char_basic_frame_tab = ttk.Frame(self.char_notebook_widget)
        self.char_notebook_widget.add(self.char_basic_frame_tab, text=lang_texts.get("basic_info_tab", "Basic Info"))
        
        ttk.Label(self.char_basic_frame_tab, text=lang_texts.get("name_label","Name:")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_name_var = tk.StringVar()
        ttk.Entry(self.char_basic_frame_tab, textvariable=self.char_name_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_basic_frame_tab, text=lang_texts.get("role_label","Role:")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_role_var = tk.StringVar()
        role_combo = ttk.Combobox(self.char_basic_frame_tab, textvariable=self.char_role_var, values=["Ana Karakter", "Yan Karakter", "Belirtilen Karakter"], state="readonly")
        role_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_basic_frame_tab, text=lang_texts.get("mentions_label","Mentions:")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_mentions_var = tk.StringVar()
        ttk.Label(self.char_basic_frame_tab, textvariable=self.char_mentions_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(self.char_basic_frame_tab, text=lang_texts.get("notes_label","Notes:")).grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_notes_text = scrolledtext.ScrolledText(self.char_basic_frame_tab, height=5)
        self.char_notes_text.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_basic_frame_tab, text=lang_texts.get("occupation_label","Occupation:")).grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_occupation_var = tk.StringVar()
        ttk.Entry(self.char_basic_frame_tab, textvariable=self.char_occupation_var).grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(self.char_basic_frame_tab, text=lang_texts.get("nickname_label","Nickname:")).grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_nickname_var = tk.StringVar()
        ttk.Entry(self.char_basic_frame_tab, textvariable=self.char_nickname_var).grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(self.char_basic_frame_tab, text=lang_texts.get("motivation_label","Motivation:")).grid(row=6, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_motivation_text = scrolledtext.ScrolledText(self.char_basic_frame_tab, height=3)
        self.char_motivation_text.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_basic_frame_tab, text=lang_texts.get("conflicts_label","Conflicts:")).grid(row=7, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_conflicts_text = scrolledtext.ScrolledText(self.char_basic_frame_tab, height=3)
        self.char_conflicts_text.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        self.char_traits_frame_tab = ttk.Frame(self.char_notebook_widget)
        self.char_notebook_widget.add(self.char_traits_frame_tab, text=lang_texts.get("traits_tab", "Traits"))
        
        ttk.Label(self.char_traits_frame_tab, text=lang_texts.get("personality_traits_label","Personality Traits:")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_personality_text = scrolledtext.ScrolledText(self.char_traits_frame_tab, height=3)
        self.char_personality_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_traits_frame_tab, text=lang_texts.get("emotional_states_label","Emotional States:")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_emotions_text = scrolledtext.ScrolledText(self.char_traits_frame_tab, height=3)
        self.char_emotions_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_traits_frame_tab, text=lang_texts.get("speech_style_label","Speech Style:")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_speech_text = scrolledtext.ScrolledText(self.char_traits_frame_tab, height=3)
        self.char_speech_text.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        self.char_relationships_frame_tab = ttk.Frame(self.char_notebook_widget)
        self.char_notebook_widget.add(self.char_relationships_frame_tab, text=lang_texts.get("relationships_tab", "Relationships"))
        
        ttk.Label(self.char_relationships_frame_tab, text=lang_texts.get("friends_label","Friends:")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_friends_text = scrolledtext.ScrolledText(self.char_relationships_frame_tab, height=3)
        self.char_friends_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_relationships_frame_tab, text=lang_texts.get("enemies_label","Enemies:")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_enemies_text = scrolledtext.ScrolledText(self.char_relationships_frame_tab, height=3)
        self.char_enemies_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_relationships_frame_tab, text=lang_texts.get("family_label","Family:")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_family_text = scrolledtext.ScrolledText(self.char_relationships_frame_tab, height=3)
        self.char_family_text.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_relationships_frame_tab, text=lang_texts.get("romantic_relationships_label","Romantic:")).grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_romantic_text = scrolledtext.ScrolledText(self.char_relationships_frame_tab, height=3)
        self.char_romantic_text.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        self.char_development_frame_tab = ttk.Frame(self.char_notebook_widget)
        self.char_notebook_widget.add(self.char_development_frame_tab, text=lang_texts.get("character_development_tab", "Development"))
        
        ttk.Label(self.char_development_frame_tab, text=lang_texts.get("beginning_label","Beginning:")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_beginning_text = scrolledtext.ScrolledText(self.char_development_frame_tab, height=3)
        self.char_beginning_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_development_frame_tab, text=lang_texts.get("middle_label","Middle:")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_middle_text = scrolledtext.ScrolledText(self.char_development_frame_tab, height=3)
        self.char_middle_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_development_frame_tab, text=lang_texts.get("end_label","End:")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_end_text = scrolledtext.ScrolledText(self.char_development_frame_tab, height=3)
        self.char_end_text.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(self.char_development_frame_tab, text=lang_texts.get("character_arc_type_label","Arc Type:")).grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_arc_type_var = tk.StringVar()
        arc_type_combo = ttk.Combobox(self.char_development_frame_tab, textvariable=self.char_arc_type_var, values=["Klasik", "Trajik", "Düz", "Dairesel"], state="readonly")
        arc_type_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        self.char_examples_frame_tab = ttk.Frame(self.char_notebook_widget)
        self.char_notebook_widget.add(self.char_examples_frame_tab, text=lang_texts.get("examples_tab", "Examples"))
        
        ttk.Label(self.char_examples_frame_tab, text=lang_texts.get("dialogue_examples_label","Dialogue Examples:")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_dialogues_text = scrolledtext.ScrolledText(self.char_examples_frame_tab, height=5)
        self.char_dialogues_text.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(self.char_examples_frame_tab, text=lang_texts.get("thought_examples_label","Thought Examples:")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.char_thoughts_text = scrolledtext.ScrolledText(self.char_examples_frame_tab, height=5)
        self.char_thoughts_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        button_frame = ttk.Frame(self.char_details_frame_widget)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.char_window.char_save_button = ttk.Button(button_frame, text=lang_texts.get("save_button", "Save"), command=self.save_character_changes)
        self.char_window.char_save_button.pack(side=tk.LEFT, padx=5)
        self.char_window.char_new_button = ttk.Button(button_frame, text=lang_texts.get("new_character_button", "New"), command=self.add_new_character)
        self.char_window.char_new_button.pack(side=tk.LEFT, padx=5)
        self.char_window.char_delete_button = ttk.Button(button_frame, text=lang_texts.get("delete_character_button", "Delete"), command=self.delete_character)
        self.char_window.char_delete_button.pack(side=tk.LEFT, padx=5)
        self.char_window.char_export_button = ttk.Button(button_frame, text=lang_texts.get("export_button", "Export"), command=self.export_characters)
        self.char_window.char_export_button.pack(side=tk.LEFT, padx=5)
        self.char_window.char_import_button = ttk.Button(button_frame, text=lang_texts.get("import_button", "Import"), command=self.import_characters)
        self.char_window.char_import_button.pack(side=tk.LEFT, padx=5)
        
        self.update_character_list()
        self.char_listbox.bind('<<ListboxSelect>>', self.on_character_select)
        if self.analyzer.characters:
            self.char_listbox.selection_set(0)
            self.char_listbox.activate(0)
            self.on_character_select(None)
        else:
            self.selected_character_name = None

    def update_character_list(self):
        self.char_listbox.delete(0, tk.END)
        for char_name in self.analyzer.characters.keys():
            self.char_listbox.insert(tk.END, char_name)
            
    def on_character_select(self, event):
        selection = self.char_listbox.curselection()
        if not selection: return
        char_name = self.char_listbox.get(selection[0])
        self.selected_character_name = char_name
        char_data = self.analyzer.characters.get(char_name, {})
        
        self.char_name_var.set(char_data.get("name", ""))
        self.char_role_var.set(char_data.get("role", "Yan Karakter"))
        self.char_mentions_var.set(str(char_data.get("mentions", 0)))
        self.char_notes_text.delete(1.0, tk.END)
        self.char_notes_text.insert(1.0, char_data.get("notes", ""))
        self.char_occupation_var.set(char_data.get("occupation", ""))
        self.char_nickname_var.set(char_data.get("nickname", ""))
        self.char_motivation_text.delete(1.0, tk.END)
        self.char_motivation_text.insert(1.0, char_data.get("motivation", ""))
        self.char_conflicts_text.delete(1.0, tk.END)
        self.char_conflicts_text.insert(1.0, ", ".join(char_data.get("conflicts", [])))
        self.char_arc_type_var.set(char_data.get("arc_type", "Klasik"))
        
        traits = char_data.get("traits", {})
        self.char_personality_text.delete(1.0, tk.END)
        self.char_personality_text.insert(1.0, ", ".join(traits.get("personality", [])))
        self.char_emotions_text.delete(1.0, tk.END)
        self.char_emotions_text.insert(1.0, ", ".join(traits.get("emotions", [])))
        self.char_speech_text.delete(1.0, tk.END)
        self.char_speech_text.insert(1.0, ", ".join(traits.get("speech_style", [])))
        
        relationships = char_data.get("relationships", {})
        self.char_friends_text.delete(1.0, tk.END)
        self.char_friends_text.insert(1.0, ", ".join(relationships.get("friends", [])))
        self.char_enemies_text.delete(1.0, tk.END)
        self.char_enemies_text.insert(1.0, ", ".join(relationships.get("enemies", [])))
        self.char_family_text.delete(1.0, tk.END)
        self.char_family_text.insert(1.0, ", ".join(relationships.get("family", [])))
        self.char_romantic_text.delete(1.0, tk.END)
        self.char_romantic_text.insert(1.0, ", ".join(relationships.get("romantic", [])))
        
        development = char_data.get("development", {})
        self.char_beginning_text.delete(1.0, tk.END)
        self.char_beginning_text.insert(1.0, ", ".join(development.get("beginning", [])))
        self.char_middle_text.delete(1.0, tk.END)
        self.char_middle_text.insert(1.0, ", ".join(development.get("middle", [])))
        self.char_end_text.delete(1.0, tk.END)
        self.char_end_text.insert(1.0, ", ".join(development.get("end", [])))

        self.char_dialogues_text.delete(1.0, tk.END)
        self.char_dialogues_text.insert(1.0, "\n".join(char_data.get("key_dialogues", [])))
        self.char_thoughts_text.delete(1.0, tk.END)
        self.char_thoughts_text.insert(1.0, "\n".join(char_data.get("key_thoughts", [])))

    def save_character_changes(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if self.selected_character_name is None:
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("select_character_warning", "Please select a character!"))
            return
        old_name = self.selected_character_name 
        new_name = self.char_name_var.get().strip() 
        if not new_name:
            messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("character_name_empty_error", "Character name cannot be empty!"))
            return
        if old_name != new_name and new_name in self.analyzer.characters:
            messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("character_exists_error", "A character named '{name}' already exists.").format(name=new_name))
            return

        char_data = self.analyzer.characters.pop(old_name, {}) # Use .pop with a default
        
        char_data["name"] = new_name
        char_data["role"] = self.char_role_var.get()
        char_data["notes"] = self.char_notes_text.get(1.0, tk.END).strip()
        char_data["occupation"] = self.char_occupation_var.get().strip()
        char_data["nickname"] = self.char_nickname_var.get().strip()
        char_data["motivation"] = self.char_motivation_text.get(1.0, tk.END).strip()
        char_data["conflicts"] = [c.strip() for c in self.char_conflicts_text.get(1.0, tk.END).strip().split(',') if c.strip()]
        char_data["arc_type"] = self.char_arc_type_var.get()
        
        char_data["traits"] = {
            "personality": [p.strip() for p in self.char_personality_text.get(1.0, tk.END).strip().split(',') if p.strip()],
            "emotions": [e.strip() for e in self.char_emotions_text.get(1.0, tk.END).strip().split(',') if e.strip()],
            "speech_style": [s.strip() for s in self.char_speech_text.get(1.0, tk.END).strip().split(',') if s.strip()]
        }
        char_data["relationships"] = {
            "friends": [f.strip() for f in self.char_friends_text.get(1.0, tk.END).strip().split(',') if f.strip()],
            "enemies": [e.strip() for e in self.char_enemies_text.get(1.0, tk.END).strip().split(',') if e.strip()],
            "family": [f.strip() for f in self.char_family_text.get(1.0, tk.END).strip().split(',') if f.strip()],
            "romantic": [r.strip() for r in self.char_romantic_text.get(1.0, tk.END).strip().split(',') if r.strip()]
        }
        char_data["development"] = {
            "beginning": [b.strip() for b in self.char_beginning_text.get(1.0, tk.END).strip().split(',') if b.strip()],
            "middle": [m.strip() for m in self.char_middle_text.get(1.0, tk.END).strip().split(',') if m.strip()],
            "end": [e.strip() for e in self.char_end_text.get(1.0, tk.END).strip().split(',') if e.strip()]
        }
        char_data["key_dialogues"] = [d.strip() for d in self.char_dialogues_text.get(1.0, tk.END).strip().split('\n') if d.strip()]
        char_data["key_thoughts"] = [t.strip() for t in self.char_thoughts_text.get(1.0, tk.END).strip().split('\n') if t.strip()]
        
        self.analyzer.characters[new_name] = char_data
        self.selected_character_name = new_name
            
        self.update_character_list()
        try:
            new_index = list(self.analyzer.characters.keys()).index(new_name)
            self.char_listbox.selection_clear(0, tk.END)
            self.char_listbox.selection_set(new_index)
            self.char_listbox.activate(new_index)
            self.char_listbox.see(new_index)
        except ValueError: pass 
        messagebox.showinfo(lang_texts.get("info_message_box_title", "Info"), lang_texts.get("character_info_saved_message", "Character information saved."))

    def add_new_character(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.char_name_var.set("")
        self.char_role_var.set("Yan Karakter")
        self.char_mentions_var.set("0")
        self.char_notes_text.delete(1.0, tk.END)
        self.char_occupation_var.set("")
        self.char_nickname_var.set("")
        self.char_motivation_text.delete(1.0, tk.END)
        self.char_conflicts_text.delete(1.0, tk.END)
        self.char_arc_type_var.set("Klasik")
        self.char_personality_text.delete(1.0, tk.END)
        self.char_emotions_text.delete(1.0, tk.END)
        self.char_speech_text.delete(1.0, tk.END)
        self.char_friends_text.delete(1.0, tk.END)
        self.char_enemies_text.delete(1.0, tk.END)
        self.char_family_text.delete(1.0, tk.END)
        self.char_romantic_text.delete(1.0, tk.END)
        self.char_beginning_text.delete(1.0, tk.END)
        self.char_middle_text.delete(1.0, tk.END)
        self.char_end_text.delete(1.0, tk.END)
        self.char_dialogues_text.delete(1.0, tk.END)
        self.char_thoughts_text.delete(1.0, tk.END)
        
        base_new_char_name = lang_texts.get("new_character_default_name", "New Character")
        new_character_name = base_new_char_name
        i = 1
        while new_character_name in self.analyzer.characters:
            new_character_name = f"{base_new_char_name} ({i})"
            i += 1
            
        self.analyzer.characters[new_character_name] = {
            "name": new_character_name, "role": "Yan Karakter", "mentions": 0, "notes": "",
            "occupation": "", "nickname": "", "personality": [], "emotions": [], "speech_style": [],
            "background": "", "motivation": "", "conflicts": [],
            "relationships": {"friends": [], "enemies": [], "family": [], "romantic": []},
            "development": {"beginning": [], "middle": [], "end": []},
            "arc_type": "Klasik", "key_dialogues": [], "key_thoughts": []
        }
        self.update_character_list()
        new_idx = list(self.analyzer.characters.keys()).index(new_character_name)
        self.char_listbox.selection_set(new_idx)
        self.char_listbox.activate(new_idx)
        self.on_character_select(None) 
        self.selected_character_name = new_character_name 
        messagebox.showinfo(lang_texts.get("info_message_box_title", "Info"), lang_texts.get("new_character_added_message", "New character '{name}' added.").format(name=new_character_name))

    def delete_character(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        selection = self.char_listbox.curselection()
        if not selection:
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("select_character_to_delete_warning", "Please select a character to delete!"))
            return
        char_name_to_delete = self.char_listbox.get(selection[0])
        if messagebox.askyesno(lang_texts.get("delete_confirmation_title", "Delete Confirmation"), lang_texts.get("delete_confirmation_message", "Are you sure you want to delete '{name}'?").format(name=char_name_to_delete)):
            if char_name_to_delete in self.analyzer.characters:
                del self.analyzer.characters[char_name_to_delete]
            self.update_character_list()
            # Clear form fields
            self.char_name_var.set("")
            self.char_role_var.set("")
            self.char_mentions_var.set("")
            self.char_notes_text.delete(1.0, tk.END)
            self.char_occupation_var.set("")
            self.char_nickname_var.set("")
            self.char_motivation_text.delete(1.0, tk.END)
            self.char_conflicts_text.delete(1.0, tk.END)
            self.char_arc_type_var.set("")
            self.char_personality_text.delete(1.0, tk.END)
            self.char_emotions_text.delete(1.0, tk.END)
            self.char_speech_text.delete(1.0, tk.END)
            self.char_friends_text.delete(1.0, tk.END)
            self.char_enemies_text.delete(1.0, tk.END)
            self.char_family_text.delete(1.0, tk.END)
            self.char_romantic_text.delete(1.0, tk.END)
            self.char_beginning_text.delete(1.0, tk.END)
            self.char_middle_text.delete(1.0, tk.END)
            self.char_end_text.delete(1.0, tk.END)
            self.char_dialogues_text.delete(1.0, tk.END)
            self.char_thoughts_text.delete(1.0, tk.END)
            self.selected_character_name = None 
            messagebox.showinfo(lang_texts.get("info_message_box_title", "Info"), lang_texts.get("character_deleted_message", "Character deleted."))

    def show_novel_details_editor(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.novel_analyzed:
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("analyze_first_warning", "Please analyze the novel first!"))
            return
        self.details_novel_window_widget = tk.Toplevel(self.root)
        self.details_novel_window_widget.title(lang_texts.get("edit_novel_details_title", "Edit Novel Details"))
        self.details_novel_window_widget.geometry("1000x800")
        main_frame = ttk.Frame(self.details_novel_window_widget, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.details_novel_notebook_widget = ttk.Notebook(main_frame)
        self.details_novel_notebook_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.cultural_frame_tab = ttk.Frame(self.details_novel_notebook_widget)
        self.details_novel_notebook_widget.add(self.cultural_frame_tab, text=lang_texts.get("cultural_context_tab", "Cultural Context"))
        self._create_cultural_context_tab(self.cultural_frame_tab)
        self.themes_frame_tab = ttk.Frame(self.details_novel_notebook_widget)
        self.details_novel_notebook_widget.add(self.themes_frame_tab, text=lang_texts.get("themes_motifs_tab", "Themes & Motifs"))
        self._create_themes_motifs_tab(self.themes_frame_tab)
        self.setting_frame_tab = ttk.Frame(self.details_novel_notebook_widget)
        self.details_novel_notebook_widget.add(self.setting_frame_tab, text=lang_texts.get("setting_atmosphere_tab", "Setting & Atmosphere"))
        self._create_setting_atmosphere_tab(self.setting_frame_tab)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        self.details_novel_window_widget.save_button = ttk.Button(button_frame, text=lang_texts.get("save_button", "Save"), command=self._save_novel_details_from_editor)
        self.details_novel_window_widget.save_button.pack(side=tk.LEFT, padx=5)
        self.details_novel_window_widget.export_button = ttk.Button(button_frame, text=lang_texts.get("export_button", "Export"), command=self.export_novel_details)
        self.details_novel_window_widget.export_button.pack(side=tk.LEFT, padx=5)
        self.details_novel_window_widget.import_button = ttk.Button(button_frame, text=lang_texts.get("import_button", "Import"), command=self.import_novel_details)
        self.details_novel_window_widget.import_button.pack(side=tk.LEFT, padx=5)
        self._load_novel_details_to_editor()

    def _create_cultural_context_tab(self, parent_frame):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        sub_frame = ttk.Frame(parent_frame, padding="10")
        sub_frame.pack(fill=tk.BOTH, expand=True)
        self.cultural_context_fields = {}
        labels_keys = [
            ("historical_period_label", "Tarihsel Dönem:"), ("social_norms_label", "Sosyal Normlar:"), 
            ("political_climate_label", "Politik İklim:"), ("cultural_references_label", "Kültürel Referanslar (virgülle ayırın):"),
            ("idioms_sayings_label", "Deyimler/Atasözleri (virgülle ayırın):"), ("specific_customs_label", "Özel Gelenekler (virgülle ayırın):"),
            ("language_nuances_label", "Dilsel Nüanslar:")
        ]
        text_vars_map = {
            "Tarihsel Dönem:": "historical_period_var", "Sosyal Normlar:": "social_norms_var", "Politik İklim:": "political_climate_var",
            "Kültürel Referanslar (virgülle ayırın):": "cultural_references_text", "Deyimler/Atasözleri (virgülle ayırın):": "idioms_sayings_text",
            "Özel Gelenekler (virgülle ayırın):": "specific_customs_text", "Dilsel Nüanslar:": "language_nuances_text"
        }
        for i, (key, default_text) in enumerate(labels_keys):
            label_text_localized = lang_texts.get(key, default_text)
            ttk.Label(sub_frame, text=label_text_localized).grid(row=i*2, column=0, sticky=tk.W, padx=5, pady=2)
            field_key = text_vars_map[default_text]
            if "text" in field_key:
                widget = scrolledtext.ScrolledText(sub_frame, height=3, wrap=tk.WORD)
                self.cultural_context_fields[field_key] = widget
            else:
                var = tk.StringVar()
                widget = ttk.Entry(sub_frame, textvariable=var)
                self.cultural_context_fields[field_key] = var
            widget.grid(row=i*2+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
        sub_frame.grid_columnconfigure(1, weight=1)

    def _create_themes_motifs_tab(self, parent_frame):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        sub_frame = ttk.Frame(parent_frame, padding="10")
        sub_frame.pack(fill=tk.BOTH, expand=True)
        self.themes_motifs_fields = {}
        labels_keys = [
            ("main_themes_label", "Ana Temalar (virgülle ayırın):"), ("sub_themes_label", "Alt Temalar (virgülle ayırın):"),
            ("recurring_motifs_label", "Tekrarlayan Motifler (virgülle ayırın):"), ("moral_lessons_label", "Ahlaki Dersler (virgülle ayırın):")
        ]
        text_vars_map = {
            "Ana Temalar (virgülle ayırın):": "main_themes_text", "Alt Temalar (virgülle ayırın):": "sub_themes_text",
            "Tekrarlayan Motifler (virgülle ayırın):": "recurring_motifs_text", "Ahlaki Dersler (virgülle ayırın):": "moral_lessons_text"
        }
        for i, (key, default_text) in enumerate(labels_keys):
            label_text_localized = lang_texts.get(key, default_text)
            ttk.Label(sub_frame, text=label_text_localized).grid(row=i*2, column=0, sticky=tk.W, padx=5, pady=2)
            field_key = text_vars_map[default_text]
            widget = scrolledtext.ScrolledText(sub_frame, height=4, wrap=tk.WORD)
            widget.grid(row=i*2+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
            self.themes_motifs_fields[field_key] = widget
        sub_frame.grid_columnconfigure(1, weight=1)

    def _create_setting_atmosphere_tab(self, parent_frame):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        sub_frame = ttk.Frame(parent_frame, padding="10")
        sub_frame.pack(fill=tk.BOTH, expand=True)
        self.setting_atmosphere_fields = {}
        labels_keys = [
            ("main_locations_label", "Ana Konumlar (virgülle ayırın):"), ("time_period_label", "Zaman Dilimi:"), 
            ("geographical_features_label", "Coğrafi Özellikler:"), ("social_environment_label", "Sosyal Çevre:"),
            ("prevailing_atmosphere_label", "Hakim Atmosfer:"), ("key_elements_label", "Anahtar Unsurlar (virgülle ayırın):")
        ]
        text_vars_map = {
            "Ana Konumlar (virgülle ayırın):": "main_locations_text", "Zaman Dilimi:": "time_period_var", 
            "Coğrafi Özellikler:": "geographical_features_var", "Sosyal Çevre:": "social_environment_var",
            "Hakim Atmosfer:": "prevailing_atmosphere_var", "Anahtar Unsurlar (virgülle ayırın):": "key_elements_text"
        }
        for i, (key, default_text) in enumerate(labels_keys):
            label_text_localized = lang_texts.get(key, default_text)
            ttk.Label(sub_frame, text=label_text_localized).grid(row=i*2, column=0, sticky=tk.W, padx=5, pady=2)
            field_key = text_vars_map[default_text]
            if "text" in field_key:
                widget = scrolledtext.ScrolledText(sub_frame, height=3, wrap=tk.WORD)
                self.setting_atmosphere_fields[field_key] = widget
            else:
                var = tk.StringVar()
                widget = ttk.Entry(sub_frame, textvariable=var)
                self.setting_atmosphere_fields[field_key] = var
            widget.grid(row=i*2+1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
        sub_frame.grid_columnconfigure(1, weight=1)

    def _load_novel_details_to_editor(self):
        if self.cultural_context:
            for key, widget_or_var in self.cultural_context_fields.items():
                data_key = key.replace("_var", "").replace("_text", "")
                value = self.cultural_context.get(data_key, "")
                if isinstance(widget_or_var, tk.StringVar):
                    widget_or_var.set(value if isinstance(value, str) else ", ".join(value))
                else: # ScrolledText
                    widget_or_var.delete(1.0, tk.END)
                    widget_or_var.insert(tk.END, value if isinstance(value, str) else ", ".join(value))
        if self.main_themes:
            for key, widget in self.themes_motifs_fields.items():
                data_key = key.replace("_text", "")
                value = self.main_themes.get(data_key, [])
                widget.delete(1.0, tk.END)
                widget.insert(tk.END, ", ".join(value))
        if self.setting_atmosphere:
            for key, widget_or_var in self.setting_atmosphere_fields.items():
                data_key = key.replace("_var", "").replace("_text", "")
                value = self.setting_atmosphere.get(data_key, "")
                if isinstance(widget_or_var, tk.StringVar):
                    widget_or_var.set(value if isinstance(value, str) else ", ".join(value))
                else: # ScrolledText
                    widget_or_var.delete(1.0, tk.END)
                    widget_or_var.insert(tk.END, value if isinstance(value, str) else ", ".join(value))

    def _save_novel_details_from_editor(self):
        for key, widget_or_var in self.cultural_context_fields.items():
            data_key = key.replace("_var", "").replace("_text", "")
            if isinstance(widget_or_var, tk.StringVar):
                self.cultural_context[data_key] = widget_or_var.get()
            else: # ScrolledText
                text_content = widget_or_var.get(1.0, tk.END).strip()
                if data_key in ["cultural_references", "idioms_sayings", "specific_customs"]:
                    self.cultural_context[data_key] = [item.strip() for item in text_content.split(',') if item.strip()]
                else:
                    self.cultural_context[data_key] = text_content
        for key, widget in self.themes_motifs_fields.items():
            data_key = key.replace("_text", "")
            text_content = widget.get(1.0, tk.END).strip()
            self.main_themes[data_key] = [item.strip() for item in text_content.split(',') if item.strip()]
        for key, widget_or_var in self.setting_atmosphere_fields.items():
            data_key = key.replace("_var", "").replace("_text", "")
            if isinstance(widget_or_var, tk.StringVar):
                self.setting_atmosphere[data_key] = widget_or_var.get()
            else: # ScrolledText
                text_content = widget_or_var.get(1.0, tk.END).strip()
                if data_key in ["main_locations", "key_elements"]:
                    self.setting_atmosphere[data_key] = [item.strip() for item in text_content.split(',') if item.strip()]
                else:
                    self.setting_atmosphere[data_key] = text_content
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        messagebox.showinfo(lang_texts.get("info_message_box_title", "Info"), lang_texts.get("novel_details_saved_message", "Novel details saved."))

    def export_characters(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.analyzer.characters:
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("no_character_to_export_warning", "No characters to export."))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title=lang_texts.get("export_characters_dialog_title", "Export Characters"))
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json5.dump(self.analyzer.characters, file, ensure_ascii=False, indent=2)
                messagebox.showinfo(lang_texts.get("success_title", "Success"), lang_texts.get("characters_exported_message", "Characters exported."))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("export_error_message", "Export error: {error}").format(error=str(e)))

    def import_characters(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title=lang_texts.get("import_characters_dialog_title", "Import Characters"))
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    imported_characters = json5.load(file)
                if not isinstance(imported_characters, dict):
                    raise ValueError(lang_texts.get("invalid_character_data_error", "Invalid character data."))
                self.analyzer.characters.update(imported_characters)
                self.update_character_list()
                messagebox.showinfo(lang_texts.get("success_title", "Success"), lang_texts.get("characters_imported_message", "Characters imported."))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("import_error_message", "Import error: {error}").format(error=str(e)))

    def export_novel_details(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.novel_analyzed:
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("no_novel_details_to_export_warning", "No novel details to export."))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title=lang_texts.get("export_novel_details_dialog_title", "Export Novel Details"))
        if file_path:
            try:
                details = {"cultural_context": self.cultural_context, "main_themes": self.main_themes, "setting_atmosphere": self.setting_atmosphere}
                with open(file_path, 'w', encoding='utf-8') as file:
                    json5.dump(details, file, ensure_ascii=False, indent=2)
                messagebox.showinfo(lang_texts.get("success_title", "Success"), lang_texts.get("novel_details_exported_message", "Novel details exported."))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("export_error_message", "Export error: {error}").format(error=str(e)))

    def import_novel_details(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title=lang_texts.get("import_novel_details_dialog_title", "Import Novel Details"))
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    imported_details = json5.load(file)
                if not isinstance(imported_details, dict):
                    raise ValueError(lang_texts.get("invalid_novel_detail_data_error", "Invalid novel detail data."))
                self.cultural_context.update(imported_details.get("cultural_context", {}))
                self.main_themes.update(imported_details.get("main_themes", {}))
                self.setting_atmosphere.update(imported_details.get("setting_atmosphere", {}))
                self._load_novel_details_to_editor()
                messagebox.showinfo(lang_texts.get("success_title", "Success"), lang_texts.get("novel_details_imported_message", "Novel details imported."))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("import_error_message", "Import error: {error}").format(error=str(e)))

    def show_prompt_editor(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.prompt_window_widget = tk.Toplevel(self.root)
        self.prompt_window_widget.title(lang_texts.get("edit_prompts_title", "Edit Translation Prompts"))
        self.prompt_window_widget.geometry("800x600") 
        
        prompt_frame = ttk.Frame(self.prompt_window_widget, padding="10")
        prompt_frame.pack(fill=tk.BOTH, expand=True)
        
        self.prompt_notebook_widget = ttk.Notebook(prompt_frame)
        self.prompt_notebook_widget.pack(fill=tk.BOTH, expand=True)
        
        self.translation_tab_widget = ttk.Frame(self.prompt_notebook_widget)
        self.line_edit_tab_widget = ttk.Frame(self.prompt_notebook_widget)
        self.cultural_tab_widget = ttk.Frame(self.prompt_notebook_widget)
        self.back_translation_tab_widget = ttk.Frame(self.prompt_notebook_widget)
        
        self.prompt_notebook_widget.add(self.translation_tab_widget, text=lang_texts.get("translation_prompt_tab", "Initial Translation"))
        self.prompt_notebook_widget.add(self.line_edit_tab_widget, text=lang_texts.get("line_editing_prompt_tab", "Line Editing"))
        self.prompt_notebook_widget.add(self.cultural_tab_widget, text=lang_texts.get("cultural_localization_prompt_tab", "Cultural Localization"))
        self.prompt_notebook_widget.add(self.back_translation_tab_widget, text=lang_texts.get("back_translation_prompt_tab", "Back-Translation Prompt"))

        current_prompts = self.translator.get_all_prompts()

        translation_prompt_text = scrolledtext.ScrolledText(self.translation_tab_widget, wrap=tk.WORD, width=80, height=20)
        translation_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        translation_prompt_text.insert(tk.END, current_prompts.get("initial_translation", ""))
        
        line_edit_prompt_text = scrolledtext.ScrolledText(self.line_edit_tab_widget, wrap=tk.WORD, width=80, height=20)
        line_edit_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        line_edit_prompt_text.insert(tk.END, current_prompts.get("line_edit", ""))
        
        cultural_prompt_text = scrolledtext.ScrolledText(self.cultural_tab_widget, wrap=tk.WORD, width=80, height=20)
        cultural_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cultural_prompt_text.insert(tk.END, current_prompts.get("cultural_localization", ""))

        back_translation_prompt_text = scrolledtext.ScrolledText(self.back_translation_tab_widget, wrap=tk.WORD, width=80, height=20)
        back_translation_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        back_translation_prompt_text.insert(tk.END, current_prompts.get("back_translation", ""))
        
        button_frame = ttk.Frame(prompt_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.prompt_window_widget.export_button = ttk.Button(button_frame, text=lang_texts.get("export_button", "Export"), command=lambda: self.export_prompts(
            translation_prompt_text.get("1.0", tk.END), line_edit_prompt_text.get("1.0", tk.END), 
            cultural_prompt_text.get("1.0", tk.END), back_translation_prompt_text.get("1.0", tk.END)
        ))
        self.prompt_window_widget.export_button.pack(side=tk.LEFT, padx=5)
        self.prompt_window_widget.import_button = ttk.Button(button_frame, text=lang_texts.get("import_button", "Import"), command=lambda: self.import_prompts(
            translation_prompt_text, line_edit_prompt_text, cultural_prompt_text, back_translation_prompt_text
        ))
        self.prompt_window_widget.import_button.pack(side=tk.LEFT, padx=5)
        self.prompt_window_widget.reset_button = ttk.Button(button_frame, text=lang_texts.get("reset_to_default_button", "Reset Defaults"), command=lambda: self.reset_prompts(
            translation_prompt_text, line_edit_prompt_text, cultural_prompt_text, back_translation_prompt_text
        ))
        self.prompt_window_widget.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.prompt_window_widget.save_button = ttk.Button(button_frame, text=lang_texts.get("save_button", "Save"), command=lambda: self.save_prompts(
            translation_prompt_text.get("1.0", tk.END), line_edit_prompt_text.get("1.0", tk.END), 
            cultural_prompt_text.get("1.0", tk.END), back_translation_prompt_text.get("1.0", tk.END)
        ))
        self.prompt_window_widget.save_button.pack(side=tk.LEFT, padx=5)
        
    def export_prompts(self, initial_translation, line_edit, cultural_localization, back_translation):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title=lang_texts.get("export_prompts_dialog_title", "Export Prompts"))
        if file_path:
            # Save all prompts from the translator instance
            prompts_to_export = {"all_translator_prompts": self.translator.get_all_prompts()}
            # Update with current UI values for the ones being edited
            prompts_to_export["all_translator_prompts"]["initial_translation"] = initial_translation.strip()
            prompts_to_export["all_translator_prompts"]["line_edit"] = line_edit.strip()
            prompts_to_export["all_translator_prompts"]["cultural_localization"] = cultural_localization.strip()
            prompts_to_export["all_translator_prompts"]["back_translation"] = back_translation.strip()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json5.dump(prompts_to_export, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(lang_texts.get("export_title", "Export"), lang_texts.get("prompts_exported_message", "Prompts exported successfully."))
        
    def import_prompts(self, initial_text_widget, line_edit_text_widget, cultural_text_widget, back_translation_text_widget):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title=lang_texts.get("import_prompts_dialog_title", "Import Prompts"))
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json5.load(f)
            
            prompts_to_load = imported_data.get("all_translator_prompts", {})
            defaults = self.translator.get_all_prompts(default=True) # For fallback
            
            # Update UI
            initial_text_widget.delete("1.0", tk.END)
            initial_text_widget.insert(tk.END, prompts_to_load.get("initial_translation", defaults["initial_translation"]))
            line_edit_text_widget.delete("1.0", tk.END)
            line_edit_text_widget.insert(tk.END, prompts_to_load.get("line_edit", defaults["line_edit"]))
            cultural_text_widget.delete("1.0", tk.END)
            cultural_text_widget.insert(tk.END, prompts_to_load.get("cultural_localization", defaults["cultural_localization"]))
            back_translation_text_widget.delete("1.0", tk.END)
            back_translation_text_widget.insert(tk.END, prompts_to_load.get("back_translation", defaults["back_translation"]))
            
            # Update translator instance with all imported prompts
            # Ensure all keys are present, falling back to defaults if not in imported file
            full_prompts_to_set = defaults.copy()
            full_prompts_to_set.update(prompts_to_load) 
            self.translator.set_all_prompts(full_prompts_to_set)

            messagebox.showinfo(lang_texts.get("import_title", "Import"), lang_texts.get("prompts_imported_message", "Prompts imported successfully."))
        
    def reset_prompts(self, initial_text_widget, line_edit_text_widget, cultural_text_widget, back_translation_text_widget):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        default_prompts = self.translator.get_all_prompts(default=True)

        initial_text_widget.delete("1.0", tk.END)
        initial_text_widget.insert(tk.END, default_prompts["initial_translation"])
        line_edit_text_widget.delete("1.0", tk.END)
        line_edit_text_widget.insert(tk.END, default_prompts["line_edit"])
        cultural_text_widget.delete("1.0", tk.END)
        cultural_text_widget.insert(tk.END, default_prompts["cultural_localization"])
        back_translation_text_widget.delete("1.0", tk.END)
        back_translation_text_widget.insert(tk.END, default_prompts["back_translation"])
        
        # Also reset the translator instance to defaults for these specific prompts
        self.translator.initial_prompt = default_prompts["initial_translation"]
        self.translator.line_edit_prompt = default_prompts["line_edit"]
        self.translator.cultural_prompt = default_prompts["cultural_localization"]
        self.translator.back_translation_prompt = default_prompts["back_translation"]
        # Style guide prompts are handled in their own editor, so no need to reset them here.
        
        messagebox.showinfo(lang_texts.get("reset_title", "Reset"), lang_texts.get("prompts_reset_message", "Prompts reset to default."))
        
    def save_prompts(self, initial_translation, line_edit, cultural_localization, back_translation):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        
        # Get all current prompts to preserve style guide prompts
        current_all_prompts = self.translator.get_all_prompts()
        prompts_to_save = {
            "initial_translation": initial_translation.strip(),
            "line_edit": line_edit.strip(),
            "cultural_localization": cultural_localization.strip(),
            "back_translation": back_translation.strip(),
            "style_guide_generation": current_all_prompts.get("style_guide_generation"),
            "style_guide_update": current_all_prompts.get("style_guide_update")
        }
        self.translator.set_all_prompts(prompts_to_save)
        self.save_prompts_to_file()
        messagebox.showinfo(lang_texts.get("save_title", "Save"), lang_texts.get("prompts_saved_message", "Prompts saved successfully."))

    def show_section_editor(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.novel_sections:
            messagebox.showinfo(lang_texts.get("info_message_box_title", "Info"), lang_texts.get("analyze_first_warning", "Please analyze the novel first!"))
            return

        self.section_window_widget = tk.Toplevel(self.root)
        self.section_window_widget.title(lang_texts.get("edit_sections_title", "Edit Sections"))
        self.section_window_widget.geometry("1000x600")

        main_frame = ttk.Frame(self.section_window_widget, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.sections_list_frame_widget = ttk.LabelFrame(main_frame, text=lang_texts.get("sections_label", "Sections"), padding="5")
        self.sections_list_frame_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        scrollbar = ttk.Scrollbar(self.sections_list_frame_widget)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.section_listbox = tk.Listbox(self.sections_list_frame_widget, yscrollcommand=scrollbar.set, width=30)
        self.section_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.section_listbox.yview)

        self.section_edit_frame_widget = ttk.LabelFrame(main_frame, text=lang_texts.get("section_content_label", "Content"), padding="5")
        self.section_edit_frame_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.section_text = scrolledtext.ScrolledText(self.section_edit_frame_widget, wrap=tk.WORD, width=60, height=30)
        self.section_text.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(self.section_edit_frame_widget)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.section_window_widget.add_button = ttk.Button(button_frame, text=lang_texts.get("add_section_button", "Add"), command=self.add_section)
        self.section_window_widget.add_button.pack(side=tk.LEFT, padx=5)
        self.section_window_widget.delete_button = ttk.Button(button_frame, text=lang_texts.get("delete_section_button", "Delete"), command=self.delete_section)
        self.section_window_widget.delete_button.pack(side=tk.LEFT, padx=5)
        self.section_window_widget.save_button = ttk.Button(button_frame, text=lang_texts.get("save_changes_button", "Save Changes"), command=self.save_sections)
        self.section_window_widget.save_button.pack(side=tk.LEFT, padx=5)
        self.section_window_widget.export_button = ttk.Button(button_frame, text=lang_texts.get("export_button", "Export"), command=self.export_sections)
        self.section_window_widget.export_button.pack(side=tk.LEFT, padx=5)
        self.section_window_widget.import_button = ttk.Button(button_frame, text=lang_texts.get("import_button", "Import"), command=self.import_sections)
        self.section_window_widget.import_button.pack(side=tk.LEFT, padx=5)

        self.update_section_listbox()
        self.section_listbox.bind('<<ListboxSelect>>', self.on_section_select)

    def update_section_listbox(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.section_listbox.delete(0, tk.END)
        for i, section in enumerate(self.novel_sections, 1):
            section_type = section.get("type", lang_texts.get("unknown_section_type", "Unknown"))
            self.section_listbox.insert(tk.END, f"{i}. {section_type}")

    def on_section_select(self, event):
        if not self.section_listbox.curselection():
            return
        index = self.section_listbox.curselection()[0]
        section = self.novel_sections[index]
        self.section_text.delete("1.0", tk.END)
        self.section_text.insert("1.0", section["text"])

    def add_section(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        new_section = {"type": lang_texts.get("new_section_default_type", "New Section"), "text": ""}
        self.novel_sections.append(new_section)
        self.update_section_listbox()
        self.section_listbox.selection_set(len(self.novel_sections) - 1)
        self.section_listbox.see(len(self.novel_sections) - 1)
        self.on_section_select(None) # Load new section into text area

    def delete_section(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.section_listbox.curselection():
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("select_section_to_delete_warning", "Please select a section to delete!"))
            return
        index = self.section_listbox.curselection()[0]
        del self.novel_sections[index]
        self.update_section_listbox()
        self.section_text.delete("1.0", tk.END)

    def save_sections(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        if not self.section_listbox.curselection():
            messagebox.showwarning(lang_texts.get("warning_message_box_title", "Warning"), lang_texts.get("select_section_to_save_warning", "Please select a section to save changes to!"))
            return
        index = self.section_listbox.curselection()[0]
        self.novel_sections[index]["text"] = self.section_text.get("1.0", tk.END).strip()
        messagebox.showinfo(lang_texts.get("info_message_box_title", "Info"), lang_texts.get("changes_saved_message", "Changes saved!"))

    def export_sections(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title=lang_texts.get("export_sections_dialog_title", "Export Sections"))
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json5.dump(self.novel_sections, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(lang_texts.get("info_message_box_title", "Info"), lang_texts.get("sections_exported_message", "Sections exported successfully!"))

    def import_sections(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title=lang_texts.get("import_sections_dialog_title", "Import Sections"))
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.novel_sections = json5.load(f)
                self.update_section_listbox()
                messagebox.showinfo(lang_texts.get("info_message_box_title", "Info"), lang_texts.get("sections_imported_message", "Sections imported successfully!"))
            except Exception as e:
                messagebox.showerror(lang_texts.get("error_message_box_title", "Error"), lang_texts.get("import_error_message", "Import error: {error}").format(error=str(e)))

    def show_analysis_prompt_editor(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.analysis_prompt_window_widget = tk.Toplevel(self.root)
        self.analysis_prompt_window_widget.title(lang_texts.get("edit_analysis_prompts_title", "Edit Analysis Prompts"))
        self.analysis_prompt_window_widget.geometry("800x600") 
        prompt_frame = ttk.Frame(self.analysis_prompt_window_widget, padding="10")
        prompt_frame.pack(fill=tk.BOTH, expand=True)
        self.analysis_prompt_notebook_widget = ttk.Notebook(prompt_frame)
        self.analysis_prompt_notebook_widget.pack(fill=tk.BOTH, expand=True)
        
        self.character_analysis_tab_widget = ttk.Frame(self.analysis_prompt_notebook_widget)
        self.cultural_context_analysis_tab_widget = ttk.Frame(self.analysis_prompt_notebook_widget)
        self.themes_motifs_analysis_tab_widget = ttk.Frame(self.analysis_prompt_notebook_widget)
        self.setting_atmosphere_analysis_tab_widget = ttk.Frame(self.analysis_prompt_notebook_widget)
        
        self.analysis_prompt_notebook_widget.add(self.character_analysis_tab_widget, text=lang_texts.get("character_analysis_tab", "Character Analysis"))
        self.analysis_prompt_notebook_widget.add(self.cultural_context_analysis_tab_widget, text=lang_texts.get("cultural_context_analysis_tab", "Cultural Context"))
        self.analysis_prompt_notebook_widget.add(self.themes_motifs_analysis_tab_widget, text=lang_texts.get("themes_motifs_analysis_tab", "Themes & Motifs"))
        self.analysis_prompt_notebook_widget.add(self.setting_atmosphere_analysis_tab_widget, text=lang_texts.get("setting_atmosphere_analysis_tab", "Setting & Atmosphere"))
        
        current_prompts = self.analyzer.get_all_prompts()
        
        character_prompt_text = scrolledtext.ScrolledText(self.character_analysis_tab_widget, wrap=tk.WORD, width=80, height=20)
        character_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        character_prompt_text.insert(tk.END, current_prompts.get("character_analysis", ""))
        
        cultural_prompt_text = scrolledtext.ScrolledText(self.cultural_context_analysis_tab_widget, wrap=tk.WORD, width=80, height=20)
        cultural_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cultural_prompt_text.insert(tk.END, current_prompts.get("cultural_context", ""))
        
        themes_prompt_text = scrolledtext.ScrolledText(self.themes_motifs_analysis_tab_widget, wrap=tk.WORD, width=80, height=20)
        themes_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        themes_prompt_text.insert(tk.END, current_prompts.get("themes_motifs", ""))
        
        setting_prompt_text = scrolledtext.ScrolledText(self.setting_atmosphere_analysis_tab_widget, wrap=tk.WORD, width=80, height=20)
        setting_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        setting_prompt_text.insert(tk.END, current_prompts.get("setting_atmosphere", ""))
        
        button_frame = ttk.Frame(prompt_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.analysis_prompt_window_widget.export_button = ttk.Button(button_frame, text=lang_texts.get("export_button", "Export"), command=lambda: self.export_analysis_prompts(character_prompt_text.get("1.0", tk.END), cultural_prompt_text.get("1.0", tk.END), themes_prompt_text.get("1.0", tk.END), setting_prompt_text.get("1.0", tk.END)))
        self.analysis_prompt_window_widget.export_button.pack(side=tk.LEFT, padx=5)
        self.analysis_prompt_window_widget.import_button = ttk.Button(button_frame, text=lang_texts.get("import_button", "Import"), command=lambda: self.import_analysis_prompts(character_prompt_text, cultural_prompt_text, themes_prompt_text, setting_prompt_text))
        self.analysis_prompt_window_widget.import_button.pack(side=tk.LEFT, padx=5)
        self.analysis_prompt_window_widget.reset_button = ttk.Button(button_frame, text=lang_texts.get("reset_to_default_button", "Reset Defaults"), command=lambda: self.reset_analysis_prompts(character_prompt_text, cultural_prompt_text, themes_prompt_text, setting_prompt_text))
        self.analysis_prompt_window_widget.reset_button.pack(side=tk.LEFT, padx=5)
        self.analysis_prompt_window_widget.save_button = ttk.Button(button_frame, text=lang_texts.get("save_button", "Save"), command=lambda: self.save_analysis_prompts(character_prompt_text.get("1.0", tk.END), cultural_prompt_text.get("1.0", tk.END), themes_prompt_text.get("1.0", tk.END), setting_prompt_text.get("1.0", tk.END)))
        self.analysis_prompt_window_widget.save_button.pack(side=tk.LEFT, padx=5)
        
    def export_analysis_prompts(self, character_prompt, cultural_prompt, themes_prompt, setting_prompt):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title=lang_texts.get("export_analysis_prompts_dialog_title", "Export Analysis Prompts"))
        if file_path:
            prompts = {
                "character_analysis": character_prompt.strip(), "cultural_context": cultural_prompt.strip(),
                "themes_motifs": themes_prompt.strip(), "setting_atmosphere": setting_prompt.strip()
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json5.dump({"all_analyzer_prompts": prompts}, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(lang_texts.get("export_title", "Export"), lang_texts.get("analysis_prompts_exported_message", "Analysis prompts exported."))
        
    def import_analysis_prompts(self, character_prompt_text, cultural_prompt_text, themes_prompt_text, setting_prompt_text):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title=lang_texts.get("import_analysis_prompts_dialog_title", "Import Analysis Prompts"))
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json5.load(f)
            prompts = imported_data.get("all_analyzer_prompts", {})
            defaults = self.analyzer.get_all_prompts(default=True)

            character_prompt_text.delete("1.0", tk.END)
            character_prompt_text.insert(tk.END, prompts.get("character_analysis", defaults["character_analysis"]))
            cultural_prompt_text.delete("1.0", tk.END)
            cultural_prompt_text.insert(tk.END, prompts.get("cultural_context", defaults["cultural_context"]))
            themes_prompt_text.delete("1.0", tk.END)
            themes_prompt_text.insert(tk.END, prompts.get("themes_motifs", defaults["themes_motifs"]))
            setting_prompt_text.delete("1.0", tk.END)
            setting_prompt_text.insert(tk.END, prompts.get("setting_atmosphere", defaults["setting_atmosphere"]))
            
            self.analyzer.set_all_prompts(prompts) # Update analyzer instance
            messagebox.showinfo(lang_texts.get("import_title", "Import"), lang_texts.get("analysis_prompts_imported_message", "Analysis prompts imported."))
        
    def reset_analysis_prompts(self, character_prompt_text, cultural_prompt_text, themes_prompt_text, setting_prompt_text):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        default_prompts = self.analyzer.get_all_prompts(default=True)
        character_prompt_text.delete("1.0", tk.END)
        character_prompt_text.insert(tk.END, default_prompts["character_analysis"])
        cultural_prompt_text.delete("1.0", tk.END)
        cultural_prompt_text.insert(tk.END, default_prompts["cultural_context"])
        themes_prompt_text.delete("1.0", tk.END)
        themes_prompt_text.insert(tk.END, default_prompts["themes_motifs"])
        setting_prompt_text.delete("1.0", tk.END)
        setting_prompt_text.insert(tk.END, default_prompts["setting_atmosphere"])
        self.analyzer.set_all_prompts(default_prompts) # Reset analyzer instance
        messagebox.showinfo(lang_texts.get("reset_title", "Reset"), lang_texts.get("analysis_prompts_reset_message", "Analysis prompts reset."))
        
    def save_analysis_prompts(self, character_prompt, cultural_prompt, themes_prompt, setting_prompt):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        prompts_to_save = {
            "character_analysis": character_prompt.strip(), "cultural_context": cultural_prompt.strip(),
            "themes_motifs": themes_prompt.strip(), "setting_atmosphere": setting_prompt.strip()
        }
        self.analyzer.set_all_prompts(prompts_to_save)
        self.save_prompts_to_file()
        messagebox.showinfo(lang_texts.get("save_title", "Save"), lang_texts.get("analysis_prompts_saved_message", "Analysis prompts saved."))

    def show_style_guide_prompt_editor(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        self.style_guide_prompt_window_widget = tk.Toplevel(self.root)
        self.style_guide_prompt_window_widget.title(lang_texts.get("edit_style_guide_prompts_title", "Edit Style Guide Prompts"))
        self.style_guide_prompt_window_widget.geometry("800x600") 
        prompt_frame = ttk.Frame(self.style_guide_prompt_window_widget, padding="10")
        prompt_frame.pack(fill=tk.BOTH, expand=True)
        self.style_guide_notebook_widget = ttk.Notebook(prompt_frame)
        self.style_guide_notebook_widget.pack(fill=tk.BOTH, expand=True)
        
        self.style_guide_generation_tab_widget = ttk.Frame(self.style_guide_notebook_widget)
        self.style_guide_update_tab_widget = ttk.Frame(self.style_guide_notebook_widget)
        
        self.style_guide_notebook_widget.add(self.style_guide_generation_tab_widget, text=lang_texts.get("style_guide_generation_tab", "Generation"))
        self.style_guide_notebook_widget.add(self.style_guide_update_tab_widget, text=lang_texts.get("style_guide_update_tab", "Update"))
        
        current_prompts = self.translator.get_all_prompts() # Use get_all_prompts
        
        generation_prompt_text = scrolledtext.ScrolledText(self.style_guide_generation_tab_widget, wrap=tk.WORD, width=80, height=20)
        generation_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        generation_prompt_text.insert(tk.END, current_prompts.get("style_guide_generation", ""))
        
        update_prompt_text = scrolledtext.ScrolledText(self.style_guide_update_tab_widget, wrap=tk.WORD, width=80, height=20)
        update_prompt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        update_prompt_text.insert(tk.END, current_prompts.get("style_guide_update", ""))
        
        button_frame = ttk.Frame(prompt_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.style_guide_prompt_window_widget.export_button = ttk.Button(button_frame, text=lang_texts.get("export_button", "Export"), command=lambda: self.export_style_guide_prompts(generation_prompt_text.get("1.0", tk.END), update_prompt_text.get("1.0", tk.END)))
        self.style_guide_prompt_window_widget.export_button.pack(side=tk.LEFT, padx=5)
        self.style_guide_prompt_window_widget.import_button = ttk.Button(button_frame, text=lang_texts.get("import_button", "Import"), command=lambda: self.import_style_guide_prompts(generation_prompt_text, update_prompt_text))
        self.style_guide_prompt_window_widget.import_button.pack(side=tk.LEFT, padx=5)
        self.style_guide_prompt_window_widget.reset_button = ttk.Button(button_frame, text=lang_texts.get("reset_to_default_button", "Reset Defaults"), command=lambda: self.reset_style_guide_prompts(generation_prompt_text, update_prompt_text))
        self.style_guide_prompt_window_widget.reset_button.pack(side=tk.LEFT, padx=5)
        self.style_guide_prompt_window_widget.save_button = ttk.Button(button_frame, text=lang_texts.get("save_button", "Save"), command=lambda: self.save_style_guide_prompts(generation_prompt_text.get("1.0", tk.END), update_prompt_text.get("1.0", tk.END)))
        self.style_guide_prompt_window_widget.save_button.pack(side=tk.LEFT, padx=5)
        
    def export_style_guide_prompts(self, generation_prompt, update_prompt):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title=lang_texts.get("export_style_guide_prompts_dialog_title", "Export Style Guide Prompts"))
        if file_path:
            # Save all prompts from the translator instance, then update the specific ones
            prompts_to_export = {"all_translator_prompts": self.translator.get_all_prompts()}
            prompts_to_export["all_translator_prompts"]["style_guide_generation"] = generation_prompt.strip()
            prompts_to_export["all_translator_prompts"]["style_guide_update"] = update_prompt.strip()
            with open(file_path, 'w', encoding='utf-8') as f:
                json5.dump(prompts_to_export, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(lang_texts.get("export_title", "Export"), lang_texts.get("style_guide_prompts_exported_message", "Style guide prompts exported."))
        
    def import_style_guide_prompts(self, generation_prompt_text, update_prompt_text):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title=lang_texts.get("import_style_guide_prompts_dialog_title", "Import Style Guide Prompts"))
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json5.load(f)
            prompts_to_load = imported_data.get("all_translator_prompts", {})
            defaults = self.translator.get_all_prompts(default=True)

            generation_prompt_text.delete("1.0", tk.END)
            generation_prompt_text.insert(tk.END, prompts_to_load.get("style_guide_generation", defaults["style_guide_generation"]))
            update_prompt_text.delete("1.0", tk.END)
            update_prompt_text.insert(tk.END, prompts_to_load.get("style_guide_update", defaults["style_guide_update"]))
            
            # Update translator instance
            current_prompts = self.translator.get_all_prompts()
            current_prompts["style_guide_generation"] = prompts_to_load.get("style_guide_generation", defaults["style_guide_generation"])
            current_prompts["style_guide_update"] = prompts_to_load.get("style_guide_update", defaults["style_guide_update"])
            self.translator.set_all_prompts(current_prompts)
            messagebox.showinfo(lang_texts.get("import_title", "Import"), lang_texts.get("style_guide_prompts_imported_message", "Style guide prompts imported."))
        
    def reset_style_guide_prompts(self, generation_prompt_text, update_prompt_text):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        default_prompts = self.translator.get_all_prompts(default=True)
        generation_prompt_text.delete("1.0", tk.END)
        generation_prompt_text.insert(tk.END, default_prompts["style_guide_generation"])
        update_prompt_text.delete("1.0", tk.END)
        update_prompt_text.insert(tk.END, default_prompts["style_guide_update"])
        
        # Reset in translator instance
        current_prompts = self.translator.get_all_prompts()
        current_prompts["style_guide_generation"] = default_prompts["style_guide_generation"]
        current_prompts["style_guide_update"] = default_prompts["style_guide_update"]
        self.translator.set_all_prompts(current_prompts)
        messagebox.showinfo(lang_texts.get("reset_title", "Reset"), lang_texts.get("style_guide_prompts_reset_message", "Style guide prompts reset."))
        
    def save_style_guide_prompts(self, generation_prompt, update_prompt):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        current_prompts = self.translator.get_all_prompts()
        current_prompts["style_guide_generation"] = generation_prompt.strip()
        current_prompts["style_guide_update"] = update_prompt.strip()
        self.translator.set_all_prompts(current_prompts)
        self.save_prompts_to_file()
        messagebox.showinfo(lang_texts.get("save_title", "Save"), lang_texts.get("style_guide_prompts_saved_message", "Style guide prompts saved."))

    def show_style_guide_viewer(self):
        lang_texts = self.ui_texts.get(self.current_app_language, {})
        style_guide = self.translator.style_guide
        # Check if style_guide is not None and has content
        if not style_guide or not any(style_guide.values()): # Handles None or all-empty-values dict
            messagebox.showinfo(lang_texts.get("style_guide_title", "Style Guide"), lang_texts.get("no_style_guide_yet_message", "No style guide has been created or loaded yet."))
            return

        self.style_guide_viewer_window_widget = tk.Toplevel(self.root)
        self.style_guide_viewer_window_widget.title(lang_texts.get("view_style_guide_title", "View Style Guide"))
        self.style_guide_viewer_window_widget.geometry("700x600")
        frame = ttk.Frame(self.style_guide_viewer_window_widget, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        text_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=30, state='normal')
        text_area.pack(fill=tk.BOTH, expand=True)
        try:
            pretty_json = json5.dumps(style_guide, ensure_ascii=False, indent=2)
        except Exception:
            pretty_json = str(style_guide) # Fallback
        text_area.insert(tk.END, pretty_json)
        text_area.config(state='disabled')
        self.style_guide_viewer_window_widget.close_button = ttk.Button(frame, text=lang_texts.get("close_button", "Close"), command=self.style_guide_viewer_window_widget.destroy)
        self.style_guide_viewer_window_widget.close_button.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = NovelTranslatorApp(root)
    root.mainloop()

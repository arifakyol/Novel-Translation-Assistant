import re
import time # Added for sleep
from typing import List, Dict, Tuple, Any # Added Any for type hinting
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import os
from dotenv import load_dotenv
import json5 # json yerine json5 kullanıldı

# Import necessary libraries based on potential AI models
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import openai

class NovelAnalyzer:
    def __init__(self):
        load_dotenv()
        self.ai_model = os.getenv("AI_MODEL", "gemini").lower() # Default to gemini if not set
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.allowed_model = os.getenv("ALLOWED_MODEL", None)

        self.style_guide = {} # This might be removed or changed later if style guide generation moves
        self.detected_language = None
        self.characters = {}
        self.cultural_context = {}
        self.main_themes = {}
        self.setting_atmosphere = {}
        
        # Default promptları sakla
        self.default_character_analysis_prompt = """Aşağıdaki metinde geçen ana ve yan karakterleri tespit et ve her biri için detaylı bir analiz yap.\n\nMetin:\n{text}\n\nLütfen yalnızca aşağıdaki JSON formatında bir dizi olarak yanıt ver. Başka açıklama ekleme:\n\n[\n  {{\n    \"name\": \"Karakter Adı\",\n    \"role\": \"Ana Karakter\" veya \"Yan Karakter\",\n    \"occupation\": \"Karakterin mesleği\",\n    \"nickname\": \"Karakterin lakabı\",\n    \"personality\": [\"cesur\", \"yalnız\", \"manipülatif\"],\n    \"emotions\": [\"öfke\", \"endişe\", \"pişmanlık\"],\n    \"speech_style\": [\"sert\", \"alaycı\", \"resmi\"],\n    \"background\": \"Karakterin geçmişi ve önemli olayları.\",\n    \"motivation\": \"Ne istiyor? Neden bu hikâyede yer alıyor?\",\n    \"conflicts\": [\"içsel çatışma\", \"bir diğer karakterle çatışma\"],\n    \"relationships\": {{\n      \"friends\": [\"isim1\", \"isim2\"],\n      \"enemies\": [\"isim3\"],\n      \"family\": [\"isim4\"],\n      \"romantic\": [\"isim5\"]\n    }},\n    \"development\": {{\n      \"beginning\": [\"nasıldı\"],\n      \"middle\": [\"nasıl değişti\"],\n      \"end\": [\"nasıl sona erdi\"]\n    }},\n    \"arc_type\": \"Klasik\",\n    \"key_dialogues\": [\"...\"],\n    \"key_thoughts\": [\"...\"]\n  }}\n]"""
        self.default_cultural_context_prompt = """Aşağıdaki metnin kültürel bağlamını analiz et.\n        \nMetin:\n{text}\n\nLütfen yalnızca aşağıdaki JSON formatında bir nesne olarak yanıt ver. Başka açıklama ekleme:\n\n{{\n  \"historical_period\": \"Romanın geçtiği tarihsel dönem (örneğin, 19. yüzyıl Osmanlı İmparatorluğu, 20. yüzyıl soğuk savaş dönemi ABD, modern Japonya)\",\n  \"social_norms\": \"Dönemin belirgin sosyal normları ve değerleri (örneğin, aile yapısı, toplumsal hiyerarşiler, ahlaki değerler)\",\n  \"political_climate\": \"Dönemin politik iklimi veya önemli politik olayları (örneğin, savaş sonrası dönem, siyasi çalkantılar, belirli bir hükümet sistemi)\",\n  \"cultural_references\": [\"metindeki önemli kültürel referanslar (örneğin, belirli festivaller, yemekler, giyim tarzları)\"],\n  \"idioms_sayings\": [\"metinde geçen veya o kültüre özgü deyimler, atasözleri, özlü sözler\"],\n  \"specific_customs\": [\"romanda geçen belirli gelenekler, ritüeller veya alışkanlıklar\"],\n  \"language_nuances\": \"Dile özgü ince ayrımlar, argo, şive veya belirli bir sosyal gruba ait dil kullanımı\"\n}}"""
        self.default_themes_motifs_prompt = """Aşağıdaki metnin ana temalarını ve tekrarlayan motiflerini analiz et.\n\nMetin:\n{text}\n\nLütfen yalnızca aşağıdaki JSON formatında bir nesne olarak yanıt ver. Başka açıklama ekleme:\n\n{{\n  \"main_themes\": [\"ana tema 1 (örneğin, aşk, kayıp, intikam)\", \"ana tema 2\"],\n  \"sub_themes\": [\"alt tema 1 (örneğin, aile bağları, yalnızlık)\", \"alt tema 2\"],\n  \"recurring_motifs\": [\"tekrarlayan motif 1 (sembol, nesne, fikir veya görüntü)\", \"tekrarlayan motif 2\"],\n  \"moral_lessons\": [\"romandan çıkarılan ahlaki dersler veya evrensel mesajlar\"]\n}}"""
        self.default_setting_atmosphere_prompt = """Aşağıdaki metnin geçtiği ortamı ve yarattığı atmosferi analiz et.\n\nMetin:\n{text}\n\nLütfen yalnızca aşağıdaki JSON formatında bir nesne olarak yanıt ver. Başka açıklama ekleme:\n\n{{\n  \"main_locations\": [\"ana konum 1 (örneğin, Paris, kırsal bir kasaba, uzay gemisi)\", \"ana konum 2\"],\n  \"time_period\": \"Geçtiği zaman dilimi (örneğin, 1800'ler, günümüz, gelecekteki bir yıl, ortaçağ)\",\n  \"geographical_features\": \"Ortamın belirgin coğrafi özellikleri (örneğin, dağlık arazi, nehir kenarı, çöller, ormanlar)\",\n  \"social_environment\": \"Sosyal çevre ve ortamın toplumsal yapısı (örneğin, aristokrat çevre, fakir mahalle, distopik toplum)\",\n  \"prevailing_atmosphere\": \"Romanın genel atmosferi veya ruh hali (örneğin, gergin, huzurlu, kasvetli, fantastik, gizemli)\",\n  \"key_elements\": [\"atmosfere katkıda bulunan ana unsurlar (örneğin, hava durumu, ışıklandırma, sesler, kokular)\"]\n}}"""
        
        self.character_analysis_prompt = self.default_character_analysis_prompt
        self.cultural_context_prompt = self.default_cultural_context_prompt
        self.themes_motifs_prompt = self.default_themes_motifs_prompt
        self.setting_atmosphere_prompt = self.default_setting_atmosphere_prompt
        
        self._setup_ai_model()
        
    def _setup_ai_model(self):
        """
        Setup the selected AI model (Gemini or OpenAI)
        """
        if self.ai_model == "gemini":
            if not self.gemini_api_key:
                raise ValueError("error_gemini_api_key_not_found")
            genai.configure(api_key=self.gemini_api_key)
            model_name = self.allowed_model if (self.allowed_model and self.ai_model == "gemini") else "gemini-1.5-flash-latest"
            self.model = genai.GenerativeModel(model_name)
            # Güvenlik ayarlarını tanımla: Tüm kategoriler için engellemeyi devre dışı bırak
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            print(f"DEBUG: Using Gemini model for analysis: {model_name}.")
        elif self.ai_model == "chatgpt":
            if not self.openai_api_key:
                raise ValueError("error_openai_api_key_not_found")
            openai.api_key = self.openai_api_key
            model_name = self.allowed_model if (self.allowed_model and self.ai_model == "chatgpt") else "gpt-4o-mini"
            self.model = model_name
            print(f"DEBUG: Using OpenAI model for analysis: {model_name}.")
        else:
            raise ValueError(f"error_unsupported_ai_model:{self.ai_model}")
        
    def _detect_language(self, text: str) -> str:
        """
        Detects the language of the given text.
        """
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"

    def _detect_genre(self, text: str) -> str:
        """
        Detects the genre of the given text (placeholder for now).
        """
        # This is a placeholder. A real implementation would use NLP models.
        # For now, it returns a default or a very basic heuristic.
        if "aşk" in text.lower() or "sevgi" in text.lower():
            return "Romantik"
        elif "cinayet" in text.lower() or "dedektif" in text.lower():
            return "Polisiye"
        elif "uzay" in text.lower() or "robot" in text.lower():
            return "Bilim Kurgu"
        else:
            return "Roman"

    def _analyze_characters(self, text: str) -> Tuple[Dict[str, Dict[str, str]], str | None]:
        """
        Metinden karakterleri tamamen AI kullanarak analiz eder ve her karakter için detaylı bilgi oluşturur.
        """
        prompt = self.character_analysis_prompt.format(text=text)

        try:
            if self.ai_model == "gemini":
                response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
                raw_response_text = response.text.strip()
            elif self.ai_model == "chatgpt":
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"} # İstek JSON formatında yanıt almak için
                )
                raw_response_text = response.choices[0].message.content.strip()

            time.sleep(5) # 5 saniye gecikme eklendi
            
            # Markdown kod bloğu işaretlerini kaldır (her iki model için de olabilir)
            if raw_response_text.startswith('```json') and raw_response_text.endswith('```'):
                raw_response_text = raw_response_text[len('```json'):-len('```')].strip()
            elif raw_response_text.startswith('```') and raw_response_text.endswith('```'):
                 raw_response_text = raw_response_text[len('```'):-len('```')].strip()

            print(f"DEBUG: _analyze_characters Cleaned AI Response (first 500 chars): {raw_response_text[:500]}...") # İlk 500 karakteri logla
            
            if not raw_response_text:
                raise ValueError("error_ai_empty_response")

            try:
                raw_characters_list = json5.loads(raw_response_text) # json yerine json5 kullanıldı
            except json5.Json5Error as json_e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                raise ValueError(f"error_json_decode:{json_e}|{raw_response_text}")
            
            characters_dict = {}
            for char_data in raw_characters_list:
                name = char_data.get("name")
                if name:
                    # AI'dan gelen veriye mention ve notes ekle (varsayılan değerlerle)
                    char_data["mentions"] = text.count(name) # Karakterin metinde geçiş sayısını hesapla
                    char_data["notes"] = char_data.get("notes", "") # AI doğrudan notes vermeyeceği için varsayılan boş string olarak başlat
                    # Meslek ve Lakap için varsayılan değerleri ayarla (eğer AI vermezse)
                    char_data["occupation"] = char_data.get("occupation", "")
                    char_data["nickname"] = char_data.get("nickname", "")

                    characters_dict[name] = char_data
            return characters_dict, None
        except Exception as e:
            error_msg = f"analyzer_char_error_prefix:{str(e)}"
            print(error_msg)
            return {}, error_msg

    def _analyze_cultural_context(self, text: str) -> Tuple[Dict[str, str], str | None]:
        """
        Metinden kültürel bağlamı analiz eder.
        """
        prompt = self.cultural_context_prompt.format(text=text)
        try:
            if self.ai_model == "gemini":
                response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
                raw_response_text = response.text.strip()
            elif self.ai_model == "chatgpt":
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"} # İstek JSON formatında yanıt almak için
                )
                raw_response_text = response.choices[0].message.content.strip()

            time.sleep(5) # 5 saniye gecikme eklendi
            
            # Markdown kod bloğu işaretlerini kaldır (her iki model için de olabilir)
            if raw_response_text.startswith('```json') and raw_response_text.endswith('```'):
                raw_response_text = raw_response_text[len('```json'):-len('```')].strip()
            elif raw_response_text.startswith('```') and raw_response_text.endswith('```'):
                 raw_response_text = raw_response_text[len('```'):-len('```')].strip()

            print(f"DEBUG: _analyze_cultural_context Cleaned AI Response (first 500 chars): {raw_response_text[:500]}...") # İlk 500 karakteri logla

            if not raw_response_text:
                raise ValueError("error_ai_empty_response")

            try:
                cultural_context_data = json5.loads(raw_response_text)
            except json5.Json5Error as json_e:
                raise ValueError(f"error_json_decode:{json_e}|{raw_response_text}")

            return cultural_context_data, None
        except Exception as e:
            error_msg = f"analyzer_cultural_error_prefix:{str(e)}"
            print(error_msg)
            return {}, error_msg

    def _analyze_main_themes_and_motifs(self, text: str) -> Tuple[Dict[str, List[str]], str | None]:
        """
        Metinden ana temaları ve motifleri analiz eder.
        """
        prompt = self.themes_motifs_prompt.format(text=text)
        try:
            if self.ai_model == "gemini":
                response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
                raw_response_text = response.text.strip()
            elif self.ai_model == "chatgpt":
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"} # İstek JSON formatında yanıt almak için
                )
                raw_response_text = response.choices[0].message.content.strip()

            time.sleep(5) # 5 saniye gecikme eklendi
            
            # Markdown kod bloğu işaretlerini kaldır (her iki model için de olabilir)
            if raw_response_text.startswith('```json') and raw_response_text.endswith('```'):
                raw_response_text = raw_response_text[len('```json'):-len('```')].strip()
            elif raw_response_text.startswith('```') and raw_response_text.endswith('```'):
                 raw_response_text = raw_response_text[len('```'):-len('```')].strip()

            print(f"DEBUG: _analyze_main_themes_and_motifs Cleaned AI Response (first 500 chars): {raw_response_text[:500]}...") # İlk 500 karakteri logla

            if not raw_response_text:
                raise ValueError("error_ai_empty_response")

            try:
                themes_motifs_data = json5.loads(raw_response_text)
            except json5.Json5Error as json_e:
                raise ValueError(f"error_json_decode:{json_e}|{raw_response_text}")

            return themes_motifs_data, None
        except Exception as e:
            error_msg = f"analyzer_themes_error_prefix:{str(e)}"
            print(error_msg)
            return {}, error_msg

    def _analyze_setting_and_atmosphere(self, text: str) -> Tuple[Dict[str, str], str | None]:
        """
        Metinden ortam ve atmosferi analiz eder.
        """
        prompt = self.setting_atmosphere_prompt.format(text=text)
        try:
            if self.ai_model == "gemini":
                response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
                raw_response_text = response.text.strip()
            elif self.ai_model == "chatgpt":
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"} # İstek JSON formatında yanıt almak için
                )
                raw_response_text = response.choices[0].message.content.strip()

            time.sleep(5) # 5 saniye gecikme eklendi
            
            # Markdown kod bloğu işaretlerini kaldır (her iki model için de olabilir)
            if raw_response_text.startswith('```json') and raw_response_text.endswith('```'):
                raw_response_text = raw_response_text[len('```json'):-len('```')].strip()
            elif raw_response_text.startswith('```') and raw_response_text.endswith('```'):
                 raw_response_text = raw_response_text[len('```'):-len('```')].strip()

            print(f"DEBUG: _analyze_setting_and_atmosphere Cleaned AI Response (first 500 chars): {raw_response_text[:500]}...") # İlk 500 karakteri logla

            if not raw_response_text:
                raise ValueError("error_ai_empty_response")

            try:
                setting_atmosphere_data = json5.loads(raw_response_text)
            except json5.Json5Error as json_e:
                raise ValueError(f"error_json_decode:{json_e}|{raw_response_text}")

            return setting_atmosphere_data, None
        except Exception as e:
            error_msg = f"analyzer_setting_error_prefix:{str(e)}"
            print(error_msg)
            return {}, error_msg

    def analyze(self, content: str, genre_input: str, characters_input: str, custom_splitter: str = None) -> Tuple[str, List[Dict[str, str]], Dict[str, str], Dict[str, List[str]], Dict[str, str], str | None]:
        """
        Analyze the novel content and break it into sections based on genre and characters.
        Returns a summary and the segmented sections.
        """
        all_errors = []

        # Detect language
        detected_language = self._detect_language(content)
        self.detected_language = detected_language

        # Use pre-defined genre if provided, otherwise detect
        genre = genre_input if genre_input else self._detect_genre(content)

        # Karakter analizi yap (tamamen AI ile)
        self.characters, char_error = self._analyze_characters(content)
        if char_error:
            all_errors.append(char_error)
        
        # Kültürel Bağlam analizi yap
        self.cultural_context, cultural_error = self._analyze_cultural_context(content)
        if cultural_error:
            all_errors.append(cultural_error)

        # Temalar ve Motifler analizi yap
        self.main_themes, themes_error = self._analyze_main_themes_and_motifs(content)
        if themes_error:
            all_errors.append(themes_error)

        # Ortam ve Atmosfer analizi yap
        self.setting_atmosphere, setting_error = self._analyze_setting_and_atmosphere(content)
        if setting_error:
            all_errors.append(setting_error)

        # Segment into sections
        sections = self.get_sections(content, custom_splitter=custom_splitter)

        # Karakter bilgilerini formatla
        character_info = "\n".join([
            f"{char['name']} ({char['role']})"
            for char in self.characters.values()
        ])

        # Kültürel bağlam bilgilerini formatla
        cultural_context_info = "\n".join([f"{k}: {v}" for k, v in self.cultural_context.items()])

        # Temalar ve motifler bilgilerini formatla
        themes_motifs_info = f"Ana Temalar: {', '.join(self.main_themes.get('main_themes', []))}\nAlt Temalar: {', '.join(self.main_themes.get('sub_themes', []))}\nTekrarlayan Motifler: {', '.join(self.main_themes.get('recurring_motifs', []))}\nEtik Dersler: {', '.join(self.main_themes.get('moral_lessons', []))}"

        # Ortam ve atmosfer bilgilerini formatla
        setting_atmosphere_info = "\n".join([f"{k}: {v}" for k, v in self.setting_atmosphere.items()])

        analysis_summary = f"""
Roman Analizi:
Tespit Edilen Dil: {detected_language}
Tespit Edilen Tür: {genre}

Tespit Edilen Karakterler:
{character_info}

Kültürel Bağlam:
{cultural_context_info}

Ana Temalar ve Motifler:
{themes_motifs_info}

Ortam ve Atmosfer:
{setting_atmosphere_info}

Bölüm Sayısı: {len(sections)}
        """
        final_error_message = "\n".join(all_errors) if all_errors else None
        if final_error_message:
            analysis_summary += f"\n\nUYARI: Analiz sırasında bazı hatalar oluştu:\n{final_error_message}"

        return analysis_summary, sections, self.cultural_context, self.main_themes, self.setting_atmosphere, final_error_message

    def get_detected_language(self) -> str:
        """
        Get the detected language of the novel.
        """
        return self.detected_language

    def get_characters(self) -> Dict[str, Dict[str, str]]:
        """
        Get the analyzed characters.
        """
        return self.characters

    def get_cultural_context(self) -> Dict[str, str]:
        """
        Get the analyzed cultural context.
        """
        return self.cultural_context

    def get_main_themes(self) -> Dict[str, List[str]]:
        """
        Get the analyzed main themes and motifs.
        """
        return self.main_themes

    def get_setting_atmosphere(self) -> Dict[str, str]:
        """
        Get the analyzed setting and atmosphere.
        """
        return self.setting_atmosphere

    def get_sections(self, text: str, max_words_per_section: int = 3000, paragraphs_per_sub_section: int = 10, custom_splitter: str = None) -> List[Dict[str, str]]:
        """
        Hibrit bir yaklaşımla metni bölümlere ayırır:
        1. Önce metni "Chapter", "Bölüm", "***" gibi yapısal ayraçlara veya kullanıcı tanımlı bir ayraca göre ana bölümlere ayırır.
        2. Eğer bir ana bölüm belirlenen kelime limitini (max_words_per_section) aşıyorsa,
           o bölümü daha küçük paragraf gruplarına ayırır.
        Tüm bölümler, içeriği ne olursa olsun "novel_section" olarak etiketlenir.
        """
        if not text.strip():
            return []

        # 1. Adım: Metni yapısal ayraçlara göre ana bölümlere ayır.
        if custom_splitter:
            # Kullanıcı özel bir ayraç girdiyse, regex'te güvenli hale getir ve onu kullan.
            splitter_pattern = f'({re.escape(custom_splitter)})'
        else:
            # Varsayılan yapısal ayraçları kullan.
            splitter_pattern = r'(\b(?:chapter|bölüm|kısım|part)\s*\d+\b.*?$|^\s*\*+\s*$|^\s*#+\s*$)'
        
        # re.split ile metni böl, ayraçları da listeye dahil et.
        # re.IGNORECASE -> büyük/küçük harf duyarsız yapar (?i) bayrağı yerine.
        # re.MULTILINE -> ^ ve $'ın her satır için çalışmasını sağlar.
        parts = re.split(splitter_pattern, text, flags=re.MULTILINE | re.IGNORECASE)
        
        main_sections = []
        current_section_content = ""

        # Bölünmüş parçaları birleştirerek ana bölümleri oluştur.
        # parts listesi [metin, ayraç, metin, ayraç, ...] şeklinde gelir.
        for i, part in enumerate(parts):
            if i % 2 == 1: # Bu bir ayraçtır.
                if current_section_content.strip():
                    main_sections.append(current_section_content.strip())
                current_section_content = part # Yeni bölüm ayraçla başlar.
            else: # Bu normal metindir.
                current_section_content += part
        
        if current_section_content.strip():
            main_sections.append(current_section_content.strip())

        # Eğer hiç ayraç bulunamazsa, tüm metni tek bir ana bölüm olarak ele al.
        if not main_sections:
            main_sections.append(text.strip())

        # 2. Adım: Uzun ana bölümleri daha küçük alt bölümlere ayır.
        final_sections = []
        for section_text in main_sections:
            word_count = len(section_text.split())
            
            if word_count <= max_words_per_section:
                # Bölüm yeterince kısaysa, olduğu gibi ekle.
                final_sections.append({"type": "novel_section", "text": section_text})
            else:
                # Bölüm çok uzunsa, paragraf gruplarına ayır.
                paragraphs = re.split(r'\n\s*\n', section_text)
                sub_section_text = ""
                
                for i, para in enumerate(paragraphs):
                    sub_section_text += para + "\n\n"
                    # Belirli sayıda paragrafa ulaşıldığında veya son paragrafta
                    if (i + 1) % paragraphs_per_sub_section == 0 or (i + 1) == len(paragraphs):
                        if sub_section_text.strip():
                            final_sections.append({"type": "novel_section", "text": sub_section_text.strip()})
                        sub_section_text = ""

        return final_sections

    # Prompt güncelleme metodları
    def update_character_analysis_prompt(self, new_prompt: str):
        """Karakter analizi promptunu günceller."""
        self.character_analysis_prompt = new_prompt

    def update_cultural_context_prompt(self, new_prompt: str):
        """Kültürel bağlam analizi promptunu günceller."""
        self.cultural_context_prompt = new_prompt

    def update_themes_motifs_prompt(self, new_prompt: str):
        """Temalar ve motifler analizi promptunu günceller."""
        self.themes_motifs_prompt = new_prompt

    def update_setting_atmosphere_prompt(self, new_prompt: str):
        """Ortam ve atmosfer analizi promptunu günceller."""
        self.setting_atmosphere_prompt = new_prompt

    def get_all_prompts(self, default=False) -> Dict[str, str]:
        """Tüm analiz promptlarını döndürür. default=True ise defaultları döndürür."""
        if default:
            return {
                "character_analysis": self.default_character_analysis_prompt,
                "cultural_context": self.default_cultural_context_prompt,
                "themes_motifs": self.default_themes_motifs_prompt,
                "setting_atmosphere": self.default_setting_atmosphere_prompt
            }
        else:
            return {
                "character_analysis": self.character_analysis_prompt,
                "cultural_context": self.cultural_context_prompt,
                "themes_motifs": self.themes_motifs_prompt,
                "setting_atmosphere": self.setting_atmosphere_prompt
            }

    def set_all_prompts(self, prompts: Dict[str, str]):
        """Tüm analiz promptlarını günceller."""
        if "character_analysis" in prompts:
            self.character_analysis_prompt = prompts["character_analysis"]
        if "cultural_context" in prompts:
            self.cultural_context_prompt = prompts["cultural_context"]
        if "themes_motifs" in prompts:
            self.themes_motifs_prompt = prompts["themes_motifs"]
        if "setting_atmosphere" in prompts:
            self.setting_atmosphere_prompt = prompts["setting_atmosphere"]

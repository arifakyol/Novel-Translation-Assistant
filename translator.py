import re
import time # Added for retry delay
from typing import Dict, List, Tuple, Any
import os
from dotenv import load_dotenv
import json5 # json yerine json5 kullanıldı

# Import necessary libraries based on potential AI models
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import openai

class NovelTranslator:
    def __init__(self, target_country: str = "US"): # API key will be handled internally based on model
        load_dotenv()
        self.target_country = target_country.upper() # Store as uppercase for consistency
        
        self.ai_model = os.getenv("AI_MODEL", "gemini").lower() # Default to gemini if not set
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Stil rehberi başlangıç değerleri kaldırılıyor, AI tarafından oluşturulacak
        self.style_guide = {
            "tone": "",
            "dialogue_style": "",
            "description_style": "",
            "thought_style": "",
            "character_voices": {},
            "consistent_terms": {},
            "cultural_references": {}
        }
        self.translation_memory = {}
        self.translation_stages = []
        self.model = None # Model değişkenini burada tanımla
        self._setup_ai_model()
        
        # Store prompts for editing
        self.initial_prompt = """RESPONSE FORMAT (STRICT):
- Your output MUST INCLUDE ONLY the translated text.
- DO NOT add greetings, summaries, explanations, markdown, or formatting.
- DO NOT include section titles, genre names, character info, or style guide notes.
- The output must be a single, continuous, plain translation.
- DO NOT DEVIATE from this rule.

TASK:
You are a professional literary translator. Translate the following {section_type} from {source_language} into {target_language} for readers in {target_country}.

Focus on:
- Preserving the original **tone**, **style**, and **emotional impact**.
- Ensuring **genre-appropriate phrasing** and **character consistency**.

SOURCE TEXT (in {source_language}):
{original_section_text}

CONTEXT FOR MODEL USE ONLY — DO NOT OUTPUT:
Source Language: {source_language}
Target Language: {target_language}
Target Country: {target_country}
Genre: {genre}
Character Info:
{formatted_characters_for_prompt}
Cultural Context:
{formatted_cultural_context_for_prompt}
Main Themes and Motifs:
{formatted_themes_motifs_for_prompt}
Setting and Atmosphere:
{formatted_setting_atmosphere_for_prompt}
Style Guide:
{style_guide_text}

⚠️ DO NOT INCLUDE ANY PART OF THE CONTEXT ABOVE IN YOUR OUTPUT. 
YOUR RESPONSE MUST BEGIN WITH THE FIRST WORD OF THE TRANSLATION AND END WITH THE LAST WORD OF THE TRANSLATION. 

---BEGIN TRANSLATED TEXT---"""
        
        self.line_edit_prompt = """RESPONSE FORMAT (STRICT):
- Your output MUST CONTAIN ONLY the edited text.
- DO NOT include explanations, greetings, summaries, markdown, metadata, or any other additional content.
- The output must be a single, clean, continuous edited version of the input translation.
- DO NOT DEVIATE from these instructions under any circumstances.

TASK:
You are a professional line editor for literary fiction. Refine the translated text below, which was translated from {source_language} into {target_language}, for readers in {target_country}.

Focus on improving:
- Flow and sentence rhythm
- Readability and clarity
- Grammar and punctuation

While preserving:
- The original meaning
- Literary tone and atmosphere
- Character voice and emotional consistency
- Conformity with the provided style guide

REFERENCE TEXT (DO NOT OUTPUT):
{original_section_text}

TEXT TO EDIT:
{initial_translation}

CONTEXT FOR MODEL USE ONLY — DO NOT OUTPUT:
Source Language: {source_language}
Target Language: {target_language}
Target Country: {target_country}
Genre: {genre}
Key Characters:
{formatted_characters_for_prompt}
Cultural Context:
{formatted_cultural_context_for_prompt}
Main Themes and Motifs:
{formatted_themes_motifs_for_prompt}
Setting and Atmosphere:
{formatted_setting_atmosphere_for_prompt}
Style Guide:
{style_guide_text}

⚠️ DO NOT INCLUDE ANY PART OF THE CONTEXT ABOVE IN YOUR OUTPUT.
YOUR RESPONSE MUST BEGIN WITH THE FIRST WORD OF THE EDITED TEXT AND END WITH THE LAST WORD OF THE EDITED TEXT.

---BEGIN EDITED TEXT---"""
        
        self.cultural_prompt = """RESPONSE FORMAT (STRICT):
- Your output MUST CONTAIN ONLY the culturally localized text.
- DO NOT include introductions, explanations, greetings, summaries, markdown, or any other content.
- DO NOT DEVIATE from these instructions under any circumstances.

TASK:
You are a professional expert in cultural adaptation for literary fiction. Adapt the following translated text, which was translated from {source_language} into {target_language}, so that it feels natural, relatable, and resonant for {target_language} readers in {target_country} — while preserving the original cultural identity, context, and emotional authenticity.

Make minimal, necessary adjustments:
- Clarify or adapt culturally specific references, idioms, or names only if comprehension would otherwise be hindered.
- Avoid over-domestication, excessive Anglicization or Americanization unless essential for clarity.
- Do not Westernize the text unless the original intent requires it.

Preserve:
- Narrative structure and flow
- Original intent and message
- Character voice and emotional tone
- Literary and stylistic consistency per the provided style guide

REFERENCE TEXT (DO NOT OUTPUT):
{original_section_text}

TEXT TO LOCALIZE:
{line_edited}

CONTEXT FOR MODEL USE ONLY — DO NOT OUTPUT:
Source Language: {source_language}
Target Language: {target_language}
Target Country: {target_country}
Genre: {genre}
Key Characters:
{formatted_characters_for_prompt}
Cultural Context:
{formatted_cultural_context_for_prompt}
Main Themes and Motifs:
{formatted_themes_motifs_for_prompt}
Setting and Atmosphere:
{formatted_setting_atmosphere_for_prompt}
Style Guide:
{style_guide_text}

⚠️ DO NOT INCLUDE ANY PART OF THE CONTEXT ABOVE IN YOUR OUTPUT.
YOUR RESPONSE MUST BEGIN WITH THE FIRST WORD OF THE LOCALIZED TEXT AND END WITH THE LAST WORD OF THE LOCALIZED TEXT.

---BEGIN LOCALIZED TEXT---"""
        
    def _setup_ai_model(self):
        """
        Setup the selected AI model (Gemini or ChatGPT)
        """
        if self.ai_model == "gemini":
            self._setup_gemini()
        elif self.ai_model == "chatgpt":
            self._setup_openai()
        else:
            raise ValueError(f"Unsupported AI model: {self.ai_model}. Choose 'gemini' or 'chatgpt'.")

    def _setup_gemini(self):
        """
        Setup Gemini API with the provided API key
        """
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest') # Use a more recent model
        
        # Güvenlik ayarlarını tanımla: Tüm kategoriler için engellemeyi devre dışı bırak
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        print("DEBUG: Gemini model setup complete.")

    def _setup_openai(self):
        """
        Setup OpenAI API with the provided API key
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")

        openai.api_key = self.openai_api_key
        self.model = "gpt-4o-mini" # Use a suitable OpenAI model
        print("DEBUG: OpenAI model setup complete.")

    def set_initial_character_info(self, characters_str):
        """
        Bu metot artık kullanılmayacak, karakter bilgileri doğrudan AI analizinden gelecek.
        """
        pass

    def generate_style_guide_with_ai(self, genre: str, characters_data: Dict[str, Any], cultural_context_data: Dict[str, Any], main_themes_data: Dict[str, Any], setting_atmosphere_data: Dict[str, Any], source_language: str, target_language: str, target_country: str, progress_callback=None, max_retries: int = 3, retry_delay: int = 5):
        """
        NovelAnalyzer'dan gelen verileri kullanarak stil rehberinin ilk taslağını yapay zeka ile oluşturur.
        Hata durumunda belirtilen sayıda yeniden deneme yapar.
        """
        if progress_callback: progress_callback("Stil Rehberi AI ile oluşturuluyor...\n")
        print("DEBUG: generate_style_guide_with_ai called for initial draft.")

        formatted_characters = self._format_characters_for_prompt(characters_data)
        formatted_cultural_context = self._format_cultural_context_for_prompt(cultural_context_data)
        formatted_themes_motifs = self._format_themes_motifs_for_prompt(main_themes_data)
        formatted_setting_atmosphere = self._format_setting_atmosphere_for_prompt(setting_atmosphere_data)

        prompt = f"""
Sen profesyonel bir edebi çevirmensin. Aşağıdaki roman analizi verilerine dayanarak, {source_language} dilinden {target_language} diline, {target_country} ülkesindeki okuyucular için bu romanın çevirisi için kapsamlı bir stil rehberi oluştur. Bu, çeviri sürecinin başlangıcında oluşturulan ilk taslak stil rehberidir.

Stil rehberi, çevirinin tutarlılığını ve kalitesini sağlamak için kullanılacaktır. Özellikle aşağıdaki alanlara odaklan:
- Genel Ton (örneğin, resmi, samimi, epik, mizahi, kasvetli)
- Diyalog Stili (örneğin, doğal, resmi, argo kullanımı, karakterlere özgü konuşma tarzları)
- Açıklama Stili (örneğin, detaylı, minimalist, şiirsel, nesnel)
- Düşünce Stili (örneğin, içe dönük, akışkan, kesik kesik)
- Karakter Sesleri (her ana karakter için ayrı ayrı, konuşma tarzları, kelime dağarcığı, resmiyet seviyesi)
- Tutarlı Terimler (romanda sık geçen özel isimler, yerler, kavramlar ve bunların çeviride nasıl ele alınacağı)
- Kültürel Referanslar (romandaki kültürel öğelerin çeviride nasıl korunacağı veya adapte edileceği)

Lütfen yalnızca aşağıdaki JSON formatında bir nesne olarak yanıt ver. Başka açıklama ekleme:

{{
  "tone": "Genel roman tonu",
  "dialogue_style": "Diyalogların genel stili",
  "description_style": "Açıklamaların genel stili",
  "thought_style": "Düşüncelerin genel stili",
  "character_voices": {{
    "Karakter Adı 1": {{
      "formality": "resmi/samimi/nötr",
      "vocabulary": "geniş/sınırlı/argo",
      "speech_patterns": ["kısa cümleler", "uzun betimlemeler", "alaycı ton"]
    }},
    "Karakter Adı 2": {{
      "formality": "resmi/samimi/nötr",
      "vocabulary": "geniş/sınırlı/argo",
      "speech_patterns": ["kısa cümleler", "uzun betimlemeler", "alaycı ton"]
    }}
  }},
  "consistent_terms": {{
    "Orijinal Terim 1": "Çevrilmiş Terim 1",
    "Orijinal Terim 2": "Çevrilmiş Terim 2"
  }},
  "cultural_references": {{
    "Orijinal Referans 1": "Çevirideki Yaklaşım/Açıklama",
    "Orijinal Referans 2": "Çevirideki Yaklaşım/Açıklama"
  }}
}}

ROMAN ANALİZİ VERİLERİ:
Kaynak Dil: {source_language}
Hedef Dil: {target_language}
Hedef Ülke: {target_country}
Tür: {genre}
Karakter Bilgisi:
{formatted_characters}
Kültürel Bağlam:
{formatted_cultural_context}
Ana Temalar ve Motifler:
{formatted_themes_motifs}
Ortam ve Atmosfer:
{formatted_setting_atmosphere}
"""
        for attempt in range(max_retries):
            try:
                if progress_callback: progress_callback(f"  - Stil Rehberi oluşturuluyor (Deneme {attempt + 1}/{max_retries})...\n")

                if self.ai_model == "gemini":
                    response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
                    raw_response_text = response.text.strip()
                elif self.ai_model == "chatgpt":
                    # Ensure self.model is set for OpenAI
                    if not self.model:
                         raise ValueError("OpenAI model not set up.")
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


                print(f"DEBUG: generate_style_guide_with_ai Cleaned AI Response (first 500 chars): {raw_response_text[:500]}...")

                if not raw_response_text:
                    raise ValueError("AI'dan boş veya sadece boşluk içeren yanıt alındı.")

                try:
                    ai_generated_style_guide = json5.loads(raw_response_text)
                    self.style_guide.update(ai_generated_style_guide)
                    print("DEBUG: Style guide successfully generated and updated from AI.")
                    if progress_callback: progress_callback("Stil Rehberi AI tarafından başarıyla oluşturuldu.\n")
                    return # Başarılı olursa döngüden çık
                except json5.Json5Error as json_e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                    if progress_callback: progress_callback(f"Stil Rehberi oluşturma hatası: AI yanıtı geçerli JSON değil: {json_e}\n")
                    raise ValueError(f"AI yanıtı geçerli JSON değil: {json_e}. Ham yanıt: {raw_response_text}")

            except Exception as e:
                error_message = f"Stil rehberi oluşturma hatası (Deneme {attempt + 1}/{max_retries}): {str(e)}"
                # Gemini'ye özgü hata detaylarını ekle
                if self.ai_model == "gemini" and hasattr(e, 'response') and e.response and hasattr(e.response, 'prompt_feedback') and e.response.prompt_feedback:
                    feedback = e.response.prompt_feedback
                    if feedback.block_reason:
                        error_message += f" (Engelleme Nedeni: {feedback.block_reason.name})"
                    if feedback.safety_ratings:
                        safety_info = "; ".join([f"{sr.category.name}: {sr.probability.name}" for sr in feedback.safety_ratings])
                        error_message += f" (Güvenlik Derecelendirmeleri: {safety_info})"
                # OpenAI'ye özgü hata detaylarını ekle (gerekiyorsa)
                # if self.ai_model == "chatgpt" and hasattr(e, 'response') and e.response:
                #     error_message += f" (OpenAI Hata Detayı: {e.response})"

                print(error_message)
                if progress_callback: progress_callback(f"{error_message}\n")
                if attempt < max_retries - 1:
                    print(f"Yeniden deneniyor {retry_delay} saniye içinde...")
                    time.sleep(retry_delay)
                else:
                    print(f"Stil rehberi oluşturma için maksimum yeniden deneme sayısına ulaşıldı. Varsayılan stil rehberi kullanılıyor.")
                    # Hata durumunda varsayılan veya boş bir stil rehberi ile devam et
                    self.style_guide = {
                        "tone": "neutral",
                        "dialogue_style": "natural",
                        "description_style": "standard",
                        "thought_style": "clear",
                        "character_voices": {},
                        "consistent_terms": {},
                        "cultural_references": {}
                    }

    def update_style_guide(self, original_text: str, translated_text: str, genre: str, characters_data: Dict[str, Any], cultural_context_data: Dict[str, Any], main_themes_data: Dict[str, Any], setting_atmosphere_data: Dict[str, Any], source_language: str, target_language: str, target_country: str, progress_callback=None, max_retries: int = 3, retry_delay: int = 5):
        """
        Çevrilen her bölümden sonra stil rehberini dinamik olarak günceller.
        Orijinal metin ve çevrilen metin arasındaki ilişkileri öğrenir.
        Hata durumunda belirtilen sayıda yeniden deneme yapar.
        """
        if progress_callback: progress_callback("Stil Rehberi dinamik olarak güncelleniyor...\n")
        print(f"DEBUG: update_style_guide called for dynamic update.")

        # Mevcut stil rehberini JSON string'e dönüştür
        current_style_guide_json = json5.dumps(self.style_guide, ensure_ascii=False, indent=2)

        # Karakter verilerini prompt için formatla
        formatted_characters = self._format_characters_for_prompt(characters_data)
        formatted_cultural_context = self._format_cultural_context_for_prompt(cultural_context_data)
        formatted_themes_motifs = self._format_themes_motifs_for_prompt(main_themes_data)
        formatted_setting_atmosphere = self._format_setting_atmosphere_for_prompt(setting_atmosphere_data)

        prompt = f"""
Sen profesyonel bir edebi çevirmensin. Amacın, {source_language} dilinden {target_language} diline, {target_country} ülkesindeki okuyucular için çevirinin mümkün olduğunca doğal, akıcı ve kültürel olarak uygun gelmesini sağlamaktır. Aşağıdaki orijinal metin ve onun çevirisi ile birlikte mevcut stil rehberini incele. Bu bilgilere dayanarak, stil rehberini daha da geliştir ve güncelle. Özellikle karakter sesleri, tutarlı terimler, kültürel referanslar ve genel ton/stil gibi alanlara odaklan.

**Önemli Not: Tutarlı Terimler ve Kültürel Referanslar için, sadece birebir çeviri veya orijinalini koruma yerine, hedef dildeki en doğal, kültürel olarak eşdeğer veya açıklayıcı yaklaşımları belirle.** Örneğin, bir rütbe veya unvan için hedef dildeki en yakın ve anlaşılır karşılığı bul, veya bir kültürel öğe için kısa bir açıklama veya adaptasyon öner.

Lütfen yalnızca güncellenmiş stil rehberini aşağıdaki JSON formatında bir nesne olarak yanıt ver. Başka açıklama ekleme:

{{
  "tone": "Genel roman tonu",
  "dialogue_style": "Diyalogların genel stili",
  "description_style": "Açıklamaların genel stili",
  "thought_style": "Düşüncelerin genel stili",
  "character_voices": {{
    "Karakter Adı 1": {{
      "formality": "resmi/samimi/nötr",
      "vocabulary": "geniş/sınırlı/argo",
      "speech_patterns": ["kısa cümleler", "uzun betimlemeler", "alaycı ton"]
    }},
    "Karakter Adı 2": {{
      "formality": "resmi/samimi/nötr",
      "vocabulary": "geniş/sınırlı/argo",
      "speech_patterns": ["kısa cümleler", "uzun betimlemeler", "alaycı ton"]
    }}
  }},
  "consistent_terms": {{
    "Orijinal Terim 1": "Çevrilmiş Terim 1 (Hedef dildeki en doğal ve anlaşılır karşılığı, gerekirse kısa açıklama)",
    "Orijinal Terim 2": "Çevrilmiş Terim 2 (Hedef dildeki en doğal ve anlaşılır karşılığı, gerekirse kısa açıklama)"
  }},
  "cultural_references": {{
    "Orijinal Referans 1": "Çevirideki Yaklaşım/Açıklama (Hedef kültüre nasıl uyarlanmalı veya açıklanmalı)",
    "Orijinal Referans 2": "Çevirideki Yaklaşım/Açıklama (Hedef kültüre nasıl uyarlanmalı veya açıklanmalı)"
  }}
}}

MEVCUT STİL REHBERİ:
{current_style_guide_json}

ROMAN ANALİZİ VERİLERİ:
Kaynak Dil: {source_language}
Hedef Dil: {target_language}
Hedef Ülke: {target_country}
Tür: {genre}
Karakter Bilgisi:
{formatted_characters}
Kültürel Bağlam:
{formatted_cultural_context}
Ana Temalar ve Motifler:
{formatted_themes_motifs}
Ortam ve Atmosfer:
{formatted_setting_atmosphere}

ORİJİNAL METİN:
{original_text}

ÇEVRİLEN METİN:
{translated_text}
"""
        for attempt in range(max_retries):
            try:
                if progress_callback: progress_callback(f"  - Stil Rehberi güncelleniyor (Deneme {attempt + 1}/{max_retries})...\n")

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

                print(f"DEBUG: update_style_guide Cleaned AI Response (first 500 chars): {raw_response_text[:500]}...")

                if not raw_response_text:
                    raise ValueError("AI'dan boş veya sadece boşluk içeren yanıt alındı.")

                try:
                    ai_updated_style_guide = json5.loads(raw_response_text)
                    self.style_guide.update(ai_updated_style_guide)
                    print("DEBUG: Style guide successfully updated from AI.")
                    if progress_callback: progress_callback("Stil Rehberi AI tarafından başarıyla güncellendi.\n")
                    return # Başarılı olursa döngüden çık
                except json5.Json5Error as json_e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                    print(f"AI yanıtı geçerli JSON değil: {json_e}. Ham yanıt: {raw_response_text}")
                    if progress_callback: progress_callback(f"Stil Rehberi güncelleme hatası: AI yanıtı geçerli JSON değil: {json_e}\n")
                    raise ValueError(f"AI yanıtı geçerli JSON değil: {json_e}. Ham yanıt: {raw_response_text}")

            except Exception as e:
                # Hata mesajını daha spesifik hale getir
                error_message = f"Stil rehberi güncelleme hatası (Deneme {attempt + 1}/{max_retries}): {str(e)}"
                # Gemini'ye özgü hata detaylarını ekle
                if self.ai_model == "gemini" and hasattr(e, 'response') and e.response and hasattr(e.response, 'prompt_feedback') and e.response.prompt_feedback:
                    feedback = e.response.prompt_feedback
                    if feedback.block_reason:
                        error_message += f" (Engelleme Nedeni: {feedback.block_reason.name})"
                    if feedback.safety_ratings:
                        safety_info = "; ".join([f"{sr.category.name}: {sr.probability.name}" for sr in feedback.safety_ratings])
                        error_message += f" (Güvenlik Derecelendirmeleri: {safety_info})"
                # OpenAI'ye özgü hata detaylarını ekle (gerekiyorsa)
                # if self.ai_model == "chatgpt" and hasattr(e, 'response') and e.response:
                #     error_message += f" (OpenAI Hata Detayı: {e.response})"
                print(error_message)
                if progress_callback: progress_callback(f"{error_message}\n")
                if attempt < max_retries - 1:
                    print(f"Yeniden deneniyor {retry_delay} saniye içinde...")
                    time.sleep(retry_delay)
                else:
                    print(f"Stil rehberi güncelleme için maksimum yeniden deneme sayısına ulaşıldı. Mevcut stil rehberi korunuyor.")
                    # Hata durumunda mevcut stil rehberini koru
                    pass

    def translate_section(self, section_data: Dict[str, str], genre: str, characters_json_str: str, cultural_context_json_str: str, main_themes_json_str: str, setting_atmosphere_json_str: str, source_language: str, target_language: str = "en", target_country: str = "US", progress_callback=None, stop_event=None, max_retries=3, retry_delay=5) -> Tuple[str, List[str]]:
        original_section_text = section_data["text"]
        section_type = section_data["type"]
        stages = []

        # Debug için JSON string'leri yazdır
        print("DEBUG: characters_json_str:", characters_json_str)
        print("DEBUG: cultural_context_json_str:", cultural_context_json_str)
        print("DEBUG: main_themes_json_str:", main_themes_json_str)
        print("DEBUG: setting_atmosphere_json_str:", setting_atmosphere_json_str)

        # Karakter bilgilerini JSON string'den parse et
        parsed_characters = {}
        if characters_json_str:
            try:
                parsed_characters = json5.loads(characters_json_str)
                print("DEBUG: Successfully parsed characters JSON")
            except json5.Json5Error as e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                print(f"Karakter bilgileri parse hatası: {e}")
                print(f"Problematic JSON string: {characters_json_str}")

        # Kültürel bağlam bilgilerini JSON string'den parse et
        parsed_cultural_context = {}
        if cultural_context_json_str:
            try:
                parsed_cultural_context = json5.loads(cultural_context_json_str)
            except json5.Json5Error as e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                print(f"Kültürel bağlam bilgileri parse hatası: {e}")

        # Ana temalar ve motifler bilgilerini JSON string'den parse et
        parsed_main_themes = {}
        if main_themes_json_str:
            try:
                parsed_main_themes = json5.loads(main_themes_json_str)
            except json5.Json5Error as e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                print(f"Ana temalar ve motifler bilgileri parse hatası: {e}")

        # Ortam ve atmosfer bilgilerini JSON string'den parse et
        parsed_setting_atmosphere = {}
        if setting_atmosphere_json_str:
            try:
                parsed_setting_atmosphere = json5.loads(setting_atmosphere_json_str)
            except json5.Json5Error as e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                print(f"Ortam ve atmosfer bilgileri parse hatası: {e}")

        # Stil rehberini AI ile oluştur (sadece bir kez, ilk çeviri çağrısında veya analizden sonra)
        # Bu çağrı, NovelTranslatorApp'teki analyze_novel metodunda yapılmalı.
        # Burada sadece stil rehberinin mevcut olduğundan emin olmalıyız.
        # Bu kısım kaldırılacak, çünkü generate_style_guide_with_ai analyze_novel'da çağrılıyor.
        # if not self.style_guide["tone"]:
        #    pass

        # Format style guide as text instead of JSON
        style_guide_text = "Tone: {}\n".format(self.style_guide.get("tone", "Belirtilmemiş"))
        style_guide_text += "Dialogue Style: {}\n".format(self.style_guide.get("dialogue_style", "Belirtilmemiş"))
        style_guide_text += "Description Style: {}\n".format(self.style_guide.get("description_style", "Belirtilmemiş"))
        style_guide_text += "Thought Style: {}\n".format(self.style_guide.get("thought_style", "Belirtilmemiş"))

        if self.style_guide["character_voices"]:
            style_guide_text += "\nCharacter Voices:\n"
            for char, voice in self.style_guide["character_voices"].items():
                speech_patterns = ", ".join(voice.get("speech_patterns", []))
                formality = voice.get("formality", "nötr")
                vocabulary = voice.get("vocabulary", "standart")
                style_guide_text += f"- {char}: Resmiyet: {formality}, Kelime Dağarcığı: {vocabulary}, Konuşma Tarzı: [{speech_patterns}]\n"

        if self.style_guide["consistent_terms"]:
            style_guide_text += "\nConsistent Terms:\n"
            for term, translation in self.style_guide["consistent_terms"].items():
                style_guide_text += f"- {term}: {translation if translation else 'Çevrilmemiş'}\n"

        if self.style_guide["cultural_references"]:
            style_guide_text += "\nCultural References:\n"
            for ref, approach in self.style_guide["cultural_references"].items():
                style_guide_text += f"- {ref}: {approach if approach else 'Yaklaşım Belirtilmemiş'}\n"

        # Debug için style guide'ı yazdır
        print("DEBUG: Style Guide before prompt formatting:")
        print(style_guide_text)

        # Karakter bilgilerini prompt için formatla
        formatted_characters_for_prompt = self._format_characters_for_prompt(parsed_characters)
        formatted_cultural_context_for_prompt = self._format_cultural_context_for_prompt(parsed_cultural_context)
        formatted_themes_motifs_for_prompt = self._format_themes_motifs_for_prompt(parsed_main_themes)
        formatted_setting_atmosphere_for_prompt = self._format_setting_atmosphere_for_prompt(parsed_setting_atmosphere)

        for attempt in range(max_retries):
            try:
                if stop_event and stop_event.is_set():
                    if progress_callback: progress_callback("Translation stopped by user.\n")
                    return original_section_text, stages

                # Stage 1: Initial Translation
                if progress_callback: progress_callback(f"  - Translating {section_type} (Initial Translation) - Attempt {attempt + 1}/{max_retries}...\n")

                initial_prompt = self.initial_prompt.format(
                    section_type=section_type,
                    source_language=source_language, # Add source_language here
                    target_language=target_language,
                    target_country=target_country,
                    original_section_text=original_section_text,
                    formatted_characters_for_prompt=formatted_characters_for_prompt,
                    formatted_cultural_context_for_prompt=formatted_cultural_context_for_prompt,
                    formatted_themes_motifs_for_prompt=formatted_themes_motifs_for_prompt,
                    formatted_setting_atmosphere_for_prompt=formatted_setting_atmosphere_for_prompt,
                    genre=genre,
                    style_guide_text=style_guide_text
                )

                if self.ai_model == "gemini":
                    initial_response = self.model.generate_content(initial_prompt, safety_settings=self.safety_settings)
                    initial_translation = self._extract_response_text(initial_response, "Initial Translation", progress_callback)
                elif self.ai_model == "chatgpt":
                    # Ensure self.model is set for OpenAI
                    if not self.model:
                         raise ValueError("OpenAI model not set up.")
                    initial_response = openai.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": initial_prompt}]
                    )
                    initial_translation = initial_response.choices[0].message.content.strip()


                time.sleep(5) # 5 saniye gecikme eklendi
                print(f"DEBUG: Initial model response parts: {initial_response.parts if self.ai_model == 'gemini' else initial_response.choices[0].message.content[:200]}...") # Log based on model
                print(f"DEBUG: Extracted initial translation: {initial_translation[:200]}...")
                stages.append(f"Initial Translation:\n{initial_translation}\n")

                if stop_event and stop_event.is_set():
                    if progress_callback: progress_callback("Translation stopped by user.\n")
                    return original_section_text, stages

                # Stage 2: Line Editing
                if progress_callback: progress_callback(f"  - Translating {section_type} (Line Editing) - Attempt {attempt + 1}/{max_retries}...\n")
                line_edit_prompt = self.line_edit_prompt.format(
                    section_type=section_type,
                    source_language=source_language, # Add source_language here
                    target_language=target_language,
                    target_country=target_country,
                    original_section_text=original_section_text,
                    formatted_characters_for_prompt=formatted_characters_for_prompt,
                    formatted_cultural_context_for_prompt=formatted_cultural_context_for_prompt,
                    formatted_themes_motifs_for_prompt=formatted_themes_motifs_for_prompt,
                    formatted_setting_atmosphere_for_prompt=formatted_setting_atmosphere_for_prompt,
                    genre=genre,
                    initial_translation=initial_translation,
                    style_guide_text=style_guide_text
                )

                if self.ai_model == "gemini":
                    line_edit_response = self.model.generate_content(line_edit_prompt, safety_settings=self.safety_settings)
                    line_edited = self._extract_response_text(line_edit_response, "Line Editing", progress_callback)
                elif self.ai_model == "chatgpt":
                    # Ensure self.model is set for OpenAI
                    if not self.model:
                         raise ValueError("OpenAI model not set up.")
                    line_edit_response = openai.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": line_edit_prompt}]
                    )
                    line_edited = line_edit_response.choices[0].message.content.strip()

                time.sleep(5) # 5 saniye gecikme eklendi
                print(f"DEBUG: Line edit model response parts: {line_edit_response.parts if self.ai_model == 'gemini' else line_edit_response.choices[0].message.content[:200]}...") # Log based on model
                print(f"DEBUG: Extracted line edit translation: {line_edited[:200]}...")
                stages.append(f"Line Editing:\n{line_edited}\n")

                if stop_event and stop_event.is_set():
                    if progress_callback: progress_callback("Translation stopped by user.\n")
                    return original_section_text, stages

                # Stage 3: Cultural Localization
                if progress_callback: progress_callback(f"  - Translating {section_type} (Cultural Localization) - Attempt {attempt + 1}/{max_retries}...\n")
                cultural_prompt = self.cultural_prompt.format(
                    section_type=section_type,
                    source_language=source_language, # Add source_language here
                    target_language=target_language,
                    target_country=target_country,
                    original_section_text=original_section_text,
                    formatted_characters_for_prompt=formatted_characters_for_prompt,
                    formatted_cultural_context_for_prompt=formatted_cultural_context_for_prompt,
                    formatted_themes_motifs_for_prompt=formatted_themes_motifs_for_prompt,
                    formatted_setting_atmosphere_for_prompt=formatted_setting_atmosphere_for_prompt,
                    genre=genre,
                    line_edited=line_edited,
                    style_guide_text=style_guide_text
                )

                if self.ai_model == "gemini":
                    cultural_response = self.model.generate_content(cultural_prompt, safety_settings=self.safety_settings)
                    final_translation = self._extract_response_text(cultural_response, "Cultural Localization", progress_callback)
                elif self.ai_model == "chatgpt":
                    # Ensure self.model is set for OpenAI
                    if not self.model:
                         raise ValueError("OpenAI model not set up.")
                    cultural_response = openai.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": cultural_prompt}]
                    )
                    final_translation = cultural_response.choices[0].message.content.strip()

                time.sleep(5) # 5 saniye gecikme eklendi
                print(f"DEBUG: Cultural localization model response parts: {cultural_response.parts if self.ai_model == 'gemini' else cultural_response.choices[0].message.content[:200]}...") # Log based on model
                print(f"DEBUG: Extracted final translation: {final_translation[:200]}...")
                stages.append(f"Cultural Localization:\n{final_translation}\n")
                
                # Stil rehberini çevrilen metinle dinamik olarak güncelle
                self.update_style_guide(
                    original_section_text,
                    final_translation,
                    genre,
                    parsed_characters,
                    parsed_cultural_context,
                    parsed_main_themes,
                    parsed_setting_atmosphere,
                    source_language, # Kaynak dil
                    target_language, # Hedef dil
                    target_country, # Hedef ülke
                    progress_callback=progress_callback,
                    max_retries=max_retries # Arayüzden gelen max_retries değerini ilet
                )
                print(f"DEBUG: Dynamic style guide update completed for section type '{section_type}'.")
                
                return final_translation, stages
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"  - Section translation error (Attempt {attempt + 1}/{max_retries}): {str(e)}\n")
                print(f"Section translation error (Attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Max retries reached for section. Returning original text.")
        return original_section_text, stages

    def _format_characters_for_prompt(self, characters_data: Dict[str, Dict[str, str]]) -> str:
        """
        Karakter verilerini AI prompt'una uygun, okunabilir bir string formatına dönüştürür.
        """
        if not characters_data:
            return "Karakter bilgisi mevcut değil."

        formatted_list = []
        for char_name, details in characters_data.items():
            role = details.get("role", "Bilinmiyor")
            personality = ", ".join(details.get("personality", []))
            emotions = ", ".join(details.get("emotions", []))
            speech_style = ", ".join(details.get("speech_style", []))
            occupation = details.get("occupation", "")
            nickname = details.get("nickname", "")
            motivation = details.get("motivation", "")
            conflicts = ", ".join(details.get("conflicts", []))
            arc_type = details.get("arc_type", "Klasik")

            char_str = f"- İsim: {char_name}, Rol: {role}"
            if occupation: char_str += f", Meslek: {occupation}"
            if nickname: char_str += f", Lakap: {nickname}"
            if personality: char_str += f", Kişilik: {personality}"
            if emotions: char_str += f", Duygular: {emotions}"
            if speech_style: char_str += f", Konuşma Tarzı: {speech_style}"
            if motivation: char_str += f", Motivasyon: {motivation}"
            if conflicts: char_str += f", Çatışmalar: {conflicts}"
            if arc_type: char_str += f", Karakter Yay Tipi: {arc_type}"

            # İlişkileri ekle
            relationships = details.get("relationships", {})
            rel_parts = []
            if relationships.get("friends"): rel_parts.append(f"Arkadaşlar: {', '.join(relationships['friends'])}")
            if relationships.get("enemies"): rel_parts.append(f"Düşmanlar: {', '.join(relationships['enemies'])}")
            if relationships.get("family"): rel_parts.append(f"Aile: {', '.join(relationships['family'])}")
            if relationships.get("romantic"): rel_parts.append(f"Romantik: {', '.join(relationships['romantic'])}")
            if rel_parts: char_str += f", İlişkiler: ({'; '.join(rel_parts)})"

            # Gelişimi ekle
            development = details.get("development", {})
            dev_parts = []
            if development.get("beginning"): dev_parts.append(f"Başlangıç: {', '.join(development['beginning'])}")
            if development.get("middle"): dev_parts.append(f"Orta: {', '.join(development['middle'])}")
            if development.get("end"): dev_parts.append(f"Son: {', '.join(development['end'])}")
            if dev_parts: char_str += f", Gelişim: ({'; '.join(dev_parts)})"

            # Anahtar diyaloglar ve düşünceler
            key_dialogues = details.get("key_dialogues", [])
            key_thoughts = details.get("key_thoughts", [])
            if key_dialogues: char_str += f", Diyalog Örnekleri: [{'; '.join(key_dialogues)}]"
            if key_thoughts: char_str += f", Düşünce Örnekleri: [{'; '.join(key_thoughts)}]"

            formatted_list.append(char_str)

        return "\n".join(formatted_list)

    def _format_cultural_context_for_prompt(self, cultural_context_data: Dict[str, Any]) -> str:
        """
        Kültürel bağlam verilerini AI prompt'una uygun, okunabilir bir string formatına dönüştürür.
        """
        if not cultural_context_data:
            return "Kültürel bağlam bilgisi mevcut değil."

        formatted_list = []
        for key, value in cultural_context_data.items():
            if isinstance(value, list):
                formatted_list.append(f"{key.replace('_', ' ').title()}: {', '.join(value)}")
            else:
                formatted_list.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted_list)

    def _format_themes_motifs_for_prompt(self, themes_motifs_data: Dict[str, List[str]]) -> str:
        """
        Temalar ve motifler verilerini AI prompt'una uygun, okunabilir bir string formatına dönüştürür.
        """
        if not themes_motifs_data:
            return "Temalar ve motifler bilgisi mevcut değil."

        formatted_list = []
        if themes_motifs_data.get("main_themes"): formatted_list.append(f"Ana Temalar: {', '.join(themes_motifs_data['main_themes'])}")
        if themes_motifs_data.get("sub_themes"): formatted_list.append(f"Alt Temalar: {', '.join(themes_motifs_data['sub_themes'])}")
        if themes_motifs_data.get("recurring_motifs"): formatted_list.append(f"Tekrarlayan Motifler: {', '.join(themes_motifs_data['recurring_motifs'])}")
        if themes_motifs_data.get("moral_lessons"): formatted_list.append(f"Ahlaki Dersler: {', '.join(themes_motifs_data['moral_lessons'])}")
        return "\n".join(formatted_list)

    def _format_setting_atmosphere_for_prompt(self, setting_atmosphere_data: Dict[str, Any]) -> str:
        """
        Ortam ve atmosfer verilerini AI prompt'una uygun, okunabilir bir string formatına dönüştürür.
        """
        if not setting_atmosphere_data:
            return "Ortam ve atmosfer bilgisi mevcut değil."

        formatted_list = []
        for key, value in setting_atmosphere_data.items():
            if isinstance(value, list):
                formatted_list.append(f"{key.replace('_', ' ').title()}: {', '.join(value)}")
            else:
                formatted_list.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted_list)

    def _extract_response_text(self, response, stage_name, progress_callback):
        """Helper to extract text from Gemini response and handle safety issues."""
        if not response.parts:
            feedback_str = "No content returned."
            if response.prompt_feedback and response.prompt_feedback.safety_ratings:
                feedback_str = "; ".join([f"{sr.category.name}: {sr.probability.name}" for sr in response.prompt_feedback.safety_ratings])
            if progress_callback: progress_callback(f"{stage_name} blocked or no content. Prompt feedback: {feedback_str}\n")
            raise Exception(f"{stage_name} failed/blocked. Details: {feedback_str}")

        text_content = response.text.strip()

        # Try to extract content between markers, if markers exist
        start_marker_str = "---BEGIN"
        end_marker_str = "---END"

        start_idx = text_content.find(start_marker_str)
        end_idx = text_content.find(end_marker_str)

        extracted_text = text_content # Varsayılan olarak tüm metni al

        if start_idx != -1 and end_idx != -1:
            # Ensure start_idx is before end_idx
            if start_idx < end_idx:
                # Adjust start_idx to be after the actual marker line, looking for the first newline after the marker
                start_line_end = text_content.find('\n', start_idx)
                if start_line_end != -1:
                    actual_text_start = start_line_end + 1
                else:
                    actual_text_start = start_idx + len(start_marker_str) # Fallback if no newline after marker
                extracted_text = text_content[actual_text_start:end_idx].strip()
            else:
                print(f"WARNING: Start marker found after end marker. Attempting to clean full text.")
                # Markers are in wrong order, try to clean the full text
                extracted_text = self._clean_ai_response_fallback(text_content)
        else:
            # If markers are not found, try to clean the full text as a fallback.
            print(f"WARNING: Markers ({start_marker_str} or {end_marker_str}) not found in response. Attempting to clean full text as fallback.")
            extracted_text = self._clean_ai_response_fallback(text_content)

        return extracted_text

    def _clean_ai_response_fallback(self, text: str) -> str:
        """
        AI yanıtında işaretler bulunamazsa, çıktıyı temizlemek için fallback metodu.
        Genellikle AI'ın başında veya sonunda eklediği gereksiz metinleri temizler.
        """
        cleaned_text = text.strip()
        # Markdown kod bloğu işaretlerini kaldır (eğer varsa)
        if cleaned_text.startswith('```json') and cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[len('```json'):-len('```')].strip()
        elif cleaned_text.startswith('```') and cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[len('```'):-len('```')].strip()
        
        # "RESPONSE FORMAT (STRICT):" gibi prompt başlıklarını kaldır
        lines = cleaned_text.split('\n')
        filtered_lines = []
        in_response_format_section = False
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("RESPONSE FORMAT (STRICT):") or \
               stripped_line.startswith("TASK:") or \
               stripped_line.startswith("CONTEXT FOR MODEL USE ONLY"):
                in_response_format_section = True
                continue
            if in_response_format_section and stripped_line.startswith("---BEGIN"):
                in_response_format_section = False
                continue
            if not in_response_format_section and stripped_line.startswith("---END"):
                continue
            if not in_response_format_section:
                filtered_lines.append(line)
        
        return "\n".join(filtered_lines).strip()


    def translate_novel(self, sections: List[Dict[str, str]], genre: str, characters: str, target_language="en", target_country="US", progress_callback=None, stop_event=None):
        """Translate the entire novel section by section"""
        try:
            translated_sections_data = []

            total_sections = len(sections)
            for i, section_data in enumerate(sections):
                if stop_event and stop_event.is_set():
                    if progress_callback: progress_callback("Translation stopped by user.\n")
                    break

                if progress_callback: progress_callback(f"Translating section {i+1}/{total_sections} (Type: {section_data['type']})...\n")

                translated_text, stages = self.translate_section(
                    section_data,
                    genre=genre,
                    characters=characters,
                    target_language=target_language,
                    target_country=target_country, # Pass target_country here
                    progress_callback=progress_callback,
                    stop_event=stop_event
                )
                translated_sections_data.append({"type": section_data["type"], "text": translated_text})
                self.translation_stages.extend(stages)

            return translated_sections_data

        except Exception as e:
            if progress_callback:
                progress_callback(f"Translation error: {str(e)}\n")
            print(f"Translation error: {str(e)}")
            return []

    def update_translation_memory(self, original: str, translation: str):
        """
        Update the translation memory with new translations.
        """
        self.translation_memory[original] = translation

    def get_translation_stages() -> List[Dict[str, str]]:
        """
        Get the list of translation stages for the last translation.
        """
        return self.translation_stages

    def back_translate(self, translated_text: str, target_language: str, source_language: str, progress_callback=None) -> str:
        """Simple back-translation of the translated text to source language"""
        try:
            back_translation_prompt = f"""RESPONSE FORMAT (STRICT):
- Your output MUST CONTAIN ONLY the back-translated text.
- DO NOT include explanations, greetings, summaries, markdown, or any additional content.
- The output must be a single, clean, continuous translation.
- DO NOT DEVIATE from these instructions.

TASK:
You are a professional literary translator. The text below is in {target_language}. Back-translate it into {source_language}, aiming to reconstruct the presumed original as accurately and naturally as possible.

Focus on:
- Faithful reproduction of meaning
- Smooth and natural language flow
- Matching tone, style, and voice of the original author

TEXT TO BACK-TRANSLATE (in {target_language}):
{translated_text}

⚠️ YOUR RESPONSE MUST BEGIN WITH THE FIRST WORD OF THE BACK-TRANSLATION AND END WITH THE LAST WORD OF THE BACK-TRANSLATION.
DO NOT INCLUDE ANY CONTEXT OR FORMATTING OUTSIDE THE TRANSLATED TEXT.

---BEGIN BACK-TRANSLATION---"""

            if progress_callback:
                progress_callback("Performing back-translation...\n")

            response = self.model.generate_content(back_translation_prompt, safety_settings=self.safety_settings)
            time.sleep(5) # 5 saniye gecikme eklendi
            back_translated = self._extract_response_text(response, "Back-Translation", progress_callback)

            return back_translated

        except Exception as e:
            if progress_callback:
                progress_callback(f"Back-translation error: {str(e)}\n")
            print(f"Back-translation error: {str(e)}")
            return translated_text

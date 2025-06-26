import re
import time # Added for retry delay
from typing import Dict, List, Tuple, Any
import os
from dotenv import load_dotenv
import json5 # json yerine json5 kullanıldı
import logging

logger = logging.getLogger(__name__)

# Import necessary libraries based on potential AI models
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import openai

def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify `source` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            deep_update(source[key], value)
        else:
            source[key] = value
    return source

class NovelTranslator:
    def __init__(self, target_country: str = "US"): # API key will be handled internally based on model
        load_dotenv()
        self.target_country = target_country.upper() # Store as uppercase for consistency
        
        self.ai_model = os.getenv("AI_MODEL", "gemini").lower() # Default to gemini if not set
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.allowed_model = os.getenv("ALLOWED_MODEL", None)

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
        
        # Default promptları sakla
        self.default_initial_prompt = """RESPONSE FORMAT (STRICT):\n- Your output MUST INCLUDE ONLY the translated text.\n- DO NOT add greetings, summaries, explanations, markdown, or formatting.\n- DO NOT include section titles, genre names, character info, or style guide notes.\n- The output must be a single, continuous, plain translation.\n- DO NOT DEVIATE from this rule.\n\nTASK:\nYou are a professional literary translator. Translate the following novel section from {source_language} into {target_language} for readers in {target_country}. This section may contain a mix of dialogue, description, and internal thoughts.\n\nFocus on:\n- Preserving the original **tone**, **style**, and **emotional impact**.\n- Ensuring **genre-appropriate phrasing** and **character consistency**.\n\n{mandatory_terms_section}\n\nSOURCE TEXT (in {source_language}):\n{original_section_text}\n\nCONTEXT FOR MODEL USE ONLY — DO NOT OUTPUT:\nSource Language: {source_language}\nTarget Language: {target_language}\nTarget Country: {target_country}\nGenre: {genre}\nCharacter Info:\n{formatted_characters_for_prompt}\nCultural Context:\n{formatted_cultural_context_for_prompt}\nMain Themes and Motifs:\n{formatted_themes_motifs_for_prompt}\nSetting and Atmosphere:\n{formatted_setting_atmosphere_for_prompt}\nStyle Guide:\n{style_guide_text}\n\n⚠️ DO NOT INCLUDE ANY PART OF THE CONTEXT ABOVE IN YOUR OUTPUT. \nYOUR RESPONSE MUST BEGIN WITH THE FIRST WORD OF THE TRANSLATION AND END WITH THE LAST WORD OF THE TRANSLATION. \n\n---BEGIN TRANSLATED TEXT---"""
        self.default_line_edit_prompt = """RESPONSE FORMAT (STRICT):\n- Your output MUST CONTAIN ONLY the edited text.\n- DO NOT include explanations, greetings, summaries, markdown, metadata, or any other additional content.\n- The output must be a single, clean, continuous edited version of the input translation.\n- DO NOT DEVIATE from these instructions under any circumstances.\n\nTASK:\nYou are a professional line editor for literary fiction. Refine the translated text below, which was translated from {source_language} into {target_language}, for readers in {target_country}. The original text is a novel section that may contain a mix of dialogue, description, and internal thoughts.\n\nFocus on improving:\n- Flow and sentence rhythm\n- Readability and clarity\n- Grammar and punctuation\n\nWhile preserving:\n- The original meaning\n- Literary tone and atmosphere\n- Character voice and emotional consistency\n- Conformity with the provided style guide\n\nREFERENCE TEXT (DO NOT OUTPUT):\n{original_section_text}\n\nTEXT TO EDIT:\n{initial_translation}\n\nCONTEXT FOR MODEL USE ONLY — DO NOT OUTPUT:\nSource Language: {source_language}\nTarget Language: {target_language}\nTarget Country: {target_country}\nGenre: {genre}\nKey Characters:\n{formatted_characters_for_prompt}\nCultural Context:\n{formatted_cultural_context_for_prompt}\nMain Themes and Motifs:\n{formatted_themes_motifs_for_prompt}\nSetting and Atmosphere:\n{formatted_setting_atmosphere_for_prompt}\nStyle Guide:\n{style_guide_text}\n\n⚠️ DO NOT INCLUDE ANY PART OF THE CONTEXT ABOVE IN YOUR OUTPUT.\nYOUR RESPONSE MUST BEGIN WITH THE FIRST WORD OF THE EDITED TEXT AND END WITH THE LAST WORD OF THE EDITED TEXT.\n\n---BEGIN EDITED TEXT---"""
        self.default_cultural_prompt = """RESPONSE FORMAT (STRICT):\n- Your output MUST CONTAIN ONLY the culturally localized text.\n- DO NOT include introductions, explanations, greetings, summaries, markdown, or any other content.\n- DO NOT DEVIATE from these instructions under any circumstances.\n\nTASK:\nYou are a professional expert in cultural adaptation for literary fiction. Adapt the following translated text, which was translated from {source_language} into {target_language}, so that it feels natural, relatable, and resonant for {target_language} readers in {target_country} — while preserving the original cultural identity, context, and emotional authenticity. The original text is a novel section that may contain a mix of dialogue, description, and internal thoughts.\n\nMake minimal, necessary adjustments:\n- Clarify or adapt culturally specific references, idioms, or names only if comprehension would otherwise be hindered.\n- Avoid over-domestication, excessive Anglicization or Americanization unless essential for clarity.\n- Do not Westernize the text unless the original intent requires it.\n\nPreserve:\n- Narrative structure and flow\n- Original intent and message\n- Character voice and emotional tone\n- Literary and stylistic consistency per the provided style guide\n\nREFERENCE TEXT (DO NOT OUTPUT):\n{original_section_text}\n\nTEXT TO LOCALIZE:\n{line_edited}\n\nCONTEXT FOR MODEL USE ONLY — DO NOT OUTPUT:\nSource Language: {source_language}\nTarget Language: {target_language}\nTarget Country: {target_country}\nGenre: {genre}\nKey Characters:\n{formatted_characters_for_prompt}\nCultural Context:\n{formatted_cultural_context_for_prompt}\nMain Themes and Motifs:\n{formatted_themes_motifs_for_prompt}\nSetting and Atmosphere:\n{formatted_setting_atmosphere_for_prompt}\nStyle Guide:\n{style_guide_text}\n\n⚠️ DO NOT INCLUDE ANY PART OF THE CONTEXT ABOVE IN YOUR OUTPUT.\nYOUR RESPONSE MUST BEGIN WITH THE FIRST WORD OF THE LOCALIZED TEXT AND END WITH THE LAST WORD OF THE LOCALIZED TEXT.\n\n---BEGIN LOCALIZED TEXT---"""
        self.default_style_guide_generation_prompt = """Sen profesyonel bir edebi çevirmensin. Aşağıdaki roman analizi verilerine dayanarak, {source_language} dilinden {target_language} diline, {target_country} ülkesindeki okuyucular için bu romanın çevirisi için kapsamlı bir stil rehberi oluştur. Bu, çeviri sürecinin başlangıcında oluşturulan ilk taslak stil rehberidir.

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
        self.default_style_guide_update_prompt = """Sen profesyonel bir edebi çevirmensin. Amacın, {source_language} dilinden {target_language} diline, {target_country} ülkesindeki okuyucular için çevirinin mümkün olduğunca doğal, akıcı ve kültürel olarak uygun gelmesini sağlamaktır. Aşağıdaki orijinal metin ve onun çevirisi ile birlikte mevcut stil rehberini incele. Bu bilgilere dayanarak, stil rehberini daha da geliştir ve güncelle. Özellikle karakter sesleri, tutarlı terimler, kültürel referanslar ve genel ton/stil gibi alanlara odaklan.

**Önemli Not: Tutarlı Terimler ve Kültürel Referanslar için, sadece birebir çeviri veya orijinalini koruma yerine, hedef dildeki en doğal, kültürel olarak eşdeğer veya açıklayıcı yaklaşımları belirle.** Örneğin, bir rütbe veya unvan için hedef dildeki en yakın ve anlaşılır karşılığı bul, veya bir kültürel öğe için kısa bir açıklama veya adaptasyon öner.

Lütfen yalnızca güncellenmiş stil rehberini aşağıdaki JSON formatında bir nesne olarak yanıt ver. Başka açıklama ekleme. JSON içindeki TÜM anahtarlar (keys) ÇİFT TIRNAK içinde olmalıdır.

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
    }}
  }},
  "consistent_terms": {{
    "Orijinal Terim 1": "Çevrilmiş Terim 1 (Hedef dildeki en doğal ve anlaşılır karşılığı, gerekirse kısa açıklama)"
  }},
  "cultural_references": {{
    "Orijinal Referans 1": "Çevirideki Yaklaşım/Açıklama (Hedef kültüre nasıl uyarlanmalı veya açıklanmalı)"
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
        self.initial_prompt = self.default_initial_prompt
        self.line_edit_prompt = self.default_line_edit_prompt
        self.cultural_prompt = self.default_cultural_prompt
        self.style_guide_generation_prompt = self.default_style_guide_generation_prompt
        self.style_guide_update_prompt = self.default_style_guide_update_prompt

        self.default_back_translation_prompt = f"""RESPONSE FORMAT (STRICT):
- Your output MUST INCLUDE ONLY the back-translated text.
- DO NOT add greetings, summaries, explanations, markdown, or formatting.
- DO NOT include section titles, genre names, character info, or style guide notes.
- The output must be a single, continuous, plain back-translation.
- DO NOT DEVIATE from this rule.

TASK:
You are a professional literary translator. Back-translate the following text from {{target_language}} into {{source_language}}. This is for quality control purposes to ensure the original meaning is preserved.

Focus on:
- Preserving the original meaning and intent
- Maintaining the same tone and style as the original
- Ensuring accuracy in the back-translation

SOURCE TEXT (in {{target_language}}):
{{translated_text}}

⚠️ DO NOT INCLUDE ANY PART OF THE CONTEXT ABOVE IN YOUR OUTPUT. 
YOUR RESPONSE MUST BEGIN WITH THE FIRST WORD OF THE BACK-TRANSLATION AND END WITH THE LAST WORD OF THE BACK-TRANSLATION. 

---BEGIN BACK-TRANSLATED TEXT---"""
        self.back_translation_prompt = self.default_back_translation_prompt
        
    def _setup_ai_model(self):
        """
        Setup the selected AI model (Gemini or ChatGPT)
        """
        if self.ai_model == "gemini":
            self._setup_gemini()
        elif self.ai_model == "chatgpt":
            self._setup_openai()
        else:
            raise ValueError(f"error_unsupported_ai_model:{self.ai_model}")

    def _setup_gemini(self):
        """
        Setup Gemini API with the provided API key
        """
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
        print(f"DEBUG: Gemini model setup complete. Using model: {model_name}")

    def _setup_openai(self):
        """
        Setup OpenAI API with the provided API key
        """
        if not self.openai_api_key:
            raise ValueError("error_openai_api_key_not_found")

        openai.api_key = self.openai_api_key
        model_name = self.allowed_model if (self.allowed_model and self.ai_model == "chatgpt") else "gpt-4o-mini"
        self.model = model_name
        print(f"DEBUG: OpenAI model setup complete. Using model: {model_name}")

    def set_initial_character_info(self, characters_str):
        """
        Bu metot artık kullanılmayacak, karakter bilgileri doğrudan AI analizinden gelecek.
        """
        pass

    def generate_style_guide_with_ai(self, genre: str, characters_data: Dict[str, Any], cultural_context_data: Dict[str, Any], main_themes_data: Dict[str, Any], setting_atmosphere_data: Dict[str, Any], source_language: str, target_language: str, target_country: str, progress_callback=None, max_retries: int = 3, retry_delay: int = 5, stop_event=None):
        """
        NovelAnalyzer'dan gelen verileri kullanarak stil rehberinin ilk taslağını yapay zeka ile oluşturur.
        Hata durumunda belirtilen sayıda yeniden deneme yapar.
        """
        if stop_event and stop_event.is_set():
            if progress_callback: progress_callback("log_style_guide_generation_stopped")
            return
        if progress_callback: progress_callback("log_style_guide_generation_started")
        print("DEBUG: generate_style_guide_with_ai called for initial draft.")

        formatted_characters = self._format_characters_for_prompt(characters_data)
        formatted_cultural_context = self._format_cultural_context_for_prompt(cultural_context_data)
        formatted_themes_motifs = self._format_themes_motifs_for_prompt(main_themes_data)
        formatted_setting_atmosphere = self._format_setting_atmosphere_for_prompt(setting_atmosphere_data)

        prompt = self.style_guide_generation_prompt.format(
            source_language=source_language,
            target_language=target_language,
            target_country=target_country,
            genre=genre,
            formatted_characters=formatted_characters,
            formatted_cultural_context=formatted_cultural_context,
            formatted_themes_motifs=formatted_themes_motifs,
            formatted_setting_atmosphere=formatted_setting_atmosphere
        )
        for attempt in range(max_retries):
            if stop_event and stop_event.is_set():
                if progress_callback: progress_callback("log_style_guide_generation_stopped")
                return
            try:
                if progress_callback: progress_callback("log_style_guide_generation_attempt", attempt=attempt + 1, max_retries=max_retries)

                logger.debug(f"Stil rehberi oluşturma prompt'u:\n{prompt}")
                if self.ai_model == "gemini":
                    response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
                    raw_response_text = response.text.strip()
                elif self.ai_model == "chatgpt":
                    # Ensure self.model is set for OpenAI
                    if not self.model:
                         raise ValueError("error_openai_model_not_set_up")
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


                logger.debug(f"DEBUG: generate_style_guide_with_ai Cleaned AI Response (first 500 chars): {raw_response_text[:500]}...")

                if not raw_response_text:
                    raise ValueError("error_ai_empty_response")

                try:
                    ai_generated_style_guide = json5.loads(raw_response_text)
                    self.style_guide.update(ai_generated_style_guide)
                    logger.info("Style guide successfully generated and updated from AI.")
                    if progress_callback: progress_callback("log_style_guide_generation_success")
                    return # Başarılı olursa döngüden çık
                except json5.Json5Error as json_e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                    if progress_callback: progress_callback("log_style_guide_generation_json_error", error=json_e)
                    raise ValueError(f"error_json_decode:{json_e}|{raw_response_text}")

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

                logger.error(error_message, exc_info=True)
                if progress_callback: progress_callback(f"{error_message}\n")
                if attempt < max_retries - 1:
                    logger.info(f"Yeniden deneniyor {retry_delay} saniye içinde...")
                    time.sleep(retry_delay)
                else:
                    logger.warning(f"Stil rehberi oluşturma için maksimum yeniden deneme sayısına ulaşıldı. Varsayılan stil rehberi kullanılıyor.")
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

    def update_style_guide(self, original_text: str, translated_text: str, genre: str, characters_data: Dict[str, Any], cultural_context_data: Dict[str, Any], main_themes_data: Dict[str, Any], setting_atmosphere_data: Dict[str, Any], source_language: str, target_language: str, target_country: str, progress_callback=None, max_retries: int = 3, retry_delay: int = 5, stop_event=None):
        """
        Çevrilen her bölümden sonra stil rehberini dinamik olarak günceller.
        Orijinal metin ve çevrilen metin arasındaki ilişkileri öğrenir.
        Hata durumunda belirtilen sayıda yeniden deneme yapar.
        """
        if stop_event and stop_event.is_set():
            if progress_callback: progress_callback("log_style_guide_update_stopped")
            return

        if progress_callback: progress_callback("log_style_guide_update_started")
        print(f"DEBUG: update_style_guide called for dynamic update.")

        # Mevcut stil rehberini JSON string'e dönüştür
        current_style_guide_json = json5.dumps(self.style_guide, ensure_ascii=False, indent=2)

        # Karakter verilerini prompt için formatla
        formatted_characters = self._format_characters_for_prompt(characters_data)
        formatted_cultural_context = self._format_cultural_context_for_prompt(cultural_context_data)
        formatted_themes_motifs = self._format_themes_motifs_for_prompt(main_themes_data)
        formatted_setting_atmosphere = self._format_setting_atmosphere_for_prompt(setting_atmosphere_data)

        prompt = self.style_guide_update_prompt.format(
            source_language=source_language,
            target_language=target_language,
            target_country=target_country,
            genre=genre,
            formatted_characters=formatted_characters,
            formatted_cultural_context=formatted_cultural_context,
            formatted_themes_motifs=formatted_themes_motifs,
            formatted_setting_atmosphere=formatted_setting_atmosphere,
            current_style_guide_json=current_style_guide_json,
            original_text=original_text,
            translated_text=translated_text
        )
        for attempt in range(max_retries):
            if stop_event and stop_event.is_set():
                if progress_callback: progress_callback("log_style_guide_update_stopped")
                return
            try:
                if progress_callback: progress_callback("log_style_guide_update_attempt", attempt=attempt + 1, max_retries=max_retries)

                logger.debug(f"Stil rehberi güncelleme prompt'u:\n{prompt}")
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
                    raise ValueError("error_ai_empty_response")

                try:
                    ai_updated_style_guide = json5.loads(raw_response_text)
                    # self.style_guide.update(ai_updated_style_guide) -> Bu satır, iç içe geçmiş sözlükleri ezer.
                    # Bunun yerine derin bir güncelleme (deep update) yap.
                    deep_update(self.style_guide, ai_updated_style_guide)
                    print("DEBUG: Style guide successfully deep-updated from AI.")
                    if progress_callback: progress_callback("log_style_guide_update_success")
                    return # Başarılı olursa döngüden çık
                except json5.Json5Error as json_e: # json.JSONDecodeError yerine json5.Json5Error kullanıldı
                    print(f"AI yanıtı geçerli JSON değil: {json_e}. Ham yanıt: {raw_response_text}")
                    if progress_callback: progress_callback("log_style_guide_update_json_error", error=json_e)
                    raise ValueError(f"error_json_decode:{json_e}|{raw_response_text}")

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
                logger.error(error_message, exc_info=True)
                if progress_callback: progress_callback(f"{error_message}\n")
                if attempt < max_retries - 1:
                    logger.info(f"Yeniden deneniyor {retry_delay} saniye içinde...")
                    time.sleep(retry_delay)
                else:
                    logger.warning(f"Stil rehberi güncelleme için maksimum yeniden deneme sayısına ulaşıldı. Mevcut stil rehberi korunuyor.")
                    # Hata durumunda mevcut stil rehberini koru
                    pass

    def translate_section(self, section_data: Dict[str, str], genre: str, characters_json_str: str, cultural_context_json_str: str, main_themes_json_str: str, setting_atmosphere_json_str: str, source_language: str, target_language: str = "en", target_country: str = "US", progress_callback=None, stop_event=None, max_retries=3, retry_delay=5, user_defined_terms: str = "", initial_translation_override: str = None, line_edit_override: str = None, localization_override: str = None, intermediate_callback=None) -> Tuple[Dict[str, str], List[str]]:
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
                speech_patterns = ", ".join(voice.get("speech_patterns", []) if isinstance(voice.get("speech_patterns"), list) else [])
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

        initial_translation = ""
        line_edited = ""
        final_translation = ""

        # Stage 1: Initial Translation
        if initial_translation_override:
            initial_translation = initial_translation_override
            if progress_callback: progress_callback("log_initial_translation_skipped")
            stages.append(f"Initial Translation (Skipped, User-provided):\n{initial_translation}\n")
        else:
            for attempt in range(max_retries):
                if stop_event and stop_event.is_set():
                    if progress_callback: progress_callback("log_translation_stopped")
                    return original_section_text, stages
                try:
                    if progress_callback: progress_callback("log_stage_attempt", stage="Initial Translation", type=section_type, attempt=attempt + 1, max_retries=max_retries)
                    mandatory_terms_section = ""
                    if user_defined_terms and user_defined_terms.strip():
                        mandatory_terms_section = f"MANDATORY TRANSLATIONS:\nThe following terms MUST be translated exactly as specified, overriding any other suggestions.\n{user_defined_terms}\n"
                    initial_prompt = self.initial_prompt.format(
                        source_language=source_language, target_language=target_language, target_country=target_country,
                        mandatory_terms_section=mandatory_terms_section, original_section_text=original_section_text,
                        formatted_characters_for_prompt=formatted_characters_for_prompt,
                        formatted_cultural_context_for_prompt=formatted_cultural_context_for_prompt,
                        formatted_themes_motifs_for_prompt=formatted_themes_motifs_for_prompt,
                        formatted_setting_atmosphere_for_prompt=formatted_setting_atmosphere_for_prompt,
                        genre=genre, style_guide_text=style_guide_text
                    )
                    if self.ai_model == "gemini":
                        logger.debug(f"İlk çeviri prompt'u:\n{initial_prompt}")
                        initial_response = self.model.generate_content(initial_prompt, safety_settings=self.safety_settings)
                        initial_translation = self._extract_response_text(initial_response, "Initial Translation", progress_callback)
                        logger.debug(f"Ham ilk çeviri yanıtı:\n{initial_translation}")
                    elif self.ai_model == "chatgpt":
                        if not self.model: raise ValueError("error_openai_model_not_set_up")
                        initial_response = openai.chat.completions.create(model=self.model, messages=[{"role": "user", "content": initial_prompt}])
                        initial_translation = initial_response.choices[0].message.content.strip()
                    
                    time.sleep(5)
                    print(f"DEBUG: Extracted initial translation: {initial_translation[:200]}...")
                    stages.append(f"Initial Translation:\n{initial_translation}\n")
                    if intermediate_callback:
                        intermediate_callback("initial", initial_translation)
                    break  # Success, exit retry loop for this stage
                except Exception as e:
                    self._handle_translation_error(e, "Initial Translation", section_type, attempt, max_retries, retry_delay, progress_callback)
                    if attempt >= max_retries - 1:
                        return {"initial": original_section_text, "edited": "", "final": ""}, stages

        if not initial_translation: return {"initial": original_section_text, "edited": "", "final": ""}, stages
        if stop_event and stop_event.is_set():
            if progress_callback: progress_callback("Translation stopped by user.\n")
            return {"initial": initial_translation, "edited": "", "final": ""}, stages

        # Stage 2: Line Editing
        if line_edit_override:
            line_edited = line_edit_override
            if progress_callback: progress_callback("log_line_edit_skipped")
            stages.append(f"Line Editing (Skipped, User-provided):\n{line_edited}\n")
        else:
            for attempt in range(max_retries):
                if stop_event and stop_event.is_set():
                    if progress_callback: progress_callback("log_translation_stopped")
                    return initial_translation, stages
                try:
                    if progress_callback: progress_callback("log_stage_attempt", stage="Line Editing", type=section_type, attempt=attempt + 1, max_retries=max_retries)
                    line_edit_prompt = self.line_edit_prompt.format(
                        source_language=source_language, target_language=target_language, target_country=target_country,
                        original_section_text=original_section_text,
                        formatted_characters_for_prompt=formatted_characters_for_prompt,
                        formatted_cultural_context_for_prompt=formatted_cultural_context_for_prompt,
                        formatted_themes_motifs_for_prompt=formatted_themes_motifs_for_prompt,
                        formatted_setting_atmosphere_for_prompt=formatted_setting_atmosphere_for_prompt,
                        genre=genre, initial_translation=initial_translation, style_guide_text=style_guide_text
                    )
                    if self.ai_model == "gemini":
                        logger.debug(f"Satır düzenleme prompt'u:\n{line_edit_prompt}")
                        line_edit_response = self.model.generate_content(line_edit_prompt, safety_settings=self.safety_settings)
                        line_edited = self._extract_response_text(line_edit_response, "Line Editing", progress_callback)
                        logger.debug(f"Ham satır düzenleme yanıtı:\n{line_edited}")
                    elif self.ai_model == "chatgpt":
                        if not self.model: raise ValueError("error_openai_model_not_set_up")
                        line_edit_response = openai.chat.completions.create(model=self.model, messages=[{"role": "user", "content": line_edit_prompt}])
                        line_edited = line_edit_response.choices[0].message.content.strip()
                    
                    time.sleep(5)
                    print(f"DEBUG: Extracted line edit translation: {line_edited[:200]}...")
                    stages.append(f"Line Editing:\n{line_edited}\n")
                    if intermediate_callback:
                        intermediate_callback("edited", line_edited)
                    break # Success
                except Exception as e:
                    self._handle_translation_error(e, "Line Editing", section_type, attempt, max_retries, retry_delay, progress_callback)
                    if attempt >= max_retries - 1:
                        return {"initial": initial_translation, "edited": "", "final": ""}, stages # Return last successful stage result

        if not line_edited: return {"initial": initial_translation, "edited": "", "final": ""}, stages
        if stop_event and stop_event.is_set():
            if progress_callback: progress_callback("Translation stopped by user.\n")
            return {"initial": initial_translation, "edited": line_edited, "final": ""}, stages

        # Stage 3: Cultural Localization
        if localization_override:
            final_translation = localization_override
            if progress_callback: progress_callback("log_localization_skipped")
            stages.append(f"Cultural Localization (Skipped, User-provided):\n{final_translation}\n")
        else:
            for attempt in range(max_retries):
                if stop_event and stop_event.is_set():
                    if progress_callback: progress_callback("log_translation_stopped")
                    return line_edited, stages
                try:
                    if progress_callback: progress_callback("log_stage_attempt", stage="Cultural Localization", type=section_type, attempt=attempt + 1, max_retries=max_retries)
                    cultural_prompt = self.cultural_prompt.format(
                        source_language=source_language, target_language=target_language, target_country=target_country,
                        original_section_text=original_section_text,
                        formatted_characters_for_prompt=formatted_characters_for_prompt,
                        formatted_cultural_context_for_prompt=formatted_cultural_context_for_prompt,
                        formatted_themes_motifs_for_prompt=formatted_themes_motifs_for_prompt,
                        formatted_setting_atmosphere_for_prompt=formatted_setting_atmosphere_for_prompt,
                        genre=genre, line_edited=line_edited, style_guide_text=style_guide_text
                    )
                    if self.ai_model == "gemini":
                        logger.debug(f"Kültürel yerelleştirme prompt'u:\n{cultural_prompt}")
                        cultural_response = self.model.generate_content(cultural_prompt, safety_settings=self.safety_settings)
                        final_translation = self._extract_response_text(cultural_response, "Cultural Localization", progress_callback)
                        logger.debug(f"Ham kültürel yerelleştirme yanıtı:\n{final_translation}")
                    elif self.ai_model == "chatgpt":
                        if not self.model: raise ValueError("error_openai_model_not_set_up")
                        cultural_response = openai.chat.completions.create(model=self.model, messages=[{"role": "user", "content": cultural_prompt}])
                        final_translation = cultural_response.choices[0].message.content.strip()
                    
                    time.sleep(5)
                    print(f"DEBUG: Extracted final translation: {final_translation[:200]}...")
                    stages.append(f"Cultural Localization:\n{final_translation}\n")
                    if intermediate_callback:
                        intermediate_callback("final", final_translation)
                    break # Success
                except Exception as e:
                    self._handle_translation_error(e, "Cultural Localization", section_type, attempt, max_retries, retry_delay, progress_callback)
                    if attempt >= max_retries - 1:
                        return {"initial": initial_translation, "edited": line_edited, "final": ""}, stages # Return last successful stage result

        if not final_translation: return {"initial": initial_translation, "edited": line_edited, "final": ""}, stages
        if stop_event and stop_event.is_set():
            if progress_callback: progress_callback("Translation stopped by user.\n")
            return {"initial": initial_translation, "edited": line_edited, "final": final_translation}, stages

        # Stil rehberini çevrilen metinle dinamik olarak güncelle
        self.update_style_guide(
            original_section_text, final_translation, genre,
            parsed_characters, parsed_cultural_context, parsed_main_themes, parsed_setting_atmosphere,
            source_language, target_language, target_country,
            progress_callback=progress_callback, max_retries=max_retries, stop_event=stop_event
        )
        print(f"DEBUG: Dynamic style guide update completed for section type '{section_type}'.")
        
        translation_results = {
            "initial": initial_translation,
            "edited": line_edited,
            "final": final_translation
        }
        return translation_results, stages

    def _handle_translation_error(self, e, stage_name, section_type, attempt, max_retries, retry_delay, progress_callback):
        """Hata yönetimi için yardımcı fonksiyon."""
        full_error_message = str(e)
        logger.error(f"Section translation error in '{stage_name}' (Attempt {attempt + 1}/{max_retries}) for '{section_type}'", exc_info=True)

        ui_display_message = ""
        feedback_marker = "Prompt Feedback Details:"
        if feedback_marker in full_error_message:
            feedback_details_part = full_error_message.split(feedback_marker, 1)[-1].strip()
            actual_block_reason_match = re.search(r"Block Reason:\s*(?!(N/A|NONE|No prompt_feedback available from AI\.?$))([^,]+)", feedback_details_part, re.IGNORECASE)
            if actual_block_reason_match:
                ui_display_message = f"API Engelleme Geri Bildirimi ({stage_name} / {section_type}): {feedback_details_part}"
        
        if not ui_display_message:
            if "The `response.parts` quick accessor" in full_error_message:
                ui_display_message = f"API yanıtı '{stage_name}' için alınamadı (SDK teknik hatası). Lütfen logları kontrol edin."
            elif "AI response.parts not structured" in full_error_message:
                 ui_display_message = f"API yanıtı '{stage_name}' için beklenmedik bir yapıdaydı. Lütfen logları kontrol edin."
            elif "AI returned no content parts" in full_error_message:
                 ui_display_message = f"API '{stage_name}' için içerik döndürmedi. Muhtemelen engellendi. Lütfen logları kontrol edin."
            else:
                ui_display_message = f"'{stage_name}' / '{section_type}' çevrilirken beklenmedik bir hata oluştu. Lütfen logları kontrol edin."
        
        if progress_callback:
            progress_callback(f"  - Çeviri Hatası (Deneme {attempt + 1}/{max_retries}): {ui_display_message}\n")

        if attempt < max_retries - 1:
            logger.info(f"Retrying '{stage_name}' for '{section_type}' in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            logger.warning(f"Max retries reached for '{stage_name}'.")
            if progress_callback:
                progress_callback(f"'{stage_name}' için maksimum deneme sayısına ulaşıldı. Bu bölüm için çeviri durduruldu.\n")
            raise Exception(f"'{stage_name}' için maksimum deneme sayısına ulaşıldı.")

    def _format_characters_for_prompt(self, characters_data: Dict[str, Dict[str, str]]) -> str:
        """
        Karakter verilerini AI prompt'una uygun, okunabilir bir string formatına dönüştürür.
        """
        if not characters_data:
            return "Karakter bilgisi mevcut değil."

        formatted_list = []
        for char_name, details in characters_data.items():
            role = details.get("role", "Bilinmiyor")
            personality = ", ".join(details.get("personality") if isinstance(details.get("personality"), list) else [])
            emotions = ", ".join(details.get("emotions") if isinstance(details.get("emotions"), list) else [])
            speech_style = ", ".join(details.get("speech_style") if isinstance(details.get("speech_style"), list) else [])
            occupation = details.get("occupation", "")
            nickname = details.get("nickname", "")
            motivation = details.get("motivation", "")
            conflicts = ", ".join(details.get("conflicts") if isinstance(details.get("conflicts"), list) else [])
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
            if isinstance(relationships.get("friends"), list) and relationships.get("friends"): rel_parts.append(f"Arkadaşlar: {', '.join(relationships['friends'])}")
            if isinstance(relationships.get("enemies"), list) and relationships.get("enemies"): rel_parts.append(f"Düşmanlar: {', '.join(relationships['enemies'])}")
            if isinstance(relationships.get("family"), list) and relationships.get("family"): rel_parts.append(f"Aile: {', '.join(relationships['family'])}")
            if isinstance(relationships.get("romantic"), list) and relationships.get("romantic"): rel_parts.append(f"Romantik: {', '.join(relationships['romantic'])}")
            if rel_parts: char_str += f", İlişkiler: ({'; '.join(rel_parts)})"

            # Gelişimi ekle
            development = details.get("development", {})
            dev_parts = []
            if isinstance(development.get("beginning"), list) and development.get("beginning"): dev_parts.append(f"Başlangıç: {', '.join(development['beginning'])}")
            if isinstance(development.get("middle"), list) and development.get("middle"): dev_parts.append(f"Orta: {', '.join(development['middle'])}")
            if isinstance(development.get("end"), list) and development.get("end"): dev_parts.append(f"Son: {', '.join(development['end'])}")
            if dev_parts: char_str += f", Gelişim: ({'; '.join(dev_parts)})"

            # Anahtar diyaloglar ve düşünceler
            key_dialogues = details.get("key_dialogues") if isinstance(details.get("key_dialogues"), list) else []
            key_thoughts = details.get("key_thoughts") if isinstance(details.get("key_thoughts"), list) else []
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
                formatted_list.append(f"{key.replace('_', ' ').title()}: {', '.join(value if isinstance(value, list) else [])}")
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
        if themes_motifs_data.get("main_themes"): formatted_list.append(f"Ana Temalar: {', '.join(themes_motifs_data['main_themes'] if isinstance(themes_motifs_data['main_themes'], list) else [])}")
        if themes_motifs_data.get("sub_themes"): formatted_list.append(f"Alt Temalar: {', '.join(themes_motifs_data['sub_themes'] if isinstance(themes_motifs_data['sub_themes'], list) else [])}")
        if themes_motifs_data.get("recurring_motifs"): formatted_list.append(f"Tekrarlayan Motifler: {', '.join(themes_motifs_data['recurring_motifs'] if isinstance(themes_motifs_data['recurring_motifs'], list) else [])}")
        if themes_motifs_data.get("moral_lessons"): formatted_list.append(f"Ahlaki Dersler: {', '.join(themes_motifs_data['moral_lessons'] if isinstance(themes_motifs_data['moral_lessons'], list) else [])}")
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
                formatted_list.append(f"{key.replace('_', ' ').title()}: {', '.join(value if isinstance(value, list) else [])}")
            else:
                formatted_list.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted_list)

    def _extract_response_text(self, response, stage_name, progress_callback):
        """Helper to extract text from Gemini response and handle safety issues."""
        
        prompt_feedback_details = []
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            pf = response.prompt_feedback
            block_reason_val = pf.block_reason
            block_reason_str = "N/A"
            if block_reason_val is not None:
                try:
                    block_reason_str = f"{block_reason_val.name} (Value: {block_reason_val})"
                except AttributeError: 
                    block_reason_str = f"Unrecognized BlockReason (Value: {block_reason_val})"
            
            block_message_str = pf.block_reason_message if hasattr(pf, 'block_reason_message') and pf.block_reason_message else "N/A"
            
            safety_ratings_list = []
            if pf.safety_ratings:
                for sr in pf.safety_ratings:
                    cat_name = sr.category.name if hasattr(sr.category, 'name') else str(sr.category)
                    prob_name = sr.probability.name if hasattr(sr.probability, 'name') else str(sr.probability)
                    safety_ratings_list.append(f"{cat_name}: {prob_name}")
            safety_ratings_str = "; ".join(safety_ratings_list) if safety_ratings_list else "N/A"
            
            feedback_log_msg = f"DEBUG: Prompt Feedback for {stage_name} - Block Reason: {block_reason_str}, Message: {block_message_str}, Safety Ratings: {safety_ratings_str}"
            print(feedback_log_msg) # Always print this for server-side logs
            prompt_feedback_details.extend([
                f"Block Reason: {block_reason_str}",
                f"Block Message: {block_message_str}",
                f"Safety Ratings: {safety_ratings_str}"
            ])
            # Removed progress_callback for DEBUG feedback here, it will be part of the raised exception if an error occurs.
        else:
            prompt_feedback_details.append("No prompt_feedback available from AI.")
            print(f"DEBUG: No prompt_feedback available for {stage_name}")

        # Attempt to get text content directly from parts[0].text
        text_content = None
        if (hasattr(response, 'parts') and
            hasattr(response.parts, '__len__') and # Check for general list-like behavior
            len(response.parts) == 1 and
            hasattr(response.parts[0], 'text') and
            response.parts[0].text is not None):
            
            text_content = response.parts[0].text.strip()
            # print(f"DEBUG: Successfully extracted text directly from parts[0] for {stage_name}. Length: {len(text_content)}")

        else: # Conditions for direct text extraction from parts[0].text not met
            error_details_list = [f"{stage_name} failed: AI response.parts not structured as expected or text is None."]
            
            if hasattr(response, 'parts') and hasattr(response.parts, '__len__'): # Check for general list-like behavior
                error_details_list.append(f"Number of parts: {len(response.parts)}.")
                if len(response.parts) == 0:
                    error_details_list.append("Parts list is empty.")
                else: # len(response.parts) > 1 or part[0] is not text/text is None
                    for i, part_item in enumerate(response.parts):
                        part_detail_str = f"Part {i}: "
                        if hasattr(part_item, 'text'):
                            if part_item.text is None:
                                part_detail_str += "Text part (text is None)"
                            else: # This case should ideally be caught by the primary if, but good for multi-part
                                part_detail_str += f"Text part (len {len(part_item.text)})"
                        elif hasattr(part_item, 'inline_data'):
                            part_detail_str += f"Inline data part (mime_type {part_item.inline_data.mime_type})"
                        elif hasattr(part_item, 'function_call'):
                            part_detail_str += "Function call part"
                        else:
                            part_detail_str += f"Unknown part type: {type(part_item)}"
                        error_details_list.append(part_detail_str)
            elif hasattr(response, 'parts'): 
                 error_details_list.append(f"Response.parts is not a list, type: {type(response.parts)}")
            else: 
                error_details_list.append("Response object does not have 'parts' attribute.")

            error_details_list.extend([f"Prompt Feedback Details:"] + prompt_feedback_details)
            
            full_error_message = " ".join(error_details_list)
            if progress_callback:
                progress_callback(f"Error in {stage_name}: {full_error_message}\n")
            print(f"RAISING EXCEPTION (from _extract_response_text due to unsuitable parts): {full_error_message}")
            raise Exception(full_error_message)
        
        # If text_content is successfully extracted, proceed with marker cleaning
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

    def back_translate(self, translated_text: str, target_language: str, source_language: str, progress_callback=None, max_retries: int = 3, retry_delay: int = 5) -> str:
        """
        Çevrilen metni geri çevirir (kaynak dile) çeviri kalitesini kontrol etmek için.
        """
        if progress_callback: progress_callback("log_back_translation_started")
        
        current_back_translation_prompt = self.back_translation_prompt.format(
            target_language=target_language,
            source_language=source_language,
            translated_text=translated_text
        )
        logger.debug(f"Geri çeviri prompt'u:\n{current_back_translation_prompt}")

        for attempt in range(max_retries):
            try:
                if progress_callback: progress_callback("log_back_translation_attempt", attempt=attempt + 1, max_retries=max_retries)
                
                if self.ai_model == "gemini":
                    response = self.model.generate_content(current_back_translation_prompt, safety_settings=self.safety_settings)
                    back_translated_text = self._extract_response_text(response, "Back Translation", progress_callback)
                elif self.ai_model == "chatgpt":
                    response = openai.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": current_back_translation_prompt}]
                    )
                    raw_response_text = response.choices[0].message.content.strip()
                    back_translated_text = self._clean_ai_response_fallback(raw_response_text)
                
                if progress_callback: progress_callback("log_back_translation_success")
                return back_translated_text
            
            except Exception as e:
                error_message = f"Geri çeviri hatası (Deneme {attempt + 1}/{max_retries}): {str(e)}"
                print(error_message)
                if progress_callback: progress_callback("log_back_translation_error", error=str(e))
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return f"[Back-translation failed after {max_retries} retries: {str(e)}]"
        
        return "[Back-translation failed after all retries.]"

    # Stil rehberi prompt güncelleme metodları
    def update_style_guide_generation_prompt(self, new_prompt: str):
        """Stil rehberi oluşturma promptunu günceller."""
        self.style_guide_generation_prompt = new_prompt

    def update_style_guide_update_prompt(self, new_prompt: str):
        """Stil rehberi güncelleme promptunu günceller."""
        self.style_guide_update_prompt = new_prompt

    def update_back_translation_prompt(self, new_prompt: str):
        """Geri çeviri promptunu günceller."""
        self.back_translation_prompt = new_prompt

    # Çeviri promptlarını güncelleme metodları (Örnek olarak eklendi, diğerleri de benzer şekilde eklenebilir)
    def update_initial_translation_prompt(self, new_prompt: str):
        """İlk çeviri promptunu günceller."""
        self.initial_prompt = new_prompt

    def update_line_edit_prompt(self, new_prompt: str):
        """Satır düzenleme promptunu günceller."""
        self.line_edit_prompt = new_prompt

    def update_cultural_localization_prompt(self, new_prompt: str):
        """Kültürel yerelleştirme promptunu günceller."""
        self.cultural_prompt = new_prompt

    def get_all_prompts(self, default=False) -> Dict[str, str]:
        """Tüm düzenlenebilir promptları döndürür. default=True ise varsayılanları döndürür."""
        if default:
            return {
                "initial_translation": self.default_initial_prompt,
                "line_edit": self.default_line_edit_prompt,
                "cultural_localization": self.default_cultural_prompt,
                "style_guide_generation": self.default_style_guide_generation_prompt,
                "style_guide_update": self.default_style_guide_update_prompt,
                "back_translation": self.default_back_translation_prompt
            }
        else:
            return {
                "initial_translation": self.initial_prompt,
                "line_edit": self.line_edit_prompt,
                "cultural_localization": self.cultural_prompt,
                "style_guide_generation": self.style_guide_generation_prompt,
                "style_guide_update": self.style_guide_update_prompt,
                "back_translation": self.back_translation_prompt
            }

    def set_all_prompts(self, prompts: Dict[str, str]):
        """Tüm düzenlenebilir promptları günceller."""
        if "initial_translation" in prompts:
            self.initial_prompt = prompts["initial_translation"]
        if "line_edit" in prompts:
            self.line_edit_prompt = prompts["line_edit"]
        if "cultural_localization" in prompts:
            self.cultural_prompt = prompts["cultural_localization"]
        if "style_guide_generation" in prompts:
            self.style_guide_generation_prompt = prompts["style_guide_generation"]
        if "style_guide_update" in prompts:
            self.style_guide_update_prompt = prompts["style_guide_update"]
        if "back_translation" in prompts:
            self.back_translation_prompt = prompts["back_translation"]

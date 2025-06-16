# Roman Çeviri Asistanı

Roman Çeviri Asistanı, romanları farklı dillere çevirmek için geliştirilmiş güçlü bir araçtır. Yapay zeka destekli çeviri, kültürel adaptasyon ve stil rehberi özellikleriyle profesyonel çeviri sürecini kolaylaştırır.

## Özellikler

### Çeviri Özellikleri
- Çoklu dil desteği (İngilizce, Türkçe, Almanca, Fransızca, İspanyolca, İtalyanca, Portekizce, Rusça, Japonca, Çince, Korece, Arapça, Hintçe)
- Ülkeye özel çeviri adaptasyonu
- Otomatik dil algılama
- Bölüm bölüm çeviri
- Geri çeviri kontrolü
- Çeviri belleği

### Analiz Özellikleri
- Karakter analizi ve yönetimi
- Kültürel bağlam analizi
- Ana temalar ve motifler analizi
- Mekan ve atmosfer analizi
- Otomatik tür algılama

### Stil ve Kalite Kontrolü
- Otomatik stil rehberi oluşturma
- Karakter tutarlılığı kontrolü
- Kültürel adaptasyon
- Düzeltme ve düzenleme araçları
- Çeviri kalite kontrolü

### Kullanıcı Arayüzü
- Sezgisel ve kullanıcı dostu arayüz
- Gerçek zamanlı ilerleme takibi
- Bölüm düzenleme ve yönetimi
- Karakter editörü
- Roman detayları editörü
- Prompt editörü

### Veri Yönetimi
- JSON5 formatında veri saklama
- Karakter bilgilerini dışa/içe aktarma
- Roman detaylarını dışa/içe aktarma
- Stil rehberini dışa/içe aktarma
- Bölümleri dışa/içe aktarma

## Kurulum

1. Python 3.8 veya üstü sürümü yükleyin
2. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

3. `.env` dosyası oluşturun ve API anahtarlarınızı ekleyin:
```
AI_MODEL=gemini  # veya chatgpt
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
TARGET_COUNTRY=US  # varsayılan hedef ülke
```

## Kullanım

1. Programı başlatın:
```bash
python novel_translator.py
```

2. Roman dosyasını seçin
3. Hedef dili ve ülkeyi belirleyin
4. Romanın türünü seçin
5. Analiz işlemini başlatın
6. Çeviri sürecini başlatın
7. Gerekli düzenlemeleri yapın
8. Çeviriyi kaydedin

## Desteklenen Dosya Formatları
- Metin dosyaları (.txt)
- Markdown dosyaları (.md)

## Gereksinimler
- Python 3.8+
- re (>=2.2.1)
- time (>=0.0.0)
- langdetect (>=1.0.9)
- google-generativeai (>=0.3.2)
- python-dotenv (>=1.0.0)
- json5 (>=0.9.14)
- openai (>=1.12.0)
- tkinter (>=8.6)
- typing (>=3.7.4.3)

## Desteklenen AI Modelleri
- Google Gemini (gemini-1.5-flash-latest)
- OpenAI GPT-4 (gpt-4o-mini)

## Lisans
Bu proje MIT lisansı altında lisanslanmıştır.

## Katkıda Bulunma
1. Bu depoyu fork edin
2. Yeni bir özellik dalı oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Dalınıza push edin (`git push origin feature/amazing-feature`)
5. Bir Pull Request oluşturun 
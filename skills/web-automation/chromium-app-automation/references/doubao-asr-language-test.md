# Doubao Voice Chat — ASR Language Support Test

**Date:** 2026-06-14
**Method:** TTS → AIFF → BlackHole → Doubao Voice Chat → CDP transcript read
**Context:** Each language injected as a separate utterance in the same voice chat session.
**Note:** Some European languages (FR, DE, ES, PT, IT, AR) produced garbled English-like text as the ASR tried to fit non-EN/ZH audio to its phoneme model. Other languages (ID, TH, VI, TR, HI, MS, NL, PL) triggered no ASR at all.

## Results Table

| # | Language | Code | TTS Voice | Injected text | ASR output | AI understood? |
|---|----------|------|-----------|---------------|------------|----------------|
| 1 | **English** | en | Samantha | "Hello. I need a translator. Can you translate between English and Chinese?" | `"Hello, I need a translate."` | ✅ Full response in English |
| 2 | **Chinese** | zh | Tingting | "请把这句话翻译成英文..." | `"请把这句话翻译成英文..."` | ✅ Full response in English |
| 3 | **Japanese** | ja | Kyoko | "こんにちは。これは音声認識のテストです。" | `"老公"` (Chinese "husband") | ❌ Garbage |
| 4 | **Korean** | ko | Yuna | "안녕하세요. 이것은 음성 인식 테스트입니다." | `"老公"` | ❌ Garbage |
| 5 | **Russian** | ru | Milena | "Здравствуйте. Это тест распознавания речи." | `"老公"` | ❌ Garbage |
| 6 | **French** | fr | Thomas | "Bonjour. C'est un test de reconnaissance vocale." | `"boo"` | ❌ Garbage |
| 7 | **German** | de | Anna | "Hallo. Dies ist ein Spracherkennungstest." | `"boo sit do"` | ❌ Garbage |
| 8 | **Spanish** | es | Monica | "Hola. Esto es una prueba de reconocimiento de voz." | `"boo sit down"` | ❌ Garbage |
| 9 | **Portuguese** | pt | Luciana | "Olá. Este é um teste de reconhecimento de fala." | `"boo sit down s"` | ❌ Garbage |
| 10 | **Italian** | it | Alice | "Ciao. Questo è un test di riconoscimento vocale." | `"boo sit on the desk"` | ❌ Garbage |
| 11 | **Arabic** | ar | Majed | "مرحبا. هذا اختبار للتعرف على الكلام." | `"boo sit on the desk quest"` | ❌ Garbage |
| 12 | **Indonesian** | id | Damayanti | "Halo. Ini adalah tes pengenalan suara." | (silence) | ❌ No trigger |
| 13 | **Thai** | th | Kanya | "สวัสดีครับ นี่คือการทดสอบการรู้จำเสียง" | (silence) | ❌ No trigger |
| 14 | **Vietnamese** | vi | Linh | "Xin chào. Đây là bài kiểm tra nhận dạng giọng nói." | (silence) | ❌ No trigger |
| 15 | **Turkish** | tr | Yelda | "Merhaba. Bu bir konuşma tanıma testidir." | (silence) | ❌ No trigger |
| 16 | **Hindi** | hi | Lekha | "नमस्ते। यह वाक् पहचान परीक्षण है।" | (silence) | ❌ No trigger |
| 17 | **Malay** | ms | Amira | "Halo. Ini adalah ujian pengecaman pertuturan." | (silence) | ❌ No trigger |
| 18 | **Dutch** | nl | Xander | "Hallo. Dit is een spraakherkenningstest." | (silence) | ❌ No trigger |
| 19 | **Polish** | pl | Zosia | "Dzień dobry. To jest test rozpoznawania mowy." | (silence → "正在听...") | ❌ Mic triggered, no text |

## Conclusion

**Doubao voice chat ASR only supports English and Chinese.**
- 2/19 languages work (11%)
- 9/19 produce garbled text (forced into Chinese or English phoneme model)
- 8/19 produce no ASR output at all

The LLM behind Doubao can handle any language in text mode, but the speech-to-text frontend is strictly bilingual.

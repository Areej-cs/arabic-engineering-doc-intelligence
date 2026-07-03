# نظام ذكاء المستندات الهندسية العربية
### Arabic Engineering Document Intelligence System

نظام OCR + NLP لقراءة تقارير الصيانة والسلامة الصناعية المكتوبة بالعربي،
واستخراج المعلومات المهمة منها وتصنيفها تلقائيًا.

> **حالة المشروع:** في مرحلة الإعداد الأولي (هيكل المجلدات فقط — لا يوجد كود فعلي بعد).

---

## المكدس التقني (Tech Stack)

| الطبقة | التقنية |
|---|---|
| API | FastAPI |
| OCR | Tesseract / EasyOCR / (اختياريًا AWS Textract) |
| NLP | AraBERT (aubmindlab/bert-base-arabertv2) |
| لوحة التحكم | Streamlit |
| قاعدة البيانات | PostgreSQL |
| التخزين والبنية التحتية | AWS (S3, وغيرها لاحقًا) |

---

## هيكل المشروع

```
arabic-engineering-doc-intelligence/
├── src/app/                # كود التطبيق (FastAPI)
│   ├── core/                # الإعدادات، اللوجينج، الأمان
│   ├── api/v1/endpoints/    # مسارات الـ API
│   ├── ocr/                 # محرك الـ OCR ومعالجة الصور
│   ├── nlp/                 # AraBERT، التصنيف، استخراج المعلومات
│   ├── models/               # Pydantic schemas + ORM models
│   ├── services/              # منطق الأعمال (تنسيق OCR+NLP، S3، ...)
│   ├── db/                    # جلسة قاعدة البيانات + migrations
│   └── utils/                  # أدوات مساعدة
├── streamlit_app/            # لوحة التحكم (واجهة المستخدم)
│   ├── pages/
│   ├── components/
│   └── utils/
├── ml/                        # تدريب وتقييم النماذج
│   ├── notebooks/
│   ├── training/
│   ├── data_prep/
│   └── experiments/
├── data/                      # البيانات (raw / processed / annotated / samples)
├── models_store/              # أوزان النماذج المدرَّبة (لا تُرفع لـ git)
├── infra/aws/                 # البنية التحتية (Terraform، سكربتات النشر)
├── tests/                     # unit + integration tests
├── docs/                       # التوثيق
├── scripts/                    # سكربتات مساعدة عامة
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── .env.example
```

---

## الإعداد المحلي (لاحقًا عند بدء الكود)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
copy .env.example .env
```

---

## خطة العمل (على أيام منفصلة)

- [x] **اليوم 1:** هيكل المجلدات، requirements، pyproject.toml، README أولي
- [ ] بناء FastAPI الأساسي (config, main, health check)
- [ ] بناء محرك الـ OCR (معالجة الصور + استخراج النص العربي)
- [ ] دمج AraBERT (تصنيف + استخراج معلومات NER)
- [ ] بناء واجهة Streamlit
- [ ] إعداد AWS (S3، النشر)
- [ ] الاختبارات (tests) والـ CI/CD

---

## الترخيص

TBD

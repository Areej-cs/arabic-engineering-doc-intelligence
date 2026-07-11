"""Generates synthetic Arabic/English maintenance-report texts labeled Urgent/Normal/Low.

Mirrors the bilingual report format produced by the OCR sample
(src/app/ocr/sample_generator.py): "تقرير الصيانة ... - Maintenance Report",
"رقم المعدة: ...", "الموقع: ... - ...", "الحالة: ... - Status: ...".
"""

import random

LABELS = ["Urgent", "Normal", "Low"]

_EQUIPMENT_PREFIXES = ["PUMP", "VALVE", "MOTOR", "GEN", "COMP", "LINE"]

_LOCATIONS = [
    ("محطة الضخ الرئيسية", "Main Pumping Station"),
    ("وحدة التكرير", "Refining Unit"),
    ("خط الإنتاج رقم 3", "Production Line 3"),
    ("المستودع الرئيسي", "Main Warehouse"),
    ("غرفة المحركات", "Engine Room"),
    ("محطة الطاقة الفرعية", "Sub Power Station"),
    ("وحدة المعالجة الأولية", "Primary Treatment Unit"),
]

# (Arabic status phrase, English status phrase) per label
_STATUS_PHRASES = {
    "Urgent": [
        ("يحتاج صيانة عاجلة", "Urgent"),
        ("تسرب خطير يهدد السلامة", "Critical Leak"),
        ("توقف كامل عن العمل", "Complete Shutdown"),
        ("خطر انفجار محتمل", "Explosion Risk"),
        ("درجة حرارة مرتفعة جدًا وخطر حريق", "Fire Hazard"),
        ("اهتزاز غير طبيعي شديد", "Severe Vibration"),
        ("يجب الإيقاف الفوري للتشغيل", "Immediate Shutdown Required"),
    ],
    "Normal": [
        ("صيانة دورية مجدولة", "Scheduled Maintenance"),
        ("الأداء طبيعي ولا يوجد خلل", "Normal Operation"),
        ("فحص روتيني دون ملاحظات", "Routine Check"),
        ("تم استبدال الفلتر حسب الجدول", "Filter Replaced On Schedule"),
        ("تشغيل مستقر ضمن المعدلات الطبيعية", "Stable Operation"),
        ("تم تنظيف المعدة ضمن الصيانة الوقائية", "Preventive Cleaning Done"),
    ],
    "Low": [
        ("ملاحظة بسيطة يمكن تأجيلها", "Minor - Can Be Deferred"),
        ("تآكل طفيف لا يؤثر على الأداء", "Minor Wear"),
        ("أولوية منخفضة ولا حاجة لتدخل فوري", "Low Priority"),
        ("صوت خفيف غير مقلق أثناء التشغيل", "Minor Noise"),
        ("خدش سطحي بسيط في الطلاء الخارجي", "Cosmetic Scratch"),
        ("تراكم غبار بسيط يُنصح بتنظيفه لاحقًا", "Minor Dust Buildup"),
    ],
}

_TITLES = [
    ("تقرير الصيانة الدورية", "Maintenance Report"),
    ("تقرير فحص المعدة", "Equipment Inspection Report"),
    ("تقرير حالة التشغيل", "Operation Status Report"),
]


def _random_equipment_id() -> str:
    prefix = random.choice(_EQUIPMENT_PREFIXES)
    return f"{prefix}-{random.randint(100, 999)}"


def _random_date() -> str:
    year = random.randint(2024, 2026)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _generate_one(label: str) -> str:
    title_ar, title_en = random.choice(_TITLES)
    equipment_id = _random_equipment_id()
    location_ar, location_en = random.choice(_LOCATIONS)
    status_ar, status_en = random.choice(_STATUS_PHRASES[label])
    date = _random_date()
    return (
        f"{title_ar} - {title_en}\n"
        f"رقم المعدة: {equipment_id}\n"
        f"الموقع: {location_ar} - {location_en}\n"
        f"الحالة: {status_ar} - Status: {status_en}\n"
        f"تاريخ الفحص: {date}"
    )


def generate_dataset(samples_per_label: int = 80, seed: int = 42) -> tuple[list[str], list[str]]:
    """Returns (texts, labels), balanced across Urgent/Normal/Low."""
    rng = random.Random(seed)
    random.seed(seed)  # _generate_one uses the module-level `random` API

    texts: list[str] = []
    labels: list[str] = []
    for label in LABELS:
        seen: set[str] = set()
        attempts = 0
        while len(seen) < samples_per_label and attempts < samples_per_label * 50:
            text = _generate_one(label)
            attempts += 1
            if text not in seen:
                seen.add(text)
                texts.append(text)
                labels.append(label)

    combined = list(zip(texts, labels))
    rng.shuffle(combined)
    texts, labels = zip(*combined)
    return list(texts), list(labels)

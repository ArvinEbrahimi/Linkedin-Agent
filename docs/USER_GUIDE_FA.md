<div dir="rtl" align="right">

# راهنمای کامل کاربری LinkAid

**نسخه:** ۱.۰ · **زبان رابط:** فارسی + اصطلاحات فنی انگلیسی · **حالت:** فقط پیشنهاد (Suggest-only)

---

## این دستیار چیست؟

**LinkAid** یک دستیار هوش مصنوعی برای **برند شخصی لینکدین** است، مخصوص مهندسان نرم‌افزار ایرانی (Backend، Full-Stack، AI).

| LinkAid انجام می‌دهد | LinkAid انجام **نمی‌دهد** |
|---------------------|-------------------------|
| پیشنهاد پست، استراتژی، headline | پست خودکار در لینکدین |
| تحلیل پروفایل و پیشنهاد connection note | ارسال خودکار پیام یا درخواست اتصال |
| حافظه از niche، اهداف و پست‌های قبلی | اسکرپینگ غیرقانونی یا رفتار bot |

> ⚠️ **همهٔ خروجی‌ها پیشنهادی هستند.** شما تصمیم نهایی را می‌گیرید و خودتان در لینکدین کپی/ارسال می‌کنید.

---

## آدرس‌های در حال اجرا (روی سیستم شما)

| سرویس | آدرس | کاربرد |
|--------|------|--------|
| **رابط کاربری (Streamlit)** | [http://127.0.0.1:8501](http://127.0.0.1:8501) | کار روزمره — چت، تب‌ها، onboarding |
| **API** | [http://localhost:8000](http://localhost:8000) | موتور پشت‌صحنه |
| **مستندات API** | [http://localhost:8000/docs](http://localhost:8000/docs) | برای توسعه‌دهندگان |
| **وضعیت سلامت** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | چک آنلاین بودن |
| **چک‌لیست آماده‌بودن** | [http://localhost:8000/api/v1/ready](http://localhost:8000/api/v1/ready) | Groq و LinkedIn تنظیم شده؟ |

---

## پیش‌نیازها

### ۱. کلید Groq (الزامی برای هوش مصنوعی)

1. ثبت‌نام در [console.groq.com](https://console.groq.com)
2. ساخت API Key
3. در فایل `.env` در ریشهٔ پروژه:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
```

بدون این کلید، API بالا می‌آید ولی چت و تولید محتوا خطا می‌دهد.

### ۲. نصب (یک‌بار)

```bash
cd d:\projects\Linkedin_Agent
pip install -e ".[dev,ui]"
```

### ۳. اجرای دستی (هر بار)

**ترمینال ۱ — API:**
```bash
make run
# یا: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**ترمینال ۲ — رابط کاربری:**
```bash
make run-ui
# یا: streamlit run app/ui/streamlit_app.py
```

سپس مرورگر: **http://127.0.0.1:8501**

---

## اولین بار: مسیر ۵ دقیقه‌ای

```
۱. باز کردن UI  →  ۲. Onboarding  →  ۳. تب Setup  →  ۴. تولید اولین پست  →  ۵. کپی در لینکدین
```

### گام ۱ — Onboarding (ویزارد خوش‌آمد)

بعد از اولین باز کردن UI، ویزارد ۴ مرحله‌ای نمایش داده می‌شود:

| مرحله | چه چیزی وارد کنید | مثال |
|-------|-------------------|------|
| ۱. دربارهٔ شما | نام، نقش، سال تجربه | علی · Backend · ۵ سال |
| ۲. حوزه تخصصی | niche، tech stack، اهداف | LLM agents for fintech · Python, FastAPI · remote jobs |
| ۳. سبک | tone، زبان، فرکانس پست | professional · fa-en · 2-5/week |
| ۴. رقبا (اختیاری) | نام رقبای محتوایی | Alice Dev, Bob ML |

این اطلاعات در **حافظهٔ بلندمدت** ذخیره می‌شود و همهٔ ماژول‌ها از آن استفاده می‌کنند.

### گام ۲ — تب ⚙️ Setup

| بخش | توضیح |
|-----|--------|
| **AI readiness** | اگر Groq سبز است، آماده‌اید |
| **Connect LinkedIn** | ورود با LinkedIn (فقط نام و ایمیل — اختیاری) |
| **Import ZIP** | **مهم‌ترین قدم** — آرشیو داده از لینکدین (پست‌ها + headline) |

#### Import از LinkedIn (توصیهٔ جدی)

1. لینکدین → **Settings & Privacy** → **Data privacy**
2. **Get a copy of your data** → انتخاب **Posts** و **Profile**
3. وقتی ZIP آماده شد، در تب Setup آپلود کنید
4. Advisor و Strategy از پست‌های import‌شده یاد می‌گیرند

راهنمای OAuth: [LINKEDIN_SETUP.md](LINKEDIN_SETUP.md)

### گام ۳ — اولین پست

1. تب **📝 Content**
2. Mode: **Single post**
3. Topic: مثلاً `سه درس از deploy کردن LLM agent در production`
4. Post type: `text`
5. Language: `fa-en`
6. **Generate** → دکمهٔ **📋 Copy** روی «Full Post»

---

## نوار کناری (Sidebar)

| فیلد | کاربرد |
|------|--------|
| **API URL** | معمولاً `http://localhost:8000` — اگر API جای دیگری است عوض کنید |
| **User ID** | شناسهٔ شما در حافظه — هر دستگاه یک ID ثابت نگه دارید |
| **UI language mix** | `fa-en` برای متن ترکیبی فارسی/انگلیسی |
| **Reset onboarding** | شروع دوبارهٔ ویزارد |

---

## تب‌ها — راهنمای کامل

### 💬 Chat — چت با Supervisor

چندنوبتی با حافظهٔ thread:

- هر مکالمه یک **Thread ID** دارد (بالای چت نمایش داده می‌شود)
- **New thread** = مکالمهٔ تازه
- مثال پیام‌ها:
  - `یک پست لینکدین دربارهٔ FastAPI بنویس`
  - `برای این پروفایل connection note بده: [متن پروفایل]`
  - `برنامهٔ محتوای ۴ هفته‌ای بده`
  - `صبحانهٔ امروز لینکدینم چی باشه؟`

خروجی همیشه ۶ بخش است: Understanding · Main Recommendation · Alternatives · Strategic Reasoning · Execution Tips · Follow-up Question

---

### 📝 Content — تولید محتوا

| حالت | کاربرد |
|------|--------|
| **Single post** | یک پست کامل + ۳ hook + CTA + هشتگ + first comment |
| **30-day campaign** | برنامهٔ ۳۰ روزه با تم هفتگی |

**انواع پست:** text · carousel · video · poll · document

**نکتهٔ الگوریتم ۲۰۲۶ (در پیشنهادها لحاظ شده):**
- لینک خارجی را در **first comment** بگذارید، نه در بدنهٔ پست
- carousel و document بیشترین save را می‌گیرند
- ۲ تا ۵ پست باکیفیت در هفته

---

### 🤝 Networking — شبکه‌سازی

| حالت | ورودی | خروجی |
|------|-------|--------|
| **Profile SWOT** | متن پروفایل هدف (paste از لینکدین) | SWOT · icebreaker · connection note ≤۳۰۰ کاراکتر |
| **Outreach sequence** | همان + context شما | ۳ مرحله follow-up |

**محدودیت:** حداکثر **۲۰ پیشنهاد outreach در روز** (در API ذخیره می‌شود).

**روش عملی:**
1. پروفایل شخص را در لینکدین باز کنید
2. متن headline + about + experience را کپی کنید
3. در Networking paste کنید
4. connection note پیشنهادی را Copy کنید
5. **خودتان** در لینکدین Send بزنید

---

### 👤 Profile — بهینه‌سازی پروفایل

| Section | ورودی | خروجی |
|---------|-------|--------|
| headline | headline فعلی | ۳ variant ≤۲۲۰ کاراکتر |
| about | متن About | ساختار Problem → Proof → CTA |
| experience | bulletهای فعلی | بازنویسی با عدد و متریک |
| featured / skills / full | محتوای فعلی | پیشنهاد بهینه |

---

### ☀️ Advisor — مشاور روزانه

| حالت | کاربرد |
|------|--------|
| **Morning briefing** | تمرکز امروز: چه پستی، با چه کسی engage کنی |
| **Post analysis** | paste پست + impressions/likes/saves → تحلیل |
| **Outreach list** | لیست اولویت‌بندی‌شده برای امروز (تا ۲۰) |

**برای تحلیل دقیق‌تر:** اول ZIP لینکدین را import کنید یا پست‌ها را دستی در memory ذخیره کنید.

---

### 🎯 Strategy — استراتژی برند

| حالت | خروجی |
|------|--------|
| **Personal narrative** | positioning + elevator pitch |
| **Competitor analysis** | جدول مقایسه + زوایای تمایز + SWOT |
| **Content calendar** | تقویم ۱ تا ۸ هفته با نوع پست و hook |

نام رقبا را با کاما جدا کنید: `Alice Dev, Bob ML`

---

### ⚙️ Setup — راه‌اندازی و LinkedIn

همان بخش onboarding تکمیلی: Groq · OAuth · Import ZIP

---

## افزونهٔ Chrome (روی خود لینکدین)

### نصب

1. API باید روشن باشد (`make run`)
2. Chrome → `chrome://extensions` → **Developer mode**
3. **Load unpacked** → پوشهٔ `extension/` در پروژه
4. آیکن LinkAid → API URL و User ID را مثل sidebar تنظیم کنید

### استفاده

| صفحه | دکمه | نتیجه |
|------|------|--------|
| پروفایل `/in/username` | **Analyze this profile** | SWOT + connection note |
| Feed / Compose | **Draft post idea** | متن داخل compose (شما Post می‌زنید) |

پنل شناور پایین‑راست صفحه ظاهر می‌شود.

جزئیات: [extension/README.md](../extension/README.md)

---

## سناریوهای عملی

### سناریو ۱ — روز کاری معمولی (۱۵ دقیقه)

1. تب Advisor → **Get today's briefing**
2. طبق briefing یک کامنت هدفمند بگذارید (خودتان)
3. تب Content → پست امروز را Generate → Copy → در لینکدین paste
4. لینک را در **first comment** بگذارید

### سناریو ۲ — آماده‌سازی برای جستجوی کار remote

1. Onboarding: هدف = `remote EU jobs`
2. Strategy → **Personal narrative**
3. Profile → بهینهٔ headline و about
4. Content → کمپین ۳۰ روزه با niche تخصصی
5. Networking → تحلیل پروفایل recruiter هدف

### سناریو ۳ — رشد thought leadership

1. Import ZIP پست‌های قبلی
2. Advisor → **Post analysis** روی پرsaveترین پست
3. Strategy → **Content calendar** ۴ هفته
4. هفته‌ای ۲–۳ پست طبق تقویم

### سناریو ۴ — اتصال با یک senior engineer

1. پروفایل را در لینکدین باز کنید
2. Extension → **Analyze** یا Networking tab با paste
3. اول روی پست اخیرشان کامنت بگذارید (خودتان)
4. connection note پیشنهادی را Copy و ارسال کنید

---

## ساختار خروجی AI (۶ بخش)

هر پیشنهاد LinkAid این ساختار را دارد:

1. **Understanding** — فهم درخواست شما
2. **Main Recommendation** — پیشنهاد اصلی (آمادهٔ copy)
3. **Alternatives** — ۲–۳ گزینهٔ جایگزین
4. **Strategic Reasoning** — چرا با الگوریتم ۲۰۲۶ هم‌خوان است
5. **Execution Tips** — زمان، طول، ریسک
6. **Follow-up Question** — سوال برای جزئیات بیشتر

---

## دکمهٔ Copy

کنار هر بلوک متنی دکمهٔ **📋 Copy** هست — یک کلیک برای کپی در کلیپ‌بورد.

متن فارسی به‌صورت خودکار **RTL** نمایش داده می‌شود.

---

## بنر هشدار (Disclaimer)

بالای UI همیشه نمایش داده می‌شود:

> LinkAid فقط پیشنهاد می‌دهد — هیچ اقدام خودکاری در لینکدین انجام نمی‌شود.

---

## عیب‌یابی

| مشکل | راه‌حل |
|------|--------|
| Sidebar: API offline | `make run` را در ترمینال اجرا کنید |
| Groq not configured | `GROQ_API_KEY` در `.env` |
| چت خطای ۵۰۰ | کلید Groq را چک کنید؛ quota console.groq.com |
| UI باز نمی‌شود | `pip install streamlit` سپس `make run-ui` |
| LinkedIn Connect کار نمی‌کند | `LINKEDIN_CLIENT_ID/SECRET` — [LINKEDIN_SETUP.md](LINKEDIN_SETUP.md) |
| Import ZIP خالی | مطمئن شوید Posts و Profile در export انتخاب شده |
| Extension پنل نمی‌آید | صفحهٔ profile یا feed لینکدین باشد؛ API روشن باشد |
| outreach limit | فردا دوباره — حد ۲۰/روز |
| متن فارسی برعکس | language mix = `fa-en`؛ متن باید حروف فارسی داشته باشد |

### چک سریع از ترمینال

```bash
make e2e          # health + openapi
make e2e-chat     # + تست چت (نیاز به Groq)
```

---

## Docker (اختیاری)

```bash
cp .env.example .env   # GROQ_API_KEY را پر کنید
make docker-up
```

- API: http://localhost:8000  
- UI: http://localhost:8501  

---

## خلاصهٔ مسیرهای API (برای مرجع)

| مسیر | کار |
|------|-----|
| `POST /api/v1/chat` | چت supervisor |
| `POST /api/v1/content/post` | تولید پست |
| `POST /api/v1/networking/analyze` | SWOT پروفایل |
| `POST /api/v1/profile/optimize` | بهینه headline/about |
| `POST /api/v1/advisor/briefing` | briefing صبح |
| `POST /api/v1/strategy/narrative` | narrative برند |
| `POST /api/v1/linkedin/import/{user_id}` | آپلود ZIP |
| `GET /api/v1/ready` | چک آماده‌بودن |

---

## نکات ویژهٔ کاربران ایرانی

- محتوای **متنی و carousel** در اولویت — video اگر bandwidth محدود است
- شرکت‌های local (اسنپ، دیجی‌کالا، کافه‌بازار) و remote EU/US را با هم در niche بگنجانید
- Groq free tier برای شروع کافی است؛ قبل از paid بودن API هشدار بگیرید
- فرض نکنید همه LinkedIn Premium دارند

---

## چک‌لیست «آمادهٔ استفاده»

- [ ] `GROQ_API_KEY` در `.env`
- [ ] `make run` — API سبز در `/api/v1/health`
- [ ] `make run-ui` — UI روی :8501
- [ ] Onboarding تکمیل شده
- [ ] (توصیه) ZIP لینکدین import شده
- [ ] (اختیاری) Extension نصب شده
- [ ] (اختیاری) LinkedIn OAuth متصل شده

---

## پشتیبانی و توسعه

- معماری: [ARCHITECTURE.md](ARCHITECTURE.md)
- محصول: [PRODUCT_SPEC.md](PRODUCT_SPEC.md)
- تسک‌ها: [TASKS.md](../TASKS.md)

---

*آخرین به‌روزرسانی: ژوئن ۲۰۲۶ · LinkAid v1*

</div>


---

# 12. `README.fa.md`

نسخه فارسی را هم جدا می‌گذاریم:

```markdown
# Telegram Ad Userbot

یک Userbot محلی مبتنی بر Pyrogram برای مدیریت کمپین‌های تبلیغاتی کنترل‌شده در Telegram.

## امکانات

- استفاده از اکانت شخصی Telegram
- کنترل از طریق Saved Messages
- دیتابیس SQLite
- شناسایی گروه‌های موجود در Archive
- ساخت Campaign
- تعیین فاصله بین ارسال‌ها
- تعیین فاصله بین Roundها
- توقف و ادامه Campaign
- مشاهده وضعیت
- ثبت History
- ذخیره دائمی وضعیت

## نکته مهم

این پروژه به‌صورت خودکار گروهی را Join، Archive یا Leave نمی‌کند و برای دور زدن سیستم‌های ضد سوءاستفاده Telegram طراحی نشده است.

فقط گروه‌هایی که کاربر خودش قبلاً عضو شده و در Archive قرار داده است می‌توانند Target کمپین باشند.

## پیش‌نیاز

Python 3.10 یا بالاتر

## نصب

Repository را دریافت کنید:

```bash
git clone <REPOSITORY_URL>
cd telegram-ad-userbot
# دليل التثبيت - نظام إدارة الطلاب

## متطلبات النظام

### متطلبات البرمجيات
- **Odoo 18.0** أو أحدث
- **Python 3.8+**
- **PostgreSQL 12+**
- **Git** (للحصول على الكود المصدري)

### متطلبات الأجهزة
- **ذاكرة الوصول العشوائي**: 4 GB كحد أدنى، 8 GB مُوصى به
- **مساحة القرص الصلب**: 10 GB كحد أدنى
- **المعالج**: معالج ثنائي النواة أو أفضل

## التثبيت خطوة بخطوة

### 1. تحضير البيئة

#### تثبيت Odoo 18
```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت المتطلبات
sudo apt install -y python3-pip python3-dev python3-venv
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y git curl wget

# إنشاء مستخدم Odoo
sudo adduser --system --home=/opt/odoo --group odoo

# تحميل Odoo 18
sudo git clone https://www.github.com/odoo/odoo --depth 1 --branch 18.0 /opt/odoo/odoo18
sudo chown -R odoo:odoo /opt/odoo/
```

#### إعداد قاعدة البيانات
```bash
# إنشاء مستخدم PostgreSQL
sudo -u postgres createuser -s odoo
sudo -u postgres psql -c "ALTER USER odoo PASSWORD 'odoo_password';"

# إنشاء قاعدة بيانات
sudo -u postgres createdb -O odoo student_management_db
```

### 2. تثبيت التطبيق

#### نسخ ملفات التطبيق
```bash
# إنشاء مجلد addons مخصص
sudo mkdir -p /opt/odoo/custom-addons
sudo chown -R odoo:odoo /opt/odoo/custom-addons

# نسخ تطبيق إدارة الطلاب
sudo cp -r /path/to/odoo_student_management /opt/odoo/custom-addons/
sudo chown -R odoo:odoo /opt/odoo/custom-addons/odoo_student_management
```

#### إعداد ملف التكوين
```bash
# إنشاء ملف التكوين
sudo nano /etc/odoo.conf
```

محتوى ملف التكوين:
```ini
[options]
; This is the password that allows database operations:
admin_passwd = admin_password
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo_password
addons_path = /opt/odoo/odoo18/addons,/opt/odoo/custom-addons
logfile = /var/log/odoo/odoo.log
log_level = info
```

### 3. إنشاء خدمة النظام

#### إنشاء ملف الخدمة
```bash
sudo nano /etc/systemd/system/odoo.service
```

محتوى ملف الخدمة:
```ini
[Unit]
Description=Odoo
Documentation=http://www.odoo.com
After=network.target postgresql.service

[Service]
Type=simple
SyslogIdentifier=odoo
PermissionsStartOnly=true
User=odoo
Group=odoo
ExecStart=/opt/odoo/odoo18/odoo-bin -c /etc/odoo.conf
StandardOutput=journal+console

[Install]
WantedBy=multi-user.target
```

#### تفعيل وبدء الخدمة
```bash
# إنشاء مجلد السجلات
sudo mkdir /var/log/odoo
sudo chown odoo:odoo /var/log/odoo

# تفعيل الخدمة
sudo systemctl daemon-reload
sudo systemctl enable odoo
sudo systemctl start odoo

# التحقق من حالة الخدمة
sudo systemctl status odoo
```

### 4. الوصول إلى النظام

#### فتح المتصفح
1. افتح المتصفح وانتقل إلى: `http://localhost:8069`
2. أنشئ قاعدة بيانات جديدة:
   - **اسم قاعدة البيانات**: student_management_db
   - **البريد الإلكتروني**: admin@example.com
   - **كلمة المرور**: admin_password
   - **اللغة**: العربية
   - **البلد**: المملكة العربية السعودية

#### تثبيت التطبيق
1. انتقل إلى قائمة "التطبيقات"
2. احذف الفلتر الافتراضي واكتب "Student Management"
3. اضغط على "تثبيت" بجانب "Student Management System"

## التحقق من التثبيت

### اختبار الوظائف الأساسية

#### 1. إنشاء مقرر دراسي
```bash
# انتقل إلى Student Management → Academic → Courses
# اضغط على "إنشاء" وأدخل:
# - اسم المقرر: علوم الحاسوب
# احفظ السجل
```

#### 2. إنشاء موظف
```bash
# انتقل إلى Student Management → Staff → All Staff
# اضغط على "إنشاء" وأدخل:
# - الاسم: د. أحمد محمد
# - البريد الإلكتروني: ahmed@university.edu
# - كلمة المرور: staff123
# احفظ السجل
```

#### 3. إنشاء طالب
```bash
# انتقل إلى Student Management → Students → All Students
# اضغط على "إنشاء" وأدخل:
# - الاسم: فاطمة علي
# - البريد الإلكتروني: fatima@student.edu
# - الجنس: أنثى
# - المقرر: علوم الحاسوب
# - كلمة المرور: student123
# احفظ السجل
```

### اختبار API

#### اختبار API باستخدام curl
```bash
# الحصول على قائمة الطلاب
curl -X POST \
  http://localhost:8069/student_management/api/students \
  -H 'Content-Type: application/json' \
  -d '{}'
```

## استكشاف الأخطاء

### مشاكل شائعة وحلولها

#### 1. خطأ في الاتصال بقاعدة البيانات
```
psycopg2.OperationalError: FATAL: password authentication failed
```
**الحل:**
```bash
# التحقق من إعدادات PostgreSQL
sudo -u postgres psql -c "\du"
# إعادة تعيين كلمة مرور المستخدم
sudo -u postgres psql -c "ALTER USER odoo PASSWORD 'new_password';"
```

#### 2. خطأ في الصلاحيات
```
PermissionError: [Errno 13] Permission denied
```
**الحل:**
```bash
# إصلاح صلاحيات الملفات
sudo chown -R odoo:odoo /opt/odoo/
sudo chmod -R 755 /opt/odoo/
```

#### 3. خطأ في تحميل التطبيق
```
ImportError: No module named 'student_management'
```
**الحل:**
```bash
# التحقق من مسار addons
grep addons_path /etc/odoo.conf
# التأكد من وجود التطبيق
ls -la /opt/odoo/custom-addons/odoo_student_management/
```

#### 4. خطأ في البورت
```
OSError: [Errno 98] Address already in use
```
**الحل:**
```bash
# العثور على العملية التي تستخدم البورت
sudo lsof -i :8069
# إيقاف العملية
sudo kill -9 <PID>
# أو تغيير البورت في ملف التكوين
```

### فحص السجلات

#### عرض سجلات Odoo
```bash
# عرض السجلات المباشرة
sudo journalctl -u odoo -f

# عرض سجلات الأخطاء
sudo tail -f /var/log/odoo/odoo.log | grep ERROR

# عرض سجلات التطبيق
sudo tail -f /var/log/odoo/odoo.log | grep student_management
```

## التحديث والصيانة

### تحديث التطبيق

#### تحديث الكود
```bash
# إيقاف الخدمة
sudo systemctl stop odoo

# نسخ احتياطية
sudo cp -r /opt/odoo/custom-addons/odoo_student_management /opt/odoo/backup/

# تحديث الملفات
sudo cp -r /path/to/new/odoo_student_management /opt/odoo/custom-addons/
sudo chown -R odoo:odoo /opt/odoo/custom-addons/odoo_student_management

# تحديث قاعدة البيانات
sudo -u odoo /opt/odoo/odoo18/odoo-bin -c /etc/odoo.conf -u odoo_student_management -d student_management_db --stop-after-init

# بدء الخدمة
sudo systemctl start odoo
```

### النسخ الاحتياطي

#### نسخ احتياطي لقاعدة البيانات
```bash
# إنشاء نسخة احتياطية
sudo -u postgres pg_dump student_management_db > /opt/odoo/backup/db_backup_$(date +%Y%m%d_%H%M%S).sql

# ضغط النسخة الاحتياطية
gzip /opt/odoo/backup/db_backup_*.sql
```

#### نسخ احتياطي للملفات
```bash
# نسخ احتياطي للتطبيق
sudo tar -czf /opt/odoo/backup/app_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /opt/odoo/custom-addons odoo_student_management

# نسخ احتياطي لملف التكوين
sudo cp /etc/odoo.conf /opt/odoo/backup/odoo.conf.backup
```

### استعادة النسخ الاحتياطية

#### استعادة قاعدة البيانات
```bash
# إيقاف Odoo
sudo systemctl stop odoo

# حذف قاعدة البيانات الحالية
sudo -u postgres dropdb student_management_db

# إنشاء قاعدة بيانات جديدة
sudo -u postgres createdb -O odoo student_management_db

# استعادة النسخة الاحتياطية
sudo -u postgres psql student_management_db < /opt/odoo/backup/db_backup_YYYYMMDD_HHMMSS.sql

# بدء Odoo
sudo systemctl start odoo
```

## الأمان

### تأمين النظام

#### تغيير كلمات المرور الافتراضية
```bash
# تغيير كلمة مرور admin في Odoo
# انتقل إلى Settings → Users & Companies → Users
# اختر المستخدم admin وغير كلمة المرور
```

#### تفعيل HTTPS
```bash
# تثبيت Nginx
sudo apt install nginx

# إعداد SSL certificate
sudo apt install certbot python3-certbot-nginx

# الحصول على شهادة SSL
sudo certbot --nginx -d yourdomain.com
```

#### إعداد Firewall
```bash
# تفعيل UFW
sudo ufw enable

# السماح بالاتصالات الضرورية
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# منع الوصول المباشر لبورت Odoo
sudo ufw deny 8069
```

## الدعم الفني

### معلومات الاتصال
- **البريد الإلكتروني**: support@example.com
- **الهاتف**: +966-XX-XXX-XXXX
- **ساعات العمل**: الأحد - الخميس، 8:00 ص - 5:00 م

### الموارد المفيدة
- [دليل المستخدم](USER_GUIDE.md)
- [وثائق API](API_DOCUMENTATION.md)
- [الأسئلة الشائعة](FAQ.md)

---

**ملاحظة**: هذا الدليل يفترض استخدام نظام Ubuntu/Debian. للأنظمة الأخرى، قد تحتاج لتعديل الأوامر حسب نظام التشغيل المستخدم.


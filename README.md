# نظام إدارة الطلاب - Odoo 18

## نظرة عامة

نظام إدارة الطلاب هو تطبيق شامل مطور باستخدام Odoo 18 لإدارة العمليات الأكاديمية والإدارية في المؤسسات التعليمية. يوفر النظام واجهات مختلفة للطلاب والموظفين ورؤساء الأقسام، مع إمكانيات متقدمة لإدارة الحضور والإجازات والإشعارات والملاحظات.

## الميزات الرئيسية

### إدارة الطلاب
- تسجيل وإدارة بيانات الطلاب
- ربط الطلاب بالمقررات الدراسية
- تتبع الحضور والغياب
- إدارة طلبات الإجازة
- نظام الإشعارات والملاحظات

### إدارة الموظفين
- تسجيل وإدارة بيانات الموظفين
- ربط الموظفين بالمواد الدراسية
- إدارة طلبات الإجازة للموظفين
- نظام التواصل والإشعارات

### إدارة المقررات والمواد
- إنشاء وإدارة المقررات الدراسية
- ربط المواد بالمقررات والموظفين
- تنظيم الهيكل الأكاديمي

### نظام الحضور
- تسجيل الحضور للطلاب
- تقارير الحضور التفصيلية
- إحصائيات الحضور والغياب

### نظام التواصل
- إرسال الإشعارات للطلاب والموظفين
- نظام الملاحظات والاستفسارات
- الرد على الملاحظات من قبل الإدارة

## متطلبات النظام

- Odoo 18.0 أو أحدث
- Python 3.8+
- PostgreSQL 12+
- نظام تشغيل Linux/Windows/macOS

## التثبيت

### 1. نسخ الملفات
```bash
cp -r odoo_student_management /path/to/odoo/addons/
```

### 2. تحديث قائمة التطبيقات
```bash
./odoo-bin -u all -d your_database
```

### 3. تثبيت التطبيق
1. انتقل إلى قائمة التطبيقات في Odoo
2. ابحث عن "Student Management System"
3. اضغط على "تثبيت"

## الهيكل التقني

### النماذج (Models)

#### 1. نموذج الطلاب (student.student)
```python
class Student(models.Model):
    _name = 'student.student'
    _description = 'Student'
    
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    course_id = fields.Many2one('student.course', string='Course')
    # ... المزيد من الحقول
```

#### 2. نموذج الموظفين (student.staff)
```python
class Staff(models.Model):
    _name = 'student.staff'
    _description = 'Staff'
    
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    # ... المزيد من الحقول
```

#### 3. نموذج المقررات (student.course)
```python
class Course(models.Model):
    _name = 'student.course'
    _description = 'Course'
    
    course_name = fields.Char(string='Course Name', required=True)
    # ... المزيد من الحقول
```

### العلاقات بين النماذج

- **الطلاب ← المقررات**: علاقة Many2one (طالب واحد ينتمي لمقرر واحد)
- **المواد ← المقررات**: علاقة Many2one (مادة واحدة تنتمي لمقرر واحد)
- **المواد ← الموظفين**: علاقة Many2one (مادة واحدة يدرسها موظف واحد)
- **الحضور ← المواد**: علاقة Many2one (سجل حضور واحد لمادة واحدة)
- **تقارير الحضور ← الطلاب**: علاقة Many2one (تقرير حضور واحد لطالب واحد)

### واجهات المستخدم (Views)

#### 1. واجهة الطلاب
- عرض قائمة الطلاب (Tree View)
- نموذج تفاصيل الطالب (Form View)
- البحث والتصفية (Search View)

#### 2. واجهة الموظفين
- عرض قائمة الموظفين
- نموذج تفاصيل الموظف
- إدارة المواد المرتبطة

#### 3. واجهة المقررات والمواد
- إدارة المقررات الدراسية
- ربط المواد بالمقررات والموظفين

### المتحكمات (Controllers)

#### API Endpoints

```python
# الحصول على قائمة الطلاب
@http.route('/student_management/api/students', type='json', auth='user')
def get_students(self, **kwargs):
    # منطق الحصول على الطلاب

# إنشاء طالب جديد
@http.route('/student_management/api/student/create', type='json', auth='user')
def create_student(self, **kwargs):
    # منطق إنشاء طالب جديد

# الموافقة على طلب إجازة
@http.route('/student_management/api/leave/approve/<int:leave_id>', type='json', auth='user')
def approve_leave(self, leave_id, **kwargs):
    # منطق الموافقة على الإجازة
```

### الأمان والصلاحيات

#### مجموعات المستخدمين
1. **مدير النظام** (group_student_management_admin)
   - صلاحيات كاملة على جميع البيانات
   - إدارة الطلاب والموظفين
   - الموافقة على الطلبات

2. **الموظفين** (group_student_management_staff)
   - عرض بيانات الطلاب
   - تسجيل الحضور
   - إدارة بياناتهم الشخصية

3. **الطلاب** (group_student_management_student)
   - عرض بياناتهم الشخصية فقط
   - تقديم طلبات الإجازة
   - عرض الإشعارات

#### قواعد الأمان (Record Rules)
```xml
<!-- الطلاب يمكنهم رؤية سجلاتهم فقط -->
<record id="student_rule_own_records" model="ir.rule">
    <field name="name">Students can only see their own records</field>
    <field name="model_id" ref="model_student_student"/>
    <field name="domain_force">[('id', '=', user.partner_id.student_id)]</field>
</record>
```

## دليل الاستخدام

### للمديرين

#### إضافة طالب جديد
1. انتقل إلى قائمة "Student Management" → "Students" → "All Students"
2. اضغط على "إنشاء"
3. املأ البيانات المطلوبة
4. احفظ السجل

#### إدارة المقررات
1. انتقل إلى "Academic" → "Courses"
2. أنشئ مقرر جديد أو عدل مقرر موجود
3. أضف المواد المرتبطة بالمقرر

### للموظفين

#### تسجيل الحضور
1. انتقل إلى "Attendance" → "Attendance Records"
2. أنشئ سجل حضور جديد
3. اختر المادة والتاريخ
4. سجل حضور الطلاب

#### إرسال إشعار
1. استخدم API endpoint لإرسال الإشعارات
2. حدد نوع المستقبل (طلاب أو موظفين)
3. اكتب الرسالة وأرسلها

### للطلاب

#### عرض الحضور
1. انتقل إلى ملفك الشخصي
2. اختر تبويب "Attendance"
3. راجع سجلات الحضور

#### تقديم طلب إجازة
1. انتقل إلى "Communication" → "Leave Requests"
2. أنشئ طلب إجازة جديد
3. املأ التفاصيل المطلوبة

## API Documentation

### Authentication
جميع API endpoints تتطلب مصادقة المستخدم (`auth='user'`)

### Students API

#### GET /student_management/api/students
إرجاع قائمة بجميع الطلاب

**Response:**
```json
[
    {
        "id": 1,
        "name": "أحمد محمد",
        "email": "ahmed@example.com",
        "gender": "male",
        "course": "علوم الحاسوب"
    }
]
```

#### POST /student_management/api/student/create
إنشاء طالب جديد

**Request Body:**
```json
{
    "name": "فاطمة علي",
    "email": "fatima@example.com",
    "gender": "female",
    "password": "password123",
    "course_id": 1
}
```

### Leave Management API

#### POST /student_management/api/leave/approve/{leave_id}
الموافقة على طلب إجازة

#### POST /student_management/api/leave/reject/{leave_id}
رفض طلب إجازة

### Notifications API

#### POST /student_management/api/notification/send
إرسال إشعار

**Request Body:**
```json
{
    "type": "student",
    "message": "إشعار مهم للطلاب",
    "recipient_ids": [1, 2, 3]
}
```

## استكشاف الأخطاء

### مشاكل شائعة

#### خطأ في التثبيت
```
ModuleNotFoundError: No module named 'student_management'
```
**الحل:** تأكد من وضع المجلد في مسار addons الصحيح

#### خطأ في قاعدة البيانات
```
ProgrammingError: relation "student_student" does not exist
```
**الحل:** قم بتحديث قاعدة البيانات باستخدام `-u all`

#### خطأ في الصلاحيات
```
AccessError: You are not allowed to access this document
```
**الحل:** تأكد من إضافة المستخدم للمجموعة المناسبة

### سجلات النظام (Logs)

لتفعيل سجلات مفصلة:
```bash
./odoo-bin --log-level=debug --log-handler=odoo.addons.student_management:DEBUG
```

## التطوير والتخصيص

### إضافة حقول جديدة

#### إضافة حقل للطلاب
```python
# في models/student.py
class Student(models.Model):
    _inherit = 'student.student'
    
    phone_number = fields.Char(string='Phone Number')
    birth_date = fields.Date(string='Birth Date')
```

#### تحديث الواجهة
```xml
<!-- في views/student_views.xml -->
<field name="phone_number"/>
<field name="birth_date"/>
```

### إضافة API جديد

```python
# في controllers/main.py
@http.route('/student_management/api/custom_endpoint', type='json', auth='user')
def custom_endpoint(self, **kwargs):
    # منطق مخصص
    return {'success': True}
```

### إضافة تقارير

```python
# إنشاء تقرير جديد
class StudentReport(models.TransientModel):
    _name = 'student.report.wizard'
    
    def generate_report(self):
        # منطق إنشاء التقرير
        pass
```

## الأداء والتحسين

### فهرسة قاعدة البيانات
```sql
-- إضافة فهارس لتحسين الأداء
CREATE INDEX idx_student_course ON student_student(course_id);
CREATE INDEX idx_attendance_date ON student_attendance(date_time);
```

### تحسين الاستعلامات
```python
# استخدام prefetch لتحسين الأداء
students = self.env['student.student'].search([]).with_prefetch(['course_id'])
```

## النسخ الاحتياطي والاستعادة

### إنشاء نسخة احتياطية
```bash
pg_dump -h localhost -U odoo -d database_name > backup.sql
```

### استعادة النسخة الاحتياطية
```bash
psql -h localhost -U odoo -d database_name < backup.sql
```

## الدعم والمساعدة

### الوثائق الرسمية
- [Odoo Documentation](https://www.odoo.com/documentation/18.0/)
- [Odoo Developer Documentation](https://www.odoo.com/documentation/18.0/developer.html)

### المجتمع
- [Odoo Community Forum](https://www.odoo.com/forum)
- [GitHub Repository](https://github.com/odoo/odoo)

### الإبلاغ عن الأخطاء
لإبلاغ عن خطأ أو طلب ميزة جديدة، يرجى إنشاء issue في مستودع المشروع.

## الترخيص

هذا المشروع مرخص تحت رخصة LGPL-3.0. راجع ملف LICENSE للمزيد من التفاصيل.

## المساهمة

نرحب بالمساهمات! يرجى قراءة دليل المساهمة قبل تقديم pull request.

## تاريخ الإصدارات

### الإصدار 1.0.0
- الإصدار الأولي
- النماذج الأساسية للطلاب والموظفين والمقررات
- نظام الحضور والإجازات
- واجهات المستخدم الأساسية
- API endpoints للعمليات الأساسية

---

**تم التطوير بواسطة:** Manus AI  
**تاريخ آخر تحديث:** 2025-02-08  
**الإصدار:** 1.0.0


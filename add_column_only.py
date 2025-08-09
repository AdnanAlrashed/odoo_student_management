import psycopg2

# بيانات الاتصال بقاعدة بيانات أودو (يجب تعديلها حسب إعداداتك)
DB_CONFIG = {
    "dbname": "isms1",
    "user": "postgres",  # المستخدم الافتراضي لأودو
    "password": "Aa112212345",  # كلمة المرور الافتراضية
    "host": "localhost",
    "port": "5432"
}

try:
    print("جاري الاتصال بقاعدة البيانات...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("جاري التحقق من وجود العمود...")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='res_users' AND column_name='user_type'
    """)
    
    if not cur.fetchone():
        print("جاري إضافة العمود user_type...")
        cur.execute("ALTER TABLE res_users ADD COLUMN user_type VARCHAR")
        conn.commit()
        print("تمت إضافة العمود بنجاح!")
    else:
        print("العمود موجود بالفعل!")
        
except Exception as e:
    print(f"حدث خطأ: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
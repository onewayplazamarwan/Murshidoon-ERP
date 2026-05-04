import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
import urllib.parse
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu

# 1. إعدادات النظام الأساسية
st.set_page_config(page_title="Murshidoon ERP Pro", layout="wide")

# ملفات قواعد البيانات
DB_FILE = "main_records.xlsx"
STUDENTS_FILE = "students_db.xlsx"
SETTINGS_FILE = "settings_db.xlsx"
EXPENSES_FILE = "expenses_db.xlsx"

# أعمدة البيانات الموحدة
STD_COLS = ["الاسم", "الموبايل", "الإيميل", "تاريخ التسجيل"]
BILL_COLS = ["ID", "تاريخ الاستحقاق", "الطالب", "المادة", "الإجمالي", "المدفوع", "المتبقي"]
EXP_COLS = ["التاريخ", "البند", "المبلغ", "الملاحظات"]
SET_COLS = ["اسم_المركز", "العنوان", "الهاتف", "الإيميل"]

def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_excel(file)
            for col in columns:
                if col not in df.columns: df[col] = "---"
            numeric_cols = ["الإجمالي", "المدفوع", "المتبقي", "المبلغ"]
            for c in numeric_cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# تحميل الإعدادات والبيانات[cite: 1]
settings_df = load_data(SETTINGS_FILE, SET_COLS)
center_info = settings_df.iloc[0].to_dict() if not settings_df.empty else {
    "اسم_المركز": "مرشدون للتعليم والتدريب الإداري", 
    "العنوان": "Doha, Qatar", 
    "الهاتف": "97400000000",
    "الإيميل": "onewayplazamarwan@gmail.com"
}

# 2. القائمة الجانبية (كل الأقسام محفوظة)
with st.sidebar:
    st.image("logo.jpg.jpg", width=300) 
    selected = option_menu(
        "نظام مرشدون برو", 
        ["الرئيسية", "الطلاب", "الفواتير والأقساط", "المصروفات", "الحضور والغياب", "⚙️ الإعدادات"], 
        icons=["house", "people", "cash-stack", "wallet2", "calendar-check", "gear"], 
        default_index=0
    )

# --- وظيفة تصميم الفاتورة بستايل Zoho وهوية مرشدون[cite: 1] ---
def generate_invoice_html(bill, center):
    return f"""
    <div style="direction: rtl; font-family: 'Arial'; max-width: 800px; margin: auto; border: 1px solid #eee; padding: 30px; background: white;">
        <style>
            @media print {{ .no-print {{ display: none !important; }} }}
            .header-table {{ width: 100%; border-bottom: 3px solid #0B3154; padding-bottom: 10px; }}
            .inv-title {{ color: #00B5CC; font-size: 28px; font-weight: bold; }}
            .details-table {{ width: 100%; margin-top: 20px; border-collapse: collapse; }}
            .details-table th {{ background: #0B3154; color: white; padding: 10px; }}
            .details-table td {{ padding: 15px; border-bottom: 1px solid #eee; text-align: center; }}
            .total-section {{ margin-top: 20px; float: left; width: 300px; text-align: left; }}
            .total-row {{ display: flex; justify-content: space-between; padding: 5px 0; }}
            .balance-due {{ background: #f9f9f9; font-weight: bold; font-size: 18px; padding: 10px; border-top: 2px solid #0B3154; }}
            .p-btn {{ background: #0B3154; color: white; padding: 10px 25px; border-radius: 5px; cursor: pointer; border: none; font-weight: bold; margin-bottom: 10px; }}
        </style>
        <button class="p-btn no-print" onclick="window.print()">🖨️ طباعة الفاتورة</button>
        <table class="header-table">
            <tr>
                <td style="text-align: right;">
                    <h2 style="color: #0B3154; margin: 0;">{center['اسم_المركز']}</h2>
                    <p style="margin: 5px 0; color: #666;">{center.get('العنوان', '')}<br>{center.get('الهاتف', '')}<br>{center.get('الإيميل', '')}</p>
                </td>
                <td style="text-align: left;">
                    <div class="inv-title">Invoice</div>
                    <p style="margin: 5px 0;">رقم الفاتورة: <b>INV-{str(bill['ID']).zfill(6)}</b></p>
                    <p style="margin: 5px 0;">تاريخ الاستحقاق: {bill['تاريخ الاستحقاق']}</p>
                </td>
            </tr>
        </table>
        <div style="margin-top: 20px;"><p>إلى السيد/ة: <br><b>{bill['الطالب']}</b></p></div>
        <table class="details-table">
            <thead><tr><th>الوصف</th><th>الكمية</th><th>السعر</th><th>الإجمالي</th></tr></thead>
            <tbody><tr><td>{bill['المادة']}</td><td>1</td><td>{bill['الإجمالي']:.2f}</td><td>{bill['الإجمالي']:.2f}</td></tr></tbody>
        </table>
        <div class="total-section">
            <div class="total-row"><span>الإجمالي (QAR):</span> <span>{bill['الإجمالي']:.2f}</span></div>
            <div class="total-row"><span>المدفوع:</span> <span>(-) {bill['المدفوع']:.2f}</span></div>
            <div class="total-row balance-due"><span>الرصيد المستحق:</span> <span>QAR {bill['المتبقي']:.2f}</span></div>
        </div>
        <div style="clear: both;"></div>
    </div>
    """

def generate_whatsapp_qr(phone, message):
    formatted_phone = str(phone).replace(" ", "").replace("+", "")
    if not formatted_phone.startswith("974"): formatted_phone = "974" + formatted_phone
    url = f"https://wa.me/{formatted_phone}?text={urllib.parse.quote(message)}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO(); img.save(buf)
    return buf.getvalue(), url

# --- الصفحات ---

# 1. الرئيسية (مع إضافة المبالغ المتأخرة)[cite: 1]
if selected == "الرئيسية":
    st.header(f"📈 لوحة التحكم - {center_info['اسم_المركز']}")
    df = load_data(DB_FILE, BILL_COLS)
    exp_df = load_data(EXPENSES_FILE, EXP_COLS)
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        sales = df['الإجمالي'].sum()
        paid = df['المدفوع'].sum()
        debt = df['المتبقي'].sum() # المبالغ المتأخرة
        costs = exp_df['المبلغ'].sum()
        
        c1.metric("إجمالي المبيعات", f"{int(sales)} ر.ق")
        c2.metric("المحصل فعلياً", f"{int(paid)} ر.ق")
        c3.metric("المبالغ المتأخرة", f"{int(debt)} ر.ق", delta="-مديونية", delta_color="inverse")
        c4.metric("صافي الربح", f"{int(paid - costs)} ر.ق")
        
        st.divider()
        st.subheader("📊 ملخص الأداء المالي")
        chart_data = pd.DataFrame({
            'المبيعات': [sales], 
            'المحصل': [paid], 
            'المتأخرات': [debt],
            'المصروفات': [costs]
        }, index=['الوضع الحالي'])
        st.bar_chart(chart_data, color=["#0B3154", "#10B981", "#EF4444", "#F59E0B"])

elif selected == "الطلاب":
    st.header("👥 إدارة شؤون الطلاب")
    std_df = load_data(STUDENTS_FILE, STD_COLS)
    bill_df = load_data(DB_FILE, BILL_COLS)
    tab1, tab2, tab3, tab4 = st.tabs(["➕ إضافة طالب جديد", "✏️ تعديل بيانات", "📋 سجل فواتير الطالب", "📁 الطلاب النشطون"])
    
    with tab1:
        with st.form("add_std"):
            n = st.text_input("اسم الطالب"); p = st.text_input("الجوال"); e = st.text_input("الإيميل")
            if st.form_submit_button("حفظ"):
                if n and p:
                    new_s = pd.DataFrame([{"الاسم": n, "الموبايل": p, "الإيميل": e, "تاريخ التسجيل": date.today()}])
                    pd.concat([std_df, new_s]).to_excel(STUDENTS_FILE, index=False)
                    st.success("تم الحفظ بنجاح"); st.rerun()

    with tab2: # تعديل بيانات[cite: 1]
        if not std_df.empty:
            s_name = st.selectbox("اختر الطالب للتعديل", std_df["الاسم"].tolist())
            idx = std_df[std_df["الاسم"] == s_name].index[0]
            with st.form("edit_std"):
                un = st.text_input("تعديل الاسم", value=std_df.at[idx, "الاسم"])
                up = st.text_input("تعديل الجوال", value=std_df.at[idx, "الموبايل"])
                ue = st.text_input("تعديل الإيميل", value=std_df.at[idx, "الإيميل"])
                if st.form_submit_button("تحديث"):
                    old_n = std_df.at[idx, "الاسم"]
                    std_df.at[idx, "الاسم"], std_df.at[idx, "الموبايل"], std_df.at[idx, "الإيميل"] = un, up, ue
                    std_df.to_excel(STUDENTS_FILE, index=False)
                    bill_df.loc[bill_df["الطلاب"] == old_n, "الطلاب"] = un
                    bill_df.to_excel(DB_FILE, index=False)
                    st.success("تم التحديث"); st.rerun()

    with tab3: # سجل فواتير الطالب[cite: 1]
        if not std_df.empty:
            target_std = st.selectbox("اختر الطالب لعرض تاريخه المالي", std_df["الاسم"].tolist())
            student_history = bill_df[bill_df["الطالب"] == target_std]
            if not student_history.empty:
                st.dataframe(student_history[["ID", "تاريخ الاستحقاق", "المادة", "الإجمالي", "المدفوع", "المتبقي"]], use_container_width=True)
                st.info(f"إجمالي المديونية الحالية لهذا الطالب: {int(student_history['المتبقي'].sum())} ر.ق")
            else:
                st.warning("لا توجد فواتير مسجلة.")

    with tab4: # الطلاب النشطون[cite: 1]
        if not std_df.empty:
            active_list = []
            for _, student in std_df.iterrows():
                total_debt = bill_df[bill_df["الطالب"] == student["الاسم"]]["المتبقي"].sum()
                active_list.append({
                    "الاسم": student["الاسم"], "البريد الإلكتروني": student["الإيميل"],
                    "هاتف العمل": student["الموبايل"], "الحسابات المدينة": f"QAR {total_debt:,.2f}"
                })
            st.dataframe(pd.DataFrame(active_list), use_container_width=True)

elif selected == "الفواتير والأقساط":
    st.header("💰 إدارة الفواتير والتحصيل")
    df = load_data(DB_FILE, BILL_COLS)
    std_df = load_data(STUDENTS_FILE, STD_COLS)
    st.dataframe(df, use_container_width=True)
    t1, t2, t3, t4 = st.tabs(["🆕 إصدار فاتورة", "💳 سداد قسط", "🖨️ معاينة وطباعة", "📱 QR واتساب"])
    
    with t1:
        with st.form("new_bill"):
            sn = st.selectbox("الطالب", std_df["الاسم"].tolist() if not std_df.empty else ["أضف طالب"])
            m = st.text_input("المادة"); tot = st.number_input("الإجمالي"); pdv = st.number_input("المدفوع")
            due_date = st.date_input("تاريخ الاستحقاق", value=date.today())
            if st.form_submit_button("إصدار"):
                new_b = pd.DataFrame([{"ID": len(df)+1001, "تاريخ الاستحقاق": due_date, "الطالب": sn, "المادة": m, "الإجمالي": tot, "المدفوع": pdv, "المتبقي": tot-pdv}])
                pd.concat([df, new_b]).to_excel(DB_FILE, index=False)
                st.success("تم الإصدار"); st.rerun()

    with t2: # سداد قسط[cite: 1]
        if not df.empty:
            b_id = st.selectbox("رقم الفاتورة للسداد", df[df["المتبقي"] > 0]["ID"].tolist())
            idx = df[df["ID"] == b_id].index[0]
            amt = st.number_input("المبلغ المطلوب سداده", max_value=float(df.at[idx, 'المتبقي']))
            if st.button("تأكيد السداد"):
                df.at[idx, "المدفوع"] += amt; df.at[idx, "المتبقي"] -= amt
                df.to_excel(DB_FILE, index=False); st.success("تم السداد"); st.rerun()

    with t3: # معاينة وطباعة[cite: 1]
        if not df.empty:
            pr_id = st.selectbox("اختر الفاتورة للمعاينة", df["ID"].tolist()[::-1])
            components.html(generate_invoice_html(df[df["ID"] == pr_id].iloc[0], center_info), height=800, scrolling=True)

    with t4: # QR واتساب[cite: 1]
        if not df.empty:
            qr_id = st.selectbox("فاتورة الـ QR", df["ID"].tolist()[::-1])
            b_r = df[df["ID"] == qr_id].iloc[0]
            s_i = std_df[std_df["الاسم"] == b_r['الطالب']].iloc[0] if b_r['الطالب'] in std_df['الاسم'].values else {"الموبايل": "97400000000"}
            msg = f"فاتورة {b_r['ID']}: المتبقي QAR {int(b_r['المتبقي'])}."
            qr_img, wa_url = generate_whatsapp_qr(s_i['الموبايل'], msg)
            st.image(qr_img, width=250); st.markdown(f'[🔗 فتح واتساب المباشر]({wa_url})')

elif selected == "المصروفات":
    st.header("💸 سجل المصروفات")
    exp_df = load_data(EXPENSES_FILE, EXP_COLS)
    with st.form("add_exp"):
        item = st.text_input("بند المصروف"); amt = st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            pd.concat([exp_df, pd.DataFrame([{"التاريخ": date.today(), "البند": item, "المبلغ": amt}])]).to_excel(EXPENSES_FILE, index=False)
            st.success("تم الحفظ"); st.rerun()

elif selected == "الحضور والغياب":
    st.header("📝 التحضير والرقابة المالية")
    df = load_data(DB_FILE, BILL_COLS)
    if not df.empty:
        target = st.selectbox("اسم الطالب", df['الطالب'].unique())
        total_debt = df[df['الطالب'] == target]["المتبقي"].sum()
        if total_debt > 0: st.error(f"🛑 الطالب عليه مديونية إجمالية بقيمة: {int(total_debt)} ر.ق")
        else: st.success("✅ الطالب مسدد بالكامل")

elif selected == "⚙️ الإعدادات":
    st.header("⚙️ إعدادات المركز")
    with st.form("set_center"):
        n = st.text_input("اسم المركز", value=center_info['اسم_المركز'])
        addr = st.text_input("العنوان", value=center_info.get('العنوان', ''))
        tel = st.text_input("الجوال", value=center_info.get('الهاتف', ''))
        mail = st.text_input("البريد الإلكتروني", value=center_info.get('الإيميل', ''))
        if st.form_submit_button("حفظ"):
            new_set = pd.DataFrame([{"اسم_المركز": n, "العنوان": addr, "الهاتف": tel, "الإيميل": mail}])
            new_set.to_excel(SETTINGS_FILE, index=False)
            st.success("تم حفظ الإعدادات"); st.rerun()
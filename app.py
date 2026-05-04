import streamlit as st
import pandas as pd
from datetime import date
import os
import urllib.parse
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu

# 1. إعدادات الصفحة والأمان
st.set_page_config(page_title="Murshidoon ERP Pro", layout="wide")

# ملفات قواعد البيانات
DB_FILE = "main_records.xlsx"
STUDENTS_FILE = "students_db.xlsx"
SETTINGS_FILE = "settings_db.xlsx"
EXPENSES_FILE = "expenses_db.xlsx"
USERS_FILE = "users_db.xlsx"

# أعمدة البيانات
STD_COLS = ["الاسم", "الموبايل", "الإيميل", "تاريخ التسجيل"]
BILL_COLS = ["ID", "تاريخ_الفاتورة", "الطالب", "المادة", "الدكتور_المشرف", "الدكتور_المحاضر", "وقت_البداية", "وقت_النهاية", "الإجمالي", "المدفوع", "المتبقي"]
EXP_COLS = ["التاريخ", "البند", "المبلغ", "الملاحظات"]
SET_COLS = ["اسم_المركز", "العنوان", "الهاتف", "الإيميل"]
USER_COLS = ["role", "username", "password"]

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

# تهيئة الحسابات (مروان وأحمد)
if not os.path.exists(USERS_FILE):
    pd.DataFrame([
        {"role": "Admin", "username": "marwan", "password": "Marwan@4101991"},
        {"role": "Admin", "username": "ahmed", "password": "Ahmed@2026"}
    ]).to_excel(USERS_FILE, index=False)

# --- نظام تسجيل الدخول ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("logo.jpg.jpg", width=250)
        st.subheader("🔐 نظام مرشدون - دخول آمن")
        users_df = load_data(USERS_FILE, USER_COLS)
        with st.form("secure_login"):
            u_input = st.text_input("اسم المستخدم")
            p_input = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                match = users_df[(users_df['username'] == u_input) & (users_df['password'] == p_input)]
                if not match.empty:
                    st.session_state['auth'] = True
                    st.session_state['current_user'] = u_input
                    st.rerun()
                else: st.error("بيانات الدخول غير صحيحة!")
    st.stop()

settings_df = load_data(SETTINGS_FILE, SET_COLS)
center_info = settings_df.iloc[0].to_dict() if not settings_df.empty else {"اسم_المركز": "مرشدون للتعليم والتدريب الإداري", "العنوان": "Doha", "الهاتف": "974"}

with st.sidebar:
    st.image("logo.jpg.jpg", width=300)
    st.success(f"مرحباً بك: {st.session_state['current_user']}")
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state['auth'] = False
        st.rerun()
    st.markdown("---")
    selected = option_menu("نظام مرشدون برو", ["الرئيسية", "الطلاب", "الفواتير والأقساط", "المصروفات", "⚙️ الإعدادات"], 
        icons=["house", "people", "cash-stack", "wallet2", "gear"], default_index=0)

# --- دالة تصميم الفاتورة ---
def generate_invoice_html(bill, center, title="فاتورة"):
    return f"""
    <div style="direction: rtl; font-family: 'Arial'; max-width: 800px; margin: auto; border: 1px solid #eee; padding: 30px; background: white;">
        <style>
            @media print {{ .no-print {{ display: none !important; }} }}
            .header-table {{ width: 100%; border-bottom: 3px solid #0B3154; padding-bottom: 10px; }}
            .inv-title {{ color: #00B5CC; font-size: 28px; font-weight: bold; }}
            .details-table {{ width: 100%; margin-top: 20px; border-collapse: collapse; }}
            .details-table th {{ background: #0B3154; color: white; padding: 10px; }}
            .details-table td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: center; }}
            .info-box {{ background: #f0f4f7; padding: 10px; border-radius: 5px; border-right: 5px solid #00B5CC; margin: 10px 0; }}
            .doctor-section {{ margin-top: 25px; text-align: center; border: 1px dashed #0B3154; padding: 15px; border-radius: 10px; }}
            .balance-due {{ background: #f9f9f9; font-weight: bold; font-size: 18px; padding: 10px; border-top: 2px solid #0B3154; }}
            .p-btn {{ background: #0B3154; color: white; padding: 10px 25px; border-radius: 5px; cursor: pointer; border: none; font-weight: bold; }}
        </style>
        <button class="p-btn no-print" onclick="window.print()">🖨️ طباعة</button>
        <table class="header-table">
            <tr>
                <td style="text-align: right;">
                    <h2 style="color: #0B3154; margin: 0;">{center['اسم_المركز']}</h2>
                    <p style="margin: 5px 0;">{center.get('العنوان', '')} | {center.get('الهاتف', '')}</p>
                </td>
                <td style="text-align: left;">
                    <div class="inv-title">{title}</div>
                    <p style="margin: 5px 0;">التاريخ: {bill.get('تاريخ_الفاتورة', date.today())}</p>
                </td>
            </tr>
        </table>
        <div style="display: flex; justify-content: space-between; margin-top: 20px;">
            <div><p>إلى السيد/ة: <b>{bill.get('الطالب', '---')}</b></p></div>
            <div class="info-box" style="min-width: 220px;">
                <p style="margin:0;">🕒 <b>مواعيد الحضور:</b></p>
                <p style="margin:0; font-size:14px;">من: {bill.get('وقت_البداية', '---')} | إلى: {bill.get('وقت_النهاية', '---')}</p>
            </div>
        </div>
        <table class="details-table">
            <thead><tr><th>الوصف / المادة</th><th>الإجمالي</th><th>المدفوع</th><th>المتبقي</th></tr></thead>
            <tbody><tr><td>{bill['المادة']}</td><td>{bill['الإجمالي']:.2f}</td><td>{bill['المدفوع']:.2f}</td><td>{bill['المتبقي']:.2f}</td></tr></tbody>
        </table>
        <div class="doctor-section">
            <p style="margin: 5px 0;">الدكتور المشرف: <b>{bill.get('الدكتور_المشرف', '---')}</b></p>
            <p style="margin: 5px 0;">الدكتور المحاضر: <b>{bill.get('الدكتور_المحاضر', '---')}</b></p>
        </div>
        <div style="margin-top: 20px;" class="balance-due">إجمالي المستحق: QAR {bill['المتبقي']:.2f}</div>
    </div>
    """

if selected == "الرئيسية":
    st.header("📈 لوحة التحكم والإحصائيات")
    df = load_data(DB_FILE, BILL_COLS)
    exp_df = load_data(EXPENSES_FILE, EXP_COLS)
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        sales, paid, debt = df['الإجمالي'].sum(), df['المدفوع'].sum(), df['المتبقي'].sum()
        total_exp = exp_df['المبلغ'].sum() if not exp_df.empty else 0
        c1.metric("إجمالي المبيعات", f"{int(sales)} ر.ق")
        c2.metric("المحصل فعلياً", f"{int(paid)} ر.ق")
        c3.metric("إجمالي المتأخرات", f"{int(debt)} ر.ق")
        c4.metric("صافي الأرباح", f"{int(paid - total_exp)} ر.ق")
        st.divider()
        st.bar_chart(pd.DataFrame({'المبيعات': [sales], 'المحصل': [paid], 'المتأخرات': [debt]}, index=['المالية']))

elif selected == "الطلاب":
    st.header("👥 إدارة الطلاب")
    std_df = load_data(STUDENTS_FILE, STD_COLS)
    bill_df = load_data(DB_FILE, BILL_COLS)
    t1, t2, t3, t4 = st.tabs(["➕ إضافة", "✏️ تعديل", "📋 كشف حساب", "🗑️ حذف الطالب"])
    with t1:
        with st.form("std_add"):
            n, p, e = st.text_input("الاسم"), st.text_input("الجوال"), st.text_input("الإيميل")
            if st.form_submit_button("حفظ"):
                if n and p:
                    pd.concat([std_df, pd.DataFrame([{"الاسم": n, "الموبايل": p, "الإيميل": e, "تاريخ التسجيل": date.today()}])]).to_excel(STUDENTS_FILE, index=False)
                    st.success("تم الحفظ"); st.rerun()
    with t2:
        if not std_df.empty:
            std_n = st.selectbox("اختر الطالب لتعديله", std_df["الاسم"].tolist())
            idx = std_df[std_df["الاسم"] == std_n].index[0]
            with st.form("std_edit"):
                new_p, new_e = st.text_input("الجوال", value=std_df.at[idx, "الموبايل"]), st.text_input("الإيميل", value=std_df.at[idx, "الإيميل"])
                if st.form_submit_button("تحديث"):
                    std_df.at[idx, "الموبايل"], std_df.at[idx, "الإيميل"] = new_p, new_e
                    std_df.to_excel(STUDENTS_FILE, index=False); st.success("تم التحديث"); st.rerun()
    with t3:
        if not std_df.empty:
            target = st.selectbox("اختر الطالب للكشف", std_df["الاسم"].tolist())
            st_bills = bill_df[bill_df["الطالب"] == target]
            if not st_bills.empty:
                summary = {"الطالب": target, "المادة": "كشف حساب مجمع", "الإجمالي": st_bills["الإجمالي"].sum(), "المدفوع": st_bills["المدفوع"].sum(), "المتبقي": st_bills["المتبقي"].sum()}
                components.html(generate_invoice_html(summary, center_info, title="Statement of Account"), height=550, scrolling=True)
    with t4: # تم إصلاح ميزة حذف الطالب هنا
        if not std_df.empty:
            del_n = st.selectbox("اختر الطالب لحذفه نهائياً", std_df["الاسم"].tolist())
            if st.button("❌ تأكيد حذف الطالب وكل بياناته"):
                std_df = std_df[std_df["الاسم"] != del_n]
                std_df.to_excel(STUDENTS_FILE, index=False)
                bill_df = bill_df[bill_df["الطالب"] != del_n]
                bill_df.to_excel(DB_FILE, index=False)
                st.success(f"تم حذف الطالب {del_n} بنجاح"); st.rerun()

elif selected == "الفواتير والأقساط":
    st.header("💰 إدارة الفواتير")
    df, std_df = load_data(DB_FILE, BILL_COLS), load_data(STUDENTS_FILE, STD_COLS)
    tabs = st.tabs(["🆕 إصدار", "✏️ تعديل", "🖨️ معاينة", "🗑️ حذف الفاتورة"])
    with tabs[0]:
        with st.form("inv_form"):
            sn = st.selectbox("الطالب", std_df["الاسم"].tolist() if not std_df.empty else ["---"])
            m = st.text_input("المادة")
            c1, c2 = st.columns(2)
            with c1: doc_sup, doc_lec = st.selectbox("المشرف", ["الدكتور / ابراهيم عوض الله", "محمد عدلي", "أخرى"]), st.text_input("المحاضر")
            with c2: ts, te = st.time_input("وقت البداية"), st.time_input("وقت النهاية")
            tot, pdv = st.number_input("الإجمالي"), st.number_input("المدفوع")
            if st.form_submit_button("إصدار"):
                new_row = pd.DataFrame([{"ID": len(df)+1001, "تاريخ_الفاتورة": date.today(), "الطالب": sn, "المادة": m, "الدكتور_المشرف": doc_sup, "الدكتور_المحاضر": doc_lec, "وقت_البداية": ts.strftime("%I:%M %p"), "وقت_النهاية": te.strftime("%I:%M %p"), "الإجمالي": tot, "المدفوع": pdv, "المتبقي": tot-pdv}])
                pd.concat([df, new_row]).to_excel(DB_FILE, index=False); st.success("تم الإصدار"); st.rerun()
    with tabs[1]:
        if not df.empty:
            inv_id = st.selectbox("رقم الفاتورة للتعديل", df["ID"].tolist())
            idx = df[df["ID"] == inv_id].index[0]
            with st.form("edit_inv_f"):
                e_m, e_tot, e_pdv = st.text_input("المادة", value=df.at[idx, "المادة"]), st.number_input("الإجمالي", value=float(df.at[idx, "الإجمالي"])), st.number_input("المدفوع", value=float(df.at[idx, "المدفوع"]))
                if st.form_submit_button("تحديث الفاتورة"):
                    df.at[idx, "المادة"], df.at[idx, "الإجمالي"], df.at[idx, "المدفوع"] = e_m, e_tot, e_pdv
                    df.at[idx, "المتبقي"] = e_tot - e_pdv
                    df.to_excel(DB_FILE, index=False); st.success("تم التعديل"); st.rerun()
    with tabs[2]:
        if not df.empty:
            pr_id = st.selectbox("اختر الفاتورة", df["ID"].tolist()[::-1])
            components.html(generate_invoice_html(df[df["ID"] == pr_id].iloc[0], center_info), height=600, scrolling=True)
    with tabs[3]:
        if not df.empty:
            del_id = st.selectbox("اختر رقم الفاتورة للحذف", df["ID"].tolist())
            if st.button("❌ تأكيد حذف الفاتورة"):
                df = df[df["ID"] != del_id]
                df.to_excel(DB_FILE, index=False); st.success("تم حذف الفاتورة"); st.rerun()

elif selected == "المصروفات":
    st.header("💸 المصروفات")
    exp_df = load_data(EXPENSES_FILE, EXP_COLS)
    with st.form("exp"):
        item, amt = st.text_input("بند المصروف"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            pd.concat([exp_df, pd.DataFrame([{"التاريخ": date.today(), "البند": item, "المبلغ": amt}])]).to_excel(EXPENSES_FILE, index=False)
            st.success("تم الحفظ"); st.rerun()
    st.dataframe(exp_df, use_container_width=True)

elif selected == "⚙️ الإعدادات":
    st.header("⚙️ إعدادات النظام")
    t_set1, t_set2, t_set3 = st.tabs(["🏠 بيانات المركز", "👥 إضافة مستخدم", "👤 حسابي"])
    with t_set1:
        with st.form("center_set"):
            n, tel, addr = st.text_input("اسم المركز", center_info.get('اسم_المركز')), st.text_input("الهاتف", center_info.get('الهاتف')), st.text_input("العنوان", center_info.get('العنوان'))
            if st.form_submit_button("تحديث"):
                pd.DataFrame([{"اسم_المركز": n, "الهاتف": tel, "العنوان": addr}]).to_excel(SETTINGS_FILE, index=False)
                st.success("تم التحديث"); st.rerun()
    with t_set2:
        u_df = load_data(USERS_FILE, USER_COLS)
        with st.form("new_u"):
            role, u_name, u_pass = st.selectbox("نوع الحساب", ["Admin", "User"]), st.text_input("اسم المستخدم الجديد"), st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("إضافة"):
                pd.concat([u_df, pd.DataFrame([{"role": role, "username": u_name, "password": u_pass}])]).to_excel(USERS_FILE, index=False)
                st.success("تمت الإضافة"); st.rerun()
    with t_set3:
        u_df, curr_u = load_data(USERS_FILE, USER_COLS), st.session_state['current_user']
        with st.form("my_p"):
            new_p = st.text_input("كلمة مرور جديدة", type="password")
            if st.form_submit_button("تحديث"):
                idx = u_df[u_df["username"] == curr_u].index[0]
                u_df.at[idx, "password"] = new_p
                u_df.to_excel(USERS_FILE, index=False); st.success("تم التحديث"); st.rerun()
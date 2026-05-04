import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components

# 1. إعدادات الصفحة والأمان
st.set_page_config(page_title="Murshidoon ERP Pro", layout="wide")

# ملفات قواعد البيانات
DB_FILE = "main_records.xlsx"
STUDENTS_FILE = "students_db.xlsx"
SETTINGS_FILE = "settings_db.xlsx"
EXPENSES_FILE = "expenses_db.xlsx"
USERS_FILE = "users_db.xlsx"
LECTURERS_FILE = "lecturers_db.xlsx"

# أعمدة البيانات
STD_COLS = ["الاسم", "الموبايل", "الإيميل", "تاريخ التسجيل"]
BILL_COLS = ["ID", "تاريخ_الفاتورة", "تاريخ_الاستحقاق", "الطالب", "المادة", "الدكتور_المشرف", "الدكتور_المحاضر", "وقت_البداية", "وقت_النهاية", "الإجمالي", "المدفوع", "المتبقي"]
EXP_COLS = ["التاريخ", "البند", "المبلغ", "الملاحظات"]
SET_COLS = ["اسم_المركز", "العنوان", "الهاتف", "الإيميل"]
USER_COLS = ["role", "username", "password"]
LEC_COLS = ["الاسم"]

def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_excel(file)
            for col in columns:
                if col not in df.columns: df[col] = "---"
            if "تاريخ_الاستحقاق" in df.columns:
                df["تاريخ_الاستحقاق"] = pd.to_datetime(df["تاريخ_الاستحقاق"]).dt.date
            numeric_cols = ["الإجمالي", "المدفوع", "المتبقي", "المبلغ"]
            for c in numeric_cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# تهيئة الحسابات
if not os.path.exists(USERS_FILE):
    pd.DataFrame([{"role": "Admin", "username": "marwan", "password": "Marwan@4101991"}]).to_excel(USERS_FILE, index=False)

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
                    st.session_state['auth'], st.session_state['current_user'] = True, u_input
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
    selected = option_menu("نظام مرشدون برو", ["الرئيسية", "الطلاب", "الفواتير والأقساط", "المصروفات", "حسابات المحاضرين", "الحضور والغياب", "⚙️ الإعدادات"], 
        icons=["house", "people", "cash-stack", "wallet2", "person-badge", "calendar-check", "gear"], default_index=0)

# --- دالة تصميم الفاتورة ---
def generate_invoice_html(bill, center, title="فاتورة"):
    return f"""
    <div style="direction: rtl; font-family: 'Arial'; max-width: 800px; margin: auto; border: 1px solid #eee; padding: 30px; background: white;">
        <style> @media print {{ .no-print {{ display: none !important; }} }} </style>
        <button class="no-print" style="background:#0B3154; color:white; padding:10px; border:none; cursor:pointer;" onclick="window.print()">🖨️ طباعة</button>
        <table style="width:100%; border-bottom:3px solid #0B3154;">
            <tr>
                <td style="text-align:right;"><h2>{center['اسم_المركز']}</h2><p>{center.get('العنوان', '')} | {center.get('الهاتف', '')}</p></td>
                <td style="text-align:left;"><h2 style="color:#00B5CC;">{title}</h2><p>التاريخ: {bill.get('تاريخ_الفاتورة', date.today())}</p><p style="color:red;">الاستحقاق: {bill.get('تاريخ_الاستحقاق', '---')}</p></td>
            </tr>
        </table>
        <div style="margin-top:20px;"><p>إلى السيد/ة: <b>{bill.get('الطالب', '---')}</b></p></div>
        <div style="background:#f0f4f7; padding:10px; border-right:5px solid #00B5CC; margin:10px 0;">🕒 من {bill.get('وقت_البداية', '---')} إلى {bill.get('وقت_النهاية', '---')}</div>
        <table style="width:100%; margin-top:20px; border-collapse:collapse; text-align:center;">
            <thead style="background:#0B3154; color:white;"><tr><th style="padding:10px;">المادة</th><th>الإجمالي</th><th>المدفوع</th><th>المتبقي</th></tr></thead>
            <tbody><tr><td style="padding:10px; border-bottom:1px solid #eee;">{bill['المادة']}</td><td>{bill['الإجمالي']:.2f}</td><td>{bill['المدفوع']:.2f}</td><td>{bill['المتبقي']:.2f}</td></tr></tbody>
        </table>
        <div style="margin-top:25px; text-align:center; border:1px dashed #0B3154; padding:15px;">المشرف: {bill.get('الدكتور_المشرف', '---')} | المحاضر: {bill.get('الدكتور_المحاضر', '---')}</div>
    </div>
    """

if selected == "الرئيسية":
    st.header("📈 لوحة التحكم")
    df, exp_df = load_data(DB_FILE, BILL_COLS), load_data(EXPENSES_FILE, EXP_COLS)
    if not df.empty:
        today = date.today()
        overdue_df = df[(df['المتبقي'] > 0) & (pd.to_datetime(df['تاريخ_الاستحقاق']).dt.date < today)].copy()
        c1, c2, c3, c4 = st.columns(4)
        sales, paid, debt = df['الإجمالي'].sum(), df['المدفوع'].sum(), df['المتبقي'].sum()
        total_exp = exp_df['المبلغ'].sum()
        c1.metric("إجمالي المبيعات", f"{int(sales)} ر.ق")
        c2.metric("المحصل", f"{int(paid)} ر.ق")
        c3.metric("الديون", f"{int(debt)} ر.ق")
        c4.metric("متأخرات الاستحقاق", f"{int(overdue_df['المتبقي'].sum())} ر.ق", delta="عاجل", delta_color="inverse")
        st.divider()
        st.subheader("🚨 الفواتير المتأخرة")
        if not overdue_df.empty:
            overdue_df['أيام_التأخير'] = overdue_df['تاريخ_الاستحقاق'].apply(lambda x: (today - x).days)
            st.dataframe(overdue_df[['ID', 'الطالب', 'المادة', 'تاريخ_الاستحقاق', 'المتبقي', 'أيام_التأخير']], use_container_width=True)
        else: st.success("لا توجد متأخرات")

elif selected == "الطلاب":
    st.header("👥 الطلاب")
    std_df, bill_df = load_data(STUDENTS_FILE, STD_COLS), load_data(DB_FILE, BILL_COLS)
    t1, t2, t3, t4 = st.tabs(["➕ إضافة", "✏️ تعديل", "📋 كشف حساب", "🗑️ حذف"])
    with t1:
        with st.form("std_add"):
            n, p, e = st.text_input("الاسم"), st.text_input("الجوال"), st.text_input("الإيميل")
            if st.form_submit_button("حفظ"):
                pd.concat([std_df, pd.DataFrame([{"الاسم": n, "الموبايل": p, "الإيميل": e, "تاريخ التسجيل": date.today()}])]).to_excel(STUDENTS_FILE, index=False)
                st.success("تم الحفظ"); st.rerun()
    with t3:
        if not std_df.empty:
            target = st.selectbox("اختر الطالب", std_df["الاسم"].tolist())
            st_bills = bill_df[bill_df["الطالب"] == target]
            if not st_bills.empty:
                summary = {"الطالب": target, "المادة": "كشف مجمع", "الإجمالي": st_bills["الإجمالي"].sum(), "المدفوع": st_bills["المدفوع"].sum(), "المتبقي": st_bills["المتبقي"].sum()}
                components.html(generate_invoice_html(summary, center_info), height=550)
    with t4:
        if not std_df.empty:
            del_n = st.selectbox("حذف طالب", std_df["الاسم"].tolist())
            if st.button("❌ حذف نهائي"):
                std_df[std_df["الاسم"] != del_n].to_excel(STUDENTS_FILE, index=False)
                bill_df[bill_df["الطالب"] != del_n].to_excel(DB_FILE, index=False)
                st.success("تم الحذف"); st.rerun()

elif selected == "الفواتير والأقساط":
    st.header("💰 الفواتير")
    df, std_df, lec_df = load_data(DB_FILE, BILL_COLS), load_data(STUDENTS_FILE, STD_COLS), load_data(LECTURERS_FILE, LEC_COLS)
    tabs = st.tabs(["🆕 إصدار", "✏️ تعديل شامل", "🖨️ معاينة", "🗑️ حذف"])
    with tabs[0]:
        with st.form("inv_form"):
            sn = st.selectbox("الطالب", std_df["الاسم"].tolist() if not std_df.empty else ["---"])
            m = st.text_input("المادة")
            c1, c2 = st.columns(2)
            with c1: 
                doc_sup = st.selectbox("المشرف", ["الدكتور / ابراهيم عوض الله", "محمد عدلي", "أخرى"])
                doc_lec = st.selectbox("المحاضر", lec_df["الاسم"].tolist() if not lec_df.empty else ["---"])
            with c2: 
                due_d = st.date_input("تاريخ الاستحقاق")
                ts = st.time_input("البداية")
                te = st.time_input("النهاية")
            tot, pdv = st.number_input("الإجمالي"), st.number_input("المدفوع")
            if st.form_submit_button("إصدار"):
                new_row = pd.DataFrame([{"ID": len(df)+1001, "تاريخ_الفاتورة": date.today(), "تاريخ_الاستحقاق": due_d, "الطالب": sn, "المادة": m, "الدكتور_المشرف": doc_sup, "الدكتور_المحاضر": doc_lec, "وقت_البداية": ts.strftime("%I:%M %p"), "وقت_النهاية": te.strftime("%I:%M %p"), "الإجمالي": tot, "المدفوع": pdv, "المتبقي": tot-pdv}])
                pd.concat([df, new_row]).to_excel(DB_FILE, index=False); st.success("تم الإصدار"); st.rerun()
    with tabs[1]:
        if not df.empty:
            inv_id = st.selectbox("رقم الفاتورة", df["ID"].tolist())
            idx = df[df["ID"] == inv_id].index[0]
            with st.form("edit_f"):
                e_sn = st.selectbox("تغيير الطالب", std_df["الاسم"].tolist(), index=0)
                e_m, e_due = st.text_input("المادة", value=df.at[idx, "المادة"]), st.date_input("تعديل الاستحقاق", value=df.at[idx, "تاريخ_الاستحقاق"])
                e_sup = st.selectbox("المشرف", ["الدكتور / ابراهيم عوض الله", "محمد عدلي", "أخرى"])
                e_lec = st.selectbox("المحاضر", lec_df["الاسم"].tolist() if not lec_df.empty else ["---"])
                e_tot, e_pdv = st.number_input("الإجمالي", value=float(df.at[idx, "الإجمالي"])), st.number_input("المدفوع", value=float(df.at[idx, "المدفوع"]))
                if st.form_submit_button("تحديث"):
                    df.at[idx, "الطالب"], df.at[idx, "المادة"], df.at[idx, "تاريخ_الاستحقاق"] = e_sn, e_m, e_due
                    df.at[idx, "الدكتور_المشرف"], df.at[idx, "الدكتور_المحاضر"] = e_sup, e_lec
                    df.at[idx, "الإجمالي"], df.at[idx, "المدفوع"], df.at[idx, "المتبقي"] = e_tot, e_pdv, e_tot - e_pdv
                    df.to_excel(DB_FILE, index=False); st.success("تم التحديث"); st.rerun()
    with tabs[3]:
        if not df.empty:
            del_id = st.selectbox("حذف فاتورة", df["ID"].tolist())
            if st.button("❌ حذف"):
                df[df["ID"] != del_id].to_excel(DB_FILE, index=False); st.success("تم الحذف"); st.rerun()

elif selected == "المصروفات":
    st.header("💸 المصروفات")
    exp_df = load_data(EXPENSES_FILE, EXP_COLS)
    with st.form("exp"):
        item, amt = st.text_input("البند"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            pd.concat([exp_df, pd.DataFrame([{"التاريخ": date.today(), "البند": item, "المبلغ": amt}])]).to_excel(EXPENSES_FILE, index=False)
            st.success("تم الحفظ"); st.rerun()
    st.dataframe(exp_df, use_container_width=True)

elif selected == "حسابات المحاضرين":
    st.header("👨‍🏫 حسابات الدكاترة")
    df = load_data(DB_FILE, BILL_COLS)
    if not df.empty:
        doc = st.selectbox("اختر الدكتور", df['الدكتور_المحاضر'].unique())
        doc_data = df[df['الدكتور_المحاضر'] == doc]
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي قيمة العمل", f"{int(doc_data['الإجمالي'].sum())} ر.ق")
        c2.metric("المحصل", f"{int(doc_data['المدفوع'].sum())} ر.ق")
        c3.metric("متبقي عند الطلبة", f"{int(doc_data['المتبقي'].sum())} ر.ق")
        st.dataframe(doc_data[['ID', 'الطالب', 'المادة', 'المدفوع', 'المتبقي']], use_container_width=True)

elif selected == "الحضور والغياب":
    st.header("📝 الحضور")
    df = load_data(DB_FILE, BILL_COLS)
    if not df.empty:
        std = st.selectbox("اسم الطالب", df['الطالب'].unique())
        debt = df[df['الطالب'] == std]['المتبقي'].sum()
        if debt > 0: st.error(f"🛑 مديونية: {int(debt)} ر.ق")
        else: st.success("✅ مسدد بالكامل")

elif selected == "⚙️ الإعدادات":
    st.header("⚙️ الإعدادات")
    t1, t2, t3, t4 = st.tabs(["🏠 المركز", "👥 المستخدمين", "👨‍🏫 الدكاترة", "👤 حسابي"])
    with t1:
        with st.form("set_c"):
            n, tel, addr = st.text_input("الاسم", center_info.get('اسم_المركز')), st.text_input("الهاتف", center_info.get('الهاتف')), st.text_input("العنوان", center_info.get('العنوان'))
            if st.form_submit_button("تحديث"):
                pd.DataFrame([{"اسم_المركز": n, "الهاتف": tel, "العنوان": addr}]).to_excel(SETTINGS_FILE, index=False)
                st.success("تم التحديث"); st.rerun()
    with t2:
        u_df = load_data(USERS_FILE, USER_COLS)
        with st.form("add_u"):
            un, up, ur = st.text_input("المستخدم"), st.text_input("كلمة المرور", type="password"), st.selectbox("الرتبة", ["Admin", "User"])
            if st.form_submit_button("إضافة"):
                pd.concat([u_df, pd.DataFrame([{"username": un, "password": up, "role": ur}])]).to_excel(USERS_FILE, index=False)
                st.success("تمت الإضافة"); st.rerun()
        st.divider()
        du = st.selectbox("حذف مستخدم", u_df["username"].tolist())
        if st.button("❌ حذف المستخدم"):
            if du != st.session_state['current_user']:
                u_df[u_df["username"] != du].to_excel(USERS_FILE, index=False); st.success("تم الحذف"); st.rerun()
            else: st.error("لا يمكنك حذف نفسك")
    with t3:
        lec_df = load_data(LECTURERS_FILE, LEC_COLS)
        with st.form("add_l"):
            ln = st.text_input("اسم الدكتور")
            if st.form_submit_button("إضافة"):
                pd.concat([lec_df, pd.DataFrame([{"الاسم": ln}])]).to_excel(LECTURERS_FILE, index=False)
                st.success("تمت الإضافة"); st.rerun()
        st.dataframe(lec_df, use_container_width=True)
    with t4:
        u_df = load_data(USERS_FILE, USER_COLS)
        with st.form("pass"):
            np = st.text_input("كلمة مرور جديدة", type="password")
            if st.form_submit_button("تحديث"):
                idx = u_df[u_df["username"] == st.session_state['current_user']].index[0]
                u_df.at[idx, "password"] = np
                u_df.to_excel(USERS_FILE, index=False); st.success("تم التحديث"); st.rerun()
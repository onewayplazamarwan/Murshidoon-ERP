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
LECTURERS_FILE = "lecturers_db.xlsx"

# أعمدة البيانات الموحدة
STD_COLS = ["الاسم", "الموبايل", "الإيميل", "تاريخ التسجيل"]
BILL_COLS = ["ID", "تاريخ_الفاتورة", "الطالب", "المادة", "الدكتور_المشرف", "الدكتور_المحاضر", "وقت_البداية", "وقت_النهاية", "الإجمالي", "المدفوع", "المتبقي"]
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
            numeric_cols = ["الإجمالي", "المدفوع", "المتبقي", "المبلغ"]
            for c in numeric_cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# تهيئة الحسابات الأساسية
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
                    st.session_state['auth'] = True
                    st.session_state['current_user'] = u_input
                    st.rerun()
                else: st.error("بيانات الدخول غير صحيحة!")
    st.stop()

# تحميل البيانات
settings_df = load_data(SETTINGS_FILE, SET_COLS)
center_info = settings_df.iloc[0].to_dict() if not settings_df.empty else {"اسم_المركز": "مرشدون للتعليم والتدريب الإداري", "العنوان": "Doha", "الهاتف": "974"}

with st.sidebar:
    st.image("logo.jpg.jpg", width=300)
    st.success(f"مرحباً بك: {st.session_state['current_user']}")
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state['auth'] = False
        st.rerun()
    st.markdown("---")
    selected = option_menu("نظام مرشدون برو", ["الرئيسية", "الطلاب", "الفواتير والأقساط", "المصروفات", "حسابات المحاضرين", "الحضور والغياب", "⚙️ الإعدادات"], 
        icons=["house", "people", "cash-stack", "wallet2", "person-badge", "calendar-check", "gear"], default_index=0)

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
        </style>
        <button class="no-print" style="background:#0B3154; color:white; padding:10px; border:none; cursor:pointer;" onclick="window.print()">🖨️ طباعة</button>
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
        <div style="margin-top: 20px;"><p>إلى السيد/ة: <b>{bill.get('الطالب', '---')}</b></p></div>
        <div class="info-box">🕒 <b>المواعيد:</b> من {bill.get('وقت_البداية', '---')} إلى {bill.get('وقت_النهاية', '---')}</div>
        <table class="details-table">
            <thead><tr><th>الوصف / المادة</th><th>الإجمالي</th><th>المدفوع</th><th>المتبقي</th></tr></thead>
            <tbody><tr><td>{bill['المادة']}</td><td>{bill['الإجمالي']:.2f}</td><td>{bill['المدفوع']:.2f}</td><td>{bill['المتبقي']:.2f}</td></tr></tbody>
        </table>
        <div class="doctor-section">
            <p>المشرف: {bill.get('الدكتور_المشرف', '---')} | المحاضر: {bill.get('الدكتور_المحاضر', '---')}</p>
        </div>
        <div class="balance-due">إجمالي المستحق: QAR {bill['المتبقي']:.2f}</div>
    </div>
    """

if selected == "الرئيسية":
    st.header("📈 لوحة التحكم")
    df, exp_df = load_data(DB_FILE, BILL_COLS), load_data(EXPENSES_FILE, EXP_COLS)
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        sales, paid, debt = df['الإجمالي'].sum(), df['المدفوع'].sum(), df['المتبقي'].sum()
        total_exp = exp_df['المبلغ'].sum() if not exp_df.empty else 0
        c1.metric("إجمالي المبيعات", f"{int(sales)} ر.ق")
        c2.metric("المحصل", f"{int(paid)} ر.ق")
        c3.metric("الديون", f"{int(debt)} ر.ق")
        c4.metric("الأرباح", f"{int(paid - total_exp)} ر.ق")
        st.divider()
        st.bar_chart(pd.DataFrame({'المبيعات': [sales], 'المحصل': [paid], 'الديون': [debt]}, index=['المالية']))

elif selected == "الطلاب":
    st.header("👥 شؤون الطلاب")
    std_df, bill_df = load_data(STUDENTS_FILE, STD_COLS), load_data(DB_FILE, BILL_COLS)
    t1, t2, t3, t4 = st.tabs(["➕ إضافة", "✏️ تعديل", "📋 كشف حساب", "🗑️ حذف"])
    with t1:
        with st.form("std_add"):
            n, p, e = st.text_input("الاسم"), st.text_input("الجوال"), st.text_input("الإيميل")
            if st.form_submit_button("حفظ"):
                if n and p:
                    pd.concat([std_df, pd.DataFrame([{"الاسم": n, "الموبايل": p, "الإيميل": e, "تاريخ التسجيل": date.today()}])]).to_excel(STUDENTS_FILE, index=False)
                    st.success("تم الحفظ بنجاح"); st.rerun()
    with t2:
        if not std_df.empty:
            std_n = st.selectbox("اختر طالب", std_df["الاسم"].tolist())
            idx = std_df[std_df["الاسم"] == std_n].index[0]
            with st.form("std_edit"):
                new_p, new_e = st.text_input("الجوال", value=std_df.at[idx, "الموبايل"]), st.text_input("الإيميل", value=std_df.at[idx, "الإيميل"])
                if st.form_submit_button("تحديث البيانات"):
                    std_df.at[idx, "الموبايل"], std_df.at[idx, "الإيميل"] = new_p, new_e
                    std_df.to_excel(STUDENTS_FILE, index=False); st.success("تم التحديث"); st.rerun()
    with t3:
        if not std_df.empty:
            target = st.selectbox("كشف حساب مجمع للطالب", std_df["الاسم"].tolist())
            st_bills = bill_df[bill_df["الطالب"] == target]
            if not st_bills.empty:
                summary = {"الطالب": target, "المادة": "كشف حساب مجمع", "الإجمالي": st_bills["الإجمالي"].sum(), "المدفوع": st_bills["المدفوع"].sum(), "المتبقي": st_bills["المتبقي"].sum()}
                components.html(generate_invoice_html(summary, center_info, title="Account Statement"), height=550, scrolling=True)
    with t4:
        if not std_df.empty:
            del_n = st.selectbox("حذف طالب نهائياً", std_df["الاسم"].tolist())
            if st.button("❌ تأكيد حذف الطالب وكل بياناته"):
                std_df[std_df["الاسم"] != del_n].to_excel(STUDENTS_FILE, index=False)
                bill_df[bill_df["الطالب"] != del_n].to_excel(DB_FILE, index=False)
                st.success("تم الحذف بنجاح"); st.rerun()

elif selected == "الفواتير والأقساط":
    st.header("💰 إدارة الفواتير")
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
            with c2: ts, te = st.time_input("البداية"), st.time_input("النهاية")
            tot, pdv = st.number_input("إجمالي المبلغ"), st.number_input("المدفوع")
            if st.form_submit_button("إصدار الفاتورة"):
                new_row = pd.DataFrame([{"ID": len(df)+1001, "تاريخ_الفاتورة": date.today(), "الطالب": sn, "المادة": m, "الدكتور_المشرف": doc_sup, "الدكتور_المحاضر": doc_lec, "وقت_البداية": ts.strftime("%I:%M %p"), "وقت_النهاية": te.strftime("%I:%M %p"), "الإجمالي": tot, "المدفوع": pdv, "المتبقي": tot-pdv}])
                pd.concat([df, new_row]).to_excel(DB_FILE, index=False); st.success("تم الإصدار"); st.rerun()
    with tabs[1]: # تعديل شامل للفاتورة
        if not df.empty:
            inv_id = st.selectbox("رقم الفاتورة للتعديل", df["ID"].tolist())
            idx = df[df["ID"] == inv_id].index[0]
            with st.form("edit_full_inv"):
                edit_sn = st.selectbox("تغيير الطالب", std_df["الاسم"].tolist(), index=std_df["الاسم"].tolist().index(df.at[idx, "الطالب"]) if df.at[idx, "الطالب"] in std_df["الاسم"].tolist() else 0)
                edit_m = st.text_input("المادة", value=df.at[idx, "المادة"])
                edit_tot = st.number_input("الإجمالي الجديد", value=float(df.at[idx, "الإجمالي"]))
                edit_pdv = st.number_input("المدفوع الجديد", value=float(df.at[idx, "المدفوع"]))
                if st.form_submit_button("حفظ كافة التعديلات"):
                    df.at[idx, "الطالب"], df.at[idx, "المادة"], df.at[idx, "الإجمالي"], df.at[idx, "المدفوع"] = edit_sn, edit_m, edit_tot, edit_pdv
                    df.at[idx, "المتبقي"] = edit_tot - edit_pdv
                    df.to_excel(DB_FILE, index=False); st.success("تم التحديث"); st.rerun()
    with tabs[2]:
        if not df.empty:
            pr_id = st.selectbox("معاينة فاتورة محددة", df["ID"].tolist()[::-1])
            components.html(generate_invoice_html(df[df["ID"] == pr_id].iloc[0], center_info), height=600, scrolling=True)
    with tabs[3]:
        if not df.empty:
            del_id = st.selectbox("رقم الفاتورة للحذف", df["ID"].tolist())
            if st.button("❌ حذف الفاتورة نهائياً"):
                df[df["ID"] != del_id].to_excel(DB_FILE, index=False); st.success("تم الحذف"); st.rerun()

elif selected == "المصروفات":
    st.header("💸 سجل المصروفات")
    exp_df = load_data(EXPENSES_FILE, EXP_COLS)
    with st.form("exp_form"):
        item, amt = st.text_input("بند المصروف"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ المصروف"):
            if item and amt > 0:
                pd.concat([exp_df, pd.DataFrame([{"التاريخ": date.today(), "البند": item, "المبلغ": amt}])]).to_excel(EXPENSES_FILE, index=False)
                st.success("تم الحفظ بنجاح"); st.rerun()
    st.dataframe(exp_df, use_container_width=True)

elif selected == "حسابات المحاضرين":
    st.header("👨‍🏫 حسابات الدكاترة")
    df = load_data(DB_FILE, BILL_COLS)
    if not df.empty:
        doc = st.selectbox("اختر الدكتور المحاضر", df['الدكتور_المحاضر'].unique())
        doc_data = df[df['الدكتور_المحاضر'] == doc]
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي قيمة العمل", f"{int(doc_data['الإجمالي'].sum())} ر.ق")
        c2.metric("المحصل فعلياً للمركز", f"{int(doc_data['المدفوع'].sum())} ر.ق")
        c3.metric("متبقي ديون عند الطلبة", f"{int(doc_data['المتبقي'].sum())} ر.ق")
        st.dataframe(doc_data[['الطالب', 'المادة', 'المدفوع', 'المتبقي']], use_container_width=True)

elif selected == "الحضور والغياب":
    st.header("📝 الحضور والتحقق المالي")
    df = load_data(DB_FILE, BILL_COLS)
    if not df.empty:
        std = st.selectbox("اسم الطالب للحضور", df['الطالب'].unique())
        debt = df[df['الطالب'] == std]['المتبقي'].sum()
        if debt > 0: st.error(f"🛑 تنبيه: الطالب عليه مديونية بقيمة {int(debt)} ر.ق. يرجى التحصيل.")
        else: st.success("✅ الطالب مسدد بالكامل، يمكنه الحضور.")

elif selected == "⚙️ الإعدادات":
    st.header("⚙️ إعدادات النظام المتقدمة")
    t1, t2, t3, t4 = st.tabs(["🏠 بيانات المركز", "👥 إدارة المستخدمين", "👨‍🏫 إدارة الدكاترة", "👤 حسابي"])
    with t1:
        with st.form("center_set"):
            n, tel, addr = st.text_input("اسم المركز", center_info.get('اسم_المركز')), st.text_input("الهاتف", center_info.get('الهاتف')), st.text_input("العنوان", center_info.get('العنوان'))
            if st.form_submit_button("تحديث بيانات المركز"):
                pd.DataFrame([{"اسم_المركز": n, "الهاتف": tel, "العنوان": addr}]).to_excel(SETTINGS_FILE, index=False)
                st.success("تم التحديث"); st.rerun()
    with t2: # إدارة المستخدمين
        u_df = load_data(USERS_FILE, USER_COLS)
        with st.form("add_user"):
            new_u, new_p = st.text_input("اسم المستخدم الجديد"), st.text_input("كلمة المرور", type="password")
            role = st.selectbox("الصلاحية", ["Admin", "User"])
            if st.form_submit_button("إضافة مستخدم جديد"):
                pd.concat([u_df, pd.DataFrame([{"username": new_u, "password": new_p, "role": role}])]).to_excel(USERS_FILE, index=False)
                st.success("تمت الإضافة"); st.rerun()
        st.divider()
        del_u = st.selectbox("اختر مستخدم للحذف", u_df["username"].tolist())
        if st.button("❌ حذف المستخدم المحدد"):
            if del_u == st.session_state['current_user']: st.error("لا يمكن حذف الحساب الحالي")
            else:
                u_df[u_df["username"] != del_u].to_excel(USERS_FILE, index=False); st.success("تم الحذف"); st.rerun()
    with t3: # إدارة الدكاترة المحاضرين
        lec_df = load_data(LECTURERS_FILE, LEC_COLS)
        with st.form("add_lec"):
            l_name = st.text_input("اسم الدكتور الجديد")
            if st.form_submit_button("إضافة لقائمة المحاضرين"):
                if l_name:
                    pd.concat([lec_df, pd.DataFrame([{"الاسم": l_name}])]).to_excel(LECTURERS_FILE, index=False)
                    st.success("تمت الإضافة"); st.rerun()
        st.dataframe(lec_df, use_container_width=True)
    with t4: # تغيير كلمة المرور للمستخدم الحالي
        u_df = load_data(USERS_FILE, USER_COLS)
        with st.form("pass_ch"):
            np = st.text_input("كلمة المرور الجديدة", type="password")
            if st.form_submit_button("تحديث كلمة المرور"):
                idx = u_df[u_df["username"] == st.session_state['current_user']].index[0]
                u_df.at[idx, "password"] = np
                u_df.to_excel(USERS_FILE, index=False); st.success("تم التحديث بنجاح"); st.rerun()
import streamlit as st
import pandas as pd
from datetime import date
import os
import base64
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components

# 🔥 1. إعداد الصفحة والاستايل الملكي
st.set_page_config(page_title="Murshidoon ERP Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { background-color: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); border-right: 6px solid #0B3154; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #0B3154; color: white; height: 3em; font-weight: bold; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #00B5CC; box-shadow: 0 5px 15px rgba(0,181,204,0.3); }
    h1, h2, h3 { color: #0B3154; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    .stTabs [aria-selected="true"] { background-color: #0B3154 !important; color: white !important; border-radius: 5px; }
    .login-logo { display: block; margin: auto; width: 220px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 🔥 2. تعريف الملفات والقواعد
DB_FILE, STUDENTS_FILE, SETTINGS_FILE = "main_records.xlsx", "students_db.xlsx", "settings_db.xlsx"
EXPENSES_FILE, USERS_FILE, LECTURERS_FILE = "expenses_db.xlsx", "users_db.xlsx", "lecturers_db.xlsx"
BLACKBOARD_FILE, LOGO_FILE = "blackboard_db.xlsx", "logo.jpg"

PAYMENT_METHODS = ["كاش", "بطاقة دفع", "تحويل فورا", "تحويل", "حساب بنكى"]
STD_COLS = ["الاسم", "الموبايل", "الإيميل", "تاريخ التسجيل"]
BILL_COLS = ["ID", "تاريخ_الفاتورة", "تاريخ_الاستحقاق", "الطالب", "رقم_الطالب", "المادة", "عدد_الساعات", "وقت_البداية", "وقت_النهاية", "الدكتور_المشرف", "الدكتور_المحاضر", "طريقة_الدفع", "الإجمالي", "المدفوع", "المتبقي"]
EXP_COLS = ["التاريخ", "البند", "المبلغ"]
BB_COLS = ["اسم_الطالب", "اسم_المستخدم", "كلمة_المرور", "ملاحظات"]
SET_COLS = ["اسم_المركز", "العنوان", "الهاتف", "الإيميل"]
USER_COLS = ["role", "username", "password"]
LEC_COLS = ["الاسم"]

# 🔥 3. دالات المساعدة
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_excel(file)
            for col in columns:
                if col not in df.columns: df[col] = None
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def get_logo_64():
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

def generate_invoice_html(title, data_dict, center_info):
    logo_64 = get_logo_64()
    logo_tag = f'<img src="data:image/jpeg;base64,{logo_64}" width="120">' if logo_64 else ''
    rows = "".join([f"<tr><td style='padding:10px; border-bottom:1px solid #eee; font-weight:bold;'>{k}</td><td style='padding:10px; border-bottom:1px solid #eee;'>{str(v) if pd.notna(v) else '---'}</td></tr>" for k, v in data_dict.items()])
    return f"""
    <div id="invoice" style="direction: rtl; font-family: 'Arial'; padding: 30px; background: white; border: 1px solid #ddd; border-radius: 15px; max-width: 800px; margin: auto;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><h2 style="color: #0B3154; margin: 0;">{center_info.get('اسم_المركز', 'مرشدون')}</h2><p>{center_info.get('العنوان', '')} | {center_info.get('الهاتف', '')}</p></div>
            <div>{logo_tag}</div>
        </div>
        <hr><h3 style="text-align: center; color: white; background: #0B3154; padding: 8px; border-radius: 5px;">{title}</h3>
        <table style="width:100%; border-collapse:collapse;">{rows}</table>
        <div class="no-print" style="text-align: center; margin-top: 30px;"><button onclick="window.print()" style="padding: 10px 20px; background: #0B3154; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">🖨️ طباعة الفاتورة أو حفظ PDF</button></div>
    </div>
    """

# 🔥 4. شاشة الدخول
if not os.path.exists(USERS_FILE):
    pd.DataFrame([{"role": "Admin", "username": "marwan", "password": "Marwan@4101991"}]).to_excel(USERS_FILE, index=False)

if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        l64 = get_logo_64()
        if l64: st.markdown(f'<img src="data:image/jpeg;base64,{l64}" class="login-logo">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>مرشدون ERP Pro</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u, p = st.text_input("اسم المستخدم"), st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول آمن"):
                users = load_data(USERS_FILE, USER_COLS)
                if not users[(users['username'] == u) & (users['password'] == p)].empty:
                    st.session_state['auth'], st.session_state['current_user'] = True, u
                    st.rerun()
                else: st.error("بيانات الدخول غير صحيحة")
    st.stop()

# 🔥 5. الواجهة والقائمة
settings_df = load_data(SETTINGS_FILE, SET_COLS)
center_info = settings_df.iloc[0].to_dict() if not settings_df.empty else {"اسم_المركز": "مرشدون"}

with st.sidebar:
    l64 = get_logo_64()
    if l64: st.markdown(f'<img src="data:image/jpeg;base64,{l64}" style="width:100%; margin-bottom:20px; border-radius:10px;">', unsafe_allow_html=True)
    selected = option_menu("ERP PRO", ["الرئيسية", "الطلاب", "الفواتير", "بيانات Blackboard", "المصروفات", "حسابات المحاضرين", "⚙️ الإعدادات"], 
        icons=["house", "people", "cash-stack", "book", "wallet2", "person-badge", "gear"], default_index=0)
    if st.button("🚪 تسجيل الخروج"): st.session_state['auth'] = False; st.rerun()

# --- الرئيسية (البحث السريع) ---
if selected == "الرئيسية":
    st.header("📊 الإحصائيات والبحث السريع")
    df, std_df = load_data(DB_FILE, BILL_COLS), load_data(STUDENTS_FILE, STD_COLS)
    search_q = st.text_input("🔍 بحث سريع برقم تليفون الطالب", placeholder="اكتب رقم التليفون هنا...")
    if search_q:
        found = std_df[std_df["الموبايل"].astype(str) == search_q]
        if not found.empty:
            name = found.iloc[0]["الاسم"]
            bills = df[df["الطالب"] == name]
            st.success(f"تم العثور على: {name}")
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي المطلوب", f"{int(bills['الإجمالي'].sum())} ر.ق")
            c2.metric("إجمالي المدفوع", f"{int(bills['المدفوع'].sum())} ر.ق")
            c3.metric("المتبقي عليه", f"{int(bills['المتبقي'].sum())} ر.ق")
            st.table(bills[["تاريخ_الفاتورة", "المادة", "المدفوع", "المتبقي"]])
        else: st.warning("لا يوجد طالب بهذا الرقم.")
    st.divider()
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي المبيعات", f"{int(pd.to_numeric(df['الإجمالي'], errors='coerce').sum())} ر.ق")
        c2.metric("المحصل الفعلي", f"{int(pd.to_numeric(df['المدفوع'], errors='coerce').sum())} ر.ق")
        c3.metric("المتأخرات العامة", f"{int(pd.to_numeric(df['المتبقي'], errors='coerce').sum())} ر.ق")

# --- الطلاب ---
elif selected == "الطلاب":
    st.header("👥 إدارة الطلاب")
    std_df, bill_df = load_data(STUDENTS_FILE, STD_COLS), load_data(DB_FILE, BILL_COLS)
    t1, t2, t3, t4 = st.tabs(["➕ إضافة", "✏️ تعديل", "📋 كشف حساب", "🗑️ حذف"])
    with t1:
        with st.form("s_a"):
            n, p, e = st.text_input("الاسم"), st.text_input("رقم التليفون"), st.text_input("الإيميل")
            if st.form_submit_button("حفظ"):
                pd.concat([std_df, pd.DataFrame([{"الاسم": n, "الموبايل": p, "الإيميل": e, "تاريخ التسجيل": date.today()}])]).to_excel(STUDENTS_FILE, index=False); st.rerun()
    with t2:
        if not std_df.empty:
            sn = st.selectbox("اختر طالب", std_df["الاسم"].tolist())
            idx = std_df[std_df["الاسم"] == sn].index[0]
            with st.form("s_e"):
                un, up, ue = st.text_input("الاسم", std_df.at[idx, "الاسم"]), st.text_input("التليفون", std_df.at[idx, "الموبايل"]), st.text_input("الإيميل", std_df.at[idx, "الإيميل"])
                if st.form_submit_button("تحديث"):
                    std_df.at[idx, "الاسم"], std_df.at[idx, "الموبايل"], std_df.at[idx, "الإيميل"] = un, up, ue
                    std_df.to_excel(STUDENTS_FILE, index=False); st.success("تم التحديث"); st.rerun()
    with t3:
        if not std_df.empty:
            target = st.selectbox("كشف حساب", std_df["الاسم"].tolist())
            st_bills = bill_df[bill_df["الطالب"] == target]
            if not st_bills.empty:
                data = {"الطالب": target, "الساعات": st_bills['عدد_الساعات'].sum(), "الإجمالي": st_bills['الإجمالي'].sum(), "المحصل": st_bills['المدفوع'].sum(), "المتبقي": st_bills['المتبقي'].sum()}
                components.html(generate_invoice_html("كشف حساب مالي", data, center_info), height=650)
    with t4:
        if not std_df.empty:
            dn = st.selectbox("حذف طالب", std_df["الاسم"].tolist())
            if st.button("❌ حذف نهائي"):
                std_df[std_df["الاسم"] != dn].to_excel(STUDENTS_FILE, index=False); st.rerun()

# --- الفواتير ---
elif selected == "الفواتير":
    st.header("💰 نظام الفواتير")
    df, std_df, lec_df = load_data(DB_FILE, BILL_COLS), load_data(STUDENTS_FILE, STD_COLS), load_data(LECTURERS_FILE, LEC_COLS)
    t1, t2, t3, t4 = st.tabs(["🆕 إصدار فاتورة", "🖨️ طباعة", "✏️ تعديل شامل", "🗑️ حذف"])
    with t1:
        with st.form("i_n"):
            sn = st.selectbox("الطالب", std_df["الاسم"].tolist() if not std_df.empty else ["---"])
            phone = std_df[std_df["الاسم"] == sn]["الموبايل"].values[0] if not std_df.empty and sn != "---" else ""
            m, h = st.text_input("المادة"), st.number_input("الساعات", min_value=0.0)
            c1, c2 = st.columns(2)
            with c1: ts, te = st.text_input("البدء"), st.text_input("الانتهاء")
            with c2: pm, due = st.selectbox("الدفع", PAYMENT_METHODS), st.date_input("الاستحقاق")
            lm, ll = st.selectbox("المشرف", lec_df["الاسم"].tolist() if not lec_df.empty else ["---"]), st.selectbox("المحاضر", lec_df["الاسم"].tolist() if not lec_df.empty else ["---"])
            tot, pdv = st.number_input("الإجمالي"), st.number_input("المدفوع")
            if st.form_submit_button("إصدار وحفظ"):
                new = pd.DataFrame([{"ID": len(df)+1001, "تاريخ_الفاتورة": date.today(), "تاريخ_الاستحقاق": pd.to_datetime(due), "الطالب": sn, "رقم_الطالب": phone, "المادة": m, "عدد_الساعات": h, "وقت_البداية": ts, "وقت_النهاية": te, "الدكتور_المشرف": lm, "الدكتور_المحاضر": ll, "طريقة_الدفع": pm, "الإجمالي": tot, "المدفوع": pdv, "المتبقي": tot-pdv}])
                pd.concat([df, new]).to_excel(DB_FILE, index=False); st.success("تم الحفظ"); st.rerun()
    with t2:
        if not df.empty:
            search_std = st.selectbox("بحث فواتير طالب", ["عرض الكل"] + std_df["الاسم"].tolist())
            filtered = df if search_std == "عرض الكل" else df[df["الطالب"] == search_std]
            if not filtered.empty:
                tid = st.selectbox("اختر رقم الفاتورة", filtered["ID"].tolist()[::-1])
                components.html(generate_invoice_html("فاتورة رسوم دراسية", filtered[filtered["ID"] == tid].iloc[0].to_dict(), center_info), height=950)
    with t3: # 🔥 التعديل الشامل
        if not df.empty:
            inv_id = st.selectbox("تعديل فاتورة رقم", df["ID"].tolist())
            idx = df[df["ID"] == inv_id].index[0]
            with st.form("edit_f"):
                e_m, e_h = st.text_input("المادة", df.at[idx, "المادة"]), st.number_input("الساعات", value=float(df.at[idx, "عدد_الساعات"]))
                e_ts, e_te = st.text_input("البدء", df.at[idx, "وقت_البداية"]), st.text_input("الانتهاء", df.at[idx, "وقت_النهاية"])
                e_mushref = st.selectbox("المشرف", lec_df["الاسم"].tolist(), index=lec_df["الاسم"].tolist().index(df.at[idx, "الدكتور_المشرف"]) if df.at[idx, "الدكتور_المشرف"] in lec_df["الاسم"].tolist() else 0)
                e_mohadir = st.selectbox("المحاضر", lec_df["الاسم"].tolist(), index=lec_df["الاسم"].tolist().index(df.at[idx, "الدكتور_المحاضر"]) if df.at[idx, "الدكتور_المحاضر"] in lec_df["الاسم"].tolist() else 0)
                e_tot, e_pd = st.number_input("الإجمالي", value=float(df.at[idx, "الإجمالي"])), st.number_input("المدفوع", value=float(df.at[idx, "المدفوع"]))
                if st.form_submit_button("تحديث شامل"):
                    df.at[idx, "المادة"], df.at[idx, "عدد_الساعات"], df.at[idx, "وقت_البداية"], df.at[idx, "وقت_النهاية"] = e_m, e_h, e_ts, e_te
                    df.at[idx, "الدكتور_المشرف"], df.at[idx, "الدكتور_المحاضر"] = e_mushref, e_mohadir
                    df.at[idx, "الإجمالي"], df.at[idx, "المدفوع"], df.at[idx, "المتبقي"] = e_tot, e_pd, e_tot-e_pd
                    df.to_excel(DB_FILE, index=False); st.success("تم التحديث"); st.rerun()
    with t4:
        if not df.empty:
            did = st.selectbox("حذف فاتورة", df["ID"].tolist())
            if st.button("❌ حذف نهائي"):
                df[df["ID"] != did].to_excel(DB_FILE, index=False); st.rerun()

# --- Blackboard ---
elif selected == "بيانات Blackboard":
    st.header("📖 حسابات Blackboard")
    bb_df, std_df = load_data(BLACKBOARD_FILE, BB_COLS), load_data(STUDENTS_FILE, STD_COLS)
    t1, t2, t3 = st.tabs(["📋 عرض", "➕ إضافة/تعديل", "🗑️ حذف"])
    with t1: st.dataframe(bb_df, use_container_width=True)
    with t2:
        with st.form("bb_a"):
            s = st.selectbox("الطالب", std_df["الاسم"].tolist() if not std_df.empty else ["---"])
            u, p = st.text_input("User"), st.text_input("Pass")
            if st.form_submit_button("حفظ"):
                bb_df = bb_df[bb_df["اسم_الطالب"] != s]
                pd.concat([bb_df, pd.DataFrame([{"اسم_الطالب": s, "اسم_المستخدم": u, "كلمة_المرور": p}])]).to_excel(BLACKBOARD_FILE, index=False); st.rerun()
    with t3:
        if not bb_df.empty:
            dbb = st.selectbox("حذف حساب", bb_df["اسم_الطالب"].tolist())
            if st.button("❌ حذف"):
                bb_df[bb_df["اسم_الطالب"] != dbb].to_excel(BLACKBOARD_FILE, index=False); st.rerun()

# --- المصروفات وحساب المحاضرين ---
elif selected == "المصروفات":
    st.header("💸 المصروفات")
    exp_df = load_data(EXPENSES_FILE, EXP_COLS)
    with st.form("ex_a"):
        b, m = st.text_input("البند"), st.number_input("المبلغ")
        if st.form_submit_button("حفظ"):
            pd.concat([exp_df, pd.DataFrame([{"التاريخ": date.today(), "البند": b, "المبلغ": m}])]).to_excel(EXPENSES_FILE, index=False); st.rerun()
    st.dataframe(exp_df, use_container_width=True)

elif selected == "حسابات المحاضرين":
    st.header("👨‍🏫 تقارير الدكاترة")
    df = load_data(DB_FILE, BILL_COLS)
    if not df.empty:
        lecs = [x for x in df['الدكتور_المحاضر'].unique() if pd.notna(x) and x != "---"]
        if lecs:
            doc = st.selectbox("اختر الدكتور", lecs)
            d_data = df[df['الدكتور_المحاضر'] == doc]
            data = {"المحاضر": doc, "إجمالي الساعات": d_data['عدد_الساعات'].sum(), "إجمالي القيمة": d_data['الإجمالي'].sum(), "المحصل": d_data['المدفوع'].sum(), "المتبقي": d_data['المتبقي'].sum()}
            components.html(generate_invoice_html("كشف حساب محاضر مالي", data, center_info), height=600)

# --- الإعدادات ---
elif selected == "⚙️ الإعدادات":
    st.header("⚙️ إعدادات النظام")
    t1, t2, t3, t4 = st.tabs(["🏠 بيانات المركز", "👥 المستخدمين", "👨‍🏫 الدكاترة", "👤 حسابي"])
    with t1:
        with st.form("c_edit"):
            n, a, ph, em = st.text_input("المركز", center_info.get('اسم_المركز')), st.text_input("العنوان", center_info.get('العنوان')), st.text_input("الهاتف", center_info.get('الهاتف')), st.text_input("الإيميل", center_info.get('الإيميل'))
            uploaded_logo = st.file_uploader("رفع لوجو", type=["png", "jpg", "jpeg"])
            if st.form_submit_button("حفظ الإعدادات واللوجو"):
                pd.DataFrame([{"اسم_المركز": n, "العنوان": a, "الهاتف": ph, "الإيميل": em}]).to_excel(SETTINGS_FILE, index=False)
                if uploaded_logo:
                    with open(LOGO_FILE, "wb") as f: f.write(uploaded_logo.getbuffer())
                st.success("تم الحفظ"); st.rerun()
    with t2:
        u_df = load_data(USERS_FILE, USER_COLS)
        with st.form("u_add"):
            un, up = st.text_input("اسم المستخدم الجديد"), st.text_input("كلمة المرور")
            if st.form_submit_button("إضافة"):
                pd.concat([u_df, pd.DataFrame([{"username": un, "password": up, "role": "User"}])]).to_excel(USERS_FILE, index=False); st.rerun()
        du = st.selectbox("حذف مستخدم", u_df["username"].tolist())
        if st.button("❌ حذف"): u_df[u_df["username"] != du].to_excel(USERS_FILE, index=False); st.rerun()
    with t3:
        l_df = load_data(LECTURERS_FILE, LEC_COLS)
        with st.form("l_add"):
            ln = st.text_input("اسم الدكتور الجديد")
            if st.form_submit_button("إضافة"): pd.concat([l_df, pd.DataFrame([{"الاسم": ln}])]).to_excel(LECTURERS_FILE, index=False); st.rerun()
        dl = st.selectbox("حذف دكتور", l_df["الاسم"].tolist())
        if st.button("❌ حذف دكتور"): l_df[l_df["الاسم"] != dl].to_excel(LECTURERS_FILE, index=False); st.rerun()
    with t4:
        u_df = load_data(USERS_FILE, USER_COLS)
        idx = u_df[u_df["username"] == st.session_state['current_user']].index[0]
        with st.form("my_acc"):
            new_u, new_p = st.text_input("اسم المستخدم", u_df.at[idx, "username"]), st.text_input("كلمة المرور", u_df.at[idx, "password"], type="password")
            if st.form_submit_button("تحديث حسابي"):
                u_df.at[idx, "username"], u_df.at[idx, "password"] = new_u, new_p
                u_df.to_excel(USERS_FILE, index=False); st.session_state['current_user'] = new_u; st.rerun()
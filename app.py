import streamlit as st
from db_manager import PantryDB
import pandas as pd
from vision_manager import scan_receipt, get_ai_recipes
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_cookies_manager import EncryptedCookieManager
from dotenv import load_dotenv
load_dotenv()

# cokkie manager must be initialized before any st.cache_resource or st.cache_data
st.set_page_config(page_title="Smart Pantry AI", page_icon="🥑", layout="centered")


cookies = EncryptedCookieManager(
    password="some_very_secret_password_123", 
)

if not cookies.ready():
    with st.spinner("Loading your pantry..."):
        st.stop()
# conect to database
@st.cache_resource
def get_db_connection():
    return PantryDB()

db = get_db_connection()

# manage user session

# check if we have a user_id in cookies to restore session
saved_user_id = cookies.get("user_id")

if 'logged_in' not in st.session_state:
    if saved_user_id:
        user_data = db.get_user_by_id(saved_user_id)
        if user_data:
            st.session_state.logged_in = True
            st.session_state.user_id = saved_user_id
            st.session_state.username = user_data.get('username', 'User')
        else:
            st.session_state.logged_in = False
    else:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None

# for who is not logged in, show login/signup tabs
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Login"):
            user_data = db.authenticate_user(u, p)
            if user_data:
                user_id_str = str(user_data['_id'])
                st.session_state.logged_in = True
                st.session_state.user_id = user_id_str
                st.session_state.username = u
                
                # save user_id in cookies for session persistence
                cookies["user_id"] = user_id_str
                cookies.save()
                
                st.success(f"Welcome back, {u}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
                
    with tab2:
        st.subheader("Create New Account")
        nu = st.text_input("Choose Username", key="reg_u")
        np = st.text_input("Choose Password", type="password", key="reg_p")
        if st.button("Register"):
            if db.create_user(nu, np):
                st.success("Account created! You can now login.")
            else:
                st.error("Username already exists.")
    st.stop() # stop here for non-logged in users

# for logged in users, show the main app

st.title(f"🥑 {st.session_state.username}'s Smart Pantry")

# menu options
menu = ["My Pantry", "Shopping List", "Add New Item", "Scan Receipt (AI)", "AI Chef 👨‍🍳"]
choice = st.sidebar.selectbox("Menu", menu)

st.sidebar.divider()
st.sidebar.subheader("🚀 Presentation Tools")
if st.sidebar.button("Run Demo Mode"):
    demo_item = db.seed_demo_data(st.session_state.user_id) 
    st.sidebar.success(f"Demo injected for {st.session_state.username}!")
    st.rerun()

if st.sidebar.button("Logout"):
    if "user_id" in cookies:
        cookies.pop("user_id") # delete user_id from cookies on logout
    cookies.save()
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.rerun()

# my pantry view
if choice == "My Pantry":
    st.subheader("What's in my kitchen?")
    items = db.get_all_items(st.session_state.user_id)
    
    if items:
        for item in items:
            expiry = item.get('expiry_date')
            status_msg = ""
            days_to_expiry = None
            
            if expiry:
                days_to_expiry = (expiry - datetime.now()).days
                if days_to_expiry < 0: status_msg = "🚨 EXPIRED"
                elif days_to_expiry < 3: status_msg = f"⏳ Exp. in {days_to_expiry}d"

            title = f"{item['product_name']} - {item['current_qty']} {item.get('unit', 'units')} {status_msg}"
            
            with st.expander(title):
                with st.spinner("AI calculating..."):
                    days_by_usage = db.predict_days_remaining(st.session_state.user_id, item['product_name'])
                
                # graph showing predicted consumption if we have usage data
                if days_by_usage is not None:
                    df_plot = pd.DataFrame({
                        "Day": ["Today", f"In {days_by_usage} Days"],
                        "Expected Qty": [item['current_qty'], 0]
                    })
                    fig = px.line(df_plot, x="Day", y="Expected Qty", 
                                 title=f"Consumption Forecast for {item['product_name']}",
                                 markers=True)
                    fig.update_traces(line_color='#FF4B4B')
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{datetime.now().timestamp()}")

                final_pred = days_by_usage
                if days_by_usage is not None and item['current_qty'] <= 4:
                    final_pred = min(days_by_usage, item['current_qty'])
                
                if days_to_expiry is not None:
                    final_pred = min(final_pred, days_to_expiry) if final_pred else days_to_expiry

                if item['current_qty'] <= 0:
                    st.error(f"🚨 Out of Stock: {item['product_name']}")
                    if st.button(f"🛒 Move to List & Delete", key=f"reorder_{item['_id']}"):
                        db.add_to_shopping_list(st.session_state.user_id, item['product_name'])
                        db.delete_item(st.session_state.user_id, item['product_name'])
                        st.rerun()
                
                elif final_pred is not None:
                    if final_pred <= 2:
                        st.warning(f"⚠️ Finish within {final_pred} days!")
                        st.info("🤖 Did you finish this item?")
                        c_y, c_n = st.columns(2)
                        if c_y.button(f"Yes, finished", key=f"ai_y_{item['_id']}"):
                            db.log_action(st.session_state.user_id, item['product_name'], "consumed", item['current_qty'])
                            db.add_to_shopping_list(st.session_state.user_id, item['product_name'])
                            db.delete_item(st.session_state.user_id, item['product_name'])
                            st.rerun()
                        if c_n.button(f"No, still have it", key=f"ai_n_{item['_id']}"):
                            st.toast("Got it!")
                    else:
                        st.info(f"💡 Smart Forecast: {final_pred} days left")

                st.divider()
                st.write(f"**Category:** {item.get('category', 'Other')}")
                col1, col2, col3 = st.columns(3)
                
                if col1.button(f"🛒 Add to List", key=f"inv_shop_{item['_id']}"):
                    db.add_to_shopping_list(st.session_state.user_id, item['product_name'])
                    st.toast("Added!")
                
                if col2.button(f"🍽️ Consume 1", key=f"cons_{item['_id']}"):
                    if item['current_qty'] > 0:
                        db.log_action(st.session_state.user_id, item['product_name'], "consumed", 1)
                        db.update_item_quantity(st.session_state.user_id, item['product_name'], -1)
                        st.rerun()
                
                if col3.button(f"🗑️ Delete", key=f"inv_del_{item['_id']}"):
                    db.delete_item(st.session_state.user_id, item['product_name'])
                    st.rerun()
    else:
        st.info("Pantry is empty.")

# Shopping List view
elif choice == "Shopping List":
    st.subheader("🛒 My Shopping List")
    
    col_in, col_add = st.columns([3, 1])
    with col_in:
        new_item = st.text_input("Need something?", placeholder="Milk...", label_visibility="collapsed")
    with col_add:
        if st.button("Add"):
            if new_item:
                db.add_to_shopping_list(st.session_state.user_id, new_item, quantity=1)
                st.rerun()

    st.divider()
    shopping_data = db.get_shopping_list(st.session_state.user_id)
    
    if shopping_data:
        for item in shopping_data:
            c_check, c_name, c_qty, c_del = st.columns([0.5, 2, 1, 0.5])
            edited_name = c_name.text_input("Item", value=item['item'], key=f"edit_n_{item['_id']}", label_visibility="collapsed")
            current_qty = item.get('quantity', 1)
            new_qty = c_qty.number_input("Qty", min_value=1, value=int(current_qty), key=f"q_{item['_id']}", label_visibility="collapsed")
            
            if c_check.button("✅", key=f"check_{item['_id']}"):
                db.move_to_pantry(st.session_state.user_id, edited_name, new_qty)
                st.rerun()

            if c_del.button("🗑️", key=f"del_{item['_id']}"):
                db.remove_from_shopping_list(st.session_state.user_id, item['item'])
                st.rerun()
    else:
        st.info("List is empty.")

# Add New Item view
elif choice == "Add New Item":
    st.subheader("Manual Item Entry")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Product Name")
        cat = st.selectbox("Category", ["Dairy", "Meat", "Veggies", "Dry Goods", "Other"])
        qty = st.number_input("Quantity", min_value=1)
        prot = st.number_input("Protein per unit", min_value=0)
        date = st.date_input("Expiry Date", value=datetime.now() + timedelta(days=7))
        
        if st.form_submit_button("Add to Pantry"):
            db.add_item(st.session_state.user_id, name, cat, qty, "units", prot, expiry_date=datetime.combine(date, datetime.min.time()))
            st.success(f"{name} added!")

# Scan Receipt view
elif choice == "Scan Receipt (AI)":
    st.subheader("📸 Receipt Scanner")
    img_file = st.camera_input("Scan your receipt")
    
    if img_file:
        if 'detected_items' not in st.session_state:
            with st.spinner("AI analyzing receipt..."):
                st.session_state.detected_items = scan_receipt(img_file)

        if st.session_state.detected_items:
            with st.form("review_scan"):
                final_items = []
                for i, item in enumerate(st.session_state.detected_items):
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
                    name = c1.text_input("Name", value=item.get('product_name', ''), key=f"n_{i}")
                    qty = c2.number_input("Qty", value=int(item.get('quantity', 1)), min_value=1, key=f"q_{i}")
                    prot = c3.number_input("Prot", value=int(item.get('protein_per_unit', 0)), key=f"p_{i}")
                    dt = c4.date_input("Expiry", value=datetime.now() + timedelta(days=7), key=f"d_{i}")
                    final_items.append({"name": name, "cat": item.get('category', 'Other'), "qty": qty, "prot": prot, "date": datetime.combine(dt, datetime.min.time())})
                
                if st.form_submit_button("✅ Save All"):
                    for fi in final_items:
                        db.add_item(st.session_state.user_id, fi['name'], fi['cat'], fi['qty'], "units", fi['prot'], expiry_date=fi['date'])
                    del st.session_state.detected_items
                    st.rerun()

# AI Chef view
elif choice == "AI Chef 👨‍🍳":
    st.subheader("What can I cook today?")
    st.info("The AI will suggest recipes based on your current pantry items.")
    
    items = db.get_all_items(st.session_state.user_id)
    product_names = [item['product_name'] for item in items if item['current_qty'] > 0]
    
    if product_names:
        if st.button("Generate Recipes"):
            with st.spinner("The Chef is thinking..."):
                recipe = get_ai_recipes(product_names)
                st.markdown(recipe)
    else:
        st.warning("Your pantry is empty! Add some items to get recipes.")
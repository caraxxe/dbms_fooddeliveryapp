"""
Food Delivery Full App (Complete Working Version) - Streamlit
- Modern UI with all features
- Complete user panel: browse restaurants, menu items, cart, checkout, orders
- Complete admin panel: manage restaurants, menu items, orders, partners, payments
- Delivery partner panel: manage order deliveries and payments
- User registration system
- Automatic quantity management
- Payment only collected when delivery partner marks as delivered
"""

import streamlit as st
import mysql.connector
from decimal import Decimal
import pandas as pd
from datetime import datetime
import time

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="FoodDelight - Food Delivery App",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- DB CONFIG --------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Aayush123&",
    "database": "food_delivery"
}

# -------------------- DB HELPERS --------------------
def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        st.error(f"DB Connection Error: {str(e)}")
        return None

def fetch_all(query, params=None):
    conn = get_db()
    if not conn: 
        return [], []
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        return cols, rows
    except mysql.connector.Error as e:
        st.error(f"Query Error: {str(e)}")
        return [], []
    finally:
        cur.close()
        conn.close()

def execute(query, params=None):
    conn = get_db()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        conn.commit()
        return True
    except mysql.connector.Error as e:
        st.error(f"DB Error: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

def call_proc(proc_name, args=None):
    conn = get_db()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.callproc(proc_name, args or ())
        conn.commit()
        return True
    except mysql.connector.Error as e:
        st.error(f"Procedure Error: {str(e)}")
        return None
    finally:
        cur.close()
        conn.close()

def fetch_one(query, params=None):
    conn = get_db()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        row = cur.fetchone()
        return row
    except mysql.connector.Error as e:
        st.error(f"Query Error: {str(e)}")
        return None
    finally:
        cur.close()
        conn.close()

# -------------------- CREATE MISSING TABLES --------------------
def create_missing_tables():
    """Create the orderitem table if it doesn't exist"""
    conn = get_db()
    if not conn:
        return False
    
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orderitem (
                orderitem_id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                item_id INT NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES menuitem(item_id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        return True
    except mysql.connector.Error as e:
        st.error(f"Error creating table: {e}")
        return False
    finally:
        cur.close()
        conn.close()

# -------------------- SESSION STATE MANAGEMENT --------------------
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'current_restaurant' not in st.session_state:
        st.session_state.current_restaurant = None
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'show_add_restaurant' not in st.session_state:
        st.session_state.show_add_restaurant = False
    if 'show_add_menuitem' not in st.session_state:
        st.session_state.show_add_menuitem = False
    if 'show_add_partner' not in st.session_state:
        st.session_state.show_add_partner = False
    if 'tables_created' not in st.session_state:
        st.session_state.tables_created = False
    if 'edit_menuitem_id' not in st.session_state:
        st.session_state.edit_menuitem_id = None

# -------------------- STYLING --------------------
def apply_custom_styles():
    st.markdown("""
        <style>
        .main {
            background-color: #FFF8F2;
        }
        .stButton>button {
            background-color: #FF6B35;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #FF8E53;
            color: white;
        }
        .card {
            background-color: #FFFFFF;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #E0E0E0;
            margin: 0.5rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

# -------------------- LOGIN SCREEN --------------------
def show_login_screen():
    st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🍔 FoodDelight</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Welcome Back!</h3>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("👤 Email / Username")
        
        with col2:
            password = st.text_input("🔒 Password / Phone", type="password")
        
        role = st.radio("Login as:", ["👤 User", "👨‍💼 Admin", "🚚 Delivery Partner"], horizontal=True)
        
        login_clicked = st.form_submit_button("🚀 Login")
        
        if login_clicked:
            if not username or not password:
                st.error("Please fill all fields")
                return
            
            # FIXED: Proper role detection
            if "Admin" in role:
                role_key = "admin"
            elif "Delivery Partner" in role:
                role_key = "partner"
            else:
                role_key = "user"
            
            if role_key == "admin":
                if (username == "admin" and password == "admin123") or username == "admin@foodapp.com":
                    st.session_state.logged_in = True
                    st.session_state.user_role = "admin"
                    st.session_state.user_data = {"name": "Admin"}
                    st.session_state.page = "admin_dashboard"
                    st.rerun()
                else:
                    st.error("Invalid admin credentials")
            
            elif role_key == "partner":
                # FIXED: delivery partner login correct
                row = fetch_one("SELECT partner_id, name, phone FROM deliverypartner WHERE name=%s AND phone=%s", 
                              (username, password))
                if row:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "partner"
                    st.session_state.user_data = {
                        "partner_id": row[0], 
                        "name": row[1], 
                        "phone": row[2]
                    }
                    st.session_state.page = "partner_orders"
                    st.rerun()
                else:
                    st.error("Delivery partner not found. Use partner name as username and phone as password.")
            
            else:  # user
                row = fetch_one("SELECT user_id, name, email, phone, address FROM user WHERE (email=%s OR name=%s) AND phone=%s", 
                              (username, username, password))
                if row:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "user"
                    st.session_state.user_data = {
                        "user_id": row[0], 
                        "name": row[1], 
                        "email": row[2], 
                        "phone": row[3],
                        "address": row[4]
                    }
                    st.session_state.page = "user_restaurants"
                    st.rerun()
                else:
                    st.error("User not found or wrong phone")
    
    st.markdown("---")
    st.markdown("### 📝 Don't have an account?")
    
    with st.expander("Create New User Account"):
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
            
            with col2:
                phone = st.text_input("Phone")
                address = st.text_area("Address")
            
            register_clicked = st.form_submit_button("💾 Create Account")
            
            if register_clicked:
                if not all([name, email, phone]):
                    st.error("Name, Email, and Phone are required")
                    return
                
                # Check if user already exists
                existing = fetch_one("SELECT user_id FROM user WHERE email=%s OR phone=%s", (email, phone))
                if existing:
                    st.error("User with this email or phone already exists")
                    return
                
                # Insert new user
                if execute("INSERT INTO user (name, email, phone, address) VALUES (%s, %s, %s, %s)",
                          (name, email, phone, address or None)):
                    st.success("Account created successfully! You can now login.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Failed to create account")
    
    st.markdown("---")
    st.markdown("### 🔐 Demo Credentials")
    st.info("""
    - **Admin**: admin / admin123
    - **Users**: Try existing emails with phone as password  
    - **Partners**: Try existing partner names with phone as password
    """)

# -------------------- DELIVERY PARTNER PANEL --------------------
def show_partner_panel():
    st.sidebar.markdown(f"### 🚚 {st.session_state.user_data['name']}")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_data = {}
        st.session_state.page = "login"
        st.rerun()
    
    # Partner navigation
    page_options = {
        "📦 My Assigned Orders": "partner_orders",
        "📊 My Statistics": "partner_stats"
    }
    
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()))
    st.session_state.page = page_options[selected_page]
    
    if st.session_state.page == "partner_orders":
        show_partner_orders()
    elif st.session_state.page == "partner_stats":
        show_partner_stats()

def show_partner_orders():
    st.title("📦 My Assigned Orders")
    
    # Refresh button
    if st.button("🔄 Refresh"):
        st.rerun()
    
    # Get orders assigned to this partner
    cols, rows = fetch_all("""
        SELECT o.order_id, u.name as customer, u.address, o.total_amt, o.status, 
               p.status as payment_status, p.pay_id, p.method as payment_method
        FROM orders o 
        JOIN user u ON o.user_id = u.user_id
        LEFT JOIN payment p ON o.pay_id = p.pay_id
        WHERE o.partner_id = %s
        ORDER BY 
            CASE 
                WHEN o.status = 'Placed' THEN 1
                WHEN o.status = 'Out for Delivery' THEN 2
                WHEN o.status = 'Delivered' THEN 3
                ELSE 4
            END,
            o.order_date DESC
    """, (st.session_state.user_data['partner_id'],))
    
    if not rows:
        st.info("No orders assigned to you")
        return
    
    for order in rows:
        order_id, customer, address, total_amt, status, payment_status, pay_id, payment_method = order
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"Order #{order_id}")
                st.write(f"**Customer:** {customer}")
                st.write(f"**Address:** {address}")
                st.write(f"**Amount:** ₹{total_amt:.2f}")
                
                status_color = "🟢" if status == 'Delivered' else "🟡" if status == 'Out for Delivery' else "🔵"
                st.write(f"**Status:** {status_color} {status}")
                
                payment_color = "🟢" if payment_status == 'Paid' else "🔴"
                st.write(f"**Payment:** {payment_color} {payment_status} ({payment_method})")
            
            with col2:
                if status == 'Placed':
                    if st.button(f"🚚 Start Delivery", key=f"start_{order_id}"):
                        if call_proc("UpdateOrderStatus", [order_id, 'Out for Delivery', 'Pending']):
                            st.success(f"Started delivery for order #{order_id}")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Failed to update order status")
                
                elif status == 'Out for Delivery':
                    if payment_method == 'COD' and payment_status == 'Pending':
                        if st.button(f"💰 Collect COD", key=f"cod_{order_id}"):
                            if execute("UPDATE payment SET status='Paid' WHERE pay_id=%s", (pay_id,)):
                                st.success(f"COD payment collected for order #{order_id}")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Failed to update payment status")
                    
                    if st.button(f"✅ Mark Delivered", key=f"deliver_{order_id}"):
                        payment_status = 'Paid' if payment_method != 'COD' else 'Pending'
                        if call_proc("UpdateOrderStatus", [order_id, 'Delivered', payment_status]):
                            st.success(f"Order #{order_id} marked as delivered!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Failed to update order status")
            
            st.markdown("---")

def show_partner_stats():
    st.title("📊 My Delivery Statistics")
    
    partner_id = st.session_state.user_data['partner_id']
    
    # Get partner statistics
    cols, rows = fetch_all("""
        SELECT 
            COUNT(o.order_id) as total_deliveries,
            SUM(CASE WHEN o.status = 'Delivered' THEN 1 ELSE 0 END) as successful_deliveries,
            AVG(o.total_amt) as avg_order_value,
            SUM(o.total_amt) as total_delivery_value
        FROM deliverypartner dp
        LEFT JOIN orders o ON dp.partner_id = o.partner_id
        WHERE dp.partner_id = %s
        GROUP BY dp.partner_id
    """, (partner_id,))
    
    if rows:
        total_deliveries, successful, avg_value, total_value = rows[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Deliveries", total_deliveries or 0)
        with col2:
            st.metric("Successful Deliveries", successful or 0)
        with col3:
            st.metric("Avg Order Value", f"₹{avg_value or 0:.2f}")
        with col4:
            st.metric("Total Value", f"₹{total_value or 0:.2f}")
    
    # Recent deliveries
    st.subheader("Recent Deliveries")
    cols, rows = fetch_all("""
        SELECT o.order_id, u.name as customer, o.total_amt, o.status, o.order_date
        FROM orders o 
        JOIN user u ON o.user_id = u.user_id
        WHERE o.partner_id = %s
        ORDER BY o.order_date DESC
        LIMIT 10
    """, (partner_id,))
    
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No delivery history found")

# -------------------- ADMIN PANEL --------------------
def show_admin_panel():
    st.sidebar.markdown("### 👨‍💼 Admin Dashboard")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_data = {}
        st.session_state.page = "login"
        st.rerun()
    
    # Admin navigation
    admin_pages = {
        "📊 Dashboard": "admin_dashboard",
        "📦 Orders": "admin_orders", 
        "🏪 Restaurants": "admin_restaurants",
        "🍽️ Menu Items": "admin_menuitems",
        "🚚 Partners": "admin_partners",
        "💳 Payments": "admin_payments",
        "👥 Users": "admin_users",
        "🔍 Analytics": "admin_analytics"
    }
    
    selected_page = st.sidebar.radio("Admin Menu", list(admin_pages.keys()))
    st.session_state.page = admin_pages[selected_page]
    
    # Route to appropriate admin page
    if st.session_state.page == "admin_dashboard":
        show_admin_dashboard()
    elif st.session_state.page == "admin_orders":
        show_admin_orders()
    elif st.session_state.page == "admin_restaurants":
        show_admin_restaurants()
    elif st.session_state.page == "admin_menuitems":
        show_admin_menuitems()
    elif st.session_state.page == "admin_partners":
        show_admin_partners()
    elif st.session_state.page == "admin_payments":
        show_admin_payments()
    elif st.session_state.page == "admin_users":
        show_admin_users()
    elif st.session_state.page == "admin_analytics":
        show_admin_analytics()

def show_admin_dashboard():
    st.title("📊 Admin Dashboard")
    
    # Get stats
    total_orders = fetch_one("SELECT COUNT(*) FROM orders")[0] or 0
    total_users = fetch_one("SELECT COUNT(*) FROM user")[0] or 0
    total_restaurants = fetch_one("SELECT COUNT(*) FROM restaurant")[0] or 0
    total_partners = fetch_one("SELECT COUNT(*) FROM deliverypartner")[0] or 0
    revenue = fetch_one("SELECT COALESCE(SUM(total_amt), 0) FROM orders WHERE status='Delivered'")[0] or 0
    avg_rating = fetch_one("SELECT avg_restaurant_rating()")[0] or 0
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    with col1:
        st.metric("📦 Total Orders", total_orders)
    with col2:
        st.metric("👥 Total Users", total_users)
    with col3:
        st.metric("🏪 Restaurants", total_restaurants)
    with col4:
        st.metric("🚚 Partners", total_partners)
    with col5:
        st.metric("💰 Revenue", f"₹{revenue:.2f}")
    with col6:
        st.metric("⭐ Avg Rating", f"{avg_rating:.2f}")
    
    # Recent orders
    st.subheader("Recent Orders")
    cols, rows = fetch_all("""
        SELECT o.order_id, u.name as customer, o.total_amt, o.status, o.order_date
        FROM orders o 
        JOIN user u ON o.user_id = u.user_id
        ORDER BY o.order_date DESC 
        LIMIT 10
    """)
    
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True)

def show_admin_orders():
    st.title("📦 Order Management")
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    cols, rows = fetch_all("""
        SELECT o.order_id, u.name as customer, o.total_amt, o.status, 
               o.order_date, dp.name as delivery_partner, p.status as payment_status
        FROM orders o 
        LEFT JOIN user u ON o.user_id = u.user_id
        LEFT JOIN deliverypartner dp ON o.partner_id = dp.partner_id
        LEFT JOIN payment p ON o.pay_id = p.pay_id
        ORDER BY o.order_date DESC
    """)
    
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        
        # Add status update functionality
        st.subheader("Update Order Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            order_id = st.selectbox("Select Order", df['order_id'].tolist())
        
        with col2:
            new_status = st.selectbox("New Status", ["Placed", "Out for Delivery", "Delivered", "Cancelled"])
        
        with col3:
            if st.button("Update Status"):
                payment_status = 'Paid' if new_status == 'Delivered' else 'Pending'
                if call_proc("UpdateOrderStatus", [order_id, new_status, payment_status]):
                    st.success(f"Order {order_id} status updated to {new_status}")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Failed to update order status")
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No orders found")

def show_admin_restaurants():
    st.title("🏪 Restaurant Management")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("➕ Add Restaurant"):
            st.session_state.show_add_restaurant = True
    
    if st.session_state.get('show_add_restaurant', False):
        with st.form("add_restaurant_form"):
            name = st.text_input("Restaurant Name")
            address = st.text_area("Address")
            rating = st.number_input("Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Restaurant"):
                    if name:
                        execute("INSERT INTO restaurant (name, address, rating) VALUES (%s, %s, %s)",
                               (name, address, rating))
                        st.success("Restaurant added successfully")
                        st.session_state.show_add_restaurant = False
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Name is required")
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_add_restaurant = False
                    st.rerun()
    
    cols, rows = fetch_all("SELECT rest_id, name, address, rating FROM restaurant ORDER BY rest_id")
    
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True)
        
        # Edit functionality
        st.subheader("Edit Restaurant")
        edit_rest_id = st.selectbox("Select Restaurant to Edit", df['rest_id'].tolist())
        
        if edit_rest_id:
            rest_data = df[df['rest_id'] == edit_rest_id].iloc[0]
            
            with st.form("edit_restaurant_form"):
                edit_name = st.text_input("Name", value=rest_data['name'])
                edit_address = st.text_area("Address", value=rest_data['address'] or "")
                edit_rating = st.number_input("Rating", value=float(rest_data['rating'] or 4.0), 
                                            min_value=0.0, max_value=5.0, step=0.1)
                
                if st.form_submit_button("💾 Update Restaurant"):
                    execute("UPDATE restaurant SET name=%s, address=%s, rating=%s WHERE rest_id=%s",
                           (edit_name, edit_address, edit_rating, edit_rest_id))
                    st.success("Restaurant updated successfully")
                    time.sleep(2)
                    st.rerun()
    else:
        st.info("No restaurants found")

def show_admin_menuitems():
    st.title("🍽️ Menu Items Management")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("➕ Add Menu Item"):
            st.session_state.show_add_menuitem = True
    
    if st.session_state.get('show_add_menuitem', False):
        # Get restaurants for dropdown
        _, restaurants = fetch_all("SELECT rest_id, name FROM restaurant ORDER BY name")
        
        with st.form("add_menuitem_form"):
            name = st.text_input("Item Name")
            price = st.number_input("Price", min_value=0.0, step=0.5, value=10.0)
            quantity = st.number_input("Quantity", min_value=0, value=10)
            restaurant_name = st.selectbox("Restaurant", [r[1] for r in restaurants])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Item"):
                    if all([name, price, quantity, restaurant_name]):
                        # Find restaurant ID
                        rest_id = None
                        for r in restaurants:
                            if r[1] == restaurant_name:
                                rest_id = r[0]
                                break
                        
                        if rest_id:
                            execute("INSERT INTO menuitem (name, price, quantity, rest_id) VALUES (%s, %s, %s, %s)",
                                   (name, price, quantity, rest_id))
                            st.success("Menu item added successfully")
                            st.session_state.show_add_menuitem = False
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Invalid restaurant selected")
                    else:
                        st.error("All fields are required")
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_add_menuitem = False
                    st.rerun()
    
    cols, rows = fetch_all("""
        SELECT m.item_id, m.name, m.price, m.quantity, r.name as restaurant, r.rest_id
        FROM menuitem m 
        JOIN restaurant r ON m.rest_id = r.rest_id 
        ORDER BY m.item_id
    """)
    
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True)
        
        # FIXED: PROPER MENU ITEM EDITING
        st.subheader("Edit Menu Item")
        
        # Create a mapping of item_id to row data for easier access
        menu_items_dict = {row[0]: row for row in rows}
        item_ids = list(menu_items_dict.keys())
        
        if item_ids:
            selected_item_id = st.selectbox("Select Menu Item to Edit", item_ids, format_func=lambda x: f"{menu_items_dict[x][1]} - ₹{menu_items_dict[x][2]}")
            
            if selected_item_id:
                item_data = menu_items_dict[selected_item_id]
                _, restaurants = fetch_all("SELECT rest_id, name FROM restaurant ORDER BY name")
                restaurant_options = {r[1]: r[0] for r in restaurants}
                
                with st.form("edit_menuitem_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_name = st.text_input("Item Name", value=item_data[1])
                        edit_price = st.number_input("Price", min_value=0.0, step=0.5, value=float(item_data[2]))
                    
                    with col2:
                        edit_quantity = st.number_input("Quantity", min_value=0, value=int(item_data[3]))
                        # Find current restaurant name
                        current_rest_name = item_data[4]
                        edit_restaurant = st.selectbox("Restaurant", 
                                                     options=list(restaurant_options.keys()),
                                                     index=list(restaurant_options.keys()).index(current_rest_name) if current_rest_name in restaurant_options else 0)
                    
                    if st.form_submit_button("💾 Update Menu Item"):
                        rest_id = restaurant_options[edit_restaurant]
                        if execute("UPDATE menuitem SET name=%s, price=%s, quantity=%s, rest_id=%s WHERE item_id=%s",
                                 (edit_name, edit_price, edit_quantity, rest_id, selected_item_id)):
                            st.success("Menu item updated successfully")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Failed to update menu item")
        else:
            st.info("No menu items available for editing")
    else:
        st.info("No menu items found")

def show_admin_partners():
    st.title("🚚 Delivery Partners")
    
    if st.button("➕ Add Partner"):
        st.session_state.show_add_partner = True
    
    if st.session_state.get('show_add_partner', False):
        with st.form("add_partner_form"):
            name = st.text_input("Partner Name")
            phone = st.text_input("Phone Number")
            rating = st.number_input("Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
            
            if st.form_submit_button("💾 Save Partner"):
                if name and phone:
                    execute("INSERT INTO deliverypartner (name, phone, rating) VALUES (%s, %s, %s)",
                           (name, phone, rating))
                    st.success("Delivery partner added successfully")
                    st.session_state.show_add_partner = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Name and phone are required")
    
    cols, rows = fetch_all("SELECT partner_id, name, phone, rating FROM deliverypartner ORDER BY partner_id")
    
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No delivery partners found")

def show_admin_payments():
    st.title("💳 Payment Management")
    
    cols, rows = fetch_all("""
        SELECT p.pay_id, p.method, p.amount, p.status, u.name as customer
        FROM payment p 
        JOIN orders o ON p.pay_id = o.pay_id
        JOIN user u ON o.user_id = u.user_id
        ORDER BY p.pay_id DESC
    """)
    
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No payments found")

def show_admin_users():
    st.title("👥 User Management")
    
    cols, rows = fetch_all("SELECT user_id, name, email, phone, address FROM user ORDER BY user_id")
    
    if rows:
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No users found")

def show_admin_analytics():
    st.title("🔍 Analytics & Reports")
    
    analytics_options = [
        "📈 Top Spending Users",
        "🏆 Best Rated Restaurants", 
        "💰 Revenue by Payment Method",
        "🚚 Partner Performance",
        "📊 Monthly Sales Trend",
        "🍽️ Popular Menu Items"
    ]
    
    selected_analytic = st.selectbox("Select Report", analytics_options)
    
    if selected_analytic == "📈 Top Spending Users":
        cols, rows = fetch_all("""
            SELECT u.user_id, u.name, u.email, 
                   SUM(o.total_amt) as total_spent,
                   COUNT(o.order_id) as total_orders
            FROM user u 
            JOIN orders o ON u.user_id = o.user_id 
            WHERE o.status = 'Delivered'
            GROUP BY u.user_id, u.name, u.email 
            ORDER BY total_spent DESC 
            LIMIT 10
        """)
        if rows:
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data available")
    
    elif selected_analytic == "🏆 Best Rated Restaurants":
        cols, rows = fetch_all("""
            SELECT r.rest_id, r.name, r.rating, COUNT(DISTINCT o.order_id) as total_orders
            FROM restaurant r
            LEFT JOIN menuitem m ON r.rest_id = m.rest_id
            LEFT JOIN orderitem oi ON m.item_id = oi.item_id
            LEFT JOIN orders o ON oi.order_id = o.order_id
            WHERE r.rating IS NOT NULL
            GROUP BY r.rest_id, r.name, r.rating
            ORDER BY r.rating DESC
            LIMIT 10
        """)
        if rows:
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data available")
    
    elif selected_analytic == "💰 Revenue by Payment Method":
        cols, rows = fetch_all("""
            SELECT 
                p.method as payment_method,
                COUNT(DISTINCT o.order_id) as total_orders,
                SUM(o.total_amt) as total_revenue,
                AVG(o.total_amt) as avg_order_value
            FROM payment p
            JOIN orders o ON p.pay_id = o.pay_id
            WHERE o.status = 'Delivered'
            GROUP BY p.method
            ORDER BY total_revenue DESC
        """)
        if rows:
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data available")
    
    elif selected_analytic == "🚚 Partner Performance":
        cols, rows = fetch_all("""
            SELECT 
                dp.partner_id,
                dp.name as partner_name,
                dp.rating,
                COUNT(o.order_id) as total_deliveries,
                SUM(CASE WHEN o.status = 'Delivered' THEN 1 ELSE 0 END) as successful_deliveries,
                AVG(o.total_amt) as avg_order_value
            FROM deliverypartner dp
            LEFT JOIN orders o ON dp.partner_id = o.partner_id
            WHERE o.status IS NOT NULL
            GROUP BY dp.partner_id, dp.name, dp.rating
            ORDER BY successful_deliveries DESC, dp.rating DESC
        """)
        if rows:
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data available")
    
    elif selected_analytic == "📊 Monthly Sales Trend":
        cols, rows = fetch_all("""
            SELECT 
                DATE_FORMAT(o.order_date, '%Y-%m') as month,
                COUNT(o.order_id) as total_orders,
                SUM(o.total_amt) as total_revenue,
                AVG(o.total_amt) as avg_order_value
            FROM orders o
            WHERE o.order_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
            ORDER BY month DESC
        """)
        if rows:
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data available")
    
    elif selected_analytic == "🍽️ Popular Menu Items":
        cols, rows = fetch_all("""
            SELECT 
                m.item_id,
                m.name as item_name,
                r.name as restaurant,
                SUM(oi.quantity) as total_ordered,
                SUM(oi.quantity * oi.price) as total_revenue
            FROM menuitem m
            JOIN restaurant r ON m.rest_id = r.rest_id
            JOIN orderitem oi ON m.item_id = oi.item_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status = 'Delivered'
            GROUP BY m.item_id, m.name, r.name
            ORDER BY total_ordered DESC
            LIMIT 15
        """)
        if rows:
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data available")

# -------------------- USER PANEL --------------------
def show_user_panel():
    st.sidebar.markdown(f"### 👤 {st.session_state.user_data['name']}")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_data = {}
        st.session_state.cart = []
        st.session_state.page = "login"
        st.rerun()
    
    # FIXED: Proper cart count calculation
    cart_count = sum(item['quantity'] for item in st.session_state.cart)
    st.sidebar.markdown(f"🛒 Cart Items: **{cart_count}**")
    
    if cart_count > 0:
        total_amount = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
        st.sidebar.markdown(f"Total: **₹{total_amount:.2f}**")
        if st.sidebar.button("🛒 View Cart"):
            st.session_state.page = "user_cart"
            st.rerun()
    
    # User navigation
    user_pages = {
        "🏠 Restaurants": "user_restaurants",
        "📋 My Orders": "user_orders", 
        "👤 Profile": "user_profile"
    }
    
    selected_page = st.sidebar.radio("Navigation", list(user_pages.keys()))
    st.session_state.page = user_pages[selected_page]
    
    # Route to appropriate user page
    if st.session_state.page == "user_restaurants":
        show_user_restaurants()
    elif st.session_state.page == "user_orders":
        show_user_orders()
    elif st.session_state.page == "user_profile":
        show_user_profile()
    elif st.session_state.page == "user_cart":
        show_user_cart()

def show_user_restaurants():
    st.title("🍽️ Restaurants Near You")
    
    cols, rows = fetch_all("SELECT rest_id, name, address, rating FROM restaurant ORDER BY rating DESC")
    
    if not rows:
        st.info("No restaurants available")
        return
    
    # Display restaurants in columns
    cols_per_row = 3
    for i in range(0, len(rows), cols_per_row):
        restaurant_group = rows[i:i + cols_per_row]
        col_list = st.columns(cols_per_row)
        
        for j, restaurant in enumerate(restaurant_group):
            with col_list[j]:
                rest_id, name, address, rating = restaurant
                
                st.subheader(name)
                st.write(f"⭐ Rating: {rating or 'N/A'}")
                if address:
                    st.write(f"📍 {address}")
                
                if st.button("View Menu", key=f"menu_{rest_id}"):
                    st.session_state.current_restaurant = rest_id
                    st.session_state.page = "restaurant_menu"
                    st.rerun()

def show_restaurant_menu():
    rest_id = st.session_state.current_restaurant
    rest_data = fetch_one("SELECT name FROM restaurant WHERE rest_id=%s", (rest_id,))
    
    if not rest_data:
        st.error("Restaurant not found")
        return
    
    rest_name = rest_data[0]
    
    st.title(f"🍽️ {rest_name}")
    
    if st.button("← Back to Restaurants"):
        st.session_state.current_restaurant = None
        st.session_state.page = "user_restaurants"
        st.rerun()
    
    cols, rows = fetch_all("""
        SELECT item_id, name, price, quantity 
        FROM menuitem WHERE rest_id=%s AND quantity > 0
    """, (rest_id,))
    
    if not rows:
        st.info("No menu items available")
        return
    
    for item in rows:
        item_id, name, price, quantity = item
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.subheader(name)
            st.write(f"₹{price} | Available: {quantity}")
        
        with col2:
            # Check if item is already in cart
            current_qty = 0
            for cart_item in st.session_state.cart:
                if cart_item['item_id'] == item_id:
                    current_qty = cart_item['quantity']
                    break
            
            if current_qty > 0:
                st.write(f"In cart: {current_qty}")
        
        with col3:
            if st.button("➕ Add to Cart", key=f"add_{item_id}"):
                # Check if item already in cart
                item_found = False
                for cart_item in st.session_state.cart:
                    if cart_item['item_id'] == item_id:
                        if cart_item['quantity'] + 1 <= quantity:
                            cart_item['quantity'] += 1
                            item_found = True
                        else:
                            st.error(f"Cannot add more {name}. Only {quantity} available.")
                        break
                
                if not item_found:
                    if quantity >= 1:
                        st.session_state.cart.append({
                            'item_id': item_id,
                            'name': name,
                            'price': float(price),
                            'quantity': 1,
                            'available_quantity': quantity
                        })
                    else:
                        st.error(f"{name} is out of stock")
                
                st.success(f"Added {name} to cart")
                time.sleep(1)
                st.rerun()
        
        st.markdown("---")

def show_user_cart():
    st.title("🛒 Your Cart")
    
    if not st.session_state.cart:
        st.info("Your cart is empty")
        if st.button("Browse Restaurants"):
            st.session_state.page = "user_restaurants"
            st.rerun()
        return
    
    total_amount = 0
    
    for i, item in enumerate(st.session_state.cart):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{item['name']}**")
            st.write(f"₹{item['price']} each")
        
        with col2:
            st.write(f"Qty: {item['quantity']}")
        
        with col3:
            item_total = item['price'] * item['quantity']
            st.write(f"**₹{item_total:.2f}**")
            total_amount += item_total
        
        with col4:
            col4a, col4b, col4c = st.columns(3)
            with col4a:
                if st.button("−", key=f"dec_{i}"):
                    if item['quantity'] > 1:
                        item['quantity'] -= 1
                    else:
                        st.session_state.cart.pop(i)
                    st.rerun()
            with col4b:
                if st.button("+", key=f"inc_{i}"):
                    if item['quantity'] + 1 <= item['available_quantity']:
                        item['quantity'] += 1
                        st.rerun()
                    else:
                        st.error(f"Cannot add more {item['name']}")
            with col4c:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
    
    st.markdown("---")
    st.subheader(f"Total: ₹{total_amount:.2f}")
    
    if st.button("💳 Proceed to Checkout"):
        st.session_state.page = "checkout"
        st.rerun()

def show_checkout():
    st.title("💳 Checkout")
    
    if not st.session_state.cart:
        st.error("Cart is empty")
        if st.button("Back to Restaurants"):
            st.session_state.page = "user_restaurants"
            st.rerun()
        return
    
    total_amount = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
    
    st.write(f"**Total Amount: ₹{total_amount:.2f}**")
    
    with st.form("checkout_form"):
        payment_method = st.selectbox("Payment Method", ["UPI", "Card", "COD"])
        
        if st.form_submit_button("✅ Place Order"):
            conn = get_db()
            if not conn:
                st.error("Database connection failed")
                return
            
            cur = conn.cursor()
            try:
                # Start transaction
                conn.start_transaction()
                
                # Create payment
                cur.execute("INSERT INTO payment (method, amount, status) VALUES (%s, %s, %s)",
                           (payment_method, total_amount, 'Pending'))
                pay_id = cur.lastrowid
                
                # Get a delivery partner
                cur.execute("SELECT partner_id FROM deliverypartner ORDER BY RAND() LIMIT 1")
                partner_result = cur.fetchone()
                partner_id = partner_result[0] if partner_result else None
                
                # Create order
                cur.execute("""
                    INSERT INTO orders (user_id, total_amt, status, pay_id, partner_id, order_date)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (st.session_state.user_data['user_id'], total_amount, 'Placed', pay_id, partner_id))
                order_id = cur.lastrowid
                
                # Add order items and update quantities
                for item in st.session_state.cart:
                    cur.execute("""
                        INSERT INTO orderitem (order_id, item_id, quantity, price)
                        VALUES (%s, %s, %s, %s)
                    """, (order_id, item['item_id'], item['quantity'], item['price']))
                    
                    cur.execute("""
                        UPDATE menuitem 
                        SET quantity = quantity - %s 
                        WHERE item_id = %s AND quantity >= %s
                    """, (item['quantity'], item['item_id'], item['quantity']))
                    
                    if cur.rowcount == 0:
                        raise Exception(f"Not enough quantity available for {item['name']}")
                
                # Commit transaction
                conn.commit()
                
                payment_note = "Payment will be collected when your order is delivered." if payment_method == 'COD' else "Payment is pending and will be processed upon delivery."
                st.success(f"Order placed successfully! Order ID: {order_id}\n{payment_note}")
                
                # Clear cart
                st.session_state.cart = []
                time.sleep(3)
                st.session_state.page = "user_orders"
                st.rerun()
                
            except Exception as e:
                conn.rollback()
                st.error(f"Failed to place order: {str(e)}")
            finally:
                cur.close()
                conn.close()

def show_user_orders():
    st.title("📋 My Orders")
    
    cols, rows = fetch_all("""
        SELECT o.order_id, o.order_date, o.total_amt, o.status, 
               dp.name as delivery_partner, p.status as payment_status, p.method as payment_method
        FROM orders o 
        LEFT JOIN deliverypartner dp ON o.partner_id = dp.partner_id
        LEFT JOIN payment p ON o.pay_id = p.pay_id
        WHERE o.user_id=%s 
        ORDER BY o.order_date DESC
    """, (st.session_state.user_data['user_id'],))
    
    if not rows:
        st.info("No orders found")
        return
    
    df = pd.DataFrame(rows, columns=cols)
    st.dataframe(df, use_container_width=True)

def show_user_profile():
    st.title("👤 My Profile")
    
    user = st.session_state.user_data
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Phone:** {user['phone']}")
        st.write(f"**Address:** {user['address'] or 'Not set'}")
    
    with col2:
        st.subheader("Order Statistics")
        # FIXED: Only count paid/delivered orders for total spent
        total_orders = fetch_one("SELECT COUNT(*) FROM orders WHERE user_id=%s", 
                                (user['user_id'],))[0] or 0
        
        # Calculate total spent only from delivered orders with paid payments
        total_spent_row = fetch_one("""
            SELECT COALESCE(SUM(o.total_amt), 0) 
            FROM orders o 
            JOIN payment p ON o.pay_id = p.pay_id
            WHERE o.user_id=%s AND o.status='Delivered' AND p.status='Paid'
        """, (user['user_id'],))
        
        total_spent = total_spent_row[0] if total_spent_row else 0
        
        st.metric("Total Orders", total_orders)
        st.metric("Total Spent", f"₹{total_spent:.2f}")

# -------------------- MAIN APPLICATION --------------------
def main():
    # Initialize session state
    init_session_state()
    
    # Apply custom styles
    apply_custom_styles()
    
    # Create missing tables
    if not st.session_state.get('tables_created', False):
        if create_missing_tables():
            st.session_state.tables_created = True
    
    # Route to appropriate screen based on login status and role
    if not st.session_state.logged_in:
        show_login_screen()
    else:
        if st.session_state.user_role == "admin":
            show_admin_panel()
        elif st.session_state.user_role == "partner":
            show_partner_panel()
        elif st.session_state.user_role == "user":
            if st.session_state.page == "restaurant_menu":
                show_restaurant_menu()
            elif st.session_state.page == "user_cart":
                show_user_cart()
            elif st.session_state.page == "checkout":
                show_checkout()
            else:
                show_user_panel()

if __name__ == "__main__":

    main()

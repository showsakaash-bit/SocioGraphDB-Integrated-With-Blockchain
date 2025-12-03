import streamlit as st
import extra_streamlit_components as stx
import time
import os
from datetime import datetime, timedelta

# Import modules
import config
import database
import crud
import components
import blockchain
from utils import get_image_base64, human_time

# --- INITIALIZATION ---
database.init_db()
st.set_page_config(page_title="Sketchy Twitter", layout="wide", page_icon="📝")
components.apply_theme()

# --- COOKIE MANAGER ---
cookie_manager = stx.CookieManager(key="auth_mgr_production_v2")
time.sleep(0.5) # Allow cookie mount
cookies = cookie_manager.get_all()

if cookies is None:
    st.spinner("Loading Sketchy UI...")
    st.stop()

cookie_user_id = cookies.get("current_user_id")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user and cookie_user_id:
    try:
        user_data = crud.get_user_by_id(int(cookie_user_id))
        if user_data:
            st.session_state.user = user_data
            if "auth_mode" not in st.session_state: st.session_state.auth_mode = "home"
        else:
            cookie_manager.delete("current_user_id")
            st.warning("Session expired. Please log in again.")
    except Exception as e:
        cookie_manager.delete("current_user_id")

# ==========================================
# AUTH SCREEN
# ==========================================
if not st.session_state.user:
    if "auth_mode" not in st.session_state: st.session_state.auth_mode = "login"
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; transform: rotate(-3deg);'>📝 SKETCHY TWITTER</h1>", unsafe_allow_html=True)
        
        with st.container(border=True):
            if st.session_state.auth_mode == "login":
                with st.form("login_form"):
                    st.write("### Login")
                    username = st.text_input("Username", placeholder="@username")
                    password = st.text_input("Password", type="password")
                    st.write("") 
                    submitted = st.form_submit_button("ENTER", type="primary", use_container_width=True)
                    if submitted:
                        row = crud.authenticate(username.strip(), password)
                        if row:
                            st.session_state.user = row
                            cookie_manager.set("current_user_id", row['id'], expires_at=datetime.now() + timedelta(days=7))
                            st.toast("Welcome back!", icon="👋")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                if st.button("Create an account", use_container_width=True):
                    st.session_state.auth_mode = "signup"
                    st.rerun()
            else:
                st.info("ℹ️ A SUI Blockchain Wallet will be generated for you.")
                with st.form("signup_form"):
                    st.write("### New Account")
                    su_user = st.text_input("Choose username")
                    su_name = st.text_input("Display name")
                    su_pass = st.text_input("Password", type="password")
                    su_bio = st.text_area("Bio (optional)")
                    su_pic = st.file_uploader("Profile Picture", type=["png","jpg","jpeg"])
                    st.write("")
                    ok = st.form_submit_button("CREATE & GENERATE WALLET", type="primary", use_container_width=True)
                    if ok:
                        if not su_user or not su_name or not su_pass: st.error("Please fill required fields")
                        else:
                            pic_path = None
                            if su_pic:
                                fname = f"{su_user}_{int(time.time()*1000)}_{su_pic.name}"
                                path = os.path.join(config.PROFILE_PIC_DIR, fname)
                                with open(path, "wb") as f: f.write(su_pic.getbuffer())
                                pic_path = path
                            with st.spinner("Generating Keys on Blockchain..."):
                                new_id = crud.create_user(su_user.strip(), su_name.strip(), su_pass, su_bio.strip(), pic_path)
                            if new_id:
                                st.success("Account created! Please log in.")
                                time.sleep(1.5)
                                st.session_state.auth_mode = "login"
                                st.rerun()
                            else: st.error("Username already exists")
                if st.button("Back to Login", use_container_width=True):
                    st.session_state.auth_mode = "login"
                    st.rerun()
    st.stop()

# ==========================================
# MAIN APP - LOGGED IN
# ==========================================
if "view" not in st.session_state: st.session_state.view = "home"

with st.sidebar:
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px; font-size: 60px; font-family: sans-serif;'>𝕏</h1>", unsafe_allow_html=True)
    if st.button("   Home", use_container_width=True): st.session_state.view = "home"; st.rerun()
    if st.button("   Explore", use_container_width=True): st.session_state.view = "explore"; st.rerun()
    if st.button("   Notifications", use_container_width=True): st.session_state.view = "notifications"; st.rerun()
    if st.button("   Messages", use_container_width=True): st.session_state.view = "messages"; st.rerun()
    if st.button("   Bookmarks", use_container_width=True): st.session_state.view = "bookmarks"; st.rerun()
    if st.button("   Wallet", use_container_width=True): st.session_state.view = "wallet"; st.rerun()
    if st.button("   Profile", use_container_width=True): st.session_state.view = f"profile:{st.session_state.user['username']}"; st.rerun()
    st.write("") 
    if st.button("WRITE POST", type="primary", use_container_width=True): st.session_state.view = "create_post"; st.rerun()
    st.markdown("---")
    
    usr = st.session_state.user
    if usr:
        usr = crud.get_user_by_id(usr['id']) 
        st.session_state.user = usr
        with st.container():
            col_p1, col_p2 = st.columns([1, 3])
            with col_p1:
                img_src = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                if usr.get('profile_pic_path') and os.path.exists(usr['profile_pic_path']):
                    b64 = get_image_base64(usr['profile_pic_path'])
                    if b64: img_src = f"data:image/png;base64,{b64}"
                st.markdown(f"""<div style="width: 50px; height: 50px; border-radius: 50%; overflow: hidden;"><img src="{img_src}" style="width: 100%; height: 100%; object-fit: cover; border: none !important;"></div>""", unsafe_allow_html=True)
            with col_p2:
                st.markdown(f"<div style='line-height: 1.1; margin-top: 2px;'><b>{usr.get('display_name')}</b><br><span style='color: #666; font-size: 0.9em;'>@{usr.get('username')}</span></div>", unsafe_allow_html=True)

    addr = usr.get("wallet_address", "No Wallet")
    short_addr = f"{addr[:5]}...{addr[-5:]}"
    st.markdown(f"<div style='background-color: #fff; color: #000; padding: 8px; border: 2px solid black; box-shadow: 2px 2px 0px black; font-family: monospace; text-align: center; font-size: 0.9em; margin-top: 5px;'>{short_addr}</div>", unsafe_allow_html=True)
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.auth_mode = "login"
        st.session_state.view = "home"
        cookie_manager.delete("current_user_id")
        time.sleep(1) 
        st.rerun()

# --- VIEW HANDLERS ---
if st.session_state.view == "create_post":
    st.header("New Post")
    with st.container(border=True):
        with st.form("post_form"):
            text = st.text_area("What's on your mind?", max_chars=280)
            img = st.file_uploader("Attach Image", type=["png","jpg","jpeg","gif"])
            ok = st.form_submit_button("PUBLISH", type="primary")
            if ok:
                img_path = None
                if img:
                    fname = f"{int(time.time()*1000)}_{img.name}"
                    path = os.path.join(config.POST_IMAGE_DIR, fname)
                    with open(path, "wb") as f: f.write(img.getbuffer())
                    img_path = path
                crud.create_post(st.session_state.user['id'], text, img_path)
                st.success("Posted!")
                st.session_state.view = "home"
                st.rerun()

elif st.session_state.view.startswith("reply:"):
    _, pid = st.session_state.view.split(":")
    pid = int(pid)
    p = crud.get_post(pid)
    if not p: st.error("Post not found")
    else:
        components.render_post(p, "reply_view")
        with st.form("reply_form"):
            txt = st.text_area("Write a reply...", max_chars=280)
            ok = st.form_submit_button("REPLY", type="primary")
            if ok:
                crud.reply_to_post(st.session_state.user['id'], pid, txt)
                st.success("Replied!")
                st.session_state.view = "home"
                st.rerun()

elif st.session_state.view == "edit_profile":
    st.header("Edit Profile")
    curr = st.session_state.user
    with st.container(border=True):
        with st.form("edit_profile_form"):
            new_name = st.text_input("Display Name", value=curr['display_name'])
            new_bio = st.text_area("Bio", value=curr['bio'] if curr['bio'] else "", max_chars=160)
            st.write("Profile Picture")
            col_preview, col_upload = st.columns([1, 3])
            with col_preview:
                if curr.get('profile_pic_path') and os.path.exists(curr['profile_pic_path']): st.image(curr['profile_pic_path'], width=80)
                else: st.markdown("👤")
            with col_upload: new_pic = st.file_uploader("Upload new image", type=["png", "jpg", "jpeg"])
            st.write("")
            submitted = st.form_submit_button("SAVE CHANGES", type="primary")
            if submitted:
                if not new_name.strip(): st.error("Display Name cannot be empty")
                else:
                    final_path = None
                    if new_pic:
                        fname = f"updated_{curr['id']}_{int(time.time())}_{new_pic.name}"
                        path = os.path.join(config.PROFILE_PIC_DIR, fname)
                        with open(path, "wb") as f: f.write(new_pic.getbuffer())
                        final_path = path
                    updated_user = crud.update_user_details(curr['id'], new_name.strip(), new_bio.strip(), final_path)
                    st.session_state.user = updated_user
                    st.success("Profile updated successfully!")
                    time.sleep(1)
                    st.session_state.view = f"profile:{curr['username']}"
                    st.rerun()
    if st.button("Cancel"):
        st.session_state.view = f"profile:{curr['username']}"
        st.rerun()

elif st.session_state.view == "home":
    st.header("TODAY")
    posts = crud.get_feed(st.session_state.user['id'], limit=100)
    if not posts: st.info("Timeline empty. Go to Explore!")
    for p in posts: components.render_post(p, "home")

elif st.session_state.view == "explore":
    st.header("EXPLORE")
    term = st.text_input("Search...", placeholder="Find users or posts...")
    if term:
        st.subheader("Users")
        for u in crud.search_users(term):
            st.write(f"@{u['username']} — {u['display_name']}")
            if st.button("View", key=f"viewu:{u['id']}"):
                st.session_state.view = f"profile:{u['username']}"; st.rerun()
        st.subheader("Posts")
        for p in crud.search_posts(term): components.render_post(p, "explore")
    else:
        st.subheader("Recent Activity")
        c = database.get_conn().cursor()
        c.execute("SELECT p.*, u.username, u.display_name, u.profile_pic_path FROM posts p JOIN users u ON p.user_id = u.id ORDER BY p.created_at DESC LIMIT 100")
        for p in c.fetchall(): components.render_post(p, "explore")

elif st.session_state.view == "bookmarks":
    st.header("SAVED")
    bookmarks = crud.get_bookmarks_for_user(st.session_state.user['id'])
    if not bookmarks: st.info("No bookmarks yet.")
    for p in bookmarks: components.render_post(p, "bookmarks")

elif st.session_state.view == "notifications":
    st.header("ALERTS")
    with st.container(border=True):
        notes = crud.get_notifications(st.session_state.user['id'])
        if not notes: st.info("No notifications.")
        for n in notes: st.write(f"**{human_time(n['created_at'])}** — {n['text']}")
        crud.mark_notifications_seen(st.session_state.user['id'])

elif st.session_state.view == "messages":
    st.header("CHAT")
    user = st.session_state.user
    rows = database.get_conn().cursor().execute("SELECT username FROM users WHERE id != ?", (user['id'],)).fetchall()
    options = [r['username'] for r in rows]
    other = st.selectbox("Select User", options=options)
    if other:
        other_row = crud.get_user_by_username(other)
        st.subheader(f"Chat with @{other_row['username']}")
        components.render_realtime_chat(user['id'], other_row['id'], user['username'], other_row['username'])
        with st.form("send_msg", clear_on_submit=True):
            txt = st.text_area("Message")
            ok = st.form_submit_button("SEND", type="primary")
            if ok and txt.strip():
                crud.send_message(user['id'], other_row['id'], txt)
                st.toast("Message sent!")

elif st.session_state.view == "wallet":
    curr = st.session_state.user
    with st.spinner("Syncing with Blockchain..."):
        balance = blockchain.get_sui_balance(curr['wallet_address'])
        sui_price, price_change_pct = blockchain.get_sui_market_data()
    holdings_value = balance * sui_price
    change_color = "#00ba7c" if price_change_pct >= 0 else "#f91880"
    change_sign = "+" if price_change_pct >= 0 else ""

    st.header("WALLET")
    st.markdown(f"""
    <div style="background-color: #ffffff; border: 3px solid black; box-shadow: 6px 6px 0px black; padding: 20px; margin-bottom: 30px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <img src="https://s2.coinmarketcap.com/static/img/coins/64x64/20947.png" width="48" height="48" style="border-radius: 50%;">
                <div>
                    <div style="font-weight: 800; font-size: 19px; color: black; display: flex; align-items: center; gap: 4px;">SUI COIN</div>
                    <div style="font-size: 15px; color: #555; margin-top: 2px;">${sui_price:,.2f} <span style="color: {change_color}; font-weight: 900;">{change_sign}{price_change_pct:.2f}%</span></div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: 800; font-size: 24px; color: black;">${holdings_value:,.2f}</div>
                <div style="font-size: 15px; color: #555; margin-top: 2px;">{balance:.4f} SUI</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Transfer Funds")
    with st.container(border=True):
        with st.form("withdraw_form"):
            dest_addr = st.text_input("Destination Address (0x...)")
            amount = st.number_input("Amount to Send", min_value=0.0, max_value=balance, step=0.1)
            if st.form_submit_button("SEND TRANSACTION", type="primary", use_container_width=True):
                if amount <= 0: st.error("Amount must be positive.")
                elif not dest_addr.startswith("0x"): st.error("Invalid SUI address.")
                else:
                    with st.spinner("Processing on Blockchain..."):
                        success, msg = blockchain.send_sui_payment(curr['private_key'], dest_addr, amount)
                        if success:
                            st.success(f"Transaction Sent! Digest: {msg}")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else: st.error(f"Failed: {msg}")
    st.divider()
    with st.expander("🔐 View Keys"):
        st.warning("These are your keys. Never share them.")
        st.text_input("Private Key", curr['private_key'], type="password", disabled=True)
        st.text_area("Mnemonic Phrase", curr['mnemonic'], disabled=True)

elif st.session_state.view.startswith("profile:"):
    _, uname = st.session_state.view.split(":")
    u_row = crud.get_user_by_username(uname)
    if not u_row: st.error("User not found")
    else:
        u = dict(u_row)
        user_id = u['id']
        current_user_id = st.session_state.user['id']
        is_me = (current_user_id == user_id)
        
        with st.container(border=True):
            header_cols = st.columns([1.2, 4, 1.2])
            with header_cols[0]:
                img_src = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                if u.get('profile_pic_path') and os.path.exists(u['profile_pic_path']):
                    b64 = get_image_base64(u['profile_pic_path'])
                    if b64: img_src = f"data:image/png;base64,{b64}"
                st.markdown(f"""
                    <div style="width: 110px; height: 110px; border-radius: 50%; overflow: hidden; display: flex; justify-content: center; align-items: center; box-shadow: 0px 0px 0px 3px white; margin-bottom: 10px;">
                        <img src="{img_src}" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                """, unsafe_allow_html=True)

            with header_cols[1]:
                st.markdown(f"""<div style="line-height: 1.2;"><span style="font-size: 1.8rem; font-weight: 900; text-transform: uppercase;">{u['display_name']}</span><br><span style="color: #555; font-size: 1.1rem;">@{u['username']}</span></div>""", unsafe_allow_html=True)
                if u.get('bio'): st.markdown(f"<div style='margin-top: 8px; font-size: 1rem;'>{u['bio']}</div>", unsafe_allow_html=True)
                st.markdown(f"""<div style="color: #666; font-size: 0.9rem; margin-top: 8px; margin-bottom: 10px;">📅 Joined {human_time(u.get('created_at')).split(' ')[0]}</div>""", unsafe_allow_html=True)
                
                stat_row = st.columns([1.2, 1.2, 3])
                with stat_row[0]:
                    if st.button(f"{crud.get_following_count(user_id)} Following", key=f"ing_{user_id}"): 
                        st.session_state.view = f"following_list:{user_id}:{uname}"
                        st.rerun()
                with stat_row[1]:
                    if st.button(f"{crud.get_follower_count(user_id)} Followers", key=f"ers_{user_id}"): 
                        st.session_state.view = f"followers_list:{user_id}:{uname}"
                        st.rerun()

                # "Followed By" Logic (Mutuals)
                if not is_me:
                    mutuals = crud.get_common_followers(current_user_id, user_id)
                    if mutuals:
                        avatar_html = ""
                        for m in mutuals:
                            m_src = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                            if m['profile_pic_path'] and os.path.exists(m['profile_pic_path']):
                                b64 = get_image_base64(m['profile_pic_path'])
                                if b64: m_src = f"data:image/png;base64,{b64}"
                            avatar_html += f"""<img src="{m_src}" style="width: 24px; height: 24px; border-radius: 50%; border: 1px solid white; margin-right: -8px;">"""
                        st.write("") 
                        if len(mutuals) == 1:
                            c_av, c_txt, c_btn, c_rest = st.columns([0.5, 1.3, 1.5, 4])
                            with c_av: st.markdown(f"<div style='display:flex;'>{avatar_html}</div>", unsafe_allow_html=True)
                            with c_txt: st.markdown("<div style='font-size: 1.1rem; color: #555; padding-top: 5px;'>Followed by</div>", unsafe_allow_html=True)
                            with c_btn:
                                if st.button(f"@{mutuals[0]['username']}", key=f"mbtn_{mutuals[0]['username']}"):
                                    st.session_state.view = f"profile:{mutuals[0]['username']}"; st.rerun()
                        elif len(mutuals) >= 2:
                            c_av, c_txt, c_btn1, c_and, c_btn2, c_rest = st.columns([0.6, 1.3, 1.5, 0.4, 1.5, 3])
                            with c_av: st.markdown(f"<div style='display:flex;'>{avatar_html}</div>", unsafe_allow_html=True)
                            with c_txt: st.markdown("<div style='font-size: 1.1rem; color: #555; padding-top: 5px;'>Followed by</div>", unsafe_allow_html=True)
                            with c_btn1:
                                if st.button(f"@{mutuals[0]['username']}", key=f"mbtn_{mutuals[0]['username']}"):
                                    st.session_state.view = f"profile:{mutuals[0]['username']}"; st.rerun()
                            with c_and: st.markdown("<div style='font-size: 1.1rem; color: #555; padding-top: 5px;'>&</div>", unsafe_allow_html=True)
                            with c_btn2:
                                if st.button(f"@{mutuals[1]['username']}", key=f"mbtn_{mutuals[1]['username']}"):
                                    st.session_state.view = f"profile:{mutuals[1]['username']}"; st.rerun()

            with header_cols[2]:
                if not is_me:
                    if crud.is_following(st.session_state.user['id'], user_id):
                        if st.button("Unfollow", key=f"unfol_{user_id}", use_container_width=True): 
                            crud.unfollow_user(st.session_state.user['id'], user_id)
                            st.rerun()
                    else:
                        if st.button("Follow", type="primary", key=f"fol_{user_id}", use_container_width=True): 
                            crud.follow_user(st.session_state.user['id'], user_id)
                            st.rerun()
                    st.write("")
                    with st.popover("💸 Tip SUI", use_container_width=True):
                        tip_val = st.number_input("Amount", 0.1, step=0.1, key=f"tip_{user_id}")
                        if st.button("Send Tip", key=f"pay_{user_id}"):
                            with st.spinner("..."):
                                s, m = blockchain.send_sui_payment(st.session_state.user['private_key'], u['wallet_address'], tip_val)
                                if s: st.success("Sent!"); crud.create_notification(user_id, f"Tip from @{st.session_state.user['username']}")
                                else: st.error(m)
                else:
                    if st.button("Edit Profile", key="edit_profile_btn", use_container_width=True): 
                        st.session_state.view = "edit_profile"
                        st.rerun()

        st.markdown("---")
        tab_posts, tab_replies, tab_likes = st.tabs(["POSTS", "REPLIES", "LIKES"])
        with tab_posts:
            user_posts = crud.get_posts_for_user(user_id, limit=100)
            if not user_posts: st.info("No posts yet.")
            for p in user_posts: components.render_post(p, "prof_posts")
        with tab_replies:
            replies_list = crud.get_replies_for_user(user_id)
            if not replies_list: st.info("No replies yet.")
            for r in replies_list:
                with st.container(border=True):
                    col_icon, col_txt = st.columns([1, 20])
                    with col_icon: st.write("💬")
                    with col_txt:
                        st.caption(f"Replying to @{r['orig_username']}")
                        st.markdown(f"**{r['reply_text']}**")
                        with st.expander("Original Post Context"):
                            fake_post_row = { "id": r["orig_post_id"], "username": r["orig_username"], "display_name": r["orig_display"], "profile_pic_path": r["orig_pic"], "text": r["orig_text"], "image_path": r["orig_image"], "created_at": r["orig_created"] }
                            components.render_post(fake_post_row, key_prefix=f"reply_ctx_{r['reply_id']}")
        with tab_likes:
             liked_posts = crud.get_liked_posts_for_user(user_id)
             if not liked_posts: st.info("No liked posts yet.")
             for p in liked_posts: components.render_post(p, "prof_likes")

elif st.session_state.view.startswith("following_list:"):
    _, user_id_str, uname = st.session_state.view.split(":")
    components.render_user_list(f"@{uname} IS FOLLOWING", crud.get_following_list(int(user_id_str)))
    if st.button("← Back"): st.session_state.view = f"profile:{uname}"; st.rerun()

elif st.session_state.view.startswith("followers_list:"):
    _, user_id_str, uname = st.session_state.view.split(":")
    components.render_user_list(f"FOLLOWERS OF @{uname}", crud.get_followers_list(int(user_id_str)))
    if st.button("← Back"): st.session_state.view = f"profile:{uname}"; st.rerun()

else: st.write("Unknown view")
st.markdown("---")

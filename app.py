import streamlit as st
import requests
from wallet import Wallet
from transaction import Transaction

# ---------------- CONFIG ----------------
SERVER_URL = "https://he-future-proof-digital-wallet.onrender.com"

st.set_page_config(page_title="Quantum-Resistant Blockchain Wallet", layout="centered")

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "wallet" not in st.session_state:
    st.session_state.wallet = None

# ---------------- AUTH UI ----------------
def auth_page():
    st.title("🔐 Quantum-Resistant Wallet Platform")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # -------- LOGIN --------
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            response = requests.post(
                f"{SERVER_URL}/login",
                json={"username": username, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                st.session_state.logged_in = True
                st.session_state.user_id = data["user_id"]
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username or password")

    # -------- REGISTER --------
    with tab2:
        st.subheader("Register")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Register"):
            response = requests.post(
                f"{SERVER_URL}/register",
                json={"username": new_user, "password": new_pass}
            )

            if response.status_code == 201:
                st.success("Registration successful. Please login.")
            else:
                st.error("Username already exists")


# ---------------- DASHBOARD ----------------
def dashboard():
    st.sidebar.title("Menu")

    choice = st.sidebar.radio(
        "Select an option",
        [
            "Create Wallet",
            "Show Wallet Address",
            "Create Transaction",
            "Mine Block",
            "View Blockchain",
            "Verify Blockchain",
            "Logout"
        ]
    )

    st.title("📊 Wallet Dashboard")

    # -------- CREATE WALLET --------
    if choice == "Create Wallet":
        if st.button("Create Wallet"):
            st.session_state.wallet = Wallet()
            st.success("Wallet created successfully")

    # -------- SHOW ADDRESS --------
    elif choice == "Show Wallet Address":
        if st.session_state.wallet:
            st.code(st.session_state.wallet.get_address())
        else:
            st.warning("Create a wallet first")

    # -------- CREATE TRANSACTION --------
    elif choice == "Create Transaction":
        if not st.session_state.wallet:
            st.warning("Create a wallet first")
        else:
            receiver = st.text_input("Receiver Address")
            amount = st.number_input("Amount", min_value=1.0, step=1.0)

            if st.button("Send Transaction"):
                temp_tx = Transaction(
                    sender=st.session_state.wallet.get_address(),
                    receiver=receiver,
                    amount=amount,
                    signature=None,
                    public_key=None
                )

                tx_hash = temp_tx.calculate_hash()
                signature = st.session_state.wallet.sign(tx_hash)

                payload = {
                    "sender": st.session_state.wallet.get_address(),
                    "receiver": receiver,
                    "amount": amount,
                    "timestamp": temp_tx.timestamp,
                    "signature": [s.hex() for s in signature],
                    "public_key": [
                        (pk0.hex(), pk1.hex())
                        for pk0, pk1 in st.session_state.wallet.public_key
                    ]
                }

                r = requests.post(f"{SERVER_URL}/add_transaction", json=payload)

                if r.status_code == 200:
                    st.success("Transaction sent successfully")
                else:
                    st.error("Transaction failed")

    # -------- MINE BLOCK --------
    elif choice == "Mine Block":
        if st.button("Mine Block"):
            r = requests.post(f"{SERVER_URL}/mine")
            if r.status_code == 200:
                st.success("Block mined successfully")
            else:
                st.error("No transactions to mine")

    # -------- VIEW BLOCKCHAIN --------
    elif choice == "View Blockchain":
        r = requests.get(f"{SERVER_URL}/chain")
        for block in r.json():
            with st.expander(f"Block {block['index']}"):
                st.write("Hash:", block["hash"])
                st.write("Previous Hash:", block["previous_hash"])
                st.write("Transactions:", block["transactions"])

    # -------- VERIFY --------
    elif choice == "Verify Blockchain":
        r = requests.get(f"{SERVER_URL}/verify")
        if r.json()["valid"]:
            st.success("Blockchain is valid ✔")
        else:
            st.error("Blockchain invalid ❌")

    # -------- LOGOUT --------
    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.wallet = None
        st.rerun()


# ---------------- MAIN ----------------
if not st.session_state.logged_in:
    auth_page()
else:
    dashboard()
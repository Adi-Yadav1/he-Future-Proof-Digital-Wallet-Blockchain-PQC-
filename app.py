import streamlit as st
from wallet import Wallet
from transaction import Transaction
from blockchain import Blockchain
from ledger import Ledger

# ---------------- INITIAL SETUP ----------------
st.set_page_config(page_title="Quantum-Resistant Blockchain Wallet", layout="centered")

if "blockchain" not in st.session_state:
    ledger = Ledger()
    blockchain = Blockchain()
    loaded_chain = ledger.load_blockchain()
    if loaded_chain:
        blockchain.chain = loaded_chain
    st.session_state.blockchain = blockchain
    st.session_state.ledger = ledger

if "wallet" not in st.session_state:
    st.session_state.wallet = None

if "tx_pool" not in st.session_state:
    st.session_state.tx_pool = []

# ---------------- UI ----------------
st.title("🔐 Quantum-Resistant Blockchain Wallet")
st.caption("Post-Quantum Cryptography using Lamport Signatures")

st.sidebar.title("Menu")
choice = st.sidebar.radio(
    "Select an action",
    [
        "Create Wallet",
        "Show Wallet Address",
        "Create Transaction",
        "Mine Block",
        "View Blockchain",
        "Verify Blockchain",
    ],
)

# ---------------- CREATE WALLET ----------------
if choice == "Create Wallet":
    if st.button("Create New Wallet"):
        st.session_state.wallet = Wallet()
        st.success("Wallet created successfully!")

# ---------------- SHOW ADDRESS ----------------
elif choice == "Show Wallet Address":
    if st.session_state.wallet:
        st.code(st.session_state.wallet.get_address())
    else:
        st.warning("Please create a wallet first.")

# ---------------- CREATE TRANSACTION ----------------
elif choice == "Create Transaction":
    if not st.session_state.wallet:
        st.warning("Please create a wallet first.")
    else:
        receiver = st.text_input("Receiver Address")
        amount = st.number_input("Amount", min_value=1.0, step=1.0)

        if st.button("Sign Transaction"):
            temp_tx = Transaction(
                sender=st.session_state.wallet.get_address(),
                receiver=receiver,
                amount=amount,
                signature=None,
                public_key=None
            )

            tx_hash = temp_tx.calculate_hash()
            signature = st.session_state.wallet.sign(tx_hash)

            tx = Transaction(
                sender=st.session_state.wallet.get_address(),
                receiver=receiver,
                amount=amount,
                signature=signature,
                public_key=st.session_state.wallet.public_key,
                timestamp=temp_tx.timestamp
            )

            st.session_state.tx_pool.append(tx)
            st.success("Transaction signed and added to pool.")

# ---------------- MINE BLOCK ----------------
elif choice == "Mine Block":
    if not st.session_state.wallet:
        st.warning("Please create a wallet first.")
    elif not st.session_state.tx_pool:
        st.warning("No transactions to mine.")
    else:
        if st.button("Mine Block"):
            st.session_state.blockchain.add_block(
                st.session_state.tx_pool,
                st.session_state.wallet
            )
            st.session_state.ledger.save_blockchain(st.session_state.blockchain)
            st.session_state.tx_pool = []
            st.success("Block mined and saved to blockchain.")

# ---------------- VIEW BLOCKCHAIN ----------------
elif choice == "View Blockchain":
    for block in st.session_state.blockchain.chain:
        with st.expander(f"Block {block.index}"):
            st.write("Timestamp:", block.timestamp)
            st.write("Previous Hash:", block.previous_hash)
            st.write("Block Hash:", block.hash)
            st.write("Transactions:", len(block.transactions))

# ---------------- VERIFY BLOCKCHAIN ----------------
elif choice == "Verify Blockchain":
    if st.session_state.blockchain.is_chain_valid():
        st.success("Blockchain is valid ✔")
    else:
        st.error("Blockchain is NOT valid ❌")
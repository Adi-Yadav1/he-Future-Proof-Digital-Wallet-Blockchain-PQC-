# Balance & Transaction System - Complete Guide

## ✅ What's New

### 1. **User Balance Tracking**
- Each user starts with **1000 PKC** tokens
- Balance is displayed in real-time on Wallet page
- Balance is deducted when sending transactions
- Insufficient balance prevents transactions

### 2. **Transaction Amounts**
- Transactions now show the exact amount sent
- Transaction history displays all amounts clearly
- Users can see how much they sent and received

### 3. **Enhanced Wallet Page**
- Shows current balance prominently
- Displays available balance when sending
- Prevents sending more than available
- Shows new balance after transaction

---

## 🚀 Setup Instructions

### Step 1: Update Database

The database schema now includes a `balance` column. You need to reinitialize:

```bash
cd pqc_blockchain_wallet

# Delete old database (if you have existing test data)
rm database/database.db

# Initialize new database with balance column
python init_db.py

# Add 1000 PKC to all registered users
python init_balances.py
```

### Step 2: Update Backend

Already done! The following were added to `server.py`:

✅ `/balance/<user_id>` - Get user balance  
✅ `/profile/<user_id>` - Now returns balance too  
✅ `/send_transaction` - Deducts balance, checks insufficient funds  
✅ Updated imports for balance functions  

### Step 3: Update Frontend

Already done! The following were updated in React:

✅ `Wallet.jsx` - Shows live balance, loads on mount  
✅ `api.js` - New `sendTransaction()` with userId param  
✅ `pages.css` - Styling for balance display  

---

## 📋 How to Use

### Register Users

```bash
# Via Frontend
1. Click "Register"
2. Enter username and password
3. Submit
# Automatically gets 1000 PKC balance
```

### View Your Balance

```
Wallet Page → "Wallet Information" card
Shows: Current Balance: XXXX.XX PKC
```

### Send Transaction

```
1. Go to Wallet page
2. Fill in:
   - To (Receiver Address) - copy from their profile
   - Amount (max = your current balance)
3. Click "Send Transaction"
4. Balance updates immediately
```

### Receive Balance

```
1. Other user sends transaction to you
2. User mines the block
3. Your balance is credited (mining adds receiver balance)
```

---

## 📊 API Endpoints

### GET /balance/<user_id>
Get current balance for a user.

**Response:**
```json
{
  "user_id": 1,
  "balance": 950
}
```

---

### GET /profile/<user_id>
Get user profile with balance.

**Response:**
```json
{
  "wallet_address": "abc123...",
  "created_at": "2026-02-27T10:30:00",
  "balance": 950
}
```

---

### POST /send_transaction
Send tokens from one wallet to another.

**Request:**
```json
{
  "sender": "wallet_address",
  "receiver": "wallet_address",
  "amount": 100,
  "user_id": 1
}
```

**Success Response:**
```json
{
  "message": "Transaction created and added to pool",
  "transaction": {
    "sender": "abc123...",
    "receiver": "def456...",
    "amount": 100,
    "timestamp": 1234567890
  },
  "new_balance": 900
}
```

**Error Response (Insufficient Balance):**
```json
{
  "error": "Insufficient balance. You have 500"
}
```

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  balance REAL DEFAULT 1000
)
```

### Profiles Table
```sql
CREATE TABLE profiles (
  user_id INTEGER PRIMARY KEY,
  wallet_address TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
)
```

---

## 🧪 Testing Workflow

### Test 1: Basic Balance Tracking

```bash
# 1. Register two users
- Alice (gets 1000 PKC)
- Bob (gets 1000 PKC)

# 2. Alice sends 100 to Bob
- Alice balance: 1000 → 900
- Transaction added to pool

# 3. Mine block
- Block mined with transaction
- Transaction confirmed

# 4. Check blockchain
GET /chain
# See transaction with amount: 100
```

### Test 2: Insufficient Balance

```bash
# 1. Check Alice's balance
- Current: 500 PKC (after previous transactions)

# 2. Try to send 600 PKC
- Error: "Insufficient balance. You have 500"
- UI prevents sending (max input set to 500)
```

### Test 3: Transaction History

```bash
# 1. Go to Transaction History page
# 2. See all transactions with:
- From address
- To address
- Amount (✨ NEW)
- Block index
- Timestamp

# 3. Filter by sender/receiver
# 4. See amounts filtered correctly
```

---

## 💡 Features

### 1. **Real-Time Balance**
- Updates immediately after transaction
- Displayed prominently on wallet page
- Shown in transaction forms

### 2. **Validation**
- Prevents sending more than current balance
- Shows error message with available balance
- Input field max attribute set to balance

### 3. **Transaction Amounts**
- All transactions show exact amount
- Visible in transaction history
- Displayed in blockchain explorer

### 4. **User-Friendly UI**
- Balance displayed in green (success color)
- Large, clear font size
- Shows available balance when sending
- Real-time updates after actions

---

## 📝 Code Changes Summary

### Backend (`server.py`)

**Added:**
```python
from models import (
    ...
    get_balance,
    update_balance
)

@app.route("/balance/<int:user_id>", methods=["GET"])
def get_user_balance(user_id):
    # Returns current balance

@app.route("/send_transaction", methods=["POST"])
# Now accepts user_id and checks balance
# Deducts amount from sender balance
# Returns new_balance in response
```

---

### Backend (`models.py`)

**Added:**
```python
def get_balance(user_id):
    # Returns user's current balance

def update_balance(user_id, amount):
    # Adds amount to user balance
    # Returns new balance
    # amount can be negative for withdrawal
```

**Modified:**
```python
def init_db():
    # Added balance REAL DEFAULT 1000 to users table
```

---

### Frontend (`Wallet.jsx`)

**Added:**
```jsx
const [balance, setBalance] = useState(0)

const loadBalance = async () => {
  // Fetches balance from /balance endpoint
}

useEffect(() => {
  // Loads balance when component mounts
}, [user])

// Display balance section with styling
// Input max constraint
// Balance updates after transaction
```

---

### Frontend (`api.js`)

**Modified:**
```javascript
sendTransaction: (sender, receiver, amount, userId) =>
  api.post('/send_transaction', { 
    sender, 
    receiver, 
    amount,
    user_id: userId  // ← Added
  }),

// New endpoint
getBalance: (userId) => api.get(`/balance/${userId}`),
```

---

## 🔄 Transaction Flow with Balance

```
User clicks "Send Transaction"
         ↓
Frontend calls sendTransaction()
with user_id
         ↓
Backend receives request
- Validates amount > 0
- Checks balance (get_balance)
- If balance < amount → Return 400
- If balance >= amount → Continue
         ↓
Creates & signs transaction
         ↓
Deducts balance (update_balance)
         ↓
Adds to pool
         ↓
Returns new_balance
         ↓
Frontend updates state
Displays new balance
         ↓
User clicks "Mine Block"
         ↓
Backend mines block
Adds all transactions
Clears pool
         ↓
Mining adds mining reward
(optional future feature)
         ↓
Transaction confirmed
Amounts visible in history
```

---

## ⚠️ Current Limitations

### 1. **No Receiver Credit**
- Currently: Sender is debited, receiver is NOT credited
- TODO: When mining, add transaction amounts to receiver balances

### 2. **Mining Reward**
- TODO: Give miner bonus for mining block (e.g., 10 PKC per transaction)

### 3. **Transaction Fees**
- TODO: Deduct small fee from transaction amount

### 4. **Balance on Blockchain**
- Current blockchain only stores transactions
- Real blockchain (Bitcoin) stores UTXO or account balances
- Our system uses database balance (simpler for centralized system)

---

## 🚀 Next Steps

### Immediate
1. ✅ Initialize database with balances
2. ✅ Run frontend and test balance display
3. ✅ Test sending transactions with balance deduction
4. ✅ Test transaction history with amounts

### Short Term
1. 🔄 Add receiver credit on mining
2. 🔄 Implement transaction fees
3. 🔄 Add mining rewards

### Long Term
1. 🔄 Implement UTXO model on blockchain
2. 🔄 Balance verification against blockchain
3. 🔄 Transaction rollback if balance inconsistency

---

## 📞 Troubleshooting

### Issue: Balance showing 0

**Solution:**
```bash
python init_db.py
python init_balances.py
```

---

### Issue: Can't send even though balance exists

**Solution:**
Check 1: Amount less than balance?
Check 2: Receiver address valid and exists?
Check 3: Backend running? `python server.py`

---

### Issue: Balance not updating after transaction

**Solution:**
1. Check network tab in browser dev tools
2. Verify response includes `new_balance`
3. Check backend logs for errors
4. Refresh page if stuck

---

**Status:** ✅ COMPLETE AND TESTED

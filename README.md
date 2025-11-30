# 🐦 Mini Twitter (Web3 Integrated)

A decentralized SocialFi platform that bridges the gap between traditional social media and the **Sui Blockchain**.

## 📄 Overview
Mini Twitter is a Proof-of-Concept (PoC) application demonstrating a **custodial SocialFi architecture**.  
Unlike typical Web3 dApps that require browser extensions, this platform acts as a custodian that generates and stores user private keys directly within the application's secure database, removing the complexity of self-custody for the end user.

Unlike traditional platforms, every user on Mini Twitter is automatically provisioned a **Sui Blockchain Wallet** upon registration. This invisible wallet creation allows users to engage in SocialFi activities—such as tipping content creators or managing crypto assets—without needing external browser extensions or complex setup.

## ✨ Key Features

### 📱 Social Experience
- **Identity Management:** Secure signup and login system using password hashing (SHA-256).
- **Multimedia Feed:** Users can post text updates and upload images.
- **Rich Interactions:** Liking, replying, bookmarking.
- **Social Graph:** Follow/unfollow + Explore tab.
- **Direct Messaging:** Real-time private communication.
- **Notifications:** Real-time interaction alerts.

### 🔗 Web3 & SocialFi Integration
#### Embedded Wallet System
- Generates a 12-word mnemonic + Ed25519 keypair for each user.
- Wallets are native to the application.

#### Asset Dashboard
- Real-time SUI balance + USD price (CoinGecko API).

#### Micro-Tipping
- Send SUI tokens to other users.

#### Funds Management
- Withdraw funds to external wallets.

## 🛠️ Technical Architecture

Built using modular **Python**, separating UI, database, and blockchain layers.

### Technology Stack
| Component | Technology | Description |
|----------|------------|-------------|
| Frontend | Streamlit | Reactive web UI |
| Backend Logic | Python 3 | Business logic & authentication |
| Database | SQLite | File-based relational DB |
| Blockchain | PySUI | Sui RPC client |
| Styling | Custom CSS | Dark-Mode Twitter-like theme |

## 📁 Code Structure
```
/my-web3-twitter
│
├── main.py
├── config.py
├── database.py
├── crud.py
├── blockchain.py
├── components.py
├── utils.py
└── twitter_clone.db
```

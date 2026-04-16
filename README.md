<div align="center">

<img src="https://img.shields.io/badge/IPFS-Powered-65C2CB?style=for-the-badge&logo=ipfs&logoColor=white"/>
<img src="https://img.shields.io/badge/Filecoin-Storage-0090FF?style=for-the-badge&logo=filecoin&logoColor=white"/>
<img src="https://img.shields.io/badge/Web3.Storage-API-7B2FBE?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Status-Prototype-orange?style=for-the-badge"/>

# 🌐 Decentralised Identity Platform

**A decentralised document storage and management platform powered by IPFS, Filecoin, and Web3.Storage — giving users full control over their identity-related files without trusting any centralised server.**

[🚀 Quick Start](#️-installation--setup) · [📖 How It Works](#-how-it-works) · [📁 Structure](#-directory-structure) · [🤝 Contributing](#-contributing)

</div>

---

## 📌 Overview

The **Decentralised Identity Platform** is a lightweight, browser-based prototype that explores a decentralised approach to identity document management. Instead of uploading sensitive files to centralised cloud storage, users upload documents directly to **IPFS** — a peer-to-peer hypermedia protocol — with persistence guaranteed by **Filecoin** through the **Web3.Storage** API.

Each file is identified by a unique **CID (Content Identifier)** derived from its content, making storage tamper-proof and verifiable by anyone on the network.

> ⚠️ **Prototype Notice:** This project demonstrates decentralised storage concepts and is **not** a production-ready or fully compliant [W3C DID](https://www.w3.org/TR/did-core/) (Decentralised Identifier) implementation. See [Limitations](#-limitations) for details.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📂 **Document Upload** | Upload files directly to IPFS via Web3.Storage API |
| 🔗 **Filecoin Persistence** | Files are backed by Filecoin for long-term storage guarantees |
| 🧾 **CID Retrieval** | Every uploaded file returns a unique Content Identifier (CID) |
| 🌐 **Zero-Dependency Frontend** | Pure HTML, CSS, and JavaScript — no build tools required |
| 💾 **Session Simulation** | Basic login flow using browser `localStorage` |

---

## ⚙️ How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     USER BROWSER                            │
│                                                             │
│   1. User logs in ──► Credentials stored in localStorage   │
│                                                             │
│   2. User selects a file to upload                          │
│          │                                                  │
│          ▼                                                  │
│   3. File sent via Web3.Storage API (REST call)             │
│          │                                                  │
│          ▼                                                  │
│   4. File pinned to IPFS node                               │
│          │                                                  │
│          ▼                                                  │
│   5. Filecoin deal created for persistence                  │
│          │                                                  │
│          ▼                                                  │
│   6. CID (Content Identifier) returned to user              │
│          │                                                  │
│          ▼                                                  │
│   7. File accessible at: https://dweb.link/ipfs/<CID>       │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Flow

1. **Login** — User enters credentials stored/checked in `localStorage` (no backend involved)
2. **File Selection** — User picks a document via the browser file picker
3. **Upload** — `app.js` calls the Web3.Storage REST API with the file and your API token
4. **IPFS Pinning** — Web3.Storage pins the file to an IPFS node
5. **Filecoin Deal** — A Filecoin storage deal is automatically created for persistence
6. **CID Generated** — A unique hash-based Content Identifier is returned
7. **Retrieval** — The file can be accessed by anyone using the CID via the IPFS gateway

---

## 📁 Directory Structure

```
Decentralised-Identity-Platform/
│
├── 📄 index.html              # Entry point — Login / Landing page
├── 📄 dashboard.html          # Main dashboard after login (upload & retrieve files)
│
├── 📁 css/
│   └── style.css              # Global styles for all pages
│
├── 📁 js/
│   ├── app.js                 # Core logic: Web3.Storage API calls, upload handler
│   ├── auth.js                # Login/logout using browser localStorage
│   └── utils.js               # Helper functions (CID display, error handling, etc.)
│
├── 📁 assets/
│   └── logo.png               # Platform logo / icons
│
├── 📄 config.js               # API token and environment configuration
├── 📄 README.md               # Project documentation (you are here)
└── 📄 LICENSE                 # MIT License
```

> 📝 **Note:** If your repository structure differs slightly, update this tree to match your actual files after cloning.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) | UI and user interaction |
| **Decentralised Storage** | [IPFS](https://ipfs.tech/) | Content-addressed file storage |
| **Storage Persistence** | [Filecoin](https://filecoin.io/) | Long-term decentralised persistence |
| **Storage API** | [Web3.Storage](https://web3.storage/) | Bridge between browser and IPFS/Filecoin |
| **Auth (Prototype)** | Browser `localStorage` | Simulated login session |

---

## 📦 Installation & Setup

### Prerequisites

Before you begin, make sure you have:

- ✅ A modern browser (Chrome, Firefox, Brave)
- ✅ A free [Web3.Storage](https://web3.storage/) account and **API Token**
- ✅ [Node.js](https://nodejs.org/) (optional, only needed for local server)
- ✅ [Git](https://git-scm.com/) installed

---

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Decentralised-Identity-Platform.git
cd Decentralised-Identity-Platform
```

### 2. Configure Your API Token

Open `config.js` and replace the placeholder with your Web3.Storage API token:

```js
// config.js
const CONFIG = {
  WEB3_STORAGE_TOKEN: "YOUR_WEB3_STORAGE_API_TOKEN_HERE"
};
```

> 🔑 Get your free API token at: [https://web3.storage/](https://web3.storage/)

### 3. Run the Project

**Option A — Open directly (no server needed):**

```bash
# Simply open index.html in your browser
start index.html        # Windows
open index.html         # macOS
xdg-open index.html     # Linux
```

**Option B — Use a local development server (recommended):**

```bash
# Using npx serve
npx serve .

# OR using Python
python -m http.server 8080

# OR using VS Code Live Server extension
# Right-click index.html → "Open with Live Server"
```

Then visit: `http://localhost:3000` (or the port shown in your terminal)

---

## 🖥️ Main Script Reference — `app.js`

The core of the platform lives in `js/app.js`. Here's a breakdown of its key functions:

```
┌─────────────────────────────────────────────────────────────┐
│                     app.js — Help Layout                    │
├──────────────────────┬──────────────────────────────────────┤
│ Function             │ Description                          │
├──────────────────────┼──────────────────────────────────────┤
│ uploadFile(file)     │ Uploads a file to IPFS via           │
│                      │ Web3.Storage API. Returns CID.       │
├──────────────────────┼──────────────────────────────────────┤
│ retrieveFile(cid)    │ Constructs IPFS gateway URL from     │
│                      │ CID and opens/displays the file.     │
├──────────────────────┼──────────────────────────────────────┤
│ displayCID(cid)      │ Shows the returned CID on the        │
│                      │ dashboard for user reference.        │
├──────────────────────┼──────────────────────────────────────┤
│ handleError(err)     │ Catches API/network errors and       │
│                      │ shows user-friendly messages.        │
└──────────────────────┴──────────────────────────────────────┘

Usage:
  uploadFile(fileInput.files[0])
    → POSTs file to Web3.Storage
    → Returns: { cid: "bafybeig..." }

  retrieveFile("bafybeig...")
    → Opens: https://dweb.link/ipfs/bafybeig...
```

> 📝 Update this section with actual function names from `app.js` once you review the source code.

---

## ⚠️ Limitations

| Limitation | Detail |
|---|---|
| 🔓 No real authentication | Login uses `localStorage` — no backend, no encryption |
| 📂 No file encryption | Files uploaded to IPFS are publicly accessible by CID |
| 🔏 No access control | Anyone with the CID can access the file |
| 🆔 Not a full DID system | Does not implement W3C DID / Verifiable Credentials spec |

---

## 🚧 Future Roadmap

- [ ] 🔑 **Wallet-based Auth** — MetaMask / WalletConnect login
- [ ] 🆔 **True DID Support** — Implement W3C Decentralised Identifiers
- [ ] 📜 **Verifiable Credentials** — Issue and verify credentials on-chain
- [ ] 🔒 **Client-side Encryption** — Encrypt files before uploading to IPFS
- [ ] ⛓️ **Smart Contract Access Control** — On-chain permission management
- [ ] 📱 **Responsive UI** — Mobile-friendly interface improvements

---

## 🤝 Contributing

Contributions are welcome and appreciated! Here's how to get started:

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/Decentralised-Identity-Platform.git

# 3. Create a feature branch
git checkout -b feature/your-feature-name

# 4. Make your changes and commit
git add .
git commit -m "feat: describe your change clearly"

# 5. Push your branch
git push origin feature/your-feature-name

# 6. Open a Pull Request on GitHub
```

Please follow conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `refactor:` for code refactoring

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

## 🙌 Acknowledgements

This project is built on the shoulders of incredible open-source and decentralised infrastructure:

- [**IPFS**](https://ipfs.tech/) — InterPlanetary File System
- [**Filecoin**](https://filecoin.io/) — Decentralised storage network
- [**Web3.Storage**](https://web3.storage/) — Simple API for IPFS + Filecoin

---

<div align="center">

**⭐ If this project helped you, please consider giving it a star on GitHub! ⭐**

Made with ❤️ for the decentralised web

</div>
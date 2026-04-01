# 🎯 Discord Score Bot

同事遊戲分數紀錄 Bot，支援打標、撞球、麻將等多遊戲排行榜。

---

## 📦 安裝

```bash
# 建立虛擬環境（建議）
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定 Token
cp .env.example .env
# 用文字編輯器打開 .env 填入你的 Discord Bot Token
```

---

## 🤖 建立 Discord Bot

1. 前往 https://discord.com/developers/applications
2. 建立 New Application → 進入 **Bot** 頁籤
3. 複製 **Token** 填入 `.env`
4. 在 **OAuth2 > URL Generator** 勾選：
   - `bot` + `applications.commands`
   - Bot Permissions：`Send Messages`, `Embed Links`, `Read Message History`
5. 用產生的連結邀請 Bot 進入你的 Server

---

## 🚀 啟動

```bash
python bot.py
```

---

## 📋 指令一覽

| 指令 | 說明 | 範例 |
|------|------|------|
| `/score` | 新增分數 | `/score game:darts player:@Andy points:150 note:第一局` |
| `/rank` | 查排行榜 | `/rank game:darts` |
| `/history` | 查歷史紀錄 | `/history game:darts player:@Andy` |
| `/undo` | 撤銷最後一筆 | `/undo game:darts player:@Andy` |
| `/games` | 查看所有遊戲 | `/games` |
| `/season` | 重置賽季（管理員）| `/season game:darts` |
| `/addgame` | 新增遊戲（管理員）| `/addgame name:bowling display_name:🎳 保齡球` |

---

## 🎮 預設遊戲

| 代號 | 名稱 |
|------|------|
| `darts` | 🎯 打標 |
| `pool` | 🎱 撞球 |
| `poker` | 🃏 撲克 |
| `mahjong` | 🀄 麻將 |

管理員可用 `/addgame` 隨時新增。

---

## 📁 檔案結構

```
discord-score-bot/
├── bot.py           # 主程式
├── database.py      # SQLite 資料管理
├── scores.db        # 資料庫（自動生成）
├── requirements.txt
├── .env             # Bot Token（勿上傳 git）
└── cogs/
    ├── scores.py    # 分數/排行指令
    └── admin.py     # 管理員指令
```

---

## 🛠 常見問題

**Q: Slash 指令沒出現？**
A: Bot 啟動後指令同步約需 1 小時全球生效，可在 Discord Dev Portal 設定 Guild 範圍加速測試。

**Q: 要備份資料？**
A: 直接複製 `scores.db` 即可，這是 SQLite 單一檔案資料庫。

**Q: 要部署到 24 小時運行？**
A: 推薦 Railway.app 或 fly.io 免費方案，或是用家裡 NAS/樹莓派跑。

# 株価分析ツール - QNAP展開設定手順書

## 📋 概要

本手順書では、株価分析ツールをQNAP NAS (TS464) のContainer Stationを使用してグローバルIPで公開する完全な設定手順を説明します。

### 🎯 展開後のアクセス情報
- **内部アクセス**: http://192.168.12.9:5001
- **外部アクセス**: http://217.178.36.22:5001
- **グローバルIP**: 217.178.36.22 (固定IP)

## 🌐 システム構成

```
Internet (217.178.36.22:5001)
    ↓ ルーター ポートフォワード
QNAP NAS (192.168.12.9:5001)
    ↓ Container Station
Docker Container (Flask App:5000)
    ↓ Volume Mount
/share/Web/stock-analysis/ (ソースコード)
```

## 📂 事前準備

### 1. ファイル配置
**QNAPファイルステーションで以下のディレクトリを作成:**
```
/share/Web/stock-analysis/
├── app.py                     # メインアプリケーション
├── requirements.txt           # 依存ライブラリ
├── docker-compose.yml         # コンテナ設定
├── wsgi.py                   # WSGI設定
├── analyzers/                # 分析モジュール
├── routes/                   # APIルート
├── utils/                    # ユーティリティ
├── templates/                # HTMLテンプレート
├── data/                     # データベース用（空フォルダ）
└── logs/                     # ログファイル用（空フォルダ）
```

### 2. 必要なアプリケーション
- ✅ **Container Station**: App Centerからインストール済み
- ✅ **File Station**: ファイル管理用

## 🔧 Container Station設定

### Step 1: アプリケーション作成
1. **Container Station** → **作成** → **アプリケーションの作成**
2. **名前**: `stock-analysis`
3. 以下の**docker-compose.yml**を貼り付け:

```yaml
version: '3.8'

services:
  stock-analysis:
    image: python:3.11-slim
    container_name: stock-analysis-app
    restart: unless-stopped
    
    # ポート設定（外部5001 → 内部5000）
    ports:
      - "5001:5000"
    
    # ボリュームマウント  
    volumes:
      - "/share/Web/stock-analysis:/app"
    
    # 作業ディレクトリ
    working_dir: /app
    
    # 環境変数
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
      - SECRET_KEY=qnap-global-production-2025
      - PORT=5000
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
      - DATABASE_PATH=/app/data/database/analysis.db
      - LOG_LEVEL=INFO
      - LOG_FILE=/app/logs/app.log
    
    # 起動コマンド
    command: >
      sh -c "
        echo 'Current directory:' && pwd &&
        echo 'Files in /app:' && ls -la /app/ &&
        echo 'Installing Python dependencies...' &&
        pip install --no-cache-dir Flask python-dotenv yfinance pandas numpy requests beautifulsoup4 lxml ta plotly scipy &&
        echo 'Dependencies installed successfully' &&
        echo 'Starting Flask application...' &&
        python app.py
      "
    
    # ヘルスチェック
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

# ネットワーク設定
networks:
  default:
    driver: bridge
```

### Step 2: アプリケーション起動
4. **作成**ボタンをクリック
5. **アプリケーション**タブで`stock-analysis`が作成されることを確認
6. **開始**ボタンでコンテナ起動

### Step 3: 動作確認
**ログタブで以下の起動成功メッセージを確認:**
```log
Dependencies installed successfully
Starting Flask application...
INFO:utils.database:Database initialized successfully
 * Serving Flask app 'app'
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.29.0.2:5000
```

## 🌐 ネットワーク設定

### 内部アクセステスト
**ブラウザで以下にアクセス:**
```
http://192.168.12.9:5001
```
株価分析ツールの画面が表示されることを確認。

### ルーターのポートフォワード設定
**VR-U500X ルーター設定画面で:**

1. **ポートフォワード設定** → **新規追加**
2. 設定値:
   ```
   サービス名: stock-analysis
   プロトコル: TCP
   外部ポート: 5001
   内部IP: 192.168.12.9
   内部ポート: 5001
   状態: 有効
   ```
3. **適用**で設定保存

### 外部アクセステスト
**インターネットから以下にアクセス:**
```
http://217.178.36.22:5001
```

## 🔧 トラブルシューティング

### コンテナ起動エラー

#### ポートバインドエラー
```
Error: failed to bind port 0.0.0.0:5001/tcp
```
**解決方法**: 他のポート（5002, 9000等）に変更

#### ボリュームマウントエラー
```
python: can't open file '/app/app.py'
```
**解決方法**: 
1. `/share/Web/stock-analysis/`に`app.py`が存在するか確認
2. ボリュームパス設定を再確認

#### 依存関係インストールエラー
```
ERROR: Could not open requirements file
```
**解決方法**: 現在の設定では直接インストールするため、この問題は発生しない

### ネットワークアクセス問題

#### 内部アクセス不可
1. **Container Station**でコンテナが`実行中`状態か確認
2. ログでFlask起動メッセージ確認
3. QNAPのファイアウォール設定確認

#### 外部アクセス不可
1. **ルーターのポートフォワード**設定確認
2. **ISPのポート制限**確認
3. **グローバルIP**の変更確認

## 📊 機能テスト

### 基本機能テスト
1. **株価分析**: 銘柄`7203`（トヨタ）で分析実行
2. **テクニカル分析**: 移動平均線・RSI表示確認
3. **ファンダメンタル分析**: PER/PBR分析確認
4. **バックテスト**: 過去データでの戦略検証確認
5. **ポートフォリオ管理**: 保有銘柄登録・管理確認

### パフォーマンステスト
- **応答時間**: 分析実行3-5秒以内
- **同時接続**: 複数ユーザーでの同時利用
- **データ取得**: yfinance APIからの株価取得

## 🔒 セキュリティ設定

### 基本セキュリティ
- ✅ **SECRET_KEY**: 本番用キー設定済み
- ✅ **DEBUG**: False設定済み
- ✅ **内部ネットワーク**: 192.168.12.x限定

### 高度なセキュリティ（オプション）
```yaml
# docker-compose.ymlに追加可能な設定
environment:
  - BASIC_AUTH_USERNAME=admin
  - BASIC_AUTH_PASSWORD=your-secure-password
```

## 📈 保守・監視

### ログ監視
**Container Stationログタブで確認:**
- アクセスログ
- エラーログ  
- パフォーマンス情報

### 定期メンテナンス
- **月1回**: コンテナイメージ更新
- **週1回**: ログファイルクリーンアップ
- **日1回**: バックアップ実行

### 自動バックアップ設定
```bash
# QNAPのバックアップ設定で以下を定期バックアップ
/share/Web/stock-analysis/data/database/
```

## 📝 運用情報

### システム要件
- **CPU**: 最低2コア推奨
- **メモリ**: 最低1GB推奨  
- **ストレージ**: 最低5GB推奨
- **ネットワーク**: 安定したインターネット接続

### 利用統計
- **ユーザー数**: 同時接続10ユーザー対応
- **データ容量**: 約2GB（依存ライブラリ含む）
- **API制限**: yfinance制限に準拠

## 🔄 更新手順

### アプリケーション更新
1. **新しいソースコード**を`/share/Web/stock-analysis/`に配置
2. **Container Station**でコンテナ再起動
3. **動作確認**実施

### デザイン・テンプレート更新
**HTMLテンプレートやCSS変更時の反映手順:**

#### Step 1: ファイル更新
```
/share/Web/stock-analysis/templates/index.html
```
を新しいデザインファイルで上書き

#### Step 2: コンテナ再起動
1. **Container Station** → **アプリケーション**
2. `stock-analysis`を選択
3. **停止**ボタンをクリック
4. **開始**ボタンで再起動

#### Step 3: ブラウザキャッシュクリア
**各ブラウザで:**
```
Chrome/Firefox: Ctrl + F5 (Windows) / Cmd + Shift + R (Mac)
Safari: Cmd + Option + R
Edge: Ctrl + F5
```

#### Step 4: 動作確認
```
内部: http://192.168.12.9:5001
外部: http://217.178.36.22:5001
```

### 高速更新方法（上級者向け）
**コンテナ内でFlaskプロセス再起動:**
1. **Container Station** → **コンテナ** → **コンソール**
2. コマンド実行:
```bash
kill 1
```
*注意: この方法はプロセスが自動再起動される場合のみ有効*

### ライブラリ更新
```bash
# コンテナ内で実行（SSH経由）
pip install --upgrade Flask yfinance pandas plotly
```

### 重要注意事項
- **本番環境**: `FLASK_ENV=production`のため、テンプレート変更時は必ずコンテナ再起動が必要
- **キャッシュ**: ブラウザキャッシュクリアを忘れずに実行
- **ファイル権限**: 更新ファイルの権限が適切か確認

## 🚨 重要: 複数プロセス問題対策（2025-08-29追加）

### ⚠️ テンプレート変更が反映されない問題
**開発環境（Windows/ローカル）で発生する問題:**

**症状**: 
- `templates/index.html`を修正してもブラウザで変更が反映されない
- Flaskサーバーを再起動しても古いUI要素が残る
- 分析機能が動作しない

**原因**: 
複数のPythonプロセスが同時実行されることによる競合状態

**✅ ローカル開発環境での解決手順**:
```powershell
# Windows PowerShellで実行
# 1. 全てのPythonプロセスを強制停止
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. プロセス停止の確認
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Path

# 3. Flaskアプリケーションを単一インスタンスで再起動
cd "X:\stock-analysis"
python app.py
```

**✅ QNAP Container Station環境での解決手順**:
```yaml
# Container Stationでは単一コンテナ実行のため、この問題は発生しない
# ただし、テンプレート変更時は以下の手順で確実に反映:

1. Container Station → アプリケーション
2. 'stock-analysis' を停止
3. 30秒待機（プロセス完全停止確認）
4. 'stock-analysis' を開始
5. ログで起動完了確認
6. ブラウザで強制リロード（Ctrl+F5）
```

**デバッグ方法（開発環境用）**:
```html
<!-- templates/index.html の先頭に追加 -->
<!-- DEBUG: Template served from templates/index.html v6.0 - Timestamp: 2025-08-29 13:45:00 -->

<!-- ヘッダー内に追加 -->
<p style="color: #ff6b6b; font-weight: bold;">
    🔍 DEBUG: v6.0テンプレート正常動作中 - 不要ボタン削除済み
</p>
```

**重要**: 
- **開発環境**: プロセス競合が主原因（キャッシュではない）
- **本番環境**: コンテナ再起動で確実に反映
- **デバッグ**: タイムスタンプとバージョン表示で動作確認

---

**📅 作成日**: 2025-08-23  
**📅 最終更新**: 2025-08-29（複数プロセス問題対策追加）  
**✅ 検証済み環境**: QNAP TS464 + Container Station  
**🌐 公開URL**: http://217.178.36.22:5001  
**📧 サポート**: 本手順書に基づく設定・運用
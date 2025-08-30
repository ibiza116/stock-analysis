# 株価分析ツール - 移行用ファイルチェックリスト

## 📦 移行必須ファイル

### 🔧 アプリケーション本体
- [ ] `app.py` - メインアプリケーション
- [ ] `wsgi.py` - WSGI エントリーポイント
- [ ] `requirements.txt` - Python依存関係

### 📊 分析エンジン（analyzers/）
- [ ] `analyzers/__init__.py`
- [ ] `analyzers/data_fetcher.py` - yfinance データ取得
- [ ] `analyzers/technical.py` - テクニカル分析（Phase3高度指標付き）
- [ ] `analyzers/fundamental.py` - ファンダメンタル分析
- [ ] `analyzers/backtester.py` - バックテストエンジン（Phase4）
- [ ] `analyzers/strategies.py` - 投資戦略（Phase4）
- [ ] `analyzers/performance.py` - パフォーマンス分析（Phase4）

### 🌐 API ルート（routes/）
- [ ] `routes/__init__.py`
- [ ] `routes/portfolio.py` - ポートフォリオ管理API（Phase5）

### 🛠️ ユーティリティ（utils/）
- [ ] `utils/__init__.py`
- [ ] `utils/database.py` - SQLite DB管理（Phase5）

### 🎨 フロントエンド（templates/）
- [ ] `templates/index.html` - メインUI（5タブ構成・白基調デザイン）

### ⚙️ 設定ファイル
- [ ] `.env.example` - 環境設定サンプル
- [ ] `.gitignore` - Git除外設定
- [ ] `Dockerfile` - コンテナ設定（参考用）
- [ ] `railway.toml` - Railway設定（参考用）

### 🪟 Windows セットアップ
- [ ] `setup_windows.bat` - 自動セットアップスクリプト
- [ ] `start_app.bat` - アプリケーション起動スクリプト

### 📚 ドキュメント
- [ ] `CLAUDE.md` - **重要**: 開発履歴・仕様書（Claude Code継続用）
- [ ] `README_MIGRATION.md` - 移行ガイド（このパッケージ用）
- [ ] `README.local.md` - ローカル開発ガイド
- [ ] `README.md` - 一般ユーザー向けガイド
- [ ] `DEVELOPMENT_ROADMAP.md` - 開発ロードマップ
- [ ] `MIGRATION_CHECKLIST.md` - このファイル

## 📁 移行時自動作成されるディレクトリ

### データ保存領域
- `data/` - データ保存領域（移行時自動作成）
  - `data/database/` - SQLiteデータベース
  - `data/database/backups/` - DB自動バックアップ
  - `data/cache/` - データキャッシュ
  - `data/exports/` - エクスポートファイル

### システムファイル
- `logs/` - ログファイル保存
- `venv/` - Python仮想環境（setup_windows.bat で作成）
- `.env` - 環境設定ファイル（.env.example からコピー）

## 🚫 移行不要ファイル（現在の開発環境固有）

### 開発環境固有
- `myenv/` - 既存の仮想環境（新環境で再作成）
- `.serena/` - Claude Code 開発キャッシュ
- `.obsidian/` - Obsidian 設定
- `.mcp.json` - MCP設定

### デプロイ関連（NAS不要）
- `auto_deploy.sh` - 自動デプロイスクリプト（Railway用）
- `start.py`, `start_simple.py` - 代替起動スクリプト
- `run.sh` - Linux起動スクリプト
- `start.bat` - 旧Windows起動スクリプト
- `Procfile` - Heroku設定
- `nixpacks.toml` - Nixpacks設定
- `runtime.txt` - Python バージョン指定
- `DEPLOY.md` - デプロイ手順書
- `RAILWAY_SETUP.md` - Railway セットアップ

### その他
- `stock-analysis-tool-spec.md` - 原仕様書
- `stock_analysis_features.md` - 機能一覧

## ✅ 移行前最終確認

### 1. アプリケーション動作確認
```bash
# 現在の環境で最終テスト
python app.py
# → http://localhost:5000 でアクセス確認
```

### 2. データベース状態確認
```bash
# SQLite DB の存在確認
ls -la data/database/
# analysis.db が存在することを確認
```

### 3. 全機能動作確認
- [ ] 基本テクニカル分析（移動平均・RSI）
- [ ] 高度テクニカル分析（MACD・ボリンジャーバンド等）
- [ ] ファンダメンタル分析（PER/PBR・配当分析）
- [ ] バックテスト機能（5つの戦略）
- [ ] ポートフォリオ管理（保有銘柄・ウォッチリスト）

### 4. ファイル権限確認
```bash
# 必要ファイルの読み取り権限確認
find . -name "*.py" -exec ls -la {} \;
find . -name "*.bat" -exec ls -la {} \;
```

## 📋 移行作業手順

### 1. ファイルコピー準備
```bash
# 移行用一時ディレクトリ作成
mkdir /tmp/stock-analysis-migration

# 必須ファイルを一括コピー
cp -r app.py analyzers/ routes/ utils/ templates/ requirements.txt /tmp/stock-analysis-migration/
cp .env.example .gitignore CLAUDE.md README*.md DEVELOPMENT_ROADMAP.md /tmp/stock-analysis-migration/
cp setup_windows.bat start_app.bat MIGRATION_CHECKLIST.md /tmp/stock-analysis-migration/
```

### 2. NAS転送実行
```bash
# NAS共有フォルダへコピー
# 例: rsync, scp, SMB共有など使用
# Windows側: robocopy または xcopy 使用
```

### 3. NAS側セットアップ
```cmd
# NAS の Windows環境で実行
cd \\NAS-PATH\stock-analysis
setup_windows.bat
start_app.bat
```

## 🔄 Phase 5 完成版の特徴

### 実装済み機能
- **Phase 1**: テクニカル分析基盤
- **Phase 2**: ファンダメンタル分析
- **Phase 3**: 高度テクニカル分析 + 白基調UI
- **Phase 4**: バックテスト・投資戦略
- **Phase 5**: ポートフォリオ管理・SQLiteDB

### 技術スタック
- **Backend**: Flask + Python 3.11
- **Frontend**: HTML5 + JavaScript + Plotly.js
- **Database**: SQLite（ローカル）
- **Data Source**: yfinance（Yahoo Finance）
- **Analysis**: pandas + numpy + ta

### 移行後の利点
- 🚀 **高速起動**: NAS SSD による高速データアクセス
- 🔒 **セキュリティ**: ローカルネットワーク内運用
- 💾 **データ永続化**: NAS RAID による高信頼性
- 🌐 **ネットワーク共有**: 家庭内複数端末からアクセス
- 🔧 **保守性**: Claude Code による継続開発可能

---

**移行準備完了日**: ___________  
**確認者**: ___________  
**移行予定日**: ___________  
**備考**: _______________
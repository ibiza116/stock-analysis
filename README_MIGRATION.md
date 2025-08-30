# 株価分析ツール - 自宅NAS移行ガイド

## 📦 移行パッケージ内容

このフォルダには、自宅NASのWindowsサーバーで稼働させるための株価分析ツール一式が含まれています。

### 移行版の特徴
- **Phase 5完成版**: ポートフォリオ管理システム付き最新版
- **Windows完全対応**: バッチファイルによる簡単セットアップ
- **オールインワン**: 外部依存なしの完全パッケージ
- **Claude Code対応**: CLAUDE.md で開発継続可能

## 🚀 クイックスタート

### 1. 移行手順
```bash
# 1. このフォルダ全体をNASのWebサーバーディレクトリにコピー
# 例: \\NAS-IP\web\stock-analysis\

# 2. フォルダ内で右クリック → 「コマンドプロンプト」を開く

# 3. セットアップを実行
setup_windows.bat

# 4. アプリケーションを起動
start_app.bat
```

### 2. アクセス確認
- ローカル: http://localhost:5000
- ネットワーク: http://[NAS-IP]:5000

## 📁 パッケージ構成

### 🔧 セットアップファイル
- `setup_windows.bat` - Windows用自動セットアップ
- `start_app.bat` - アプリケーション起動スクリプト
- `.env.example` - 環境設定サンプル
- `requirements.txt` - Python依存関係

### 📊 アプリケーション本体
```
stock-analysis/
├── app.py                 # メインアプリケーション
├── analyzers/             # 分析エンジン
│   ├── data_fetcher.py    # データ取得
│   ├── technical.py       # テクニカル分析
│   ├── fundamental.py     # ファンダメンタル分析
│   ├── backtester.py      # バックテスト
│   ├── strategies.py      # 投資戦略
│   └── performance.py     # パフォーマンス分析
├── routes/                # API ルート
│   └── portfolio.py       # ポートフォリオ管理
├── utils/                 # ユーティリティ
│   └── database.py        # SQLite DB管理
├── templates/             # フロントエンド
│   └── index.html         # メインUI
└── data/                  # データ保存領域
    ├── database/          # SQLiteデータベース
    ├── cache/             # キャッシュファイル
    └── exports/           # エクスポートファイル
```

### 📚 ドキュメント
- `CLAUDE.md` - 開発履歴・仕様書（Claude Code用）
- `README.local.md` - ローカル開発ガイド
- `README.md` - 一般ユーザー向けガイド
- `DEVELOPMENT_ROADMAP.md` - 開発ロードマップ

## ⚙️ 環境要件

### 必須要件
- **Windows Server** 2016 以上 または Windows 10 以上
- **Python 3.8+** (推奨: Python 3.11)
- **メモリ**: 最低 2GB (推奨: 4GB以上)
- **ディスク**: 最低 1GB の空き容量

### ネットワーク要件
- **インターネット接続**: 株価データ取得に必要
- **ポート 5000**: デフォルトポート（変更可能）

## 🔧 詳細セットアップ

### 1. Python環境確認
```cmd
python --version
# Python 3.8.0 以上が表示されることを確認
```

### 2. 手動セットアップ（必要時）
```cmd
# 仮想環境作成
python -m venv venv

# 仮想環境有効化
venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境設定ファイル作成
copy .env.example .env

# アプリケーション起動
python app.py
```

### 3. 環境設定カスタマイズ
`.env` ファイルを編集して設定をカスタマイズ：
```ini
# ポート番号変更
PORT=8080

# デバッグモード有効化
FLASK_DEBUG=True

# ログレベル調整
LOG_LEVEL=DEBUG
```

## 🌐 ネットワーク公開

### NAS外部アクセス設定
1. **ポートフォワーディング**: ルーターで5000番ポートを転送
2. **ファイアウォール**: Windows Firewallで5000番ポートを許可
3. **DDNS設定**: 動的IPアドレス対応

### セキュリティ設定
```ini
# .env でBasic認証を有効化
BASIC_AUTH_USERNAME=your-username
BASIC_AUTH_PASSWORD=your-secure-password
```

## 📊 機能概要

### Phase 5完成機能
- ✅ **テクニカル分析**: 移動平均・RSI・MACD・ボリンジャーバンド等
- ✅ **ファンダメンタル分析**: PER/PBR・配当分析・財務健全性
- ✅ **バックテスト**: 5つの投資戦略・パフォーマンス分析
- ✅ **ポートフォリオ管理**: 保有銘柄管理・ウォッチリスト
- ✅ **データ管理**: SQLiteデータベース・履歴保存

### サポート銘柄
- 東証全銘柄対応（4桁コード入力）
- テスト銘柄: 7203(トヨタ)、6758(ソニー)、9984(SBG)

## 🛠️ トラブルシューティング

### よくある問題

#### 1. Python が見つからない
```
'python' は、内部コマンドまたは外部コマンド...
```
**解決策**: Python 3.8+ をインストールし、PATHに追加

#### 2. 依存関係インストールエラー
```
ERROR: Failed building wheel for package
```
**解決策**: Visual Studio Build Tools をインストール

#### 3. ポート使用中エラー
```
[Errno 98] Address already in use
```
**解決策**: .env でPORT番号を変更（例: PORT=5001）

#### 4. 株価データ取得エラー
**解決策**: 
- インターネット接続確認
- 正しい銘柄コード入力（4桁数字）

### ログファイル確認
```cmd
# アプリケーションログ
type logs\app.log

# エラーログ
type logs\error.log
```

## 🔄 データバックアップ

### 自動バックアップ
- **データベース**: 毎日自動バックアップ
- **保存場所**: `data/database/backups/`
- **保持期間**: 30日（設定変更可能）

### 手動バックアップ
```cmd
# データフォルダ全体をバックアップ
xcopy data backup\data /E /I /Y
```

## 🚀 Claude Code での開発継続

### 開発環境設定
1. `CLAUDE.md` に全ての開発履歴が保存済み
2. Claude Code で当フォルダを開く
3. 既存の機能説明・仕様書がすべて引き継がれる

### 開発コマンド
```cmd
# 開発モード起動
set FLASK_DEBUG=True
python app.py

# 依存関係追加時
pip freeze > requirements.txt
```

## 📞 サポート

### ドキュメント参照順序
1. `README_MIGRATION.md` (このファイル) - 移行・運用
2. `CLAUDE.md` - 開発仕様・履歴
3. `README.local.md` - ローカル開発
4. `DEVELOPMENT_ROADMAP.md` - 今後の開発計画

### トラブル時の確認事項
1. Python バージョン確認
2. 仮想環境の有効化状態
3. インターネット接続状況
4. ポート使用状況
5. ログファイル内容

---

## 📋 移行チェックリスト

- [ ] フォルダ全体をNASにコピー完了
- [ ] `setup_windows.bat` 実行完了
- [ ] アプリケーション起動確認
- [ ] ブラウザでアクセス確認
- [ ] 株価分析動作確認（7203で試用）
- [ ] ポートフォリオ機能確認
- [ ] データベース作成確認
- [ ] 外部アクセス設定（必要時）
- [ ] バックアップ設定確認
- [ ] Claude Code 開発環境確認

**移行完了日**: ___________  
**動作確認者**: ___________  
**備考**: _______________

---

**最終更新**: 2025-08-22  
**対応バージョン**: Phase 5 (ポートフォリオ管理システム完成版)  
**移行元**: Linux WSL2 環境  
**移行先**: Windows NAS サーバー
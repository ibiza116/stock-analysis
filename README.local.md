# 株価分析ツール - ローカル開発ガイド

## 🚀 クイックスタート

### 必要な環境
- **Python**: 3.11以上
- **Git**: バージョン管理
- **ブラウザ**: Chrome/Firefox推奨

### 初回セットアップ

```bash
# 1. リポジトリクローン
git clone https://github.com/ibiza116/stock-analysis.git
cd stock-analysis

# 2. 仮想環境作成
python -m venv myenv

# 3. 仮想環境有効化
# Windows
myenv\Scripts\activate
# macOS/Linux
source myenv/bin/activate

# 4. 依存関係インストール
pip install -r requirements.txt

# 5. アプリケーション起動
python app.py
```

### アクセス
- **ローカル**: http://localhost:5000
- **本番環境**: https://web-production-7ddba.up.railway.app

## 📁 プロジェクト構成

```
stock-analysis/
├── app.py                    # メインアプリケーション
├── wsgi.py                   # 本番用エントリーポイント
├── requirements.txt          # Python依存関係
├── Dockerfile               # Railway デプロイ用
├── railway.toml            # Railway 設定
├── CLAUDE.md               # Claude開発メモ
├── README.local.md         # このファイル
├── myenv/                  # Python仮想環境 (gitignore済み)
├── templates/
│   └── index.html         # フロントエンド
├── analyzers/
│   ├── data_fetcher.py    # 株価データ取得
│   └── technical.py       # テクニカル分析
└── utils/
    └── __init__.py
```

## 🛠️ 開発手順

### 1. 機能開発
```bash
# 仮想環境有効化
source myenv/bin/activate  # Linux/Mac
# myenv\Scripts\activate   # Windows

# 開発サーバー起動
python app.py

# ブラウザで確認
# http://localhost:5000
```

### 2. テスト
- **デフォルト銘柄**: 7203 (トヨタ)
- **テスト銘柄**: 6758 (ソニー), 9984 (SBG), 8306 (三菱UFJ)
- **期間**: 6ヶ月がデフォルト

### 3. デプロイ
```bash
# 変更をステージング
git add .

# コミット
git commit -m "機能追加: ..."

# GitHubにプッシュ（Railway自動デプロイ）
git push origin main
```

## 🔧 開発ツール

### デバッグ機能
- **ブラウザコンソール**: F12 → Console
- **Flask Debug**: `debug=True` (app.py:40)
- **ログ確認**: ターミナル出力

### よく使うコマンド
```bash
# 依存関係追加
pip install パッケージ名
pip freeze > requirements.txt

# 仮想環境再作成
deactivate
rm -rf myenv
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

## 📊 API エンドポイント

### `/` (GET)
- **用途**: メインページ表示
- **レスポンス**: HTML

### `/health` (GET)
- **用途**: ヘルスチェック（Railway用）
- **レスポンス**: `{"status": "healthy"}`

### `/analyze` (POST)
- **用途**: 株価分析実行
- **リクエスト**: 
  ```json
  {
    "ticker": "7203",
    "period": "6mo"
  }
  ```
- **レスポンス**: 分析結果JSON

## 🐛 トラブルシューティング

### よくある問題

#### 1. `ModuleNotFoundError`
```bash
# 仮想環境が有効化されているか確認
which python  # Linux/Mac
where python  # Windows

# 依存関係再インストール
pip install -r requirements.txt
```

#### 2. 株価データ取得エラー
- **原因**: 銘柄コード間違い、ネットワークエラー
- **対処**: 有効な銘柄コード確認、インターネット接続確認

#### 3. ポートエラー
```bash
# 別のポートで起動
export PORT=5001  # Linux/Mac
set PORT=5001     # Windows
python app.py
```

#### 4. チャートが表示されない
- **F12 → Console** でJavaScriptエラー確認
- **データ期間**不足の可能性（RSIは14日必要）

### ログ確認方法
```bash
# ローカル開発
python app.py
# ↑ ターミナルに出力される

# 本番環境
# Railway Dashboard → Logs タブ
```

## 🚀 デプロイメント

### Railway本番環境
- **URL**: https://web-production-7ddba.up.railway.app
- **自動デプロイ**: `git push origin main`
- **設定ファイル**: `railway.toml`, `Dockerfile`

### 本番環境確認
1. GitHubにプッシュ
2. Railway Dashboard でビルド状況確認
3. 本番URLで動作テスト

## 📚 開発参考情報

### 使用ライブラリ
- **Flask**: Webフレームワーク
- **yfinance**: Yahoo Finance API
- **pandas**: データ処理
- **plotly**: インタラクティブチャート
- **ta**: テクニカル分析

### コード規約
- **Python**: PEP 8準拠
- **JavaScript**: ES6+使用
- **HTML**: セマンティックマークアップ

### Git ワークフロー
```bash
# 基本フロー
git add .
git commit -m "fix: 問題修正"
git push origin main

# コミットメッセージ例
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
style: スタイル調整
```

---
**最終更新**: 2025-07-31  
**サポート**: CLAUDE.md参照
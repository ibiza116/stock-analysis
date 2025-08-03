# 株価分析ツール Pro - ローカル開発ガイド (Phase 3)

## 🚀 クイックスタート

### 必要な環境
- **Python**: 3.11以上
- **Git**: バージョン管理
- **ブラウザ**: Chrome/Firefox推奨
- **GitHub Personal Access Token**: 自動デプロイ用

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

# 5. 環境設定ファイル作成
cp .env.example .env
# .envファイルを編集してGitHub Token等を設定

# 6. アプリケーション起動
python app.py
```

### 🔧 自動デプロイ設定
```bash
# GitHub Personal Access Token設定
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env

# 自動デプロイ実行
./auto_deploy.sh
```

### アクセス
- **ローカル**: http://localhost:5000
- **本番環境**: https://web-production-7ddba.up.railway.app

## 📁 プロジェクト構成 (Phase 3)

```
stock-analysis/
├── app.py                    # メインアプリケーション
├── wsgi.py                   # 本番用エントリーポイント
├── requirements.txt          # Python依存関係
├── Dockerfile               # Railway デプロイ用
├── railway.toml            # Railway 設定
├── CLAUDE.md               # Claude開発メモ（Phase 3更新済み）
├── README.md               # ユーザーマニュアル（Phase 3更新済み）
├── README.local.md         # このファイル
├── .env                    # 環境変数（GitHub Token等）
├── auto_deploy.sh          # 自動デプロイスクリプト 🆕
├── myenv/                  # Python仮想環境 (gitignore済み)
├── templates/
│   └── index.html         # フロントエンド（Phase 3: 白基調UI）
├── analyzers/
│   ├── data_fetcher.py    # 株価データ取得
│   ├── technical.py       # テクニカル分析（Phase 3: 高度指標追加）
│   └── fundamental.py     # ファンダメンタル分析
└── utils/
    └── __init__.py
```

## 🆕 Phase 3の新機能

### 高度テクニカル分析
- **🎯 ボリンジャーバンド**: 20日SMA ± 2σ、スクイーズ検出
- **📊 MACD**: 12/26日EMA、シグナル線、ヒストグラム
- **⚡ ストキャスティクス**: %K/%D線、買われすぎ/売られすぎ
- **📈 出来高分析**: 出来高移動平均比較、異常出来高検出

### UI/UX改善
- **白基調クールデザイン**: 清潔感のある洗練されたUI
- **3タブ構成**: 基本・高度・ファンダメンタル
- **教育コンテンツ**: 各指標の詳細解説付き
- **レスポンシブチャート**: 白基調Plotlyテーマ

### 開発効率化
- **自動デプロイ**: ワンクリックで本番環境更新
- **環境変数管理**: .envファイルでセキュアな設定

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

### 2. Phase 3テスト項目
- **基本テクニカル**: 移動平均線・RSI・基本シグナル
- **高度テクニカル**: 4つの新指標・詳細解説表示
- **ファンダメンタル**: 企業価値・財務分析
- **デザイン**: 白基調UI・3タブ切り替え
- **レスポンシブ**: PC・タブレット対応

### 3. 自動デプロイ
```bash
# 簡単デプロイ
./auto_deploy.sh

# または手動デプロイ
git add .
git commit -m "Phase 3: 新機能追加"
source .env && git push https://$GITHUB_TOKEN@github.com/ibiza116/stock-analysis.git main
```

## 🧪 テスト銘柄・ケース

### 推奨テスト銘柄
| 銘柄コード | 企業名 | テスト目的 |
|----------|-------|-----------|
| **7203** | トヨタ自動車 | 大型株・安定値動き |
| **6758** | ソニーグループ | 値動き大・高度分析向け |
| **9984** | ソフトバンクG | 高ボラティリティ |
| **8306** | 三菱UFJ | 金融株・配当分析 |

### テストケース
1. **正常ケース**: 上記銘柄で全機能動作確認
2. **エラーケース**: 無効銘柄（9999）でエラーハンドリング確認
3. **データ不足ケース**: 短期間（3ヶ月）で指標表示確認
4. **UI/UXテスト**: タブ切り替え・レスポンシブ確認

## 🔧 開発ツール

### デバッグ機能
- **ブラウザコンソール**: F12 → Console（フロントエンドデバッグ）
- **Flask Debug**: `debug=True` (app.py:40)
- **ログ確認**: ターミナル出力
- **Phase 3チェック**: 各タブで新機能動作確認

### よく使うコマンド
```bash
# 依存関係管理
pip install パッケージ名
pip freeze > requirements.txt

# 仮想環境再作成
deactivate
rm -rf myenv  # Linux/Mac
# rmdir /s myenv  # Windows
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt

# Phase 3特有のテスト
python -c "from analyzers.technical import TechnicalAnalyzer; print('Technical analyzer loaded')"
python -c "from analyzers.fundamental import FundamentalAnalyzer; print('Fundamental analyzer loaded')"
```

## 🔐 環境変数設定

### .envファイル設定
```bash
# GitHub Personal Access Token（自動デプロイ用）
GITHUB_TOKEN=ghp_your_token_here

# Basic認証設定
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=your_secure_password

# Flask設定
SECRET_KEY=your_secret_key_here
FLASK_DEBUG=False
PORT=5000
```

### セキュリティ注意事項
- **GitHubトークン**: 絶対にGitにコミットしない
- **.gitignore**: .envファイルを必ず除外
- **権限管理**: トークンは最小権限（repoスコープのみ）

## 📊 API エンドポイント

### `/` (GET)
- **用途**: メインページ表示（Phase 3 UI）
- **認証**: Basic認証必要
- **レスポンス**: HTML（3タブ構成）

### `/health` (GET)
- **用途**: ヘルスチェック（Railway用）
- **認証**: 不要
- **レスポンス**: `{"status": "healthy"}`

### `/analyze` (POST)
- **用途**: 株価分析実行（Phase 3拡張）
- **認証**: Basic認証必要
- **リクエスト**: 
  ```json
  {
    "ticker": "7203",
    "period": "6mo"
  }
  ```
- **レスポンス**: 
  ```json
  {
    "success": true,
    "data": {
      "technical": {
        "chart_data": {...},
        "bollinger_data": {...},  // Phase 3追加
        "macd_data": {...},       // Phase 3追加
        "stoch_data": {...},      // Phase 3追加
        "volume_data": {...}      // Phase 3追加
      },
      "fundamental": {...},
      "stock_info": {...}
    }
  }
  ```

## 🐛 トラブルシューティング

### Phase 3特有の問題

#### 1. 新しいテクニカル指標エラー
```bash
# taライブラリの確認
python -c "from ta.volatility import BollingerBands; print('BollingerBands OK')"
python -c "from ta.trend import MACD; print('MACD OK')"
python -c "from ta.momentum import StochasticOscillator; print('Stochastic OK')"

# 依存関係再インストール
pip install --upgrade ta
```

#### 2. 白基調UIが表示されない
- **ブラウザキャッシュクリア**: Ctrl + F5
- **CSSの確認**: F12 → Elements → styles確認
- **テンプレート確認**: templates/index.html更新確認

#### 3. 3タブが動作しない
- **JavaScript確認**: F12 → Console でエラー確認
- **タブ関数確認**: showTab()関数の動作確認

#### 4. 自動デプロイエラー
```bash
# GitHubトークン確認
echo $GITHUB_TOKEN

# 手動プッシュテスト
git push https://$GITHUB_TOKEN@github.com/ibiza116/stock-analysis.git main

# 権限確認
# GitHub → Settings → Personal access tokens → 権限確認
```

### 一般的な問題

#### 1. `ModuleNotFoundError`
```bash
# 仮想環境確認
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

## 🚀 デプロイメント

### 自動デプロイフロー
1. **ローカル開発・テスト**
2. **自動デプロイ実行**: `./auto_deploy.sh`
3. **GitHub自動プッシュ**
4. **Railway自動ビルド・デプロイ**
5. **本番環境確認**

### Railway本番環境
- **URL**: https://web-production-7ddba.up.railway.app
- **自動デプロイ**: `git push origin main`
- **設定ファイル**: `railway.toml`, `Dockerfile`
- **環境変数**: Railway Dashboard → Variables

### デプロイ確認手順
1. 自動デプロイまたはGitHubプッシュ実行
2. Railway Dashboard でビルド状況確認
3. 本番URLでPhase 3機能テスト
4. 3タブ全ての動作確認

## 📚 開発参考情報

### Phase 3使用ライブラリ
- **Flask**: Webフレームワーク
- **yfinance**: Yahoo Finance API
- **pandas**: データ処理
- **plotly**: インタラクティブチャート（白基調テーマ）
- **ta**: テクニカル分析（Phase 3で拡張）

### コード規約
- **Python**: PEP 8準拠
- **JavaScript**: ES6+使用
- **HTML**: セマンティックマークアップ
- **CSS**: 白基調カラーパレット統一

### Git ワークフロー
```bash
# Phase 3開発フロー
git add .
git commit -m "feat(phase3): ボリンジャーバンド追加"
./auto_deploy.sh

# コミットメッセージ例
feat(phase3): 新機能追加
fix(ui): 白基調デザイン修正
docs: Phase 3ドキュメント更新
style: CSS調整
```

### Phase 3開発のベストプラクティス
1. **機能単位でコミット**: 指標ごとに分けて開発
2. **テスト銘柄確認**: 各機能を複数銘柄でテスト
3. **UI一貫性**: 白基調デザインの統一
4. **レスポンシブ確認**: 各デバイスサイズでテスト
5. **自動デプロイ活用**: 小さな変更も積極的にデプロイ

---
**Phase**: 3.0.0 (高度テクニカル分析 + 白基調UI)  
**最終更新**: 2025-08-03  
**自動デプロイ**: 🔧 設定完了  
**サポート**: CLAUDE.md参照
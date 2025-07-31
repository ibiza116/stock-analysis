# 株価分析ツール - Railway デプロイメント手順

## 準備完了済みファイル
✅ `app.py` - 本番環境対応済み  
✅ `wsgi.py` - Gunicorn用エントリーポイント  
✅ `requirements.txt` - Gunicorn追加済み  
✅ `railway.toml` - Railway設定ファイル  
✅ `nixpacks.toml` - ビルド設定  

## Railway デプロイ手順（推奨）

### 1. GitHubリポジトリ作成
```bash
# Gitリポジトリ初期化
git init
git add .
git commit -m "Initial commit for Railway deployment"

# GitHubにプッシュ（リポジトリ作成済みの場合）
git remote add origin https://github.com/username/repository-name.git
git branch -M main
git push -u origin main
```

### 2. Railway デプロイ
1. https://railway.app でアカウント作成
2. "Deploy from GitHub repo" をクリック
3. 作成したリポジトリを選択
4. 自動的にデプロイが開始されます

### 3. 環境変数設定
Railwayダッシュボードで以下を設定：
- `SECRET_KEY`: `your-secret-key-here`（ランダムな文字列）
- `FLASK_DEBUG`: `False`
- `PORT`: `8000`（自動設定されることが多い）

### 4. カスタムドメイン（オプション）
- Railway設定 → "Domains" → "Generate Domain"
- 独自ドメインも設定可能

## その他のデプロイ方法

### Heroku（代替案）
```bash
# Herokuアプリ作成
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key-here
git push heroku main
```

### Render（代替案）
1. https://render.com でGitHub連携
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn wsgi:app`

## セキュリティ注意事項

### 本番環境チェックリスト
- [ ] `SECRET_KEY`を環境変数で設定
- [ ] `FLASK_DEBUG=False`に設定
- [ ] HTTPSアクセスのみ許可
- [ ] 定期的な依存関係更新

### トラブルシューティング
- **デプロイ失敗**: ログで`requirements.txt`エラー確認
- **500エラー**: 環境変数`SECRET_KEY`未設定の可能性
- **株価取得エラー**: yfinanceのAPI制限の可能性

## コスト目安
- **Heroku**: 無料〜月$7
- **Render**: 無料〜月$7  
- **Railway**: 無料500時間/月

**推奨**: 初回はRender（無料SSL付き）
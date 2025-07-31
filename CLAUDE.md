# 株価分析ツール - Claude開発メモ

## プロジェクト概要
スイング投資向けの日本株式テクニカル分析ツール。Flask + yfinance + Plotlyで構築。

**現在のバージョン**: Phase 1 (基本実装完了)
**稼働状況**: 🚀 本番環境デプロイ済み
**本番URL**: https://web-production-7ddba.up.railway.app
**GitHubリポジトリ**: https://github.com/ibiza116/stock-analysis
**開発環境**: Python仮想環境 (`myenv/`)

## プロジェクト構成

```
stock-analysis-tool/
├── app.py                     # Flaskメインアプリケーション
├── requirements.txt           # 依存ライブラリ（>=バージョン指定）
├── myenv/                     # Python仮想環境
├── templates/
│   └── index.html            # フロントエンド（デバッグ機能付き）
├── static/                   # 静的ファイル用（未使用）
├── analyzers/
│   ├── __init__.py
│   ├── data_fetcher.py       # yfinanceデータ取得
│   └── technical.py          # テクニカル分析（NaN対応済み）
├── utils/
│   └── __init__.py
├── wsgi.py                    # Gunicorn WSGI エントリーポイント
├── Dockerfile                 # Railway デプロイ用
├── railway.toml              # Railway 設定ファイル
├── README.local.md           # ローカル開発用ドキュメント
└── stock-analysis-tool-spec.md  # 元仕様書
```

## セットアップ手順

### 1. 仮想環境作成・有効化
```bash
# 仮想環境作成（既存の場合スキップ）
python -m venv myenv

# 仮想環境有効化
# Windows
myenv\Scripts\activate
# Linux/Mac
source myenv/bin/activate
```

### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 3. アプリケーション起動
```bash
python app.py
```

### 4. ブラウザでアクセス
```
http://localhost:5000
```

## 現在の実装機能

### ✅ 完成済み機能
- **株価データ取得**: yfinanceによる東証銘柄データ取得
- **テクニカル分析**: 
  - 移動平均線（5日、25日、75日）
  - RSI（14日）
  - ゴールデンクロス・デッドクロス検出
- **チャート表示**: Plotlyインタラクティブチャート
- **売買シグナル**: RSIベース + ゴールデンクロス
- **UIデバッグ機能**: コンソールログ出力
- **エラーハンドリング**: NaN値対応、通信エラー処理

### 🔧 実装済み改善点
- **NaN値安全処理**: `_safe_float()`, `_safe_list()`メソッド
- **フロントエンドデバッグ**: console.log追加、エラー詳細表示
- **UI改善**: スタイリング改善、デフォルト銘柄設定（7203）
- **依存関係柔軟化**: requirements.txtで>=バージョン指定

## テスト銘柄
- **7203** (トヨタ) - 大型株、デフォルト設定
- **6758** (ソニー) - 値動きが大きい
- **9984** (ソフトバンクG) - ボラティリティ高
- **8306** (三菱UFJ) - 金融株

## 今後の開発計画

### Phase 2: テクニカル分析拡張
- [ ] ボリンジャーバンド追加
- [ ] MACD指標追加
- [ ] 出来高分析
- [ ] ストキャスティクス

### Phase 3: ファンダメンタル分析
- [ ] PER/PBR比較分析
- [ ] 適正株価計算
- [ ] 配当利回り分析
- [ ] 財務指標取得（EDINET API）

### Phase 4: 高度な機能
- [ ] バックテスト機能
- [ ] ポートフォリオ分析
- [ ] アラート機能
- [ ] データ保存・履歴管理

### Phase 5: UI/UX改善
- [ ] レスポンシブデザイン
- [ ] ダークモード
- [ ] 複数銘柄同時分析
- [ ] レポート出力機能

## 技術的詳細

### 使用ライブラリ
- **Flask**: Webアプリケーションフレームワーク
- **yfinance**: Yahoo Financeデータ取得
- **pandas/numpy**: データ処理
- **ta**: テクニカル分析ライブラリ
- **plotly**: インタラクティブチャート

### データフロー
1. フロントエンド → Flask API (`/analyze`)
2. `data_fetcher.py` → yfinance → 株価データ取得
3. `technical.py` → テクニカル分析実行
4. JSON結果 → フロントエンド → Plotlyチャート描画

### エラーハンドリング
- **NaN値処理**: `_safe_float()`, `_safe_list()`で安全な変換
- **API通信エラー**: try-catch + ユーザーフレンドリーなメッセージ
- **データ不足**: 移動平均線データ不足時の表示制御

## 開発メモ

### 解決済み問題
1. **NaN値エラー**: RSI計算でNaN値が発生 → `_safe_float()`で対応
2. **移動平均線表示**: データ不足時のグラフエラー → null値チェック追加
3. **依存関係**: 固定バージョンによる互換性問題 → >=指定に変更
4. **Railwayデプロイ**: nixpacksビルダーでpipエラー → Dockerfile使用に変更
5. **ポート設定**: 固定ポートとPORT環境変数の競合 → 動的ポート対応
6. **ヘルスチェック**: 起動確認失敗 → `/health`エンドポイント追加

### 注意事項
- 東証銘柄は自動的に`.T`サフィックス追加
- RSI計算には最低14日のデータが必要
- 移動平均線は期間に応じてデータ不足の場合あり

### パフォーマンス
- yfinanceのAPI制限に注意（連続リクエスト）
- データ取得時間: 通常2-5秒
- チャート描画: リアルタイム

## トラブルシューティング

### よくある問題
1. **銘柄コードエラー**: 4桁数字 + 存在確認
2. **データ取得失敗**: 銘柄廃止・上場廃止の場合
3. **移動平均線が表示されない**: データ期間不足

### デバッグ方法
- ブラウザのデベロッパーツール → Console確認
- Flaskのdebug=Trueで詳細エラー表示
- print文でのデータ確認

## デプロイメント

### Railway本番環境
- **URL**: https://web-production-7ddba.up.railway.app
- **プラットフォーム**: Railway (Dockerベース)
- **自動デプロイ**: GitHubプッシュ時に自動実行
- **ヘルスチェック**: `/health` エンドポイント
- **環境変数**: `PORT` (Railway自動設定)

### デプロイ手順
1. コード修正・テスト
2. `git add .` → `git commit` → `git push origin main`
3. Railwayが自動ビルド・デプロイ
4. ヘルスチェック成功で公開完了

### 本番環境設定
```dockerfile
# Dockerfile
FROM python:3.11-slim
# gcc for numpy/pandas compilation
# gunicorn with $PORT environment variable
# logging enabled for debugging
```

## 運用メモ
- **本番環境**: gunicornでproduction実行
- **セキュリティ**: Railway HTTPS自動設定済み
- **モニタリング**: Railwayダッシュボードでログ確認
- **スケーリング**: 必要に応じてRailway Proプラン検討

## 開発ワークフロー
1. **ローカル開発**: `python app.py` (詳細はREADME.local.md参照)
2. **テスト**: ブラウザで動作確認
3. **デプロイ**: GitHubプッシュで自動デプロイ
4. **確認**: 本番URLで動作確認

---
**最終更新**: 2025-07-31
**動作確認**: 🚀 Railway本番環境で動作確認済み
**本番URL**: https://web-production-7ddba.up.railway.app
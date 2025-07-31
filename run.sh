#!/bin/bash
# 株価分析ツール スタートアップスクリプト（Linux/Mac版）

echo "==============================================="
echo "🏢 株価分析ツール スタートアップ（Linux/Mac版）"
echo "==============================================="

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"
echo "📁 作業ディレクトリ: $(pwd)"

# 仮想環境の確認と有効化
if [ -d "myenv" ]; then
    echo "✅ 仮想環境を有効化中..."
    source myenv/bin/activate
    
    echo "📦 依存関係を確認中..."
    pip install -r requirements.txt
    
    echo "🚀 Flaskサーバーを起動中..."
    echo "✅ 株価分析ツールが起動しました!"
    echo "📊 デフォルト銘柄: トヨタ自動車 (7203)"
    echo "🔗 アクセスURL: http://localhost:5000"
    echo ""
    echo "🌐 3秒後にブラウザが自動で開きます..."
    echo "終了するには Ctrl+C を押してください"
    echo ""
    
    # ブラウザを3秒後に開く（バックグラウンド）
    (sleep 3 && python -m webbrowser http://localhost:5000) &
    
    # Flaskアプリを起動
    python app.py
else
    echo "❌ 仮想環境 'myenv' が見つかりません"
    echo "以下のコマンドで仮想環境を作成してください:"
    echo "python -m venv myenv"
fi
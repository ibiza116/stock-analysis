#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
株価分析ツール 簡単スタートアップスクリプト
Flaskサーバーを起動し、自動でブラウザを開く
"""

import os
import sys
import time
import webbrowser
import subprocess
import threading
from pathlib import Path

def open_browser_delayed(url="http://localhost:5000", delay=3):
    """指定秒後にブラウザを開く"""
    def delayed_open():
        time.sleep(delay)
        print(f"🌐 ブラウザでアプリケーションを開いています: {url}")
        webbrowser.open(url)
    
    thread = threading.Thread(target=delayed_open)
    thread.daemon = True
    thread.start()

def main():
    """メイン処理"""
    print("=" * 50)
    print("🏢 株価分析ツール スタートアップ")
    print("=" * 50)
    
    # プロジェクトディレクトリの確認
    project_dir = Path(__file__).parent
    app_file = project_dir / "app.py"
    
    if not app_file.exists():
        print("❌ app.py が見つかりません")
        return
    
    print(f"📁 作業ディレクトリ: {project_dir}")
    print("🚀 Flaskサーバーを起動中...")
    
    # ブラウザの自動起動（3秒後）
    open_browser_delayed()
    
    # app.pyを直接実行
    try:
        print("✅ 株価分析ツールが起動しました!")
        print("📊 デフォルト銘柄: トヨタ自動車 (7203)")
        print("🔗 アクセスURL: http://localhost:5000")
        print("\n終了するには Ctrl+C を押してください\n")
        
        # app.pyを実行
        os.chdir(project_dir)
        import app
        
    except KeyboardInterrupt:
        print("\n🛑 アプリケーションを終了中...")
        print("✅ 正常に終了しました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print("💡 直接 'python app.py' を実行してみてください")

if __name__ == "__main__":
    main()
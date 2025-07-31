#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
株価分析ツール スタートアップスクリプト
Flask サーバーを起動し、自動でブラウザを開く
"""

import os
import sys
import time
import webbrowser
import subprocess
import threading
from pathlib import Path

# プロジェクトディレクトリをPythonパスに追加
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def check_virtual_env():
    """仮想環境の確認"""
    venv_path = project_dir / "myenv"
    if not venv_path.exists():
        print("❌ 仮想環境 'myenv' が見つかりません")
        print("以下のコマンドで仮想環境を作成してください:")
        print("python -m venv myenv")
        return False
    return True

def activate_virtual_env():
    """仮想環境のアクティベート（Windows/Linux対応）"""
    if os.name == 'nt':  # Windows
        activate_script = project_dir / "myenv" / "Scripts" / "activate.bat"
        python_exe = project_dir / "myenv" / "Scripts" / "python.exe"
    else:  # Linux/Mac
        activate_script = project_dir / "myenv" / "bin" / "activate"
        python_exe = project_dir / "myenv" / "bin" / "python"
    
    return python_exe if python_exe.exists() else None

def check_dependencies():
    """依存関係の確認とインストール"""
    python_exe = activate_virtual_env()
    if not python_exe:
        print("❌ 仮想環境のPythonが見つかりません")
        return False
    
    requirements_file = project_dir / "requirements.txt"
    if requirements_file.exists():
        print("📦 依存関係を確認中...")
        try:
            result = subprocess.run([
                str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            if result.returncode != 0:
                print(f"❌ 依存関係のインストールに失敗: {result.stderr}")
                return False
            print("✅ 依存関係の確認完了")
        except Exception as e:
            print(f"❌ 依存関係の確認中にエラー: {e}")
            return False
    return True

def start_flask_server():
    """Flaskサーバーの起動"""
    python_exe = activate_virtual_env()
    if not python_exe:
        return None
    
    app_file = project_dir / "app.py"
    if not app_file.exists():
        print("❌ app.py が見つかりません")
        return None
    
    try:
        print("🚀 Flaskサーバーを起動中...")
        process = subprocess.Popen([
            str(python_exe), str(app_file)
        ], cwd=str(project_dir))
        return process
    except Exception as e:
        print(f"❌ Flaskサーバーの起動に失敗: {e}")
        return None

def wait_for_server(url="http://localhost:5000", max_attempts=30):
    """サーバーの起動を待機"""
    import urllib.request
    
    for attempt in range(max_attempts):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except:
            time.sleep(1)
            print(f"⏳ サーバー起動待機中... ({attempt + 1}/{max_attempts})")
    return False

def open_browser(url="http://localhost:5000"):
    """ブラウザでアプリケーションを開く"""
    def delayed_open():
        time.sleep(3)  # サーバー起動を待つ
        if wait_for_server(url):
            print(f"🌐 ブラウザでアプリケーションを開いています: {url}")
            webbrowser.open(url)
        else:
            print("❌ サーバーの起動を確認できませんでした")
    
    thread = threading.Thread(target=delayed_open)
    thread.daemon = True
    thread.start()

def main():
    """メイン処理"""
    print("=" * 50)
    print("🏢 株価分析ツール スタートアップ")
    print("=" * 50)
    
    # 作業ディレクトリの確認
    print(f"📁 作業ディレクトリ: {project_dir}")
    
    # 仮想環境の確認
    if not check_virtual_env():
        return
    
    # 依存関係の確認
    if not check_dependencies():
        return
    
    # Flaskサーバーの起動
    server_process = start_flask_server()
    if not server_process:
        return
    
    # ブラウザの自動起動
    open_browser()
    
    print("\n✅ 株価分析ツールが起動しました!")
    print("📊 デフォルト銘柄: トヨタ自動車 (7203)")
    print("🔗 アクセスURL: http://localhost:5000")
    print("\n終了するには Ctrl+C を押してください")
    
    try:
        # サーバープロセスの監視
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 アプリケーションを終了中...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ 正常に終了しました")

if __name__ == "__main__":
    main()
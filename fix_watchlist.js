        // ウォッチリスト読み込み
        async function loadWatchlist() {
            const watchlistContainer = document.getElementById('watchlist-content');
            watchlistContainer.innerHTML = '<div class="loading">👁️ ウォッチリストを読み込み中...</div>';
            
            try {
                const response = await fetch('/api/portfolio/watchlist');
                const result = await response.json();
                
                if (result.success && result.data) {
                    const watchlistData = Array.isArray(result.data) ? result.data : [];
                    if (watchlistData.length > 0) {
                        const watchlistHtml = watchlistData.map(item => `
                        <div class="watchlist-item">
                            <div class="watchlist-info">
                                <div class="ticker-name">
                                    <strong>${item.ticker}</strong>
                                    <span class="company-name">${item.company_name || ''}</span>
                                </div>
                                <div class="target-price">
                                    目標価格: ¥${item.target_price?.toLocaleString() || 'N/A'}
                                </div>
                                <div class="category">
                                    カテゴリ: ${item.category || '未分類'}
                                </div>
                            </div>
                            <div class="watchlist-actions">
                                <button onclick="addToPortfolio('${item.ticker}')" class="add-portfolio-btn">📈 追加</button>
                                <button onclick="removeFromWatchlist(${item.id})" class="remove-btn">🗑️</button>
                            </div>
                        </div>
                        `).join('');
                    
                        const watchlistStyle = `
                        <style>
                        .watchlist-item {
                            background: #4b5563;
                            border-radius: 8px;
                            padding: 15px;
                            margin-bottom: 10px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }
                        
                        .watchlist-info .ticker-name {
                            margin-bottom: 5px;
                        }
                        
                        .watchlist-info .company-name {
                            margin-left: 10px;
                            color: #9ca3af;
                            font-size: 14px;
                        }
                        
                        .target-price, .category {
                            font-size: 13px;
                            color: #d1d5db;
                            margin-bottom: 3px;
                        }
                        
                        .watchlist-actions {
                            display: flex;
                            gap: 8px;
                        }
                        
                        .add-portfolio-btn, .remove-btn {
                            background: #3b82f6;
                            color: white;
                            border: none;
                            padding: 6px 12px;
                            border-radius: 4px;
                            font-size: 12px;
                            cursor: pointer;
                        }
                        
                        .remove-btn {
                            background: #ef4444;
                        }
                        </style>
                        `;
                        
                        watchlistContainer.innerHTML = `
                            <div class="watchlist-container">${watchlistHtml}</div>
                            ${watchlistStyle}
                        `;
                    } else {
                        watchlistContainer.innerHTML = `
                            <div class="empty-state">
                                <h4>👁️ ウォッチリストは空です</h4>
                                <p>「銘柄追加」ボタンから注目銘柄を登録してください</p>
                            </div>
                        `;
                    }
                } else {
                    watchlistContainer.innerHTML = `
                        <div class="empty-state">
                            <h4>👁️ ウォッチリストは空です</h4>
                            <p>「銘柄追加」ボタンから注目銘柄を登録してください</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Watchlist load error:', error);
                watchlistContainer.innerHTML = '<div class="error">ウォッチリスト読み込みエラー</div>';
            }
        }
// グローバル変数
let comparisonChart = null;

// チャートのテーマ取得
function getChartTheme() {
    const theme = document.body.getAttribute('data-theme');
    return {
        textColor: theme === 'dark' ? '#e9ecef' : '#212529',
        gridColor: theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        backgroundColor: theme === 'dark' ? '#2d2d2d' : '#ffffff'
    };
}

// DOMが読み込まれた後に実行
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('prediction-form');
    const predictBtn = document.getElementById('predict-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorAlert = document.getElementById('error-alert');
    const resultsContainer = document.getElementById('results-container');
    const welcomeMessage = document.getElementById('welcome-message');

    // フォーム送信イベント
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // バリデーション
        if (!validateForm()) {
            return;
        }

        // UI状態の更新
        showLoading();
        
        // フォームデータの準備
        const formData = new FormData(form);
        
        // Ajax リクエスト
        fetch('/predict/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                displayResults(data);
            } else {
                showError(data.error || '予測の実行に失敗しました。');
            }
        })
        .catch(error => {
            hideLoading();
            showError('通信エラーが発生しました。');
            console.error('Error:', error);
        });
    });

    // 初期状態で全ての月をチェック
    initializeMonthSelection();
});

// フォームバリデーション
function validateForm() {
    const resortSelect = document.getElementById('id_resort');
    const monthCheckboxes = document.querySelectorAll('input[name="months"]:checked');
    
    if (!resortSelect.value) {
        showError('スキー場を選択してください。');
        return false;
    }
    
    if (monthCheckboxes.length === 0) {
        showError('予測したい月を少なくとも1つ選択してください。');
        return false;
    }
    
    return true;
}

// ローディング表示
function showLoading() {
    document.getElementById('loading-spinner').style.display = 'block';
    document.getElementById('error-alert').style.display = 'none';
    document.getElementById('results-container').style.display = 'none';
    document.getElementById('welcome-message').style.display = 'none';
    document.getElementById('predict-btn').disabled = true;
}

// ローディング非表示
function hideLoading() {
    document.getElementById('loading-spinner').style.display = 'none';
    document.getElementById('predict-btn').disabled = false;
}

// エラー表示
function showError(message) {
    const errorAlert = document.getElementById('error-alert');
    const errorMessage = document.getElementById('error-message');
    
    errorMessage.textContent = message;
    errorAlert.style.display = 'block';
    
    // 他のコンテンツを非表示
    document.getElementById('results-container').style.display = 'none';
    document.getElementById('welcome-message').style.display = 'none';
}

// 結果表示
function displayResults(data) {
    // エラーを非表示
    document.getElementById('error-alert').style.display = 'none';
    document.getElementById('welcome-message').style.display = 'none';
    
    // スキー場名を設定
    document.getElementById('resort-name').textContent = data.resort_name;
    
    // 予測テーブルを更新
    updatePredictionTable(data.prediction_table);
    
    // 比較グラフを更新
    updateComparisonChart(data.chart_data);
    
    // 結果コンテナを表示
    const resultsContainer = document.getElementById('results-container');
    resultsContainer.style.display = 'block';
    resultsContainer.classList.add('fade-in');
}

// 予測テーブル更新
function updatePredictionTable(data) {
    const tbody = document.querySelector('#prediction-table tbody');
    tbody.innerHTML = '';
    
    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="fw-bold">${row.date}</td>
            <td class="text-primary fw-bold">${row.predicted}</td>
            <td class="text-muted">${row.lower}</td>
            <td class="text-muted">${row.upper}</td>
        `;
        tbody.appendChild(tr);
    });
}

// 比較グラフ更新
function updateComparisonChart(chartData) {
    const ctx = document.getElementById('comparison-chart').getContext('2d');
    const theme = getChartTheme();
    
    // 既存のチャートを破棄
    if (comparisonChart) {
        comparisonChart.destroy();
    }
    
    // 新しいチャートを作成
    comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '過去10シーズンと未来予測の月別積雪量比較',
                    color: theme.textColor,
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        color: theme.textColor
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '積雪量 (cm)',
                        color: theme.textColor,
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        color: theme.textColor
                    },
                    grid: {
                        color: theme.gridColor
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '月',
                        color: theme.textColor,
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        color: theme.textColor
                    },
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });

    // グローバルアクセス用
    window.comparisonChart = comparisonChart;
}

// 月選択の初期化
function initializeMonthSelection() {
    const monthCheckboxes = document.querySelectorAll('input[name="months"]');
    monthCheckboxes.forEach(checkbox => {
        checkbox.checked = true; // 全ての月を初期選択
    });
}

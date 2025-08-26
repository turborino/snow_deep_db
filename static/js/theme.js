// ダークモード切り替え機能
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const body = document.body;

    // ローカルストレージからテーマ設定を読み込み
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    // テーマ切り替えボタンのクリックイベント
    themeToggle.addEventListener('click', function() {
        const currentTheme = body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    });

    function setTheme(theme) {
        body.setAttribute('data-theme', theme);
        
        // アイコンの切り替え
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-sun';
            themeToggle.title = 'ライトモード切り替え';
        } else {
            themeIcon.className = 'fas fa-moon';
            themeToggle.title = 'ダークモード切り替え';
        }
        
        // Chart.jsのテーマも更新（既存のチャートがある場合）
        updateChartTheme(theme);
    }

    function updateChartTheme(theme) {
        // グローバルにアクセス可能なチャートが存在する場合、テーマを更新
        if (window.comparisonChart) {
            const textColor = theme === 'dark' ? '#e9ecef' : '#212529';
            const gridColor = theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
            
            window.comparisonChart.options.plugins.title.color = textColor;
            window.comparisonChart.options.plugins.legend.labels.color = textColor;
            window.comparisonChart.options.scales.y.title.color = textColor;
            window.comparisonChart.options.scales.y.ticks.color = textColor;
            window.comparisonChart.options.scales.y.grid.color = gridColor;
            window.comparisonChart.options.scales.x.title.color = textColor;
            window.comparisonChart.options.scales.x.ticks.color = textColor;
            window.comparisonChart.options.scales.x.grid.color = gridColor;
            
            window.comparisonChart.update();
        }
    }

    // テーマ変更をグローバルで利用可能にする
    window.updateChartTheme = updateChartTheme;
});

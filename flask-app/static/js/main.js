// This file contains JavaScript code for client-side functionality.

document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript is loaded and ready to go!');

    // Example of a simple interaction
    const button = document.getElementById('myButton');
    if (button) {
        button.addEventListener('click', function() {
            alert('Button was clicked!');
        });
    }
});

function getChartOptions() {
    const dark = document.body.classList.contains('dark-mode');
    return {
        chart: {
            type: 'line',
            backgroundColor: 'transparent'
        },
        title: {
            text: 'Historical Stock Prices for {{ stock_symbol }} (10 Years)',
            style: { color: dark ? '#b3baff' : 'var(--primary)' }
        },
        xAxis: {
            type: 'datetime',
            title: { text: 'Date', style: { color: dark ? '#b3baff' : 'inherit' } },
            labels: { style: { color: dark ? '#b3baff' : 'inherit' } },
            gridLineColor: dark ? '#353945' : '#e6e8ec'
        },
        yAxis: {
            title: { text: 'Price (USD)', style: { color: dark ? '#b3baff' : 'inherit' } },
            labels: { style: { color: dark ? '#b3baff' : 'inherit' } },
            gridLineColor: dark ? '#353945' : '#e6e8ec'
        },
        series: [{
            name: "{{ stock_symbol }}",
            data: {{ chart_data|tojson|safe }},
            color: dark ? "#b3baff" : "#0033a0",
            lineWidth: 3,
            marker: { enabled: false }
        }],
        credits: { enabled: false }
    };
}
function renderChart() {
    Highcharts.stockChart('stock-chart', getChartOptions());
}
document.addEventListener('DOMContentLoaded', renderChart);
document.getElementById('toggleModeBtn').onclick = () => {
    setMode(!document.body.classList.contains('dark-mode'));
    setTimeout(renderChart, 200);
};
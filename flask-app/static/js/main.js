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

const vars = window.stockWizVars || {};
// Use vars.stockSymbol, vars.chartData, etc. in your chart code

function getChartOptions() {
    const dark = document.body.classList.contains('dark-mode');
    const vars = window.stockWizVars || {};
    const predictedPriceNum = Number(vars.predictedPrice); // <-- Add this line
    return {
        chart: {
            type: 'line',
            backgroundColor: 'transparent'
        },
        title: {
            text: `Historical Stock Prices for ${vars.stockSymbol} (10 Years)`,
            style: { color: dark ? '#b3baff' : 'var(--primary)' }
        },
        xAxis: {
            type: 'datetime',
            title: { text: 'Date', style: { color: dark ? '#b3baff' : 'inherit' } },
            labels: { style: { color: dark ? '#b3baff' : 'inherit' } },
            gridLineColor: dark ? '#353945' : '#e6e8ec',
            plotLines: (!isNaN(predictedPriceNum)) ? [{
                value: vars.predictedTimestamp,
                color: '#007bff',
                width: 2,
                dashStyle: 'Dash',
                label: {
                    text: `Predicted Price: $${predictedPriceNum.toFixed(2)}`,
                    align: 'left',
                    style: { color: '#007bff' }
                }
            }] : []
        },
        yAxis: {
            title: { text: 'Price (USD)', style: { color: dark ? '#b3baff' : 'inherit' } },
            labels: { style: { color: dark ? '#b3baff' : 'inherit' } },
            gridLineColor: dark ? '#353945' : '#e6e8ec'
        },
        series: [
            {
                name: vars.stockSymbol,
                data: vars.chartData,
                color: dark ? "#b3baff" : "#0033a0",
                lineWidth: 3,
                marker: { enabled: false }
            },
            {
                name: "Linear Trend",
                data: vars.regressionData,
                color: "orange",
                dashStyle: "ShortDash",
                lineWidth: 2,
                marker: { enabled: false }
            },
            ...( !isNaN(predictedPriceNum) ? [{
                name: "Predicted Next Price",
                type: "scatter",
                data: [
                    [vars.predictedTimestamp, predictedPriceNum]
                ],
                color: "red",
                marker: { symbol: "circle", radius: 6 },
                tooltip: { valueDecimals: 2, valuePrefix: "$" }
}] : [])
        ],
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
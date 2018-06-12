    // Create the chart
    Highcharts.chart('chart-energy-dr', {
        chart: {
            type: 'column'
        },
        title: {
            text: 'Total Energy Consumption'
        },
        legend: {
            layout: 'vertical',
            align: 'left',
            verticalAlign: 'top',
            x: 150,
            y: 100,
            floating: true,
            borderWidth: 1,
            backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'
        },
        xAxis: {
            categories: [
                '12a',
                '1a',
                '2a',
                '3a',
                '4a',
                '5a',
                '6a',
                '7a',
                '8a',
                '9a',
                '10a',
                '11a',
                '12p',
                '1p',
                '2p',
                '3p',
                '4p',
                '5p',
                '6p',
                '7p',
                '8p',
                '9p',
                '10p',
                '11p',
                '12p'
            ],
            plotBands: [{ // visualize the weekend
                from: 14,
                to: 18,
                color: '#F1F8E9'
            }]
        },
        yAxis: {
            title: {
                text: 'kWh'
            }
        },
        tooltip: {
            shared: true,
            valueSuffix: ' kWh'
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            areaspline: {
                fillOpacity: 0.5
            }
        },
        legend: {
            enabled: false
        },
        series: [{
            name: 'Current Energy Usage',
            color: '#AED581',
            data: [3, 4, 3, 5, 4, 10, 12, 13, 14, 13, 15, 14, 10, 12, 16, 17, 19, 16, 18, 15, 17, 23, 21, 21, 18]
        }, {
            name: 'Recommended Energy Usage',
            color: '#8BC34A',
            data: [2, 3, 3, 3, 2, 8, 11, 11, 12, 10, 12, 13, 7, 10, 13, 13, 15, 15, 16, 14, 13, 20, 17, 19, 17]
        }]
    });
           
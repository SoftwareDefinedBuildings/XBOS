// functions for plotting data

var updateGraph = function(name, data) {
    //TODO: fix time
    var chart;
    nv.addGraph(function() {
        chart = nv.models.lineChart()
                  .margin({left: 50, right: 50})
                  .height(400)
                  .useInteractiveGuideline(true)
                  .showYAxis(true)
                  .showXAxis(true)
                ;
        chart.lines.xScale(d3.time.scale());
        chart.xAxis
             .axisLabel('Time')
             .tickFormat(function(d) { return d3.time.format("%H:%M:%S")(d); })
             ;

        chart.yAxis
             .axisLabel('Unit')
             .tickFormat(d3.format('0.2f'))
             ;

        var points = _.map(data, function(point) {
            return {x: moment(point[0]).toDate(), y: point[1]}
        });

        var myData = [
            {
                values: points,
                key: name
            }
        ];

        var plotID = "#plot"+name;
        var select = plotID + " svg";
        d3.select(select)
          .datum(myData)
          .call(chart)
          ;

        nv.utils.windowResize(function() { chart.update() });
        return chart;
    });
};

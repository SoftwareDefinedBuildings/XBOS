// functions for plotting data

var updateGraph = function(name, units, data) {
    var chart;
    nv.addGraph(function() {
        chart = nv.models.lineChart()
                  .margin({left: 60, right: 50})
                  .height(400)
                  .useInteractiveGuideline(true)
                  .showLegend(true)
                  .showYAxis(true)
                  .showXAxis(true)
                ;
        chart.lines.xScale(d3.time.scale());
        chart.xAxis
             .axisLabel('Time')
             .tickFormat(function(d) { return d3.time.format("%H:%M:%S")(d); })
             ;

        chart.yAxis
             .axisLabel(units)
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

/*
 * Generic plotting component. Requires the following props
 * {
 *  length: # of seconds from now that the plot should be generated for
 *  name: <unique name for the plot>
 *  height: height of the plot. by default it will expand to full width
 *  streams: [
 *      {
 *          uuid: <uuid to plot>
 *          units: if null, it will query
 *          color: <CSS color code>
 *      }
 *           ]
 * }
 */
var Plot = React.createClass({
    getInitialState: function() {
        var data = {};
        _.each(this.props.streams, function(stream) {
            data[stream.uuid] = [];
        });
        return {data: data}
    },
    componentWillMount: function () {
        // we assign this.fetchData to be the callback for fetching the units for
        // each of the streams, but it will only be called once after they all complete
        this.fetchData();
    },
    componentWillReceiveProps: function(prevProps) {
        this.fetchData();
        //return prevProps.streams.length != this.props.streams.length;
    },
    updateGraph: function() {
        var self = this;
        var chart;
        nv.addGraph(function() {
            chart = nv.models.lineChart()
                      .margin({left: 50, right: 50})
                      .height(200)
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
                 .axisLabel("unit")
                 .tickFormat(d3.format('0.2f'))
                 ;
            var datum = [];
            _.each(self.state.data, function(datachunk) {
                datum.push(datachunk);
            });
            d3.select("#plot"+self.props.name.replace(" ","")+" svg")
              .datum(datum)
              .call(chart)
              ;
            nv.utils.windowResize(function() { chart.update() });
            return chart;

        });
    },
    fetchData: function() {
        var self = this;
        _.each(this.props.streams, function(stream) {
            if (stream.uuid == null) { return; }
            run_query2("select data in (now -"+self.props.length+"s, now) as ms where uuid = '"+stream.uuid+"';",
                function(data) {
                    if (data.length == 0) { return; }
                    var streamdata = self.state.data;
                    var readings = data[0].Readings;
                    var points = _.map(readings, function(point) {
                        return {x: moment(point[0]).toDate(), y: point[1]}
                    });
                    var myData =  {
                            values: points,
                            key: stream.name,
                            color: stream.color
                            };
                    streamdata[stream.uuid] = myData;
                    self.setState({data: streamdata});
                    self.updateGraph();
                },
                function(err) {
                    console.error("ERR fetching data", err)
                }
            )
        });
    },
    render: function() {
        self.updateGraph();
        return (
            <div className="plot">
                <div style={{height: "200px"}} id={"plot"+this.props.name.replace(" ","")}>
                    <svg></svg>
                </div>
            </div>
        )
    }
});

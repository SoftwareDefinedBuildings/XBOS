Template.pointDetail.rendered = function() {

    var n = 500,
        duration = 750,
        now = new Date(Date.now() - duration),
        count = 0

    var margin = {top: 6, right: 0, bottom: 20, left: 30},
        width = 860 - margin.right - margin.left,
        height = 420 - margin.top - margin.bottom;

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d, i) { return x(time[i]); })
        .y(function(d, i) { return y(d); });
    
    var svg = d3.select(".pointDetailContainer").append("p").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .style("margin-left", margin.left + "px")
        .style("margin-top", "20px")
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg.append("defs").append("clipPath")
        .attr("id", "clip")
      .append("rect")
        .attr("width", width)
        .attr("height", height);

    var xaxis = svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(x.axis = d3.svg.axis().scale(x).orient("bottom"));

    var yaxis = svg.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(0,0)")
        .call(y.axis = d3.svg.axis().scale(y).orient("left"));

    var path = svg.append("g")
        .attr("clip-path", "url(#clip)")
        .append("path")
        .attr("class", "line");

    var that = this;
    var data, time;
    var restrict = 'uuid="'+ this.data.uuid + '"';

    Meteor.call("latest", restrict, n, function(err, res){
      var readings = _.zip.apply(_, res[0].Readings);
      time = _.map(readings[0], function(d){
        var date = new Date(d);
        return date;
      });
      data = readings[1];
      path.data([data])
      tick();
    });

    function tick() {
       
        p = Points.findOne({uuid: that.data.uuid});
        if (p.value !== undefined){
            now = new Date(1000 * p.time);
            time.push(now);
            data.push(p.value);

            x.domain([time[0], time[n-2]]);
            y.domain([d3.min(data), d3.max(data)]);

            // push the accumulated count onto the back, and reset the count
            count = 0;

            // redraw the line
            svg.select(".line")
                .attr("d", line)
                .attr("transform", null);

            // slide the x-axis left
            xaxis.transition()
                .duration(duration)
                .ease("linear")
                .call(x.axis);

            yaxis.transition()
                .duration(duration)
                .ease("linear")
                .call(y.axis);

            // slide the line left
            path.transition()
                .duration(duration)
                .ease("linear")
                .attr("transform", "translate(" + x(time[1]) + ")")
                .each("end", tick);

            // pop the old data point off the front
            time.shift();
            data.shift();
         
          }
      }
}

Template.pointDetail.rendered = function() {

    var n = 243,
        duration = 750,
        now = new Date(Date.now() - duration),
        count = 0,
        data = d3.range(n).map(function() { return 0; });

    var margin = {top: 6, right: 0, bottom: 20, left: 40},
        width = 960 - margin.right,
        height = 120 - margin.top - margin.bottom;

    var x = d3.time.scale()
        .domain([now - (n - 2) * duration, now - duration])
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d, i) { return x(now - (n - 1 - i) * duration); })
        .y(function(d, i) { return y(d); });

    var svg = d3.select(".pointDetailContainer").append("p").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .style("margin-left", -margin.left + "px")
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
        .data([data])
        .attr("class", "line");

    var that = this;

    tick();

    function tick() {

        p = Points.findOne({uuid: that.data.uuid});
        if (p.value !== undefined){
            now = new Date();
            data.push(p.value);

            x.domain([now - (n - 2) * duration, now - duration]);
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
                .attr("transform", "translate(" + x(now - (n - 1) * duration) + ")")
                .each("end", tick);

            // pop the old data point off the front
            data.shift();

          }
      }
}

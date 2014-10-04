(function($) {
    $(document).ready(function() {

        // plot demand data
        d3.json("/demanddata", function(err, data) {
            var margin = {
                top: 50,
                right: 50,
                bottom: 50,
                left: 50
              },
              width = 1600,
              height = 400;
            
            var x = d3.time.scale()
                .range([0, width]);
            var y = d3.scale.linear()
                .range([height, 0]);
            var xAxis = d3.svg.axis()
                .scale(x)
                .tickSubdivide(true)
                .orient("bottom");
            var yAxis = d3.svg.axis()
                .scale(y)
                .orient("left");

            var line = d3.svg.line()
                .x(function(d) { return x(d.date); })
                .y(function(d) { return y(d.value); });

            var svg = d3.select("#totaldemandplot").append("svg")
                .attr("width", width+margin.left+margin.right)
                .attr("height", height+margin.top+margin.bottom)
                .append("g")
                .attr("transform","translate("+margin.left+","+margin.top+")");
            if (err) {
                console.log("ERROR", err);
            }
            console.log("main svg",svg);
            data = data['data'].sort(function(a,b) { return b.date - a.date; });
            console.log(data);
            data.forEach(function(d) {
                d.date = new Date(d['date']*1);
                d.value = d['value'];
            });

            x.domain(d3.extent(data, function(d) { return d.date; }));
            y.domain(d3.extent(data, function(d) { return d.value; }));
            svg.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height + ")")
              .call(xAxis);

            svg.append("g")
              .attr("class", "y axis")
              .call(yAxis)
              .append("text")
              .attr("transform", "rotate(-90)")
              .attr("y", 6)
              .attr("dy", ".71em")
              .style("text-anchor", "end")
              .text("kW");

            svg.append("path")
              .datum(data)
              .attr("class", "line")
              .attr("d", line);
        });

        $('.dailyplot').each(function(idx) {
            var val = $( this );
            var key = val.data("key");
            var zone = val.data("zone");
            d3.json("/zonedata/"+key+"/"+zone, function(err, data) {
                var margin = {
                    top: 10,
                    right: 50,
                    bottom: 20,
                    left: 50
                  },
                  width = 400,
                  height = 200;
                var x = d3.time.scale()
                    .range([0, width]);
                var y_demand = d3.scale.linear()
                    .range([0, height]);
                var y_temp = d3.scale.linear()
                    .range([height, 0]);
                var xAxis = d3.svg.axis()
                    .scale(x)
                    .orient("bottom");
                var y_demandAxis = d3.svg.axis()
                    .scale(y_demand)
                    .orient("right");
                var y_tempAxis = d3.svg.axis()
                    .scale(y_temp)
                    .orient("left");
                var demand_line = d3.svg.line()
                    .x(function(d) { return x(d.date); })
                    .y(function(d) { return y_demand(d.value); });
                var temp_line = d3.svg.line()
                    .x(function(d) { return x(d.date); })
                    .y(function(d) { return y_temp(d.value); });

                var svg = d3.select("#"+key+"_"+zone).append("svg")
                    .attr("width", width+margin.left+margin.right)
                    .attr("height", height+margin.top+margin.bottom)
                  .append("g")
                    .attr("transform","translate("+margin.left+","+margin.top+")");
                data_hvac_state = data['hvac_state'].sort(function(a,b) { return b.date - a.date; });
                data_hvac_state.forEach(function(d) {
                    d.date = moment(new Date(d['date']*1)).add(7,'hours').toDate();
                    d.value = d['value'];
                });
                data_temp_heat = data['temp_heat'].sort(function(a,b) { return b.date - a.date; });
                data_temp_heat.forEach(function(d) {
                    d.date = moment(new Date(d['date']*1)).add(7,'hours').toDate();
                    d.value = d['value'];
                });
                data_temp_cool = data['temp_cool'].sort(function(a,b) { return b.date - a.date; });
                data_temp_cool.forEach(function(d) {
                    d.date = moment(new Date(d['date']*1)).add(7,'hours').toDate();
                    d.value = d['value'];
                });
                data_temp = data['temp'].sort(function(a,b) { return b.date - a.date; });
                data_temp.forEach(function(d) {
                    d.date = moment(new Date(d['date']*1)).add(7,'hours').toDate();
                    d.value = d['value'];
                });
                var minx = moment(d3.min(data_temp, function(d) { return Math.min(d.date);}));
                var start = minx.startOf('day').toDate();
                var minx = moment(d3.min(data_temp, function(d) { return Math.min(d.date);}));
                var end = minx.endOf('day').toDate();
                x.domain([start,end]);
                //TODO: bring in demand data
                //y_demand.domain(d3.extent(data, function(d) { return d.value; }));
                var miny_a = d3.min(data_temp, function(d) { return Math.min(d.value); });
                var maxy_a = d3.max(data_temp, function(d) { return Math.max(d.value); });
                var miny_b = d3.min(data_temp_cool, function(d) { return Math.min(d.value); });
                var maxy_b = d3.max(data_temp_cool, function(d) { return Math.max(d.value); });
                var miny_c = d3.min(data_temp_heat, function(d) { return Math.min(d.value); });
                var maxy_c = d3.max(data_temp_heat, function(d) { return Math.max(d.value); });
                var extent = d3.extent([miny_a,miny_b,miny_c,maxy_b,maxy_c,maxy_a])
                y_temp.domain([extent[0]-5, extent[1]+5]);
                //y_temp.domain([10 + d3.max(data_temp_cool, function(d) {return Math.max(d.value)}), d3.min(data_temp_heat,function(d) {return Math.min(d.value)}) - 10]);
                svg.append("g")
                  .attr("class", "x axis")
                  .attr("transform", "translate(0," + height + ")")
                  .call(xAxis);

                svg.append("g")
                  .attr("class", "y axis")
                  .call(y_tempAxis)
                  .append("text")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 6)
                  .attr("dy", ".71em")
                  .style("text-anchor", "end")
                  .text("F");

                svg.append("path")
                  .datum(data_temp)
                  .attr("class", "temp")
                  .attr("d", temp_line);
                svg.append("path")
                  .datum(data_temp_heat)
                  .attr("class", "temp_heat")
                  .attr("d", temp_line);
                svg.append("path")
                  .datum(data_temp_cool)
                  .attr("class", "temp_cool")
                  .attr("d", temp_line);
                svg.append("text")
                  .attr("x", (width / 2))
                  .attr("y", margin.top)
                  .attr("text-anchor", "middle")

                  .style("font-size", "16px")
                  .text(zone);
              });
        });
        
        $('.histogram_disaggregate').each(function(idx) {
            var val = $( this );
            var zone = val.data("zone");
            d3.json("/histogram/"+zone, function(err, data) {
              if (err) {
                return true;
              }
              data = data.data;
              var margin = {top: 10, right:30, bottom: 30, left: 30},
                  width = 400, height = 200;
              var x = d3.scale.linear()
                  .domain(d3.extent(data))
                  .range([0, width]);
              var histdata = d3.layout.histogram()
                      .bins(x.ticks(10))(data);

              var y = d3.scale.linear()
                  .domain([0, d3.max(histdata, function(d) { return d.y; })])
                  .range([height,0]);

              var xAxis = d3.svg.axis()
                  .scale(x)
                  .orient("bottom");

              var svg = d3.select("#"+zone+"_hist").append("svg")
                  .attr("width", width+margin.left+margin.right)
                  .attr("height", height+margin.top+margin.bottom)
                .append("g")
                  .attr("transform", "translate("+margin.left+","+margin.top+")");
              
              var bar = svg.selectAll(".bar")
                  .data(histdata)
                .enter().append("g")
                  .attr("class", "bar")
                  .attr("transform", function(d) { return "translate(" + x(d.x) + "," + y(d.y) + ")";});
              
              bar.append("rect")
                  .attr("x", 1)
                  .attr("width", x(histdata[0].dx) - 1)
                  .attr("height", function(d) { return height - y(d.y); });

              bar.append("text")
                  .attr("dy", ".75em")
                  .attr("y", 6)
                  .attr("x", x(histdata[0].dx / 2))
                  .attr("text-anchor", "middle")
                  .text("");

              svg.append("g")
                  .attr("class", "x axis")
                  .attr("transform", "translate(0,"+height+")")
                  .call(xAxis);
            });
        });

    });
})(jQuery);

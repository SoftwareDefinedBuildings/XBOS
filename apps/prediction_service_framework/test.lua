request = {predstart = "2018-07-10T00:00:00Z", predend = "2018-07-11T00:00:00Z", resolution="1h"}
bw.subscribe("scratch.ns/s.predictions/myid/i.hvac/signal/response", "2.0.0.0", function(uri, msg)
    print(bw.dumptable(msg['EastZone']['inside']))
end)
bw.publish("scratch.ns/s.predictions/myid/i.hvac/slot/request", "2.0.0.0", request)
bw.sleep(10)

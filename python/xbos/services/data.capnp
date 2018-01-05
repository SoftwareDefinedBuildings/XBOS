@0xd213afc571b92e25;

struct Stream {
    times @0: List(Int64);
    values @1: List(Float64);
}

struct StreamCollection {
    times @0: List(Int64);
    streams @1: List(Stream);
}

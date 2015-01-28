# OpenBAS v2.0

The primary motivation for a rewrite of the OpenBAS front-end is to incorporate
the lessons learned in implementing OpenBAS v1 on top of Meteor, Mongo, and the
original sMAP archiver.

## Mongo Data Model

Meteor's MongoDB-centric pipeline for reactive applications made things more
complicated than they needed to be. MongoDB was only incorporated into OpenBAS
because Meteor required it in order to do reactive updates to the DOM. The
Meteor server mainly served as a manual pub/sub broker between the sMAP
archiver's HTTP API and MongoDB. This required a number of transformations of
the data as it was sliced, keys were reassigned and portions of data were
placed into multiple MongoDB collections in order to make all of the Meteor
components happy with valid data.

Meteor (at least at the time of writing of OpenBAS, though I don't imagine it
has changed much in this aspect since then) did not have a clear and idiomatic
way of defining modular, nestable, reusable components. The namespaces of each
of the components remained discrete, so nested components had to retrieve data
from their parents in hacky ways (global variable, put another record into a
Mongo collection, access infinitely-nested JS prototypes, etc). Dynamically
inserting new components into the DOM often meant lots of callbacks.
Additionally, all dynamic data updates were doen via Mongo, so the data on the
rendered page did not necessarily affect nor represent what was actually in
sMAP until the server-side polling process of sMAP queries ensured consistency.
This also made code difficult to write correctly, as each additional component
or feature required the programmer to know exactly where new data had to be
placed in order for all the components to remain consistent as well as any
side-effects of doing so.as well as any side-effects of doing so.

What's needed in OpenBAS is a distinction between application data and the
building profile. The building profile is the set of timeseries readings and
metadata documents that consist the physical installation that OpenBAS is
representing. Application data is anything that exists above that. This
distinction was *possible* with the original Meteor implementation of OpenBAS,
but the execution left it too easy to be sloppy.

## ReactJS + WebSockets

ReactJS is a JS library for building user interfaces. It concerns itself
entirely with aspects of the UI, and does not make any assumptions about the
rest of the stack below it. This gives us much more freedom in choosing the
mechanisms for real-time data delivery to the client and allows us to build the
OpenBAS frontend directly over the sMAP archiver while still having a separate
application-specific server program.

Giles, the new sMAP archiver, provides flexibility in the interface for
interaction, meaning we can use a technology such as WebSockets to provide
streams of data to individual components, and have that data trickle down into
the nested components as necessary.

$(document).ready(function() {
                // initialize the external events
        // -----------------------------------------------------------------

        $('#external-events .fc-event').each(function() {

        //   // store data so the calendar knows to render an event upon drop
          $(this).data('event', {
            title: $.trim($(this).text()), // use the element's text as the event title
            stick: true, // maintain when user navigates (see docs on the renderEvent method)
            color: $(this).data('color') // maintain the event color

          });

          // make the event draggable using jQuery UI
          $(this).draggable({
            zIndex: 999,
            revert: true,      // will cause the event to go back to its
            revertDuration: 0  //  original position after the drag
          });

        });

        // initialize the calendar
        // -----------------------------------------------------------------


          $('#calendar').fullCalendar({

            header: false,
            // defaultDate: '2017-10-12',
            navLinks: false, // can click day/week names to navigate views
            defaultView: "agendaWeek",
            columnFormat: "ddd",

            editable: true,
            droppable: true, // this allows things to be dropped onto the calendar
            

          });
      });
$(document).ready(function() {

    var weekClipBoard = null;
    var weekClipBoardOrigin = null;

    $("#btnCopyWeek").click(function() {
        $("#btnPasteWeek").prop('disabled', false);
        weekClipBoardOrigin = $('#calendar').fullCalendar('getDate');
        weekClipBoard = $('#calendar').fullCalendar('clientEvents', function(event) {
            return event.start.isoWeek() == weekClipBoardOrigin.isoWeek() &&
                event.start.year() == weekClipBoardOrigin.year();
        });
    });
    $("#btnPasteWeek").click(function() {
        var now = $('#calendar').fullCalendar('getDate');
        weekClipBoard.forEach(function(original) {
            var event = {
                title : original.title,
                start : moment(original.start),
                end : moment(original.end),
                allDay: false,
                id: "__NEW_EVENT",
                backgroundColor: original.backgroundColor
            };
            event.start.year(now.year());
            event.start.isoWeek(now.isoWeek());
            event.end.year(now.year());
            event.end.isoWeek(now.isoWeek());
            $.get("/newperiod/"+event.start.unix()+"/"+event.end.unix()+"/"+event.title,
                  function(data) {
                      event.id = data;
                      $('#calendar').fullCalendar('renderEvent', event, true);
                  });
        });
    });

    $("#btnPdfReport").click(function() {
        week = $('#calendar').fullCalendar('getDate');
        window.open("/get_pdf_report/"+week.unix(), '_blank');
    });

    $("#btnOptions").click(function() {
        $('#optionsDialog').modal();
    });

    $("#btnAddWorkPlace").click(function() {
        name = $('#wpName').val();
        color = $('#wpColor').val();
        $.get("/newworkplace/"+name+"/"+color,
              function(data) {
                  if (data == 'OK') {
                      $('#lstWorkPlaces').append('<li class="list-group-item"><span style="color:'+color+';font-weight:bold">'+name+'<span></li>');
                      $('#modalActivity').append($('<option>', {
                          value: name+'|'+color,
                          text: name
                      }));
                      $('#modalActivity').selectpicker('refresh');
                      $('#wpName').val('');
                      $('#wpColor').val('');
                  }
              });
    });


    var currentEvent = null;

    $("#modalDelete").click(function() {
        $.get("/rmperiod/"+currentEvent.id,
              function(data) {
                  if (data == 'OK') {
                      $("#calendar").fullCalendar('removeEvents', currentEvent.id);
                  }
                  currentEvent = null;
                  $('#eventDialog').modal('hide');
              });
    });

    $("#modalConfirm").click(function() {
        var data = $("#modalActivity").val().split("|");
        currentEvent.title = data[0];
        currentEvent.backgroundColor = data[1];
        if (currentEvent.id == "__NEW_EVENT") {
            $.get("/newperiod/"+currentEvent.start.unix()+"/"+currentEvent.end.unix()+"/"+data[0],
                  function(data) {
                      currentEvent.id = data;
                      $('#calendar').fullCalendar('renderEvent', currentEvent, true);
                      currentEvent = null;
                      $('#eventDialog').modal('hide');
                  });
        }
        else {
           $.get("/editperiod/"+currentEvent.id+"/"+currentEvent.start.unix()+"/"+currentEvent.end.unix()+"/"+data[0],
                  function(data) {
                      if (data != "OK") {
                          alert("Si e' verificato un errore, riprovare! L'errore riportato e': " + data);
                      }
                      else {
                          $('#calendar').fullCalendar('updateEvent', currentEvent);
                          currentEvent = null;
                          $('#eventDialog').modal('hide');
                      }
                  });
        }
    });

    $('#calendar').fullCalendar({
        locale: 'it',
        allDaySlot: false,
        weekends: false,
        minTime: "12:00:00",
        maxTime: "22:00:00",
        selectable: true,
        slotDuration: "00:15:00",
        timezone: 'UTC',
        select: function(start, end, jsEvent, view) {
            currentEvent = {
                title : null,
                start : start,
                end : end,
                allDay: false,
                id: "__NEW_EVENT",
                backgroundColor: null
            };
            $('#eventDialogTitle').html("Nuova Attivit&agrave;");
            $('#modalDelete').hide();
            $('#eventDialog').modal();
        },
        header: {
	    left: 'prev,next today',
	    center: 'title',
	    right: ''
	},
	defaultView: 'agendaWeek',
	editable: true,
        themeSystem: 'bootstrap3',
        bootstrapGlyphicons: {
            close: 'glyphicon-remove',
            prev: 'glyphicon-chevron-left',
            next: 'glyphicon-chevron-right',
            prevYear: 'glyphicon-backward',
            nextYear: 'glyphicon-forward'
        },
        // eventRender: function(event, element) {
        //     element.append(s);
        // },
        //        height: 650,
        eventClick: function(event) {
            currentEvent = event;
            $('#eventDialogTitle').html("Modifica Attivit&agrave;");
            $('#modalDelete').show();
            var value = event.title + "|" + event.backgroundColor;
            $("#modalActivity").val(value).change();;

            $('#eventDialog').modal();
        },
        eventDrop: function(event, delta, revertFunc) {
            $.get("/chperiod/"+event.id+"/"+event.start.unix()+"/"+event.end.unix(),
                  function(data) {
                      if (data != "OK") {
                          alert("Si e' verificato un errore, riprovare! L'errore riportato e': " + data);
                          revertFunc();
                      }
              });
        },
        eventResize: function(event, delta, revertFunc) {
            $.get("/chperiod/"+event.id+"/"+event.start.unix()+"/"+event.end.unix(),
                  function(data) {
                      if (data != "OK") {
                          alert("Si e' verificato un errore, riprovare! L'errore riportato e': " + data);
                          revertFunc();
                      }
              });
        },
        contentHeight: 'auto',
	events: allEvents
    });
});

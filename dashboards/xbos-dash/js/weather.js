$(document).ready(function() {  
  getWeather(); //Get the initial weather.
  setInterval(getWeather, 600000); //Update the weather every 10 minutes.
});

function getWeather() {
  $.simpleWeather({
    location: '94703',
    unit: 'f',
    success: function(weather) {
      html = '<i class="icon-'+weather.code+'"></i>' + weather.temp+'&deg;'+weather.units.temp+', ' + weather.currently;
      //html += '<ul><li>'+weather.city+', '+weather.region+'</li>';
      //html += '<li class="currently">''</li></ul>';
      //html += '<li>'+weather.alt.temp+'&deg;C</li></ul>';
  
      $("#weather").html(html);
    },
    error: function(error) {
      $("#weather").html('<p>'+error+'</p>');
    }
  });
}

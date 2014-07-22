Meteor.methods({
  // in the client: 
  // Meteor.call('method_name', param, param, function(err, data){ ... });

  foo: function(){
    return 'bar';
  },

  bar: function(a, b){
    return a + b;
  },

});

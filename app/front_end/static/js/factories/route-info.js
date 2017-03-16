'use strict';

postOrdersApp.factory('RouteInfo', ['Restangular', function(Restangular) {
    return {
        get: function(route) {
            return Restangular.one('route-info', route).get();
        },
    };
}]);


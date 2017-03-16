'use strict';

postOrdersApp.factory('ScanOrder', ['Restangular', function(Restangular) {
    return {
        get: function(id, route) {
            return Restangular.one('scan-order', id).get({route: route});
        },
    };
}]);


'use strict';

postOrdersApp.controller('Frame', ['$scope', '$location', '$window', '$filter', '$log', 'Restangular', '$cookies',
    function($scope, $location, $window, $filter, $log, Restangular, $cookies) {

    $scope.alerts = [];

    $scope.addAlert = function(message) {
        $scope.alerts.push({type: 'danger', msg: message});
    };

    $scope.closeAlert = function(index) {
        $scope.alerts.splice(index, 1);
    };

    $scope.clearAlerts = function() {
        $scope.alerts.length = 0;
    };

    $scope.isActive = function(route) {
        return $location.path().match("^" + route);
    }

    $scope.api_prefix = angular.element('body').attr('api_prefix');

    $scope.route_prefix = angular.element('body').attr('route_prefix');

    $scope.hrefs = ['/' + $scope.route_prefix + '/admin/admin.unused_standard_order',
                    '/' + $scope.route_prefix + '/admin/admin.unused_fast_track_order'];

    $scope.query_stats = function() {
        Restangular.one('orders').get().then(
            function(data){
                $scope.stats = data.stats;
                var alert_thresholds = data.alert_thresholds.map(function(item) {
                    return parseInt(item, 10)
                }).sort(function (a, b) {  return a - b;  });
                angular.forEach($scope.stats, function(value, key) {
                    var alerted = false;
                    angular.forEach(alert_thresholds, function(v, k){
                        var cookie_key = key + v;
                        if (value.unused < v) {
                            if (!alerted) {
                                if (typeof($cookies.get(cookie_key)) === 'undefined') {
                                    $window.alert("提醒: " + key + ' 不足' + v + ", 请尽快上载!");
                                    alerted = true;
                                    $cookies.put(cookie_key, true)
                                }
                            }
                        } else {
                            $cookies.remove(cookie_key);
                        }
                    });
                });

                $scope.used_count = data.used_count;
                $scope.unretracted_count = data.unretracted_count;
                $scope.retracted_count = data.retracted_count;
            },
            function(data){
                $scope.clearAlerts();
                $scope.addAlert("Connection error, please refresh the page...");
            });
    };
}]);

'use strict';

postOrdersApp.controller('Frame', ['$scope', '$location', '$window', '$filter', '$log',
    function($scope, $location, $window, $filter, $log) {

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
}]);

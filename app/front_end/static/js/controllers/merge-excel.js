'use strict';

postOrdersApp.controller('MergeExcel', ['$scope', '$window', '$log',
    function($scope, $window, $log) {

    $scope.clearAlerts();

    $scope.submit_url = '/' + $scope.route_prefix + '/merge-excel';

    var els = angular.element('.flash-message');
    angular.forEach(els, function( el ){
       $scope.addAlert(angular.element(el).text());
       el.remove();
    });
    angular.element('.div-flash-message').remove();

    $scope.onSubmit = function () {
        $scope.clearAlerts();
    };
}]);

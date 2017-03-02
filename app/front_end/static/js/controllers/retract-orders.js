'use strict';

postOrdersApp.controller('RetractOrders', ['$scope', 'Upload', '$location', '$timeout', '$window', '$log',
    function($scope, Upload, $location, $timeout, $window, $log) {

    $scope.running = false;
    $scope.retraction_id = null;

    $scope.query_stats();

    $scope.$watch('file', function () {
        $scope.clearAlerts();
        $scope.order_numbers = null;
        $scope.retraction_id = null;
        $scope.running = false;
        $scope.upload($scope.file);
    });

    $scope.upload = function (file) {
        if (file != undefined) {
            (function() {
                $scope.upload_file = { name: file.name, percentage: 0 };
                $scope.running = true;

                Upload.upload({
                    url: $scope.$parent.api_prefix + '/retract-orders',
                    file: file,
                    data: {route: $scope.route},
                }).progress(function (evt) {
                    $scope.upload_file.percentage = parseInt(100.0 * evt.loaded / evt.total);
                }).success(function (data, status, headers, config) {
                    $scope.order_numbers = data.order_numbers;
                    $scope.retraction_id = data.id;
                    $scope.running = false;
                    $scope.query_stats();
                }).error(function (data) {
                    $scope.addAlert(data.message);
                    $scope.running = false;
                    $scope.query_stats();
                });
            }) ();
        }
    };
}]);
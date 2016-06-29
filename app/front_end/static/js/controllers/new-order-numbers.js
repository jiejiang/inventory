'use strict';

postOrdersApp.controller('NewOrderNumbers', ['$scope', 'Upload', '$location', '$timeout', '$window', '$log',
    function($scope, Upload, $location, $timeout, $window, $log) {

    $scope.running = false;

    $scope.$watch('file', function () {
        $scope.clearAlerts();
        $scope.existing_order_numbers = null;
        $scope.inserted_order_numbers = null;
        $scope.invalid_order_numbers = null;
        $scope.running = false;
        $scope.upload($scope.file);
    });

    $scope.upload = function (file) {
        if (file != undefined) {
            (function() {
                $scope.upload_file = { name: file.name, percentage: 0 };
                $scope.running = true;

                Upload.upload({
                    url: $scope.$parent.api_prefix + '/orders',
                    file: file,
                }).progress(function (evt) {
                    $scope.upload_file.percentage = parseInt(100.0 * evt.loaded / evt.total);
                }).success(function (data, status, headers, config) {
                    $scope.inserted_order_numbers = data.inserted_order_numbers;
                    $scope.invalid_order_numbers = data.invalid_order_numbers;
                    $scope.existing_order_numbers = data.existing_order_numbers;
                    $scope.running = false;
                }).error(function (data) {
                    $log.log(data);
                    $scope.addAlert(data.message);
                });
            }) ();
        }
    };
}]);
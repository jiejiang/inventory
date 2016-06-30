'use strict';

postOrdersApp.controller('BatchOrder', ['$scope', 'Upload', 'BatchOrderJob', '$location', '$timeout', '$window', '$log', 'Restangular',
    function($scope, Upload, BatchOrderJob, $location, $timeout, $window, $log, Restangular) {

    $scope.job = BatchOrderJob;
    $scope.running = false;

    $scope.hrefs = ['/' + $scope.$parent.route_prefix + '/admin/admin.unused_standard_order',
                    '/' + $scope.$parent.route_prefix + '/admin/admin.unused_fast_track_order'];

    $scope.query_stats = function() {
        Restangular.one('orders').get().then(
            function(data){
                $scope.stats = data.stats;
                $scope.used_count = data.used_count;
            },
            function(data){
                $scope.clearAlerts();
                $scope.addAlert("Connection error, please refresh the page...");
            });
    };

    $scope.query_stats();

    $scope.$watch('file', function () {
        $scope.clearAlerts();
        $scope.upload($scope.file);
    });

    $scope.upload = function (file) {
        if (file != undefined) {
            $scope.job.clear();
            $scope.running = true;

            (function() {
                $scope.job.upload_file = { name: file.name, percentage: 0 };

                Upload.upload({
                    url: $scope.$parent.api_prefix + '/batch-order',
                    file: file,
                }).progress(function (evt) {
                    $scope.job.upload_file.percentage = parseInt(100.0 * evt.loaded / evt.total);
                }).success(function (data, status, headers, config) {
                    $scope.job.id = data.id;
                    $scope.job.data = {
                        status: 'Waiting',
                        percentage: 0,
                    };
                    (function tick() {
                        $scope.job.get().then(
                            function(data){
                                $scope.job.setData(data);
                                if (!data.finished && $scope.job.id) {
                                    $timeout(tick, 3000);
                                } else {
                                    $scope.running = false;
                                    if (!data.success) {
                                        $scope.addAlert(data.message);
                                    } else {

                                    }
                                }
                                $scope.query_stats();
                            },
                            function(data){
                                if ($scope.job.id) {
                                    $scope.clearAlerts();
                                    $scope.addAlert("Connection error, retrying...");
                                    $timeout(tick, 5000);
                                }
                            });
                    })();

                }).error(function (data) {
                    $scope.job.clear();
                    $scope.addAlert(data.message);
                    $scope.query_stats();
                    $scope.running = false;
                });
            }) ();
        }
    };
}]);
'use strict';

postOrdersApp.controller('BatchOrder', ['$scope', 'Upload', 'BatchOrderJob', '$location', '$timeout', '$window', '$log',
    function($scope, Upload, BatchOrderJob, $location, $timeout, $window, $log) {

    $scope.job = BatchOrderJob;

    $scope.$watch('file', function () {
        $scope.clearAlerts();
        $scope.upload($scope.file);
    });

    $scope.upload = function (file) {
        if (file != undefined) {
            $scope.job.clear();

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
                                    if (!data.success) {
                                        $scope.addAlert(data.message);
                                    } else {

                                    }
                                }
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
                    $log.log(data);
                    $scope.job.clear();
                    $scope.addAlert(data.message);
                });
            }) ();
        }
    };
}]);
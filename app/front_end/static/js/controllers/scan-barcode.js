'use strict';

postOrdersApp.controller('ScanBarcode', ['$scope', 'Upload', '$location', '$timeout', '$window', '$log',
    function($scope, Upload, $location, $timeout, $window, $log) {

    $scope.validScan = [];
    $scope.invalidScan = [];
    $scope.barcodeStorage = new Object();

    $scope.$on('keypress', function($event, event) {
        $log.log($event);
        $log.log(event);
    });

    $scope.onSelectRoute = function () {

    };

    $scope.onScan = function(barcode) {
        if ($scope.barcodeStorage.hasOwnProperty(barcode)) {
            $scope.invalidScan.push({barcode:barcode, prompt:'Error: Duplicated'});
        } else {
            $scope.barcodeStorage[barcode] = {};
            $scope.validScan.push({barcode:barcode, prompt:'Error: Scanned'});
        }
    };

    $scope.barcodeKeyPressed = function($event) {
        var keyCode = $event.which || $event.keyCode;
        if (keyCode == 13 && $scope.barcode) {
            var barcode = $scope.barcode;
            $scope.barcode = '';
            $log.log(barcode);
            $scope.onScan(barcode);
        }
    };
}]);

'use strict';

postOrdersApp.controller('ScanBarcode', ['$scope', 'ScanOrder', 'RouteInfo', '$http', '$cacheFactory', '$window', '$log',
    function($scope, ScanOrder, RouteInfo, $http, $cacheFactory, $window, $log) {

    $scope.initialize = function () {
        $scope.validScan = [];
        $scope.invalidScan = [];
        $scope.barcodeStorage = new Object();
        $scope.receiverCount = new Object();
        $scope.exportBarcodes = "";
    };

    $scope.initialize();

    $scope.onSelectRoute = function () {
        $scope.initialize();

        if ($scope.route) {
            RouteInfo.get($scope.route).then(
                function(data) {
                    $scope.route_info = data;
                },
                function(data) {
                    $scope.clearAlerts();
                    $scope.addAlert("Connection error, please retry");
            });
        }
    };

    $scope.cache = $cacheFactory('scan-prompt');

    $scope.playAudio = function(sentence) {
        var audio = $scope.cache.get(sentence);
        if (! audio) {
            audio = new Audio('/' + $scope.route_prefix + '/tts/' + sentence);
            $scope.cache.put(sentence, audio);
        }
        audio.play();
    };

    function getActiveClass(index) {
        if (index == 0) {
            return "animated infinite flash";
        }
        return ""
    };

    function getInactiveClass(index) {
        return ""
    };

    $scope.onReset = function() {
        $scope.initialize();
        $scope.route = "";
    };

    $scope.submit_url = '/' + $scope.route_prefix + '/scan-export';

    $scope.onSubmit = function() {
        $scope.exportBarcodes = $scope.validScan.map(function(obj) {
            return obj.barcode;
        }).join(",");
    /*
        $http.post('/scan-export', {barcodes: $scope.validScan.map(function(obj) {
            return obj.barcode;
        })}, {}).then(function(response) {
            var hiddenElement = document.createElement('a');
            hiddenElement.href = 'data:attachment/csv,' + encodeURI(response.data);
            hiddenElement.target = '_blank';
            hiddenElement.download = 'myFile.csv';
            hiddenElement.click();
        }, function(response) {
            $scope.clearAlerts();
            $scope.addAlert("Connection error, please retry");

            $scope.getAcceptClass = getInactiveClass;
            $scope.getRejectClass = getInactiveClass;
        });
        */
    };

    $scope.removeValidScan = function(index){
        var barcode = $scope.validScan[index].barcode;
        var id_number = $scope.barcodeStorage[barcode].receiver_id_number;
        if ($scope.receiverCount[id_number] > 0) {
            $scope.receiverCount[id_number] -= 1;
        }
        delete $scope.barcodeStorage[barcode];
        if (index === $scope.validScan.length - 1) {
            $scope.getAcceptClass = getInactiveClass;
        }
        $scope.validScan.splice(index, 1);
    };

    $scope.onScan = function(barcode) {
        if ($scope.barcodeStorage.hasOwnProperty(barcode)) {
            var message = 'Error: Barcode Duplicated';
            $scope.invalidScan.push({barcode:barcode, prompt:message});
            $scope.playAudio(message);

            $scope.getAcceptClass = getInactiveClass;
            $scope.getRejectClass = getActiveClass;
        } else {
            ScanOrder.get(barcode, $scope.route).then(
                function(data) {
                    var message = null;
                    if (data.success) {
                        var receiver_id_number = data.receiver_id_number;
                        if (!$scope.receiverCount.hasOwnProperty(receiver_id_number)) {
                            $scope.receiverCount[receiver_id_number] = 0;
                        }
                        if ($scope.receiverCount[receiver_id_number] >= $scope.route_info['max_order_number_per_receiver']) {
                            message = "Error: Exceeded Personal Package Allowance";
                            $scope.invalidScan.push({barcode:barcode, prompt:message});

                            $scope.getAcceptClass = getInactiveClass;
                            $scope.getRejectClass = getActiveClass;
                        } else {
                            $scope.barcodeStorage[barcode] = data;
                            $scope.validScan.push({barcode:barcode, prompt:data.message});
                            message = data.message;
                            $scope.receiverCount[receiver_id_number] += 1;

                            $scope.getAcceptClass = getActiveClass;
                            $scope.getRejectClass = getInactiveClass;
                        }
                    } else {
                        message = data.message;
                        $scope.invalidScan.push({barcode:barcode, prompt:message});

                        $scope.getAcceptClass = getInactiveClass;
                        $scope.getRejectClass = getActiveClass;
                    }
                    if (message) {
                        $scope.playAudio(message);
                    }
                },
                function(data) {
                    $scope.clearAlerts();
                    $scope.addAlert("Connection error, please retry");

                    $scope.getAcceptClass = getInactiveClass;
                    $scope.getRejectClass = getInactiveClass;
            });
        }
    };

    $scope.barcodeKeyPressed = function($event) {
        var keyCode = $event.which || $event.keyCode;
        if (keyCode == 13 && $scope.barcode) {
            var barcode = $scope.barcode;
            $scope.barcode = '';
            $scope.onScan(barcode);
        }
    };
}]);

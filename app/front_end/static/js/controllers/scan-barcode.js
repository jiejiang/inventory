'use strict';

postOrdersApp.controller('ScanBarcode', ['$scope', 'Upload', 'ScanOrder', 'RouteInfo', '$http', '$cacheFactory', '$window', '$log',
    function($scope, Upload, ScanOrder, RouteInfo, $http, $cacheFactory, $window, $log) {

    $scope.initialize = function () {
        $scope.validScan = [];
        $scope.invalidScan = [];
        $scope.barcodeStorage = new Object();
        $scope.receiverCount = new Object();
        $scope.receiverName = new Object();
        $scope.receiverAddress = new Object();
        $scope.dutiable_count = 0;
        $scope.dutiable_category_count = 0;
        $scope.exportBarcodes = "";
        $scope.clearAlerts();
        $scope.running = false;
        $scope.preScansList = [];
    };

    $scope.initialize();

    $scope.barcode_size = function () {
        var count = 0;
        for (var k in $scope.barcodeStorage) if ($scope.barcodeStorage.hasOwnProperty(k)) ++count;
        return count;
    }

    $scope.dutiablePercentage = function () {
        if ($scope.dutiable_category_count > 0) {
            return parseFloat($scope.dutiable_count * 100 / $scope.dutiable_category_count).toFixed(1);
        }
        return 0
    }

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

    $scope.cache = $cacheFactory.get('scan-prompt') || $cacheFactory('scan-prompt');

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
        var receiver_name = $scope.barcodeStorage[barcode].receiver_name;
        var receiver_address = $scope.barcodeStorage[barcode].receiver_address;
        if ($scope.receiverCount[id_number] > 0) {
            $scope.receiverCount[id_number] -= 1;
        }
        if ($scope.receiverName[receiver_name] > 0) {
            $scope.receiverName[receiver_name] -= 1;
        }
        if ($scope.receiverAddress[receiver_address] > 0) {
            $scope.receiverAddress[receiver_address] -= 1;
        }
        if ($scope.barcodeStorage[barcode].is_dutiable_category) {
            $scope.dutiable_category_count--;
            if ($scope.barcodeStorage[barcode].dutiable) {
                $scope.dutiable_count--;
            }
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
                        console.log($scope.route_info['max_order_number_per_receiver']);
                        var receiver_id_number = data.receiver_id_number;
                        var receiver_name = data.receiver_name;
                        var receiver_address = data.receiver_address;
                        if (!$scope.receiverCount.hasOwnProperty(receiver_id_number)) {
                            $scope.receiverCount[receiver_id_number] = 0;
                        }
                        if (!$scope.receiverName.hasOwnProperty(receiver_name)) {
                            $scope.receiverName[receiver_name] = 0;
                        }
                        if (!$scope.receiverAddress.hasOwnProperty(receiver_address)) {
                            $scope.receiverAddress[receiver_address] = 0;
                        }
                        if ($scope.route_info['max_order_number_per_receiver'] &&
                        (($scope.receiverCount[receiver_id_number] >= $scope.route_info['max_order_number_per_receiver'])
                        || ($scope.receiverName[receiver_name] >= $scope.route_info['max_order_number_per_receiver'])
                        )) { //|| ($scope.receiverAddress[receiver_address] >= $scope.route_info['max_order_number_per_receiver'])
                            message = "Error: Exceeded Personal Package Allowance: " + $scope.route_info['max_order_number_per_receiver'];
                            $scope.invalidScan.push({barcode:barcode, prompt:message});

                            $scope.getAcceptClass = getInactiveClass;
                            $scope.getRejectClass = getActiveClass;
                        } else {
                            $scope.barcodeStorage[barcode] = data;
                            if ($scope.barcodeStorage[barcode].is_dutiable_category) {
                                $scope.dutiable_category_count++;
                                if ($scope.barcodeStorage[barcode].dutiable) {
                                    $scope.dutiable_count++;
                                }
                            }
                            $scope.validScan.push({barcode:barcode, prompt:data.message});
                            message = data.message;
                            $scope.receiverCount[receiver_id_number] += 1;
                            $scope.receiverName[receiver_name] += 1;
                            $scope.receiverAddress[receiver_address] += 1;

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

    $scope.$watch('file', function () {
        $scope.clearAlerts();
        $scope.running = false;
        $scope.upload($scope.file);
    });

    $scope.upload = function (file) {
        if (file != undefined) {
            (function() {

                $scope.running = true;

                Upload.upload({
                    url: $scope.$parent.api_prefix + '/retract-orders',
                    file: file,
                    data: {route: $scope.route, dryrun: true},
                }).progress(function (evt) {
                }).success(function (data, status, headers, config) {
                    //precombine validate
                    var _barcodeStorage = new Object();
                    var _receiverCount = new Object();
                    var _receiverName = new Object();
                    var _receiverAddress = new Object();
                    for (var i = 0, len = data.length; i < len; i++) {
                        var scan = data[i];
                        if (_barcodeStorage.hasOwnProperty(scan.barcode) || $scope.barcodeStorage.hasOwnProperty(scan.barcode)){
                            $scope.addAlert('Loading failed with duplicated scanned barcode: ' + scan.barcode);
                            return;
                        }
                        if (!_receiverCount.hasOwnProperty(scan.receiver_id_number)) {
                            _receiverCount[scan.receiver_id_number] = 0;
                        }
                        if (!_receiverName.hasOwnProperty(scan.receiver_name)) {
                            _receiverName[scan.receiver_name] = 0;
                        }
                        if (!_receiverAddress.hasOwnProperty(scan.receiver_address)) {
                            _receiverAddress[scan.receiver_address] = 0;
                        }
                        if ($scope.route_info['max_order_number_per_receiver']
                        && ((_receiverCount[scan.receiver_id_number] >= $scope.route_info['max_order_number_per_receiver'])
                        || (_receiverName[scan.receiver_name] >= $scope.route_info['max_order_number_per_receiver'])
                        )) { //|| (_receiverAddress[scan.receiver_address] >= $scope.route_info['max_order_number_per_receiver'])
                            $scope.addAlert('Loading failed with exceeded personal allowance :'
                            + $scope.route_info['max_order_number_per_receiver']);
                            return;
                        }
                        _barcodeStorage[scan.barcode] = scan;
                        _receiverCount[scan.receiver_id_number] += 1;
                        _receiverName[scan.receiver_name] += 1;
                        _receiverAddress[scan.receiver_address] += 1;
                    }
                    if ($scope.route_info['max_order_number_per_receiver']) {
                        for (var receiver_id_number in _receiverCount) {
                            if (_receiverCount.hasOwnProperty(receiver_id_number)
                            && $scope.receiverCount.hasOwnProperty(receiver_id_number)) {
                                if (_receiverCount[receiver_id_number] + $scope.receiverCount[receiver_id_number]
                                > $scope.route_info['max_order_number_per_receiver']) {
                                    $scope.addAlert('Loading failed with exceeded personal allowance ('
                                    + $scope.route_info['max_order_number_per_receiver'] + '): ' + receiver_id_number)
                                    return;
                                }
                            }
                        }
                        for (var receiver_name in _receiverName) {
                            if (_receiverName.hasOwnProperty(receiver_name)
                            && $scope.receiverName.hasOwnProperty(receiver_name)) {
                                if (_receiverName[receiver_name] + $scope.receiverName[receiver_name]
                                > $scope.route_info['max_order_number_per_receiver']) {
                                    $scope.addAlert('Loading failed with exceeded personal allowance ('
                                    + $scope.route_info['max_order_number_per_receiver'] + '): ' + receiver_name)
                                    return;
                                }
                            }
                        }
//                        for (var receiver_address in _receiverAddress) {
//                            if (_receiverAddress.hasOwnProperty(receiver_address)
//                            && $scope.receiverAddress.hasOwnProperty(receiver_address)) {
//                                if (_receiverAddress[receiver_address] + $scope.receiverAddress[receiver_address]
//                                > $scope.route_info['max_order_number_per_receiver']) {
//                                    $scope.addAlert('Loading failed with exceeded personal allowance ('
//                                    + $scope.route_info['max_order_number_per_receiver'] + '): ' + receiver_address)
//                                    return;
//                                }
//                            }
//                        }
                    }
                    //combine and add
                    var scans = [];
                    for (var i = 0, len = data.length; i < len; i++) {
                        var scan = data[i];
                        $scope.barcodeStorage[scan.barcode] = scan;
                        console.log(scan);
                        if ($scope.barcodeStorage[scan.barcode].is_dutiable_category) {
                            $scope.dutiable_category_count++;
                            if ($scope.barcodeStorage[scan.barcode].dutiable) {
                                $scope.dutiable_count++;
                            }
                        }
                        if (!$scope.receiverCount.hasOwnProperty(scan.receiver_id_number)) {
                            $scope.receiverCount[scan.receiver_id_number] = 0;
                        }
                        if (!$scope.receiverName.hasOwnProperty(scan.receiver_name)) {
                            $scope.receiverName[scan.receiver_name] = 0;
                        }
                        if (!$scope.receiverAddress.hasOwnProperty(scan.receiver_address)) {
                            $scope.receiverAddress[scan.receiver_address] = 0;
                        }
                        $scope.receiverCount[scan.receiver_id_number] += 1;
                        $scope.receiverName[scan.receiver_name] += 1;
                        $scope.receiverAddress[scan.receiver_address] += 1;
                        scans.push(scan);
                    }
                    $scope.preScansList.push({name:file.name, scans:scans, visible:false});
                }).error(function (data) {
                    $scope.addAlert(data.message);
                }).finally(function () {
                    $scope.running = false;
                });
            }) ();
        }
    };

    $scope.togglePreScans = function(index){
        if (index < $scope.preScansList.length) {
            $scope.preScansList[index].visible = !$scope.preScansList[index].visible;
        }
    };
}]);

'use strict';

window.postOrdersApp = angular.module('postOrdersApp',
    ['ngRoute', 'restangular', 'ui.bootstrap', 'ngFileUpload', 'ngCookies']
    )

.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[');
    $interpolateProvider.endSymbol(']}');
}])

.config(['$routeProvider', 'RestangularProvider', function($routeProvider, RestangularProvider) {
    RestangularProvider.setBaseUrl(angular.element('body').attr('api_prefix'));

    var partialsDir = 'static/partials/';

    $routeProvider
    .when('/batch-order', {
        templateUrl: partialsDir + 'batch-order.html',
        controller: 'BatchOrder'
    })
    .when('/retract-orders', {
        templateUrl: partialsDir + 'retract-orders.html',
        controller: 'RetractOrders'
    })
    .when('/new-order-numbers', {
        templateUrl: partialsDir + 'new-order-numbers.html',
        controller: 'NewOrderNumbers'
    })
    .when('/scan-barcode', {
        templateUrl: partialsDir + 'scan-barcode.html',
        controller: 'ScanBarcode'
    })
    .when('/merge-excel', {
        templateUrl: partialsDir + 'merge-excel.html',
        controller: 'MergeExcel'
    })
    .otherwise({redirectTo: '/batch-order'});
}]);

$(function() {
	$('#side-menu').metisMenu();
});

'use strict';window.postOrdersApp=angular.module('postOrdersApp',['ngRoute','restangular','ui.bootstrap','ngFileUpload','ngCookies']).config(['$interpolateProvider',function($interpolateProvider){$interpolateProvider.startSymbol('{[');$interpolateProvider.endSymbol(']}');}]).config(['$routeProvider','RestangularProvider',function($routeProvider,RestangularProvider){RestangularProvider.setBaseUrl(angular.element('body').attr('api_prefix'));var partialsDir='static/partials/';$routeProvider.when('/batch-order',{templateUrl:partialsDir+'batch-order.html',controller:'BatchOrder'}).when('/retract-orders',{templateUrl:partialsDir+'retract-orders.html',controller:'RetractOrders'}).when('/new-order-numbers',{templateUrl:partialsDir+'new-order-numbers.html',controller:'NewOrderNumbers'}).when('/scan-barcode',{templateUrl:partialsDir+'scan-barcode.html',controller:'ScanBarcode'}).otherwise({redirectTo:'/batch-order'});}]);$(function(){$('#side-menu').metisMenu();});'use strict';postOrdersApp.controller('Frame',['$scope','$location','$window','$filter','$log','Restangular','$cookies',function($scope,$location,$window,$filter,$log,Restangular,$cookies){$scope.alerts=[];$scope.addAlert=function(message){$scope.alerts.push({type:'danger',msg:message});};$scope.closeAlert=function(index){$scope.alerts.splice(index,1);};$scope.clearAlerts=function(){$scope.alerts.length=0;};$scope.isActive=function(route){return $location.path().match("^"+route);}
$scope.api_prefix=angular.element('body').attr('api_prefix');$scope.route_prefix=angular.element('body').attr('route_prefix');$scope.hrefs=['/'+$scope.route_prefix+'/admin/admin.unused_standard_order','/'+$scope.route_prefix+'/admin/admin.unused_fast_track_order'];$scope.query_stats=function(){Restangular.one('orders').get().then(function(data){$scope.stats=data.stats;var alert_thresholds=data.alert_thresholds.map(function(item){return parseInt(item,10)}).sort(function(a,b){return a-b;});angular.forEach($scope.stats,function(value,key){var alerted=false;angular.forEach(alert_thresholds,function(v,k){var cookie_key=key+v;if(value.unused<v){if(!alerted){if(typeof($cookies.get(cookie_key))==='undefined'){$window.alert("提醒: "+key+' 不足'+v+", 请尽快上载!");alerted=true;$cookies.put(cookie_key,true)}}}else{$cookies.remove(cookie_key);}});});$scope.used_count=data.used_count;$scope.unretracted_count=data.unretracted_count;$scope.retracted_count=data.retracted_count;},function(data){$scope.clearAlerts();$scope.addAlert("Connection error, please refresh the page...");});};}]);'use strict';postOrdersApp.controller('BatchOrder',['$scope','Upload','BatchOrderJob','$location','$timeout','$window','$log','Restangular',function($scope,Upload,BatchOrderJob,$location,$timeout,$window,$log,Restangular){$scope.job=BatchOrderJob;$scope.running=false;$scope.query_stats();$scope.$watch('file',function(){$scope.clearAlerts();$scope.upload($scope.file);});$scope.upload=function(file){if(file!=undefined){$scope.job.clear();$scope.running=true;(function(){$scope.job.upload_file={name:file.name,percentage:0};Upload.upload({url:$scope.$parent.api_prefix+'/batch-order',file:file,}).progress(function(evt){$scope.job.upload_file.percentage=parseInt(100.0*evt.loaded/evt.total);}).success(function(data,status,headers,config){$scope.job.id=data.id;$scope.job.data={status:'Waiting',percentage:0,};(function tick(){$scope.job.get().then(function(data){$scope.job.setData(data);if(!data.finished&&$scope.job.id){$timeout(tick,3000);}else{$scope.running=false;if(!data.success){$scope.addAlert(data.message);}else{}}
$scope.query_stats();},function(data){if($scope.job.id){$scope.clearAlerts();$scope.addAlert("Connection error, retrying...");$timeout(tick,5000);}});})();}).error(function(data){$scope.job.clear();$scope.addAlert(data.message);$scope.query_stats();$scope.running=false;});})();}};}]);'use strict';postOrdersApp.factory('BatchOrderJob',['Restangular',function(Restangular){return{id:null,upload_file:null,data:null,clear:function(){this.id=null;this.upload_file=null;this.data=null;},get:function(){return Restangular.one('job',this.id).get();},setData:function(data){this.data=data;},};}]);'use strict';postOrdersApp.controller('NewOrderNumbers',['$scope','Upload','$location','$timeout','$window','$log',function($scope,Upload,$location,$timeout,$window,$log){$scope.running=false;$scope.$watch('file',function(){$scope.clearAlerts();$scope.existing_order_numbers=null;$scope.inserted_order_numbers=null;$scope.invalid_order_numbers=null;$scope.running=false;$scope.upload($scope.file);});$scope.upload=function(file){if(file!=undefined){(function(){$scope.upload_file={name:file.name,percentage:0};$scope.running=true;Upload.upload({url:$scope.$parent.api_prefix+'/orders',file:file,}).progress(function(evt){$scope.upload_file.percentage=parseInt(100.0*evt.loaded/evt.total);}).success(function(data,status,headers,config){$scope.inserted_order_numbers=data.inserted_order_numbers;$scope.invalid_order_numbers=data.invalid_order_numbers;$scope.existing_order_numbers=data.existing_order_numbers;$scope.running=false;}).error(function(data){$scope.addAlert(data.message);$scope.running=false;});})();}};}]);'use strict';postOrdersApp.controller('RetractOrders',['$scope','Upload','$location','$timeout','$window','$log',function($scope,Upload,$location,$timeout,$window,$log){$scope.running=false;$scope.retraction_id=null;$scope.query_stats();$scope.$watch('file',function(){$scope.clearAlerts();$scope.order_numbers=null;$scope.retraction_id=null;$scope.running=false;$scope.upload($scope.file);});$scope.upload=function(file){if(file!=undefined){(function(){$scope.upload_file={name:file.name,percentage:0};$scope.running=true;Upload.upload({url:$scope.$parent.api_prefix+'/retract-orders',file:file,data:{route:$scope.route},}).progress(function(evt){$scope.upload_file.percentage=parseInt(100.0*evt.loaded/evt.total);}).success(function(data,status,headers,config){$scope.order_numbers=data.order_numbers;$scope.retraction_id=data.id;$scope.running=false;$scope.query_stats();}).error(function(data){$scope.addAlert(data.message);$scope.running=false;$scope.query_stats();});})();}};}]);'use strict';postOrdersApp.controller('ScanBarcode',['$scope','Upload','$location','$timeout','$window','$log',function($scope,Upload,$location,$timeout,$window,$log){$scope.validScan=[];$scope.invalidScan=[];$scope.barcodeStorage=new Object();$scope.$on('keypress',function($event,event){$log.log($event);$log.log(event);});$scope.onSelectRoute=function(){};$scope.onScan=function(barcode){if($scope.barcodeStorage.hasOwnProperty(barcode)){$scope.invalidScan.push({barcode:barcode,prompt:'Duplicated'});}else{$scope.barcodeStorage[barcode]={};$scope.validScan.push({barcode:barcode,prompt:'Scanned'});}};$scope.barcodeKeyPressed=function($event){var keyCode=$event.which||$event.keyCode;if(keyCode==13&&$scope.barcode){var barcode=$scope.barcode;$scope.barcode='';$log.log(barcode);$scope.onScan(barcode);}};}]);
// Ionic Starter App

// angular.module is a global place for creating, registering and retrieving Angular modules
// 'starter' is the name of this angular module example (also set in a <body> attribute in index.html)
// the 2nd parameter is an array of 'requires'
angular.module('app', ['ionic'])
.controller('mainController', function($scope, $http, $ionicPopup){
    $scope.server = {};
    $scope.client = {};

    $scope.refreshItems = function() {
        $http({
            url: '/status'
        }).success(function(response){
            $scope.items = response.result;

        }).error(function(error){
            $scope.items = [];
        });
    };

    $scope.onStatusTab = function() {
        $scope.refreshItems();
    };

    $scope.onServerTab = function() {
        $scope.server = {};
    };

    $scope.onClientTab = function() {
        $scope.client = {};
    };

    $scope.addServer = function() {
        $http({
            url: '/server',
            params: {channel: $scope.server.channel, address: $scope.server.address, port: $scope.server.port}
        }).success(function(response){
            $ionicPopup.alert({
                title: 'Add Server',
                template: 'Server item is successfully created.'
            });

        }).error(function(error){
            $ionicPopup.alert({
                title: 'Add Server',
                template: 'Server item creation is failed.'
            });

        });
    };

    $scope.addClient = function() {
        $http({
            url: '/client',
            params: {channel: $scope.client.channel, port: $scope.client.port}
        }).success(function(response){
            $ionicPopup.alert({
                title: 'Add Client',
                template: 'Client item is successfully created.'
            });

        }).error(function(error){
            $ionicPopup.alert({
                title: 'Add Client',
                template: 'Client item creation is failed.'
            });

        });
    };

    $scope.kill = function(id) {
        $ionicPopup.confirm({
            title: 'Kill',
            template: 'Are you sure you want to kill this item?'
        }).then(function(res) {
            if(res) {
                $http({
                    url: '/kill',
                    params: {id:id}

                }).success(function(response){
                    $scope.refreshItems();
                }).error(function(error){
                });
            }
        });
    };

    $scope.openSSH = function() {
        var loc = 'http://' + window.location.hostname + ':8022';
        window.location = loc;
    };

})
.config(function($stateProvider, $urlRouterProvider) {
  // Ionic uses AngularUI Router which uses the concept of states
  // Learn more here: https://github.com/angular-ui/ui-router
  // Set up the various states which the app can be in.
  // Each state's controller can be found in controllers.js
  $stateProvider
    .state('page1', {
      url: '/main',
      templateUrl: 'page1.html'
    });

  // if none of the above states are matched, use this as the fallback
  $urlRouterProvider.otherwise('/main');
})
.run(function($ionicPlatform) {
  $ionicPlatform.ready(function() {
    // Hide the accessory bar by default (remove this to show the accessory bar above the keyboard
    // for form inputs)
    if(window.cordova && window.cordova.plugins.Keyboard) {
      cordova.plugins.Keyboard.hideKeyboardAccessoryBar(true);
    }
    if(window.StatusBar) {
      // org.apache.cordova.statusbar required
      StatusBar.styleDefault();
    }
  });
})

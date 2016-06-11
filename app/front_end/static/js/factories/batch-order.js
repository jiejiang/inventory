'use strict';

postOrdersApp.factory('BatchOrderJob', ['Restangular', function(Restangular) {
    return {
        id: null,
        upload_file: null,
        data: null,

        clear: function() {
            this.id = null;
            this.upload_file = null;
            this.data = null;
        },

        get: function() {
            return Restangular.one('job', this.id).get();
        },

        setData: function(data) {
            this.data = data;
        },
    };
}]);
/* Copyright <YEAR(S)> <AUTHOR(S)>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */

odoo.define('web_module_name.objectName', function(require){
    "use strict";

    var core = require('web.core');

    core.bus.on('web_client_ready', null, function () {
        // Script that will be loaded when document is ready
    });

    function methodToExport () {
        // This method will be exported as
        // require('module_name.object_name').methodToExport
    }

    return {methodToExport: methodToExport};

});

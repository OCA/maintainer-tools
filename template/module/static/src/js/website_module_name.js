/* Copyright <YEAR(S)> <AUTHOR(S)>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */

odoo.define('website_module_name.objectName', function(require){
    "use strict";

    var base = require('web_editor.base');
    base.ready().done(function() {
        // Script that will be loaded when document is ready
    });

    function methodToExport () {
        // This method will be exported as
        // require('module_name.object_name').methodToExport
    }

    return {methodToExport: methodToExport};

});

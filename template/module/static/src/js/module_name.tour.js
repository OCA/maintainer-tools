/* © <YEAR(S)> <AUTHOR(S)>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */

"use strict";
odoo.define("module_name.tour", function (require) {

var Core = require("web.core");
var Tour = require("web.Tour");
var _t = Core._t;


Tour.register({
    id: "test_module_name",
    name: _t("Try to demostrate how to create a tour"),
    path: "/path/where/tour/starts",
    mode: "test",  // Or "tutorial" if it is intended to be used by humans
    steps: [
        {
            title: _t("The title of this step, appears in logs"),
            element: "div.jquery-selector-of-element-to-click-or-use",
            sampleText: "Value to enter if it is an input",
            waitFor: ".start-when-this-jquery-selector-matches-something",
            waitNot: ".start-when-this-jquery-selector-matches-nothing",
            onend: function() {
                // Custom code that should return true for step to success
                return true;
            },

            // Only for "tutorial" mode.
            // See http://getbootstrap.com/javascript/#popovers-usage
            content: _t("Instructions for end user."),
            backdrop: false,
            orphan: false, // Display it in the middle of the page
            placement: "auto",
            template: "<div class='popover'/>",
            popover: {  // Only used if "template" is not defined
                next: _t("Text for continue button."),
                arrow: false,
                fixed: false,
            },
        },
        // More steps here...
    ]
});

// On tours normally you return nothing, but on other modules, you must return
// whatever your module exposes, as a JS or $.Deferred() object.
// See https://www.odoo.com/documentation/9.0/reference/javascript.html#javascript-module-system-overview
return {
    some_exposed_variable: true,
}

});

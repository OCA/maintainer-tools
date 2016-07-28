/* Copyright <YEAR(S)> <AUTHOR(S)>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl). */

odoo.define("web_module_name.tour", function (require) {
    "use strict";

    // Dependencies here by alphabetic order. Template only for Odoo 9+.
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
                // Only translate title of tutorial tours
                title: _t("The title of this step, appears in logs"),
                element: "div.jquery-selector-of-element-to-click-or-use",
                sampleText: "Value to enter if it is an input",
                wait: 3000, // Milliseconds to wait
                waitFor: ".start-when-this-jquery-selector-matches-something",
                waitNot: ".start-when-this-jquery-selector-matches-nothing",

                // Custom code that can return a step title to jump to it
                onload: function () {
                    // `this` is the step itself
                    return "some step title";
                },
                onend: function() {
                    // `this` is the step itself
                    return "some step title";
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

    // On tours normally you return nothing, but on other modules, you must
    // return whatever your module exposes, as a JS or $.Deferred() object. See
    // https://www.odoo.com/documentation/9.0/reference/javascript.html#javascript-module-system-overview
    return {
        some_exposed_variable: true,
    };

});

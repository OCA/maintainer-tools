/* Copyright <YEAR(S)> <AUTHOR(S)>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define_section('module_name', ['module_name.ExportedObject'], function(test) {
    "use strict";

    test('It should demonstrate a PhantomJS test for web (backend)',
        function(assert, ExportedObject) {
            var expect = 'Expected Return',
                result = new ExportedObject();
            assert.assertStrictEqual(
                result,
                expect,
                "Result !== Expect and the test failed with this message"
            );
        }
    );
    
});

#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import ast
import re
import sys

import autopep8
import inflection


CODING_COMMENT = '# coding: utf-8'


class Pep8Extended(object):
    def __init__(self, pep8_options, source):
        self.pep8_options = pep8_options
        self.source = source
        self.msgs = {
            'CW0001': 'Class name with snake_case style found, '
                      'should use CamelCase. Change of "{old_class_name}" '
                      'to "{new_class_name}" next (lines,columns): '
                      '{lines_columns}',
            'CW0002': 'VIM comment found',
            'CW0003': 'Coding comment no standard, should use ' +
                      CODING_COMMENT,
            'CW0004': 'Missed coding comment',
        }
        self.coding_comment = None

    def check_cw0002(self):
        'Detect vim comment'
        msg_code = 'CW0002'
        check_result = []
        msg = self.msgs[msg_code]
        line_no = 0
        for line in self.source:
            column = 0
            line_no += 1
            line = line.strip()
            if line.startswith('#') and \
               line[1:].strip().lower().startswith('vim:'):
                check_result.append({
                    'id': msg_code,
                    'line': line_no,
                    'column': column,
                    'info': msg,
                })
        return check_result

    def strip_coding_comment(self):
        '''Remove coding comment if found in first two lines
        This fix 'SyntaxError: encoding declaration in Unicode string'
        If the first or second line has the `# xx coding xx` comment,
            it will be removed.
        :return: source code without coding comment
        '''
        source_strip = list(self.source)
        line_index = 0
        for line in source_strip[:2]:
            if line.strip().startswith('#') \
                    and "coding" in line:
                self.coding_comment = source_strip.pop(line_index)
            else:
                line_index += 1
        return source_strip

    def check_cw0001(self):
        '''Find class with `snake_case` style.
        Based on `self.source` to get source code.
        Use autoflak8 dictionary
            'id': MSG_CODE,
            'line': LINE_NUMBER,
            'column': COLUMN_NUMBER,
            'info': MESSAGE,
        :return: if snake_case is found return list of autoflake8 dict
                 with code data else return empty list.
        '''
        code = 'CW0001'
        msg = self.msgs[code]
        class_renamed = {}
        check_result = []

        source = self.strip_coding_comment()
        line_deleted = len(self.source) - len(source)
        parsed = ast.parse(''.join(source))

        renamed_names = []
        for node in ast.walk(parsed):
            if isinstance(node, ast.ClassDef):
                node_renamed = inflection.camelize(
                    node.name, uppercase_first_letter=True)
                renamed_names.append(node_renamed)
                if node_renamed != node.name:
                    class_renamed.setdefault(
                        node.name, {'line_col': [], 'renamed': node_renamed})
                    class_renamed[node.name]['line_col'].append((
                        node.lineno + line_deleted,
                        node.col_offset + 1))
            if isinstance(node, ast.Name) \
               and node.id in class_renamed:
                class_renamed[node.id]['line_col'].append((
                    node.lineno + line_deleted, node.col_offset + 1))
        if len(set(renamed_names)) != len(renamed_names):
            # Avoid errors when you have duplicated class name
            # but with different style in same file.
            # e.g. class my_class_1() and class MyClass1()
            print(
                "Waning: Aborted. You have two class named "
                "my_name and MyName in a same file.\n"
                "Review your next class names: "
                "{0}".format(renamed_names)
            )
            return check_result

        for class_original_name in class_renamed:
            line, column = class_renamed[
                class_original_name]['line_col'][0]
            check_result.append({
                'id': code,
                'line': line,
                'column': column,
                'info': msg.format(
                    old_class_name=class_original_name,
                    new_class_name=class_renamed[
                        class_original_name]['renamed'],
                    lines_columns=class_renamed[
                        class_original_name]['line_col']
                ),
            })
        return check_result

    def check_cw0003(self):
        'Detect coding comment no standard'
        self.strip_coding_comment()
        if self.coding_comment is not None:
            msg_code = 'CW0003'
            msg = self.msgs[msg_code]
            line = self.source.index(self.coding_comment) + 1
            column = 0
            return [{
                'id': msg_code,
                'line': line,
                'column': column,
                'info': msg,
            }]

    def check_cw0004(self):
        'Detect missed coding comment'
        self.strip_coding_comment()
        if self.coding_comment is None:
            msg_code = 'CW0004'
            msg = self.msgs[msg_code]
            line = 1
            column = 0
            return [{
                'id': msg_code,
                'line': line,
                'column': column,
                'info': msg,
            }]

    def _execute_pep8_extendend(self):
        '''Wrapper method to run check method based on check name.
        This method will call to methods:
            check_CHECK_NAME(self)
        :return: List extended with methods result.
        '''
        checks_results = []
        for check in self.msgs:
            # Validate if error is enabled.
            if check not in self.pep8_options['ignore'] \
               and (not self.pep8_options['select'] or
                    check in self.pep8_options['select']):
                check_methodname = 'check_' + check.lower()
                if hasattr(self, check_methodname):
                    check_method = getattr(self, check_methodname)
                    check_results = check_method()
                    if check_results and self.source:
                        checks_results.extend(check_results)
        return checks_results


_execute_pep8_original = autopep8._execute_pep8


def _execute_pep8(pep8_options, source):
    """
    Get all messages error with structure:
    {
        'id': code,
        'line': line_number,
        'column': offset + 1,
        'info': text
    }
    @param pep8_options: dictionary with next structure:
        {
            'ignore': self.options.ignore,
            'select': self.options.select,
            'max_line_length': self.options.max_line_length,
        }
    @param source: Lines of code.
    @return: list with all dict structures
    """
    pep8_extended_obj = Pep8Extended(pep8_options, source)
    res_extended = pep8_extended_obj._execute_pep8_extendend()
    res = _execute_pep8_original(pep8_options, source)
    res.extend(res_extended)
    return res


autopep8._execute_pep8 = _execute_pep8


class FixPEP8(autopep8.FixPEP8):
    def fix_cw0002(self, result):
        """Delete vim comment
        :param result: Dict with next values
            {
            'id': code,
            'line': line_number,
            'column': column_number,
            'info': msg
            }
        :return: List of integers with lines deleted
        """
        line = result['line']
        self.source[line - 1] = ''
        lines_modified = [line]
        return lines_modified

    def fix_cw0001(self, result):
        '''
        Replace class name from snake_case to CamelCase
        :param result: Dict with next values
            {
            'id': code,
            'line': line_number,
            'column': column_number,
            'info': 'Class name with snake_case style found, '
                    'should use CamelCase. Change of "{old_class_name}"'
                    ' to "{new_class_name}" next (lines,columns):'
                    ' {lines_columns}',
            }
            Where info keys values {old_class_name} to replace,
            {new_class_name} is new class name,
            {lines_columns} is a list of lines, columns
            with invokes to {old_class_name}.
        :return: Return list of integer with value of # line modified
        '''
        regex_old_new = r'\"(?P<old>\w*)(\" to \")(?P<new>\w*)\"'
        match_old_new = re.search(regex_old_new, result['info'])
        regex_lc = r"(?P<lines_columns>\[[\(\d, \)]*\])"
        match_lc = re.search(regex_lc, result['info'])
        if not match_lc or not match_old_new:
            return []
        str_old = match_old_new.group('old')
        str_new = match_old_new.group('new')
        lines_columns = ast.literal_eval(
            match_lc.group('lines_columns'))
        lines_modified = []
        for line, column in lines_columns:
            target = self.source[line - 1]
            offset = column - 1
            fixed = target[:offset] + target[offset:].replace(
                str_old, str_new, 1)
            self.source[line - 1] = fixed
            lines_modified.append(line)
        return lines_modified

    def fix_cw0003(self, result):
        """Replace coding comment to `CODING_COMMENT` global variable
        :param result: Dict with next values
            {
            'id': code,
            'line': line_number,
            'column': column_number,
            'info': msg,
            }
        :return: Return list of integers with value of # line modified
        """
        line = result['line']
        self.source[line - 1] = CODING_COMMENT + '\n'
        return [line]

    def fix_cw0004(self, result):
        """Add new coding comment to `CODING_COMMENT` global variable
        :param result: Dict with next values
            {
            'id': code,
            'line': line_number,
            'column': column_number,
            'info': msg,
            }
        :return: Return list of integers with value of # line modified
        """
        self.source.insert(0, CODING_COMMENT + '\n')
        return [result['line']]


autopep8.FixPEP8 = FixPEP8


def main():
    return autopep8.main()


if __name__ == '__main__':
    sys.exit(main())

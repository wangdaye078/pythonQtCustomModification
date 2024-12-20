# 这是一个示例 Python 脚本。

import argparse
import os
import re
import xml.etree.ElementTree as ET


def frontInsert(_source: str, _tag: str, _insert: str):
    if (pos := _source.find(_tag)) > 0:
        return _source[:pos] + _insert + _source[pos:]
    raise Exception(f'not found {_tag}')


def rfrontInsert(_source: str, _tag: str, _insert: str):
    if (pos := _source.rfind(_tag)) > 0:
        return _source[:pos] + _insert + _source[pos:]
    raise Exception(f'not found {_tag}')


def backInsert(_source: str, _tag: str, _insert: str):
    if (pos := _source.find(_tag)) > 0:
        return _source[:pos + len(_tag)] + _insert + _source[pos + len(_tag):]
    raise Exception(f'not found {_tag}')


def replace(_source: str, _tag: str, _insert: str):
    if (pos := _source.find(_tag)) > 0:
        return _source.replace(_tag, _insert)
    raise Exception(f'not found {_tag}')


def get_qt_version(_path: str):
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        result = re.search('QT_REPO_MODULE_VERSION "(\\d+).(\\d+).(\\d+)"', code)
        return int(result.group(1)), int(result.group(2)), int(result.group(3))
    return None, None, None


def PythonQt_Cpp_Modification(_path: str):
    insert1 = ('PythonQtObjectPtr PythonQt::getModule(const QString& name) {\n'
               '  PythonQtObjectPtr dict = PyImport_GetModuleDict();\n'
               '  return PyDict_GetItemString(dict, QStringToPythonCharPointer(name));\n}\n\n'
               'void PythonQt::removeModule(const QString &name) {\n'
               '  PythonQtObjectPtr dict = PyImport_GetModuleDict();\n'
               '  PyDict_SetItemString(dict, QStringToPythonCharPointer(name), Py_None);\n'
               '  PyDict_DelItemString(dict, QStringToPythonCharPointer(name));\n}\n\n')
    insert2 = ('\nvoid PythonQt_init(int flags, const QByteArray& pythonQtModuleName) {\n'
               '  PythonQt::init(flags, pythonQtModuleName);\n}\n\n'
               'PythonQt* PythonQt_self() {\n'
               '  return PythonQt::self();\n}\n\n'
               'PythonQtObjectPtr* PythonQt_CreateObjectPtr(PythonQtObjectPtr _ptr) {\n'
               '  return new PythonQtObjectPtr(_ptr);\n}\n\n')
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("PythonQtObjectPtr PythonQt::getModule") >= 0:
            print('PythonQt.cpp is Modified!')
            return
        code = frontInsert(code, 'PythonQtObjectPtr PythonQt::importModule', insert1)
        code += insert2
        f.seek(0, 0)
        f.write(code)
    return


def PythonQt_H_Modification(_path: str):
    insert1 = ('  //! get the given module of python\n'
               '  virtual PythonQtObjectPtr getModule(const QString &name);\n\n'
               '  //! remove the given module of python\n'
               '  virtual void removeModule(const QString &name);\n\n')
    insert2 = ('extern "C" PYTHONQT_EXPORT void PythonQt_init(int flags, const QByteArray& pythonQtModuleName);\n'
               'extern "C" PYTHONQT_EXPORT PythonQt* PythonQt_self();\n'
               'extern "C" PYTHONQT_EXPORT PythonQtObjectPtr* PythonQt_CreateObjectPtr(PythonQtObjectPtr _ptr);\n\n'
               'typedef void (*_PythonQt_init)(int,const QByteArray&);\n'
               'typedef PythonQt* (*_PythonQt_self)();\n'
               'typedef PythonQtObjectPtr* (*_PythonQt_CreateObjectPtr)(PythonQtObjectPtr _ptr);\n\n')
    virtualMethods = ['PythonQtObjectPtr getMainModule',
                      'PythonQtObjectPtr importModule',
                      'PythonQtObjectPtr createModuleFromFile',
                      'PythonQtObjectPtr createModuleFromScript',
                      'PythonQtObjectPtr createUniqueModule',
                      'void registerClass',
                      'void registerCPPClass',
                      'void evalFile']
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("virtual PythonQtObjectPtr getModule") >= 0:
            print('PythonQt.h is Modified!')
            return
        code = frontInsert(code, '  //! import the given module', insert1)
        code = rfrontInsert(code, '#endif', insert2)
        for virtualMethod in virtualMethods:
            code = frontInsert(code, virtualMethod, 'virtual ')
        f.seek(0, 0)
        f.write(code)
    return


def PythonQtObjectPtr_H_Modification(_path: str):
    virtualMethods = ['bool isNull',
                      'PyObject* operator->',
                      'PyObject& operator*',
                      'operator PyObject*',
                      'void setNewRef',
                      # 'PyObject* object',
                      'QVariant evalScript',
                      'QVariant evalCode',
                      'void evalFile',
                      'void addObject',
                      'void addVariable',
                      'void removeVariable',
                      'QVariant getVariable',
                      'QVariant call(const QString&',
                      'QVariant call(const QVariantList&']
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("virtual ~PythonQtObjectPtr") >= 0:
            print('PythonQtObjectPtr.h is Modified!')
            return
        code = frontInsert(code, '~PythonQtObjectPtr', 'virtual ')
        code = frontInsert(code, '~PythonQtSafeObjectPtr', 'virtual ')
        for virtualMethod in virtualMethods:
            code = frontInsert(code, virtualMethod, 'virtual ')
        f.seek(0, 0)
        f.write(code)
    return


def PythonQt_QtAll_Cpp_Modification(_path: str):
    insert1 = ('void PythonQt_QtAll_init() {\n'
               '    PythonQt_QtAll::init();\n'
               '}\n')
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("PythonQt_QtAll_init") >= 0:
            print('PythonQt_QtAll.cpp is Modified!')
            return
        code += insert1
        f.seek(0, 0)
        f.write(code)
    return


def PythonQt_QtAll_H_Modification(_path: str):
    insert1 = ('extern "C" PYTHONQT_QTALL_EXPORT void PythonQt_QtAll_init();\n'
               'typedef void (*_PythonQt_QtAll_init)();\n\n')
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("PythonQt_QtAll_init") >= 0:
            print('PythonQt_QtAll.h is Modified!')
            return
        code = rfrontInsert(code, '#endif', insert1)
        f.seek(0, 0)
        f.write(code)
    return


def pythonqt_pro_Modification(_path: str):
    with open(_path, 'r', encoding="utf8") as f:
        code = f.read()
        if code.find("SUBDIRS = generator") < 0:
            print('pythonqt.pro is Modified!')
            return
        code = replace(code, 'SUBDIRS = generator ', 'SUBDIRS = ')
    with open(_path, 'w', encoding="utf8") as f:
        f.write(code)
    return


def src_pro_Modification(_path: str):
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("DLLDESTDIR    = ../bin") >= 0:
            print('src.pro is Modified!')
            return
        code = backInsert(code, 'DESTDIR    = ../lib\n', 'DLLDESTDIR    = ../bin\n')
        code = backInsert(code, 'win32: target.path = /\n',
                          'win32: target.CONFIG = no_dll\nwin32: dlltarget.path = $$[QT_INSTALL_PREFIX]/bin\n')
        code = replace(code, 'win32: target.path = /', 'win32: target.path = $$[QT_INSTALL_PREFIX]/lib')
        code = replace(code, 'headers.path = $${INSTALL_PREFIX}/include',
                       'headers.path = $$[QT_INSTALL_PREFIX]/include/PythonQt')
        code = backInsert(code, 'INSTALLS += target headers', ' dlltarget')
        f.seek(0, 0)
        f.write(code)
    return


def PythonQt_QtAll_pro_Modification(_path: str):
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("DLLDESTDIR") > 0:
            print('PythonQt_QtAll.pro is Modified!')
            return
        if code.find("eval(CONFIG += $${PYTHONQTALL_CONFIG})") == 0:
            code = replace(code, 'CONFIG += $${PYTHONQTALL_CONFIG}', 'eval(CONFIG += $${PYTHONQTALL_CONFIG})')
        code = backInsert(code, 'DESTDIR    = ../../lib\n', 'DLLDESTDIR    = ../../bin\n')
        code = backInsert(code, 'win32: target.path = /\n',
                          'win32: target.CONFIG = no_dll\nwin32: dlltarget.path = $$[QT_INSTALL_PREFIX]/bin\n')
        code = replace(code, 'win32: target.path = /', 'win32: target.path = $$[QT_INSTALL_PREFIX]/lib')
        code = replace(code, 'headers.path = $${INSTALL_PREFIX}/include',
                       'headers.path = $$[QT_INSTALL_PREFIX]/include/PythonQt')
        code = backInsert(code, 'INSTALLS += target headers', ' dlltarget')
        f.seek(0, 0)
        f.write(code)
    return


def common_prf_Modification(_path: str):
    insert1 = ('        PYTHONQT_GENERATED_PATH = $$PWD/../generated_cpp_511\n'
               '      }\n      else:contains( QT_MINOR_VERSION, 15 ) {\n')
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("#CONFIG += debug_and_release") < 0:
            print('common.prf is Modified!')
            return
        code = replace(code, '#CONFIG += debug_and_release', 'CONFIG += debug_and_release')
        if code.find('generated_cpp_515') < 0:
            code = backInsert(code, 'else:contains( QT_MINOR_VERSION, 12 ) {\n', insert1)
        f.seek(0, 0)
        f.write(code)
    return


def typesystem_gui_Modification(_gui_path: str, _opengl_path: str):
    gui_tree = ET.parse(_gui_path)
    gui_root = gui_tree.getroot()
    element_list = []
    for sub_element in gui_root:
        if sub_element.get('name', '').find('QOpenGL') == 0:
            element_list.append(sub_element)
        if sub_element.get('class', '').find('QOpenGL') == 0:
            element_list.append(sub_element)

    assert len(element_list) > 0
    if element_list[0].get('before-version', '') == '6':
        print('typesystem_gui.xml is Modified! ')
        return
    for sub_element in element_list:
        sub_element.set('before-version', '6')
    gui_tree.write(_gui_path, encoding='UTF-8', xml_declaration=True)

    opengl_tree = ET.parse(_opengl_path)
    opengl_root = opengl_tree.getroot()
    for sub_element in opengl_root:
        if sub_element.tag != 'suppress-warning':
            sub_element.set('before-version', '6')
    for sub_element in reversed(element_list):
        sub_element.attrib.pop('before-version')
        sub_element.set('since-version', '6')
        opengl_root.insert(0, sub_element)
    opengl_tree.write(_opengl_path, encoding='UTF-8', xml_declaration=True)
    return


def codelistfind(_list: list, _str: str, _begin: int, _step: int, _max_count: int):
    count = 0
    while count <= _max_count and (_begin + _step * count) >= 0 and (_begin + _step * count) < len(_list):
        if _list[_begin + _step * count].find(_str) >= 0:
            return _begin + _step * count
        count += 1
    return -1


def PythonQt_QtAll_pro_Modification_opengl(_path: str):
    with open(_path, 'r+', encoding="utf8") as f:
        codelist = f.readlines()
    line_Opengl = codelistfind(codelist, "CONFIG += PythonQtOpengl", 0, 1, 9999999)
    assert line_Opengl > 0
    line_Opengl_rem = codelistfind(codelist, '# module is empty in Qt6', line_Opengl, -1, 1)
    if line_Opengl_rem < 0:
        print('PythonQt_QtAll.pro opengl module is Modified!')
        return
    if codelist[line_Opengl + 1].find('}') >= 0:
        del codelist[line_Opengl + 1]
    if codelist[line_Opengl - 1].find('# module is empty in Qt6') >= 0:
        del codelist[line_Opengl - 1]
    if codelist[line_Opengl - 2].find('lessThan(QT_MAJOR_VERSION, 6)') >= 0:
        del codelist[line_Opengl - 2]
    line_Opengl = codelistfind(codelist, '  QT += opengl', 0, 1, 9999999)
    assert line_Opengl > 0
    line_openglwidgets = codelistfind(codelist, 'equals(QT_MAJOR_VERSION, 6)', line_Opengl, 1, 1)
    if line_openglwidgets < 0:
        codelist.insert(line_Opengl + 1, '  equals(QT_MAJOR_VERSION, 6){\n')
        codelist.insert(line_Opengl + 2, '    QT += openglwidgets\n')
        codelist.insert(line_Opengl + 3, '  }\n')

    with open(_path, 'w', encoding="utf8") as f:
        f.writelines(codelist)
    return


def pythonQtModification(_path: str):
    PythonQtProPath = os.path.abspath(os.path.join(_path, './PythonQt.pro'))
    if not os.path.exists(PythonQtProPath):
        print(f'{PythonQtProPath} not exist!')
        return

    try:
        ver_major, ver_minor, ver_patch = get_qt_version(os.path.join(_path, '../qtbase/.cmake.conf'))
        if not ver_major:
            raise
        path = os.path.abspath(os.path.join(_path, './src/PythonQt.cpp'))
        PythonQt_Cpp_Modification(path)
        path = os.path.abspath(os.path.join(_path, './src/PythonQt.h'))
        PythonQt_H_Modification(path)
        path = os.path.abspath(os.path.join(_path, './src/PythonQtObjectPtr.h'))
        PythonQtObjectPtr_H_Modification(path)
        path = os.path.abspath(os.path.join(_path, './extensions/PythonQt_QtAll/PythonQt_QtAll.cpp'))
        PythonQt_QtAll_Cpp_Modification(path)
        path = os.path.abspath(os.path.join(_path, './extensions/PythonQt_QtAll/PythonQt_QtAll.h'))
        PythonQt_QtAll_H_Modification(path)
        path = os.path.abspath(os.path.join(_path, './PythonQt.pro'))
        pythonqt_pro_Modification(path)
        path = os.path.abspath(os.path.join(_path, './src/src.pro'))
        src_pro_Modification(path)
        path = os.path.abspath(os.path.join(_path, './extensions/PythonQt_QtAll/PythonQt_QtAll.pro'))
        PythonQt_QtAll_pro_Modification(path)
        path = os.path.abspath(os.path.join(_path, './build/common.prf'))
        common_prf_Modification(path)

        # 对于Qt6.x，opengl模块已经从gui中独立出来了，所以修改这个配置文件，可以独立控制是否编译
        typesystem_gui_Modification(os.path.join(_path, './generator/typesystem_gui.xml'),
                                    os.path.join(_path, './generator/typesystem_opengl.xml'))
        PythonQt_QtAll_pro_Modification_opengl(os.path.join(_path, './extensions/PythonQt_QtAll/PythonQt_QtAll.pro'))

        print('modification is over!')
    except Exception as e:
        print(f'modification {path} error! {e}')
        return


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='修改PythonQt源码，方便编译和动态加载')
    parser.add_argument('--path', '-p', metavar='PythonQt Path', type=str, help='指定PythonQt源码路径')
    args = vars(parser.parse_args())
    for (cmd, arg) in args.items():
        if (cmd == 'path' and arg):
            pythonQtModification(arg)

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助

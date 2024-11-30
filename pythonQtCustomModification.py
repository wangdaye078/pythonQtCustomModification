# 这是一个示例 Python 脚本。

import argparse
import os
import re
import xml.etree.ElementTree as ET


def frontInsert(_source, _tag, _insert):
    if (pos := _source.find(_tag)) > 0:
        return _source[:pos] + _insert + _source[pos:]
    raise Exception(f'not found {_tag}')


def rfrontInsert(_source, _tag, _insert):
    if (pos := _source.rfind(_tag)) > 0:
        return _source[:pos] + _insert + _source[pos:]
    raise Exception(f'not found {_tag}')


def backInsert(_source, _tag, _insert):
    if (pos := _source.find(_tag)) > 0:
        return _source[:pos + len(_tag)] + _insert + _source[pos + len(_tag):]
    raise Exception(f'not found {_tag}')


def replace(_source, _tag, _insert):
    if (pos := _source.find(_tag)) > 0:
        return _source.replace(_tag, _insert)
    raise Exception(f'not found {_tag}')


def get_qt_version(_path):
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        result = re.search('QT_REPO_MODULE_VERSION "(\\d+).(\\d+).(\\d+)"', code)
        return int(result.group(1)), int(result.group(2)), int(result.group(3))
    return None, None, None


def PythonQt_Cpp_Modification(_path) -> bool:
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
        if code.find("PythonQtObjectPtr PythonQt::getModule") > 0:
            return True
        code = frontInsert(code, 'PythonQtObjectPtr PythonQt::importModule', insert1)
        code += insert2
        f.seek(0, 0)
        f.write(code)
    return True


def PythonQt_H_Modification(_path) -> bool:
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
        if code.find("virtual PythonQtObjectPtr getModule") > 0:
            return True
        code = frontInsert(code, '  //! import the given module', insert1)
        code = rfrontInsert(code, '#endif', insert2)
        for virtualMethod in virtualMethods:
            code = frontInsert(code, virtualMethod, 'virtual ')
        f.seek(0, 0)
        f.write(code)
    return True


def PythonQtObjectPtr_H_Modification(_path) -> bool:
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
        if code.find("virtual ~PythonQtObjectPtr") > 0:
            return True
        code = frontInsert(code, '~PythonQtObjectPtr', 'virtual ')
        code = frontInsert(code, '~PythonQtSafeObjectPtr', 'virtual ')
        for virtualMethod in virtualMethods:
            code = frontInsert(code, virtualMethod, 'virtual ')
        f.seek(0, 0)
        f.write(code)
    return True


def PythonQt_QtAll_Cpp_Modification(_path):
    insert1 = ('void PythonQt_QtAll_init() {\n'
               '    PythonQt_QtAll::init();\n'
               '}\n')
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("PythonQt_QtAll_init") > 0:
            return
        code += insert1
        f.seek(0, 0)
        f.write(code)
    return


def PythonQt_QtAll_H_Modification(_path):
    insert1 = ('extern "C" PYTHONQT_QTALL_EXPORT void PythonQt_QtAll_init();\n'
               'typedef void (*_PythonQt_QtAll_init)();\n\n')
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("PythonQt_QtAll_init") > 0:
            return
        code = rfrontInsert(code, '#endif', insert1)
        f.seek(0, 0)
        f.write(code)
    return


def pythonqt_pro_Modification(_path):
    with open(_path, 'r', encoding="utf8") as f:
        code = f.read()
        code = replace(code, 'SUBDIRS = generator ', 'SUBDIRS = ')
    with open(_path, 'w', encoding="utf8") as f:
        f.write(code)
    return


def src_pro_Modification(_path):
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("DLLDESTDIR    = ../bin") > 0:
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


def PythonQt_QtAll_pro_Modification(_path):
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("DLLDESTDIR    = ../bin") > 0:
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


def common_prf_Modification(_path):
    insert1 = ('        PYTHONQT_GENERATED_PATH = $$PWD/../generated_cpp_511\n'
               '      }\n      else:contains( QT_MINOR_VERSION, 15 ) {\n')
    with open(_path, 'r+', encoding="utf8") as f:
        code = f.read()
        if code.find("#CONFIG += debug_and_release") == 0:
            return
        code = replace(code, '#CONFIG += debug_and_release', 'CONFIG += debug_and_release')
        if code.find('generated_cpp_515') == 0:
            code = backInsert(code, 'else:contains( QT_MINOR_VERSION, 12 ) {\n', insert1)
        f.seek(0, 0)
        f.write(code)
    return


def typesystem_gui_Modification(_gui_path, _opengl_path):
    gui_tree = ET.parse(_gui_path)
    gui_root = gui_tree.getroot()
    opengl_root = ET.Element('typesystem')
    opengl_root.set('package', 'com.trolltech.qt.OpenGL')
    element_list = []
    for sub_element in gui_root:
        if sub_element.get('name', '').find('QOpenGL') == 0:
            element_list.append(sub_element)
        if sub_element.get('class', '').find('QOpenGL') == 0:
            element_list.append(sub_element)

    if len(element_list) == 0:
        return

    for sub_element in element_list:
        gui_root.remove(sub_element)
        opengl_root.append(sub_element)

    opengl_tree = ET.ElementTree(opengl_root)
    opengl_tree.write(_opengl_path, encoding='UTF-8', xml_declaration=True)
    gui_tree.write(_opengl_path, encoding='UTF-8', xml_declaration=True)
    return


def codelistfind(_list, _str, _begin, _step, _max_count):
    count = 0
    while count < _max_count and (_begin + _step * count) >= 0 and (_begin + _step * count) < len(_list):
        count += 1
        if _list[_begin + _step * count].find(_str) >= 0:
            return _begin + _step * count
    return -1


def PythonQt_QtAll_pro_Modification_opengl(_path):
    with open(_path, 'r+', encoding="utf8") as f:
        codelist = f.readlines()
    line_Opengl = codelistfind(codelist, "CONFIG += PythonQtOpengl", 0, 1, 9999999)
    if line_Opengl >= 0:
        if codelist[line_Opengl + 1].find('}') >= 0:
            del codelist[line_Opengl + 1]
        if codelist[line_Opengl - 1].find('# module is empty in Qt6') >= 0:
            del codelist[line_Opengl - 1]
        if codelist[line_Opengl - 2].find('lessThan(QT_MAJOR_VERSION, 6)') >= 0:
            del codelist[line_Opengl - 2]
    line_Opengl = codelistfind(codelist, '  QT += opengl', 0, 1, 9999999)
    if line_Opengl >= 0:
        codelist[line_Opengl] = '  QT += openglwidgets opengl\n'

    with open(_path, 'w', encoding="utf8") as f:
        f.writelines(codelist)
    return


def pythonQtModification(_path):
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
        if ver_major >= 6:
            # 对于Qt6.x，opengl模块已经从gui中独立出来了，所以修改这个配置文件，可以独立控制是否编译
            typesystem_gui_Modification(os.path.join(_path, './generator/typesystem_gui.xml'),
                                        os.path.join(_path, './generator/typesystem_opengl.xml'))
            PythonQt_QtAll_pro_Modification_opengl(
                os.path.join(_path, './extensions/PythonQt_QtAll/PythonQt_QtAll.pro'))
            pass
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

pythonQt一般只能直接链接到程序，这样就限制了用户使用的Python版本。  
通过修改程序，可以使pythonQt支持动态加载，这样编译者可以编译多个pythonQt库，每个库针对一个常用的python版本，比如win7最高只能使用3.8，win10可以使用3.11或者3.12，启动后自动查找系统内安装的python，然后动态载入合适的pythonQt库。  
如果没找到合适的版本，则不载入pythonQt，只保留程序的基本功能，放弃脚本扩展。  
通过增大发布程序的体积，增加兼容性。  
pythonQtCustomModification.py为pythonQt的补丁脚本  
PythonQtLoader是我使用的动态载入代码，需要动态载入的可以参考后自己写。  

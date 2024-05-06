//********************************************************************
//  filename:   F:\mygit\ManageTools_src\GtManage\src\PythonQtLoad.h
//  desc:
//
//  created:    hying 18:4:2020   11:12
//********************************************************************
#ifndef PythonQtLoad_h__
#define PythonQtLoad_h__
#include <QtCore/QString>
#include <PythonQt.h>
#include <PythonQt_QtAll.h>
class PythonQtLoader :public QObject
{
	Q_OBJECT;
	typedef void(*_Py_SetPythonHome)(const wchar_t*);
	typedef void (*__PyModule_Clear)(PyObject*);
	typedef void(*_PyConfig_InitPythonConfig)(PyConfig* config);
	typedef PyStatus(*_PyConfig_SetArgv)(PyConfig* config, Py_ssize_t argc, wchar_t* const* argv);
	typedef PyStatus(*_Py_InitializeFromConfig)(const PyConfig* config);
public:
	PythonQtLoader(QObject* _parent);
	~PythonQtLoader();
	bool initPython(void);
	void loadCommonScript(const QString& _Dir);
	void loadExtraScript(const QString& _Dir);
	Q_INVOKABLE void loadMudule(const QString& _ModuleName, const QString& _Path);
	Q_INVOKABLE void unloadMudule(const QString& _ModuleName);
private:
	_Py_SetPythonHome m_pPy_SetPythonHome;
	__PyModule_Clear m_pPyModule_Clear;
	_PyConfig_InitPythonConfig m_pPyConfig_InitPythonConfig;
	_PyConfig_SetArgv m_pPyConfig_SetArgv;
	_Py_InitializeFromConfig m_pPy_InitializeFromConfig;
	_PythonQt_init m_pPythonQt_init;
	_PythonQt_self m_pPythonQt_self;
	_PythonQt_CreateObjectPtr m_pPythonQt_CreateObjectPtr;
	_PythonQt_QtAll_init m_pPythonQt_QtAll_init;
};
extern PythonQtLoader* g_pPythonQtLoader;

/*
struct A;
A a = createA();		createA是动态DLL的导出函数
这样函数的执行过程实际是在执行createA之前在栈里取了一块内存，然后在createA里使用定位new，构造了这个a变量。
然后在外部函数结束前执行A::~A来析构a，但是因为createA所在的DLL是动态加载的，所以主程序不知道A::~A在哪，
而即使设置了虚析构函数，但是虚函数只能通过类指针执行，a不是指针，所以无法析构，也就编译不过。

typedef A* (*_A_CreatePtr)(A _a);
A a;	先不管这个a是怎么来的。
......
A* pa = A_CreatePtr(a);		A_CreatePtr是动态DLL的导出函数
这个在执行A_CreatePtr的时候不会直接使用a，而是在栈里申请内存，构造一个a的复制品，然后传入A_CreatePtr，保证在函数里a复制品的改变不会影响a，
并在退出A_CreatePtr前对a的复制品执行析构。这个过程由于DLL的动态加载，也不知道A::A，所以也编译不过。

A* pa = A_CreatePtr(createA());
delete pa;
执行时先在栈里取一块内存，在createA里面对这块内存执行构造，然后因为这个变量不会再有其他地方使用，无需复制，直接把这块内存传入A_CreatePtr，
然后在A_CreatePtr里执行了析构。整个过程在主程序里不涉及构造和析构函数的隐式调用，所以完全没问题。
最后执行delete的时候，只要析构函数是虚函式。就可以通过类指针来执行，所以也没问题。
所有问题完美解决。
*/

#endif // PythonQtLoad_h__

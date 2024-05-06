#include "PythonQtLoader.h"
#include <QtCore/QThread>
#include <QtCore/QDir>
#include <QtCore/QLibrary>
#include <QtCore/QFileInfo>
#include <QtCore/QProcessEnvironment>
#include <QtWidgets/QApplication>
#include <QtXml/QDomDocument>
#include <QtXml/QDomElement>
#include "QT_ClientCtrl.h"
#include "QT_ServerModel.h"
#include "QTW_Maintain.h"
#include "QTW_Manage.h"

PythonQtLoader* g_pPythonQtLoader;

struct TPythonLib
{
	QString path;
	bool havedebug;
	TPythonLib(const QString& _path = "", bool _havedebug = false) : path(_path), havedebug(_havedebug) {};
};
void FindPythonVersion(QMap<int, TPythonLib>& _mapVer)
{
	_mapVer.clear();
	QProcessEnvironment t_SysEnvironment = QProcessEnvironment::systemEnvironment();
	QString t_Paths = t_SysEnvironment.value("PATH");
	QStringList t_PathList = t_Paths.split(";", QString::SkipEmptyParts);
	foreach(QString t_Path, t_PathList)
	{
		QFileInfoList t_FileInfos = QDir(t_Path).entryInfoList(QStringList() << "python3[0-9]*.*", QDir::Files);
		foreach(QFileInfo t_FileInfo, t_FileInfos)
		{
			if (!QLibrary::isLibrary(t_FileInfo.absoluteFilePath()))
				continue;
			QString t_Ver = t_FileInfo.completeBaseName().mid(QString("python").length());
			if (t_Ver.isEmpty() || t_Ver.toInt() == 0)
				continue;
			QString t_DebugVerFile = t_FileInfo.absolutePath() + "/python" + t_Ver + "_d." + t_FileInfo.suffix();
			bool t_HaveDebug = QFileInfo::exists(t_DebugVerFile);
			_mapVer.insert(t_Ver.toInt(), TPythonLib(t_Path, t_HaveDebug));
			qDebug() << "find python ver:" << t_Ver;
		}
	}
}

PythonQtLoader::PythonQtLoader(QObject* _parent)
	:QObject(_parent)
{
	g_pPythonQtLoader = this;
}
bool PythonQtLoader::initPython(void)
{
	QMap<int, TPythonLib> t_PythonLibs;
	FindPythonVersion(t_PythonLibs);
	if (t_PythonLibs.size() == 0)
		return false;
	PythonQtObjectPtr* t_pPythonMainModule = NULL;
	for (QMap<int, TPythonLib>::iterator i = --t_PythonLibs.end(); i != --t_PythonLibs.begin(); --i)
	{
		QString t_szPythonQt = "PythonQt-Qt5-Python" + QString::number(i.key()).insert(1, ".");
		QString t_szPythonQt_QtAll = "PythonQt_QtAll-Qt5-Python" + QString::number(i.key()).insert(1, ".");
		QString t_szPython = "python" + QString::number(i.key());
#ifndef NDEBUG
		if (i.value().havedebug)
		{
			t_szPythonQt += "_d";
			t_szPythonQt_QtAll += "_d";
			t_szPython += "_d";
		}
#endif
		QLibrary t_PythonLib(t_szPython);
		qDebug() << "load " << t_szPython;
		if (!t_PythonLib.load())
		{
			qDebug() << t_szPython << " load fail";
			continue;
		}
		QLibrary t_PythonQtLib(t_szPythonQt);
		qDebug() << "load " << t_szPythonQt;
		if (!t_PythonQtLib.load())
		{
			qDebug() << t_szPythonQt << " load fail";
			continue;
		}
		QLibrary t_PythonQt_QtAllLib(t_szPythonQt_QtAll);
		qDebug() << "load " << t_szPythonQt_QtAll;
		if (!t_PythonQt_QtAllLib.load())
		{
			qDebug() << t_szPythonQt_QtAll << " load fail";
			continue;
		}
		m_pPy_SetPythonHome = (_Py_SetPythonHome)t_PythonLib.resolve("Py_SetPythonHome");
		m_pPyModule_Clear = (__PyModule_Clear)t_PythonLib.resolve("_PyModule_Clear");
		m_pPyConfig_InitPythonConfig = (_PyConfig_InitPythonConfig)t_PythonLib.resolve("PyConfig_InitPythonConfig");
		m_pPyConfig_SetArgv = (_PyConfig_SetArgv)t_PythonLib.resolve("PyConfig_SetArgv");
		m_pPy_InitializeFromConfig = (_Py_InitializeFromConfig)t_PythonLib.resolve("Py_InitializeFromConfig");
		Q_ASSERT(m_pPy_SetPythonHome != NULL && m_pPyModule_Clear != NULL &&
			m_pPyConfig_InitPythonConfig != NULL && m_pPyConfig_SetArgv != NULL && m_pPy_InitializeFromConfig != NULL);
		m_pPy_SetPythonHome((wchar_t*)(i.value().path).utf16());
		m_pPythonQt_init = (_PythonQt_init)t_PythonQtLib.resolve("PythonQt_init");
		m_pPythonQt_self = (_PythonQt_self)t_PythonQtLib.resolve("PythonQt_self");
		m_pPythonQt_CreateObjectPtr = (_PythonQt_CreateObjectPtr)t_PythonQtLib.resolve("PythonQt_CreateObjectPtr");
		m_pPythonQt_QtAll_init = (_PythonQt_QtAll_init)t_PythonQt_QtAllLib.resolve("PythonQt_QtAll_init");
		Q_ASSERT(m_pPythonQt_init != NULL && m_pPythonQt_self != NULL && m_pPythonQt_CreateObjectPtr != NULL && m_pPythonQt_QtAll_init != NULL);
		qDebug() << "resolve PythonQt Module over ";
		m_pPythonQt_init(PythonQt::IgnoreSiteModule | PythonQt::RedirectStdOut, QByteArray());
		qDebug() << "PythonQt_init over ";
		m_pPythonQt_QtAll_init();
		qDebug() << "PythonQt_QtAll_init over ";
		PythonQt* t_pPythonQt = m_pPythonQt_self();
		qDebug() << "PythonQt_self over ";
		return true;
	}
	return false;
}
void PythonQtLoader::loadCommonScript(const QString& _Dir)
{
	PythonQt* t_pPythonQt = m_pPythonQt_self();
	qDebug() << "PythonQt_self over ";
	//不知道哪些类需要显式注册，因为大多数类似乎可以自动注册，比如GtManage下的那些子窗口
	t_pPythonQt->registerClass(&QT_ClientCtrl::staticMetaObject, "GtManage");
	t_pPythonQt->registerClass(&QT_ServerModel::staticMetaObject, "GtManage");
	t_pPythonQt->registerClass(&TRunProcess::staticMetaObject, "GtManage");
	t_pPythonQt->registerCPPClass("QProcessSet", "", "GtManage", PythonQtCreateObject<QProcessSetWrapper>);
	//t_pPythonQt->registerCPPClass("TRunProcess", "", "GtManage", PythonQtCreateObject<TRunProcessWrapper>);
	t_pPythonQt->registerCPPClass("PROTO_MANAGERTOOL", "", "GtManage", PythonQtCreateObject<PythonQtWrapper_PROTO_MANAGERTOOL>);
	qDebug() << "registerClass over ";
	PythonQtObjectPtr* t_pPythonMainModule = m_pPythonQt_CreateObjectPtr(t_pPythonQt->getMainModule());
	Q_ASSERT(!t_pPythonMainModule->isNull());
	t_pPythonMainModule->addObject("g_GtManage", g_pManage);
	t_pPythonMainModule->addObject("g_App", g_app);
	QStringList t_Files = QDir(_Dir).entryList(QStringList() << "*.py", QDir::Files);
	foreach(QString t_File, t_Files)
	{
		t_pPythonMainModule->evalFile(_Dir + t_File);
	}
	delete t_pPythonMainModule;
}
void PythonQtLoader::loadExtraScript(const QString& _Dir)
{
	QStringList t_Files = QDir(_Dir).entryList(QStringList() << "*.py", QDir::Files);
	foreach(QString t_File, t_Files)
	{
		PyConfig t_PyConfig;
		m_pPyConfig_InitPythonConfig(&t_PyConfig);
		QString t_ScriptPath = _Dir + t_File;
		wchar_t* const t_PyArgv[] = { const_cast<wchar_t*>(L""), (wchar_t*)(t_ScriptPath.utf16()) };
		int t_PyArgc = _countof(t_PyArgv);
		PyStatus t_status = m_pPyConfig_SetArgv(&t_PyConfig, t_PyArgc, t_PyArgv);
		if (t_status._type == PyStatus::_PyStatus_TYPE_OK)
			Py_InitializeFromConfig(&t_PyConfig);

		QString t_ModuleName = QFileInfo(t_File).baseName();
		PythonQtObjectPtr* t_Module = m_pPythonQt_CreateObjectPtr(m_pPythonQt_self()->createModuleFromScript(t_ModuleName));
		t_Module->addObject("g_GtManage", g_pManage);
		t_Module->addVariable("__file__", t_ScriptPath);
		t_Module->evalFile(t_ScriptPath);
		t_Module->call("main", QVariantList() << true);
		delete t_Module;
	}
}
void PythonQtLoader::loadMudule(const QString& _ModuleName, const QString& _Path)
{
	PythonQtObjectPtr* t_Module = m_pPythonQt_CreateObjectPtr(m_pPythonQt_self()->getModule(_ModuleName));
	if (t_Module->isNull())
	{
		t_Module = m_pPythonQt_CreateObjectPtr(m_pPythonQt_self()->createModuleFromScript(_ModuleName));
		t_Module->addObject("g_GtManage", g_pManage);
		t_Module->addVariable("__file__", _Path);
		t_Module->evalFile(_Path);
		t_Module->call("main", QVariantList() << true);
	}
	delete t_Module;
}
void PythonQtLoader::unloadMudule(const QString& _ModuleName)
{
	PythonQtObjectPtr* t_Module = m_pPythonQt_CreateObjectPtr(m_pPythonQt_self()->getModule(_ModuleName));
	if (!t_Module->isNull())
	{
		t_Module->call("main", QVariantList() << false);
		//释放模块功能
		m_pPyModule_Clear(*t_Module);
		//从模块列表里删除
		m_pPythonQt_self()->removeModule(_ModuleName);
	}
	delete t_Module;
}
PythonQtLoader::~PythonQtLoader()
{
}
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

void ReorganizePythonVersion(QList<TPythonVer>& _listVer, QMap<TPythonVer, int>& _mapVer, const TPythonVer& _PriorityVersion)
{
	//如果指定了优先使用的版本，那就把它放最前面，然后按版本号从大到小顺序放入
	if (!_PriorityVersion.MajorVersion.isEmpty())
	{
		QMap<TPythonVer, int>::iterator t_iter = _mapVer.find(_PriorityVersion);
		if (t_iter != _mapVer.end())
		{
			_listVer.append(t_iter.key());
			_mapVer.erase(t_iter);
		}
	}
	for (QMap<TPythonVer, int>::iterator i = --_mapVer.end(); i != --_mapVer.begin(); --i)
	{
		_listVer.append(i.key());
	}
}
#if defined(Q_OS_WIN)
void PythonQtLoader::FindPythonVersion(QList<TPythonVer>& _listVer)
{
	_listVer.clear();
	QMap<TPythonVer, int> t_mapVer;		//QSet好像只支持HASH，不支持自定义比较函数
	QProcessEnvironment t_SysEnvironment = QProcessEnvironment::systemEnvironment();
	QString t_Paths = t_SysEnvironment.value("PATH");
	QStringList t_PathList = t_Paths.split(";", Qt::SkipEmptyParts);
	//如果指定了home路径，则优先找这个
	if (!m_PythonHome.isEmpty())
		t_PathList.append(m_PythonHome);

	QString t_DebugExt = "";
#ifndef NDEBUG
	t_DebugExt = "_d";
#endif
	QString t_PythonQtName = QString("python*.dll");
	QRegExp t_PythonQtNameReg(QString("python([0-9])([0-9]+)%1").arg(t_DebugExt));
	foreach(QString t_Path, t_PathList)
	{
		QFileInfoList t_FileInfos = QDir(t_Path).entryInfoList(QStringList() << t_PythonQtName, QDir::Files);
		foreach(QFileInfo t_FileInfo, t_FileInfos)
		{
			if (!QLibrary::isLibrary(t_FileInfo.absoluteFilePath()))
				continue;
			QString t_CompleteBaseName = t_FileInfo.completeBaseName();
			if (t_PythonQtNameReg.indexIn(t_CompleteBaseName) == -1)
				continue;
			TPythonVer t_PythonVer(t_PythonQtNameReg.cap(1), t_PythonQtNameReg.cap(2));
			//相同版本只保留最前面的那个
			if (t_mapVer.find(t_PythonVer) != t_mapVer.end())
				continue;
			//windows下，PythonHome就是库文件所在目录
			t_PythonVer.path = QDir(t_Path).absolutePath();
			t_mapVer.insert(t_PythonVer, 0);
			qDebug() << "find python ver:" << t_PythonVer.MajorVersion << "." << t_PythonVer.MinorVersion;
		}
	}
	ReorganizePythonVersion(_listVer, t_mapVer, m_PriorityVersion);
}
#elif defined(Q_OS_LINUX)
void PythonQtLoader::FindPythonVersion(QList<TPythonVer>& _listVer)
{
	_listVer.clear();
	QMap<TPythonVer, int> t_mapVer;

	QProcess t_ldconfig;
	t_ldconfig.start("ldconfig", QStringList() << "-p");
	t_ldconfig.waitForFinished();
	QString t_out = QString(t_ldconfig.readAllStandardOutput());
	//QFile t_file("z:/ldconfig-p.txt");
	//t_file.open(QIODevice::ReadOnly | QIODevice::Text);
	//QString t_out = QString(t_file.readAll());

	QStringList t_lines = t_out.split('\n', Qt::SkipEmptyParts);
	QRegExp t_PythonQtNameReg(QString("libpython([0-9]).([0-9]+)\\.so$"));
	foreach(QString t_line, t_lines)
	{
		QStringList t_sub = t_line.split(' ', Qt::SkipEmptyParts);
		if (t_sub.size() != 4)
			continue;
		if (t_PythonQtNameReg.indexIn(t_sub[0]) == -1)
			continue;
		TPythonVer t_PythonVer(t_PythonQtNameReg.cap(1), t_PythonQtNameReg.cap(2));
		//相同版本只保留最前面的那个
		if (t_mapVer.find(t_PythonVer) != t_mapVer.end())
			continue;
		t_PythonVer.path = QFileInfo(t_sub[3]).absolutePath();
		t_mapVer.insert(t_PythonVer, 0);
		qDebug() << "find python ver:" << t_PythonVer.MajorVersion << "." << t_PythonVer.MinorVersion;
	}
	ReorganizePythonVersion(_listVer, t_mapVer, m_PriorityVersion);
}
#endif

PythonQtLoader::PythonQtLoader(QObject* _parent)
	:QObject(_parent)
{
	g_pPythonQtLoader = this;
}
void PythonQtLoader::setPythonHome(const QString& _Dir)
{
	m_PythonHome = QDir(_Dir).absolutePath();
	//在ubuntu2204，大概应该设置路径为/usr, 通过import sys/nprint(sys.prefix)得到
}
void PythonQtLoader::setPythonVersionPriority(const QString& _Version)
{
	int t_pos = _Version.indexOf(".");
	if ((t_pos) >= 0)
	{
		m_PriorityVersion.MajorVersion = _Version.mid(0, t_pos);
		m_PriorityVersion.MinorVersion = _Version.mid(t_pos + 1);
	}
	else
	{
		m_PriorityVersion.MajorVersion = _Version.mid(0, 1);
		m_PriorityVersion.MinorVersion = _Version.mid(1);
	}
}
#include <Python.h>
bool PythonQtLoader::initPython(void)
{
	QList<TPythonVer> t_PythonVers;
	FindPythonVersion(t_PythonVers);
	if (t_PythonVers.size() == 0)
		return false;
	for (QList<TPythonVer>::iterator i = t_PythonVers.begin(); i != t_PythonVers.end(); ++i)
	{
		QString t_szPythonQt = QString("PythonQt-Qt5-Python%1.%2").arg(i->MajorVersion).arg(i->MinorVersion);
		QString t_szPythonQt_QtAll = QString("PythonQt_QtAll-Qt5-Python%1.%2").arg(i->MajorVersion).arg(i->MinorVersion);
#if defined(Q_OS_WIN)
		QString t_szPython = QString("python%1%2").arg(i->MajorVersion).arg(i->MinorVersion);
#elif defined(Q_OS_LINUX)
		QString t_szPython = QString("python%1.%2").arg(i->MajorVersion).arg(i->MinorVersion);//libpython3.10.so，前后都可以由Qt自动加上
#endif
#ifndef NDEBUG
		t_szPythonQt += "_d";
		t_szPythonQt_QtAll += "_d";
#if defined(Q_OS_WIN)
		t_szPython += "_d";
#endif
#endif
		//加上路径，保证是载入指定的那个，而不是其他的什么地方的版本
		QLibrary t_PythonLib(i->path + "/" + t_szPython);
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
#if defined(Q_OS_WIN)
		m_pPy_SetPythonHome((wchar_t*)(i->path).utf16());
#elif defined(Q_OS_LINUX)
		if (m_PythonHome.isEmpty())
		{
			QProcess t_ProcessPython;
			t_ProcessPython.start("python3", QStringList() << "-c" << "import sys;print(sys.prefix)");
			t_ProcessPython.waitForFinished();
			m_PythonHome = QString(t_ProcessPython.readAllStandardOutput());
		}
		m_pPy_SetPythonHome((wchar_t*)(m_PythonHome).utf16());
#endif
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
			m_pPy_InitializeFromConfig(&t_PyConfig);

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
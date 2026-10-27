#include <QAction>
#include <QApplication>
#include <QDebug>
#include <QDesktopServices>
#include <QDir>
#include <QFileIconProvider>
#include <QFileInfo>
#include <QIcon>
#include <QMenu>
#include <QProcess>
#include <QSystemTrayIcon>
#include <QTimer>
#include <QUrl>

class GoogleCalendarReminder : public QObject
{
private:
    QString _icon = QDir(QApplication::applicationDirPath()).filePath("GoogleCalendarReminder.svg");
    int _update_interval = 2 * 60 * 1000;

    QSystemTrayIcon _trayIcon;
    QMenu _trayMenu;
    QTimer _timer;

public:
    GoogleCalendarReminder()
    {
        connect(qApp, &QApplication::aboutToQuit, &_trayIcon, &QSystemTrayIcon::hide);
#if defined (Q_OS_WIN)
        QIcon icon = QFileIconProvider().icon(QFileInfo(QApplication::applicationFilePath()));
        if (icon.isNull())
            icon = QIcon(_icon);
        _trayIcon.setIcon(icon);
#else
        _trayIcon.setIcon(QIcon(_icon));
#endif
        connect(&_trayIcon, &QSystemTrayIcon::activated, this, &GoogleCalendarReminder::_on_tray_icon_activated);

        _trayIcon.setContextMenu(&_trayMenu);
        connect(_trayMenu.addAction("Open Google Calendar"), &QAction::triggered, this, &GoogleCalendarReminder::_open_google_calendar);
        connect(_trayMenu.addAction("Show Agenda"), &QAction::triggered, this, &GoogleCalendarReminder::_show_agenda);
        _trayMenu.addSeparator();
        connect(_trayMenu.addAction("Remind Now"), &QAction::triggered, this, &GoogleCalendarReminder::_remind_now);
        QAction *autoRemind = _trayMenu.addAction("Remind Automatically");
        autoRemind->setCheckable(true);
        autoRemind->setChecked(true);
        connect(autoRemind, &QAction::triggered, this, &GoogleCalendarReminder::_on_auto_remind_toggled);
        _trayMenu.addSeparator();
        connect(_trayMenu.addAction("Exit"), &QAction::triggered, qApp, &QApplication::quit);

        _timer.setSingleShot(false);
        _timer.setInterval(_update_interval);
        connect(&_timer, &QTimer::timeout, this, &GoogleCalendarReminder::_remind_now);
        _timer.start();

        QTimer::singleShot(1000, this, &GoogleCalendarReminder::_remind_now);
    }

    void show()
    {
        while (!_trayIcon.geometry().isValid())
        {
            _trayIcon.hide();
            _trayIcon.show();
        }
    }

private:
    void _open_google_calendar()
    {
        QDesktopServices::openUrl(QUrl("https://calendar.google.com"));
    }

    void _show_notification(const QString &text)
    {
#if defined (Q_OS_WIN)
        bool success = false;
#else
        bool success = QProcess::startDetached("notify-send", {
            "-u", "critical",
            "-i", _icon,
            "-a", "GoogleCalendarReminder",
            "Google Calendar Reminder",
            text
        });
#endif
        if (!success)
            _trayIcon.showMessage("Google Calendar Reminder", text, _trayIcon.icon());
    }

    QString _call_gcalcli(const QStringList &args)
    {
        QProcess process;
#if defined (Q_OS_WIN)
        process.start("wsl", QStringList{"gcalcli"} + args);
#else
        process.start("gcalcli", args);
#endif
        if (!process.waitForStarted())
        {
            qCritical() << process.errorString();
            return process.errorString();
        }
        process.waitForFinished();
        if (process.exitStatus() != QProcess::NormalExit)
        {
            QString err = "gcalcli process crashed:\n" + QString::fromUtf8(process.readAllStandardError().constData());
            qCritical() << err;
            return err;
        }
        if (process.exitCode() != 0)
        {
            QString err = "gcalcli process exited with non-zero code:\n" + QString::fromUtf8(process.readAllStandardError().constData());
            qCritical() << err;
            return err;
        }
        return QString::fromUtf8(process.readAllStandardOutput().constData());
    }

    void _update_agenda()
    {
        _trayIcon.setToolTip(_call_gcalcli({"--nocolor", "agenda"}));
    }

    void _show_agenda()
    {
        _update_agenda();
        _show_notification(_trayIcon.toolTip());
    }

    void _remind_now()
    {
        QString remind_text = _call_gcalcli({"remind", "10", "echo %s"});
        if (!remind_text.isEmpty())
        {
            _show_notification(remind_text);
            _update_agenda();
        }
    }

    void _on_tray_icon_activated(QSystemTrayIcon::ActivationReason reason)
    {
        if (reason == QSystemTrayIcon::DoubleClick || reason == QSystemTrayIcon::MiddleClick)
            _open_google_calendar();
        else if (reason == QSystemTrayIcon::Trigger)
            _show_agenda();
    }

    void _on_auto_remind_toggled(bool checked)
    {
        if (checked && _timer.isActive())
            return;
        if (checked)
            _timer.start();
        else
            _timer.stop();
    }
};

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    app.setQuitOnLastWindowClosed(false);
    GoogleCalendarReminder reminder;
    reminder.show();
    return app.exec();
}

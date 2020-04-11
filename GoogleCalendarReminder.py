#!/usr/bin/env python3

import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class GoogleCalendarReminder(QtCore.QObject):
    def __init__(self):
        super(GoogleCalendarReminder, self).__init__()
        self.trayIcon = QtWidgets.QSystemTrayIcon()
        QtWidgets.qApp.aboutToQuit.connect(self.trayIcon.hide)
        icon = QtGui.QIcon.fromTheme("appointment-soon")
        self.trayIcon.setIcon(icon)
        self.trayIcon.activated.connect(self._on_tray_icon_activated)

        self.trayMenu = QtWidgets.QMenu()
        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayMenu.addAction("Open Google Calendar").triggered.connect(self._open_google_calendar)
        self.trayMenu.addSeparator()
        self.trayMenu.addAction("Remind Now").triggered.connect(self._remind_now)
        autoRemind = self.trayMenu.addAction("Remind Automatically")
        autoRemind.setCheckable(True)
        autoRemind.setChecked(True)
        autoRemind.triggered.connect(self._on_auto_remind_toggled)
        self.trayMenu.addSeparator()
        self.trayMenu.addAction("Exit").triggered.connect(QtWidgets.qApp.quit)

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.setInterval(2 * 60 * 1000)
        self.timer.timeout.connect(self._remind_now)
        self.timer.start()

        QtCore.QTimer.singleShot(1000, self._remind_now)

    def show(self):
        self.trayIcon.show()

    def _open_google_calendar(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://calendar.google.com"))

    def _remind_now(self):
        remind_process = QtCore.QProcess()
        remind_process.start("/usr/bin/gcalcli", ["remind", "10"])
        remind_process.waitForFinished()
        agenda_process = QtCore.QProcess()
        agenda_process.start("/usr/bin/gcalcli", ["--nocolor", "agenda"])
        agenda_process.waitForFinished()
        self.trayIcon.setToolTip(agenda_process.readAllStandardOutput().data().decode('utf8'))

    def _on_tray_icon_activated(self, reason):
        if reason in [QtWidgets.QSystemTrayIcon.DoubleClick, QtWidgets.QSystemTrayIcon.MiddleClick]:
            self._open_google_calendar()
        elif reason == QtWidgets.QSystemTrayIcon.Trigger:
            self._remind_now()
            # self.trayIcon.showMessage("Calendar", self.trayIcon.toolTip(), self.trayIcon.icon())
            QtCore.QProcess.startDetached("/usr/bin/notify-send", [
                "-u", "critical",
                "-i", "appointment-soon",
                "-a", "gcalcli",
                "Google Calendar Reminder",
                self.trayIcon.toolTip()
            ])

    def _on_auto_remind_toggled(self, checked):
        if checked and self.timer.isActive():
            return
        if checked:
            self.timer.start()
        else:
            self.timer.stop()


def main():
    app = QtWidgets.QApplication([])
    reminder = GoogleCalendarReminder()
    reminder.show()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())

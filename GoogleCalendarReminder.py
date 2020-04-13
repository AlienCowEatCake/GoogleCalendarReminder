#!/usr/bin/env python3

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class GoogleCalendarReminder(QtCore.QObject):
    icon = os.path.join(os.path.dirname(os.path.realpath(__file__)), "GoogleCalendarReminder.svg")
    update_interval = 2 * 60 * 1000

    def __init__(self):
        super(GoogleCalendarReminder, self).__init__()
        self.trayIcon = QtWidgets.QSystemTrayIcon()
        QtWidgets.qApp.aboutToQuit.connect(self.trayIcon.hide)
        icon = QtGui.QIcon(self.icon)
        self.trayIcon.setIcon(icon)
        self.trayIcon.activated.connect(self._on_tray_icon_activated)

        self.trayMenu = QtWidgets.QMenu()
        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayMenu.addAction("Open Google Calendar").triggered.connect(self._open_google_calendar)
        self.trayMenu.addAction("Show Agenda").triggered.connect(self._show_agenda)
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
        self.timer.setInterval(self.update_interval)
        self.timer.timeout.connect(self._remind_now)
        self.timer.start()

        QtCore.QTimer.singleShot(1000, self._remind_now)

    def show(self):
        self.trayIcon.show()

    def _open_google_calendar(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://calendar.google.com"))

    def _show_notification(self, text):
        if not QtCore.QProcess.startDetached("notify-send", [
            "-u", "critical",
            "-i", self.icon,
            "-a", "GoogleCalendarReminder",
            "Google Calendar Reminder",
            text
        ]):
            self.trayIcon.showMessage("Google Calendar Reminder", text, self.trayIcon.icon())

    def _update_agenda(self):
        process = QtCore.QProcess()
        process.start("gcalcli", ["--nocolor", "agenda"])
        process.waitForFinished()
        self.trayIcon.setToolTip(process.readAllStandardOutput().data().decode('utf8'))

    def _show_agenda(self):
        self._update_agenda()
        self._show_notification(self.trayIcon.toolTip())

    def _remind_now(self):
        process = QtCore.QProcess()
        process.start("gcalcli", ["remind", "10", "echo %s"])
        process.waitForFinished()
        remind_text = process.readAllStandardOutput().data().decode('utf8')
        if remind_text:
            self._show_notification(remind_text)
        self._update_agenda()

    def _on_tray_icon_activated(self, reason):
        if reason in [QtWidgets.QSystemTrayIcon.DoubleClick, QtWidgets.QSystemTrayIcon.MiddleClick]:
            self._open_google_calendar()
        elif reason == QtWidgets.QSystemTrayIcon.Trigger:
            self._remind_now()
            self._show_agenda()

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

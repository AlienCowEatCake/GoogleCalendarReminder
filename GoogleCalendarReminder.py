#!/usr/bin/env python3

import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class GoogleCalendarReminder(QtCore.QObject):
    _icon = os.path.join(os.path.dirname(os.path.realpath(__file__)), "GoogleCalendarReminder.svg")
    _update_interval = 2 * 60 * 1000

    def __init__(self):
        super(GoogleCalendarReminder, self).__init__()
        self._trayIcon = QtWidgets.QSystemTrayIcon()
        QtWidgets.qApp.aboutToQuit.connect(self._trayIcon.hide)
        self._trayIcon.setIcon(QtGui.QIcon(self._icon))
        self._trayIcon.activated.connect(self._on_tray_icon_activated)

        self._trayMenu = QtWidgets.QMenu()
        self._trayIcon.setContextMenu(self._trayMenu)
        self._trayMenu.addAction("Open Google Calendar").triggered.connect(self._open_google_calendar)
        self._trayMenu.addAction("Show Agenda").triggered.connect(self._show_agenda)
        self._trayMenu.addSeparator()
        self._trayMenu.addAction("Remind Now").triggered.connect(self._remind_now)
        autoRemind = self._trayMenu.addAction("Remind Automatically")
        autoRemind.setCheckable(True)
        autoRemind.setChecked(True)
        autoRemind.triggered.connect(self._on_auto_remind_toggled)
        self._trayMenu.addSeparator()
        self._trayMenu.addAction("Exit").triggered.connect(QtWidgets.qApp.quit)

        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(False)
        self._timer.setInterval(self._update_interval)
        self._timer.timeout.connect(self._remind_now)
        self._timer.start()

        QtCore.QTimer.singleShot(1000, self._remind_now)

    def show(self):
        while not self._trayIcon.geometry().isValid():
            self._trayIcon.hide()
            self._trayIcon.show()

    def _open_google_calendar(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://calendar.google.com"))

    def _show_notification(self, text):
        if not QtCore.QProcess.startDetached("notify-send", [
            "-u", "critical",
            "-i", self._icon,
            "-a", "GoogleCalendarReminder",
            "Google Calendar Reminder",
            text
        ]):
            self._trayIcon.showMessage("Google Calendar Reminder", text, self._trayIcon.icon())

    def _update_agenda(self):
        process = QtCore.QProcess()
        process.start("gcalcli", ["--nocolor", "agenda"])
        process.waitForFinished()
        self._trayIcon.setToolTip(process.readAllStandardOutput().data().decode('utf8'))

    def _show_agenda(self):
        self._update_agenda()
        self._show_notification(self._trayIcon.toolTip())

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
            self._show_agenda()

    def _on_auto_remind_toggled(self, checked):
        if checked and self._timer.isActive():
            return
        if checked:
            self._timer.start()
        else:
            self._timer.stop()


def main():
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    reminder = GoogleCalendarReminder()
    reminder.show()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())

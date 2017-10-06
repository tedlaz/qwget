import sys
import os
import re
import subprocess
from PyQt5 import QtCore as Qc
from PyQt5 import QtGui as Qg
from PyQt5 import QtWidgets as Qw
from PyQt5 import QtWebKitWidgets as Qwkit
INIT_URL = "https://alexandria-library.space/files/"


class Fwget(Qw.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = Qc.QSettings()
        vlayout = Qw.QVBoxLayout(self)
        url_layout = Qw.QHBoxLayout()
        self.url = Qw.QLineEdit(self)
        self.burl = Qw.QToolButton(self)
        self.burl.setArrowType(Qc.Qt.DownArrow)
        url_layout.addWidget(self.url)
        url_layout.addWidget(self.burl)
        vlayout.addLayout(url_layout)
        # Webkit
        self.web = Qwkit.QWebView(self)
        url = self.settings.value("save_url",
                                  defaultValue=INIT_URL)
        self.web.setUrl(Qc.QUrl(url))
        vlayout.addWidget(self.web)
        sp1 = Qw.QSpacerItem(20, 10, Qw.QSizePolicy.Minimum,
                             Qw.QSizePolicy.Minimum)
        vlayout.addItem(sp1)
        # Path layout
        path_layout = Qw.QHBoxLayout()
        vlayout.addLayout(path_layout)
        path_layout.addWidget(Qw.QLabel('Save Path :'))
        self.save_path = Qw.QLineEdit(self)
        save_path = self.settings.value("save_path", defaultValue='')
        self.save_path.setText(save_path)
        path_layout.addWidget(self.save_path)
        self.bpath = Qw.QToolButton(self)
        self.bpath.setText('...')
        path_layout.addWidget(self.bpath)
        ext_layout = Qw.QHBoxLayout()
        vlayout.addLayout(ext_layout)
        ext_layout.addWidget(Qw.QLabel('File extensions :'))
        self.extensions = Qw.QLineEdit(self)
        ext = self.settings.value("ext", defaultValue='mp4,mp3,pdf,jpg')
        self.extensions.setText(ext)
        self.extensions.setToolTip('Comma separated file extensions')
        ext_layout.addWidget(self.extensions)
        button_layout = Qw.QHBoxLayout()
        vlayout.addLayout(button_layout)
        sp2 = Qw.QSpacerItem(40, 20, Qw.QSizePolicy.Expanding,
                             Qw.QSizePolicy.Minimum)
        button_layout.addItem(sp2)
        self.bexec = Qw.QPushButton('run wget', self)
        self.bexec.setFocusPolicy(Qc.Qt.NoFocus)
        button_layout.addWidget(self.bexec)
        # Connections
        self.burl.clicked.connect(self.update_web)
        self.bpath.clicked.connect(self.update_path)
        self.bexec.clicked.connect(self.open_run_window)
        self.web.urlChanged.connect(self.update_url)
        Qw.QApplication.clipboard().dataChanged.connect(self.clip_changed)

    def clip_changed(self):
        text = Qw.QApplication.clipboard().text()
        self.url.setText(text)
        self.update_web()

    def update_path(self):
        old = self.save_path.text()
        opt = Qw.QFileDialog.DontResolveSymlinks | Qw.QFileDialog.ShowDirsOnly
        path = Qw.QFileDialog.getExistingDirectory(self, 'path', old, opt)
        if path:
            self.save_path.setText(path)
            self.settings.setValue("save_path", path)

    def open_run_window(self):
        if self.save_path.text():
            runwindow = RunWindow(self.wget_param(), self)
            runwindow.exec_()
        else:
            Qw.QMessageBox.critical(self, 'Critical', 'Empty save path')

    def wget_param(self):
        url = self.url.text()
        save_path = self.save_path.text()
        ext = self.extensions.text()
        os.chdir(save_path)
        return ['-A', ext, '-m', '-p', '-E', '-k', '-K', '-np', url]

    def update_web(self):
        text = self.url.text()
        if text.startswith('http://') or text.startswith('https://'):
            self.web.setUrl(Qc.QUrl(text))
            self.settings.setValue("save_url", text)
        else:
            self.url.setText(self.web.url())

    def update_url(self):
        self.url.setText(self.web.url().toString())


class RunWindow(Qw.QDialog):
    def __init__(self, wget_par, parent):
        super().__init__(parent)
        self.resize(600, 250)
        self.wget_params = wget_par
        self.files_down = 0
        layout = Qw.QVBoxLayout(self)
        self.out = Qw.QTextEdit()
        self.out.setLineWrapMode(0)  # No text wrap
        self.out.setReadOnly(True)
        layout.addWidget(self.out)
        self.progressBar = Qw.QProgressBar(self)
        self.progressBar.setRange(0, 1)
        layout.addWidget(self.progressBar)
        self.button = Qw.QPushButton('Return')
        self.button.setFocusPolicy(Qc.Qt.NoFocus)
        layout.addWidget(self.button)
        # pyQt process
        self.process = Qc.QProcess(self)
        self.process.setProcessChannelMode(Qc.QProcess.MergedChannels)
        # self.process.readyRead.connect(self.data_ready)
        self.process.readyReadStandardOutput.connect(self.data_ready)
        # connect
        self.button.clicked.connect(self.accept)
        self.process.started.connect(lambda: self.button.setEnabled(False))
        self.process.finished.connect(lambda: self.button.setEnabled(True))
        self.rex = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.*?saved")
        self.call_program()

    def call_program(self):
        txt = 'running wget %s\n\nresults:\n=======\n'
        self.out.append(txt % ' '.join(self.wget_params))
        self.progressBar.setRange(0, 0)
        self.process.start('wget', self.wget_params)

    @Qc.pyqtSlot()
    def data_ready(self):
        txt = self.process.readAllStandardOutput().data().decode('utf-8')
        foun = []
        foun = self.rex.findall(txt)
        if foun:
            if ".tmp.html’ saved" not in foun[0]:
                cursor = self.out.textCursor()
                cursor.movePosition(cursor.End)
                cursor.insertText(foun[0] + '\n')
                self.out.ensureCursorVisible()
                self.files_down += 1
        if 'FINISHED' in txt:
            self.out.append("Total downloaded files: %s" % self.files_down)
            self.progressBar.setRange(0, 1)


if __name__ == '__main__':
    app = Qw.QApplication(sys.argv)
    app.setWindowIcon(Qg.QIcon('qwget.png'))
    app.setOrganizationName("tedlaz")
    app.setOrganizationDomain("tedlaz")
    app.setApplicationName("qwget")
    ui = Fwget()
    ui.show()
    appex = app.exec_()
    sys.exit(appex)

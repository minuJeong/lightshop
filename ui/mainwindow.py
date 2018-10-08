# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwin\mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_window(object):
    def setupUi(self, window):
        window.setObjectName("window")
        window.resize(633, 479)
        self.centralWidget = QtWidgets.QWidget(window)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.le_psdpath = QtWidgets.QLineEdit(self.centralWidget)
        self.le_psdpath.setObjectName("le_psdpath")
        self.horizontalLayout_2.addWidget(self.le_psdpath)
        self.b_refresh = QtWidgets.QPushButton(self.centralWidget)
        self.b_refresh.setMinimumSize(QtCore.QSize(120, 0))
        self.b_refresh.setObjectName("b_refresh")
        self.horizontalLayout_2.addWidget(self.b_refresh)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.hl_canvasgroup = QtWidgets.QHBoxLayout()
        self.hl_canvasgroup.setContentsMargins(11, 11, 11, 11)
        self.hl_canvasgroup.setSpacing(6)
        self.hl_canvasgroup.setObjectName("hl_canvasgroup")
        self.verticalLayout_2.addLayout(self.hl_canvasgroup)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralWidget)
        self.pushButton_2.setMinimumSize(QtCore.QSize(120, 0))
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.pushButton_3 = QtWidgets.QPushButton(self.centralWidget)
        self.pushButton_3.setMinimumSize(QtCore.QSize(120, 0))
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout.addWidget(self.pushButton_3)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.b_exit = QtWidgets.QPushButton(self.centralWidget)
        self.b_exit.setMinimumSize(QtCore.QSize(120, 0))
        self.b_exit.setObjectName("b_exit")
        self.horizontalLayout.addWidget(self.b_exit)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        window.setCentralWidget(self.centralWidget)

        self.retranslateUi(window)
        QtCore.QMetaObject.connectSlotsByName(window)

    def retranslateUi(self, window):
        _translate = QtCore.QCoreApplication.translate
        window.setWindowTitle(_translate("window", "MainWindow"))
        self.b_refresh.setText(_translate("window", "Refresh"))
        self.pushButton_2.setText(_translate("window", "1"))
        self.pushButton_3.setText(_translate("window", "2"))
        self.b_exit.setText(_translate("window", "Exit"))


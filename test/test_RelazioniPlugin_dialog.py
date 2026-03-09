# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'gianoli.federico@gmail.com'
__date__ = '2024-10-03'
__copyright__ = 'Copyright 2024, Federico Gianoli'

import unittest

from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog

from RelazioniPlugin_dialog import RelazioniPluginDialog

# Qt6 scoped enum compatibility
try:
    _OK = QDialogButtonBox.StandardButton.Ok
    _CANCEL = QDialogButtonBox.StandardButton.Cancel
    _ACCEPTED = QDialog.DialogCode.Accepted
    _REJECTED = QDialog.DialogCode.Rejected
except AttributeError:
    _OK = QDialogButtonBox.Ok
    _CANCEL = QDialogButtonBox.Cancel
    _ACCEPTED = QDialog.Accepted
    _REJECTED = QDialog.Rejected

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()


class RelazioniPluginDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.dialog = RelazioniPluginDialog(None)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_ok(self):
        """Test we can click OK."""

        button = self.dialog.button_box.button(_OK)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, _ACCEPTED)

    def test_dialog_cancel(self):
        """Test we can click cancel."""
        button = self.dialog.button_box.button(_CANCEL)
        button.click()
        result = self.dialog.result()
        self.assertEqual(result, _REJECTED)

if __name__ == "__main__":
    suite = unittest.makeSuite(RelazioniPluginDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


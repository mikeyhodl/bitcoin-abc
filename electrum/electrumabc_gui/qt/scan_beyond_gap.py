# Electrum ABC - lightweight eCash client
# Copyright (C) 2020 The Electrum ABC developers
# Copyright (C) 2019 calin.culianu@gmail.com
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import threading

from qtpy import QtWidgets
from qtpy.QtCore import QTimer, Signal

from electrumabc.i18n import _
from electrumabc.printerror import PrintError
from electrumabc.util import ServerError

from .util import Buttons, WindowModalDialog


class ScanBeyondGap(WindowModalDialog, PrintError):
    progress_sig = Signal(int, int, int, int)
    done_sig = Signal(int, int)
    error_sig = Signal(Exception)

    def __init__(self, main_window):
        super().__init__(parent=main_window, title=_("Scan Beyond Gap"))
        self.resize(450, 400)
        self.main_window = main_window
        vbox = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(
            "<p><font size=+1><b><i>"
            + _("Scanning Beyond the Gap")
            + "</i></b></font></p><p>"
            + _(
                "Deterministic wallets can contain a nearly infinite number of"
                " addresses. However, usually only a relatively small block of"
                " addresses at the beginning are ever used."
            )
            + "</p><p>"
            + _(
                "Normally, when you (re)generate a wallet from its seed, addresses are"
                " derived and added to the wallet until a block of addresses is found"
                " without a history. This is referred to as the gap."
            )
            # + "</p><p>" + _("Addresses beyond this gap are not scanned for a balance (since they would normally not have one for most users).")
            + "</p><p>"
            + _(
                "If you think this wallet may have a transaction history for addresses"
                " beyond the gap, use this tool to search for them. If any history for"
                " an address is found, those addresses (plus all intervening"
                " addresses), will be added to your wallet."
            )
            + "</p>"
        )
        label.setWordWrap(True)
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        vbox.addWidget(label)

        vbox.addStretch(1)
        hbox = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(_("Number of addresses to scan:"))
        hbox.addWidget(label)
        self.num_sb = QtWidgets.QSpinBox()
        self.num_sb.setMinimum(1)
        self.num_sb.setMaximum(1000000)
        self.num_sb.setValue(100)
        hbox.addWidget(self.num_sb)
        self.which_cb = QtWidgets.QComboBox()
        self.which_cb.addItem(_("Both Receiving & Change (x2)"))
        self.which_cb.addItem(_("Receiving Addresses Only"))
        self.which_cb.addItem(_("Change Addresses Only"))
        self.which_cb.setCurrentIndex(0)
        hbox.addWidget(self.which_cb)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        self.always_add_addresses_cb = QtWidgets.QCheckBox(
            _("Always add scanned addresses to the wallet")
        )
        self.always_add_addresses_cb.setToolTip(
            _(
                "Add the scanned addresses even if no new history is found. Leave this "
                "unchecked if unsure, because subscribing to more addresses may "
                "needlessly slow down your wallet."
            )
        )
        vbox.addWidget(self.always_add_addresses_cb)

        self.prog = QtWidgets.QProgressBar()
        self.prog.setMinimum(0)
        self.prog.setMaximum(100)
        vbox.addWidget(self.prog)

        self.prog_label = QtWidgets.QLabel()
        vbox.addWidget(self.prog_label)

        self.found_label = QtWidgets.QLabel()
        vbox.addWidget(self.found_label)
        vbox.addStretch(1)

        self.cancel_but = QtWidgets.QPushButton(_("Cancel"))
        self.scan_but = QtWidgets.QPushButton(_("Start Scan"))
        vbox.addLayout(Buttons(self.cancel_but, self.scan_but))

        self.cancel_but.clicked.connect(self.cancel)
        self.scan_but.clicked.connect(self.scan)

        self.thread = threading.Thread(target=self.scan_thread, daemon=True)
        self._thread_args = (None,) * 3
        self.stop_flag = False
        self.canceling = False
        self.stage2 = False

        self.progress_sig.connect(self.progress_slot)
        self.done_sig.connect(self.done_slot)
        self.error_sig.connect(self.error_slot)

    def cancel(self):
        if self.canceling:
            return
        self.canceling = True  # reentrancy preventer
        self.scan_but.setDisabled(True)
        self.cancel_but.setDisabled(True)
        self.found_label.setText("")

        def reject():
            super(ScanBeyondGap, self).reject()

        if self.thread.is_alive():
            # We do the below so the user can get the "Canceling..." text
            # before we begin waiting for the worker thread and blocking the
            # UI thread.
            self.stop_flag = True

            def wait_for_thread():
                self.thread.join()
                self.prog_label.setText(_("Canceled"))
                QTimer.singleShot(100, reject)

            self.prog_label.setText(_("Canceling..."))
            QTimer.singleShot(10, wait_for_thread)
        else:
            reject()

    def reject(self):
        """overrides super and calls cancel for us"""
        self.cancel()

    def accept(self):
        self.cancel()

    def scan(self):
        self.scan_but.setDisabled(True)
        self.prog_label.setVisible(True)
        self.found_label.setVisible(False)
        self.which_cb.setDisabled(True)
        self.num_sb.setDisabled(True)
        self.found_label.setText("")
        self._thread_args = (
            self.num_sb.value(),
            self.which_cb.currentIndex(),
            self.always_add_addresses_cb.isChecked(),
        )
        self.thread.start()

    def progress_slot(self, pct, scanned, total, found):
        if self.canceling:
            return
        if not self.stage2:
            found_txt = ""
            if found:
                found_txt = _(" {} found").format(found)
            self.prog_label.setText(
                _("Scanning {} of {} addresses ...{}").format(scanned, total, found_txt)
            )
        else:
            self.prog_label.setText(
                _("Adding {} of {} new addresses to wallet...").format(scanned, total)
            )
        self.prog.setValue(pct)

    def done_slot(self, num_found, num_added):
        if self.canceling:
            return
        self.cancel_but.setText(_("Close"))
        if num_added:
            self.show_message(
                _(
                    "{} address(es) with a history and {} in-between address(es) were"
                    " added to your wallet."
                ).format(num_found, num_added)
            )
        else:
            self.show_message(
                _(
                    "No addresses with transaction histories were found in the"
                    " specified scan range."
                )
            )
        self.accept()

    def error_slot(self, exc: Exception):
        if self.canceling:
            return
        self.cancel_but.setText(_("Close"))
        self.prog_label.setText(
            "<font color=red><b>Error:</b></font> <i>{}</i>".format(repr(exc))
        )

    def _add_addresses(self, recv_end: int, change_end: int) -> int:
        self.stage2 = True
        wallet = self.main_window.wallet
        total, added = 0, 0
        if recv_end > -1:
            total += recv_end - len(wallet.get_receiving_addresses()) + 1
        if change_end > -1:
            total += change_end - len(wallet.get_change_addresses()) + 1
        self.progress_sig.emit(
            0, added, total, None
        )  # progress bar indicator reset to base for stage2
        while len(wallet.get_receiving_addresses()) < recv_end + 1:
            if self.stop_flag:
                return
            wallet.create_new_address(for_change=False)
            added += 1
            self.progress_sig.emit(added * 100 // total, added, total, None)
        while len(wallet.get_change_addresses()) < change_end + 1:
            if self.stop_flag:
                return
            wallet.create_new_address(for_change=True)
            added += 1
            self.progress_sig.emit(added * 100 // total, added, total, None)
        return added

    def _addr_has_history(self, address, network):
        return bool(
            network.synchronous_get(
                ("blockchain.scripthash.get_history", [address.to_scripthash_hex()]),
                timeout=5,
            )
        )

    def scan_thread(self):
        total, which, always_add = self._thread_args
        assert all(arg is not None for arg in self._thread_args)
        wallet = self.main_window.wallet
        network = wallet.network
        assert network
        num_found, recv_end, change_end = 0, 0, 0
        recv_begin = len(wallet.get_receiving_addresses())
        change_begin = len(wallet.get_change_addresses())
        paths = (False, recv_begin), (True, change_begin)

        if which == 1:
            paths = paths[:1]
        elif which == 2:
            paths = paths[1:]
        total *= len(paths)  # if change & addresses, will be * 2, otherwise * 1
        i, ct = 0, 0
        try:
            self.progress_sig.emit(
                0, 0, total, 0
            )  # initial clear of status text to indicate we began
            while not self.stop_flag and ct < total:
                for is_change, start in paths:
                    n = start + i
                    pks = wallet.derive_pubkeys(is_change, n)
                    addr = wallet.pubkeys_to_address(pks)
                    self.print_error(
                        "Scanning:", addr, "(Change)" if is_change else "(Receiving)", n
                    )
                    if self.stop_flag:
                        return
                    has_history = self._addr_has_history(addr, network)
                    if has_history:
                        self.print_error(
                            "FOUND:",
                            addr,
                            "(Change)" if is_change else "(Receiving)",
                            n,
                        )
                        num_found += 1
                    if has_history or always_add:
                        if is_change:
                            change_end = n
                        else:
                            recv_end = n
                    ct += 1
                    self.progress_sig.emit(ct * 100 // total, ct, total, num_found)
                i += 1
            num_added = 0
            if num_found or (always_add and (recv_end or change_end)):
                num_added = self._add_addresses(recv_end, change_end)
            self.done_sig.emit(num_found, num_added)
        except ServerError as e:
            # Suppress untrusted server string from appearing in the UI
            self.print_error("Server error:", repr(e))
            self.error_sig.emit(ServerError("The server replied with an error."))
        except Exception as e:
            self.error_sig.emit(e)

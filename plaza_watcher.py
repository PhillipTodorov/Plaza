import sys
import subprocess
import threading
from flask import Flask, request
from flask_cors import CORS
from flask_cors import CORS
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QPushButton
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont

flask_app = Flask(__name__)
CORS(flask_app)
CORS(flask_app)

class Bridge(QObject):
    message_received = pyqtSignal(str)

bridge = Bridge()

def run_command(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return str(e)

@flask_app.route('/message', methods=['POST'])
def receive():
    text = request.json.get('text', '')
    bridge.message_received.emit(text)
    return 'ok'

class BlockCard(QFrame):
    def __init__(self, code, parent=None):
        super().__init__(parent)
        self.code = code
        self.setStyleSheet("QFrame { border: 1px solid #444; border-radius: 6px; background: #1e1e1e; margin-bottom: 4px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        code_label = QLabel(code)
        code_label.setFont(QFont("monospace", 12))
        code_label.setStyleSheet("color: #e8e8e8; border: none; background: transparent;")
        code_label.setWordWrap(True)
        layout.addWidget(code_label)
        self.run_btn = QPushButton("Run")
        self.run_btn.setStyleSheet("QPushButton { background: #2a2a2a; border: 1px solid #4caf50; border-radius: 4px; color: #4caf50; font-size: 11px; padding: 4px; }")
        self.run_btn.clicked.connect(self.run_code)
        layout.addWidget(self.run_btn)
        self.out = QLabel("")
        self.out.setFont(QFont("monospace", 11))
        self.out.setStyleSheet("color: #aaa; border: none;")
        self.out.setWordWrap(True)
        self.out.hide()
        layout.addWidget(self.out)

    def run_code(self):
        self.run_btn.setEnabled(False)
        output = run_command(self.code)
        self.out.setText(output if output else "(no output)")
        self.out.show()
        self.run_btn.setEnabled(True)

class Plaza(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plaza")
        self.setMinimumWidth(500)
        self.setStyleSheet("QWidget { background: #141414; color: #e0e0e0; }")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)
        self.status = QLabel("Waiting for Claude...")
        self.status.setStyleSheet("color: #888; font-size: 12px;")
        root.addWidget(self.status)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; }")
        self.inner = QWidget()
        self.inner_layout = QVBoxLayout(self.inner)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(8)
        self.scroll.setWidget(self.inner)
        root.addWidget(self.scroll)
        bridge.message_received.connect(self.receive)

    def receive(self, text):
        for i in reversed(range(self.inner_layout.count())):
            w = self.inner_layout.itemAt(i).widget()
            if w: w.deleteLater()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        self.status.setText(f"{len(lines)} line{'s' if len(lines)>1 else ''} received.")
        for line in lines:
            self.inner_layout.addWidget(BlockCard(line))

if __name__ == "__main__":
    qapp = QApplication(sys.argv)
    w = Plaza()
    t = threading.Thread(target=lambda: flask_app.run(port=5000), daemon=True)
    t.start()
    w.show()
    sys.exit(qapp.exec())

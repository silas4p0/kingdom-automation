import math
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QTimer
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QLinearGradient, QRadialGradient,
    QFont, QMouseEvent, QPaintEvent,
)

WORKSPACES = [
    {"id": "audio", "label": "Audio", "lon": -60, "lat": 20},
    {"id": "video", "label": "Video", "lon": 60, "lat": 20},
    {"id": "editor", "label": "Editor", "lon": 0, "lat": -15},
    {"id": "assets", "label": "Assets", "lon": -120, "lat": -10},
    {"id": "master", "label": "Master", "lon": 150, "lat": 5},
]

WORKSPACE_BOOK_MAP: dict[str, int] = {
    "audio": 1,
    "video": 5,
    "editor": 0,
    "assets": 3,
    "master": 5,
}


class SphereWidget(QWidget):
    workspace_clicked = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        self._rotation_x: float = 0.0
        self._rotation_y: float = 0.0
        self._dragging: bool = False
        self._last_pos: QPointF = QPointF()
        self._hover_id: str = ""
        self.setMouseTracking(True)

    def _project(self, lon_deg: float, lat_deg: float) -> tuple[float, float, float]:
        lon = math.radians(lon_deg + self._rotation_y)
        lat = math.radians(lat_deg + self._rotation_x)
        x = math.cos(lat) * math.sin(lon)
        y = -math.sin(lat)
        z = math.cos(lat) * math.cos(lon)
        return x, y, z

    def _to_screen(self, x: float, y: float, cx: float, cy: float, r: float) -> QPointF:
        return QPointF(cx + x * r * 0.85, cy + y * r * 0.85)

    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 20

        grad = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 1.4)
        grad.setColorAt(0.0, QColor(60, 80, 120))
        grad.setColorAt(0.4, QColor(30, 45, 75))
        grad.setColorAt(1.0, QColor(15, 20, 40))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(80, 120, 180), 2))
        p.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        grid_pen = QPen(QColor(60, 90, 140, 80), 1)
        p.setPen(grid_pen)
        for lat_d in range(-60, 90, 30):
            pts = []
            for lon_d in range(0, 361, 10):
                x3, y3, z3 = self._project(float(lon_d), float(lat_d))
                if z3 > -0.1:
                    pts.append(self._to_screen(x3, y3, cx, cy, radius))
                else:
                    if len(pts) > 1:
                        for i in range(len(pts) - 1):
                            p.drawLine(pts[i], pts[i + 1])
                    pts = []
            if len(pts) > 1:
                for i in range(len(pts) - 1):
                    p.drawLine(pts[i], pts[i + 1])

        for lon_d in range(-180, 180, 30):
            pts = []
            for lat_d in range(-90, 91, 10):
                x3, y3, z3 = self._project(float(lon_d), float(lat_d))
                if z3 > -0.1:
                    pts.append(self._to_screen(x3, y3, cx, cy, radius))
                else:
                    if len(pts) > 1:
                        for i in range(len(pts) - 1):
                            p.drawLine(pts[i], pts[i + 1])
                    pts = []
            if len(pts) > 1:
                for i in range(len(pts) - 1):
                    p.drawLine(pts[i], pts[i + 1])

        font = QFont("Arial", 11, QFont.Weight.Bold)
        p.setFont(font)

        for ws in WORKSPACES:
            x3, y3, z3 = self._project(ws["lon"], ws["lat"])
            if z3 < -0.05:
                continue
            alpha = max(40, int(255 * (z3 + 0.1)))
            sp = self._to_screen(x3, y3, cx, cy, radius)

            is_hover = ws["id"] == self._hover_id
            dot_r = 14 if is_hover else 10
            col = QColor(0, 212, 255, alpha) if is_hover else QColor(0, 180, 220, alpha)
            p.setBrush(QBrush(col))
            p.setPen(QPen(QColor(255, 255, 255, alpha), 2 if is_hover else 1))
            p.drawEllipse(sp, dot_r, dot_r)

            p.setPen(QPen(QColor(255, 255, 255, alpha)))
            p.drawText(
                QRectF(sp.x() - 50, sp.y() + dot_r + 4, 100, 20),
                Qt.AlignmentFlag.AlignCenter,
                ws["label"],
            )

        p.end()

    def _hit_test(self, pos: QPointF) -> str:
        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 20

        for ws in WORKSPACES:
            x3, y3, z3 = self._project(ws["lon"], ws["lat"])
            if z3 < -0.05:
                continue
            sp = self._to_screen(x3, y3, cx, cy, radius)
            dx = pos.x() - sp.x()
            dy = pos.y() - sp.y()
            if dx * dx + dy * dy < 22 * 22:
                return ws["id"]
        return ""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            hit = self._hit_test(event.position())
            if hit:
                self.workspace_clicked.emit(hit)
                return
            self._dragging = True
            self._last_pos = event.position()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            dx = event.position().x() - self._last_pos.x()
            dy = event.position().y() - self._last_pos.y()
            self._rotation_y += dx * 0.5
            self._rotation_x += dy * 0.5
            self._rotation_x = max(-80, min(80, self._rotation_x))
            self._last_pos = event.position()
            self.update()
        else:
            old = self._hover_id
            self._hover_id = self._hit_test(event.position())
            if old != self._hover_id:
                self.setCursor(
                    Qt.CursorShape.PointingHandCursor if self._hover_id else Qt.CursorShape.OpenHandCursor
                )
                self.update()


class WorldNavigatorDialog(QDialog):
    workspace_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("World Navigator")
        self.setMinimumSize(480, 520)
        self.setStyleSheet(
            "QDialog { background: #0d1117; }"
            "QLabel { color: #c9d1d9; }"
            "QLineEdit { background: #161b22; border: 1px solid #30363d; color: #c9d1d9; padding: 6px; border-radius: 4px; }"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("World Navigator")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff; padding: 4px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self._search = QLineEdit()
        self._search.setToolTip("Filter workspaces by name")
        self._search.setPlaceholderText("Search workspace (e.g. audio, editor, master)...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._sphere = SphereWidget()
        self._sphere.setToolTip("Drag to rotate the globe; click a workspace dot to switch")
        self._sphere.workspace_clicked.connect(self._on_workspace_clicked)
        layout.addWidget(self._sphere)

        self._result_row = QHBoxLayout()
        self._result_buttons: list[QPushButton] = []
        for ws in WORKSPACES:
            btn = QPushButton(ws["label"])
            btn.setStyleSheet(
                "QPushButton { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 6px 14px; border-radius: 4px; }"
                "QPushButton:hover { background: #30363d; color: #58a6ff; }"
            )
            btn.setProperty("ws_id", ws["id"])
            btn.clicked.connect(lambda checked=False, wid=ws["id"]: self._on_workspace_clicked(wid))
            self._result_row.addWidget(btn)
            self._result_buttons.append(btn)
        layout.addLayout(self._result_row)

        hint = QLabel("Drag to rotate | Click a region to switch workspace")
        hint.setStyleSheet("color: #484f58; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

    def _on_search(self, text: str) -> None:
        query = text.lower().strip()
        for btn in self._result_buttons:
            if not query:
                btn.setVisible(True)
            else:
                label = btn.text().lower()
                btn.setVisible(query in label)

    def _on_workspace_clicked(self, workspace_id: str) -> None:
        self.workspace_selected.emit(workspace_id)
        self.accept()

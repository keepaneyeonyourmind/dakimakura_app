# =========================================================
# PRODUCT CARD — карточка товара в каталоге
# =========================================================

import os

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QRectF


# =========================================================
# СКРУГЛЕНИЕ И МАСШТАБИРОВАНИЕ ФОТО
# =========================================================

def rounded_image(path: str, width: int, height: int, radius: int = 20) -> QPixmap:
    """
    Загружает изображение по пути, масштабирует его с сохранением пропорций
    (KeepAspectRatioByExpanding — заполняет всю область без полей),
    обрезает до нужного размера и применяет скругление углов.
    Возвращает пустой QPixmap, если файл не найден или повреждён.
    """
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return QPixmap()

    # Масштабируем так, чтобы изображение полностью покрывало область
    scaled = pixmap.scaled(
        width,
        height,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )

    # Создаём целевой пиксмап и отрисовываем с маской
    result = QPixmap(width, height)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, width, height), radius, radius)
    painter.setClipPath(clip)

    # Центрируем обрезку
    x = (scaled.width()  - width)  // 2
    y = (scaled.height() - height) // 2
    painter.drawPixmap(0, 0, scaled, x, y, width, height)
    painter.end()

    return result


# =========================================================
# КАРТОЧКА ТОВАРА
# =========================================================

class ProductCard(QFrame):

    IMG_W, IMG_H, IMG_R = 260, 220, 20   # размеры и радиус картинки

    def __init__(
        self,
        image_path: str,
        name: str,
        size: str,
        material: str,
        fill: str,
        visual: str,
        features: str,
        quantity,
        price,
        index: int,
        on_edit,
        on_delete,
    ):
        super().__init__()
        self.setObjectName("productCard")
        self.setFixedSize(290, 500)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # ── Картинка ──────────────────────────────────────
        img_label = QLabel()
        img_label.setFixedSize(self.IMG_W, self.IMG_H)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet("background: transparent;")

        img_path = str(image_path) if image_path else ""
        if img_path and img_path != "nan" and os.path.exists(img_path):
            pix = rounded_image(img_path, self.IMG_W, self.IMG_H, self.IMG_R)
            if not pix.isNull():
                img_label.setPixmap(pix)
            else:
                self._set_no_photo(img_label)
        else:
            self._set_no_photo(img_label)

        # ── Название ──────────────────────────────────────
        name_label = QLabel(str(name))
        name_label.setObjectName("cardTitle")
        name_label.setWordWrap(True)

        # ── Параметры ─────────────────────────────────────
        def param(key: str, val) -> QLabel:
            lbl = QLabel(
                f'<span style="color:#818cf8;font-weight:600">{key}:</span> {val}'
            )
            lbl.setWordWrap(True)
            lbl.setStyleSheet("background: transparent;")
            return lbl

        # ── Цена + кнопки ─────────────────────────────────
        price_label = QLabel(f"{price} ₽")
        price_label.setObjectName("priceLabel")

        btn_edit = QPushButton("✏️")
        btn_edit.setObjectName("btnIcon")
        btn_edit.setFixedSize(36, 36)
        btn_edit.setToolTip("Редактировать")
        btn_edit.clicked.connect(lambda: on_edit(index))

        btn_del = QPushButton("🗑️")
        btn_del.setObjectName("btnIconDanger")
        btn_del.setFixedSize(36, 36)
        btn_del.setToolTip("Удалить")
        btn_del.clicked.connect(lambda: on_delete(index))

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(price_label)
        bottom_row.addStretch()
        bottom_row.addWidget(btn_edit)
        bottom_row.addWidget(btn_del)

        # ── Сборка ────────────────────────────────────────
        layout.addWidget(img_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        layout.addWidget(param("Размер",      size))
        layout.addWidget(param("Материал",    material))
        layout.addWidget(param("Наполнитель", fill))
        layout.addWidget(param("Печать",      visual))
        layout.addWidget(param("Особенности", features))
        layout.addWidget(param("В наличии",   f"{quantity} шт."))
        layout.addStretch()
        layout.addLayout(bottom_row)

        self.setLayout(layout)

    # ── заглушка «нет фото» ───────────────────────────────
    @staticmethod
    def _set_no_photo(label: QLabel) -> None:
        label.setText("🛏️")
        label.setStyleSheet("""
            background-color: #1e293b;
            border-radius: 20px;
            color: #818cf8;
            font-size: 60px;
        """)
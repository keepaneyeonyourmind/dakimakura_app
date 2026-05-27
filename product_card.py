# =========================================================
# PRODUCT CARD — карточка товара в каталоге
# =========================================================

import os

from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton
)

from PyQt6.QtGui import (
    QPixmap,
    QPainter,
    QPainterPath
)

from PyQt6.QtCore import Qt, QRectF


# =========================================================
# СКРУГЛЕНИЕ ФОТО
# =========================================================

def rounded_image(path, width, height, radius=20):

    pixmap = QPixmap(path)

    if pixmap.isNull():
        return QPixmap()

    pixmap = pixmap.scaled(
        width,
        height,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )

    rounded = QPixmap(width, height)
    rounded.fill(Qt.GlobalColor.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    path_round = QPainterPath()
    path_round.addRoundedRect(
        QRectF(0, 0, width, height),
        radius,
        radius
    )

    painter.setClipPath(path_round)

    x = (pixmap.width() - width) // 2
    y = (pixmap.height() - height) // 2

    painter.drawPixmap(0, 0, pixmap, x, y, width, height)
    painter.end()

    return rounded


# =========================================================
# КАРТОЧКА ТОВАРА
# =========================================================

class ProductCard(QFrame):

    def __init__(
        self,
        image_path,
        name,
        size,
        material,
        fill,
        visual,
        features,
        quantity,
        price,
        index,
        on_edit,
        on_delete,
        dark_mode
    ):

        super().__init__()

        self.setObjectName("productCard")
        self.setFixedSize(290, 500)

        self.dark_mode = dark_mode

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # =================================================
        # IMAGE
        # =================================================

        self.image_label = QLabel()
        self.image_label.setFixedSize(260, 220)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")

        # =================================================
        # PHOTO
        # =================================================

        if (
            image_path
            and str(image_path) != "nan"
            and os.path.exists(str(image_path))
        ):

            rounded = rounded_image(str(image_path), 260, 220, 20)
            self.image_label.setPixmap(rounded)

        # =================================================
        # NO PHOTO
        # =================================================

        else:

            self.image_label.setText("🛏️")

            no_photo_bg = "#dbe4ff" if not dark_mode else "#1e293b"
            no_photo_color = "#6d28d9" if not dark_mode else "#818cf8"

            self.image_label.setStyleSheet(f"""
                background-color: {no_photo_bg};
                border-radius: 20px;
                color: {no_photo_color};
                font-size: 60px;
            """)

        # =================================================
        # НАЗВАНИЕ
        # =================================================

        name_label = QLabel(str(name))
        name_label.setObjectName("cardTitle")
        name_label.setWordWrap(True)

        # =================================================
        # ПАРАМЕТРЫ
        # =================================================

        accent = "#818cf8" if dark_mode else "#7c3aed"

        def param_label(key, val):
            lbl = QLabel(
                f'<span style="color:{accent};font-weight:600">'
                f'{key}:</span> {val}'
            )
            lbl.setWordWrap(True)
            lbl.setStyleSheet("background: transparent;")
            return lbl

        size_label    = param_label("Размер", size)
        mat_label     = param_label("Материал", material)
        fill_label    = param_label("Наполнитель", fill)
        visual_label  = param_label("Печать", visual)
        feat_label    = param_label("Особенности", features)
        qty_label     = param_label("В наличии", f"{quantity} шт.")

        # =================================================
        # ЦЕНА + КНОПКИ
        # =================================================

        price_label = QLabel(f"{price} ₽")
        price_label.setObjectName("priceLabel")

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(price_label)
        bottom_row.addStretch()

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

        bottom_row.addWidget(btn_edit)
        bottom_row.addWidget(btn_del)

        # =================================================
        # ADD
        # =================================================

        layout.addWidget(
            self.image_label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(name_label)
        layout.addWidget(size_label)
        layout.addWidget(mat_label)
        layout.addWidget(fill_label)
        layout.addWidget(visual_label)
        layout.addWidget(feat_label)
        layout.addWidget(qty_label)
        layout.addStretch()
        layout.addLayout(bottom_row)

        self.setLayout(layout)
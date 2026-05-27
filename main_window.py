# =========================================================
# MAIN WINDOW — главное окно приложения
# =========================================================

import os
import shutil
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QMessageBox,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QFrame,
    QFileDialog,
    QScrollArea,
    QGridLayout,
    QSizePolicy,
    QSplitter,
    QCheckBox,
    QButtonGroup,
    QScrollBar,
)

from PyQt6.QtGui import (
    QFont,
    QPixmap,
    QPainter,
    QPainterPath,
    QIcon,
)

from PyQt6.QtCore import Qt, QRectF, QSize, QPropertyAnimation, QEasingCurve

import data_manager
from product_card import ProductCard, rounded_image


# =========================================================
# ПАНЕЛЬ ФИЛЬТРОВ (выдвигающаяся)
# =========================================================

class FilterPanel(QFrame):

    def __init__(self, on_filter_changed, dark_mode):
        super().__init__()
        self.on_filter_changed = on_filter_changed
        self.dark_mode = dark_mode
        self.setObjectName("filterPanel")
        self.setFixedWidth(0)   # начинаем скрытой
        self._visible = False
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Фильтры")
        title.setObjectName("filterTitle")
        layout.addWidget(title)

        # ----- Размер -----
        size_lbl = QLabel("Размер")
        size_lbl.setObjectName("filterGroupLabel")
        layout.addWidget(size_lbl)

        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "Все", "100x35 см", "150x50 см",
            "160x50 см", "170x50 см", "160x60 см"
        ])
        self.size_combo.currentIndexChanged.connect(self._changed)
        layout.addWidget(self.size_combo)

        # ----- Материал -----
        mat_lbl = QLabel("Материал наволочки")
        mat_lbl.setObjectName("filterGroupLabel")
        layout.addWidget(mat_lbl)

        self.mat_combo = QComboBox()
        self.mat_combo.addItems([
            "Все", "Полиэстер", "Сатин", "Хлопок", "Велюр", "Шёлк"
        ])
        self.mat_combo.currentIndexChanged.connect(self._changed)
        layout.addWidget(self.mat_combo)

        # ----- Наполнитель -----
        fill_lbl = QLabel("Наполнитель")
        fill_lbl.setObjectName("filterGroupLabel")
        layout.addWidget(fill_lbl)

        self.fill_combo = QComboBox()
        self.fill_combo.addItems([
            "Все", "Холлофайбер", "Пух", "Синтепон", "Меморифоам"
        ])
        self.fill_combo.currentIndexChanged.connect(self._changed)
        layout.addWidget(self.fill_combo)

        # ----- Цена -----
        price_lbl = QLabel("Цена (до ₽)")
        price_lbl.setObjectName("filterGroupLabel")
        layout.addWidget(price_lbl)

        self.price_spin = QSpinBox()
        self.price_spin.setRange(0, 99999)
        self.price_spin.setValue(99999)
        self.price_spin.setSuffix(" ₽")
        self.price_spin.setSingleStep(500)
        self.price_spin.valueChanged.connect(self._changed)
        layout.addWidget(self.price_spin)

        # ----- Наличие -----
        stock_lbl = QLabel("Наличие")
        stock_lbl.setObjectName("filterGroupLabel")
        layout.addWidget(stock_lbl)

        self.stock_check = QCheckBox("Только в наличии")
        self.stock_check.stateChanged.connect(self._changed)
        layout.addWidget(self.stock_check)

        layout.addStretch()

        # ----- Сброс -----
        btn_reset = QPushButton("↺  Сбросить фильтры")
        btn_reset.setObjectName("btnReset")
        btn_reset.clicked.connect(self.reset)
        layout.addWidget(btn_reset)

    def _changed(self):
        self.on_filter_changed(self.get_filters())

    def get_filters(self) -> dict:
        return {
            "size":     self.size_combo.currentText(),
            "material": self.mat_combo.currentText(),
            "fill":     self.fill_combo.currentText(),
            "price":    self.price_spin.value(),
            "in_stock": self.stock_check.isChecked(),
        }

    def reset(self):
        self.size_combo.setCurrentIndex(0)
        self.mat_combo.setCurrentIndex(0)
        self.fill_combo.setCurrentIndex(0)
        self.price_spin.setValue(99999)
        self.stock_check.setChecked(False)

    def toggle(self):
        if self._visible:
            self._visible = False
            self.setFixedWidth(0)
        else:
            self._visible = True
            self.setFixedWidth(240)

    def apply_theme(self, dark_mode):
        self.dark_mode = dark_mode


# =========================================================
# ГЛАВНОЕ ОКНО
# =========================================================

class DakimakuraApp(QWidget):

    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.image_path = ""
        self.edit_index = -1
        self.setWindowTitle("Дакимакуры")
        self.setGeometry(100, 30, 1400, 900)
        self.init_ui()
        self.set_dark_theme()
        self.load_data()

    # =====================================================
    # UI
    # =====================================================

    def init_ui(self):

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # =================================================
        # БОКОВАЯ ПАНЕЛЬ
        # =================================================

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(18, 28, 18, 22)
        sidebar_layout.setSpacing(6)

        logo = QLabel("Дакимакуры")
        logo.setObjectName("sidebarLogo")
        logo.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        sidebar_layout.addWidget(logo)

        sidebar_layout.addSpacing(20)

        nav_label = QLabel("НАВИГАЦИЯ")
        nav_label.setObjectName("navSectionLabel")
        sidebar_layout.addWidget(nav_label)
        sidebar_layout.addSpacing(4)

        self.btn_catalog = QPushButton()
        self.btn_catalog.setIcon(QIcon("icons/catalog.png"))
        self.btn_catalog.setIconSize(QSize(24, 24))
        self.btn_catalog.setToolTip("Каталог")

        self.btn_catalog.setObjectName("navBtn")
        self.btn_catalog.setCheckable(True)
        self.btn_catalog.setChecked(True)
        self.btn_catalog.clicked.connect(lambda: self.switch_tab("catalog"))

        self.btn_add_tab = QPushButton("➕  Добавить товар")
        self.btn_add_tab.setObjectName("navBtn")
        self.btn_add_tab.setCheckable(True)
        self.btn_add_tab.clicked.connect(lambda: self.switch_tab("add"))

        self.btn_search_tab = QPushButton()
        self.btn_search_tab.setIcon(QIcon("icons/search.png"))
        self.btn_search_tab.setIconSize(QSize(24, 24))
        self.btn_search_tab.setToolTip("Поиск")

        self.btn_search_tab.setObjectName("navBtn")
        self.btn_search_tab.setCheckable(True)
        self.btn_search_tab.clicked.connect(lambda: self.switch_tab("search"))

        self.nav_buttons = [
            self.btn_catalog,
            self.btn_add_tab,
            self.btn_search_tab,
        ]

        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sidebarSep")
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(8)

        self.btn_excel = QPushButton("📗  Открыть Excel")
        self.btn_excel.setObjectName("navBtn")
        self.btn_excel.clicked.connect(data_manager.open_excel)
        sidebar_layout.addWidget(self.btn_excel)

        sidebar_layout.addSpacing(8)

        self.theme_btn = QPushButton()
        self.theme_btn.setIcon(QIcon("icons/theme_change.png"))
        self.theme_btn.setIconSize(QSize(24, 24))
        self.theme_btn.setToolTip("Смена темы")
        self.theme_btn.setObjectName("btnTheme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        sidebar_layout.addWidget(self.theme_btn)

        sidebar.setLayout(sidebar_layout)

        # =================================================
        # КОНТЕНТ
        # =================================================

        content_wrapper = QVBoxLayout()
        content_wrapper.setSpacing(0)
        content_wrapper.setContentsMargins(0, 0, 0, 0)

        # --- Топ-бар ---
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(64)

        topbar_layout = QHBoxLayout()
        topbar_layout.setContentsMargins(24, 0, 24, 0)

        self.page_title = QLabel("Каталог")
        self.page_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.page_title.setObjectName("pageTitle")

        topbar_layout.addWidget(self.page_title)
        topbar_layout.addStretch()
        topbar.setLayout(topbar_layout)

        content_wrapper.addWidget(topbar)

        # =================================================
        # ВКЛАДКА КАТАЛОГ
        # =================================================

        self.catalog_widget = QWidget()
        self.catalog_widget.setObjectName("contentArea")

        catalog_layout = QVBoxLayout()
        catalog_layout.setContentsMargins(24, 16, 24, 24)
        catalog_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("mainScroll")

        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")

        self.products_layout = QGridLayout()
        self.products_layout.setSpacing(20)
        self.products_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_content.setLayout(self.products_layout)
        self.scroll.setWidget(scroll_content)

        catalog_layout.addWidget(self.scroll)
        self.catalog_widget.setLayout(catalog_layout)

        # =================================================
        # ВКЛАДКА ДОБАВИТЬ
        # =================================================

        self.add_widget = QWidget()
        self.add_widget.setObjectName("contentArea")

        add_outer = QVBoxLayout()
        add_outer.setContentsMargins(24, 16, 24, 24)

        add_frame = QFrame()
        add_frame.setObjectName("formCard")

        add_layout = QVBoxLayout()
        add_layout.setContentsMargins(28, 24, 28, 24)
        add_layout.setSpacing(14)

        self.preview_label = QLabel("🛏️")
        self.preview_label.setFixedSize(260, 220)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setObjectName("previewImage")

        self.load_image_btn = QPushButton("🖼  Загрузить фото")
        self.load_image_btn.setObjectName("btnSecondary")
        self.load_image_btn.clicked.connect(self.load_image)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Сакура в цвету")

        self.size_input = QComboBox()
        self.size_input.addItems([
            "100x35 см", "150x50 см", "160x50 см",
            "170x50 см", "160x60 см"
        ])
        self.size_input.setEditable(True)

        self.material_input = QComboBox()
        self.material_input.addItems([
            "Полиэстер", "Сатин", "Хлопок", "Велюр", "Шёлк"
        ])
        self.material_input.setEditable(True)

        self.fill_input = QComboBox()
        self.fill_input.addItems([
            "Холлофайбер", "Пух", "Синтепон", "Меморифоам"
        ])
        self.fill_input.setEditable(True)

        self.visual_input = QLineEdit()
        self.visual_input.setPlaceholderText("Двусторонняя печать, HD...")

        self.features_input = QLineEdit()
        self.features_input.setPlaceholderText("Съёмный чехол, гипоаллергенная...")

        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setSuffix(" шт.")

        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(99999999)
        self.price_input.setDecimals(0)
        self.price_input.setSuffix(" ₽")

        form_layout.addRow("Название:", self.name_input)
        form_layout.addRow("Размер:", self.size_input)
        form_layout.addRow("Материал наволочки:", self.material_input)
        form_layout.addRow("Наполнитель:", self.fill_input)
        form_layout.addRow("Визуальные параметры:", self.visual_input)
        form_layout.addRow("Особенности:", self.features_input)
        form_layout.addRow("Количество:", self.quantity_input)
        form_layout.addRow("Цена:", self.price_input)

        self.save_btn = QPushButton("💾  Сохранить товар")
        self.save_btn.setObjectName("btnSave")
        self.save_btn.setMinimumHeight(52)
        self.save_btn.clicked.connect(self.save_data)

        self.cancel_edit_btn = QPushButton("✕  Отменить редактирование")
        self.cancel_edit_btn.setObjectName("btnSecondary")
        self.cancel_edit_btn.setMinimumHeight(44)
        self.cancel_edit_btn.clicked.connect(self.cancel_edit)
        self.cancel_edit_btn.hide()

        add_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        add_layout.addWidget(self.load_image_btn)
        add_layout.addSpacing(4)
        add_layout.addLayout(form_layout)
        add_layout.addStretch()
        add_layout.addWidget(self.cancel_edit_btn)
        add_layout.addWidget(self.save_btn)

        add_frame.setLayout(add_layout)
        add_outer.addWidget(add_frame)
        self.add_widget.setLayout(add_outer)

        # =================================================
        # ВКЛАДКА ПОИСК
        # =================================================

        self.search_widget = QWidget()
        self.search_widget.setObjectName("contentArea")

        search_outer = QVBoxLayout()
        search_outer.setContentsMargins(24, 16, 24, 24)
        search_outer.setSpacing(12)

        # --- Строка: поисковая строка + кнопка фильтров ---
        search_top_row = QHBoxLayout()
        search_top_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию, материалу, особенностям...")
        self.search_input.setObjectName("searchBar")
        self.search_input.setMinimumHeight(44)
        self.search_input.textChanged.connect(self.do_search)

        self.btn_filter_toggle = QPushButton("⚙  Фильтры")
        self.btn_filter_toggle.setObjectName("btnFilter")
        self.btn_filter_toggle.setMinimumHeight(44)
        self.btn_filter_toggle.setCheckable(True)
        self.btn_filter_toggle.clicked.connect(self._toggle_filter_panel)

        search_top_row.addWidget(self.search_input)
        search_top_row.addWidget(self.btn_filter_toggle)

        search_outer.addLayout(search_top_row)

        # --- Тело: результаты + выдвигающаяся панель ---
        search_body = QHBoxLayout()
        search_body.setSpacing(0)

        # Панель результатов
        results_area = QWidget()
        results_area.setObjectName("contentArea")
        results_v = QVBoxLayout(results_area)
        results_v.setContentsMargins(0, 0, 0, 0)

        search_scroll = QScrollArea()
        search_scroll.setWidgetResizable(True)
        search_scroll.setObjectName("mainScroll")

        search_scroll_content = QWidget()
        search_scroll_content.setObjectName("scrollContent")

        self.search_results_layout = QGridLayout()
        self.search_results_layout.setSpacing(20)
        self.search_results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        search_scroll_content.setLayout(self.search_results_layout)
        search_scroll.setWidget(search_scroll_content)

        results_v.addWidget(search_scroll)

        # Фильтр-панель (выдвигающаяся)
        self.filter_panel = FilterPanel(
            on_filter_changed=self._on_filter_changed,
            dark_mode=self.dark_mode
        )
        self.filter_panel.setObjectName("filterPanel")

        search_body.addWidget(results_area)
        search_body.addWidget(self.filter_panel)

        search_outer.addLayout(search_body)
        self.search_widget.setLayout(search_outer)

        # =================================================
        # СТЕК ВКЛАДОК
        # =================================================

        self.catalog_widget.show()
        self.add_widget.hide()
        self.search_widget.hide()

        content_wrapper.addWidget(self.catalog_widget)
        content_wrapper.addWidget(self.add_widget)
        content_wrapper.addWidget(self.search_widget)

        # =================================================
        # СБОРКА
        # =================================================

        main_layout.addWidget(sidebar)

        content_frame = QWidget()
        content_frame.setObjectName("contentFrame")
        content_frame.setLayout(content_wrapper)

        main_layout.addWidget(content_frame)
        self.setLayout(main_layout)

    # =====================================================
    # ФИЛЬТРЫ
    # =====================================================

    def _toggle_filter_panel(self):
        self.filter_panel.toggle()

    def _on_filter_changed(self, filters: dict):
        self.do_search(self.search_input.text(), filters=filters)

    # =====================================================
    # ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК
    # =====================================================

    def switch_tab(self, tab: str):

        tabs = {
            "catalog": (self.catalog_widget, self.btn_catalog,   "Каталог"),
            "add":     (self.add_widget,     self.btn_add_tab,   "Добавить товар"),
            "search":  (self.search_widget,  self.btn_search_tab,"Поиск"),
        }

        for key, (widget, btn, _) in tabs.items():
            widget.setVisible(key == tab)
            btn.setChecked(key == tab)

        self.page_title.setText(tabs[tab][2])

        if tab == "search":
            self.search_input.setFocus()

    # =====================================================
    # ЗАГРУЗКА ФОТО
    # =====================================================

    def load_image(self):

        file_name, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "",
            "Изображения (*.png *.jpg *.jpeg *.webp)"
        )

        if file_name:
            os.makedirs("images", exist_ok=True)
            dest = os.path.join("images", os.path.basename(file_name))
            if file_name != dest:
                shutil.copy2(file_name, dest)

            self.image_path = dest
            rounded = rounded_image(dest, 260, 220, 20)
            self.preview_label.setPixmap(rounded)
            self.preview_label.setText("")

    # =====================================================
    # СОХРАНЕНИЕ ДАННЫХ
    # =====================================================

    def save_data(self):

        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название товара!")
            return

        record = {
            "Название":             name,
            "Размер":               self.size_input.currentText(),
            "Материал наволочки":   self.material_input.currentText(),
            "Наполнитель":          self.fill_input.currentText(),
            "Визуальные параметры": self.visual_input.text(),
            "Особенности":          self.features_input.text(),
            "Количество":           self.quantity_input.value(),
            "Цена":                 int(self.price_input.value()),
            "Фото":                 self.image_path,
        }

        if self.edit_index >= 0:
            data_manager.update_record(self.edit_index, record)
            QMessageBox.information(self, "Успех", "Товар обновлён!")
            self.cancel_edit()
        else:
            data_manager.add_record(record)
            QMessageBox.information(self, "Успех", "Товар сохранён!")
            self.clear_form()

        self.load_data()
        self.switch_tab("catalog")

    # =====================================================
    # ЗАГРУЗКА КАТАЛОГА
    # =====================================================

    def load_data(self):

        self._clear_grid(self.products_layout)
        records = data_manager.load_data()

        if not records:
            empty = QLabel("Товаров пока нет.\nНажмите «➕ Добавить товар»")
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.products_layout.addWidget(empty, 0, 0)
            return

        cols = 4
        for i, rec in enumerate(records):
            card = ProductCard(
                image_path=rec.get("Фото", ""),
                name=rec.get("Название", ""),
                size=rec.get("Размер", ""),
                material=rec.get("Материал наволочки", ""),
                fill=rec.get("Наполнитель", ""),
                visual=rec.get("Визуальные параметры", ""),
                features=rec.get("Особенности", ""),
                quantity=rec.get("Количество", "0"),
                price=rec.get("Цена", "0"),
                index=i,
                on_edit=self.edit_item,
                on_delete=self.delete_item,
                dark_mode=self.dark_mode
            )
            self.products_layout.addWidget(card, i // cols, i % cols)

    # =====================================================
    # ПОИСК + ФИЛЬТРЫ
    # =====================================================

    def do_search(self, query: str = "", filters: dict = None):

        self._clear_grid(self.search_results_layout)
        records = data_manager.load_data()

        # текстовый поиск
        q = query.lower().strip()
        if q:
            records = [r for r in records if q in str(r).lower()]

        # фильтры
        if filters is None:
            filters = self.filter_panel.get_filters()

        if filters["size"] != "Все":
            records = [r for r in records
                       if str(r.get("Размер", "")) == filters["size"]]

        if filters["material"] != "Все":
            records = [r for r in records
                       if str(r.get("Материал наволочки", "")) == filters["material"]]

        if filters["fill"] != "Все":
            records = [r for r in records
                       if str(r.get("Наполнитель", "")) == filters["fill"]]

        max_price = filters["price"]
        def safe_price(r):
            try:
                return float(r.get("Цена", 0))
            except (ValueError, TypeError):
                return 0.0

        records = [r for r in records if safe_price(r) <= max_price]

        if filters["in_stock"]:
            def safe_qty(r):
                try:
                    return int(r.get("Количество", 0))
                except (ValueError, TypeError):
                    return 0
            records = [r for r in records if safe_qty(r) > 0]

        if not records:
            lbl = QLabel("Ничего не найдено")
            lbl.setObjectName("emptyLabel")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.search_results_layout.addWidget(lbl, 0, 0)
            return

        cols = 3
        for i, rec in enumerate(records):
            card = ProductCard(
                image_path=rec.get("Фото", ""),
                name=rec.get("Название", ""),
                size=rec.get("Размер", ""),
                material=rec.get("Материал наволочки", ""),
                fill=rec.get("Наполнитель", ""),
                visual=rec.get("Визуальные параметры", ""),
                features=rec.get("Особенности", ""),
                quantity=rec.get("Количество", "0"),
                price=rec.get("Цена", "0"),
                index=i,
                on_edit=self.edit_item,
                on_delete=self.delete_item,
                dark_mode=self.dark_mode
            )
            self.search_results_layout.addWidget(card, i // cols, i % cols)

    # =====================================================
    # РЕДАКТИРОВАНИЕ
    # =====================================================

    def edit_item(self, index: int):

        records = data_manager.load_data()
        if not (0 <= index < len(records)):
            return

        rec = records[index]
        self.edit_index = index

        self.name_input.setText(rec.get("Название", ""))

        size_idx = self.size_input.findText(rec.get("Размер", ""))
        self.size_input.setCurrentIndex(max(size_idx, 0))

        mat_idx = self.material_input.findText(rec.get("Материал наволочки", ""))
        self.material_input.setCurrentIndex(max(mat_idx, 0))

        fill_idx = self.fill_input.findText(rec.get("Наполнитель", ""))
        self.fill_input.setCurrentIndex(max(fill_idx, 0))

        self.visual_input.setText(rec.get("Визуальные параметры", ""))
        self.features_input.setText(rec.get("Особенности", ""))

        try:
            self.quantity_input.setValue(int(rec.get("Количество", 0)))
        except (ValueError, TypeError):
            self.quantity_input.setValue(0)

        try:
            self.price_input.setValue(float(rec.get("Цена", 0)))
        except (ValueError, TypeError):
            self.price_input.setValue(0)

        img = rec.get("Фото", "")
        self.image_path = img

        if img and os.path.exists(img):
            rounded = rounded_image(img, 260, 220, 20)
            self.preview_label.setPixmap(rounded)
            self.preview_label.setText("")
        else:
            self.preview_label.clear()
            self.preview_label.setText("🛏️")

        self.cancel_edit_btn.show()
        self.save_btn.setText("💾  Сохранить изменения")
        self.switch_tab("add")
        self.page_title.setText("Редактировать товар")

    def cancel_edit(self):
        self.edit_index = -1
        self.cancel_edit_btn.hide()
        self.save_btn.setText("💾  Сохранить товар")
        self.clear_form()
        self.switch_tab("catalog")

    def clear_form(self):
        self.name_input.clear()
        self.size_input.setCurrentIndex(0)
        self.material_input.setCurrentIndex(0)
        self.fill_input.setCurrentIndex(0)
        self.visual_input.clear()
        self.features_input.clear()
        self.quantity_input.setValue(0)
        self.price_input.setValue(0)
        self.image_path = ""
        self.preview_label.clear()
        self.preview_label.setText("🛏️")

    # =====================================================
    # УДАЛЕНИЕ
    # =====================================================

    def delete_item(self, index: int):

        msg = QMessageBox(self)
        msg.setWindowTitle("Удалить товар?")
        msg.setText("Вы уверены? Это действие нельзя отменить.")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        msg.button(QMessageBox.StandardButton.Yes).setText("Удалить")
        msg.button(QMessageBox.StandardButton.Cancel).setText("Отмена")

        if msg.exec() == QMessageBox.StandardButton.Yes:
            data_manager.delete_record(index)
            self.load_data()

    # =====================================================
    # ВСПОМОГАТЕЛЬНОЕ
    # =====================================================

    def _clear_grid(self, grid_layout):
        for i in reversed(range(grid_layout.count())):
            widget = grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    # =====================================================
    # ТЕМЫ
    # =====================================================

    def toggle_theme(self):
        if self.dark_mode:
            self.set_light_theme()
        else:
            self.set_dark_theme()
        self.load_data()

    # ─────────────────────────────────────────────────────
    # ТЁМНАЯ ТЕМА
    # ─────────────────────────────────────────────────────

    def set_dark_theme(self):

        self.dark_mode = True
        self.theme_btn.setText("☀️  Светлая тема")

        self.setStyleSheet("""

            QWidget {
                background-color: #0f172a;
                color: #cbd5e1;
                font-size: 14px;
                font-family: Arial;
            }

            QLabel {
                background: transparent;
                color: #cbd5e1;
            }

            QWidget#contentArea,
            QWidget#contentFrame,
            QWidget#scrollContent {
                background-color: #0f172a;
            }

            /* ── Боковая панель ── */
            QFrame#sidebar {
                background-color: #1e293b;
                border-right: 1px solid #334155;
            }

            QLabel#sidebarLogo {
                color: #a78bfa;
                font-size: 16px;
                font-weight: bold;
            }

            QLabel#navSectionLabel {
                color: #64748b;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            QPushButton#navBtn {
                background: transparent;
                border: none;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 14px;
                text-align: left;
                padding: 10px 12px;
            }

            QPushButton#navBtn:hover {
                background: #334155;
                color: #e2e8f0;
            }

            QPushButton#navBtn:checked {
                background: #6d28d9;
                color: #ffffff;
                font-weight: bold;
            }

            QFrame#sidebarSep { color: #334155; }

            QPushButton#btnTheme {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 13px;
                padding: 9px 12px;
                text-align: left;
            }

            QPushButton#btnTheme:hover {
                background: #334155;
                color: #e2e8f0;
            }

            /* ── Топ-бар ── */
            QFrame#topbar {
                background-color: #0f172a;
                border-bottom: 1px solid #1e293b;
            }

            QLabel#pageTitle {
                color: #f1f5f9;
                font-size: 18px;
                font-weight: bold;
            }

            /* ── Форма ── */
            QFrame#formCard {
                background-color: #1e293b;
                border-radius: 20px;
                border: 1px solid #334155;
            }

            QLabel {
                color: #cbd5e1;
                font-size: 14px;
            }

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                min-height: 24px;
                color: #e2e8f0;
                font-size: 14px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #7c3aed;
            }

            QComboBox::drop-down { border: none; }

            QComboBox QAbstractItemView {
                background: #1e293b;
                color: #e2e8f0;
                selection-background-color: #6d28d9;
                font-size: 14px;
            }

            QLineEdit#searchBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 22px;
                padding: 8px 20px;
                color: #e2e8f0;
                font-size: 14px;
            }

            QPushButton#btnFilter {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 22px;
                color: #94a3b8;
                font-size: 14px;
                padding: 8px 18px;
                min-width: 110px;
            }

            QPushButton#btnFilter:hover {
                background: #334155;
                color: #e2e8f0;
            }

            QPushButton#btnFilter:checked {
                background: #6d28d9;
                color: #ffffff;
                border: 1px solid #7c3aed;
            }

            /* ── Панель фильтров ── */
            QFrame#filterPanel {
                background-color: #1e293b;
                border-left: 1px solid #334155;
                border-radius: 0;
            }

            QLabel#filterTitle {
                color: #a78bfa;
                font-size: 15px;
                font-weight: bold;
            }

            QLabel#filterGroupLabel {
                color: #64748b;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            QCheckBox {
                color: #94a3b8;
                font-size: 13px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #475569;
                border-radius: 4px;
                background: #0f172a;
            }

            QCheckBox::indicator:checked {
                background: #7c3aed;
                border: 1px solid #7c3aed;
            }

            QPushButton#btnReset {
                background: transparent;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 13px;
                padding: 8px;
            }

            QPushButton#btnReset:hover {
                background: #334155;
                color: #e2e8f0;
            }

            /* ── Кнопки ── */
            QPushButton#btnSave {
                background-color: #7c3aed;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
            }

            QPushButton#btnSave:hover { background-color: #6d28d9; }

            QPushButton#btnSecondary {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 10px;
                font-size: 13px;
                padding: 8px;
            }

            QPushButton#btnSecondary:hover {
                background-color: #334155;
                color: #e2e8f0;
            }

            /* ── Превью ── */
            QLabel#previewImage {
                background-color: #1e293b;
                border-radius: 20px;
                color: #818cf8;
                font-size: 60px;
                border: 2px dashed #334155;
            }

            /* ── Карточки ── */
            QFrame#productCard {
                background-color: #1e293b;
                border-radius: 20px;
                border: 1px solid #334155;
            }

            QLabel#cardTitle {
                font-size: 15px;
                font-weight: bold;
                color: #f1f5f9;
                background: transparent;
            }

            QLabel#priceLabel {
                font-size: 20px;
                font-weight: bold;
                color: #a78bfa;
                background: transparent;
            }

            QPushButton#btnIcon {
                background: #334155;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }

            QPushButton#btnIcon:hover { background: #475569; }

            QPushButton#btnIconDanger {
                background: transparent;
                border: 1px solid #7f1d1d;
                border-radius: 8px;
                font-size: 14px;
            }

            QPushButton#btnIconDanger:hover { background: #7f1d1d; }

            /* ── Скролл ── */
            QScrollArea#mainScroll {
                background: #0f172a;
                border: none;
            }

            QScrollBar:vertical {
                background: #1e293b;
                width: 6px;
                border-radius: 3px;
            }

            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 3px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }

            QLabel#emptyLabel {
                color: #475569;
                font-size: 16px;
            }

        """)

    # ─────────────────────────────────────────────────────
    # СВЕТЛАЯ ТЕМА
    # ─────────────────────────────────────────────────────

    def set_light_theme(self):

        self.dark_mode = False
        self.theme_btn.setText("🌙  Тёмная тема")

        self.setStyleSheet("""

            QWidget {
                background-color: #f1f5f9;
                color: #1e293b;
                font-size: 14px;
                font-family: Arial;
            }

            QLabel {
                background: transparent;
                color: #1e293b;
            }

            QWidget#contentArea,
            QWidget#contentFrame,
            QWidget#scrollContent {
                background-color: #f1f5f9;
            }

            /* ── Боковая панель ── */
            QFrame#sidebar {
                background-color: #ffffff;
                border-right: 1px solid #e2e8f0;
            }

            QLabel#sidebarLogo {
                color: #7c3aed;
                font-size: 16px;
                font-weight: bold;
            }

            QLabel#navSectionLabel {
                color: #94a3b8;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            QPushButton#navBtn {
                background: transparent;
                border: none;
                border-radius: 8px;
                color: #64748b;
                font-size: 14px;
                text-align: left;
                padding: 10px 12px;
            }

            QPushButton#navBtn:hover {
                background: #f1f5f9;
                color: #1e293b;
            }

            QPushButton#navBtn:checked {
                background: #ede9fe;
                color: #7c3aed;
                font-weight: bold;
            }

            QFrame#sidebarSep { color: #e2e8f0; }

            QPushButton#btnTheme {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                color: #64748b;
                font-size: 13px;
                padding: 9px 12px;
                text-align: left;
            }

            QPushButton#btnTheme:hover {
                background: #f1f5f9;
                color: #1e293b;
            }

            /* ── Топ-бар ── */
            QFrame#topbar {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }

            QLabel#pageTitle {
                color: #1e293b;
                font-size: 18px;
                font-weight: bold;
            }

            /* ── Форма ── */
            QFrame#formCard {
                background-color: #ffffff;
                border-radius: 20px;
                border: 1px solid #e2e8f0;
            }

            QLabel {
                color: #1e293b;
                font-size: 14px;
            }

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                min-height: 24px;
                color: #1e293b;
                font-size: 14px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #7c3aed;
            }

            QComboBox::drop-down { border: none; }

            QComboBox QAbstractItemView {
                background: #ffffff;
                color: #1e293b;
                selection-background-color: #ede9fe;
                font-size: 14px;
            }

            QLineEdit#searchBar {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 22px;
                padding: 8px 20px;
                color: #1e293b;
                font-size: 14px;
            }

            QPushButton#btnFilter {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 22px;
                color: #64748b;
                font-size: 14px;
                padding: 8px 18px;
                min-width: 110px;
            }

            QPushButton#btnFilter:hover {
                background: #f1f5f9;
                color: #1e293b;
            }

            QPushButton#btnFilter:checked {
                background: #7c3aed;
                color: #ffffff;
                border: 1px solid #6d28d9;
            }

            /* ── Панель фильтров ── */
            QFrame#filterPanel {
                background-color: #ffffff;
                border-left: 1px solid #e2e8f0;
            }

            QLabel#filterTitle {
                color: #7c3aed;
                font-size: 15px;
                font-weight: bold;
            }

            QLabel#filterGroupLabel {
                color: #94a3b8;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            QCheckBox {
                color: #64748b;
                font-size: 13px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background: #ffffff;
            }

            QCheckBox::indicator:checked {
                background: #7c3aed;
                border: 1px solid #7c3aed;
            }

            QPushButton#btnReset {
                background: transparent;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                color: #64748b;
                font-size: 13px;
                padding: 8px;
            }

            QPushButton#btnReset:hover {
                background: #f1f5f9;
                color: #1e293b;
            }

            /* ── Кнопки ── */
            QPushButton#btnSave {
                background-color: #7c3aed;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
            }

            QPushButton#btnSave:hover { background-color: #6d28d9; }

            QPushButton#btnSecondary {
                background-color: #f1f5f9;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                font-size: 13px;
                padding: 8px;
            }

            QPushButton#btnSecondary:hover {
                background-color: #e2e8f0;
                color: #1e293b;
            }

            /* ── Превью ── */
            QLabel#previewImage {
                background-color: #ede9fe;
                border-radius: 20px;
                color: #7c3aed;
                font-size: 60px;
                border: 2px dashed #c4b5fd;
            }

            /* ── Карточки ── */
            QFrame#productCard {
                background-color: #ffffff;
                border-radius: 20px;
                border: 1px solid #e2e8f0;
            }

            QLabel#cardTitle {
                font-size: 15px;
                font-weight: bold;
                color: #1e293b;
                background: transparent;
            }

            QLabel#priceLabel {
                font-size: 20px;
                font-weight: bold;
                color: #7c3aed;
                background: transparent;
            }

            QPushButton#btnIcon {
                background: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
            }

            QPushButton#btnIcon:hover { background: #e2e8f0; }

            QPushButton#btnIconDanger {
                background: #ffffff;
                border: 1px solid #fecaca;
                border-radius: 8px;
                font-size: 14px;
            }

            QPushButton#btnIconDanger:hover { background: #fee2e2; }

            /* ── Скролл ── */
            QScrollArea#mainScroll {
                background: #f1f5f9;
                border: none;
            }

            QScrollBar:vertical {
                background: #e2e8f0;
                width: 6px;
                border-radius: 3px;
            }

            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 3px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }

            QLabel#emptyLabel {
                color: #94a3b8;
                font-size: 16px;
            }

        """)
# =========================================================
# MAIN WINDOW — главное окно приложения
# =========================================================

import os
import shutil

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox,
    QFrame, QFileDialog, QScrollArea, QGridLayout,
    QCheckBox,
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize

import data_manager
from product_card import ProductCard, rounded_image
from resource_path import resource_path, writable_path


# =========================================================
# ПАНЕЛЬ ФИЛЬТРОВ (выдвигающаяся)
# =========================================================

class FilterPanel(QFrame):

    def __init__(self, on_filter_changed):
        super().__init__()
        self.on_filter_changed = on_filter_changed
        self.setObjectName("filterPanel")
        self.setFixedWidth(0)
        self._visible = False
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Фильтры")
        title.setObjectName("filterTitle")
        layout.addWidget(title)

        def group(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName("filterGroupLabel")
            return lbl

        # Размер
        layout.addWidget(group("Размер"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Все", "150x50 см", "160x60 см", "170x50 см"])
        self.size_combo.currentIndexChanged.connect(self._changed)
        layout.addWidget(self.size_combo)

        # Материал
        layout.addWidget(group("Материал наволочки"))
        self.mat_combo = QComboBox()
        self.mat_combo.addItems([
            "Все", "Велюр", "Шёлк", "Микрофибра",
            "Персиковая кожа", "Бамбуковое волокно"
        ])
        self.mat_combo.currentIndexChanged.connect(self._changed)
        layout.addWidget(self.mat_combo)

        # Наполнитель
        layout.addWidget(group("Наполнитель"))
        self.fill_combo = QComboBox()
        self.fill_combo.addItems([
            "Все", "Холлофайбер", "Пена с памятью",
            "Синтепон", "Пух", "Меморифоам"
        ])
        self.fill_combo.currentIndexChanged.connect(self._changed)
        layout.addWidget(self.fill_combo)

        # Цена
        layout.addWidget(group("Цена (до ₽)"))
        self.price_spin = QSpinBox()
        self.price_spin.setRange(0, 99_999)
        self.price_spin.setValue(99_999)
        self.price_spin.setSuffix(" ₽")
        self.price_spin.setSingleStep(500)
        self.price_spin.valueChanged.connect(self._changed)
        layout.addWidget(self.price_spin)

        # Наличие
        layout.addWidget(group("Наличие"))
        self.stock_check = QCheckBox("Только в наличии")
        self.stock_check.stateChanged.connect(self._changed)
        layout.addWidget(self.stock_check)

        layout.addStretch()

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
        self.price_spin.setValue(99_999)
        self.stock_check.setChecked(False)

    def toggle(self):
        self._visible = not self._visible
        self.setFixedWidth(240 if self._visible else 0)


# =========================================================
# ГЛАВНОЕ ОКНО
# =========================================================

class DakimakuraApp(QWidget):

    CATALOG_COLS = 4
    SEARCH_COLS  = 3

    def __init__(self):
        super().__init__()
        self.image_path = ""
        self.edit_index = -1
        self.setWindowTitle("Дакимакуры")
        self.setGeometry(100, 30, 1400, 900)
        self._init_ui()
        self._apply_theme()
        self.load_data()

    # =====================================================
    # UI
    # =====================================================

    def _init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self._build_sidebar())

        content_frame = QWidget()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self._build_topbar())
        content_layout.addWidget(self._build_catalog_tab())
        content_layout.addWidget(self._build_add_tab())
        content_layout.addWidget(self._build_search_tab())
        content_frame.setLayout(content_layout)

        self.catalog_widget.show()
        self.add_widget.hide()
        self.search_widget.hide()

        main_layout.addWidget(content_frame)
        self.setLayout(main_layout)

    # ── Боковая панель ───────────────────────────────────

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 28, 18, 22)
        layout.setSpacing(6)

        logo = QLabel("Дакимакуры")
        logo.setObjectName("sidebarLogo")
        logo.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        layout.addWidget(logo)
        layout.addSpacing(20)

        nav_lbl = QLabel("НАВИГАЦИЯ")
        nav_lbl.setObjectName("navSectionLabel")
        layout.addWidget(nav_lbl)
        layout.addSpacing(4)

        def nav_btn(text: str, icon: str, tooltip: str) -> QPushButton:
            btn = QPushButton(f"    {text}")
            btn.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            btn.setIcon(QIcon(resource_path(f"icons/{icon}.png")))
            btn.setIconSize(QSize(24, 24))
            btn.setToolTip(tooltip)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            return btn

        self.btn_catalog    = nav_btn("Каталог",        "catalog",     "Каталог")
        self.btn_add_tab    = nav_btn("Добавить товар", "add_product", "Добавить товар")
        self.btn_search_tab = nav_btn("Поиск",          "search",      "Поиск")

        self.btn_catalog.setChecked(True)
        self.btn_catalog.clicked.connect(lambda: self.switch_tab("catalog"))
        self.btn_add_tab.clicked.connect(lambda: self.switch_tab("add"))
        self.btn_search_tab.clicked.connect(lambda: self.switch_tab("search"))

        self.nav_buttons = [self.btn_catalog, self.btn_add_tab, self.btn_search_tab]
        for btn in self.nav_buttons:
            layout.addWidget(btn)

        layout.addStretch()

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sidebarSep")
        layout.addWidget(sep)
        layout.addSpacing(8)

        btn_excel = QPushButton("     Открыть Excel")
        btn_excel.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        btn_excel.setIcon(QIcon(resource_path("icons/excel_btn.png")))
        btn_excel.setIconSize(QSize(24, 24))
        btn_excel.setToolTip("Открыть Excel")
        btn_excel.setObjectName("navBtn")
        btn_excel.clicked.connect(data_manager.open_excel)
        layout.addWidget(btn_excel)

        sidebar.setLayout(layout)
        return sidebar

    # ── Топ-бар ──────────────────────────────────────────

    def _build_topbar(self) -> QFrame:
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
        return topbar

    # ── Вкладка «Каталог» ────────────────────────────────

    def _build_catalog_tab(self) -> QWidget:
        self.catalog_widget = QWidget()
        self.catalog_widget.setObjectName("contentArea")

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(0)

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
        layout.addWidget(self.scroll)
        self.catalog_widget.setLayout(layout)
        return self.catalog_widget

    # ── Вкладка «Добавить» ───────────────────────────────

    def _build_add_tab(self) -> QWidget:
        self.add_widget = QWidget()
        self.add_widget.setObjectName("contentArea")

        outer = QVBoxLayout()
        outer.setContentsMargins(24, 16, 24, 24)

        card = QFrame()
        card.setObjectName("formCard")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(14)

        # Превью
        self.preview_label = QLabel("🛏️")
        self.preview_label.setFixedSize(260, 220)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setObjectName("previewImage")

        btn_load = QPushButton("🖼  Загрузить фото")
        btn_load.setObjectName("btnSecondary")
        btn_load.clicked.connect(self.load_image)

        # Форма
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Сакура в цвету")

        self.size_input = QComboBox()
        self.size_input.addItems(["150x50 см", "160x60 см", "170x50 см"])
        self.size_input.setEditable(True)

        self.material_input = QComboBox()
        self.material_input.addItems([
            "Велюр", "Шёлк", "Микрофибра",
            "Персиковая кожа", "Бамбуковое волокно"
        ])
        self.material_input.setEditable(True)

        self.fill_input = QComboBox()
        self.fill_input.addItems([
            "Холлофайбер", "Пена с памятью",
            "Синтепон", "Пух", "Меморифоам"
        ])
        self.fill_input.setEditable(True)

        self.visual_input = QLineEdit()
        self.visual_input.setPlaceholderText("Двусторонняя печать, HD...")

        self.features_input = QLineEdit()
        self.features_input.setPlaceholderText("Съёмный чехол, гипоаллергенная...")

        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(999_999)
        self.quantity_input.setSuffix(" шт.")

        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(99_999_999)
        self.price_input.setDecimals(0)
        self.price_input.setSuffix(" ₽")

        form.addRow("Название:",             self.name_input)
        form.addRow("Размер:",               self.size_input)
        form.addRow("Материал наволочки:",   self.material_input)
        form.addRow("Наполнитель:",          self.fill_input)
        form.addRow("Визуальные параметры:", self.visual_input)
        form.addRow("Особенности:",          self.features_input)
        form.addRow("Количество:",           self.quantity_input)
        form.addRow("Цена:",                 self.price_input)

        self.save_btn = QPushButton("💾  Сохранить товар")
        self.save_btn.setObjectName("btnSave")
        self.save_btn.setMinimumHeight(52)
        self.save_btn.clicked.connect(self.save_data)

        self.cancel_edit_btn = QPushButton("✕  Отменить редактирование")
        self.cancel_edit_btn.setObjectName("btnSecondary")
        self.cancel_edit_btn.setMinimumHeight(44)
        self.cancel_edit_btn.clicked.connect(self.cancel_edit)
        self.cancel_edit_btn.hide()

        card_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(btn_load)
        card_layout.addSpacing(4)
        card_layout.addLayout(form)
        card_layout.addStretch()
        card_layout.addWidget(self.cancel_edit_btn)
        card_layout.addWidget(self.save_btn)

        card.setLayout(card_layout)
        outer.addWidget(card)
        self.add_widget.setLayout(outer)
        return self.add_widget

    # ── Вкладка «Поиск» ──────────────────────────────────

    def _build_search_tab(self) -> QWidget:
        self.search_widget = QWidget()
        self.search_widget.setObjectName("contentArea")

        outer = QVBoxLayout()
        outer.setContentsMargins(24, 16, 24, 24)
        outer.setSpacing(12)

        # Строка поиска + кнопка фильтров
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Поиск по названию, материалу, особенностям..."
        )
        self.search_input.setObjectName("searchBar")
        self.search_input.setMinimumHeight(44)
        self.search_input.textChanged.connect(self.do_search)

        self.btn_filter_toggle = QPushButton("⚙  Фильтры")
        self.btn_filter_toggle.setObjectName("btnFilter")
        self.btn_filter_toggle.setMinimumHeight(44)
        self.btn_filter_toggle.setCheckable(True)
        self.btn_filter_toggle.clicked.connect(self._toggle_filter_panel)

        top_row.addWidget(self.search_input)
        top_row.addWidget(self.btn_filter_toggle)
        outer.addLayout(top_row)

        # Область результатов
        body = QHBoxLayout()
        body.setSpacing(0)

        results_area = QWidget()
        results_area.setObjectName("contentArea")
        results_v = QVBoxLayout(results_area)
        results_v.setContentsMargins(0, 0, 0, 0)

        search_scroll = QScrollArea()
        search_scroll.setWidgetResizable(True)
        search_scroll.setObjectName("mainScroll")

        search_content = QWidget()
        search_content.setObjectName("scrollContent")

        self.search_results_layout = QGridLayout()
        self.search_results_layout.setSpacing(20)
        self.search_results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        search_content.setLayout(self.search_results_layout)

        search_scroll.setWidget(search_content)
        results_v.addWidget(search_scroll)

        # Фильтр-панель
        self.filter_panel = FilterPanel(on_filter_changed=self._on_filter_changed)
        self.filter_panel.setObjectName("filterPanel")

        body.addWidget(results_area)
        body.addWidget(self.filter_panel)
        outer.addLayout(body)

        self.search_widget.setLayout(outer)
        return self.search_widget

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
            "catalog": (self.catalog_widget, self.btn_catalog,    "Каталог"),
            "add":     (self.add_widget,     self.btn_add_tab,    "Добавить товар"),
            "search":  (self.search_widget,  self.btn_search_tab, "Поиск"),
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
        if not file_name:
            return

        images_dir = writable_path("images")
        os.makedirs(images_dir, exist_ok=True)
        dest = os.path.join(images_dir, os.path.basename(file_name))
        if file_name != dest:
            shutil.copy2(file_name, dest)

        self.image_path = dest
        pix = rounded_image(dest, 260, 220, 20)
        if not pix.isNull():
            self.preview_label.setPixmap(pix)
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
            empty = QLabel("Товаров пока нет.\nНажмите «Добавить товар»")
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.products_layout.addWidget(empty, 0, 0)
            return

        for i, rec in enumerate(records):
            card = self._make_card(rec, i)
            self.products_layout.addWidget(card, i // self.CATALOG_COLS, i % self.CATALOG_COLS)

    # =====================================================
    # ПОИСК + ФИЛЬТРЫ
    # =====================================================

    def do_search(self, query: str = "", filters: dict = None):
        self._clear_grid(self.search_results_layout)
        records = data_manager.load_data()

        q = query.lower().strip()
        if q:
            records = [r for r in records if q in str(r).lower()]

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

        def safe_float(r, key: str, default: float = 0.0) -> float:
            try:
                return float(r.get(key, default))
            except (ValueError, TypeError):
                return default

        records = [r for r in records if safe_float(r, "Цена") <= filters["price"]]

        if filters["in_stock"]:
            records = [r for r in records if int(safe_float(r, "Количество")) > 0]

        if not records:
            lbl = QLabel("Ничего не найдено")
            lbl.setObjectName("emptyLabel")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.search_results_layout.addWidget(lbl, 0, 0)
            return

        for i, rec in enumerate(records):
            card = self._make_card(rec, i)
            self.search_results_layout.addWidget(
                card, i // self.SEARCH_COLS, i % self.SEARCH_COLS
            )

    # =====================================================
    # ФАБРИКА КАРТОЧЕК
    # =====================================================

    def _make_card(self, rec: dict, index: int) -> ProductCard:
        return ProductCard(
            image_path=rec.get("Фото", ""),
            name=rec.get("Название", ""),
            size=rec.get("Размер", ""),
            material=rec.get("Материал наволочки", ""),
            fill=rec.get("Наполнитель", ""),
            visual=rec.get("Визуальные параметры", ""),
            features=rec.get("Особенности", ""),
            quantity=rec.get("Количество", "0"),
            price=rec.get("Цена", "0"),
            index=index,
            on_edit=self.edit_item,
            on_delete=self.delete_item,
        )

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

        for combo, key in (
            (self.size_input,     "Размер"),
            (self.material_input, "Материал наволочки"),
            (self.fill_input,     "Наполнитель"),
        ):
            idx = combo.findText(rec.get(key, ""))
            combo.setCurrentIndex(max(idx, 0))

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
            pix = rounded_image(img, 260, 220, 20)
            if not pix.isNull():
                self.preview_label.setPixmap(pix)
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
    # ТЁМНАЯ ТЕМА (единственная)
    # =====================================================

    def _apply_theme(self):
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
                border: 2px dashed #4c1d95;
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
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 14px;
            }

            QPushButton#btnIcon:hover { background: #334155; }

            QPushButton#btnIconDanger {
                background: #0f172a;
                border: 1px solid #7f1d1d;
                border-radius: 8px;
                font-size: 14px;
            }

            QPushButton#btnIconDanger:hover { background: #450a0a; }

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
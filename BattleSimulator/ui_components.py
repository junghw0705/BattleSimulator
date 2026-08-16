from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QFrame, QPushButton, QComboBox, QSpinBox, QSplitter, QTextEdit,
    QGroupBox, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0b0f19;
    color: #f1f5f9;
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 6px 14px;
    margin-right: 3px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    font-weight: bold;
    font-size: 11px;
}

QTabBar::tab:selected {
    background: #6366f1;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background: #334155;
    color: #cbd5e1;
}

QGroupBox {
    border: 1px solid #1e293b;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 10px;
    font-weight: bold;
    font-size: 11px;
    color: #818cf8;
    background-color: #0f172a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    background-color: #1e293b;
    border-radius: 3px;
}

QComboBox, QSpinBox, QLineEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 3px 8px;
    color: #f8fafc;
    min-height: 20px;
    font-size: 11px;
}

QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
    border: 1px solid #818cf8;
}

QComboBox::drop-down {
    border: none;
    width: 16px;
}

QPushButton {
    background-color: #4f46e5;
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    min-height: 20px;
    font-size: 11px;
}

QPushButton:hover {
    background-color: #6366f1;
}

QPushButton:pressed {
    background-color: #3730a3;
}

QPushButton#btn-danger {
    background-color: #dc2626;
}

QPushButton#btn-danger:hover {
    background-color: #ef4444;
}

QPushButton#btn-success {
    background-color: #059669;
}

QPushButton#btn-success:hover {
    background-color: #10b981;
}

QPushButton#btn-accent {
    background-color: #8b5cf6;
}

QPushButton#btn-accent:hover {
    background-color: #a855f7;
}

QTableWidget {
    background-color: #0f172a;
    gridline-color: #1e293b;
    border: 1px solid #1e293b;
    border-radius: 4px;
    color: #f1f5f9;
    font-size: 11px;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #3730a3;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 5px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #334155;
    font-size: 11px;
}

QScrollBar:vertical {
    border: none;
    background: #0b0f19;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 16px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar:horizontal {
    border: none;
    background: #0b0f19;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #475569;
    min-width: 30px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background: #6366f1;
}
"""

class StatCard(QFrame):
    def __init__(self, title, value_str="0", color="#4f46e5", max_val=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            StatCard {{
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(1)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(self.lbl_title)

        self.lbl_value = QLabel(value_str)
        self.lbl_value.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(self.lbl_value)

        self.max_val = max_val
        self.pbar = None
        if max_val is not None:
            self.pbar = QProgressBar()
            self.pbar.setMaximum(max_val)
            self.pbar.setTextVisible(False)
            self.pbar.setFixedHeight(4)
            self.pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #0b0f19;
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 2px;
                }}
            """)
            layout.addWidget(self.pbar)

    def set_title(self, title):
        self.lbl_title.setText(title)

    def set_value(self, val, val_str=None, max_val=None):
        if val_str is None:
            val_str = str(val)
        self.lbl_value.setText(val_str)
        if self.pbar and max_val is not None:
            self.pbar.setMaximum(int(max_val))
            self.pbar.setValue(int(min(val, max_val)))
        elif self.pbar:
            self.pbar.setValue(int(val))

class VisualTrainBlueprintHeader(QFrame):
    """Expanded Blueprint UI occupying ~1/3 of screen height with spacious unclipped car cards and horizontal slide scroll"""
class ClickableBlueprintCard(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

class VisualTrainBlueprintHeader(QGroupBox):
    coachSelected = pyqtSignal(int)

    def __init__(self, title="🚂 열차 구성 블루프린트 조감도 (Visual Blueprint & Shields)"):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #818cf8;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 12px;
                background-color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        header_bar = QHBoxLayout()
        header_bar.addWidget(QLabel("🔍 열차 칸 카드를 클릭하여 2번 탭 상세 스탯으로 즉시 이동합니다."))
        header_bar.addStretch()

        self.lbl_blueprint_summary = QLabel("보호막: 0 | 포탑: 0개")
        self.lbl_blueprint_summary.setStyleSheet("font-weight: bold; color: #38bdf8;")
        header_bar.addWidget(self.lbl_blueprint_summary)

        main_layout.addLayout(header_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumHeight(190)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #1e293b;
                border-radius: 6px;
                background-color: #0b0f19;
            }
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(12, 10, 12, 10)
        self.container_layout.setSpacing(14)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll, stretch=1)

    def update_blueprint(self, train_config, selected_index=0):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. Locomotive Card
        loco_card = ClickableBlueprintCard()
        loco_card.setObjectName("LocoCard")
        loco_card.setMinimumSize(240, 180)
        loco_card.setMaximumWidth(250)
        
        is_loco_sel = (selected_index == 0)
        b_color_l = "#10b981" if is_loco_sel else "#6366f1"
        bg_color_l = "#064e3b" if is_loco_sel else "#1e1b4b"

        loco_card.setStyleSheet(f"""
            QFrame#LocoCard {{
                background-color: {bg_color_l};
                border: 2px solid {b_color_l};
                border-radius: 8px;
            }}
            QFrame#LocoCard:hover {{
                border: 2px solid #10b981;
            }}
        """)
        loco_card.setCursor(Qt.CursorShape.PointingHandCursor)
        loco_card.clicked.connect(lambda: self.coachSelected.emit(0))

        l_layout = QVBoxLayout(loco_card)
        l_layout.setContentsMargins(10, 8, 10, 8)
        l_layout.setSpacing(3)

        loco_name = train_config.locomotive.get("locomotiveName") if train_config.locomotive else "기관차 미선택"
        loco_hp = train_config.locomotive.get("locomotiveHp", 1000) if train_config.locomotive else 1000
        loco_def = train_config.locomotive.get("locomotiveDef", 10) if train_config.locomotive else 10
        loco_shield = train_config.get_locomotive_shield()

        lbl_l_tag = QLabel("🚂 [기관차 (LOCOMOTIVE)]")
        lbl_l_tag.setStyleSheet("font-weight: bold; color: #a5b4fc; font-size: 11px; border: none; background: transparent;")
        
        lbl_l_name = QLabel(loco_name)
        lbl_l_name.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13.5px; border: none; background: transparent;")

        lbl_l_stats = QLabel(f"• Def: {loco_def:.0f} | 🛡️보호막: {loco_shield:.0f} | HP: {loco_hp}")
        lbl_l_stats.setStyleSheet("color: #38bdf8; font-size: 10.5px; font-weight: bold; border: none; background: transparent;")

        # 2 Turret Slots on Locomotive (T1, T2)
        lt_box = QHBoxLayout()
        lt_box.setSpacing(4)
        for t_i in range(2):
            if t_i < len(train_config.locomotive_turrets):
                w = train_config.locomotive_turrets[t_i]
                wname = (w.get("weaponName") or w.get("weaponId"))[:3]
                ltype = str(w.get("weaponLandType") or "L").strip().upper()
                t_color = "#f59e0b" if ltype == "L" else "#06b6d4"
                t_chip = QLabel(f"T{t_i+1}:{wname}")
                t_chip.setStyleSheet(f"background-color: {t_color}; color: #000000; font-size: 9.5px; font-weight: bold; border-radius: 3px; padding: 2px 4px;")
            else:
                t_chip = QLabel(f"T{t_i+1}:-")
                t_chip.setStyleSheet("background-color: #0f172a; color: #64748b; font-size: 9.5px; border-radius: 3px; padding: 2px 4px;")
            lt_box.addWidget(t_chip)

        pbar_shield_l = QProgressBar()
        pbar_shield_l.setValue(100)
        pbar_shield_l.setFixedHeight(4)
        pbar_shield_l.setTextVisible(False)
        pbar_shield_l.setStyleSheet("QProgressBar { background: #0f172a; border: none; border-radius: 2px; } QProgressBar::chunk { background: #06b6d4; border-radius: 2px; }")

        pbar_l = QProgressBar()
        pbar_l.setValue(100)
        pbar_l.setFixedHeight(4)
        pbar_l.setTextVisible(False)
        pbar_l.setStyleSheet("QProgressBar { background: #0f172a; border: none; border-radius: 2px; } QProgressBar::chunk { background: #6366f1; border-radius: 2px; }")

        l_layout.addWidget(lbl_l_tag)
        l_layout.addWidget(lbl_l_name)
        l_layout.addWidget(lbl_l_stats)
        l_layout.addLayout(lt_box)
        l_layout.addStretch()
        l_layout.addWidget(pbar_shield_l)
        l_layout.addWidget(pbar_l)

        for child in loco_card.findChildren(QWidget):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.container_layout.addWidget(loco_card)

        # 2. Coaches Cards
        for idx, slot in enumerate(train_config.coaches):
            c_card = ClickableBlueprintCard()
            c_card.setObjectName(f"CoachCard_{idx}")
            is_sel = (selected_index == idx + 1)
            b_color = "#10b981" if is_sel else "#334155"
            bg_color = "#064e3b" if is_sel else "#1e293b"

            c_card.setMinimumSize(260, 180)
            c_card.setMaximumWidth(270)
            c_card.setStyleSheet(f"""
                QFrame#CoachCard_{idx} {{
                    background-color: {bg_color};
                    border: 2px solid {b_color};
                    border-radius: 8px;
                }}
                QFrame#CoachCard_{idx}:hover {{
                    border: 2px solid #10b981;
                }}
            """)
            c_card.setCursor(Qt.CursorShape.PointingHandCursor)
            c_card.clicked.connect(lambda i=idx: self.coachSelected.emit(i + 1))
            
            c_layout = QVBoxLayout(c_card)
            c_layout.setContentsMargins(10, 8, 10, 8)
            c_layout.setSpacing(3)

            syn = slot.get_synergy_power()
            chp = slot.couch_data.get("couchHp", 500) if slot.couch_data else 500
            cshield = slot.get_total_coach_shield(generator=train_config.generator)
            cdef = slot.get_total_coach_def()

            lbl_c_tag = QLabel(f"🚃 [객차 #{slot.index}번 칸] (시너지:{syn:.1f}x)")
            lbl_c_tag.setStyleSheet("font-weight: bold; color: #a7f3d0; font-size: 11px; border: none; background: transparent;")

            lbl_c_name = QLabel(slot.get_name())
            lbl_c_name.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13px; border: none; background: transparent;")
            
            lbl_c_stats = QLabel(f"• Def: {cdef:.1f} | 🛡️보호막: {cshield:.0f} | HP: {chp}")
            lbl_c_stats.setStyleSheet("color: #cbd5e1; font-size: 10.5px; border: none; background: transparent;")

            # 4 Turret Slots (T1, T2, T3, T4)
            t_box = QHBoxLayout()
            t_box.setSpacing(4)
            for t_i in range(4):
                if t_i < len(slot.turrets):
                    w = slot.turrets[t_i]
                    wname = (w.get("weaponName") or w.get("weaponId"))[:3]
                    ltype = str(w.get("weaponLandType") or "L").strip().upper()
                    t_color = "#f59e0b" if ltype == "L" else "#06b6d4"
                    t_chip = QLabel(f"T{t_i+1}:{wname}")
                    t_chip.setStyleSheet(f"background-color: {t_color}; color: #000000; font-size: 9.5px; font-weight: bold; border-radius: 3px; padding: 2px 4px;")
                else:
                    t_chip = QLabel(f"T{t_i+1}:-")
                    t_chip.setStyleSheet("background-color: #0f172a; color: #64748b; font-size: 9.5px; border-radius: 3px; padding: 2px 4px;")
                t_box.addWidget(t_chip)

            if slot.crew:
                c_crew_name = slot.crew.get("crewName") or slot.crew.get("crewId")
                lbl_crew = QLabel(f"👨‍✈️ 승무원: {c_crew_name} (Lv.{slot.crew_level})")
            else:
                lbl_crew = QLabel("👨‍✈️ 승무원: 미배치")
            lbl_crew.setStyleSheet("color: #818cf8; font-size: 10.5px; font-weight: bold; border: none; background: transparent;")

            pbar_shield_c = QProgressBar()
            pbar_shield_c.setValue(100)
            pbar_shield_c.setFixedHeight(4)
            pbar_shield_c.setTextVisible(False)
            pbar_shield_c.setStyleSheet("QProgressBar { background: #0f172a; border: none; border-radius: 2px; } QProgressBar::chunk { background: #06b6d4; border-radius: 2px; }")

            pbar_c = QProgressBar()
            pbar_c.setValue(100)
            pbar_c.setFixedHeight(4)
            pbar_c.setTextVisible(False)
            pbar_c.setStyleSheet("QProgressBar { background: #0f172a; border: none; border-radius: 2px; } QProgressBar::chunk { background: #10b981; border-radius: 2px; }")

            c_layout.addWidget(lbl_c_tag)
            c_layout.addWidget(lbl_c_name)
            c_layout.addWidget(lbl_c_stats)
            c_layout.addLayout(t_box)
            c_layout.addWidget(lbl_crew)
            c_layout.addStretch()
            for child in c_card.findChildren(QWidget):
                child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

            self.container_layout.addWidget(c_card)

        self.container_layout.addStretch()

class CoachStatDashboard(QGroupBox):
    """Compact Dedicated Stat Dashboard for a selected Coach"""
    def __init__(self, title="선택 객차 전용 스테이터스 대시보드", parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 6)
        layout.setSpacing(4)

        self.lbl_name = QLabel("선택된 객차 없음")
        self.lbl_name.setStyleSheet("font-size: 13px; font-weight: bold; color: #10b981;")
        layout.addWidget(self.lbl_name)

        grid = QGridLayout()
        grid.setSpacing(4)
        self.card_hp = StatCard("객차 체력 (HP)", "0", "#10b981")
        self.card_shield = StatCard("객차 보호막", "0", "#06b6d4")
        self.card_def = StatCard("객차 방어력", "0", "#3b82f6")
        self.card_weight = StatCard("객차 무게", "0 kg", "#ef4444")
        self.card_synergy = StatCard("시너지 계수", "1.0", "#8b5cf6")
        self.card_cost = StatCard("객차 가격", "0 G", "#f59e0b")

        grid.addWidget(self.card_hp, 0, 0)
        grid.addWidget(self.card_shield, 0, 1)
        grid.addWidget(self.card_def, 1, 0)
        grid.addWidget(self.card_weight, 1, 1)
        grid.addWidget(self.card_synergy, 2, 0)
        grid.addWidget(self.card_cost, 2, 1)
        layout.addLayout(grid)

        self.txt_details = QTextEdit()
        self.txt_details.setReadOnly(True)
        self.txt_details.setFixedHeight(95)
        self.txt_details.setStyleSheet("""
            QTextEdit {
                background-color: #0b0f19;
                border: 1px solid #334155;
                color: #f1f5f9;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                border-radius: 4px;
                padding: 4px;
            }
        """)
    def set_locomotive_data(self, train_config):
        if not train_config or not train_config.locomotive:
            self.lbl_name.setText("🚂 기관차 미선택")
            self.card_hp.set_title("기관차 체력 (HP)")
            self.card_shield.set_title("제네레이터 보호막")
            self.card_def.set_title("기관차 방어력")
            self.card_weight.set_title("현재 중량 / 허용 중량")
            self.card_synergy.set_title("총 엔진 출력")
            self.card_cost.set_title("객차 연결 (현재/최대)")

            self.card_hp.set_value(0)
            self.card_shield.set_value(0)
            self.card_def.set_value(0)
            self.card_weight.set_value(0, "0 kg")
            self.card_synergy.set_value(0, "0 HP")
            self.card_cost.set_value(0, "0 / 0 칸")
            self.txt_details.setText("기관차를 파츠선택에서 장착하세요.")
            return

        ldata = train_config.locomotive
        lname = ldata.get("locomotiveName") or "기관차"
        self.lbl_name.setText(f"🚂 [기관차 대시보드] {lname}")

        stats = train_config.calculate_stats()

        hp = ldata.get("locomotiveHp") or 0
        loco_shield = train_config.get_locomotive_shield()
        base_def = stats["locomotive_def"]
        wt_cur = stats["current_weight"]
        wt_lim = stats["weight_limit"]
        horsepower = stats["horsepower"]
        cc_cur = stats["current_couches"]
        cc_max = stats["max_couches"]

        self.card_hp.set_title("기관차 체력 (HP)")
        self.card_shield.set_title("제네레이터 보호막")
        self.card_def.set_title("기관차 방어력")
        self.card_weight.set_title("현재 중량 / 허용 중량")
        self.card_synergy.set_title("총 엔진 출력")
        self.card_cost.set_title("객차 연결 (현재/최대)")

        self.card_hp.set_value(hp)
        self.card_shield.set_value(loco_shield)
        self.card_def.set_value(base_def)
        self.card_weight.set_value(wt_cur, f"{wt_cur:.0f} / {wt_lim:.0f} kg", max_val=max(wt_lim, 1))
        self.card_synergy.set_value(horsepower, f"{horsepower:.0f} HP")
        self.card_cost.set_value(cc_cur, f"{cc_cur} / {cc_max} 칸", max_val=max(cc_max, 1))

        eng_name = train_config.engine.get("engineName") if train_config.engine else "엔진 미장착"
        gen_name = train_config.generator.get("generatorName") if train_config.generator else "제네레이터 미장착"
        brk_name = train_config.brake.get("breakName") if train_config.brake else "제동장치 미장착"

        lines = [
            f"⚡ 엔진: {eng_name} (가속력: {stats['accel_power']:.2f})",
            f"🛡️ 제네레이터: {gen_name} (전체 공유 보호막)",
            f"🛑 제동장치: {brk_name} (제동력: {stats['brake_power']:.2f})",
            f"🔫 기관차 자체 포탑 ({len(train_config.locomotive_turrets)}/2개):"
        ]
        if train_config.locomotive_turrets:
            for idx, w in enumerate(train_config.locomotive_turrets):
                wname = w.get("weaponName") or w.get("weaponId")
                pwr = float(w.get("weaponPower") or 0)
                ltype = str(w.get("weaponLandType") or "L").strip().upper()
                lines.append(f"   • T{idx+1}:{wname} [{ltype}] | 위력:{pwr:.1f}")
        else:
            lines.append("   • (장착된 기관차 포탑 없음)")

        self.txt_details.setText("\n".join(lines))

    def set_coach_slot(self, slot):
        self.card_hp.set_title("객차 체력 (HP)")
        self.card_shield.set_title("객차 보호막")
        self.card_def.set_title("객차 방어력")
        self.card_weight.set_title("객차 무게")
        self.card_synergy.set_title("시너지 계수")
        self.card_cost.set_title("객차 가격")

        if not slot or not slot.couch_data:
            self.lbl_name.setText("선택된 객차 없음")
            self.card_hp.set_value(0)
            self.card_shield.set_value(0)
            self.card_def.set_value(0)
            self.card_weight.set_value(0, "0 kg")
            self.card_synergy.set_value(1.0)
            self.card_cost.set_value(0, "0 G")
            self.txt_details.setText("객차를 선택하세요.")
            return

        cdata = slot.couch_data
        cname = slot.get_name()
        self.lbl_name.setText(f"🚃 [{slot.index}번 객차 대시보드] {cname}")

        hp = cdata.get("couchHp") or 0
        shield = cdata.get("couchShield") or 0
        base_def = cdata.get("couchDef") or 0
        
        eff_crew = slot.get_effective_crew_stats()
        crew_def = eff_crew["def"]
        total_def = base_def + crew_def

        weight = cdata.get("couchWeight") or 0
        synergy = eff_crew["synergy"]
        cost = cdata.get("couchCost") or 0

        self.card_hp.set_value(hp)
        self.card_shield.set_value(shield)
        self.card_def.set_value(total_def, f"{total_def:.1f} (기본:{base_def}+승무원:{crew_def:.1f})")
        self.card_weight.set_value(weight, f"{weight} kg")
        self.card_synergy.set_value(round(synergy, 2), f"{synergy:.2f}x")
        self.card_cost.set_value(cost, f"{cost:,} G")

        lines = []
        if slot.crew:
            cname = slot.crew.get("crewName") or slot.crew.get("crewId")
            ctype = slot.crew.get("crewType") or ""
            lvl = eff_crew.get("level", 1)
            atk_p = eff_crew.get("atk_pts", 0)
            def_p = eff_crew.get("def_pts", 0)
            prod_p = eff_crew.get("prod_pts", 0)
            pt_rate = eff_crew.get("point_rate", 1.0)

            b_land = eff_crew.get("base_landpower", 0.0)
            b_fly = eff_crew.get("base_flypower", 0.0)
            b_def = eff_crew.get("base_def", 0.0)
            b_prod = eff_crew.get("base_product", 0.0)
            b_ind = eff_crew.get("base_industry", 0.0)

            e_land = eff_crew["landpower"]
            e_fly = eff_crew["flypower"]
            e_def = eff_crew["def"]
            e_prod = eff_crew.get("product", 0.0)
            e_ind = eff_crew.get("industry", 0.0)

            lines.append(f"👨‍✈️ 승무원: {cname} [{ctype}] (Lv.{lvl} | ⚔️공격+{atk_p}pt, 🛡️방어+{def_p}pt, 🏭생산+{prod_p}pt | 1pt당 +{pt_rate:.1f}%)")
            lines.append(f"   • 대지:{e_land:.1f} (기본 {b_land:.0f}*(1+{atk_p*pt_rate/100:.2f})*{synergy:.2f}x) | 대공:{e_fly:.1f} (기본 {b_fly:.0f}*(1+{atk_p*pt_rate/100:.2f})*{synergy:.2f}x)")
            lines.append(f"   • Def:+{e_def:.1f} (기본 {b_def:.0f}*(1+{def_p*pt_rate/100:.2f})*{synergy:.2f}x)")
            lines.append(f"   • 생산:{e_prod:.1f} (기본 {b_prod:.0f}*(1+{prod_p*pt_rate/100:.2f})*{synergy:.2f}x) | 공업:{e_ind:.1f} (기본 {b_ind:.0f}*(1+{prod_p*pt_rate/100:.2f})*{synergy:.2f}x)")
        else:
            lines.append("👨‍✈️ 승무원: 미배치")

        lines.append(f"🔫 포탑 ({len(slot.turrets)}/4개):")
        if slot.turrets:
            for idx, w in enumerate(slot.turrets):
                wname = w.get("weaponName") or w.get("weaponId")
                base_pwr = float(w.get("weaponPower") or 0)
                ltype = str(w.get("weaponLandType") or "L").strip().upper()

                if ltype == "L":
                    c_bonus = eff_crew["landpower"]
                    type_str = "대지(L)"
                elif ltype == "F":
                    c_bonus = eff_crew["flypower"]
                    type_str = "대공(F)"
                else:
                    c_bonus = max(eff_crew["landpower"], eff_crew["flypower"])
                    type_str = "대지/대공(LF)"

                total_pwr = base_pwr + c_bonus
                lines.append(f"   • T{idx+1}:{wname} [{type_str}] | 위력:{total_pwr:.1f}(기본:{base_pwr:.1f}+승무원:{c_bonus:.1f})")
        else:
            lines.append("   • (장착된 포탑 없음)")

        self.txt_details.setText("\n".join(lines))

class IndividualStatInspector(QFrame):
    """Expanded Widget to display raw individual stats of a selected object"""
    def __init__(self, title="개별 스테이터스 상세 정보", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-weight: bold; color: #818cf8; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(self.lbl_title)

        self.txt_display = QTextEdit()
        self.txt_display.setReadOnly(True)
        self.txt_display.setStyleSheet("""
            QTextEdit {
                background-color: #0b0f19;
                border: 1px solid #334155;
                color: #f1f5f9;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.txt_display, stretch=1)

    def set_item_data(self, item_name, data_dict):
        if not data_dict:
            self.lbl_title.setText("개별 스테이터스: (선택 항목 없음)")
            self.txt_display.setText("선택된 개별 물체가 없습니다.")
            return

        self.lbl_title.setText(f"🔍 {item_name} 상세 스탯")
        lines = []
        for k, v in data_dict.items():
            val_str = str(v) if v is not None else "-"
            lines.append(f"  • {k:<22}: {val_str}")
        self.txt_display.setText("\n".join(lines))

class DataTableWidget(QWidget):
    rowSelected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        search_box = QHBoxLayout()
        search_label = QLabel("🔍 검색:")
        search_label.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 11px; border: none; background: transparent;")
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("검색어를 입력하세요...")
        self.txt_search.textChanged.connect(self._filter_table)
        search_box.addWidget(search_label)
        search_box.addWidget(self.txt_search)
        layout.addLayout(search_box)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        self._columns = []
        self._raw_data = []

    def set_data(self, columns_info, records):
        self._raw_data = records
        self._columns = []
        header_labels = []

        for col in columns_info:
            if isinstance(col, tuple):
                field_key = col[0]
                label = col[1] if len(col) > 1 else col[0]
            else:
                field_key = str(col)
                label = str(col)
            self._columns.append(field_key)
            header_labels.append(label)

        self.table.setRowCount(0)
        self.table.setColumnCount(len(self._columns))
        self.table.setHorizontalHeaderLabels(header_labels)

        for r_idx, rec in enumerate(records):
            self.table.insertRow(r_idx)
            for c_idx, col_name in enumerate(self._columns):
                val = rec.get(col_name)
                display_str = str(val) if val is not None else "-"
                item = QTableWidgetItem(display_str)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r_idx, c_idx, item)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

    def _filter_table(self, query):
        q = query.strip().lower()
        for row in range(self.table.rowCount()):
            match = False
            if not q:
                match = True
            else:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and q in item.text().lower():
                        match = True
                        break
            self.table.setRowHidden(row, not match)

    def _on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row_idx = selected_rows[0].row()
            if 0 <= row_idx < len(self._raw_data):
                self.rowSelected.emit(self._raw_data[row_idx])

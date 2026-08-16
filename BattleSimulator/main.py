import sys
import os
import csv
import random
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QGroupBox, QLabel, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QGridLayout,
    QSpinBox, QDoubleSpinBox, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QSplitter, QFileDialog, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QPen, QFont

from data_loader import DataLoader
from models import TrainConfig, TurretConfig, EnemyGroupConfig
from battle_engine import BattleSimulationEngine
from ui_components import (
    DARK_STYLESHEET, StatCard, DataTableWidget, IndividualStatInspector,
    CoachStatDashboard, VisualTrainBlueprintHeader
)

class BattleSimulatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Siecletrain - 전투 시뮬레이터 (Visual Blueprint UI & 16:9 Layout)")
        # Standard 16:9 Aspect Ratio Window Size
        self.resize(1366, 768)

        # 1. Load Data
        self.loader = DataLoader()

        # 2. Models
        self.train_config = TrainConfig()
        self.turret_config = TurretConfig(max_slots_per_coach=4)
        self.enemy_config = EnemyGroupConfig()

        self.last_engine = None
        self.last_summary = None

        self._refresh_data_maps()
        self.init_ui()

    def _refresh_data_maps(self):
        self.locomotives_map = {r["locomotiveId"]: r for r in self.loader.get_sheet_data("Locomotive") if r.get("locomotiveId")}
        self.couches_map = {r["couchId"]: r for r in self.loader.get_sheet_data("Couch") if r.get("couchId")}
        self.engines_map = {r["engineId"]: r for r in self.loader.get_sheet_data("Engine") if r.get("engineId")}
        self.generators_map = {r["generatorId"]: r for r in self.loader.get_sheet_data("Generator") if r.get("generatorId")}
        self.brakes_map = {r["breakId"]: r for r in self.loader.get_sheet_data("Break") if r.get("breakId")}
        self.crews_map = {r["crewId"]: r for r in self.loader.get_sheet_data("Crew") if r.get("crewId")}
        self.weapons_map = {r["weaponId"]: r for r in self.loader.get_sheet_data("Weapon") if r.get("weaponId")}
        self.monsters_map = {r["monsterId"]: r for r in self.loader.get_sheet_data("MonsterData") if r.get("monsterId")}
        self.battle_areas_map = {r["battleAreaId"]: r for r in self.loader.get_sheet_data("BattleArea") if r.get("battleAreaId")}

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 4, 6, 4)
        main_layout.setSpacing(4)

        # Header Title & Reload Bar
        header_box = QHBoxLayout()
        header_box.setContentsMargins(2, 0, 2, 0)
        header = QLabel("🚂 SIECLETRAIN VISUAL BATTLE SIMULATOR")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #818cf8; padding: 2px;")
        header_box.addWidget(header)

        header_box.addStretch()

        btn_reload = QPushButton("🔄 엑셀 새로고침 (Excel Reload)")
        btn_reload.setStyleSheet("font-size: 11px; font-weight: bold; background-color: #8b5cf6; padding: 4px 10px;")
        btn_reload.clicked.connect(self.reload_excel_data)
        header_box.addWidget(btn_reload)

        main_layout.addLayout(header_box)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=1)

        self.tab_workshop = QWidget()
        self.tab_log_sheet = QWidget()
        self.tab_inspector = QWidget()
        self.tab_crew_sim = QWidget()

        self.tabs.addTab(self.tab_workshop, "1. 🚂 통합 열차 & 적 세팅 워크숍")
        self.tabs.addTab(self.tab_log_sheet, "2. 📋 전투 로그 시트 (Combat Log)")
        self.tabs.addTab(self.tab_inspector, "3. 🔍 Raw 데이터 검증 (Inspector)")
        self.tabs.addTab(self.tab_crew_sim, "4. 🎲 승무원 레벨업 랜덤 성장 시뮬레이터")

        # Build each tab
        self._build_workshop_tab()
        self._build_log_sheet_tab()
        self._build_inspector_tab()
        self._build_crew_sim_tab()

        self._populate_all_combos()

        # Initial Updates
        self._update_train_stats()
        self._update_coach_layout_ui()
        self._update_enemy_ui()

    def _on_blueprint_coach_clicked(self, list_row_idx):
        if 0 <= list_row_idx < self.lst_layout_couches.count():
            self.lst_layout_couches.setCurrentRow(list_row_idx)

    def reload_excel_data(self):
        try:
            self.loader.reload_all_data()
            self._refresh_data_maps()

            self._populate_all_combos()

            cols_w = self.loader.get_sheet_columns("Weapon")
            recs_w = self.loader.get_sheet_data("Weapon")
            self.weapon_db_table.set_data(cols_w, recs_w)

            monster_cols = [
                ("monsterId", "ID"),
                ("monsterName", "Name"),
                ("monsterLv", "레벨"),
                ("monsterUseArea", "Area")
            ]
            recs_m = self.loader.get_sheet_data("MonsterData")
            self.monster_table.set_data(monster_cols, recs_m)

            self._rebuild_inspector_tab()

            self._on_train_part_changed()
            self._update_coach_layout_ui()
            self._update_enemy_ui()
            self._update_preview_ui()

            total_items = sum(len(r) for r in self.loader.data.values())
            QMessageBox.information(
                self, "새로고침 완료",
                f"엑셀 파일에서 총 {total_items}건의 데이터가 성공적으로 새로고침 되었습니다!"
            )
        except Exception as e:
            QMessageBox.critical(self, "새로고침 오류", f"엑셀 파일 읽기 중 오류 발생:\n{e}")

    def _populate_all_combos(self):
        cur_loco = self.combo_loco.currentData()
        self.combo_loco.blockSignals(True)
        self.combo_loco.clear()
        self.combo_loco.addItem("-- 미장착 --", None)
        for lid, ldata in self.locomotives_map.items():
            name = ldata.get("locomotiveName") or lid
            self.combo_loco.addItem(f"{name} ({lid})", lid)
        if cur_loco is not None:
            idx = self.combo_loco.findData(cur_loco)
            if idx >= 0:
                self.combo_loco.setCurrentIndex(idx)
        else:
            self.combo_loco.setCurrentIndex(0)
        self.combo_loco.blockSignals(False)

        cur_eng = self.combo_engine.currentData()
        self.combo_engine.blockSignals(True)
        self.combo_engine.clear()
        self.combo_engine.addItem("-- 미장착 --", None)
        for eid, edata in self.engines_map.items():
            name = edata.get("engineName") or eid
            self.combo_engine.addItem(f"{name} ({eid})", eid)
        if cur_eng:
            idx = self.combo_engine.findData(cur_eng)
            if idx >= 0:
                self.combo_engine.setCurrentIndex(idx)
        self.combo_engine.blockSignals(False)

        cur_gen = self.combo_gen.currentData()
        self.combo_gen.blockSignals(True)
        self.combo_gen.clear()
        self.combo_gen.addItem("-- 미장착 --", None)
        for gid, gdata in self.generators_map.items():
            name = gdata.get("generatorName") or gid
            self.combo_gen.addItem(f"{name} ({gid})", gid)
        if cur_gen:
            idx = self.combo_gen.findData(cur_gen)
            if idx >= 0:
                self.combo_gen.setCurrentIndex(idx)
        self.combo_gen.blockSignals(False)

        cur_brk = self.combo_brake.currentData()
        self.combo_brake.blockSignals(True)
        self.combo_brake.clear()
        self.combo_brake.addItem("-- 미장착 --", None)
        for bid, bdata in self.brakes_map.items():
            name = bdata.get("breakName") or bid
            self.combo_brake.addItem(f"{name} ({bid})", bid)
        if cur_brk:
            idx = self.combo_brake.findData(cur_brk)
            if idx >= 0:
                self.combo_brake.setCurrentIndex(idx)
        self.combo_brake.blockSignals(False)

        if hasattr(self, 'combo_couch_add'):
            self.combo_couch_add.clear()
            for cid, cdata in self.couches_map.items():
                name = cdata.get("couchName") or cid
                syn = cdata.get("couchSynergyPower") or 1.0
                self.combo_couch_add.addItem(f"{name} (시너지:{syn:.1f}x)", cid)

        if hasattr(self, 'combo_turret_add'):
            self.combo_turret_add.clear()
            for wid, wdata in self.weapons_map.items():
                wname = wdata.get("weaponName") or wid
                pwr = wdata.get("weaponPower") or 0
                ltype = wdata.get("weaponLandType") or "L"
                self.combo_turret_add.addItem(f"[{ltype}] {wname} (위력:{pwr})", wid)

        if hasattr(self, 'combo_coach_crew'):
            self.combo_coach_crew.clear()
            self.combo_coach_crew.addItem("-- 승무원 미배치 --", None)
            for cid, cdata in self.crews_map.items():
                name = cdata.get("crewName") or cid
                land = cdata.get("crewLandpower") or 0
                fly = cdata.get("crewFlypower") or 0
                self.combo_coach_crew.addItem(f"{name} (대지+{land}, 대공+{fly})", cid)

        if hasattr(self, 'combo_battle_area'):
            self.combo_battle_area.clear()
            self.combo_battle_area.addItem("-- 프리셋 선택 --", None)
            for ba_id, ba_data in self.battle_areas_map.items():
                lvl_id = ba_data.get("battleLevelId") or ""
                self.combo_battle_area.addItem(f"{ba_id} [{lvl_id}]", ba_id)

        if hasattr(self, 'combo_sim_crew'):
            cur_sim_crew = self.combo_sim_crew.currentData()
            self.combo_sim_crew.blockSignals(True)
            self.combo_sim_crew.clear()
            for cid, cdata in self.crews_map.items():
                name = cdata.get("crewName") or cid
                ctype = cdata.get("crewType") or "일반"
                self.combo_sim_crew.addItem(f"[{ctype}] {name} ({cid})", cid)
            if cur_sim_crew:
                idx = self.combo_sim_crew.findData(cur_sim_crew)
                if idx >= 0:
                    self.combo_sim_crew.setCurrentIndex(idx)
            self.combo_sim_crew.blockSignals(False)
            self._on_sim_crew_selected()

    # ----------------------------------------------------
    # UNIFIED MASTER WORKSHOP TAB (Tabs 1, 2, 3, 4 Combined)
    # ----------------------------------------------------
    def _build_workshop_tab(self):
        tab_layout = QVBoxLayout(self.tab_workshop)
        tab_layout.setContentsMargins(4, 4, 4, 4)
        tab_layout.setSpacing(4)

        # 1. TOP AREA: VISUAL BLUEPRINT UI (Occupies ~25% Height)
        self.train_blueprint = VisualTrainBlueprintHeader()
        self.train_blueprint.coachSelected.connect(self._on_blueprint_coach_clicked)
        tab_layout.addWidget(self.train_blueprint, stretch=3)

        # 2. BOTTOM AREA: 3-COLUMN SPLIT LAYOUT (Occupies ~75% Height)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(6)

        # =========================================================================
        # COLUMN 1 (LEFT): 📊 능력치 대시보드 & 기관차 파츠 세팅
        # =========================================================================
        box_col1 = QWidget()
        col1_layout = QVBoxLayout(box_col1)
        col1_layout.setContentsMargins(0, 0, 0, 0)
        col1_layout.setSpacing(6)

        # 1. TOP: Dynamic Unified Selection Stat Dashboard ( 기관차 <-> 객차 실시간 전환 대시보드 )
        self.coach_stat_dashboard = CoachStatDashboard("📊 능력치 대시보드")
        col1_layout.addWidget(self.coach_stat_dashboard, stretch=2)

        # 2. BOTTOM: 기관차 파츠 선택 GroupBox
        box_parts = QGroupBox("🚂 기관차 핵심 파츠 선택")
        grid_parts = QGridLayout(box_parts)
        grid_parts.setContentsMargins(6, 6, 6, 6)
        grid_parts.setSpacing(4)

        grid_parts.addWidget(QLabel("기관차 (Loco):"), 0, 0)
        self.combo_loco = QComboBox()
        grid_parts.addWidget(self.combo_loco, 0, 1)

        grid_parts.addWidget(QLabel("⚡ 엔진 (Engine):"), 1, 0)
        self.combo_engine = QComboBox()
        grid_parts.addWidget(self.combo_engine, 1, 1)

        grid_parts.addWidget(QLabel("🛡️ 제네레이터 (Gen):"), 2, 0)
        self.combo_gen = QComboBox()
        grid_parts.addWidget(self.combo_gen, 2, 1)

        grid_parts.addWidget(QLabel("🛑 제동장치 (Brake):"), 3, 0)
        self.combo_brake = QComboBox()
        grid_parts.addWidget(self.combo_brake, 3, 1)

        col1_layout.addWidget(box_parts)

        bottom_layout.addWidget(box_col1, stretch=3)

        # =========================================================================
        # COLUMN 2 (MIDDLE): 🚃 객차 구성 & 포탑/승무원 세팅 & Inspector
        # =========================================================================
        box_col2 = QGroupBox("🚃 객차배치도 & 포탑/승무원 세팅")
        col2_layout = QVBoxLayout(box_col2)
        col2_layout.setContentsMargins(6, 6, 6, 6)
        col2_layout.setSpacing(4)

        # Add Coach Row
        add_c_row = QHBoxLayout()
        self.combo_couch_add = QComboBox()
        btn_add_couch = QPushButton("객차 추가 (+)")
        btn_add_couch.setObjectName("btn-success")
        btn_add_couch.clicked.connect(self._add_couch)
        add_c_row.addWidget(self.combo_couch_add, stretch=1)
        add_c_row.addWidget(btn_add_couch)
        col2_layout.addLayout(add_c_row)

        # Coach List (Item 0: Locomotive, Item 1..N: Coaches)
        col2_layout.addWidget(QLabel("📋 열차 칸 목록 (클릭하여 장착/배치):"))
        self.lst_layout_couches = QListWidget()
        self.lst_layout_couches.currentRowChanged.connect(self._on_layout_coach_selected)
        col2_layout.addWidget(self.lst_layout_couches, stretch=2)

        # Remove Coach Button
        btn_remove_couch = QPushButton("선택한 객차 삭제 (-)")
        btn_remove_couch.setObjectName("btn-danger")
        btn_remove_couch.clicked.connect(self._remove_couch)
        col2_layout.addWidget(btn_remove_couch)

        # Selected Coach Details & Customization Label
        self.lbl_selected_coach_info = QLabel("객차를 블루프린트나 목록에서 선택하세요.")
        self.lbl_selected_coach_info.setStyleSheet("font-weight: bold; color: #10b981; font-size: 11px;")
        col2_layout.addWidget(self.lbl_selected_coach_info)

        # Turret Equipment Row
        t_box = QHBoxLayout()
        t_box.addWidget(QLabel("포탑 장착:"))
        self.combo_turret_add = QComboBox()
        btn_equip_turret = QPushButton("장착 (+)")
        btn_equip_turret.setObjectName("btn-success")
        btn_equip_turret.clicked.connect(self._equip_turret_to_selected_coach)
        t_box.addWidget(self.combo_turret_add, stretch=1)
        t_box.addWidget(btn_equip_turret)
        col2_layout.addLayout(t_box)

        # Mounted Turret List
        self.lst_coach_turrets = QListWidget()
        self.lst_coach_turrets.setFixedHeight(65)
        col2_layout.addWidget(self.lst_coach_turrets)

        btn_unequip_turret = QPushButton("선택 포탑 해제 (-)")
        btn_unequip_turret.setObjectName("btn-danger")
        btn_unequip_turret.clicked.connect(self._unequip_turret_from_selected_coach)
        col2_layout.addWidget(btn_unequip_turret)

        # Crew Assignment Row
        c_box = QHBoxLayout()
        c_box.addWidget(QLabel("승무원 배치:"))
        self.combo_coach_crew = QComboBox()
        btn_assign_crew = QPushButton("배치 (+)")
        btn_assign_crew.setObjectName("btn-success")
        btn_assign_crew.clicked.connect(self._assign_crew_to_selected_coach)
        btn_unassign_crew = QPushButton("해제 (-)")
        btn_unassign_crew.setObjectName("btn-danger")
        btn_unassign_crew.clicked.connect(self._unassign_crew_from_selected_coach)
        c_box.addWidget(self.combo_coach_crew, stretch=1)
        c_box.addWidget(btn_assign_crew)
        c_box.addWidget(btn_unassign_crew)
        col2_layout.addLayout(c_box)

        # Crew Level & Stat Points Distribution Panel
        self.box_crew_level = QGroupBox("👨‍✈️ 승무원 레벨 & 스탯 포인트 배분 (※ 승무원을 배치한 칸만 조절 가능 / 기관차 불가)")
        crew_lvl_layout = QVBoxLayout(self.box_crew_level)
        crew_lvl_layout.setContentsMargins(6, 6, 6, 6)
        crew_lvl_layout.setSpacing(4)

        # Row 1: Level spinbox with [-10], [-], [+], [+10] buttons, Remaining Points label, Common point rate spinbox
        lvl_row = QHBoxLayout()
        lvl_row.setSpacing(3)
        lvl_row.addWidget(QLabel("레벨(1~50):"))

        btn_lvl_style = "QPushButton { font-size: 11px; font-weight: bold; padding: 0px; min-width: 26px; height: 24px; border-radius: 3px; } QPushButton:hover { background-color: #3b82f6; color: white; }"

        btn_lvl_m10 = QPushButton("-10")
        btn_lvl_m10.setStyleSheet(btn_lvl_style)
        btn_lvl_m10.setFixedWidth(30)
        btn_lvl_m10.clicked.connect(lambda: self._adjust_crew_level(-10))
        lvl_row.addWidget(btn_lvl_m10)

        btn_lvl_minus = QPushButton("-")
        btn_lvl_minus.setStyleSheet(btn_lvl_style)
        btn_lvl_minus.setFixedWidth(24)
        btn_lvl_minus.clicked.connect(lambda: self._adjust_crew_level(-1))
        lvl_row.addWidget(btn_lvl_minus)

        self.spin_crew_level = QSpinBox()
        self.spin_crew_level.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_crew_level.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_crew_level.setFixedWidth(36)
        self.spin_crew_level.setFixedHeight(24)
        self.spin_crew_level.setStyleSheet("font-size: 11px; font-weight: bold; padding: 0px;")
        self.spin_crew_level.setRange(1, 50)
        self.spin_crew_level.setValue(1)
        self.spin_crew_level.valueChanged.connect(self._on_crew_level_changed)
        lvl_row.addWidget(self.spin_crew_level)

        btn_lvl_plus = QPushButton("+")
        btn_lvl_plus.setStyleSheet(btn_lvl_style)
        btn_lvl_plus.setFixedWidth(24)
        btn_lvl_plus.clicked.connect(lambda: self._adjust_crew_level(1))
        lvl_row.addWidget(btn_lvl_plus)

        btn_lvl_p10 = QPushButton("+10")
        btn_lvl_p10.setStyleSheet(btn_lvl_style)
        btn_lvl_p10.setFixedWidth(30)
        btn_lvl_p10.clicked.connect(lambda: self._adjust_crew_level(10))
        lvl_row.addWidget(btn_lvl_p10)

        self.lbl_crew_points_remaining = QLabel("남은 포인트: 0 / 0 pt")
        self.lbl_crew_points_remaining.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 11px;")
        lvl_row.addWidget(self.lbl_crew_points_remaining, stretch=1)

        lvl_row.addWidget(QLabel("1pt당 증가율:"))
        self.spin_crew_point_rate = QDoubleSpinBox()
        self.spin_crew_point_rate.setRange(0.1, 100.0)
        self.spin_crew_point_rate.setSingleStep(0.5)
        self.spin_crew_point_rate.setValue(1.0)
        self.spin_crew_point_rate.setSuffix(" %")
        self.spin_crew_point_rate.valueChanged.connect(self._on_crew_point_rate_changed)
        lvl_row.addWidget(self.spin_crew_point_rate)

        crew_lvl_layout.addLayout(lvl_row)

        # Row 2: 3 Points Input (Attack, Defense, Production/Industry) with explicit [-], [+] buttons
        pts_grid = QGridLayout()
        pts_grid.setSpacing(4)

        btn_pts_style = "QPushButton { font-size: 12px; font-weight: bold; padding: 0px; min-width: 22px; max-width: 24px; height: 24px; border-radius: 3px; } QPushButton:hover { background-color: #10b981; color: white; }"

        # Attack Row
        pts_grid.addWidget(QLabel("⚔️ 공격력:"), 0, 0)
        atk_box = QHBoxLayout()
        atk_box.setSpacing(2)
        btn_atk_m = QPushButton("-")
        btn_atk_m.setStyleSheet(btn_pts_style)
        btn_atk_m.setFixedSize(24, 24)
        btn_atk_m.clicked.connect(lambda: self._adjust_crew_point("atk", -1))
        self.spin_crew_atk_pts = QSpinBox()
        self.spin_crew_atk_pts.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_crew_atk_pts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_crew_atk_pts.setFixedWidth(36)
        self.spin_crew_atk_pts.setFixedHeight(24)
        self.spin_crew_atk_pts.setStyleSheet("font-size: 11px; font-weight: bold; padding: 0px;")
        self.spin_crew_atk_pts.setRange(0, 49)
        self.spin_crew_atk_pts.setValue(0)
        self.spin_crew_atk_pts.valueChanged.connect(self._on_crew_points_changed)
        btn_atk_p = QPushButton("+")
        btn_atk_p.setStyleSheet(btn_pts_style)
        btn_atk_p.setFixedSize(24, 24)
        btn_atk_p.clicked.connect(lambda: self._adjust_crew_point("atk", 1))
        atk_box.addWidget(btn_atk_m)
        atk_box.addWidget(self.spin_crew_atk_pts)
        atk_box.addWidget(btn_atk_p)
        pts_grid.addLayout(atk_box, 0, 1)

        # Defense Row
        pts_grid.addWidget(QLabel("🛡️ 방어력:"), 0, 2)
        def_box = QHBoxLayout()
        def_box.setSpacing(2)
        btn_def_m = QPushButton("-")
        btn_def_m.setStyleSheet(btn_pts_style)
        btn_def_m.setFixedSize(24, 24)
        btn_def_m.clicked.connect(lambda: self._adjust_crew_point("def", -1))
        self.spin_crew_def_pts = QSpinBox()
        self.spin_crew_def_pts.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_crew_def_pts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_crew_def_pts.setFixedWidth(36)
        self.spin_crew_def_pts.setFixedHeight(24)
        self.spin_crew_def_pts.setStyleSheet("font-size: 11px; font-weight: bold; padding: 0px;")
        self.spin_crew_def_pts.setRange(0, 49)
        self.spin_crew_def_pts.setValue(0)
        self.spin_crew_def_pts.valueChanged.connect(self._on_crew_points_changed)
        btn_def_p = QPushButton("+")
        btn_def_p.setStyleSheet(btn_pts_style)
        btn_def_p.setFixedSize(24, 24)
        btn_def_p.clicked.connect(lambda: self._adjust_crew_point("def", 1))
        def_box.addWidget(btn_def_m)
        def_box.addWidget(self.spin_crew_def_pts)
        def_box.addWidget(btn_def_p)
        pts_grid.addLayout(def_box, 0, 3)

        # Production Row
        pts_grid.addWidget(QLabel("🏭 생산/공업:"), 1, 0)
        prod_box = QHBoxLayout()
        prod_box.setSpacing(2)
        btn_prod_m = QPushButton("-")
        btn_prod_m.setStyleSheet(btn_pts_style)
        btn_prod_m.setFixedSize(24, 24)
        btn_prod_m.clicked.connect(lambda: self._adjust_crew_point("prod", -1))
        self.spin_crew_prod_pts = QSpinBox()
        self.spin_crew_prod_pts.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_crew_prod_pts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_crew_prod_pts.setFixedWidth(36)
        self.spin_crew_prod_pts.setFixedHeight(24)
        self.spin_crew_prod_pts.setStyleSheet("font-size: 11px; font-weight: bold; padding: 0px;")
        self.spin_crew_prod_pts.setRange(0, 49)
        self.spin_crew_prod_pts.setValue(0)
        self.spin_crew_prod_pts.valueChanged.connect(self._on_crew_points_changed)
        btn_prod_p = QPushButton("+")
        btn_prod_p.setStyleSheet(btn_pts_style)
        btn_prod_p.setFixedSize(24, 24)
        btn_prod_p.clicked.connect(lambda: self._adjust_crew_point("prod", 1))
        prod_box.addWidget(btn_prod_m)
        prod_box.addWidget(self.spin_crew_prod_pts)
        prod_box.addWidget(btn_prod_p)
        pts_grid.addLayout(prod_box, 1, 1)

        # Quick preset buttons
        quick_btn_box = QHBoxLayout()
        quick_btn_box.setSpacing(3)
        btn_pts_reset = QPushButton("초기화")
        btn_pts_reset.clicked.connect(lambda: self._quick_distribute_crew_points("reset"))
        btn_pts_atk = QPushButton("공격 올인")
        btn_pts_atk.clicked.connect(lambda: self._quick_distribute_crew_points("atk"))
        btn_pts_def = QPushButton("방어 올인")
        btn_pts_def.clicked.connect(lambda: self._quick_distribute_crew_points("def"))
        btn_pts_even = QPushButton("균등 분배")
        btn_pts_even.clicked.connect(lambda: self._quick_distribute_crew_points("even"))

        quick_btn_box.addWidget(btn_pts_reset)
        quick_btn_box.addWidget(btn_pts_atk)
        quick_btn_box.addWidget(btn_pts_def)
        quick_btn_box.addWidget(btn_pts_even)
        pts_grid.addLayout(quick_btn_box, 1, 2, 1, 2)

        crew_lvl_layout.addLayout(pts_grid)
        col2_layout.addWidget(self.box_crew_level)

        bottom_layout.addWidget(box_col2, stretch=4)

        # =========================================================================
        # COLUMN 3 (RIGHT): 👾 적 군단 세팅 & 전투 시뮬레이션 즉시 실행
        # =========================================================================
        box_col3 = QGroupBox("👾 적 군단 선택 & 전투 실행")
        col3_layout = QVBoxLayout(box_col3)
        col3_layout.setContentsMargins(6, 6, 6, 6)
        col3_layout.setSpacing(4)

        # Preset Selector
        ba_row = QHBoxLayout()
        ba_row.addWidget(QLabel("전투 구역 (BattleArea):"))
        self.combo_battle_area = QComboBox()
        self.combo_battle_area.currentIndexChanged.connect(self._on_battle_area_selected)
        ba_row.addWidget(self.combo_battle_area, stretch=1)
        col3_layout.addLayout(ba_row)

        # Monster Selection Table (Show ID, Name, Level, Area only)
        self.monster_table = DataTableWidget()
        monster_cols = [
            ("monsterId", "ID"),
            ("monsterName", "Name"),
            ("monsterLv", "레벨"),
            ("monsterUseArea", "Area")
        ]
        recs_m = self.loader.get_sheet_data("MonsterData")
        self.monster_table.set_data(monster_cols, recs_m)
        self.monster_table.rowSelected.connect(self._on_monster_selected)
        col3_layout.addWidget(self.monster_table, stretch=2)

        # Add Monster Control Row
        add_m_row = QHBoxLayout()
        add_m_row.addWidget(QLabel("수량:"))
        self.spin_monster_count = QSpinBox()
        self.spin_monster_count.setRange(1, 100)
        self.spin_monster_count.setValue(5)
        add_m_row.addWidget(self.spin_monster_count)

        btn_add_enemy = QPushButton("적 추가 (+)")
        btn_add_enemy.setObjectName("btn-success")
        btn_add_enemy.clicked.connect(self._add_selected_monster_to_army)
        add_m_row.addWidget(btn_add_enemy)
        col3_layout.addLayout(add_m_row)

        # Enemies Army List & Summary Card
        self.lst_enemies = QListWidget()
        self.lst_enemies.setFixedHeight(85)
        col3_layout.addWidget(self.lst_enemies)

        self.card_enemy_summary = StatCard("적 군단 합산 스탯", "총 0 마리", "#ef4444")
        col3_layout.addWidget(self.card_enemy_summary)

        btn_clear_enemies = QPushButton("적 군단 전체 초기화")
        btn_clear_enemies.setObjectName("btn-danger")
        btn_clear_enemies.clicked.connect(self._clear_enemy_army)
        col3_layout.addWidget(btn_clear_enemies)

        # 🚀 Instant Simulation Execution Button!
        btn_start_sim = QPushButton("⚡ 전투 시뮬레이션 실행 (Run Engine & View Log)")
        btn_start_sim.setStyleSheet("font-size: 13.5px; font-weight: bold; padding: 8px; background-color: #10b981; color: white; border-radius: 6px;")
        btn_start_sim.clicked.connect(self._run_simulation_engine)
        col3_layout.addWidget(btn_start_sim)

        bottom_layout.addWidget(box_col3, stretch=4)

        tab_layout.addLayout(bottom_layout, stretch=7)

        # Connect signals for Part combos
        self.combo_loco.currentIndexChanged.connect(self._on_train_part_changed)
        self.combo_engine.currentIndexChanged.connect(self._on_train_part_changed)
        self.combo_gen.currentIndexChanged.connect(self._on_train_part_changed)
        self.combo_brake.currentIndexChanged.connect(self._on_train_part_changed)

    def _on_train_part_changed(self):
        loco_id = self.combo_loco.currentData()
        self.train_config.locomotive = self.locomotives_map.get(loco_id) if loco_id else None

        engine_id = self.combo_engine.currentData()
        self.train_config.engine = self.engines_map.get(engine_id) if engine_id else None

        gen_id = self.combo_gen.currentData()
        self.train_config.generator = self.generators_map.get(gen_id) if gen_id else None

        brake_id = self.combo_brake.currentData()
        self.train_config.brake = self.brakes_map.get(brake_id) if brake_id else None

        sender = self.sender()
        if hasattr(self, 'inspector_train_part') and self.inspector_train_part:
            if sender == self.combo_loco:
                if self.train_config.locomotive:
                    self.inspector_train_part.set_item_data(self.train_config.locomotive.get("locomotiveName") or loco_id, self.train_config.locomotive)
                else:
                    self.inspector_train_part.set_item_data("기관차 미선택", None)
            elif sender == self.combo_engine:
                if self.train_config.engine:
                    self.inspector_train_part.set_item_data(self.train_config.engine.get("engineName") or engine_id, self.train_config.engine)
                else:
                    self.inspector_train_part.set_item_data("엔진 미선택", None)
            elif sender == self.combo_gen:
                if self.train_config.generator:
                    self.inspector_train_part.set_item_data(self.train_config.generator.get("generatorName") or gen_id, self.train_config.generator)
                else:
                    self.inspector_train_part.set_item_data("제네레이터 미선택", None)
            elif sender == self.combo_brake:
                if self.train_config.brake:
                    self.inspector_train_part.set_item_data(self.train_config.brake.get("breakName") or brake_id, self.train_config.brake)
                else:
                    self.inspector_train_part.set_item_data("제동장치 미선택", None)

        self._update_train_stats()

    def _add_couch(self):
        if not self.train_config.locomotive:
            QMessageBox.warning(self, "기관차 미선택", "기관차를 먼저 선택하세요.")
            return

        max_couches = int(self.train_config.locomotive.get("locomotiveCouch") or 0)
        current_couches = len(self.train_config.coaches)
        if current_couches >= max_couches:
            loco_name = self.train_config.locomotive.get("locomotiveName") or "기관차"
            QMessageBox.warning(
                self, "최대 객차 연결 제한",
                f"선택한 [{loco_name}] 기관차에는 최대 {max_couches}칸의 객차만 연결할 수 있습니다!\n(현재 연결 수: {current_couches} / {max_couches}칸)"
            )
            return

        couch_id = self.combo_couch_add.currentData()
        cdata = self.couches_map.get(couch_id)
        if cdata:
            slot = self.train_config.add_coach(cdata)
            if hasattr(self, 'inspector_train_part') and self.inspector_train_part:
                self.inspector_train_part.set_item_data(f"객차 #{slot.index}: {slot.get_name()}", cdata)
            self._update_train_stats()
            self._update_coach_layout_ui(preserve_row=len(self.train_config.coaches))

    def _remove_couch(self):
        row = self.lst_layout_couches.currentRow()
        if row == 0:
            QMessageBox.warning(self, "삭제 불가", "기관차는 삭제할 수 없습니다. 객차를 선택하세요.")
            return
        if 1 <= row <= len(self.train_config.coaches):
            c_idx = row - 1
            self.train_config.remove_coach(c_idx)
            self._update_train_stats()
            target_r = max(0, min(row - 1, len(self.train_config.coaches)))
            self._update_coach_layout_ui(preserve_row=target_r)
        else:
            QMessageBox.information(self, "안내", "삭제할 객차를 목록에서 먼저 선택하세요.")

    def _on_couch_list_selected(self, row):
        if 0 <= row < len(self.train_config.coaches):
            slot = self.train_config.coaches[row]
            if hasattr(self, 'inspector_train_part') and self.inspector_train_part:
                self.inspector_train_part.set_item_data(f"객차 #{slot.index}: {slot.get_name()}", slot.couch_data)

    def _update_train_stats(self):
        stats = self.train_config.calculate_stats()
        selected_r = self.lst_layout_couches.currentRow() if hasattr(self, 'lst_layout_couches') else 0

        if hasattr(self, 'coach_stat_dashboard') and self.coach_stat_dashboard:
            if selected_r <= 0:
                self.coach_stat_dashboard.set_locomotive_data(self.train_config)
            elif 1 <= selected_r <= len(self.train_config.coaches):
                slot = self.train_config.coaches[selected_r - 1]
                self.coach_stat_dashboard.set_coach_slot(slot)

        self.train_blueprint.update_blueprint(self.train_config, selected_index=selected_r)
        self._update_preview_ui()

    def _update_coach_layout_ui(self, preserve_row=None):
        if preserve_row is None:
            preserve_row = self.lst_layout_couches.currentRow()

        self.lst_layout_couches.blockSignals(True)
        self.lst_layout_couches.clear()

        # Item 0: Locomotive Car
        loco_name = self.train_config.locomotive.get("locomotiveName") if self.train_config.locomotive else "기관차 미선택"
        lt_names = [w.get("weaponName") or w.get("weaponId") for w in self.train_config.locomotive_turrets]
        lt_str = f"자체 포탑 {len(self.train_config.locomotive_turrets)}/2: " + (", ".join(lt_names) if lt_names else "없음")
        loco_def = self.train_config.locomotive.get("locomotiveDef", 10) if self.train_config.locomotive else 0
        loco_hp = self.train_config.locomotive.get("locomotiveHp", 1000) if self.train_config.locomotive else 0
        loco_shield = self.train_config.get_locomotive_shield()
        self.lst_layout_couches.addItem(f"🚂 [기관차] {loco_name} (Def:{loco_def:.0f}|🛡️{loco_shield:.0f}|HP:{loco_hp}) | {lt_str} | (승무원불가)")

        # Items 1..N: Coach Cars
        for slot in self.train_config.coaches:
            t_names = [w.get("weaponName") or w.get("weaponId") for w in slot.turrets]
            t_str = f"포탑 {len(slot.turrets)}/4: " + (", ".join(t_names) if t_names else "없음")
            c_name = slot.crew.get("crewName") if slot.crew else "승무원 미배치"
            chp = slot.couch_data.get("couchHp") if slot.couch_data else 500
            cshield = slot.get_total_coach_shield(generator=self.train_config.generator)
            syn = slot.get_synergy_power()
            cdef = slot.get_total_coach_def()
            self.lst_layout_couches.addItem(f"🚃 [{slot.index}번 칸] {slot.get_name()} (시너지:{syn:.1f}x|Def:{cdef:.1f}|🛡️{cshield:.0f}|HP:{chp}) | {t_str} | {c_name}")

        self.lst_layout_couches.blockSignals(False)

        target_row = preserve_row if (0 <= preserve_row < self.lst_layout_couches.count()) else 0
        self.lst_layout_couches.setCurrentRow(target_row)
        self._on_layout_coach_selected(target_row)

        self.train_blueprint.update_blueprint(self.train_config, selected_index=target_row)
        if hasattr(self, 'blueprint_tab2'):
            self.blueprint_tab2.update_blueprint(self.train_config, selected_index=target_row)

    def _on_layout_coach_selected(self, row):
        if row == 0:
            # Locomotive Selected
            loco_name = self.train_config.locomotive.get("locomotiveName") if self.train_config.locomotive else "기관차 미선택"
            loco_hp = self.train_config.locomotive.get("locomotiveHp", 1000) if self.train_config.locomotive else 0
            loco_def = self.train_config.locomotive.get("locomotiveDef", 10) if self.train_config.locomotive else 0
            loco_shield = self.train_config.get_locomotive_shield()
            self.lbl_selected_coach_info.setText(f"선택: 🚂 [기관차] {loco_name} (Def:{loco_def:.0f} | 🛡️보호막:{loco_shield:.0f} | 자체 포탑:{len(self.train_config.locomotive_turrets)}/2개)")

            self.lst_coach_turrets.clear()
            for idx, w in enumerate(self.train_config.locomotive_turrets):
                wname = w.get("weaponName") or w.get("weaponId")
                pwr = float(w.get("weaponPower") or 0)
                ltype = str(w.get("weaponLandType") or "L").strip().upper()
                self.lst_coach_turrets.addItem(f"🔫 기관차 포탑 #{idx+1}: {wname} [{ltype}] (위력: {pwr:.1f})")

            self.combo_coach_crew.setEnabled(False)
            self.combo_coach_crew.setCurrentIndex(0)

            if hasattr(self, 'box_crew_level'):
                self.box_crew_level.setEnabled(False)
                self.box_crew_level.setTitle("👨‍✈️ 승무원 레벨 & 스탯 배분 (※ 기관차 불가 · 승무원을 배치한 객차만 조절 가능)")

            if hasattr(self, 'coach_stat_dashboard'):
                self.coach_stat_dashboard.set_locomotive_data(self.train_config)

            self.train_blueprint.update_blueprint(self.train_config, selected_index=0)
            if hasattr(self, 'blueprint_tab2'):
                self.blueprint_tab2.update_blueprint(self.train_config, selected_index=0)

        elif 1 <= row <= len(self.train_config.coaches):
            # Coach Selected (slot index = row - 1)
            slot = self.train_config.coaches[row - 1]
            cname = slot.get_name()
            chp = slot.couch_data.get("couchHp") if slot.couch_data else 500
            cshield = slot.get_total_coach_shield(generator=self.train_config.generator)
            syn = slot.get_synergy_power()
            cdef = slot.get_total_coach_def()
            self.lbl_selected_coach_info.setText(f"선택: 🚃 [{slot.index}번 칸] {cname} (Def:{cdef:.1f} | 🛡️보호막:{cshield:.0f} | 시너지:{syn:.1f}x | HP:{chp})")

            self.lst_coach_turrets.clear()
            eff_crew = slot.get_effective_crew_stats()
            for idx, w in enumerate(slot.turrets):
                wname = w.get("weaponName") or w.get("weaponId")
                pwr = float(w.get("weaponPower") or 0)
                ltype = str(w.get("weaponLandType") or "L").strip().upper()

                if ltype == "L":
                    c_bonus = eff_crew["landpower"]
                elif ltype == "F":
                    c_bonus = eff_crew["flypower"]
                else:
                    c_bonus = max(eff_crew["landpower"], eff_crew["flypower"])

                tot_pwr = pwr + c_bonus
                self.lst_coach_turrets.addItem(f"🔫 객차 포탑 #{idx+1}: {wname} [{ltype}] (총 위력: {tot_pwr:.1f} = 기본:{pwr:.1f} + 승무원:{c_bonus:.1f})")

            self.combo_coach_crew.setEnabled(True)
            if slot.crew:
                cid = slot.crew.get("crewId")
                idx = self.combo_coach_crew.findData(cid)
                if idx >= 0:
                    self.combo_coach_crew.setCurrentIndex(idx)
                if hasattr(self, 'box_crew_level'):
                    self.box_crew_level.setEnabled(True)
                    cr_name = slot.crew.get("crewName") or slot.crew.get("crewId")
                    self.box_crew_level.setTitle(f"👨‍✈️ [{slot.index}번 {cr_name}] 레벨 & 스탯 포인트 배분")
                    self._sync_crew_level_inputs(slot)
            else:
                self.combo_coach_crew.setCurrentIndex(0)
                if hasattr(self, 'box_crew_level'):
                    self.box_crew_level.setEnabled(False)
                    self.box_crew_level.setTitle(f"👨‍✈️ [{slot.index}번 객차] 승무원 레벨 & 스탯 배분 (※ 승무원 미배치 · 승무원을 배치해야 조절 가능)")

            if hasattr(self, 'coach_stat_dashboard'):
                self.coach_stat_dashboard.set_coach_slot(slot)

            self.train_blueprint.update_blueprint(self.train_config, selected_index=row)
            if hasattr(self, 'blueprint_tab2'):
                self.blueprint_tab2.update_blueprint(self.train_config, selected_index=row)
        else:
            self.lbl_selected_coach_info.setText("선택된 열차 파츠가 없습니다.")
            self.lst_coach_turrets.clear()
            if hasattr(self, 'box_crew_level'):
                self.box_crew_level.setEnabled(False)
                self.box_crew_level.setTitle("👨‍✈️ 승무원 레벨 & 스탯 포인트 배분 (※ 승무원을 배치한 칸만 조절 가능 / 기관차 불가)")
            if hasattr(self, 'coach_stat_dashboard'):
                self.coach_stat_dashboard.set_coach_slot(None)

    def _sync_crew_level_inputs(self, slot):
        if not hasattr(self, 'spin_crew_level'):
            return
        self.spin_crew_level.blockSignals(True)
        self.spin_crew_point_rate.blockSignals(True)
        self.spin_crew_atk_pts.blockSignals(True)
        self.spin_crew_def_pts.blockSignals(True)
        self.spin_crew_prod_pts.blockSignals(True)

        self.spin_crew_level.setValue(slot.crew_level)
        self.spin_crew_point_rate.setValue(self.train_config.crew_point_rate)

        max_pts = slot.get_max_available_points()
        rem_pts = slot.get_remaining_points()
        used_pts = slot.get_used_points()

        self.spin_crew_atk_pts.setRange(0, 49)
        self.spin_crew_def_pts.setRange(0, 49)
        self.spin_crew_prod_pts.setRange(0, 49)

        self.spin_crew_atk_pts.setValue(slot.crew_atk_pts)
        self.spin_crew_def_pts.setValue(slot.crew_def_pts)
        self.spin_crew_prod_pts.setValue(slot.crew_prod_pts)

        self.lbl_crew_points_remaining.setText(f"남은 포인트: {rem_pts} / {max_pts} pt (사용:{used_pts}pt)")
        if rem_pts > 0:
            self.lbl_crew_points_remaining.setStyleSheet("font-weight: bold; color: #38bdf8;")
        elif rem_pts == 0:
            self.lbl_crew_points_remaining.setStyleSheet("font-weight: bold; color: #10b981;")
        else:
            self.lbl_crew_points_remaining.setStyleSheet("font-weight: bold; color: #ef4444;")

        self.spin_crew_level.blockSignals(False)
        self.spin_crew_point_rate.blockSignals(False)
        self.spin_crew_atk_pts.blockSignals(False)
        self.spin_crew_def_pts.blockSignals(False)
        self.spin_crew_prod_pts.blockSignals(False)

    def _adjust_crew_level(self, delta):
        row = self.lst_layout_couches.currentRow()
        if not (1 <= row <= len(self.train_config.coaches)):
            return
        slot = self.train_config.coaches[row - 1]
        cur = slot.crew_level
        if delta == "max":
            new_lvl = 50
        else:
            new_lvl = max(1, min(50, cur + int(delta)))
        self.spin_crew_level.setValue(new_lvl)

    def _adjust_crew_point(self, stat_name, delta):
        row = self.lst_layout_couches.currentRow()
        if not (1 <= row <= len(self.train_config.coaches)):
            return
        slot = self.train_config.coaches[row - 1]
        rem = slot.get_remaining_points()

        if delta > 0:
            if rem <= 0:
                self.lbl_crew_points_remaining.setText(f"⚠️ 남은 포인트가 없습니다! (먼저 레벨을 올리세요 / 현재 Lv.{slot.crew_level})")
                self.lbl_crew_points_remaining.setStyleSheet("font-weight: bold; color: #f59e0b;")
                return
            add_amt = min(delta, rem)
            if stat_name == "atk":
                slot.crew_atk_pts += add_amt
            elif stat_name == "def":
                slot.crew_def_pts += add_amt
            elif stat_name == "prod":
                slot.crew_prod_pts += add_amt
        elif delta < 0:
            sub_amt = abs(delta)
            if stat_name == "atk":
                slot.crew_atk_pts = max(0, slot.crew_atk_pts - sub_amt)
            elif stat_name == "def":
                slot.crew_def_pts = max(0, slot.crew_def_pts - sub_amt)
            elif stat_name == "prod":
                slot.crew_prod_pts = max(0, slot.crew_prod_pts - sub_amt)

        self._sync_crew_level_inputs(slot)
        self._update_coach_layout_ui(preserve_row=row)
        self._update_train_stats()

    def _on_crew_level_changed(self, val):
        row = self.lst_layout_couches.currentRow()
        if 1 <= row <= len(self.train_config.coaches):
            slot = self.train_config.coaches[row - 1]
            slot.set_crew_level(val)
            self._sync_crew_level_inputs(slot)
            self._update_coach_layout_ui(preserve_row=row)
            self._update_train_stats()

    def _on_crew_point_rate_changed(self, val):
        self.train_config.set_crew_point_rate(val)
        row = self.lst_layout_couches.currentRow()
        if 1 <= row <= len(self.train_config.coaches):
            slot = self.train_config.coaches[row - 1]
            self._sync_crew_level_inputs(slot)
        self._update_train_stats()

    def _on_crew_points_changed(self):
        row = self.lst_layout_couches.currentRow()
        if 1 <= row <= len(self.train_config.coaches):
            slot = self.train_config.coaches[row - 1]
            a = self.spin_crew_atk_pts.value()
            d = self.spin_crew_def_pts.value()
            p = self.spin_crew_prod_pts.value()
            slot.set_crew_points(a, d, p)
            self._sync_crew_level_inputs(slot)
            self._update_coach_layout_ui(preserve_row=row)
            self._update_train_stats()

    def _quick_distribute_crew_points(self, mode):
        row = self.lst_layout_couches.currentRow()
        if not (1 <= row <= len(self.train_config.coaches)):
            return
        slot = self.train_config.coaches[row - 1]
        max_pts = slot.get_max_available_points()
        if mode == "reset":
            slot.set_crew_points(0, 0, 0)
        elif mode == "atk":
            slot.set_crew_points(max_pts, 0, 0)
        elif mode == "def":
            slot.set_crew_points(0, max_pts, 0)
        elif mode == "even":
            each = max_pts // 3
            rem = max_pts % 3
            slot.set_crew_points(each + (1 if rem > 0 else 0), each + (1 if rem > 1 else 0), each)
        self._sync_crew_level_inputs(slot)
        self._update_coach_layout_ui(preserve_row=row)
        self._update_train_stats()

    def _equip_turret_to_selected_coach(self):
        row = self.lst_layout_couches.currentRow()
        wid = self.combo_turret_add.currentData()
        wdata = self.weapons_map.get(wid)
        if not wdata:
            return

        if row == 0:
            # Equip to Locomotive (max 2)
            if not self.train_config.locomotive:
                QMessageBox.warning(self, "기관차 미선택", "기관차를 먼저 선택하세요.")
                return
            if len(self.train_config.locomotive_turrets) >= 2:
                QMessageBox.warning(self, "포탑 개수 제한", "기관차에는 최대 2개의 자체 포탑만 배치할 수 있습니다!")
                return
            self.train_config.locomotive_turrets.append(wdata)
            self._update_coach_layout_ui(preserve_row=0)
            if hasattr(self, 'inspector_train_part') and self.inspector_train_part:
                self.inspector_train_part.set_item_data(wdata.get("weaponName") or wid, wdata)
            self._update_train_stats()
        elif 1 <= row <= len(self.train_config.coaches):
            # Equip to Coach (max 4)
            slot = self.train_config.coaches[row - 1]
            if len(slot.turrets) >= 4:
                QMessageBox.warning(self, "포탑 개수 제한", f"선택한 [{slot.index}번 칸] 객차에는 최대 4개의 포탑만 배치할 수 있습니다!")
                return
            slot.turrets.append(wdata)
            self._update_coach_layout_ui(preserve_row=row)
            if hasattr(self, 'inspector_train_part') and self.inspector_train_part:
                self.inspector_train_part.set_item_data(wdata.get("weaponName") or wid, wdata)
            self._update_train_stats()
        else:
            QMessageBox.information(self, "안내", "포탑을 장착할 기관차 또는 객차를 목록에서 먼저 선택하세요.")

    def _unequip_turret_from_selected_coach(self):
        row = self.lst_layout_couches.currentRow()
        t_row = self.lst_coach_turrets.currentRow()
        if row == 0:
            if 0 <= t_row < len(self.train_config.locomotive_turrets):
                self.train_config.locomotive_turrets.pop(t_row)
                self._update_coach_layout_ui(preserve_row=0)
                self._update_train_stats()
        elif 1 <= row <= len(self.train_config.coaches):
            slot = self.train_config.coaches[row - 1]
            if 0 <= t_row < len(slot.turrets):
                slot.turrets.pop(t_row)
                self._update_coach_layout_ui(preserve_row=row)
                self._update_train_stats()

    def _assign_crew_to_selected_coach(self):
        row = self.lst_layout_couches.currentRow()
        if row == 0:
            QMessageBox.warning(self, "승무원 배치 불가", "기관차에는 승무원을 배치할 수 없습니다. 객차를 선택하세요.")
            return
        if not (1 <= row <= len(self.train_config.coaches)):
            QMessageBox.information(self, "안내", "승무원을 배치할 객차를 목록에서 먼저 선택하세요.")
            return

        cid = self.combo_coach_crew.currentData()
        cdata = self.crews_map.get(cid)
        if not cdata:
            QMessageBox.warning(self, "안내", "배치할 승무원을 선택하세요.")
            return

        target_idx = row - 1

        # Check if the crew is already assigned to another coach
        for other_idx, other_slot in enumerate(self.train_config.coaches):
            if other_idx != target_idx and other_slot.crew and other_slot.crew.get("crewId") == cid:
                cname = cdata.get("crewName") or cid
                QMessageBox.warning(
                    self, "중복 배치 불가",
                    f"[{cname}] 승무원은 이미 [{other_slot.index}번 칸 객차]에 배치되어 있습니다!\n\n"
                    f"동일한 승무원은 열차 내 1개의 객차에만 배치할 수 있으며 중복 장착이 불가능합니다."
                )
                return

        slot = self.train_config.coaches[target_idx]
        slot.crew = cdata
        self._update_coach_layout_ui(preserve_row=row)
        if hasattr(self, 'inspector_train_part') and self.inspector_train_part:
            self.inspector_train_part.set_item_data(cdata.get("crewName") or cid, cdata)
        self._update_train_stats()

    def _unassign_crew_from_selected_coach(self):
        row = self.lst_layout_couches.currentRow()
        if not (1 <= row <= len(self.train_config.coaches)):
            QMessageBox.information(self, "안내", "승무원을 해제할 객차를 목록에서 먼저 선택하세요.")
            return

        slot = self.train_config.coaches[row - 1]
        slot.crew = None
        self._update_coach_layout_ui(preserve_row=row)
        self._update_train_stats()

    def _on_monster_selected(self, m_data):
        self.selected_monster_data = m_data
        if hasattr(self, 'inspector_monster_part') and self.inspector_monster_part:
            mname = m_data.get("monsterName") or m_data.get("monsterId")
            self.inspector_monster_part.set_item_data(f"몬스터: {mname}", m_data)

    def _on_battle_area_selected(self):
        ba_id = self.combo_battle_area.currentData()
        if not ba_id:
            return

        ba_record = self.battle_areas_map.get(ba_id)
        lvl_id = ba_record.get("battleLevelId") if ba_record else ba_id

        spawn_records = self.loader.get_sheet_data("SpawnData")
        self.enemy_config.clear()

        for sp in spawn_records:
            target_lvl = sp.get("levelId")
            if target_lvl and (target_lvl == lvl_id or target_lvl == ba_id):
                mid = sp.get("levelSpawnMonsterId")
                if mid and mid in self.monsters_map:
                    cur = self.enemy_config.monster_counts.get(mid, 0)
                    self.enemy_config.set_monster_count(mid, cur + 1)

        self._update_enemy_ui()

    def _add_selected_monster_to_army(self):
        selected_rows = self.monster_table.table.selectionModel().selectedRows()
        if not selected_rows or not self.selected_monster_data:
            QMessageBox.warning(
                self, "몬스터 미선택",
                "⚠️ 적 군단에 추가할 몬스터가 선택되지 않았습니다!\n\n위 몬스터 목록 테이블에서 추가하고 싶은 몬스터 행을 먼저 클릭하신 후 [적 추가 (+)] 버튼을 눌러주세요."
            )
            return

        mid = self.selected_monster_data.get("monsterId")
        if not mid:
            QMessageBox.warning(self, "오류", "선택한 몬스터의 ID 정보를 찾을 수 없습니다.")
            return

        count = self.spin_monster_count.value()
        cur = self.enemy_config.monster_counts.get(mid, 0)
        self.enemy_config.set_monster_count(mid, cur + count)
        self._update_enemy_ui()

    def _clear_enemy_army(self):
        self.enemy_config.clear()
        self._update_enemy_ui()

    def _update_enemy_ui(self):
        self.lst_enemies.clear()
        summary = self.enemy_config.get_summary(self.monsters_map)

        for mid, cnt in self.enemy_config.monster_counts.items():
            m_info = self.monsters_map.get(mid, {})
            mname = m_info.get("monsterName") or mid
            hp = m_info.get("monsterHp") or 0
            self.lst_enemies.addItem(f"👾 {mname} ({mid}) x {cnt}마리 (개당 HP: {hp})")

        tot_cnt = summary["total_count"]
        tot_hp = summary["total_hp"]
        tot_pwr = summary["total_power"]
        self.card_enemy_summary.set_value(tot_cnt, f"총 {tot_cnt} 마리 | HP: {tot_hp} | Atk: {tot_pwr}")

        self._update_preview_ui()

    # ----------------------------------------------------
    # TAB 4: BATTLE SIMULATION OVERVIEW & EXECUTION
    # ----------------------------------------------------
    def _build_preview_tab(self):
        layout = QVBoxLayout(self.tab_preview)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        cards_layout = QHBoxLayout()

        self.box_train_preview = QGroupBox("🚂 우리 트레인 요약 (독립 방어력)")
        t_layout = QVBoxLayout(self.box_train_preview)
        t_layout.setContentsMargins(6, 6, 6, 6)
        self.lbl_train_summary = QLabel("트레인을 구성해주세요.")
        self.lbl_train_summary.setStyleSheet("font-size: 11px; font-weight: bold; color: #10b981;")
        t_layout.addWidget(self.lbl_train_summary)
        cards_layout.addWidget(self.box_train_preview)

        lbl_vs = QLabel("VS")
        lbl_vs.setStyleSheet("font-size: 22px; font-weight: bold; color: #ef4444; margin: 10px;")
        cards_layout.addWidget(lbl_vs)

        self.box_enemy_preview = QGroupBox("👾 1:다 적 군단 요약")
        e_layout = QVBoxLayout(self.box_enemy_preview)
        e_layout.setContentsMargins(6, 6, 6, 6)
        self.lbl_enemy_summary = QLabel("적 몬스터를 선택해주세요.")
        self.lbl_enemy_summary.setStyleSheet("font-size: 11px; font-weight: bold; color: #ef4444;")
        e_layout.addWidget(self.lbl_enemy_summary)
        cards_layout.addWidget(self.box_enemy_preview)

        self.box_result_summary = QGroupBox("🏆 전투 시뮬레이션 최종 결과")
        r_layout = QVBoxLayout(self.box_result_summary)
        r_layout.setContentsMargins(6, 6, 6, 6)
        self.lbl_sim_result = QLabel("전투 미실행 (Ready 버튼을 누르세요)")
        self.lbl_sim_result.setStyleSheet("font-size: 11px; font-weight: bold; color: #f59e0b;")
        r_layout.addWidget(self.lbl_sim_result)
        cards_layout.addWidget(self.box_result_summary)

        layout.addLayout(cards_layout)

        canvas_box = QGroupBox("전투 시뮬레이션 2D 뷰포트 (독립 HP & 독립 방어력 피격 시각화)")
        canvas_layout = QVBoxLayout(canvas_box)
        canvas_layout.setContentsMargins(4, 4, 4, 4)

        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor("#0b0f19")))
        self.view = QGraphicsView(self.scene)
        self.view.setFixedHeight(190)
        canvas_layout.addWidget(self.view)

        layout.addWidget(canvas_box)

        btn_start_sim = QPushButton("⚡ 전투 시뮬레이션 실행 (Run Engine & Log Generation)")
        btn_start_sim.setStyleSheet("font-size: 13px; padding: 6px;")
        btn_start_sim.setObjectName("btn-success")
        btn_start_sim.clicked.connect(self._run_simulation_engine)
        layout.addWidget(btn_start_sim)

    def _update_preview_ui(self):
        if not hasattr(self, 'lbl_train_summary') or not self.lbl_train_summary:
            return

        stats = self.train_config.calculate_stats()
        turret_sum = self.turret_config.calculate_dps_summary(self.train_config)
        loco_name = self.train_config.locomotive.get("locomotiveName") if self.train_config.locomotive else "없음"
        loco_hp = (self.train_config.locomotive.get("locomotiveHp") or 0) if self.train_config.locomotive else 0

        loco_def = stats["locomotive_def"]
        c_def_list = stats["coaches_def_list"]
        c_def_str = ", ".join(f"#{i+1}:{d:.1f}" for i, d in enumerate(c_def_list)) if c_def_list else "없음"

        t_text = (
            f"• 기관차: {loco_name} (HP: {loco_hp} | Def: {loco_def:.0f})\n"
            f"• 객차 수: {stats['current_couches']} / {stats['max_couches']} 칸 (객차별 독립 Def: {c_def_str})\n"
            f"• 보호막: {stats['total_shield']:.0f} | 총 엔진 출력: {stats['horsepower']:.0f}\n"
            f"• 장착 포탑 수: {turret_sum['equipped_count']} / {turret_sum['max_slots']} 개 (기관차 자체 2개, 객차당 최대 4개)\n"
            f"• L속성 대지위력: +{stats['crew_landpower']:.1f} | F속성 대공위력: +{stats['crew_flypower']:.1f}"
        )
        self.lbl_train_summary.setText(t_text)

        if hasattr(self, 'lbl_enemy_summary') and self.lbl_enemy_summary:
            e_sum = self.enemy_config.get_summary(self.monsters_map)
            e_text = (
                f"• 적 몬스터 총 수량: {e_sum['total_count']} 마리\n"
                f"• 몬스터 종류: {e_sum['monster_types_count']} 종\n"
                f"• 총 적 체력 합계: {e_sum['total_hp']}\n"
                f"• 총 적 공격력 합계: {e_sum['total_power']}"
            )
            self.lbl_enemy_summary.setText(e_text)

        self.scene.clear()

        x_start = 40
        y_center = 85

        loco_rect = QGraphicsRectItem(x_start, y_center - 25, 80, 50)
        loco_rect.setBrush(QBrush(QColor("#4f46e5")))
        loco_rect.setPen(QPen(QColor("#818cf8"), 1.5))
        self.scene.addItem(loco_rect)

        loco_txt = self.scene.addText(f"🚂기관차\nDef:{loco_def:.0f}")
        loco_txt.setDefaultTextColor(QColor("white"))
        loco_txt.setPos(x_start + 2, y_center - 22)

        for t_idx, w in enumerate(self.train_config.locomotive_turrets):
            tx = x_start + 8 + (t_idx * 22)
            ty = y_center - 38
            t_rect = QGraphicsRectItem(tx, ty, 16, 12)
            ltype = str(w.get("weaponLandType") or "L").strip().upper()
            color_hex = "#f59e0b" if ltype == "L" else "#06b6d4"
            t_rect.setBrush(QBrush(QColor(color_hex)))
            t_rect.setPen(QPen(QColor("#ffffff"), 1))
            self.scene.addItem(t_rect)

        couch_x = x_start + 90
        for idx, slot in enumerate(self.train_config.coaches):
            chp = slot.couch_data.get("couchHp") if slot.couch_data else 500
            cdef = slot.get_total_coach_def()
            c_rect = QGraphicsRectItem(couch_x, y_center - 20, 85, 40)
            c_rect.setBrush(QBrush(QColor("#1e293b")))
            c_rect.setPen(QPen(QColor("#10b981"), 1.5))
            self.scene.addItem(c_rect)

            c_txt = self.scene.addText(f"객차#{slot.index}\nDef:{cdef:.1f}")
            c_txt.setDefaultTextColor(QColor("#f8fafc"))
            c_txt.setPos(couch_x + 4, y_center - 18)

            for t_idx, w in enumerate(slot.turrets):
                tx = couch_x + 6 + (t_idx * 18)
                ty = y_center - 34
                t_rect = QGraphicsRectItem(tx, ty, 14, 12)
                ltype = str(w.get("weaponLandType") or "L").strip().upper()
                color_hex = "#f59e0b" if ltype == "L" else "#06b6d4"
                t_rect.setBrush(QBrush(QColor(color_hex)))
                t_rect.setPen(QPen(QColor("#ffffff"), 1))
                self.scene.addItem(t_rect)

            couch_x += 92

        enemy_x_start = 750
        enemy_y_start = 20
        col_cnt = 0
        row_cnt = 0

        for mid, count in self.enemy_config.monster_counts.items():
            for _ in range(count):
                ex = enemy_x_start + (col_cnt * 35)
                ey = enemy_y_start + (row_cnt * 35)

                e_rect = QGraphicsRectItem(ex, ey, 25, 25)
                e_rect.setBrush(QBrush(QColor("#dc2626")))
                e_rect.setPen(QPen(QColor("#f87171"), 1))
                self.scene.addItem(e_rect)

                col_cnt += 1
                if col_cnt >= 8:
                    col_cnt = 0
                    row_cnt += 1

    def _run_simulation_engine(self):
        if not self.train_config.coaches and not self.train_config.locomotive:
            QMessageBox.warning(self, "전투 실행 불가", "열차(기관차 및 객차)를 먼저 구성하세요.")
            return

        if not self.enemy_config.monster_counts:
            QMessageBox.warning(self, "전투 실행 불가", "전투 상대 적 몬스터를 1마리 이상 선택하세요.")
            return

        self.last_engine = BattleSimulationEngine(self.train_config, self.enemy_config, self.monsters_map)
        self.last_summary = self.last_engine.run_full_simulation()

        res_str = self.last_summary["result"]
        dur = self.last_summary["duration"]
        dmg_dealt = self.last_summary["total_damage_dealt"]
        kills = self.last_summary["total_kills"]
        logs_cnt = self.last_summary["log_count"]

        cars_status_lines = []
        for car in self.last_summary["cars"]:
            status_text = "💥 파괴됨" if car["is_destroyed"] else f"HP: {car['hp_left']}/{car['max_hp']}"
            cars_status_lines.append(f"  • {car['name']}: {status_text}")
        cars_str = "\n".join(cars_status_lines)

        if hasattr(self, 'lbl_sim_result') and self.lbl_sim_result:
            self.lbl_sim_result.setText(r_text)
            self.lbl_sim_result.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color_str};")

        self._populate_combat_log_sheet()

        QMessageBox.information(
            self, "전투 시뮬레이션 완료",
            f"전투가 종료되었습니다!\n\n결과: {res_str}\n소요 시간: {dur}초\n\n칸별 생존 상태:\n{cars_str}\n\n'2. 전투 로그 시트' 탭에서 상세 기록을 확인하세요."
        )
        self.tabs.setCurrentIndex(1)

    # ----------------------------------------------------
    # TAB 5: COMBAT LOG SHEET & METADATA REPORT
    # ----------------------------------------------------
    def _build_log_sheet_tab(self):
        layout = QVBoxLayout(self.tab_log_sheet)
        layout.setContentsMargins(4, 4, 4, 4)

        box_meta = QGroupBox("📋 전투 시뮬레이션 설정 및 결과 메타데이터 요약")
        box_meta.setStyleSheet("font-weight: bold; color: #818cf8;")
        meta_layout = QVBoxLayout(box_meta)
        meta_layout.setContentsMargins(6, 6, 6, 6)

        self.lbl_log_meta_info = QLabel("전투 시뮬레이션을 실행하면 이곳에 열차 구성, 적 구성 및 결과 요약 메타데이터가 기록됩니다.")
        self.lbl_log_meta_info.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: normal;")
        meta_layout.addWidget(self.lbl_log_meta_info)

        top_bar = QHBoxLayout()
        btn_copy_meta = QPushButton("📋 요약 텍스트 클립보드 복사")
        btn_copy_meta.clicked.connect(self._copy_log_meta_to_clipboard)
        top_bar.addWidget(btn_copy_meta)

        top_bar.addStretch()

        btn_export_excel = QPushButton("📊 엑셀 Excel 저장 (.xlsx - 시트 2개 분리)")
        btn_export_excel.setObjectName("btn-success")
        btn_export_excel.clicked.connect(self._export_log_excel)
        top_bar.addWidget(btn_export_excel)

        btn_export_csv = QPushButton("📄 CSV 다중 저장 (.csv - 파일 2개 분리)")
        btn_export_csv.setObjectName("btn-accent")
        btn_export_csv.clicked.connect(self._export_log_csv)
        top_bar.addWidget(btn_export_csv)

        meta_layout.addLayout(top_bar)
        layout.addWidget(box_meta)

        self.log_table = DataTableWidget()
        cols = ["시간(sec)", "이벤트", "공격자/주체", "피해자/대상", "피해량", "남은 HP", "상세 내용"]
        self.log_table.set_data(cols, [])
        layout.addWidget(self.log_table, stretch=1)

    def _copy_log_meta_to_clipboard(self):
        text = self.lbl_log_meta_info.text()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "복사 완료", "전투 시뮬레이션 설정 및 결과 요약 텍스트가 클립보드에 복사되었습니다.")

    def _populate_combat_log_sheet(self):
        if not self.last_engine:
            return

        meta_lines = []
        if self.last_summary:
            meta_lines.append(f"• 전투 결과: {self.last_summary['result']} | 소요 시간: {self.last_summary['duration']}초 | 가한 총 피해량: {self.last_summary['total_damage_dealt']} | 처치 몬스터: {self.last_summary['total_kills']}마리")
        
        meta_lines.append("\n[1. 트레인 구성 정보 (Train Setup)]")
        for line in self.train_config.get_config_details():
            meta_lines.append("  " + line)

        meta_lines.append("\n[2. 적 군단 구성 정보 (Enemy Army Setup)]")
        for line in self.enemy_config.get_config_details(self.monsters_map):
            meta_lines.append("  " + line)

        self.lbl_log_meta_info.setText("\n".join(meta_lines))

        cols = ["시간(sec)", "이벤트", "공격자/주체", "피해자/대상", "피해량", "남은 HP", "상세 내용"]
        records = []
        for entry in self.last_engine.combat_logs:
            records.append({
                "시간(sec)": entry["time"],
                "이벤트": entry["event_type"],
                "공격자/주체": entry["attacker"],
                "피해자/대상": entry["target"],
                "피해량": entry["damage"],
                "남은 HP": entry["target_hp"],
                "상세 내용": entry["details"]
            })
        self.log_table.set_data(cols, records)

    def _export_log_excel(self):
        if not self.last_engine or not self.last_engine.combat_logs:
            QMessageBox.warning(self, "저장 불가", "저장할 전투 로그 데이터가 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "전투 로그 엑셀(2개 시트) 저장", "combat_log_result.xlsx", "Excel Files (*.xlsx)")
        if file_path:
            try:
                import openpyxl

                wb = openpyxl.Workbook()

                # SHEET 1: 전투로그데이터 (Combat Log Data)
                ws_log = wb.active
                ws_log.title = "전투로그데이터"
                cols = ["시간(sec)", "이벤트", "공격자/주체", "피해자/대상", "피해량", "남은 HP", "상세 내용"]
                ws_log.append(cols)

                for entry in self.last_engine.combat_logs:
                    ws_log.append([
                        entry["time"],
                        entry["event_type"],
                        entry["attacker"],
                        entry["target"],
                        entry["damage"],
                        entry["target_hp"],
                        entry["details"]
                    ])

                # SHEET 2: 트레인및적구성정보 (Configuration Info)
                ws_cfg = wb.create_sheet(title="트레인및적구성정보")
                ws_cfg.append(["구분", "항목", "상세 내용 및 수치"])

                if self.last_summary:
                    ws_cfg.append(["시뮬레이션결과", "전투 결과", self.last_summary["result"]])
                    ws_cfg.append(["시뮬레이션결과", "소요 시간", f"{self.last_summary['duration']} 초"])
                    ws_cfg.append(["시뮬레이션결과", "가한 총 피해량", self.last_summary["total_damage_dealt"]])
                    ws_cfg.append(["시뮬레이션결과", "처치 몬스터 수", f"{self.last_summary['total_kills']} 마리"])
                    ws_cfg.append(["시뮬레이션결과", "총 이벤트 로그 수", f"{self.last_summary['log_count']} 건"])

                ws_cfg.append([])
                ws_cfg.append(["[1. 트레인 구성 정보 (Train Configuration)]"])
                for line in self.train_config.get_config_details():
                    ws_cfg.append(["트레인 구성", line])

                ws_cfg.append([])
                ws_cfg.append(["[2. 적 군단 구성 정보 (Enemy Army Configuration)]"])
                for line in self.enemy_config.get_config_details(self.monsters_map):
                    ws_cfg.append(["적 군단 구성", line])

                wb.save(file_path)
                QMessageBox.information(
                    self, "엑셀 저장 완료",
                    f"2개의 시트로 분리된 엑셀 파일이 성공적으로 저장되었습니다!\n\n• 시트1: 전투로그데이터\n• 시트2: 트레인및적구성정보\n\n저장 경로:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "저장 오류", f"엑셀 파일 저장 중 오류가 발생했습니다: {e}")

    def _export_log_csv(self):
        if not self.last_engine or not self.last_engine.combat_logs:
            QMessageBox.warning(self, "저장 불가", "저장할 전투 로그 데이터가 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "전투 로그 CSV 저장", "combat_log_result.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                base, ext = os.path.splitext(file_path)
                path_log = f"{base}_전투로그.csv"
                path_cfg = f"{base}_구성정보.csv"

                # 1. Export Clean Log Events Table CSV
                with open(path_log, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["시간(sec)", "이벤트", "공격자/주체", "피해자/대상", "피해량", "남은 HP", "상세 내용"])
                    for entry in self.last_engine.combat_logs:
                        writer.writerow([
                            entry["time"],
                            entry["event_type"],
                            entry["attacker"],
                            entry["target"],
                            entry["damage"],
                            entry["target_hp"],
                            entry["details"]
                        ])

                # 2. Export Configuration Info CSV
                with open(path_cfg, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["# =============================================================================="])
                    writer.writerow(["# SIECLETRAIN BATTLE SIMULATION LOG & CONFIGURATION REPORT"])
                    writer.writerow(["# =============================================================================="])
                    if self.last_summary:
                        writer.writerow(["# 전투 결과", self.last_summary["result"]])
                        writer.writerow(["# 소요 시간", f"{self.last_summary['duration']} 초"])
                        writer.writerow(["# 가한 총 피해량", self.last_summary["total_damage_dealt"]])
                        writer.writerow(["# 처치 몬스터 수", f"{self.last_summary['total_kills']} 마리"])
                        writer.writerow(["# 총 이벤트 로그 수", f"{self.last_summary['log_count']} 건"])
                    writer.writerow(["# ------------------------------------------------------------------------------"])
                    writer.writerow(["# [1. 트레인 구성 정보 (Train Configuration)]"])
                    for line in self.train_config.get_config_details():
                        writer.writerow(["# " + line])
                    writer.writerow(["# ------------------------------------------------------------------------------"])
                    writer.writerow(["# [2. 적 군단 구성 정보 (Enemy Army Configuration)]"])
                    for line in self.enemy_config.get_config_details(self.monsters_map):
                        writer.writerow(["# " + line])

                QMessageBox.information(
                    self, "CSV 다중 저장 완료",
                    f"요청하신 2개의 CSV 파일로 분리 저장되었습니다!\n\n1. 전투 로그 전용 CSV:\n   {path_log}\n\n2. 트레인/적 구성 정보 전용 CSV:\n   {path_cfg}"
                )
            except Exception as e:
                QMessageBox.critical(self, "저장 오류", f"CSV 파일 저장 중 오류가 발생했습니다: {e}")

    # ----------------------------------------------------
    # TAB 6: DATA INSPECTOR
    # ----------------------------------------------------
    def _build_inspector_tab(self):
        self.inspector_tab_layout = QVBoxLayout(self.tab_inspector)
        self.inspector_tab_layout.setContentsMargins(4, 4, 4, 4)
        self._rebuild_inspector_tab()

    def _rebuild_inspector_tab(self):
        while self.inspector_tab_layout.count():
            item = self.inspector_tab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        inspector_tabs = QTabWidget()
        self.inspector_tab_layout.addWidget(inspector_tabs)

        for sname in self.loader.data.keys():
            tab_item = QWidget()
            t_layout = QVBoxLayout(tab_item)
            t_layout.setContentsMargins(4, 4, 4, 4)

            dt_widget = DataTableWidget()
            cols = self.loader.get_sheet_columns(sname)
            recs = self.loader.get_sheet_data(sname)
            dt_widget.set_data(cols, recs)

            t_layout.addWidget(dt_widget)
            inspector_tabs.addTab(tab_item, f"{sname} ({len(recs)}건)")

    # ----------------------------------------------------
    # TAB 4: CREW LEVEL-UP RANDOM GROWTH SIMULATOR
    # ----------------------------------------------------
    def _build_crew_sim_tab(self):
        tab_layout = QHBoxLayout(self.tab_crew_sim)
        tab_layout.setContentsMargins(8, 8, 8, 8)
        tab_layout.setSpacing(8)

        self.last_crew_sim_result = None

        # ----------------------------------------------------
        # LEFT PANEL: Parameters & Controls (Width: 380px)
        # ----------------------------------------------------
        left_panel = QWidget()
        left_panel.setFixedWidth(380)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # 1. Crew Selector Group
        box_crew_select = QGroupBox("👨‍✈️ 1. 시뮬레이션 대상 승무원 선택")
        c_layout = QVBoxLayout(box_crew_select)
        c_layout.setContentsMargins(8, 8, 8, 8)
        c_layout.setSpacing(4)

        self.combo_sim_crew = QComboBox()
        self.combo_sim_crew.currentIndexChanged.connect(self._on_sim_crew_selected)
        c_layout.addWidget(self.combo_sim_crew)

        self.lbl_sim_crew_info = QLabel("승무원을 선택하세요.")
        self.lbl_sim_crew_info.setStyleSheet("font-size: 11px; color: #cbd5e1; background: #0f172a; padding: 6px; border-radius: 4px;")
        c_layout.addWidget(self.lbl_sim_crew_info)
        left_layout.addWidget(box_crew_select)

        # 2. Probability Weights Group (Primary Stat + Auto Sub-Stat Formula)
        box_prob = QGroupBox("🎯 2. 주스탯(유형별) 및 레벨업 성장 확률 설정")
        p_layout = QVBoxLayout(box_prob)
        p_layout.setContentsMargins(8, 8, 8, 8)
        p_layout.setSpacing(5)

        self.lbl_sim_type_badge = QLabel("🎯 주스탯: ⚔️ 공격력 (유형: 전투형)")
        self.lbl_sim_type_badge.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 11.5px; background: #0f172a; padding: 4px; border-radius: 4px;")
        p_layout.addWidget(self.lbl_sim_type_badge)

        # Primary Stat Probability Input
        row_main_prob = QHBoxLayout()
        self.lbl_main_stat_name = QLabel("⭐ 주스탯 확률 설정:")
        self.lbl_main_stat_name.setStyleSheet("font-weight: bold; color: #f59e0b;")
        row_main_prob.addWidget(self.lbl_main_stat_name)

        self.spin_sim_p_main = QDoubleSpinBox()
        self.spin_sim_p_main.setRange(0.0, 100.0)
        self.spin_sim_p_main.setValue(50.0)
        self.spin_sim_p_main.setSuffix(" %")
        self.spin_sim_p_main.setSingleStep(5.0)
        self.spin_sim_p_main.valueChanged.connect(self._on_sim_main_prob_changed)
        row_main_prob.addWidget(self.spin_sim_p_main)
        p_layout.addLayout(row_main_prob)

        # Quick Preset Buttons for Primary Stat
        preset_box = QHBoxLayout()
        preset_box.setSpacing(2)
        for pct_v in [40, 50, 60, 70, 80, 100]:
            btn_pct = QPushButton(f"{pct_v}%")
            btn_pct.setStyleSheet("font-size: 10px; padding: 2px 4px;")
            btn_pct.clicked.connect(lambda _, v=pct_v: self.spin_sim_p_main.setValue(float(v)))
            preset_box.addWidget(btn_pct)
        p_layout.addLayout(preset_box)

        # Calculated Stat Probabilities Display (Read-Only / Synchronized)
        box_stat_calc = QFrame()
        box_stat_calc.setStyleSheet("background: #0f172a; border-radius: 4px; padding: 4px;")
        calc_layout = QGridLayout(box_stat_calc)
        calc_layout.setContentsMargins(4, 4, 4, 4)
        calc_layout.setSpacing(4)

        self.lbl_prob_atk_tag = QLabel("⚔️ 공격력:")
        self.lbl_prob_atk_val = QLabel("50.0% (⭐주스탯)")
        self.lbl_prob_atk_val.setStyleSheet("font-weight: bold; color: #f59e0b;")
        calc_layout.addWidget(self.lbl_prob_atk_tag, 0, 0)
        calc_layout.addWidget(self.lbl_prob_atk_val, 0, 1)

        self.lbl_prob_def_tag = QLabel("🛡️ 방어력:")
        self.lbl_prob_def_val = QLabel("25.0% (보조: (100-50)/2)")
        self.lbl_prob_def_val.setStyleSheet("font-weight: bold; color: #38bdf8;")
        calc_layout.addWidget(self.lbl_prob_def_tag, 1, 0)
        calc_layout.addWidget(self.lbl_prob_def_val, 1, 1)

        self.lbl_prob_prod_tag = QLabel("🏭 생산/공업:")
        self.lbl_prob_prod_val = QLabel("25.0% (보조: (100-50)/2)")
        self.lbl_prob_prod_val.setStyleSheet("font-weight: bold; color: #10b981;")
        calc_layout.addWidget(self.lbl_prob_prod_tag, 2, 0)
        calc_layout.addWidget(self.lbl_prob_prod_val, 2, 1)

        p_layout.addWidget(box_stat_calc)

        # Formula Rule Help text
        lbl_formula_hint = QLabel("💡 규칙: 나머지 2개 보조스탯 확률 = (100% - 주스탯%) ÷ 2")
        lbl_formula_hint.setStyleSheet("color: #94a3b8; font-size: 10.5px;")
        p_layout.addWidget(lbl_formula_hint)

        self.lbl_sim_prob_total = QLabel("확률 합계: 100.0% (항상 100% 자동 유지)")
        self.lbl_sim_prob_total.setStyleSheet("font-weight: bold; color: #10b981; font-size: 11px;")
        p_layout.addWidget(self.lbl_sim_prob_total)

        left_layout.addWidget(box_prob)

        # 3. Simulation Parameters Group
        box_params = QGroupBox("⚙️ 3. 시뮬레이션 파라미터")
        param_layout = QVBoxLayout(box_params)
        param_layout.setContentsMargins(8, 8, 8, 8)
        param_layout.setSpacing(4)

        row_lvl = QHBoxLayout()
        row_lvl.addWidget(QLabel("목표 레벨 (1~50):"))
        self.spin_sim_target_lvl = QSpinBox()
        self.spin_sim_target_lvl.setRange(2, 50)
        self.spin_sim_target_lvl.setValue(50)
        row_lvl.addWidget(self.spin_sim_target_lvl)
        self.lbl_sim_rolls_count = QLabel("(= 49회 성장)")
        self.lbl_sim_rolls_count.setStyleSheet("color: #94a3b8; font-size: 11px;")
        row_lvl.addWidget(self.lbl_sim_rolls_count)
        param_layout.addLayout(row_lvl)

        self.spin_sim_target_lvl.valueChanged.connect(
            lambda v: self.lbl_sim_rolls_count.setText(f"(= {v - 1}회 성장)")
        )

        row_rate = QHBoxLayout()
        row_rate.addWidget(QLabel("1pt당 스탯 증가율:"))
        self.spin_sim_rate = QDoubleSpinBox()
        self.spin_sim_rate.setRange(0.1, 100.0)
        self.spin_sim_rate.setValue(1.0)
        self.spin_sim_rate.setSuffix(" %")
        self.spin_sim_rate.setSingleStep(0.5)
        row_rate.addWidget(self.spin_sim_rate)
        param_layout.addLayout(row_rate)

        row_trials = QHBoxLayout()
        row_trials.addWidget(QLabel("시뮬레이션 반복 횟수:"))
        self.spin_sim_trials = QSpinBox()
        self.spin_sim_trials.setRange(1, 100000)
        self.spin_sim_trials.setValue(1000)
        self.spin_sim_trials.setSingleStep(100)
        row_trials.addWidget(self.spin_sim_trials)
        param_layout.addLayout(row_trials)

        trial_btn_box = QHBoxLayout()
        trial_btn_box.setSpacing(2)
        for t_cnt in [1, 100, 1000, 10000]:
            btn_t = QPushButton(f"{t_cnt:,}회")
            btn_t.clicked.connect(lambda _, c=t_cnt: self.spin_sim_trials.setValue(c))
            trial_btn_box.addWidget(btn_t)
        param_layout.addLayout(trial_btn_box)

        left_layout.addWidget(box_params)

        # 4. Action Buttons
        btn_run = QPushButton("🎲 랜덤 성장 시뮬레이션 실행 (Run)")
        btn_run.setObjectName("btn-success")
        btn_run.setStyleSheet("font-size: 13px; font-weight: bold; padding: 8px; background-color: #10b981; color: white; border-radius: 6px;")
        btn_run.clicked.connect(self._run_crew_growth_simulation)
        left_layout.addWidget(btn_run)

        btn_apply = QPushButton("🎯 시뮬레이션 결과 워크숍 적용 (동일 승무원 일괄 동기화)")
        btn_apply.setStyleSheet("font-size: 11px; font-weight: bold; padding: 6px; background-color: #6366f1; color: white; border-radius: 4px;")
        btn_apply.clicked.connect(self._apply_sim_result_to_workshop)
        left_layout.addWidget(btn_apply)

        left_layout.addStretch()
        tab_layout.addWidget(left_panel)

        # ----------------------------------------------------
        # RIGHT PANEL: Result Dashboard & Analytics Table
        # ----------------------------------------------------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        # Top KPI Cards Row
        kpi_row = QHBoxLayout()
        self.card_sim_atk = StatCard("⚔️ 공격력 포인트 기대값", "시뮬레이션 대기 중", "#f59e0b")
        self.card_sim_def = StatCard("🛡️ 방어력 포인트 기대값", "시뮬레이션 대기 중", "#3b82f6")
        self.card_sim_prod = StatCard("🏭 생산/공업 포인트 기대값", "시뮬레이션 대기 중", "#10b981")
        kpi_row.addWidget(self.card_sim_atk)
        kpi_row.addWidget(self.card_sim_def)
        kpi_row.addWidget(self.card_sim_prod)
        right_layout.addLayout(kpi_row)

        # Expected Final Stats Table
        lbl_tbl = QLabel("📊 승무원 레벨업 최종 스탯 기대값 및 최소/최대 범위 분석")
        lbl_tbl.setStyleSheet("font-weight: bold; color: #a7f3d0; font-size: 12px; margin-top: 4px;")
        right_layout.addWidget(lbl_tbl)

        self.tbl_sim_stats = QTableWidget()
        self.tbl_sim_stats.setFixedHeight(160)
        self.tbl_sim_stats.setColumnCount(7)
        self.tbl_sim_stats.setHorizontalHeaderLabels([
            "스탯 항목", "기본 수치(Base)", "평균 획득 포인트", "평균 배율(Mult)", "평균 최종 스탯", "최저 결과(Min)", "최고 결과(Max)"
        ])
        self.tbl_sim_stats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_sim_stats.verticalHeader().setVisible(False)
        self.tbl_sim_stats.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_sim_stats.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        right_layout.addWidget(self.tbl_sim_stats)

        # Detailed Analytics & Log Sub-Tabs
        sub_tabs = QTabWidget()

        # Sub-Tab 1: Detailed Statistics & Percentiles
        tab_sub_stats = QWidget()
        sub_s_layout = QVBoxLayout(tab_sub_stats)
        sub_s_layout.setContentsMargins(6, 6, 6, 6)
        self.txt_sim_analytics = QTextEdit()
        self.txt_sim_analytics.setReadOnly(True)
        self.txt_sim_analytics.setStyleSheet("font-family: 'Consolas', 'Malgun Gothic', monospace; font-size: 11.5px; background-color: #0b0f19; color: #e2e8f0;")
        self.txt_sim_analytics.setText("시뮬레이션을 실행하면 확률 분포, 표준편차, 상위/하위 백분위 통계가 여기에 출력됩니다.")
        sub_s_layout.addWidget(self.txt_sim_analytics)
        sub_tabs.addTab(tab_sub_stats, "📈 상세 통계 및 백분위 분포 분석 (Percentiles)")

        # Sub-Tab 2: Step-by-Step Dice Rolls / Trials List
        tab_sub_rolls = QWidget()
        sub_r_layout = QVBoxLayout(tab_sub_rolls)
        sub_r_layout.setContentsMargins(6, 6, 6, 6)
        self.txt_sim_log = QTextEdit()
        self.txt_sim_log.setReadOnly(True)
        self.txt_sim_log.setStyleSheet("font-family: 'Consolas', 'Malgun Gothic', monospace; font-size: 11.5px; background-color: #0b0f19; color: #e2e8f0;")
        self.txt_sim_log.setText("단일 회차(1회) 실행 시 각 레벨별 주사위 판정 상세 로그가 출력되며,\n다회차 실행 시 회차별 획득 결과 목록이 출력됩니다.")
        sub_r_layout.addWidget(self.txt_sim_log)
        sub_tabs.addTab(tab_sub_rolls, "📜 레벨업 주사위 판정 로그 / 회차별 결과")

        right_layout.addWidget(sub_tabs, stretch=1)
        tab_layout.addWidget(right_panel, stretch=1)

    def _on_sim_crew_selected(self):
        if not hasattr(self, 'combo_sim_crew') or not hasattr(self, 'spin_sim_p_main'):
            return
        cid = self.combo_sim_crew.currentData()
        cdata = self.crews_map.get(cid)
        if not cdata:
            return

        cname = cdata.get("crewName") or cid
        ctype = str(cdata.get("crewType") or "일반").strip()
        land = cdata.get("crewLandpower", 0)
        fly = cdata.get("crewFlypower", 0)
        cdef = cdata.get("crewDef", 0)
        prod = cdata.get("crewProduct", 0.0)
        ind = cdata.get("crewIndustry", 0.0)

        info_text = (
            f"• 승무원: {cname} (ID: {cid})\n"
            f"• 유형: {ctype}\n"
            f"• 기본 스탯: 대지위력:{land} | 대공위력:{fly} | Def:{cdef} | 생산:{prod:.1f} | 공업:{ind:.1f}"
        )
        self.lbl_sim_crew_info.setText(info_text)

        # Detect Primary Stat (주스탯) based on crewType
        cid_str = str(cid or "")
        if "전투" in ctype or "공격" in ctype or "Batt" in cid_str:
            self.sim_primary_stat = "atk"
            self.lbl_sim_type_badge.setText("🎯 주스탯: ⚔️ 공격력 (유형: 전투형)")
            self.lbl_sim_type_badge.setStyleSheet("font-weight: bold; color: #f59e0b; font-size: 11.5px; background: #0f172a; padding: 4px; border-radius: 4px;")
            self.lbl_main_stat_name.setText("⭐ 공격력(주스탯) 확률:")
        elif "방어" in ctype or "Def" in cid_str:
            self.sim_primary_stat = "def"
            self.lbl_sim_type_badge.setText("🎯 주스탯: 🛡️ 방어력 (유형: 방어형)")
            self.lbl_sim_type_badge.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 11.5px; background: #0f172a; padding: 4px; border-radius: 4px;")
            self.lbl_main_stat_name.setText("⭐ 방어력(주스탯) 확률:")
        elif "생산" in ctype or "공업" in ctype or "Prod" in cid_str:
            self.sim_primary_stat = "prod"
            self.lbl_sim_type_badge.setText("🎯 주스탯: 🏭 생산/공업 (유형: 생산형)")
            self.lbl_sim_type_badge.setStyleSheet("font-weight: bold; color: #10b981; font-size: 11.5px; background: #0f172a; padding: 4px; border-radius: 4px;")
            self.lbl_main_stat_name.setText("⭐ 생산/공업(주스탯) 확률:")
        else:
            self.sim_primary_stat = "even"
            self.lbl_sim_type_badge.setText("🎯 밸런스/균등형 (기타)")
            self.lbl_sim_type_badge.setStyleSheet("font-weight: bold; color: #a855f7; font-size: 11.5px; background: #0f172a; padding: 4px; border-radius: 4px;")
            self.lbl_main_stat_name.setText("⭐ 기준 스탯 확률:")

        self._on_sim_main_prob_changed(self.spin_sim_p_main.value())

    def _on_sim_main_prob_changed(self, main_val):
        sub_val = max(0.0, (100.0 - main_val) / 2.0)

        if not hasattr(self, 'sim_primary_stat'):
            self.sim_primary_stat = "atk"

        if self.sim_primary_stat == "atk":
            self.sim_p_atk = main_val
            self.sim_p_def = sub_val
            self.sim_p_prod = sub_val
            self.lbl_prob_atk_val.setText(f"{main_val:.1f}%  (⭐ 주스탯)")
            self.lbl_prob_atk_val.setStyleSheet("font-weight: bold; color: #f59e0b;")
            self.lbl_prob_def_val.setText(f"{sub_val:.1f}%  (보조: (100-{main_val:.0f})/2)")
            self.lbl_prob_def_val.setStyleSheet("font-weight: bold; color: #38bdf8;")
            self.lbl_prob_prod_val.setText(f"{sub_val:.1f}%  (보조: (100-{main_val:.0f})/2)")
            self.lbl_prob_prod_val.setStyleSheet("font-weight: bold; color: #10b981;")
        elif self.sim_primary_stat == "def":
            self.sim_p_atk = sub_val
            self.sim_p_def = main_val
            self.sim_p_prod = sub_val
            self.lbl_prob_def_val.setText(f"{main_val:.1f}%  (⭐ 주스탯)")
            self.lbl_prob_def_val.setStyleSheet("font-weight: bold; color: #38bdf8;")
            self.lbl_prob_atk_val.setText(f"{sub_val:.1f}%  (보조: (100-{main_val:.0f})/2)")
            self.lbl_prob_atk_val.setStyleSheet("font-weight: bold; color: #f59e0b;")
            self.lbl_prob_prod_val.setText(f"{sub_val:.1f}%  (보조: (100-{main_val:.0f})/2)")
            self.lbl_prob_prod_val.setStyleSheet("font-weight: bold; color: #10b981;")
        elif self.sim_primary_stat == "prod":
            self.sim_p_atk = sub_val
            self.sim_p_def = sub_val
            self.sim_p_prod = main_val
            self.lbl_prob_prod_val.setText(f"{main_val:.1f}%  (⭐ 주스탯)")
            self.lbl_prob_prod_val.setStyleSheet("font-weight: bold; color: #10b981;")
            self.lbl_prob_atk_val.setText(f"{sub_val:.1f}%  (보조: (100-{main_val:.0f})/2)")
            self.lbl_prob_atk_val.setStyleSheet("font-weight: bold; color: #f59e0b;")
            self.lbl_prob_def_val.setText(f"{sub_val:.1f}%  (보조: (100-{main_val:.0f})/2)")
            self.lbl_prob_def_val.setStyleSheet("font-weight: bold; color: #38bdf8;")
        else:
            self.sim_p_atk = main_val
            self.sim_p_def = sub_val
            self.sim_p_prod = sub_val
            self.lbl_prob_atk_val.setText(f"{main_val:.1f}%")
            self.lbl_prob_def_val.setText(f"{sub_val:.1f}%")
            self.lbl_prob_prod_val.setText(f"{sub_val:.1f}%")

        tot = self.sim_p_atk + self.sim_p_def + self.sim_p_prod
        self.lbl_sim_prob_total.setText(f"확률 합계: {tot:.1f}% (항상 100% 자동 유지)")

    def _run_crew_growth_simulation(self):
        cid = self.combo_sim_crew.currentData()
        cdata = self.crews_map.get(cid)
        if not cdata:
            QMessageBox.warning(self, "안내", "시뮬레이션할 승무원을 먼저 선택하세요.")
            return

        target_lvl = self.spin_sim_target_lvl.value()
        rolls = target_lvl - 1
        trials = self.spin_sim_trials.value()
        rate = self.spin_sim_rate.value()

        p_atk = getattr(self, 'sim_p_atk', 50.0)
        p_def = getattr(self, 'sim_p_def', 25.0)
        p_prod = getattr(self, 'sim_p_prod', 25.0)
        p_sum = p_atk + p_def + p_prod

        if p_sum <= 0:
            QMessageBox.warning(self, "오류", "확률 합계가 0%보다 커야 합니다.")
            return

        w_atk = p_atk / p_sum
        w_def = p_def / p_sum
        w_prod = p_prod / p_sum

        atk_results = []
        def_results = []
        prod_results = []
        single_roll_logs = []

        for trial_i in range(trials):
            a_cnt, d_cnt, p_cnt = 0, 0, 0
            for r_idx in range(rolls):
                r_val = random.random()
                if r_val < w_atk:
                    a_cnt += 1
                    stat_hit = "⚔️ 공격력"
                elif r_val < w_atk + w_def:
                    d_cnt += 1
                    stat_hit = "🛡️ 방어력"
                else:
                    p_cnt += 1
                    stat_hit = "🏭 생산/공업"

                if trials == 1:
                    lvl_cur = r_idx + 2
                    roll_pct = r_val * 100.0
                    single_roll_logs.append(
                        f"[Lv. {lvl_cur:2d}] 🎲 주사위 {roll_pct:5.1f}% ➔ {stat_hit} +1pt 획득 | 현재 누적 (⚔️:{a_cnt}pt, 🛡️:{d_cnt}pt, 🏭:{p_cnt}pt)"
                    )

            atk_results.append(a_cnt)
            def_results.append(d_cnt)
            prod_results.append(p_cnt)

        # Statistics Calculation
        avg_a = sum(atk_results) / trials
        avg_d = sum(def_results) / trials
        avg_p = sum(prod_results) / trials

        min_a, max_a = min(atk_results), max(atk_results)
        min_d, max_d = min(def_results), max(def_results)
        min_p, max_p = min(prod_results), max(prod_results)

        std_a = math.sqrt(sum((x - avg_a) ** 2 for x in atk_results) / trials)
        std_d = math.sqrt(sum((x - avg_d) ** 2 for x in def_results) / trials)
        std_p = math.sqrt(sum((x - avg_p) ** 2 for x in prod_results) / trials)

        sorted_a = sorted(atk_results)
        sorted_d = sorted(def_results)
        sorted_p = sorted(prod_results)

        def get_pctl(lst, pct):
            idx = int(len(lst) * pct)
            return lst[min(idx, len(lst) - 1)]

        # Update KPI Cards
        self.card_sim_atk.set_value(
            avg_a,
            f"평균 {avg_a:.1f} pt ({avg_a/rolls*100:.1f}%) [최소 {min_a} ~ 최대 {max_a} pt]"
        )
        self.card_sim_def.set_value(
            avg_d,
            f"평균 {avg_d:.1f} pt ({avg_d/rolls*100:.1f}%) [최소 {min_d} ~ 최대 {max_d} pt]"
        )
        self.card_sim_prod.set_value(
            avg_p,
            f"평균 {avg_p:.1f} pt ({avg_p/rolls*100:.1f}%) [최소 {min_p} ~ 최대 {max_p} pt]"
        )

        # Base Stats
        b_land = float(cdata.get("crewLandpower") or 0.0)
        b_fly = float(cdata.get("crewFlypower") or 0.0)
        b_def = float(cdata.get("crewDef") or 0.0)
        b_prod = float(cdata.get("crewProduct") or 0.0)
        b_ind = float(cdata.get("crewIndustry") or 0.0)

        # Expected Multipliers
        m_avg_atk = 1.0 + (avg_a * rate / 100.0)
        m_avg_def = 1.0 + (avg_d * rate / 100.0)
        m_avg_prod = 1.0 + (avg_p * rate / 100.0)

        # Populate Expected Stats Table
        stat_rows = [
            ("⚔️ 대지 위력 (Landpower)", b_land, avg_a, m_avg_atk, b_land * m_avg_atk, b_land * (1.0 + min_a * rate / 100.0), b_land * (1.0 + max_a * rate / 100.0)),
            ("🏹 대공 위력 (Flypower)", b_fly, avg_a, m_avg_atk, b_fly * m_avg_atk, b_fly * (1.0 + min_a * rate / 100.0), b_fly * (1.0 + max_a * rate / 100.0)),
            ("🛡️ 방어력 (Def)", b_def, avg_d, m_avg_def, b_def * m_avg_def, b_def * (1.0 + min_d * rate / 100.0), b_def * (1.0 + max_d * rate / 100.0)),
            ("🌾 생산력 (Product)", b_prod, avg_p, m_avg_prod, b_prod * m_avg_prod, b_prod * (1.0 + min_p * rate / 100.0), b_prod * (1.0 + max_p * rate / 100.0)),
            ("⚙️ 공업력 (Industry)", b_ind, avg_p, m_avg_prod, b_ind * m_avg_prod, b_ind * (1.0 + min_p * rate / 100.0), b_ind * (1.0 + max_p * rate / 100.0)),
        ]

        self.tbl_sim_stats.setRowCount(len(stat_rows))
        for row_idx, (name, base, pts, mult, avg_stat, min_s, max_s) in enumerate(stat_rows):
            self.tbl_sim_stats.setItem(row_idx, 0, QTableWidgetItem(name))
            self.tbl_sim_stats.setItem(row_idx, 1, QTableWidgetItem(f"{base:.1f}"))
            self.tbl_sim_stats.setItem(row_idx, 2, QTableWidgetItem(f"{pts:.2f} pt"))
            self.tbl_sim_stats.setItem(row_idx, 3, QTableWidgetItem(f"{mult:.3f}x (+{(mult-1)*100:.1f}%)"))
            self.tbl_sim_stats.setItem(row_idx, 4, QTableWidgetItem(f"{avg_stat:.2f}"))
            self.tbl_sim_stats.setItem(row_idx, 5, QTableWidgetItem(f"{min_s:.2f}"))
            self.tbl_sim_stats.setItem(row_idx, 6, QTableWidgetItem(f"{max_s:.2f}"))

        # Detailed Analytics Report
        cname = cdata.get("crewName") or cid
        analytics_lines = [
            f"================================================================================",
            f"📊 [승무원 레벨업 몬테카를로 랜덤 성장 통계 보고서]",
            f"================================================================================",
            f"• 대상 승무원: {cname} [{cdata.get('crewType')}] (ID: {cid})",
            f"• 목표 레벨: Lv.{target_lvl} (총 {rolls}회 스탯 성장 롤)",
            f"• 총 시뮬레이션 반복 횟수: {trials:,} 회 | 1pt당 증가율: {rate:.1f}%",
            f"• 설정된 확률 가중치: ⚔️공격력 {w_atk*100:.1f}% | 🛡️방어력 {w_def*100:.1f}% | 🏭생산/공업 {w_prod*100:.1f}%\n",
            f"--------------------------------------------------------------------------------",
            f"📈 [포인트 획득 분포 통계 (Percentiles & Deviation)]",
            f"--------------------------------------------------------------------------------",
            f"스탯 항목         평균(Mean)     표준편차(σ)   하위10%   하위25%   중앙값(50%)  상위25%   상위10%",
            f"⚔️ 공격력 포인트   {avg_a:6.2f} pt    ±{std_a:5.2f} pt   {get_pctl(sorted_a, 0.10):4d} pt   {get_pctl(sorted_a, 0.25):4d} pt    {get_pctl(sorted_a, 0.50):4d} pt   {get_pctl(sorted_a, 0.75):4d} pt   {get_pctl(sorted_a, 0.90):4d} pt",
            f"🛡️ 방어력 포인트   {avg_d:6.2f} pt    ±{std_d:5.2f} pt   {get_pctl(sorted_d, 0.10):4d} pt   {get_pctl(sorted_d, 0.25):4d} pt    {get_pctl(sorted_d, 0.50):4d} pt   {get_pctl(sorted_d, 0.75):4d} pt   {get_pctl(sorted_d, 0.90):4d} pt",
            f"🏭 생산/공업 포인트 {avg_p:6.2f} pt    ±{std_p:5.2f} pt   {get_pctl(sorted_p, 0.10):4d} pt   {get_pctl(sorted_p, 0.25):4d} pt    {get_pctl(sorted_p, 0.50):4d} pt   {get_pctl(sorted_p, 0.75):4d} pt   {get_pctl(sorted_p, 0.90):4d} pt\n",
            f"--------------------------------------------------------------------------------",
            f"💡 [밸런스 기획자 코멘트 및 분석 요약]",
            f"--------------------------------------------------------------------------------",
            f"• 공격력 포인트 기대값은 전체 {rolls}포인트 중 {avg_a:.1f}pt({avg_a/rolls*100:.1f}%)로, 이론 확률({w_atk*100:.1f}%)에 정확히 수렴했습니다.",
            f"• 상위 10% 대박 육성 시 공격력 포인트를 최대 {get_pctl(sorted_a, 0.90)}pt까지 획득하여 위력이 +{get_pctl(sorted_a, 0.90)*rate:.1f}% 증가합니다.",
            f"• 하위 10% 쪽박 육성 시 공격력 포인트를 {get_pctl(sorted_a, 0.10)}pt만 획득하여 위력이 +{get_pctl(sorted_a, 0.10)*rate:.1f}%에 머무를 수 있습니다."
        ]
        self.txt_sim_analytics.setText("\n".join(analytics_lines))

        # Roll History / Trials Log
        if trials == 1:
            log_header = [
                f"🎲 [1회 단일 레벨업 주사위 판정 상세 진행 로그 (Lv.1 ➔ Lv.{target_lvl})]",
                f"--------------------------------------------------------------------------------"
            ]
            self.txt_sim_log.setText("\n".join(log_header + single_roll_logs))
        else:
            log_lines = [
                f"📋 [총 {trials:,}회 시뮬레이션 중 상위/하위 대표 회차 샘플]",
                f"--------------------------------------------------------------------------------",
                f"• 최고 공격력 회차: ⚔️공격 {max_a}pt, 🛡️방어 {def_results[atk_results.index(max_a)]}pt, 🏭생산 {prod_results[atk_results.index(max_a)]}pt",
                f"• 최고 방어력 회차: ⚔️공격 {atk_results[def_results.index(max_d)]}pt, 🛡️방어 {max_d}pt, 🏭생산 {prod_results[def_results.index(max_d)]}pt",
                f"• 최고 생산력 회차: ⚔️공격 {atk_results[prod_results.index(max_p)]}pt, 🛡️방어 {def_results[prod_results.index(max_p)]}pt, 🏭생산 {max_p}pt",
                f"--------------------------------------------------------------------------------",
                f"📌 [최근 30개 시뮬레이션 회차별 결과]"
            ]
            for i in range(min(30, trials)):
                log_lines.append(
                    f"  Trial #{i+1:04d}: ⚔️공격 {atk_results[i]:2d}pt ({atk_results[i]/rolls*100:4.1f}%) | 🛡️방어 {def_results[i]:2d}pt ({def_results[i]/rolls*100:4.1f}%) | 🏭생산 {prod_results[i]:2d}pt ({prod_results[i]/rolls*100:4.1f}%)"
                )
            self.txt_sim_log.setText("\n".join(log_lines))

        # Save last sample result for Apply button
        sample_a = atk_results[0] if trials > 0 else int(round(avg_a))
        sample_d = def_results[0] if trials > 0 else int(round(avg_d))
        sample_p = prod_results[0] if trials > 0 else int(round(avg_p))
        self.last_crew_sim_result = (cdata, target_lvl, sample_a, sample_d, sample_p)

    def _apply_sim_result_to_workshop(self):
        if not self.last_crew_sim_result:
            QMessageBox.warning(self, "안내", "먼저 시뮬레이션을 1회 이상 실행하세요.")
            return

        cdata, target_lvl, sample_a, sample_d, sample_p = self.last_crew_sim_result
        cid = cdata.get("crewId")
        cname = cdata.get("crewName") or cid

        if not self.train_config.coaches:
            QMessageBox.information(self, "안내", "열차에 객차가 없습니다. 1번 워크숍 탭에서 먼저 객차를 추가해 주세요.")
            return

        # Find all coaches that already carry this crew
        matching_slots = []
        for slot in self.train_config.coaches:
            if slot.crew and slot.crew.get("crewId") == cid:
                matching_slots.append(slot)

        if not matching_slots:
            QMessageBox.warning(
                self, "적용 불가 (승무원 미배치)",
                f"현재 열차에 [{cname}] 승무원이 배치되어 있지 않습니다!\n\n"
                f"1번 워크숍 탭에서 원하는 객차에 [{cname}] 승무원을 먼저 배치한 후 다시 적용해 주세요."
            )
            return

        # Apply to ALL coaches carrying this crew
        for slot in matching_slots:
            slot.set_crew_level(target_lvl)
            slot.set_crew_points(sample_a, sample_d, sample_p)

        target_row = matching_slots[0].index
        indices_str = ", ".join(f"#{s.index}번" for s in matching_slots)
        msg = (
            f"열차에서 [{cname}] 승무원이 탑승 중인 총 {len(matching_slots)}개 객차({indices_str} 칸)에 일괄 동기화 적용되었습니다!\n\n"
            f"• 승무원: {cname} (Lv.{target_lvl})\n"
            f"• 배분 포인트: ⚔️공격 {sample_a}pt, 🛡️방어 {sample_d}pt, 🏭생산 {sample_p}pt\n"
            f"• 1번 탭의 조감도 및 능력치 대시보드에서 동기화된 스탯을 확인하실 수 있습니다."
        )

        self._update_coach_layout_ui(preserve_row=target_row)
        self._update_train_stats()

        self.tabs.setCurrentIndex(0)
        QMessageBox.information(self, "승무원 일괄 동기화 완료", msg)

def excepthook(exc_type, exc_value, exc_traceback):
    import traceback
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("Unhandled Exception:\n", err_msg)
    try:
        QMessageBox.critical(None, "실행 오류 (Error)", f"프로그램 실행 중 오류가 발생했습니다:\n\n{exc_value}\n\n{err_msg}")
    except Exception:
        pass

def main():
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    window = BattleSimulatorWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

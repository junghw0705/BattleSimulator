import csv
import html
import io
import math
import os
import random
import re
import sys
import zipfile

import numpy as np
import pandas as pd
import streamlit as st
from openpyxl import Workbook


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from battle_engine import BattleSimulationEngine
from data_loader import DataLoader
from models import EnemyGroupConfig, TrainConfig, TurretConfig


# ==============================================================================
# PAGE CONFIGURATION / DESKTOP THEME
# ==============================================================================
st.set_page_config(
    page_title="Siecletrain - 전투 시뮬레이터",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    :root {
        --bg: #0b1220;
        --surface: #111827;
        --surface-raised: #182235;
        --surface-hover: #202c40;
        --border: #2e3b52;
        --border-strong: #455673;
        --text: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --accent: #3b82f6;
        --accent-hover: #2563eb;
        --accent-soft: rgba(59, 130, 246, .14);
        --success: #10b981;
        --success-soft: rgba(16, 185, 129, .12);
        --warning: #f59e0b;
        --danger: #ef4444;
        --danger-soft: rgba(239, 68, 68, .12);
    }

    html { color-scheme: dark; }
    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: "Segoe UI", "Malgun Gothic", sans-serif;
        font-size: 14px;
    }
    .block-container {
        max-width: 1900px;
        padding: .8rem 1.15rem 1.75rem;
    }
    header[data-testid="stHeader"] {
        height: 0;
        background: transparent;
    }
    #MainMenu, footer { visibility: hidden; }

    .app-header {
        display: flex;
        align-items: center;
        gap: 12px;
        min-height: 52px;
    }
    .app-mark {
        display: grid;
        place-items: center;
        width: 40px;
        height: 40px;
        flex: 0 0 40px;
        border: 1px solid #315d96;
        border-radius: 10px;
        background: var(--accent-soft);
        font-size: 22px;
    }
    .app-title {
        color: var(--text);
        font-size: 19px;
        font-weight: 900;
        letter-spacing: -.15px;
        line-height: 1.25;
        white-space: nowrap;
    }
    .app-subtitle {
        color: var(--text-muted);
        font-size: 11.5px;
        font-weight: 600;
        line-height: 1.4;
        margin-top: 3px;
    }
    .group-title {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--text);
        background: transparent;
        border: 0;
        border-bottom: 1px solid var(--border);
        padding: 1px 0 9px;
        font-size: 13px;
        font-weight: 900;
        margin-bottom: 12px;
    }
    .group-title::before {
        content: "";
        display: block;
        width: 3px;
        height: 18px;
        border-radius: 3px;
        background: var(--accent);
    }
    .section-caption {
        color: var(--text-secondary);
        font-size: 11.5px;
        font-weight: 700;
        line-height: 1.45;
        margin-bottom: 8px;
    }
    .selected-title {
        color: #bfdbfe;
        background: var(--accent-soft);
        border: 1px solid #315d96;
        border-radius: 7px;
        padding: 7px 9px;
        font-size: 12.5px;
        font-weight: 800;
        line-height: 1.45;
        margin: 2px 0 10px;
    }
    .hint {
        color: var(--text-muted);
        font-size: 11px;
        line-height: 1.45;
    }
    .mono-box {
        background: #0d1525;
        border: 1px solid var(--border);
        border-radius: 7px;
        color: var(--text-secondary);
        font-family: Consolas, "Malgun Gothic", monospace;
        font-size: 11px;
        line-height: 1.55;
        padding: 10px 11px;
        white-space: pre-wrap;
    }
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin-bottom: 10px;
    }
    .stat-card {
        background: var(--surface-raised);
        border: 1px solid var(--border);
        border-top: 2px solid #3c4d67;
        border-radius: 8px;
        min-height: 62px;
        padding: 9px 10px;
    }
    .stat-label {
        color: var(--text-muted);
        font-size: 10.5px;
        font-weight: 700;
        line-height: 1.3;
    }
    .stat-value {
        color: var(--text);
        font-size: 14px;
        font-weight: 900;
        line-height: 1.3;
        margin-top: 4px;
    }
    .enemy-summary {
        background: var(--danger-soft);
        border: 1px solid #7f3540;
        border-left: 3px solid var(--danger);
        border-radius: 8px;
        padding: 10px;
        margin: 8px 0;
        color: #fecdd3;
        font-weight: 800;
        font-size: 12px;
    }
    .result-box {
        background: var(--success-soft);
        border: 1px solid #216e58;
        border-left: 3px solid var(--success);
        border-radius: 8px;
        padding: 11px;
        margin-top: 10px;
    }
    .danger-text { color: #fda4af; }
    .success-text { color: #6ee7b7; }
    .cyan-text { color: #93c5fd; }
    .amber-text { color: #fcd34d; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface);
        border-color: var(--border) !important;
        border-radius: 10px;
        box-shadow: none;
    }
    div[data-testid="stMetric"] {
        background: var(--surface-raised);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 10px 12px;
    }
    div[data-testid="stMetricLabel"] p {
        color: var(--text-muted);
        font-size: 11px;
        font-weight: 800;
    }
    div[data-testid="stMetricValue"] {
        color: var(--text);
        font-size: 17px;
        font-weight: 900;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 10.5px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        margin-bottom: 10px;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        padding: 8px 15px;
        background: transparent;
        border: 0;
        border-bottom: 2px solid transparent;
        border-radius: 0;
        color: var(--text-muted);
        font-size: 12px;
        font-weight: 800;
    }
    .stTabs [aria-selected="true"] {
        background: var(--accent-soft) !important;
        border-bottom-color: var(--accent) !important;
        color: #dbeafe !important;
        box-shadow: none;
    }

    .stButton > button, .stDownloadButton > button {
        min-height: 36px;
        padding: 6px 11px;
        border: 1px solid var(--border-strong);
        border-radius: 7px;
        background: var(--surface-raised);
        color: var(--text);
        font-size: 11.5px;
        font-weight: 800;
        line-height: 1.3;
        box-shadow: none;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--accent);
        background: var(--surface-hover);
        color: white;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent);
        border-color: var(--accent);
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-hover);
        border-color: var(--accent-hover);
    }
    div[data-testid="stSelectbox"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stSlider"] label {
        color: var(--text-secondary);
        font-size: 11.5px;
        font-weight: 800;
    }
    div[data-baseweb="select"] > div,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {
        min-height: 36px;
        background: var(--surface-raised);
        border: 1px solid var(--border-strong);
        border-radius: 7px;
        color: var(--text);
        font-size: 12px;
        font-weight: 600;
    }
    div[data-baseweb="select"] > div:hover,
    div[data-testid="stNumberInput"] input:hover,
    div[data-testid="stTextInput"] input:hover {
        border-color: #5e78a1;
    }
    div[data-baseweb="select"] span {
        color: var(--text) !important;
    }
    ul[role="listbox"] {
        background: var(--surface-raised) !important;
        border: 1px solid var(--border-strong);
    }
    li[role="option"] {
        color: var(--text) !important;
        font-size: 12px;
    }
    li[role="option"]:hover {
        background: var(--surface-hover) !important;
    }
    div[data-testid="stNumberInput"] button {
        background: var(--surface-hover);
        color: var(--text);
        border-color: var(--border-strong);
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
    }
    div[data-testid="stCaptionContainer"] p {
        color: var(--text-muted);
        font-size: 11px;
        line-height: 1.45;
    }
    .stMarkdown p, .stMarkdown li {
        color: var(--text-secondary);
        line-height: 1.5;
    }
    .stAlert {
        padding: 10px 12px;
        font-size: 11.5px;
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    hr {
        border-color: var(--border);
        margin: 10px 0;
    }
    div[data-testid="stCodeBlock"] {
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: var(--surface); }
    ::-webkit-scrollbar-thumb {
        background: #3a4961;
        border: 2px solid var(--surface);
        border-radius: 8px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #536782; }

    @media (max-width: 900px) {
        .block-container { padding: .65rem .65rem 1.25rem; }
        .app-title { font-size: 16px; }
        .app-subtitle { display: none; }
        .stTabs [data-baseweb="tab"] { padding: 7px 10px; font-size: 11px; }
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# HELPERS / SESSION STATE
# ==============================================================================
def esc(value):
    return html.escape(str(value if value is not None else "-"))


def fmt_num(value, digits=0):
    try:
        number = float(value or 0)
        return f"{number:,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def stat_cards(cards):
    body = "".join(
        f'<div class="stat-card"><div class="stat-label">{esc(label)}</div>'
        f'<div class="stat-value">{esc(value)}</div></div>'
        for label, value, _color in cards
    )
    st.markdown(f'<div class="stat-grid">{body}</div>', unsafe_allow_html=True)


def set_flash(level, message):
    st.session_state.flash_message = (level, message)


def show_flash():
    flash = st.session_state.pop("flash_message", None)
    if not flash:
        return
    level, message = flash
    getattr(st, level, st.info)(message)


def build_data_maps(loader):
    return {
        "locomotives": {
            r["locomotiveId"]: r
            for r in loader.get_sheet_data("Locomotive")
            if r.get("locomotiveId")
        },
        "couches": {
            r["couchId"]: r
            for r in loader.get_sheet_data("Couch")
            if r.get("couchId")
        },
        "engines": {
            r["engineId"]: r
            for r in loader.get_sheet_data("Engine")
            if r.get("engineId")
        },
        "generators": {
            r["generatorId"]: r
            for r in loader.get_sheet_data("Generator")
            if r.get("generatorId")
        },
        "brakes": {
            r["breakId"]: r
            for r in loader.get_sheet_data("Break")
            if r.get("breakId")
        },
        "crews": {
            r["crewId"]: r
            for r in loader.get_sheet_data("Crew")
            if r.get("crewId")
        },
        "weapons": {
            r["weaponId"]: r
            for r in loader.get_sheet_data("Weapon")
            if r.get("weaponId")
        },
        "monsters": {
            r["monsterId"]: r
            for r in loader.get_sheet_data("MonsterData")
            if r.get("monsterId")
        },
        "battle_areas": {
            r["battleAreaId"]: r
            for r in loader.get_sheet_data("BattleArea")
            if r.get("battleAreaId")
        },
    }


def parse_selected_coach_index(value, default=0):
    """Convert current and legacy Streamlit selectbox values into a coach index."""
    fallback = default if default is None else int(default)
    if isinstance(value, bool):
        return fallback
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"locomotive", "loco", "기관차", "0"}:
            return 0
        match = re.fullmatch(r"(?:coach[\s:_-]*)?(\d+)", normalized)
        if match:
            return int(match.group(1))
    return fallback


def coach_selector_token(index):
    return "locomotive" if int(index) <= 0 else f"coach:{int(index)}"


def normalize_selected_index():
    max_index = len(st.session_state.train_config.coaches)
    pending_token = st.session_state.pop("pending_coach_selection", None)
    if pending_token is not None:
        parsed_index = parse_selected_coach_index(pending_token, default=0)
        st.session_state.coach_row_selector = coach_selector_token(parsed_index)
    else:
        selector_index = parse_selected_coach_index(
            st.session_state.get("coach_row_selector"), default=None
        )
        parsed_index = (
            selector_index
            if selector_index is not None
            else parse_selected_coach_index(
                st.session_state.get("selected_coach_idx", 0), default=0
            )
        )
    st.session_state.selected_coach_idx = max(
        0, min(parsed_index, max_index)
    )


def sync_part(attr_name, widget_key, data_map):
    selected_id = st.session_state.get(widget_key)
    setattr(st.session_state.train_config, attr_name, data_map.get(selected_id))


def sync_selected_row():
    selected_index = parse_selected_coach_index(
        st.session_state.get("coach_row_selector"), default=0
    )
    max_index = len(st.session_state.train_config.coaches)
    st.session_state.selected_coach_idx = max(
        0, min(selected_index, max_index)
    )


def sync_crew_level(slot, widget_key):
    slot.set_crew_level(st.session_state[widget_key])


def sync_point_rate(widget_key):
    st.session_state.train_config.set_crew_point_rate(st.session_state[widget_key])


def sync_crew_points(slot, atk_key, def_key, prod_key):
    slot.set_crew_points(
        st.session_state[atk_key],
        st.session_state[def_key],
        st.session_state[prod_key],
    )


def apply_battle_area(area_id, battle_areas_map, monsters_map, loader, enemy_config):
    if not area_id:
        return 0
    area_record = battle_areas_map.get(area_id, {})
    level_id = area_record.get("battleLevelId") or area_id
    enemy_config.clear()
    enemy_config.selected_battle_area_id = area_id
    count = 0
    for spawn in loader.get_sheet_data("SpawnData"):
        target_level = spawn.get("levelId")
        if target_level and target_level in (level_id, area_id):
            monster_id = spawn.get("levelSpawnMonsterId")
            if monster_id in monsters_map:
                current = enemy_config.monster_counts.get(monster_id, 0)
                enemy_config.set_monster_count(monster_id, current + 1)
                count += 1
    return count


def combat_meta_text(summary, train_config, enemy_config, monsters_map):
    lines = []
    if summary:
        lines.append(
            "• 전투 결과: "
            f"{summary['result']} | 소요 시간: {summary['duration']}초 | "
            f"가한 총 피해량: {summary['total_damage_dealt']} | "
            f"처치 몬스터: {summary['total_kills']}마리"
        )
    lines.append("")
    lines.append("[1. 트레인 구성 정보 (Train Setup)]")
    lines.extend(f"  {line}" for line in train_config.get_config_details())
    lines.append("")
    lines.append("[2. 적 군단 구성 정보 (Enemy Army Setup)]")
    lines.extend(
        f"  {line}" for line in enemy_config.get_config_details(monsters_map)
    )
    return "\n".join(lines)


def combat_log_dataframe(engine):
    columns = [
        "시간(sec)",
        "이벤트",
        "공격자/주체",
        "피해자/대상",
        "피해량",
        "남은 HP",
        "상세 내용",
    ]
    records = []
    for entry in engine.combat_logs:
        records.append(
            {
                "시간(sec)": entry["time"],
                "이벤트": entry["event_type"],
                "공격자/주체": entry["attacker"],
                "피해자/대상": entry["target"],
                "피해량": entry["damage"],
                "남은 HP": entry["target_hp"],
                "상세 내용": entry["details"],
            }
        )
    return pd.DataFrame(records, columns=columns)


def battle_result_dataframes(summary, engine):
    car_rows = []
    for car in summary.get("cars", []):
        max_hp = float(car.get("max_hp") or 0)
        hp_left = float(car.get("hp_left") or 0)
        survival_rate = (hp_left / max_hp * 100.0) if max_hp > 0 else 0.0
        car_rows.append(
            {
                "열차 칸": car.get("name") or "-",
                "구분": "기관차" if car.get("type") == "locomotive" else "객차",
                "상태": "파괴" if car.get("is_destroyed") else "생존",
                "남은 HP": round(hp_left, 2),
                "최대 HP": round(max_hp, 2),
                "생존율": f"{survival_rate:.1f}%",
                "장착 포탑": int(car.get("turrets_count") or 0),
            }
        )

    total_turret_damage = sum(
        float(turret.get("total_damage") or 0)
        for turret in summary.get("turrets", [])
    )
    turret_rows = []
    for turret in summary.get("turrets", []):
        turret_damage = float(turret.get("total_damage") or 0)
        damage_share = (
            turret_damage / total_turret_damage * 100.0
            if total_turret_damage > 0
            else 0.0
        )
        turret_rows.append(
            {
                "포탑": turret.get("full_name") or "-",
                "속성": turret.get("land_type") or "-",
                "공격 패턴": turret.get("pattern") or "-",
                "기본 위력": round(float(turret.get("base_power") or 0), 2),
                "승무원 보너스": round(
                    float(turret.get("crew_power_bonus") or 0), 2
                ),
                "유효 위력": round(
                    float(turret.get("effective_power") or 0), 2
                ),
                "누적 피해": round(turret_damage, 2),
                "피해 기여도": f"{damage_share:.1f}%",
                "처치": int(turret.get("kills") or 0),
                "작동 상태": "정상" if turret.get("is_active") else "정지",
            }
        )

    log_frame = combat_log_dataframe(engine)
    event_rows = []
    if not log_frame.empty:
        for event_name, event_group in log_frame.groupby("이벤트", dropna=False):
            damage_values = pd.to_numeric(
                event_group["피해량"], errors="coerce"
            ).fillna(0.0)
            event_rows.append(
                {
                    "이벤트": event_name or "-",
                    "발생 횟수": len(event_group),
                    "전체 비중": f"{len(event_group) / len(log_frame) * 100:.1f}%",
                    "총 피해량": round(float(damage_values.sum()), 2),
                    "평균 피해량": round(float(damage_values.mean()), 2),
                    "최대 피해량": round(float(damage_values.max()), 2),
                }
            )
        event_rows.sort(key=lambda row: row["발생 횟수"], reverse=True)

    return (
        pd.DataFrame(car_rows),
        pd.DataFrame(turret_rows),
        pd.DataFrame(event_rows),
    )


def build_excel_report(summary, meta_text, log_df):
    workbook = Workbook()
    log_sheet = workbook.active
    log_sheet.title = "전투로그데이터"
    log_sheet.append(list(log_df.columns))
    for row in log_df.itertuples(index=False, name=None):
        log_sheet.append(list(row))

    config_sheet = workbook.create_sheet("트레인및적구성정보")
    config_sheet.append(["구분", "항목", "상세 내용 및 수치"])
    config_sheet.append(["시뮬레이션결과", "전투 결과", summary["result"]])
    config_sheet.append(["시뮬레이션결과", "소요 시간", summary["duration"]])
    config_sheet.append(
        ["시뮬레이션결과", "가한 총 피해량", summary["total_damage_dealt"]]
    )
    config_sheet.append(
        ["시뮬레이션결과", "처치 몬스터 수", summary["total_kills"]]
    )
    config_sheet.append(["시뮬레이션결과", "총 이벤트 로그 수", summary["log_count"]])
    config_sheet.append([])
    for line in meta_text.splitlines():
        config_sheet.append(["구성 정보", line])

    for sheet in (log_sheet, config_sheet):
        sheet.freeze_panes = "A2"
        for column_cells in sheet.columns:
            max_length = max(
                len(str(cell.value)) if cell.value is not None else 0
                for cell in column_cells
            )
            sheet.column_dimensions[column_cells[0].column_letter].width = min(
                max(max_length + 2, 11), 60
            )

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def build_csv_zip(meta_text, log_df):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "combat_log_전투로그.csv",
            log_df.to_csv(index=False).encode("utf-8-sig"),
        )
        config_buffer = io.StringIO()
        writer = csv.writer(config_buffer)
        writer.writerow(["SIECLETRAIN BATTLE SIMULATION LOG & CONFIGURATION REPORT"])
        for line in meta_text.splitlines():
            writer.writerow([line])
        archive.writestr(
            "combat_log_구성정보.csv",
            config_buffer.getvalue().encode("utf-8-sig"),
        )
    return buffer.getvalue()


def ensure_battle_artifacts(battle_result):
    """Build derived tables/downloads once and reuse them across Streamlit reruns."""
    if not battle_result:
        return battle_result

    engine = battle_result["engine"]
    summary = battle_result["summary"]
    meta_text = battle_result["meta_text"]

    if "log_df" not in battle_result:
        battle_result["log_df"] = combat_log_dataframe(engine)
    if not all(
        key in battle_result
        for key in ("car_frame", "turret_frame", "event_frame")
    ):
        car_frame, turret_frame, event_frame = battle_result_dataframes(
            summary, engine
        )
        battle_result["car_frame"] = car_frame
        battle_result["turret_frame"] = turret_frame
        battle_result["event_frame"] = event_frame
    if "excel_report" not in battle_result:
        battle_result["excel_report"] = build_excel_report(
            summary, meta_text, battle_result["log_df"]
        )
    if "csv_report" not in battle_result:
        battle_result["csv_report"] = build_csv_zip(
            meta_text, battle_result["log_df"]
        )
    return battle_result


def percentile(sorted_values, ratio):
    index = int(len(sorted_values) * ratio)
    return sorted_values[min(index, len(sorted_values) - 1)]


def arrow_safe_dataframe(frame):
    """Prevent mixed Excel value types (for example int + '#N/A') from upsetting Arrow."""
    safe_frame = frame.copy()
    for column in safe_frame.columns:
        if safe_frame[column].dtype == "object":
            safe_frame[column] = safe_frame[column].map(
                lambda value: None if value is None else str(value)
            )
    return safe_frame


if "loader" not in st.session_state:
    st.session_state.loader = DataLoader()
if "train_config" not in st.session_state:
    st.session_state.train_config = TrainConfig()
if "enemy_config" not in st.session_state:
    st.session_state.enemy_config = EnemyGroupConfig()
if "turret_config" not in st.session_state:
    st.session_state.turret_config = TurretConfig(max_slots_per_coach=4)
if "selected_coach_idx" not in st.session_state:
    st.session_state.selected_coach_idx = 0
if "last_battle_result" not in st.session_state:
    st.session_state.last_battle_result = None
if "last_crew_sim_result" not in st.session_state:
    st.session_state.last_crew_sim_result = None

loader = st.session_state.loader
train_config = st.session_state.train_config
enemy_config = st.session_state.enemy_config
turret_config = st.session_state.turret_config

maps = build_data_maps(loader)
locomotives_map = maps["locomotives"]
couches_map = maps["couches"]
engines_map = maps["engines"]
generators_map = maps["generators"]
brakes_map = maps["brakes"]
crews_map = maps["crews"]
weapons_map = maps["weapons"]
monsters_map = maps["monsters"]
battle_areas_map = maps["battle_areas"]

normalize_selected_index()


# ==============================================================================
# HEADER
# ==============================================================================
header_left, header_right = st.columns([5, 1.45])
with header_left:
    st.markdown(
        """
        <div class="app-header">
            <div class="app-mark">🚂</div>
            <div>
                <div class="app-title">SIECLETRAIN BATTLE SIMULATOR</div>
                <div class="app-subtitle">열차 구성 · 적 편성 · 전투 로그 · 승무원 성장 분석</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_right:
    if st.button(
        "🔄 엑셀 새로고침 (Excel Reload)",
        key="reload_excel",
        use_container_width=True,
    ):
        try:
            loader.reload_all_data()
            total_items = sum(len(records) for records in loader.data.values())
            st.session_state.last_battle_result = None
            set_flash(
                "success",
                f"엑셀 파일에서 총 {total_items:,}건의 데이터를 새로고침했습니다.",
            )
            st.rerun()
        except Exception as exc:
            st.error(f"엑셀 파일 읽기 중 오류가 발생했습니다: {exc}")

show_flash()

tab_workshop, tab_log, tab_inspector, tab_crew = st.tabs(
    [
        "1. 🚂 통합 열차 & 적 세팅 워크숍",
        "2. 📋 전투 로그 시트 (Combat Log)",
        "3. 🔍 Raw 데이터 검증 (Inspector)",
        "4. 🎲 승무원 레벨업 랜덤 성장 시뮬레이터",
    ]
)


# ==============================================================================
# TAB 1: WORKSHOP
# ==============================================================================
with tab_workshop:
    stats = train_config.calculate_stats()

    # 상단 Visual Blueprint
    with st.container(border=True):
        summary_left, summary_right = st.columns([4, 1])
        with summary_left:
            st.markdown(
                '<div class="section-caption">🔍 열차 칸 카드를 클릭하여 상세 스탯과 장착 대상을 전환합니다.</div>',
                unsafe_allow_html=True,
            )
        with summary_right:
            st.markdown(
                f'<div class="section-caption cyan-text" style="text-align:right">'
                f"보호막: {stats['total_shield']:.0f} | 포탑: {stats['turret_count']}개"
                "</div>",
                unsafe_allow_html=True,
            )

        blueprint_columns = st.columns(
            max(1, len(train_config.coaches) + 1), gap="small"
        )
        with blueprint_columns[0]:
            locomotive = train_config.locomotive
            loco_name = (
                locomotive.get("locomotiveName") if locomotive else "기관차 미선택"
            )
            loco_hp = float(locomotive.get("locomotiveHp") or 0) if locomotive else 0
            loco_def = (
                float(locomotive.get("locomotiveDef") or 0) if locomotive else 0
            )
            loco_shield = train_config.get_locomotive_shield()
            loco_turret_names = [
                (weapon.get("weaponName") or weapon.get("weaponId"))[:3]
                for weapon in train_config.locomotive_turrets
            ]
            while len(loco_turret_names) < 2:
                loco_turret_names.append("-")
            if st.button(
                "🚂 [기관차]\n"
                f"{loco_name}\n"
                f"Def:{loco_def:.0f} | 🛡️:{loco_shield:.0f} | HP:{loco_hp:.0f}\n"
                f"T1:{loco_turret_names[0]}  T2:{loco_turret_names[1]}",
                key="blueprint_locomotive",
                type=(
                    "primary"
                    if st.session_state.selected_coach_idx == 0
                    else "secondary"
                ),
                use_container_width=True,
            ):
                st.session_state.selected_coach_idx = 0
                st.session_state.coach_row_selector = coach_selector_token(0)
                st.rerun()

        for coach_index, slot in enumerate(train_config.coaches, start=1):
            with blueprint_columns[coach_index]:
                coach_stats = slot.get_couch_stats()
                coach_shield = slot.get_total_coach_shield(
                    generator=train_config.generator
                )
                crew_name = (
                    slot.crew.get("crewName") if slot.crew else "승무원 미배치"
                )
                if st.button(
                    f"🚃 [객차 #{slot.index}] 시너지:{slot.get_synergy_power():.1f}x\n"
                    f"{slot.get_name()}\n"
                    f"Def:{slot.get_total_coach_def():.1f} | 🛡️:{coach_shield:.0f} | HP:{coach_stats.get('hp', 0):.0f}\n"
                    f"🔫 {len(slot.turrets)}/4 | 👨‍✈️ {crew_name} Lv.{slot.crew_level}",
                    key=f"blueprint_coach_{coach_index}",
                    type=(
                        "primary"
                        if st.session_state.selected_coach_idx == coach_index
                        else "secondary"
                    ),
                    use_container_width=True,
                ):
                    st.session_state.selected_coach_idx = coach_index
                    st.session_state.coach_row_selector = coach_selector_token(
                        coach_index
                    )
                    st.rerun()

    left_column, middle_column, right_column = st.columns([3, 4, 4], gap="small")

    # --------------------------------------------------------------------------
    # LEFT: Selected dashboard + locomotive parts
    # --------------------------------------------------------------------------
    with left_column:
        with st.container(border=True):
            st.markdown(
                '<div class="group-title">📊 능력치 대시보드</div>',
                unsafe_allow_html=True,
            )
            selected_index = st.session_state.selected_coach_idx
            if selected_index == 0:
                if train_config.locomotive:
                    locomotive = train_config.locomotive
                    st.markdown(
                        f'<div class="selected-title">🚂 [기관차 대시보드] '
                        f"{esc(locomotive.get('locomotiveName') or locomotive.get('locomotiveId'))}</div>",
                        unsafe_allow_html=True,
                    )
                    stat_cards(
                        [
                            (
                                "기관차 체력 (HP)",
                                fmt_num(locomotive.get("locomotiveHp")),
                                "#10b981",
                            ),
                            (
                                "제네레이터 보호막",
                                fmt_num(train_config.get_locomotive_shield()),
                                "#06b6d4",
                            ),
                            (
                                "기관차 방어력",
                                fmt_num(stats["locomotive_def"]),
                                "#3b82f6",
                            ),
                            (
                                "현재 중량 / 허용 중량",
                                f"{stats['current_weight']:.0f} / {stats['weight_limit']:.0f} kg",
                                "#ef4444",
                            ),
                            (
                                "총 엔진 출력",
                                f"{stats['horsepower']:.0f} HP",
                                "#8b5cf6",
                            ),
                            (
                                "객차 연결 (현재/최대)",
                                f"{stats['current_couches']} / {stats['max_couches']} 칸",
                                "#f59e0b",
                            ),
                        ]
                    )
                    engine_name = (
                        train_config.engine.get("engineName")
                        if train_config.engine
                        else "엔진 미장착"
                    )
                    generator_name = (
                        train_config.generator.get("generatorName")
                        if train_config.generator
                        else "제네레이터 미장착"
                    )
                    brake_name = (
                        train_config.brake.get("breakName")
                        if train_config.brake
                        else "제동장치 미장착"
                    )
                    details = [
                        f"⚡ 엔진: {engine_name} (가속력: {stats['accel_power']:.2f})",
                        f"🛡️ 제네레이터: {generator_name} (전체 공유 보호막)",
                        f"🛑 제동장치: {brake_name} (제동력: {stats['brake_power']:.2f})",
                        f"🔫 기관차 자체 포탑 ({len(train_config.locomotive_turrets)}/2개):",
                    ]
                    if train_config.locomotive_turrets:
                        for index, weapon in enumerate(
                            train_config.locomotive_turrets, start=1
                        ):
                            details.append(
                                f"   • T{index}:{weapon.get('weaponName') or weapon.get('weaponId')} "
                                f"[{str(weapon.get('weaponLandType') or 'L').upper()}] | "
                                f"위력:{float(weapon.get('weaponPower') or 0):.1f}"
                            )
                    else:
                        details.append("   • (장착된 기관차 포탑 없음)")
                    st.markdown(
                        f'<div class="mono-box">{esc(chr(10).join(details))}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="selected-title">🚂 기관차 미선택</div>',
                        unsafe_allow_html=True,
                    )
                    stat_cards(
                        [
                            ("기관차 체력 (HP)", "0", "#10b981"),
                            ("제네레이터 보호막", "0", "#06b6d4"),
                            ("기관차 방어력", "0", "#3b82f6"),
                            ("현재 중량 / 허용 중량", "0 / 0 kg", "#ef4444"),
                            ("총 엔진 출력", "0 HP", "#8b5cf6"),
                            ("객차 연결 (현재/최대)", "0 / 0 칸", "#f59e0b"),
                        ]
                    )
                    st.info("기관차를 아래 파츠 선택에서 장착하세요.")
            else:
                slot = train_config.coaches[selected_index - 1]
                coach_stats = slot.get_couch_stats()
                effective = slot.get_effective_crew_stats()
                st.markdown(
                    f'<div class="selected-title">🚃 [{slot.index}번 객차 대시보드] '
                    f"{esc(slot.get_name())}</div>",
                    unsafe_allow_html=True,
                )
                stat_cards(
                    [
                        ("객차 체력 (HP)", fmt_num(coach_stats["hp"]), "#10b981"),
                        (
                            "객차 보호막",
                            fmt_num(
                                slot.get_total_coach_shield(
                                    generator=train_config.generator
                                )
                            ),
                            "#06b6d4",
                        ),
                        (
                            "객차 방어력",
                            f"{slot.get_total_coach_def():.1f} "
                            f"(기본:{coach_stats['def']:.0f}+승무원:{effective['def']:.1f})",
                            "#3b82f6",
                        ),
                        ("객차 무게", f"{coach_stats['weight']:.0f} kg", "#ef4444"),
                        (
                            "시너지 계수",
                            f"{slot.get_synergy_power():.2f}x",
                            "#8b5cf6",
                        ),
                        ("객차 가격", f"{coach_stats['cost']:,.0f} G", "#f59e0b"),
                    ]
                )
                details = []
                if slot.crew:
                    crew_name = slot.crew.get("crewName") or slot.crew.get("crewId")
                    details.extend(
                        [
                            f"👨‍✈️ 승무원: {crew_name} [{slot.crew.get('crewType') or ''}] "
                            f"(Lv.{slot.crew_level} | ⚔️+{slot.crew_atk_pts}pt, "
                            f"🛡️+{slot.crew_def_pts}pt, 🏭+{slot.crew_prod_pts}pt)",
                            f"   • 대지:{effective['landpower']:.1f} | 대공:{effective['flypower']:.1f}",
                            f"   • Def:+{effective['def']:.1f} | 생산:{effective['product']:.1f} | 공업:{effective['industry']:.1f}",
                        ]
                    )
                else:
                    details.append("👨‍✈️ 승무원: 미배치")
                details.append(f"🔫 포탑 ({len(slot.turrets)}/4개):")
                if slot.turrets:
                    for index, weapon in enumerate(slot.turrets, start=1):
                        land_type = str(
                            weapon.get("weaponLandType") or "L"
                        ).strip().upper()
                        crew_bonus = (
                            effective["landpower"]
                            if land_type == "L"
                            else effective["flypower"]
                            if land_type == "F"
                            else max(
                                effective["landpower"], effective["flypower"]
                            )
                        )
                        base_power = float(weapon.get("weaponPower") or 0)
                        details.append(
                            f"   • T{index}:{weapon.get('weaponName') or weapon.get('weaponId')} "
                            f"[{land_type}] | 위력:{base_power + crew_bonus:.1f}"
                            f"(기본:{base_power:.1f}+승무원:{crew_bonus:.1f})"
                        )
                else:
                    details.append("   • (장착된 포탑 없음)")
                st.markdown(
                    f'<div class="mono-box">{esc(chr(10).join(details))}</div>',
                    unsafe_allow_html=True,
                )

        with st.container(border=True):
            st.markdown(
                '<div class="group-title">🚂 기관차 핵심 파츠 선택</div>',
                unsafe_allow_html=True,
            )
            part_specs = [
                (
                    "기관차 (Loco)",
                    "part_locomotive",
                    "locomotive",
                    locomotives_map,
                    "locomotiveId",
                    "locomotiveName",
                ),
                (
                    "⚡ 엔진 (Engine)",
                    "part_engine",
                    "engine",
                    engines_map,
                    "engineId",
                    "engineName",
                ),
                (
                    "🛡️ 제네레이터 (Gen)",
                    "part_generator",
                    "generator",
                    generators_map,
                    "generatorId",
                    "generatorName",
                ),
                (
                    "🛑 제동장치 (Brake)",
                    "part_brake",
                    "brake",
                    brakes_map,
                    "breakId",
                    "breakName",
                ),
            ]
            for label, key, attr, data_map, id_field, name_field in part_specs:
                current_data = getattr(train_config, attr)
                current_id = current_data.get(id_field) if current_data else None
                options = [None] + list(data_map.keys())
                if key not in st.session_state or st.session_state[key] not in options:
                    st.session_state[key] = (
                        current_id if current_id in data_map else None
                    )
                st.selectbox(
                    label,
                    options,
                    key=key,
                    format_func=lambda item, m=data_map, nf=name_field: (
                        "-- 미장착 --"
                        if item is None
                        else f"{m[item].get(nf) or item} ({item})"
                    ),
                    on_change=sync_part,
                    args=(attr, key, data_map),
                )

    # --------------------------------------------------------------------------
    # MIDDLE: Coach list, turret and crew setup
    # --------------------------------------------------------------------------
    with middle_column:
        with st.container(border=True):
            st.markdown(
                '<div class="group-title">🚃 객차배치도 & 포탑/승무원 세팅</div>',
                unsafe_allow_html=True,
            )

            add_coach_left, add_coach_right = st.columns([3, 1])
            couch_ids = list(couches_map.keys())
            with add_coach_left:
                selected_couch_id = st.selectbox(
                    "추가할 객차",
                    couch_ids,
                    key="couch_to_add",
                    format_func=lambda item: (
                        f"{couches_map[item].get('couchName') or item} "
                        f"(시너지:{float(couches_map[item].get('couchSynergyPower') or 1):.1f}x)"
                    ),
                    label_visibility="collapsed",
                )
            with add_coach_right:
                if st.button(
                    "객차 추가 (+)", key="add_coach", use_container_width=True
                ):
                    if not train_config.locomotive:
                        st.warning("기관차를 먼저 선택하세요.")
                    else:
                        max_coaches = int(
                            train_config.locomotive.get("locomotiveCouch") or 0
                        )
                        if len(train_config.coaches) >= max_coaches:
                            st.warning(
                                f"선택한 기관차에는 최대 {max_coaches}칸만 연결할 수 있습니다."
                            )
                        elif selected_couch_id:
                            train_config.add_coach(couches_map[selected_couch_id])
                            new_coach_index = len(train_config.coaches)
                            st.session_state.selected_coach_idx = new_coach_index
                            st.session_state.coach_row_selector = (
                                coach_selector_token(new_coach_index)
                            )
                            st.rerun()

            st.markdown(
                '<div class="section-caption">📋 열차 칸 목록 (클릭하여 장착/배치)</div>',
                unsafe_allow_html=True,
            )
            coach_rows = ["locomotive"] + [
                coach_selector_token(index)
                for index in range(1, len(train_config.coaches) + 1)
            ]

            def coach_row_label(row_token):
                row = parse_selected_coach_index(row_token, default=0)
                if row == 0:
                    # Keep labels stable. Dynamic text here makes Streamlit treat
                    # the options as a new list and reset selection to row 0.
                    return "🚂 [기관차] 파츠 / 자체 포탑 설정"
                selected_slot = train_config.coaches[row - 1]
                return f"🚃 [{selected_slot.index}번 칸] {selected_slot.get_name()}"

            if (
                "coach_row_selector" not in st.session_state
                or st.session_state.coach_row_selector not in coach_rows
            ):
                st.session_state.coach_row_selector = coach_selector_token(
                    st.session_state.selected_coach_idx
                )

            selected_row_token = st.selectbox(
                "열차 칸 목록",
                coach_rows,
                key="coach_row_selector",
                format_func=coach_row_label,
                on_change=sync_selected_row,
                label_visibility="collapsed",
            )
            selected_index = parse_selected_coach_index(
                selected_row_token,
                default=st.session_state.selected_coach_idx,
            )
            st.session_state.selected_coach_idx = max(
                0, min(selected_index, len(train_config.coaches))
            )
            selected_index = st.session_state.selected_coach_idx

            if selected_index > 0:
                if st.button(
                    "선택한 객차 삭제 (-)",
                    key="remove_selected_coach",
                    use_container_width=True,
                ):
                    train_config.remove_coach(selected_index - 1)
                    target_index = max(0, selected_index - 1)
                    st.session_state.selected_coach_idx = target_index
                    st.session_state.pending_coach_selection = (
                        coach_selector_token(target_index)
                    )
                    st.rerun()

            if selected_index == 0:
                selected_name = (
                    train_config.locomotive.get("locomotiveName")
                    if train_config.locomotive
                    else "기관차 미선택"
                )
                st.markdown(
                    f'<div class="selected-title">선택: 🚂 [기관차] {esc(selected_name)} '
                    f"(Def:{stats['locomotive_def']:.0f} | "
                    f"🛡️보호막:{train_config.get_locomotive_shield():.0f} | "
                    f"자체 포탑:{len(train_config.locomotive_turrets)}/2개)</div>",
                    unsafe_allow_html=True,
                )
                selected_turrets = train_config.locomotive_turrets
                turret_limit = 2
                selected_slot = None
            else:
                selected_slot = train_config.coaches[selected_index - 1]
                selected_turrets = selected_slot.turrets
                turret_limit = 4
                coach_stats = selected_slot.get_couch_stats()
                st.markdown(
                    f'<div class="selected-title">선택: 🚃 [{selected_slot.index}번 칸] '
                    f"{esc(selected_slot.get_name())} "
                    f"(Def:{selected_slot.get_total_coach_def():.1f} | "
                    f"🛡️보호막:{selected_slot.get_total_coach_shield(generator=train_config.generator):.0f} | "
                    f"시너지:{selected_slot.get_synergy_power():.1f}x | HP:{coach_stats['hp']:.0f})</div>",
                    unsafe_allow_html=True,
                )

            turret_left, turret_right = st.columns([3, 1])
            weapon_ids = list(weapons_map.keys())
            with turret_left:
                selected_weapon_id = st.selectbox(
                    "포탑 장착",
                    weapon_ids,
                    key="turret_to_equip",
                    format_func=lambda item: (
                        f"[{weapons_map[item].get('weaponLandType') or 'L'}] "
                        f"{weapons_map[item].get('weaponName') or item} "
                        f"(위력:{weapons_map[item].get('weaponPower') or 0})"
                    ),
                    label_visibility="collapsed",
                )
            with turret_right:
                if st.button(
                    "장착 (+)", key="equip_turret", use_container_width=True
                ):
                    if selected_index == 0 and not train_config.locomotive:
                        st.warning("기관차를 먼저 선택하세요.")
                    elif len(selected_turrets) >= turret_limit:
                        st.warning(
                            f"현재 선택 칸에는 최대 {turret_limit}개의 포탑만 장착할 수 있습니다."
                        )
                    elif selected_weapon_id:
                        selected_turrets.append(weapons_map[selected_weapon_id])
                        st.rerun()

            if selected_turrets:
                for turret_index, weapon in enumerate(list(selected_turrets)):
                    turret_info, turret_remove = st.columns([4, 1])
                    land_type = str(
                        weapon.get("weaponLandType") or "L"
                    ).strip().upper()
                    base_power = float(weapon.get("weaponPower") or 0)
                    crew_bonus = 0.0
                    if selected_slot:
                        effective = selected_slot.get_effective_crew_stats()
                        crew_bonus = (
                            effective["landpower"]
                            if land_type == "L"
                            else effective["flypower"]
                            if land_type == "F"
                            else max(
                                effective["landpower"], effective["flypower"]
                            )
                        )
                    with turret_info:
                        st.caption(
                            f"🔫 #{turret_index + 1}: "
                            f"**{weapon.get('weaponName') or weapon.get('weaponId')}** "
                            f"[{land_type}] (총 위력: {base_power + crew_bonus:.1f})"
                        )
                    with turret_remove:
                        if st.button(
                            "해제 (-)",
                            key=f"remove_turret_{selected_index}_{turret_index}",
                            use_container_width=True,
                        ):
                            selected_turrets.pop(turret_index)
                            st.rerun()
            else:
                st.caption("장착된 포탑이 없습니다.")

            if selected_slot is None:
                st.info(
                    "👨‍✈️ 기관차에는 승무원을 배치할 수 없습니다. 객차를 선택하세요."
                )
            else:
                crew_select, crew_assign, crew_unassign = st.columns([3, 1, 1])
                crew_ids = [None] + list(crews_map.keys())
                current_crew_id = (
                    selected_slot.crew.get("crewId") if selected_slot.crew else None
                )
                crew_widget_key = f"crew_select_{selected_slot.index}"
                if (
                    crew_widget_key not in st.session_state
                    or st.session_state[crew_widget_key] not in crew_ids
                ):
                    st.session_state[crew_widget_key] = current_crew_id
                with crew_select:
                    chosen_crew_id = st.selectbox(
                        "승무원 배치",
                        crew_ids,
                        key=crew_widget_key,
                        format_func=lambda item: (
                            "-- 승무원 미배치 --"
                            if item is None
                            else f"{crews_map[item].get('crewName') or item} "
                            f"(대지+{crews_map[item].get('crewLandpower') or 0}, "
                            f"대공+{crews_map[item].get('crewFlypower') or 0})"
                        ),
                        label_visibility="collapsed",
                    )
                with crew_assign:
                    if st.button(
                        "배치 (+)",
                        key=f"assign_crew_{selected_slot.index}",
                        use_container_width=True,
                    ):
                        if chosen_crew_id is None:
                            st.warning("배치할 승무원을 선택하세요.")
                        else:
                            duplicate = next(
                                (
                                    slot
                                    for slot in train_config.coaches
                                    if slot is not selected_slot
                                    and slot.crew
                                    and slot.crew.get("crewId") == chosen_crew_id
                                ),
                                None,
                            )
                            if duplicate:
                                st.error(
                                    f"[{crews_map[chosen_crew_id].get('crewName')}] 승무원은 "
                                    f"이미 {duplicate.index}번 객차에 배치되어 있습니다."
                                )
                            else:
                                selected_slot.crew = crews_map[chosen_crew_id]
                                st.rerun()
                with crew_unassign:
                    if st.button(
                        "해제 (-)",
                        key=f"unassign_crew_{selected_slot.index}",
                        use_container_width=True,
                    ):
                        selected_slot.crew = None
                        st.session_state[crew_widget_key] = None
                        st.rerun()

                if selected_slot.crew:
                    crew_name = (
                        selected_slot.crew.get("crewName")
                        or selected_slot.crew.get("crewId")
                    )
                    with st.container(border=True):
                        st.markdown(
                            f'<div class="group-title">👨‍✈️ [{selected_slot.index}번 {esc(crew_name)}] '
                            "레벨 & 스탯 포인트 배분</div>",
                            unsafe_allow_html=True,
                        )

                        level_key = f"crew_level_{selected_slot.index}"
                        rate_key = f"crew_rate_{selected_slot.index}"
                        if (
                            level_key not in st.session_state
                            or st.session_state[level_key]
                            != selected_slot.crew_level
                        ):
                            st.session_state[level_key] = selected_slot.crew_level
                        if (
                            rate_key not in st.session_state
                            or float(st.session_state[rate_key])
                            != float(train_config.crew_point_rate)
                        ):
                            st.session_state[rate_key] = float(
                                train_config.crew_point_rate
                            )

                        level_m10, level_m1, level_value, level_p1, level_p10 = (
                            st.columns([1, 1, 2, 1, 1])
                        )
                        with level_m10:
                            if st.button(
                                "-10",
                                key=f"level_m10_{selected_slot.index}",
                                use_container_width=True,
                            ):
                                selected_slot.set_crew_level(
                                    selected_slot.crew_level - 10
                                )
                                st.session_state[level_key] = (
                                    selected_slot.crew_level
                                )
                                st.rerun()
                        with level_m1:
                            if st.button(
                                "-",
                                key=f"level_m1_{selected_slot.index}",
                                use_container_width=True,
                            ):
                                selected_slot.set_crew_level(
                                    selected_slot.crew_level - 1
                                )
                                st.session_state[level_key] = (
                                    selected_slot.crew_level
                                )
                                st.rerun()
                        with level_value:
                            st.number_input(
                                "레벨(1~50)",
                                min_value=1,
                                max_value=50,
                                step=1,
                                key=level_key,
                                on_change=sync_crew_level,
                                args=(selected_slot, level_key),
                            )
                        with level_p1:
                            if st.button(
                                "+",
                                key=f"level_p1_{selected_slot.index}",
                                use_container_width=True,
                            ):
                                selected_slot.set_crew_level(
                                    selected_slot.crew_level + 1
                                )
                                st.session_state[level_key] = (
                                    selected_slot.crew_level
                                )
                                st.rerun()
                        with level_p10:
                            if st.button(
                                "+10",
                                key=f"level_p10_{selected_slot.index}",
                                use_container_width=True,
                            ):
                                selected_slot.set_crew_level(
                                    selected_slot.crew_level + 10
                                )
                                st.session_state[level_key] = (
                                    selected_slot.crew_level
                                )
                                st.rerun()

                        points_left, rate_right = st.columns([2, 1])
                        with points_left:
                            st.markdown(
                                f'<div class="section-caption cyan-text">남은 포인트: '
                                f"{selected_slot.get_remaining_points()} / "
                                f"{selected_slot.get_max_available_points()} pt "
                                f"(사용:{selected_slot.get_used_points()}pt)</div>",
                                unsafe_allow_html=True,
                            )
                        with rate_right:
                            st.number_input(
                                "1pt당 증가율 (%)",
                                min_value=0.1,
                                max_value=100.0,
                                step=0.5,
                                key=rate_key,
                                on_change=sync_point_rate,
                                args=(rate_key,),
                            )

                        point_specs = [
                            (
                                "⚔️ 공격력",
                                "atk",
                                "crew_atk_pts",
                                "#f59e0b",
                            ),
                            (
                                "🛡️ 방어력",
                                "def",
                                "crew_def_pts",
                                "#38bdf8",
                            ),
                            (
                                "🏭 생산/공업",
                                "prod",
                                "crew_prod_pts",
                                "#10b981",
                            ),
                        ]
                        point_keys = {
                            stat_key: f"crew_{stat_key}_pts_{selected_slot.index}"
                            for _, stat_key, _, _ in point_specs
                        }
                        for _, stat_key, attr_name, _ in point_specs:
                            if (
                                point_keys[stat_key] not in st.session_state
                                or st.session_state[point_keys[stat_key]]
                                != getattr(selected_slot, attr_name)
                            ):
                                st.session_state[point_keys[stat_key]] = getattr(
                                    selected_slot, attr_name
                                )

                        for label, stat_key, attr_name, color in point_specs:
                            point_label, point_minus, point_value, point_plus = (
                                st.columns([2.4, 0.7, 1.2, 0.7])
                            )
                            with point_label:
                                st.markdown(
                                    f'<div style="font-weight:700;color:{color};padding-top:7px">{label}</div>',
                                    unsafe_allow_html=True,
                                )
                            with point_minus:
                                if st.button(
                                    "-",
                                    key=f"point_minus_{selected_slot.index}_{stat_key}",
                                    use_container_width=True,
                                ):
                                    setattr(
                                        selected_slot,
                                        attr_name,
                                        max(0, getattr(selected_slot, attr_name) - 1),
                                    )
                                    st.session_state[point_keys[stat_key]] = getattr(
                                        selected_slot, attr_name
                                    )
                                    st.rerun()
                            with point_value:
                                st.number_input(
                                    label,
                                    min_value=0,
                                    max_value=49,
                                    step=1,
                                    key=point_keys[stat_key],
                                    on_change=sync_crew_points,
                                    args=(
                                        selected_slot,
                                        point_keys["atk"],
                                        point_keys["def"],
                                        point_keys["prod"],
                                    ),
                                    label_visibility="collapsed",
                                )
                            with point_plus:
                                if st.button(
                                    "+",
                                    key=f"point_plus_{selected_slot.index}_{stat_key}",
                                    use_container_width=True,
                                ):
                                    if selected_slot.get_remaining_points() <= 0:
                                        st.warning(
                                            "남은 포인트가 없습니다. 먼저 레벨을 올리세요."
                                        )
                                    else:
                                        setattr(
                                            selected_slot,
                                            attr_name,
                                            getattr(selected_slot, attr_name) + 1,
                                        )
                                        st.session_state[
                                            point_keys[stat_key]
                                        ] = getattr(selected_slot, attr_name)
                                        st.rerun()

                        preset_reset, preset_atk, preset_def, preset_even = st.columns(
                            4
                        )
                        presets = [
                            (preset_reset, "초기화", (0, 0, 0), "reset"),
                            (
                                preset_atk,
                                "공격 올인",
                                (
                                    selected_slot.get_max_available_points(),
                                    0,
                                    0,
                                ),
                                "atk",
                            ),
                            (
                                preset_def,
                                "방어 올인",
                                (
                                    0,
                                    selected_slot.get_max_available_points(),
                                    0,
                                ),
                                "def",
                            ),
                        ]
                        max_points = selected_slot.get_max_available_points()
                        each = max_points // 3
                        remainder = max_points % 3
                        presets.append(
                            (
                                preset_even,
                                "균등 분배",
                                (
                                    each + (1 if remainder > 0 else 0),
                                    each + (1 if remainder > 1 else 0),
                                    each,
                                ),
                                "even",
                            )
                        )
                        for column, label, values, key_suffix in presets:
                            with column:
                                if st.button(
                                    label,
                                    key=f"point_preset_{selected_slot.index}_{key_suffix}",
                                    use_container_width=True,
                                ):
                                    selected_slot.set_crew_points(*values)
                                    st.session_state[point_keys["atk"]] = (
                                        selected_slot.crew_atk_pts
                                    )
                                    st.session_state[point_keys["def"]] = (
                                        selected_slot.crew_def_pts
                                    )
                                    st.session_state[point_keys["prod"]] = (
                                        selected_slot.crew_prod_pts
                                    )
                                    st.rerun()
                else:
                    st.info(
                        "승무원을 배치하면 레벨과 스탯 포인트 배분이 활성화됩니다."
                    )

    # --------------------------------------------------------------------------
    # RIGHT: Enemy army + run engine
    # --------------------------------------------------------------------------
    with right_column:
        with st.container(border=True):
            st.markdown(
                '<div class="group-title">👾 적 군단 선택 & 전투 실행</div>',
                unsafe_allow_html=True,
            )
            area_options = [None] + list(battle_areas_map.keys())
            selected_area = st.selectbox(
                "전투 구역 (BattleArea)",
                area_options,
                key="battle_area_selector",
                format_func=lambda item: (
                    "-- 프리셋 선택 --"
                    if item is None
                    else f"{item} [{battle_areas_map[item].get('battleLevelId') or ''}]"
                ),
            )
            if st.button(
                "선택 프리셋 적용",
                key="apply_battle_area",
                use_container_width=True,
            ):
                if selected_area is None:
                    st.warning("적 군단 프리셋을 선택하세요.")
                else:
                    loaded_count = apply_battle_area(
                        selected_area,
                        battle_areas_map,
                        monsters_map,
                        loader,
                        enemy_config,
                    )
                    set_flash(
                        "success",
                        f"{selected_area} 프리셋에서 몬스터 {loaded_count}마리를 불러왔습니다.",
                    )
                    st.rerun()

            st.markdown(
                '<div class="section-caption">몬스터 목록 (ID / Name / 레벨 / Area)</div>',
                unsafe_allow_html=True,
            )
            monster_query = st.text_input(
                "몬스터 검색",
                key="monster_search",
                placeholder="검색어를 입력하세요...",
                label_visibility="collapsed",
            )
            monster_rows = loader.get_sheet_data("MonsterData")
            monster_frame = pd.DataFrame(monster_rows)
            display_columns = [
                column
                for column in [
                    "monsterId",
                    "monsterName",
                    "monsterLv",
                    "monsterUseArea",
                ]
                if column in monster_frame.columns
            ]
            if monster_query and not monster_frame.empty:
                mask = monster_frame.astype(str).apply(
                    lambda column: column.str.contains(
                        monster_query, case=False, na=False
                    )
                )
                monster_frame = monster_frame[mask.any(axis=1)]
            st.dataframe(
                monster_frame[display_columns]
                if display_columns
                else monster_frame,
                use_container_width=True,
                height=180,
                hide_index=True,
            )

            filtered_monster_ids = [
                monster_id
                for monster_id in monster_frame.get("monsterId", pd.Series()).tolist()
                if monster_id in monsters_map
            ]
            if not filtered_monster_ids:
                filtered_monster_ids = list(monsters_map.keys())
            add_enemy_left, add_enemy_count, add_enemy_button = st.columns(
                [2.4, 0.8, 1]
            )
            with add_enemy_left:
                selected_monster_id = st.selectbox(
                    "추가할 몬스터",
                    filtered_monster_ids,
                    key="monster_to_add",
                    format_func=lambda item: (
                        f"{monsters_map[item].get('monsterName') or item} ({item})"
                    ),
                    label_visibility="collapsed",
                )
            with add_enemy_count:
                enemy_add_count = st.number_input(
                    "수량",
                    min_value=1,
                    max_value=100,
                    value=5,
                    step=1,
                    key="enemy_add_count",
                    label_visibility="collapsed",
                )
            with add_enemy_button:
                if st.button(
                    "적 추가 (+)", key="add_enemy", use_container_width=True
                ):
                    current_count = enemy_config.monster_counts.get(
                        selected_monster_id, 0
                    )
                    enemy_config.set_monster_count(
                        selected_monster_id, current_count + enemy_add_count
                    )
                    st.rerun()

            if enemy_config.monster_counts:
                for monster_id, count in list(
                    enemy_config.monster_counts.items()
                ):
                    monster = monsters_map.get(monster_id, {})
                    enemy_info, enemy_minus, enemy_count, enemy_plus = st.columns(
                        [3.3, 0.55, 0.8, 0.55]
                    )
                    with enemy_info:
                        st.caption(
                            f"👾 **{monster.get('monsterName') or monster_id}** "
                            f"({monster_id}) · 개당 HP:{monster.get('monsterHp') or 0}"
                        )
                    with enemy_minus:
                        if st.button(
                            "-",
                            key=f"enemy_minus_{monster_id}",
                            use_container_width=True,
                        ):
                            enemy_config.set_monster_count(
                                monster_id, max(0, count - 1)
                            )
                            st.rerun()
                    with enemy_count:
                        st.markdown(
                            f"<div style='text-align:center;font-weight:800;padding-top:6px'>{count}마리</div>",
                            unsafe_allow_html=True,
                        )
                    with enemy_plus:
                        if st.button(
                            "+",
                            key=f"enemy_plus_{monster_id}",
                            use_container_width=True,
                        ):
                            enemy_config.set_monster_count(monster_id, count + 1)
                            st.rerun()
            else:
                st.caption("편성된 적 몬스터가 없습니다.")

            enemy_summary = enemy_config.get_summary(monsters_map)
            st.markdown(
                '<div class="enemy-summary">적 군단 합산 스탯 · '
                f"총 {enemy_summary['total_count']}마리 | "
                f"HP: {enemy_summary['total_hp']:,.0f} | "
                f"Atk: {enemy_summary['total_power']:,.0f}</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "적 군단 전체 초기화",
                key="clear_enemy_army",
                use_container_width=True,
            ):
                enemy_config.clear()
                st.rerun()

            if st.button(
                "⚡ 전투 시뮬레이션 실행 (Run Engine & View Log)",
                key="run_battle",
                type="primary",
                use_container_width=True,
            ):
                if not train_config.locomotive and not train_config.coaches:
                    st.error("열차(기관차 및 객차)를 먼저 구성하세요.")
                elif not enemy_config.monster_counts:
                    st.error("전투 상대 적 몬스터를 1마리 이상 선택하세요.")
                else:
                    with st.spinner("전투 엔진을 실행하고 상세 로그를 생성하는 중입니다..."):
                        engine = BattleSimulationEngine(
                            train_config, enemy_config, monsters_map
                        )
                        summary = engine.run_full_simulation()
                    new_battle_result = {
                        "engine": engine,
                        "summary": summary,
                        "meta_text": combat_meta_text(
                            summary, train_config, enemy_config, monsters_map
                        ),
                    }
                    st.session_state.last_battle_result = ensure_battle_artifacts(
                        new_battle_result
                    )
                    st.success(
                        f"전투 완료: {summary['result']} · "
                        f"{summary['duration']}초 · 로그 {summary['log_count']:,}건"
                    )

            if st.session_state.last_battle_result:
                battle_result = st.session_state.last_battle_result
                summary = battle_result["summary"]
                result_color = (
                    "#34d399" if "VICTORY" in summary["result"] else "#f87171"
                )
                car_lines = []
                for car in summary["cars"]:
                    status = (
                        "💥 파괴됨"
                        if car["is_destroyed"]
                        else f"HP: {car['hp_left']}/{car['max_hp']}"
                    )
                    car_lines.append(f"• {car['name']}: {status}")
                st.markdown(
                    '<div class="result-box">'
                    f'<div style="font-weight:900;color:{result_color}">{esc(summary["result"])}</div>'
                    f"<div class='hint'>소요 {summary['duration']}초 · "
                    f"총 피해 {summary['total_damage_dealt']:,.1f} · "
                    f"처치 {summary['total_kills']} · 로그 {summary['log_count']:,}건</div>"
                    f'<div class="mono-box" style="margin-top:5px">{esc(chr(10).join(car_lines))}</div>'
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.caption("상세 이벤트 기록과 다운로드는 2번 전투 로그 탭에서 확인하세요.")

    if st.session_state.last_battle_result:
        battle_result = ensure_battle_artifacts(
            st.session_state.last_battle_result
        )
        battle_summary = battle_result["summary"]
        battle_engine = battle_result["engine"]
        car_frame = battle_result["car_frame"]
        turret_frame = battle_result["turret_frame"]
        event_frame = battle_result["event_frame"]

        st.markdown(
            '<div class="group-title">📊 전투 결과 상세 통계</div>',
            unsafe_allow_html=True,
        )
        result_kpi, duration_kpi, damage_kpi, kills_kpi, logs_kpi = st.columns(5)
        with result_kpi:
            st.metric("전투 결과", battle_summary["result"])
        with duration_kpi:
            st.metric("전투 시간", f"{battle_summary['duration']:.2f}초")
        with damage_kpi:
            st.metric(
                "총 가한 피해",
                f"{battle_summary['total_damage_dealt']:,.2f}",
            )
        with kills_kpi:
            st.metric(
                "몬스터 처치",
                f"{battle_summary['total_kills']} / {len(battle_engine.monsters)}",
            )
        with logs_kpi:
            st.metric("전투 이벤트", f"{battle_summary['log_count']:,}건")

        battle_chart_choice = st.selectbox(
            "전투 결과 그래프",
            [
                "🚃 칸별 HP 생존 현황",
                "🔫 포탑별 누적 피해",
                "📈 이벤트 발생 및 피해량",
            ],
            key="battle_chart_choice",
        )
        if battle_chart_choice == "🚃 칸별 HP 생존 현황":
            if car_frame.empty:
                st.info("그래프로 표시할 열차 칸 데이터가 없습니다.")
            else:
                car_chart = car_frame[["열차 칸", "남은 HP", "최대 HP"]].copy()
                car_chart["손실 HP"] = (
                    car_chart["최대 HP"] - car_chart["남은 HP"]
                ).clip(lower=0)
                st.bar_chart(
                    car_chart.set_index("열차 칸")[["남은 HP", "손실 HP"]],
                    height=320,
                )
        elif battle_chart_choice == "🔫 포탑별 누적 피해":
            if turret_frame.empty:
                st.info("그래프로 표시할 포탑 데이터가 없습니다.")
            else:
                turret_chart = turret_frame[
                    ["포탑", "누적 피해", "처치"]
                ].copy()
                st.bar_chart(
                    turret_chart.set_index("포탑")[["누적 피해"]],
                    height=320,
                )
        else:
            if event_frame.empty:
                st.info("그래프로 표시할 이벤트 데이터가 없습니다.")
            else:
                event_count_chart, event_damage_chart = st.columns(2)
                with event_count_chart:
                    st.caption("이벤트 발생 횟수")
                    st.bar_chart(
                        event_frame.set_index("이벤트")[["발생 횟수"]],
                        height=290,
                    )
                with event_damage_chart:
                    st.caption("이벤트별 총 피해량")
                    st.bar_chart(
                        event_frame.set_index("이벤트")[["총 피해량"]],
                        height=290,
                    )

        car_stats_tab, turret_stats_tab, event_stats_tab = st.tabs(
            [
                "🚃 칸별 생존 현황",
                "🔫 포탑별 전투 성과",
                "📈 이벤트 유형 집계",
            ]
        )
        with car_stats_tab:
            if car_frame.empty:
                st.info("표시할 열차 칸 결과가 없습니다.")
            else:
                st.dataframe(
                    car_frame,
                    use_container_width=True,
                    height=min(360, 78 + len(car_frame) * 36),
                    hide_index=True,
                )
        with turret_stats_tab:
            if turret_frame.empty:
                st.info("장착된 포탑이 없어 포탑별 성과가 없습니다.")
            else:
                st.dataframe(
                    turret_frame,
                    use_container_width=True,
                    height=min(420, 78 + len(turret_frame) * 36),
                    hide_index=True,
                )
        with event_stats_tab:
            if event_frame.empty:
                st.info("집계할 전투 이벤트가 없습니다.")
            else:
                st.dataframe(
                    event_frame,
                    use_container_width=True,
                    height=min(420, 78 + len(event_frame) * 36),
                    hide_index=True,
                )


# ==============================================================================
# TAB 2: COMBAT LOG
# ==============================================================================
with tab_log:
    st.markdown(
        '<div class="group-title">📋 전투 시뮬레이션 설정 및 결과 메타데이터 요약</div>',
        unsafe_allow_html=True,
    )
    if not st.session_state.last_battle_result:
        st.info(
            "1번 워크숍에서 전투 시뮬레이션을 실행하면 열차 구성, 적 구성 및 결과가 기록됩니다."
        )
    else:
        battle_result = ensure_battle_artifacts(
            st.session_state.last_battle_result
        )
        engine = battle_result["engine"]
        summary = battle_result["summary"]
        meta_text = battle_result["meta_text"]
        log_df = battle_result["log_df"]

        st.markdown(
            f'<div class="mono-box">{esc(meta_text)}</div>',
            unsafe_allow_html=True,
        )
        download_meta, download_excel, download_csv = st.columns([1, 1.35, 1.35])
        with download_meta:
            st.download_button(
                "📋 요약 텍스트 저장",
                data=meta_text.encode("utf-8-sig"),
                file_name="combat_log_summary.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with download_excel:
            st.download_button(
                "📊 엑셀 저장 (.xlsx · 시트 2개)",
                data=battle_result["excel_report"],
                file_name="combat_log_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with download_csv:
            st.download_button(
                "📄 CSV 다중 저장 (.zip · 파일 2개)",
                data=battle_result["csv_report"],
                file_name="combat_log_csv_files.zip",
                mime="application/zip",
                use_container_width=True,
            )

        log_search = st.text_input(
            "🔍 전투 로그 검색",
            key="combat_log_search",
            placeholder="이벤트, 공격자, 대상, 상세 내용을 검색하세요...",
        )
        filtered_log_df = log_df
        if log_search and not log_df.empty:
            mask = log_df.astype(str).apply(
                lambda column: column.str.contains(log_search, case=False, na=False)
            )
            filtered_log_df = log_df[mask.any(axis=1)]
        st.dataframe(
            filtered_log_df,
            use_container_width=True,
            height=510,
            hide_index=True,
        )
        st.caption(
            f"표시 {len(filtered_log_df):,}건 / 전체 {len(log_df):,}건의 전투 이벤트 로그"
        )


# ==============================================================================
# TAB 3: RAW DATA INSPECTOR
# ==============================================================================
with tab_inspector:
    sheet_names = list(loader.data.keys())
    if not sheet_names:
        st.warning("로드된 엑셀 시트가 없습니다.")
    else:
        selected_sheet_name = st.selectbox(
            "확인할 데이터 시트",
            sheet_names,
            key="inspector_sheet_selector",
            format_func=lambda sheet_name: (
                f"{sheet_name} ({len(loader.get_sheet_data(sheet_name)):,}건)"
            ),
        )
        records = loader.get_sheet_data(selected_sheet_name)
        frame = pd.DataFrame(records)
        query = st.text_input(
            "🔍 검색",
            key="inspector_search",
            placeholder="선택한 시트에서 검색할 내용을 입력하세요...",
        )
        if query and not frame.empty:
            mask = frame.astype(str).apply(
                lambda column: column.str.contains(
                    query, case=False, na=False
                )
            )
            frame = frame[mask.any(axis=1)]
        st.dataframe(
            arrow_safe_dataframe(frame),
            use_container_width=True,
            height=610,
            hide_index=True,
        )
        st.caption(
            f"표시 {len(frame):,}건 / 전체 {len(records):,}건 · "
            f"컬럼 {len(loader.get_sheet_columns(selected_sheet_name))}개 · "
            "선택한 시트 1개만 렌더링하여 화면 부하를 줄였습니다."
        )


# ==============================================================================
# TAB 4: CREW GROWTH MONTE CARLO
# ==============================================================================
with tab_crew:
    crew_left, crew_right = st.columns([380, 900], gap="small")

    with crew_left:
        with st.container(border=True):
            st.markdown(
                '<div class="group-title">👨‍✈️ 1. 시뮬레이션 대상 승무원 선택</div>',
                unsafe_allow_html=True,
            )
            crew_ids = list(crews_map.keys())
            selected_sim_crew_id = st.selectbox(
                "시뮬레이션 대상 승무원",
                crew_ids,
                key="simulation_crew",
                format_func=lambda item: (
                    f"[{crews_map[item].get('crewType') or '일반'}] "
                    f"{crews_map[item].get('crewName') or item} ({item})"
                ),
            )
            sim_crew = crews_map[selected_sim_crew_id]
            sim_crew_name = (
                sim_crew.get("crewName") or selected_sim_crew_id
            )
            sim_crew_type = str(sim_crew.get("crewType") or "일반").strip()
            crew_info = (
                f"• 승무원: {sim_crew_name} (ID: {selected_sim_crew_id})\n"
                f"• 유형: {sim_crew_type}\n"
                f"• 기본 스탯: 대지위력:{sim_crew.get('crewLandpower') or 0} | "
                f"대공위력:{sim_crew.get('crewFlypower') or 0} | "
                f"Def:{sim_crew.get('crewDef') or 0} | "
                f"생산:{float(sim_crew.get('crewProduct') or 0):.1f} | "
                f"공업:{float(sim_crew.get('crewIndustry') or 0):.1f}"
            )
            st.markdown(
                f'<div class="mono-box">{esc(crew_info)}</div>',
                unsafe_allow_html=True,
            )

        with st.container(border=True):
            st.markdown(
                '<div class="group-title">🎯 2. 주스탯(유형별) 및 레벨업 성장 확률 설정</div>',
                unsafe_allow_html=True,
            )
            crew_id_text = str(selected_sim_crew_id)
            if (
                "전투" in sim_crew_type
                or "공격" in sim_crew_type
                or "Batt" in crew_id_text
            ):
                primary_stat = "atk"
                primary_label = "⚔️ 공격력 (유형: 전투형)"
            elif "방어" in sim_crew_type or "Def" in crew_id_text:
                primary_stat = "def"
                primary_label = "🛡️ 방어력 (유형: 방어형)"
            elif (
                "생산" in sim_crew_type
                or "공업" in sim_crew_type
                or "Prod" in crew_id_text
            ):
                primary_stat = "prod"
                primary_label = "🏭 생산/공업 (유형: 생산형)"
            else:
                primary_stat = "even"
                primary_label = "⚖️ 밸런스/균등형 (기타)"

            st.markdown(
                f'<div class="selected-title">🎯 주스탯: {primary_label}</div>',
                unsafe_allow_html=True,
            )
            main_probability = st.number_input(
                "⭐ 주스탯 확률 설정 (%)",
                min_value=0.0,
                max_value=100.0,
                value=50.0,
                step=5.0,
                key="crew_main_probability",
            )
            preset_columns = st.columns(6)
            for preset_column, probability in zip(
                preset_columns, [40, 50, 60, 70, 80, 100]
            ):
                with preset_column:
                    if st.button(
                        f"{probability}%",
                        key=f"probability_preset_{probability}",
                        use_container_width=True,
                    ):
                        st.session_state.crew_main_probability = float(probability)
                        st.rerun()

            sub_probability = max(0.0, (100.0 - main_probability) / 2.0)
            if primary_stat == "atk":
                probability_atk, probability_def, probability_prod = (
                    main_probability,
                    sub_probability,
                    sub_probability,
                )
            elif primary_stat == "def":
                probability_atk, probability_def, probability_prod = (
                    sub_probability,
                    main_probability,
                    sub_probability,
                )
            elif primary_stat == "prod":
                probability_atk, probability_def, probability_prod = (
                    sub_probability,
                    sub_probability,
                    main_probability,
                )
            else:
                probability_atk, probability_def, probability_prod = (
                    main_probability,
                    sub_probability,
                    sub_probability,
                )

            stat_cards(
                [
                    (
                        "⚔️ 공격력 확률",
                        f"{probability_atk:.1f}%"
                        + (" (⭐주스탯)" if primary_stat == "atk" else " (보조)"),
                        "#f59e0b",
                    ),
                    (
                        "🛡️ 방어력 확률",
                        f"{probability_def:.1f}%"
                        + (" (⭐주스탯)" if primary_stat == "def" else " (보조)"),
                        "#38bdf8",
                    ),
                    (
                        "🏭 생산/공업 확률",
                        f"{probability_prod:.1f}%"
                        + (" (⭐주스탯)" if primary_stat == "prod" else " (보조)"),
                        "#10b981",
                    ),
                    (
                        "확률 합계",
                        f"{probability_atk + probability_def + probability_prod:.1f}%",
                        "#a78bfa",
                    ),
                ]
            )
            st.caption("규칙: 나머지 2개 보조스탯 확률 = (100% - 주스탯%) ÷ 2")

        with st.container(border=True):
            st.markdown(
                '<div class="group-title">⚙️ 3. 시뮬레이션 파라미터</div>',
                unsafe_allow_html=True,
            )
            target_level = st.number_input(
                "목표 레벨 (2~50)",
                min_value=2,
                max_value=50,
                value=50,
                step=1,
                key="crew_target_level",
            )
            growth_rolls = target_level - 1
            st.caption(f"= {growth_rolls}회 성장")
            point_rate = st.number_input(
                "1pt당 스탯 증가율 (%)",
                min_value=0.1,
                max_value=100.0,
                value=1.0,
                step=0.5,
                key="crew_sim_point_rate",
            )
            trial_count = st.number_input(
                "시뮬레이션 반복 횟수",
                min_value=1,
                max_value=100000,
                value=1000,
                step=100,
                key="crew_trial_count",
            )
            trial_presets = st.columns(4)
            for preset_column, trials in zip(
                trial_presets, [1, 100, 1000, 10000]
            ):
                with preset_column:
                    if st.button(
                        f"{trials:,}회",
                        key=f"trial_preset_{trials}",
                        use_container_width=True,
                    ):
                        st.session_state.crew_trial_count = trials
                        st.rerun()

        if st.button(
            "🎲 랜덤 성장 시뮬레이션 실행 (Run)",
            key="run_crew_simulation",
            type="primary",
            use_container_width=True,
        ):
            probability_sum = (
                probability_atk + probability_def + probability_prod
            )
            weight_atk = probability_atk / probability_sum
            weight_def = probability_def / probability_sum
            weight_prod = probability_prod / probability_sum

            attack_results = []
            defense_results = []
            production_results = []
            single_roll_logs = []
            trials_int = int(trial_count)

            with st.spinner(
                f"{trials_int:,}회 몬테카를로 시뮬레이션을 실행하는 중입니다..."
            ):
                if trials_int == 1:
                    attack_count = 0
                    defense_count = 0
                    production_count = 0
                    for roll_index in range(growth_rolls):
                        roll_value = random.random()
                        if roll_value < weight_atk:
                            attack_count += 1
                            hit_name = "⚔️ 공격력"
                        elif roll_value < weight_atk + weight_def:
                            defense_count += 1
                            hit_name = "🛡️ 방어력"
                        else:
                            production_count += 1
                            hit_name = "🏭 생산/공업"
                        single_roll_logs.append(
                            f"[Lv. {roll_index + 2:2d}] 🎲 주사위 "
                            f"{roll_value * 100:5.1f}% ➔ {hit_name} +1pt 획득 | "
                            f"현재 누적 (⚔️:{attack_count}pt, "
                            f"🛡️:{defense_count}pt, 🏭:{production_count}pt)"
                        )
                    attack_results.append(attack_count)
                    defense_results.append(defense_count)
                    production_results.append(production_count)
                else:
                    # NumPy's multinomial sampler replaces up to 4.9 million
                    # Python-level random iterations with one vectorized call.
                    probability_weights = np.array(
                        [weight_atk, weight_def, weight_prod], dtype=float
                    )
                    probability_weights /= probability_weights.sum()
                    samples = np.random.default_rng().multinomial(
                        growth_rolls,
                        probability_weights,
                        size=trials_int,
                    )
                    attack_results = samples[:, 0].tolist()
                    defense_results = samples[:, 1].tolist()
                    production_results = samples[:, 2].tolist()

            st.session_state.last_crew_sim_result = {
                "crew": sim_crew,
                "target_level": int(target_level),
                "rolls": growth_rolls,
                "trials": trials_int,
                "rate": float(point_rate),
                "probabilities": (
                    probability_atk,
                    probability_def,
                    probability_prod,
                ),
                "attack": attack_results,
                "defense": defense_results,
                "production": production_results,
                "single_logs": single_roll_logs,
            }
            st.rerun()

        if st.button(
            "🎯 시뮬레이션 결과 워크숍 적용 (동일 승무원 일괄 동기화)",
            key="apply_crew_simulation",
            use_container_width=True,
        ):
            result = st.session_state.last_crew_sim_result
            if not result:
                st.warning("먼저 시뮬레이션을 1회 이상 실행하세요.")
            else:
                result_crew_id = result["crew"].get("crewId")
                matching_slots = [
                    slot
                    for slot in train_config.coaches
                    if slot.crew and slot.crew.get("crewId") == result_crew_id
                ]
                if not matching_slots:
                    st.warning(
                        f"현재 열차에 [{result['crew'].get('crewName')}] 승무원이 배치되어 있지 않습니다."
                    )
                else:
                    sample_attack = result["attack"][0]
                    sample_defense = result["defense"][0]
                    sample_production = result["production"][0]
                    for slot in matching_slots:
                        slot.set_crew_level(result["target_level"])
                        slot.set_crew_points(
                            sample_attack, sample_defense, sample_production
                        )
                    st.session_state.selected_coach_idx = matching_slots[0].index
                    st.session_state.pending_coach_selection = (
                        coach_selector_token(matching_slots[0].index)
                    )
                    set_flash(
                        "success",
                        f"[{result['crew'].get('crewName')}] 승무원이 탑승한 "
                        f"{len(matching_slots)}개 객차에 Lv.{result['target_level']} / "
                        f"공격 {sample_attack}pt / 방어 {sample_defense}pt / "
                        f"생산 {sample_production}pt를 적용했습니다.",
                    )
                    st.rerun()

    with crew_right:
        result = st.session_state.last_crew_sim_result
        if not result:
            st.info(
                "좌측에서 파라미터를 설정하고 랜덤 성장 시뮬레이션을 실행하면 결과가 표시됩니다."
            )
        else:
            attack_results = result["attack"]
            defense_results = result["defense"]
            production_results = result["production"]
            trials = result["trials"]
            rolls = result["rolls"]
            rate = result["rate"]
            probability_atk, probability_def, probability_prod = result[
                "probabilities"
            ]

            average_attack = sum(attack_results) / trials
            average_defense = sum(defense_results) / trials
            average_production = sum(production_results) / trials
            min_attack, max_attack = min(attack_results), max(attack_results)
            min_defense, max_defense = min(defense_results), max(defense_results)
            min_production, max_production = (
                min(production_results),
                max(production_results),
            )
            std_attack = math.sqrt(
                sum((value - average_attack) ** 2 for value in attack_results)
                / trials
            )
            std_defense = math.sqrt(
                sum((value - average_defense) ** 2 for value in defense_results)
                / trials
            )
            std_production = math.sqrt(
                sum(
                    (value - average_production) ** 2
                    for value in production_results
                )
                / trials
            )
            sorted_attack = sorted(attack_results)
            sorted_defense = sorted(defense_results)
            sorted_production = sorted(production_results)

            dashboard_attack, dashboard_defense, dashboard_production = st.columns(3)
            with dashboard_attack:
                st.metric(
                    "⚔️ 공격력 포인트 기대값",
                    f"{average_attack:.2f} pt",
                    f"{average_attack / rolls * 100:.1f}% · {min_attack}~{max_attack}pt",
                )
            with dashboard_defense:
                st.metric(
                    "🛡️ 방어력 포인트 기대값",
                    f"{average_defense:.2f} pt",
                    f"{average_defense / rolls * 100:.1f}% · {min_defense}~{max_defense}pt",
                )
            with dashboard_production:
                st.metric(
                    "🏭 생산/공업 포인트 기대값",
                    f"{average_production:.2f} pt",
                    f"{average_production / rolls * 100:.1f}% · {min_production}~{max_production}pt",
                )

            distribution_specs = [
                (
                    "⚔️ 공격력",
                    probability_atk,
                    average_attack,
                    std_attack,
                    min_attack,
                    max_attack,
                    sorted_attack,
                ),
                (
                    "🛡️ 방어력",
                    probability_def,
                    average_defense,
                    std_defense,
                    min_defense,
                    max_defense,
                    sorted_defense,
                ),
                (
                    "🏭 생산/공업",
                    probability_prod,
                    average_production,
                    std_production,
                    min_production,
                    max_production,
                    sorted_production,
                ),
            ]
            distribution_frame = pd.DataFrame(
                [
                    {
                        "성장 스탯": stat_name,
                        "설정 확률": f"{probability:.1f}%",
                        "이론 기대값": f"{rolls * probability / 100:.2f} pt",
                        "실제 평균": f"{average:.2f} pt",
                        "기대값 오차": f"{average - rolls * probability / 100:+.2f} pt",
                        "표준편차": f"{std_dev:.2f}",
                        "최소": min_value,
                        "하위 10%": percentile(sorted_values, 0.10),
                        "하위 25%": percentile(sorted_values, 0.25),
                        "중앙값": percentile(sorted_values, 0.50),
                        "상위 25%": percentile(sorted_values, 0.75),
                        "상위 10%": percentile(sorted_values, 0.90),
                        "최대": max_value,
                    }
                    for (
                        stat_name,
                        probability,
                        average,
                        std_dev,
                        min_value,
                        max_value,
                        sorted_values,
                    ) in distribution_specs
                ]
            )
            st.markdown(
                '<div class="selected-title">📈 성장 포인트 확률·편차·백분위 통계표</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(
                distribution_frame,
                use_container_width=True,
                height=185,
                hide_index=True,
            )

            result_crew = result["crew"]
            base_land = float(result_crew.get("crewLandpower") or 0)
            base_fly = float(result_crew.get("crewFlypower") or 0)
            base_defense = float(result_crew.get("crewDef") or 0)
            base_product = float(result_crew.get("crewProduct") or 0)
            base_industry = float(result_crew.get("crewIndustry") or 0)
            attack_multiplier = 1 + average_attack * rate / 100
            defense_multiplier = 1 + average_defense * rate / 100
            production_multiplier = 1 + average_production * rate / 100

            stat_rows = [
                (
                    "⚔️ 대지 위력 (Landpower)",
                    base_land,
                    average_attack,
                    attack_multiplier,
                    base_land * attack_multiplier,
                    base_land * (1 + min_attack * rate / 100),
                    base_land * (1 + max_attack * rate / 100),
                ),
                (
                    "🏹 대공 위력 (Flypower)",
                    base_fly,
                    average_attack,
                    attack_multiplier,
                    base_fly * attack_multiplier,
                    base_fly * (1 + min_attack * rate / 100),
                    base_fly * (1 + max_attack * rate / 100),
                ),
                (
                    "🛡️ 방어력 (Def)",
                    base_defense,
                    average_defense,
                    defense_multiplier,
                    base_defense * defense_multiplier,
                    base_defense * (1 + min_defense * rate / 100),
                    base_defense * (1 + max_defense * rate / 100),
                ),
                (
                    "🌾 생산력 (Product)",
                    base_product,
                    average_production,
                    production_multiplier,
                    base_product * production_multiplier,
                    base_product * (1 + min_production * rate / 100),
                    base_product * (1 + max_production * rate / 100),
                ),
                (
                    "⚙️ 공업력 (Industry)",
                    base_industry,
                    average_production,
                    production_multiplier,
                    base_industry * production_multiplier,
                    base_industry * (1 + min_production * rate / 100),
                    base_industry * (1 + max_production * rate / 100),
                ),
            ]
            stats_frame = pd.DataFrame(
                [
                    {
                        "스탯 항목": name,
                        "기본 수치(Base)": f"{base:.1f}",
                        "평균 획득 포인트": f"{points:.2f} pt",
                        "평균 배율(Mult)": f"{multiplier:.3f}x (+{(multiplier - 1) * 100:.1f}%)",
                        "평균 최종 스탯": f"{average_stat:.2f}",
                        "최저 결과(Min)": f"{min_stat:.2f}",
                        "최고 결과(Max)": f"{max_stat:.2f}",
                    }
                    for (
                        name,
                        base,
                        points,
                        multiplier,
                        average_stat,
                        min_stat,
                        max_stat,
                    ) in stat_rows
                ]
            )
            st.markdown(
                '<div class="selected-title">📊 승무원 레벨업 최종 스탯 기대값 및 최소/최대 범위 분석</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(
                stats_frame,
                use_container_width=True,
                height=215,
                hide_index=True,
            )

            st.markdown(
                '<div class="selected-title">📊 승무원 성장 결과 그래프</div>',
                unsafe_allow_html=True,
            )
            crew_chart_choice = st.selectbox(
                "승무원 통계 그래프",
                [
                    "포인트 획득 분포",
                    "이론 기대값과 실제 평균",
                    "기본·평균·최저·최고 최종 스탯",
                ],
                key="crew_chart_choice",
                label_visibility="collapsed",
            )
            if crew_chart_choice == "포인트 획득 분포":
                point_distribution_chart = pd.concat(
                    [
                        pd.Series(attack_results)
                        .value_counts()
                        .rename("공격력"),
                        pd.Series(defense_results)
                        .value_counts()
                        .rename("방어력"),
                        pd.Series(production_results)
                        .value_counts()
                        .rename("생산/공업"),
                    ],
                    axis=1,
                ).fillna(0)
                point_distribution_chart = point_distribution_chart.sort_index()
                point_distribution_chart.index.name = "획득 포인트"
                st.bar_chart(
                    point_distribution_chart.astype(int),
                    height=340,
                )
            elif crew_chart_choice == "이론 기대값과 실제 평균":
                expectation_chart = pd.DataFrame(
                    {
                        "이론 기대 포인트": [
                            rolls * probability_atk / 100,
                            rolls * probability_def / 100,
                            rolls * probability_prod / 100,
                        ],
                        "실제 평균 포인트": [
                            average_attack,
                            average_defense,
                            average_production,
                        ],
                    },
                    index=["공격력", "방어력", "생산/공업"],
                )
                st.bar_chart(expectation_chart, height=340)
            else:
                final_stat_chart = pd.DataFrame(
                    [
                        {
                            "스탯": name,
                            "기본": base,
                            "최저": min_stat,
                            "평균": average_stat,
                            "최고": max_stat,
                        }
                        for (
                            name,
                            base,
                            _points,
                            _multiplier,
                            average_stat,
                            min_stat,
                            max_stat,
                        ) in stat_rows
                    ]
                ).set_index("스탯")
                st.bar_chart(final_stat_chart, height=360)

            analytics_lines = [
                "================================================================================",
                "📊 [승무원 레벨업 몬테카를로 랜덤 성장 통계 보고서]",
                "================================================================================",
                f"• 대상 승무원: {result_crew.get('crewName')} [{result_crew.get('crewType')}] "
                f"(ID: {result_crew.get('crewId')})",
                f"• 목표 레벨: Lv.{result['target_level']} (총 {rolls}회 스탯 성장 롤)",
                f"• 총 시뮬레이션 반복 횟수: {trials:,}회 | 1pt당 증가율: {rate:.1f}%",
                f"• 설정 확률: ⚔️공격 {probability_atk:.1f}% | "
                f"🛡️방어 {probability_def:.1f}% | 🏭생산/공업 {probability_prod:.1f}%",
                "",
                "--------------------------------------------------------------------------------",
                "📈 [포인트 획득 분포 통계 (Percentiles & Deviation)]",
                "--------------------------------------------------------------------------------",
                "스탯 항목         평균(Mean)    표준편차(σ)   하위10%  하위25%  중앙값  상위25%  상위10%",
                f"⚔️ 공격력 포인트   {average_attack:6.2f} pt   ±{std_attack:5.2f} pt"
                f"   {percentile(sorted_attack, .10):4d}    {percentile(sorted_attack, .25):4d}"
                f"    {percentile(sorted_attack, .50):4d}    {percentile(sorted_attack, .75):4d}"
                f"    {percentile(sorted_attack, .90):4d}",
                f"🛡️ 방어력 포인트   {average_defense:6.2f} pt   ±{std_defense:5.2f} pt"
                f"   {percentile(sorted_defense, .10):4d}    {percentile(sorted_defense, .25):4d}"
                f"    {percentile(sorted_defense, .50):4d}    {percentile(sorted_defense, .75):4d}"
                f"    {percentile(sorted_defense, .90):4d}",
                f"🏭 생산/공업 포인트 {average_production:6.2f} pt   ±{std_production:5.2f} pt"
                f"   {percentile(sorted_production, .10):4d}    {percentile(sorted_production, .25):4d}"
                f"    {percentile(sorted_production, .50):4d}    {percentile(sorted_production, .75):4d}"
                f"    {percentile(sorted_production, .90):4d}",
                "",
                "--------------------------------------------------------------------------------",
                "💡 [밸런스 기획자 코멘트 및 분석 요약]",
                "--------------------------------------------------------------------------------",
                f"• 공격력 포인트 기대값은 {rolls}포인트 중 {average_attack:.1f}pt"
                f"({average_attack / rolls * 100:.1f}%)로 이론 확률({probability_atk:.1f}%)에 수렴합니다.",
                f"• 상위 10% 공격 성장 결과는 {percentile(sorted_attack, .90)}pt이며 "
                f"공격 계열 스탯이 +{percentile(sorted_attack, .90) * rate:.1f}% 증가합니다.",
                f"• 하위 10% 공격 성장 결과는 {percentile(sorted_attack, .10)}pt이며 "
                f"공격 계열 스탯이 +{percentile(sorted_attack, .10) * rate:.1f}% 증가합니다.",
            ]

            analytics_tab, rolls_tab = st.tabs(
                [
                    "📈 상세 통계 및 백분위 분포 분석 (Percentiles)",
                    "📜 레벨업 주사위 판정 로그 / 회차별 결과",
                ]
            )
            with analytics_tab:
                st.code("\n".join(analytics_lines), language="text")
            with rolls_tab:
                if trials == 1:
                    roll_lines = [
                        f"🎲 [1회 단일 레벨업 주사위 판정 상세 진행 로그 "
                        f"(Lv.1 ➔ Lv.{result['target_level']})]",
                        "--------------------------------------------------------------------------------",
                    ] + result["single_logs"]
                else:
                    max_attack_index = attack_results.index(max_attack)
                    max_defense_index = defense_results.index(max_defense)
                    max_production_index = production_results.index(max_production)
                    roll_lines = [
                        f"📋 [총 {trials:,}회 시뮬레이션 중 상위/하위 대표 회차 샘플]",
                        "--------------------------------------------------------------------------------",
                        f"• 최고 공격력 회차: ⚔️공격 {max_attack}pt, "
                        f"🛡️방어 {defense_results[max_attack_index]}pt, "
                        f"🏭생산 {production_results[max_attack_index]}pt",
                        f"• 최고 방어력 회차: ⚔️공격 {attack_results[max_defense_index]}pt, "
                        f"🛡️방어 {max_defense}pt, "
                        f"🏭생산 {production_results[max_defense_index]}pt",
                        f"• 최고 생산력 회차: ⚔️공격 {attack_results[max_production_index]}pt, "
                        f"🛡️방어 {defense_results[max_production_index]}pt, "
                        f"🏭생산 {max_production}pt",
                        "--------------------------------------------------------------------------------",
                        "📌 [최근 30개 시뮬레이션 회차별 결과]",
                    ]
                    for index in range(min(30, trials)):
                        roll_lines.append(
                            f"  Trial #{index + 1:04d}: "
                            f"⚔️공격 {attack_results[index]:2d}pt "
                            f"({attack_results[index] / rolls * 100:4.1f}%) | "
                            f"🛡️방어 {defense_results[index]:2d}pt "
                            f"({defense_results[index] / rolls * 100:4.1f}%) | "
                            f"🏭생산 {production_results[index]:2d}pt "
                            f"({production_results[index] / rolls * 100:4.1f}%)"
                        )
                st.code("\n".join(roll_lines), language="text")

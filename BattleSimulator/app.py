import os
import sys
import random
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from data_loader import DataLoader
from models import TrainConfig, CoachSlot, TurretConfig, EnemyGroupConfig
from battle_engine import BattleSimulationEngine

# ==============================================================================
# PAGE CONFIGURATION & DARK STUDIO THEME
# ==============================================================================
st.set_page_config(
    page_title="Siecletrain Visual Battle Simulator",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Global Base */
    .stApp {
        background-color: #0f172a;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Top Header Banner */
    .header-banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #4f46e5;
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-title {
        font-size: 22px;
        font-weight: 800;
        color: #a5b4fc;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-desc {
        font-size: 12px;
        color: #94a3b8;
        margin: 2px 0 0 0;
    }

    /* Section Containers */
    .section-head {
        font-size: 15px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Info Badge Grid */
    .info-card {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 12px;
        margin: 6px 0 10px 0;
    }
    .info-card-title {
        font-size: 13px;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 6px;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 3px;
    }
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(115px, 1fr));
        gap: 6px;
    }
    .info-item {
        font-size: 11px;
        background-color: #1e293b;
        padding: 4px 6px;
        border-radius: 4px;
        border: 1px solid #334155;
    }
    .info-label { color: #94a3b8; }
    .info-val { color: #f8fafc; font-weight: 700; }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 700;
        border-radius: 8px 8px 0 0;
        background-color: #1e293b;
        color: #94a3b8;
        border: 1px solid #334155;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        border-color: #6366f1 !important;
    }

    /* Buttons */
    div.stButton > button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "loader" not in st.session_state:
    st.session_state.loader = DataLoader()

if "train_config" not in st.session_state:
    st.session_state.train_config = TrainConfig()

if "enemy_config" not in st.session_state:
    st.session_state.enemy_config = EnemyGroupConfig()

if "selected_coach_idx" not in st.session_state:
    st.session_state.selected_coach_idx = 0

if "last_battle_result" not in st.session_state:
    st.session_state.last_battle_result = None

if "last_crew_sim_result" not in st.session_state:
    st.session_state.last_crew_sim_result = None

loader = st.session_state.loader
train_config = st.session_state.train_config
enemy_config = st.session_state.enemy_config

# Helper data maps
locomotives_map = {r["locomotiveId"]: r for r in loader.get_sheet_data("Locomotive") if r.get("locomotiveId")}
couches_map = {r["couchId"]: r for r in loader.get_sheet_data("Couch") if r.get("couchId")}
engines_map = {r["engineId"]: r for r in loader.get_sheet_data("Engine") if r.get("engineId")}
generators_map = {r["generatorId"]: r for r in loader.get_sheet_data("Generator") if r.get("generatorId")}
brakes_map = {r["breakId"]: r for r in loader.get_sheet_data("Break") if r.get("breakId")}
crews_map = {r["crewId"]: r for r in loader.get_sheet_data("Crew") if r.get("crewId")}
weapons_map = {r["weaponId"]: r for r in loader.get_sheet_data("Weapon") if r.get("weaponId")}
monsters_map = {r["monsterId"]: r for r in loader.get_sheet_data("MonsterData") if r.get("monsterId")}
battle_areas_map = {r["battleAreaId"]: r for r in loader.get_sheet_data("BattleArea") if r.get("battleAreaId")}

# Default Locomotive setup
if not train_config.locomotive and locomotives_map:
    first_loco = list(locomotives_map.values())[0]
    train_config.locomotive = first_loco

# ==============================================================================
# TOP APP HEADER
# ==============================================================================
col_h1, col_h2 = st.columns([3.5, 1])
with col_h1:
    st.markdown("""
    <div class="header-banner">
        <div>
            <p class="header-title">🚂 SIECLETRAIN VISUAL BATTLE SIMULATOR</p>
            <p class="header-desc">데이터 기반 쿼터뷰 열차 전투 밸런스 및 승무원 성장 시뮬레이터 (Studio Web Edition)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    if st.button("🔄 엑셀 데이터 새로고침", use_container_width=True):
        loader.reload_all_data()
        st.success("엑셀 데이터를 성공적으로 다시 불러왔습니다!")
        st.rerun()

# 4 Main Tabs matching Desktop GUI
tab1, tab2, tab3, tab4 = st.tabs([
    "🚂 1. 통합 열차 & 적 세팅 워크숍",
    "📋 2. 전투 로그 시트 (Combat Log)",
    "🔍 3. Raw 데이터 검증 (Inspector)",
    "🎲 4. 승무원 레벨업 랜덤 성장 시뮬레이터"
])

# ==============================================================================
# TAB 1: 🚂 워크숍 (Workshop)
# ==============================================================================
with tab1:
    stats = train_config.calculate_stats()
    loco_hp = float(train_config.locomotive.get("locomotiveHp") or 0.0) if train_config.locomotive else 0.0
    gen_shield = float(train_config.generator.get("generatorShieldUp") or 0.0) if train_config.generator else 0.0
    crew_prod = sum(c.get_effective_crew_stats()["product"] for c in train_config.coaches)
    crew_ind = sum(c.get_effective_crew_stats()["industry"] for c in train_config.coaches)

    # 1. Clickable Visual Train Blueprint (상단 실시간 조감도 & 클릭 선택)
    with st.container(border=True):
        st.markdown("<div style='font-size:13px; font-weight:700; color:#94a3b8; margin-bottom:6px;'>🚂 실시간 열차 조감도 (칸을 클릭하면 해당 객차의 세부 설정으로 즉시 전환됩니다)</div>", unsafe_allow_html=True)

        total_nodes = 1 + len(train_config.coaches)
        bp_cols = st.columns(total_nodes)

        # Locomotive Block Button
        with bp_cols[0]:
            is_loco_sel = (st.session_state.selected_coach_idx == 0)
            loco_nm = train_config.locomotive.get("locomotiveName", "기관차") if train_config.locomotive else "기관차"
            lt_cnt = len(train_config.locomotive_turrets)
            btn_loco_type = "primary" if is_loco_sel else "secondary"
            if st.button(f"🚂 {loco_nm}\n(HP:{loco_hp:.0f} | 🛡️:{stats['locomotive_def']:.0f})\n포탑:{lt_cnt}/2", key="bp_btn_loco", type=btn_loco_type, use_container_width=True):
                st.session_state.selected_coach_idx = 0
                st.rerun()

        # Coach Block Buttons
        for idx, c_slot in enumerate(train_config.coaches):
            with bp_cols[idx + 1]:
                is_c_sel = (st.session_state.selected_coach_idx == (idx + 1))
                c_nm = c_slot.get_name()
                cr_nm = c_slot.crew.get("crewName") if c_slot.crew else "미배치"
                cr_lvl = f"Lv.{c_slot.crew_level}" if c_slot.crew else ""
                t_cnt = len(c_slot.turrets)
                c_hp = c_slot.get_couch_stats()["hp"]
                c_def = c_slot.get_total_coach_def()
                btn_c_type = "primary" if is_c_sel else "secondary"

                if st.button(f"🚃 #{c_slot.index} {c_nm}\n(HP:{c_hp:.0f}|Def:{c_def:.0f})\n{cr_nm} {cr_lvl} [T:{t_cnt}/4]", key=f"bp_btn_c_{idx}", type=btn_c_type, use_container_width=True):
                    st.session_state.selected_coach_idx = idx + 1
                    st.rerun()

    # Top KPI Metrics Cards
    k_col1, k_col2, k_col3, k_col4, k_col5 = st.columns(5)
    with k_col1:
        st.metric("🚂 기관차 HP / Def", f"{loco_hp:.0f} / {stats['locomotive_def']:.0f}", loco_nm)
    with k_col2:
        st.metric("🚃 연결 객차 수", f"{stats['current_couches']} / {stats['max_couches']} 칸", f"엔진 출력: {stats['horsepower']:.0f} HP")
    with k_col3:
        st.metric("🛡️ 총 보호막 (Shield)", f"{stats['total_shield']:.0f}", f"제네레이터: +{gen_shield:.0f}")
    with k_col4:
        st.metric("⚔️ L-대지 / F-대공 위력", f"+{stats['crew_landpower']:.1f} / +{stats['crew_flypower']:.1f}", "승무원 전투 보너스")
    with k_col5:
        st.metric("🏭 생산력 / 공업력", f"{crew_prod:.1f} / {crew_ind:.1f}", "열차 총 생산 합계")

    st.markdown("<hr style='margin: 12px 0; border-color: #334155;'>", unsafe_allow_html=True)

    # 3-Column Studio Layout
    c1, c2, c3 = st.columns([1.15, 1.25, 1.15])

    # ----------------------------------------------------
    # COLUMN 1: 기관차 및 파츠 세팅
    # ----------------------------------------------------
    with c1:
        with st.container(border=True):
            st.markdown('<div class="section-head">⚙️ 1. 기관차 및 파츠 구성</div>', unsafe_allow_html=True)

            loco_opts = list(locomotives_map.keys())
            loco_labels = [f"{locomotives_map[k].get('locomotiveName')} ({k})" for k in loco_opts]
            cur_loco_id = train_config.locomotive.get("locomotiveId") if train_config.locomotive else loco_opts[0]
            cur_loco_idx = loco_opts.index(cur_loco_id) if cur_loco_id in loco_opts else 0

            sel_loco_idx = st.selectbox("🚂 기관차 파츠 선택", range(len(loco_opts)), format_func=lambda i: loco_labels[i], index=cur_loco_idx)
            train_config.locomotive = locomotives_map[loco_opts[sel_loco_idx]]

            # Locomotive Inspector Card
            if train_config.locomotive:
                l_data = train_config.locomotive
                st.markdown(f'''
                <div class="info-card">
                    <div class="info-card-title">📋 기관차 스탯 인스펙터: {l_data.get("locomotiveName")}</div>
                    <div class="info-grid">
                        <div class="info-item"><span class="info-label">HP:</span> <span class="info-val">{l_data.get("locomotiveHp")}</span></div>
                        <div class="info-item"><span class="info-label">Def:</span> <span class="info-val">{l_data.get("locomotiveDef")}</span></div>
                        <div class="info-item"><span class="info-label">보호막:</span> <span class="info-val">{l_data.get("locomotiveShield")}</span></div>
                        <div class="info-item"><span class="info-label">객차한도:</span> <span class="info-val">{l_data.get("locomotiveCouch")}칸</span></div>
                        <div class="info-item"><span class="info-label">시너지:</span> <span class="info-val">{l_data.get("synergy") or "없음"}</span></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

            # Engine
            eng_opts = ["(미장착)"] + list(engines_map.keys())
            cur_eng_id = train_config.engine.get("engineId") if train_config.engine else "(미장착)"
            cur_eng_idx = eng_opts.index(cur_eng_id) if cur_eng_id in eng_opts else 0
            sel_eng_idx = st.selectbox("🔥 엔진 (Horsepower)", range(len(eng_opts)), format_func=lambda i: f"{engines_map[eng_opts[i]].get('engineName')} (+{engines_map[eng_opts[i]].get('enginePowerUp')}HP)" if eng_opts[i] != "(미장착)" else "(미장착)", index=cur_eng_idx)
            train_config.engine = engines_map.get(eng_opts[sel_eng_idx])

            # Generator
            gen_opts = ["(미장착)"] + list(generators_map.keys())
            cur_gen_id = train_config.generator.get("generatorId") if train_config.generator else "(미장착)"
            cur_gen_idx = gen_opts.index(cur_gen_id) if cur_gen_id in gen_opts else 0
            sel_gen_idx = st.selectbox("⚡ 제네레이터 (Shield)", range(len(gen_opts)), format_func=lambda i: f"{generators_map[gen_opts[i]].get('generatorName')} (+{generators_map[gen_opts[i]].get('generatorShieldUp')}보호막)" if gen_opts[i] != "(미장착)" else "(미장착)", index=cur_gen_idx)
            train_config.generator = generators_map.get(gen_opts[sel_gen_idx])

            # Brake
            brk_opts = ["(미장착)"] + list(brakes_map.keys())
            cur_brk_id = train_config.brake.get("breakId") if train_config.brake else "(미장착)"
            cur_brk_idx = brk_opts.index(cur_brk_id) if cur_brk_id in brk_opts else 0
            sel_brk_idx = st.selectbox("🛑 제동장치 (Brake)", range(len(brk_opts)), format_func=lambda i: f"{brakes_map[brk_opts[i]].get('breakName')} (+{brakes_map[brk_opts[i]].get('breakPowerUp')})" if brk_opts[i] != "(미장착)" else "(미장착)", index=cur_brk_idx)
            train_config.brake = brakes_map.get(brk_opts[sel_brk_idx])

            # Locomotive Turrets (Max 2)
            st.markdown("###### 🔫 기관차 자체 포탑 (최대 2개)")
            col_lt1, col_lt2 = st.columns([2.2, 1])
            w_opts = list(weapons_map.keys())
            with col_lt1:
                sel_w_id = st.selectbox("장착할 포탑 선택", w_opts, format_func=lambda k: f"{weapons_map[k].get('weaponName')} (위력:{weapons_map[k].get('weaponPower')})", key="sb_lt")
            with col_lt2:
                if st.button("포탑 장착 (+)", key="btn_add_lt", use_container_width=True):
                    if len(train_config.locomotive_turrets) < 2:
                        train_config.locomotive_turrets.append(weapons_map[sel_w_id])
                        st.rerun()
                    else:
                        st.warning("기관차 포탑은 최대 2개까지만 장착 가능합니다!")

            for idx, w in enumerate(train_config.locomotive_turrets):
                col_w_info, col_w_del = st.columns([3, 1])
                with col_w_info:
                    st.caption(f"#{idx+1}: **{w.get('weaponName')}** [위력: {w.get('weaponPower')} | 사거리: {w.get('weaponRange')}]")
                with col_w_del:
                    if st.button("해제 (-)", key=f"del_lt_{idx}", use_container_width=True):
                        train_config.locomotive_turrets.pop(idx)
                        st.rerun()

    # ----------------------------------------------------
    # COLUMN 2: 객차 및 승무원 레벨/스탯 배분
    # ----------------------------------------------------
    with c2:
        with st.container(border=True):
            st.markdown('<div class="section-head">🚃 2. 객차 구성 & 승무원 레벨/스탯 관리</div>', unsafe_allow_html=True)

            # Coach Add Row
            col_c_add1, col_c_add2 = st.columns([2.2, 1])
            couch_opts = list(couches_map.keys())
            with col_c_add1:
                sel_couch_id = st.selectbox("연결할 객차 파츠", couch_opts, format_func=lambda k: f"{couches_map[k].get('couchName')} ({k})")
            with col_c_add2:
                if st.button("객차 추가 (+)", use_container_width=True):
                    max_c = int(train_config.locomotive.get("locomotiveCouch", 5)) if train_config.locomotive else 5
                    if len(train_config.coaches) < max_c:
                        train_config.add_coach(couches_map[sel_couch_id])
                        st.session_state.selected_coach_idx = len(train_config.coaches)
                        st.rerun()
                    else:
                        st.warning(f"선택한 기관차의 최대 객차 연결 한도는 {max_c}칸입니다!")

            # Coach List Selector
            coach_display_list = [f"🚂 [기관차] {train_config.locomotive.get('locomotiveName', '')}"]
            for slot in train_config.coaches:
                c_crew = slot.crew.get("crewName") if slot.crew else "미배치"
                coach_display_list.append(f"🚃 [#{slot.index}번 칸] {slot.get_name()} | 승무원: {c_crew} (Lv.{slot.crew_level})")

            sel_coach_row = st.selectbox("🎯 조작할 객차 칸 선택", range(len(coach_display_list)), format_func=lambda i: coach_display_list[i], index=min(st.session_state.selected_coach_idx, len(coach_display_list)-1))
            st.session_state.selected_coach_idx = sel_coach_row

            if sel_coach_row > 0:
                slot = train_config.coaches[sel_coach_row - 1]
                couch_syn = slot.couch_data.get("synergy", "없음") if slot.couch_data else "없음"

                col_del_c, col_c_info = st.columns([1.2, 2.8])
                with col_del_c:
                    if st.button("현재 객차 삭제 (-)", key="btn_del_cur_coach", use_container_width=True):
                        train_config.remove_coach(sel_coach_row - 1)
                        st.session_state.selected_coach_idx = max(0, sel_coach_row - 1)
                        st.rerun()
                with col_c_info:
                    st.caption(f"HP: {slot.get_couch_stats()['hp']} | Def: {slot.get_total_coach_def():.0f} | 시너지: {couch_syn}")

                # Crew Assignment Box
                st.markdown("###### 👨‍✈️ 승무원 배치 (동일 승무원 중복 장착 불가)")
                col_cr_sel, col_cr_act, col_cr_un = st.columns([2, 1, 1])
                cr_opts = ["(미배치)"] + list(crews_map.keys())
                cur_slot_cid = slot.crew.get("crewId") if slot.crew else "(미배치)"
                cur_cr_idx = cr_opts.index(cur_slot_cid) if cur_slot_cid in cr_opts else 0

                with col_cr_sel:
                    sel_cr_idx = st.selectbox("배치할 승무원", range(len(cr_opts)), format_func=lambda i: f"{crews_map[cr_opts[i]].get('crewName')} [{crews_map[cr_opts[i]].get('crewType')}]" if cr_opts[i] != "(미배치)" else "(미배치)", index=cur_cr_idx, label_visibility="collapsed")
                with col_cr_act:
                    if st.button("배치 (+)", key="btn_assign_crew", use_container_width=True):
                        if cr_opts[sel_cr_idx] != "(미배치)":
                            target_cid = cr_opts[sel_cr_idx]
                            dup_slot = None
                            for o_idx, o_slot in enumerate(train_config.coaches):
                                if o_idx != (sel_coach_row - 1) and o_slot.crew and o_slot.crew.get("crewId") == target_cid:
                                    dup_slot = o_slot
                                    break
                            if dup_slot:
                                st.error(f"[{crews_map[target_cid].get('crewName')}] 승무원은 이미 #{dup_slot.index}번 칸 객차에 배치되어 있습니다! 중복 배치가 불가능합니다.")
                            else:
                                slot.crew = crews_map[target_cid]
                                st.rerun()
                with col_cr_un:
                    if st.button("해제 (-)", key="btn_unassign_crew", use_container_width=True):
                        slot.crew = None
                        st.rerun()

                # Crew Level & Point Allocation with tactile buttons
                if slot.crew:
                    cr_name = slot.crew.get("crewName")
                    with st.container(border=True):
                        st.markdown(f'<div style="font-weight:700; color:#a855f7; font-size:13px; margin-bottom:8px;">👨‍✈️ [#{slot.index}번 {cr_name}] 레벨 & 스탯 포인트 배분</div>', unsafe_allow_html=True)

                        # Level Row with [-10], [-1], [Lv], [+1], [+10]
                        col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns([1, 1, 2, 1, 1])
                        with col_l1:
                            if st.button("-10", key="btn_lvl_m10", use_container_width=True):
                                slot.set_crew_level(max(1, slot.crew_level - 10))
                                st.rerun()
                        with col_l2:
                            if st.button("-1", key="btn_lvl_m1", use_container_width=True):
                                slot.set_crew_level(max(1, slot.crew_level - 1))
                                st.rerun()
                        with col_l3:
                            st.markdown(f"<div style='text-align:center; font-weight:800; font-size:16px; color:#38bdf8; padding-top:4px;'>Lv. {slot.crew_level}</div>", unsafe_allow_html=True)
                        with col_l4:
                            if st.button("+1", key="btn_lvl_p1", use_container_width=True):
                                slot.set_crew_level(min(50, slot.crew_level + 1))
                                st.rerun()
                        with col_l5:
                            if st.button("+10", key="btn_lvl_p10", use_container_width=True):
                                slot.set_crew_level(min(50, slot.crew_level + 10))
                                st.rerun()

                        rem_pts = slot.get_remaining_points()
                        max_pts = slot.get_max_available_points()
                        st.markdown(f"<div style='font-size:12px; color:#cbd5e1; margin: 6px 0;'>남은 포인트: <b style='color:#38bdf8;'>{rem_pts}</b> / {max_pts} pt (포인트당 +1.0% 증가)</div>", unsafe_allow_html=True)

                        # 1. Attack Row
                        col_a_lbl, col_a_m1, col_a_val, col_a_p1 = st.columns([2.5, 1, 1.5, 1])
                        with col_a_lbl:
                            st.markdown("⚔️ **공격력** *(대지/대공)*")
                        with col_a_m1:
                            if st.button("[-]", key="btn_atk_m1", use_container_width=True):
                                slot.set_crew_points(max(0, slot.crew_atk_pts - 1), slot.crew_def_pts, slot.crew_prod_pts)
                                st.rerun()
                        with col_a_val:
                            st.markdown(f"<div style='text-align:center; font-weight:700; color:#fbbf24;'>{slot.crew_atk_pts} pt</div>", unsafe_allow_html=True)
                        with col_a_p1:
                            if st.button("[+]", key="btn_atk_p1", use_container_width=True):
                                if rem_pts > 0:
                                    slot.set_crew_points(slot.crew_atk_pts + 1, slot.crew_def_pts, slot.crew_prod_pts)
                                    st.rerun()
                                else:
                                    st.warning("남은 포인트가 없습니다!")

                        # 2. Defense Row
                        col_d_lbl, col_d_m1, col_d_val, col_d_p1 = st.columns([2.5, 1, 1.5, 1])
                        with col_d_lbl:
                            st.markdown("🛡️ **방어력** *(승무원 방어)*")
                        with col_d_m1:
                            if st.button("[-]", key="btn_def_m1", use_container_width=True):
                                slot.set_crew_points(slot.crew_atk_pts, max(0, slot.crew_def_pts - 1), slot.crew_prod_pts)
                                st.rerun()
                        with col_d_val:
                            st.markdown(f"<div style='text-align:center; font-weight:700; color:#38bdf8;'>{slot.crew_def_pts} pt</div>", unsafe_allow_html=True)
                        with col_d_p1:
                            if st.button("[+]", key="btn_def_p1", use_container_width=True):
                                if rem_pts > 0:
                                    slot.set_crew_points(slot.crew_atk_pts, slot.crew_def_pts + 1, slot.crew_prod_pts)
                                    st.rerun()
                                else:
                                    st.warning("남은 포인트가 없습니다!")

                        # 3. Production Row
                        col_p_lbl, col_p_m1, col_p_val, col_p_p1 = st.columns([2.5, 1, 1.5, 1])
                        with col_p_lbl:
                            st.markdown("🏭 **생산/공업** *(생산력)*")
                        with col_p_m1:
                            if st.button("[-]", key="btn_prod_m1", use_container_width=True):
                                slot.set_crew_points(slot.crew_atk_pts, slot.crew_def_pts, max(0, slot.crew_prod_pts - 1))
                                st.rerun()
                        with col_p_val:
                            st.markdown(f"<div style='text-align:center; font-weight:700; color:#34d399;'>{slot.crew_prod_pts} pt</div>", unsafe_allow_html=True)
                        with col_p_p1:
                            if st.button("[+]", key="btn_prod_p1", use_container_width=True):
                                if rem_pts > 0:
                                    slot.set_crew_points(slot.crew_atk_pts, slot.crew_def_pts, slot.crew_prod_pts + 1)
                                    st.rerun()
                                else:
                                    st.warning("남은 포인트가 없습니다!")

                        # Quick Preset Buttons
                        qp_c1, qp_c2, qp_c3, qp_c4 = st.columns(4)
                        with qp_c1:
                            if st.button("초기화", key="q_reset", use_container_width=True):
                                slot.set_crew_points(0, 0, 0)
                                st.rerun()
                        with qp_c2:
                            if st.button("공격 올인", key="q_atk", use_container_width=True):
                                slot.set_crew_points(max_pts, 0, 0)
                                st.rerun()
                        with qp_c3:
                            if st.button("방어 올인", key="q_def", use_container_width=True):
                                slot.set_crew_points(0, max_pts, 0)
                                st.rerun()
                        with qp_c4:
                            if st.button("균등 분배", key="q_even", use_container_width=True):
                                each = max_pts // 3
                                rem = max_pts % 3
                                slot.set_crew_points(each + (1 if rem > 0 else 0), each + (1 if rem > 1 else 0), each)
                                st.rerun()
                else:
                    st.info("💡 승무원을 배치하면 레벨 설정 및 스탯 포인트 배분이 활성화됩니다.")

                # Coach Turrets Box (Max 4)
                st.markdown("###### 🔫 객차 포탑 장착 (최대 4개)")
                col_ct1, col_ct2 = st.columns([2.2, 1])
                with col_ct1:
                    sel_ct_id = st.selectbox("장착할 객차 포탑", w_opts, format_func=lambda k: f"{weapons_map[k].get('weaponName')} (위력:{weapons_map[k].get('weaponPower')})", key="sb_ct")
                with col_ct2:
                    if st.button("포탑 장착 (+)", key="btn_add_ct", use_container_width=True):
                        if len(slot.turrets) < 4:
                            slot.turrets.append(weapons_map[sel_ct_id])
                            st.rerun()
                        else:
                            st.warning("객차 포탑은 최대 4개까지만 장착 가능합니다!")

                for idx, w in enumerate(slot.turrets):
                    col_w_info, col_w_del = st.columns([3, 1])
                    with col_w_info:
                        st.caption(f"#{idx+1}: **{w.get('weaponName')}** [위력: {w.get('weaponPower')} | 사거리: {w.get('weaponRange')}]")
                    with col_w_del:
                        if st.button("해제 (-)", key=f"del_ct_{slot.index}_{idx}", use_container_width=True):
                            slot.turrets.pop(idx)
                            st.rerun()
            else:
                st.info("🚂 현재 [기관차]가 선택되어 있습니다. 객차를 조작하려면 위의 조감도 또는 드롭다운에서 객차를 선택하세요.")

    # ----------------------------------------------------
    # COLUMN 3: 적 군단 세팅 & 시뮬레이션
    # ----------------------------------------------------
    with c3:
        with st.container(border=True):
            st.markdown('<div class="section-head">👾 3. 적 군단 세팅 & 전투 시뮬레이션</div>', unsafe_allow_html=True)

            ba_opts = ["(직접 구성)"] + list(battle_areas_map.keys())
            sel_ba = st.selectbox("🗺️ 적 편대 프리셋 (BattleArea)", ba_opts)

            if sel_ba != "(직접 구성)":
                ba_rec = battle_areas_map.get(sel_ba)
                lvl_id = ba_rec.get("battleLevelId") if ba_rec else sel_ba
                if st.button(f"'{lvl_id}' 프리셋 불러오기", use_container_width=True):
                    spawn_recs = loader.get_sheet_data("SpawnData")
                    enemy_config.clear()
                    enemy_config.selected_battle_area_id = lvl_id
                    count_loaded = 0
                    for sp in spawn_recs:
                        target_lvl = sp.get("levelId")
                        if target_lvl and (target_lvl == lvl_id or target_lvl == sel_ba):
                            mid = sp.get("levelSpawnMonsterId")
                            if mid and mid in monsters_map:
                                cur = enemy_config.monster_counts.get(mid, 0)
                                enemy_config.set_monster_count(mid, cur + 1)
                                count_loaded += 1
                    st.success(f"{lvl_id} 프리셋 {count_loaded}마리 로드 완료!")
                    st.rerun()

            # Enemy Summary Card
            e_sum = enemy_config.get_summary(monsters_map)
            st.markdown(f"""
            <div class="info-card" style="border-color: #ef4444;">
                <div class="info-card-title" style="color: #f87171;">👾 적 군단 현황 요약</div>
                <div class="info-grid">
                    <div class="info-item"><span class="info-label">총 수량:</span> <span class="info-val">{e_sum['total_count']}마리 ({e_sum['monster_types_count']}종)</span></div>
                    <div class="info-item"><span class="info-label">총 체력:</span> <span class="info-val">{e_sum['total_hp']:,}</span></div>
                    <div class="info-item"><span class="info-label">총 위력:</span> <span class="info-val">{e_sum['total_power']:,}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Add monster with Quantity Chooser
            m_opts = list(monsters_map.keys())
            st.markdown("###### ➕ 몬스터 직접 추가")
            col_m1, col_m2, col_m3 = st.columns([2.2, 1.1, 1.2])
            with col_m1:
                sel_m_id = st.selectbox("몬스터 종류", m_opts, format_func=lambda k: f"{monsters_map[k].get('monsterName')} (HP:{monsters_map[k].get('monsterHp')})")
            with col_m2:
                add_cnt = st.number_input("수량", min_value=1, max_value=50, value=1, step=1, key="num_add_m_cnt")
            with col_m3:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("추가 (+)", key="btn_add_monster_with_count", use_container_width=True):
                    cur = enemy_config.monster_counts.get(sel_m_id, 0)
                    enemy_config.set_monster_count(sel_m_id, cur + add_cnt)
                    st.rerun()

            # Quick Quantity Preset Buttons
            col_qp1, col_qp2, col_qp3 = st.columns(3)
            with col_qp1:
                if st.button(f"+1마리 추가", key="btn_qp_1", use_container_width=True):
                    cur = enemy_config.monster_counts.get(sel_m_id, 0)
                    enemy_config.set_monster_count(sel_m_id, cur + 1)
                    st.rerun()
            with col_qp2:
                if st.button(f"+5마리 추가", key="btn_qp_5", use_container_width=True):
                    cur = enemy_config.monster_counts.get(sel_m_id, 0)
                    enemy_config.set_monster_count(sel_m_id, cur + 5)
                    st.rerun()
            with col_qp3:
                if st.button(f"+10마리 추가", key="btn_qp_10", use_container_width=True):
                    cur = enemy_config.monster_counts.get(sel_m_id, 0)
                    enemy_config.set_monster_count(sel_m_id, cur + 10)
                    st.rerun()

            if enemy_config.monster_counts:
                st.markdown("###### 📋 편성된 몬스터 목록 (마리수 조절)")
                for m_k, m_cnt in list(enemy_config.monster_counts.items()):
                    m_info = monsters_map.get(m_k, {})
                    c_m_lbl, c_m_m1, c_m_cnt, c_m_p1, c_m_del = st.columns([3, 0.7, 1, 0.7, 0.9])
                    with c_m_lbl:
                        st.caption(f"• **{m_info.get('monsterName', m_k)}** (HP:{m_info.get('monsterHp', 0)})")
                    with c_m_m1:
                        if st.button("-", key=f"btn_m_sub_{m_k}", use_container_width=True):
                            enemy_config.set_monster_count(m_k, max(0, m_cnt - 1))
                            st.rerun()
                    with c_m_cnt:
                        st.markdown(f"<div style='text-align:center; font-weight:700; font-size:12px;'>{m_cnt}마리</div>", unsafe_allow_html=True)
                    with c_m_p1:
                        if st.button("+", key=f"btn_m_add_{m_k}", use_container_width=True):
                            enemy_config.set_monster_count(m_k, m_cnt + 1)
                            st.rerun()
                    with c_m_del:
                        if st.button("삭제", key=f"del_m_{m_k}", use_container_width=True):
                            enemy_config.set_monster_count(m_k, 0)
                            st.rerun()

                if st.button("적 군단 전체 비우기", use_container_width=True):
                    enemy_config.clear()
                    st.rerun()

            st.markdown("<hr style='margin: 14px 0; border-color: #334155;'>", unsafe_allow_html=True)

            # BIG RUN SIMULATION BUTTON
            if st.button("⚡ 전투 시뮬레이션 실행 (Run Simulation)", type="primary", use_container_width=True):
                if not enemy_config.monster_counts:
                    st.error("전투를 실행할 적 몬스터가 없습니다!")
                else:
                    engine = BattleSimulationEngine(train_config, enemy_config, monsters_map)
                    summary = engine.run_simulation()
                    st.session_state.last_battle_result = {
                        "summary": summary,
                        "engine": engine
                    }
                    st.success(f"전투 종료! 결과: {summary['result']} (소요시간: {summary['duration']:.1f}초)")

    # 4. 2D Interactive Battle Viewport Result
    if st.session_state.last_battle_result:
        st.markdown("<hr style='margin: 16px 0; border-color: #334155;'>", unsafe_allow_html=True)
        st.markdown("##### 🎮 2D 전투 시뮬레이션 결과 및 지표 분석")
        res = st.session_state.last_battle_result
        summ = res["summary"]

        r_c1, r_c2, r_c3, r_c4 = st.columns(4)
        with r_c1:
            st.metric("🏆 전투 결과", summ["result"])
        with r_c2:
            st.metric("⏱️ 소요 시간", f"{summ['duration']:.1f} 초")
        with r_c3:
            st.metric("💥 가한 총 피해량", f"{summ['total_damage_dealt']:,}")
        with r_c4:
            st.metric("👾 처치 몬스터 수", f"{summ['total_kills']} / {summ['total_monsters']} 마리")

# ==============================================================================
# TAB 2: 📋 전투 로그 시트 (Combat Log Sheet)
# ==============================================================================
with tab2:
    st.markdown('<div class="section-head">📋 틱(Tick) 단위 상세 전투 이벤트 로그 시트</div>', unsafe_allow_html=True)
    if st.session_state.last_battle_result:
        engine = st.session_state.last_battle_result["engine"]
        logs = engine.logs
        if logs:
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs, use_container_width=True, height=520)

            csv_data = df_logs.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 엑셀 호환 전투 로그 CSV 다운로드",
                data=csv_data,
                file_name="siecletrain_battle_log.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("기록된 로그 데이터가 없습니다.")
    else:
        st.info("💡 1번 워크숍 탭에서 '전투 시뮬레이션 실행' 버튼을 누르면 틱 단위 상세 전투 로그가 여기에 기록됩니다.")

# ==============================================================================
# TAB 3: 🔍 Raw 데이터 검증 (Data Inspector)
# ==============================================================================
with tab3:
    st.markdown('<div class="section-head">🔍 엑셀 Raw 데이터 인스펙터</div>', unsafe_allow_html=True)
    sheet_names = list(loader.data.keys())
    if sheet_names:
        sel_sheet = st.selectbox("확인할 엑셀 데이터 시트 선택", sheet_names)
        records = loader.get_sheet_data(sel_sheet)
        if records:
            df_sheet = pd.DataFrame(records)
            st.dataframe(df_sheet, use_container_width=True, height=550)
            st.caption(f"총 {len(records)} 건의 레코드가 정상 로드되었습니다.")
        else:
            st.info("해당 시트에 데이터가 없습니다.")

# ==============================================================================
# TAB 4: 🎲 승무원 레벨업 랜덤 성장 시뮬레이터 (Monte Carlo)
# ==============================================================================
with tab4:
    st.markdown('<div class="section-head">🎲 4. 승무원 레벨업 랜덤 성장 몬테카를로 시뮬레이터</div>', unsafe_allow_html=True)

    col_sim_left, col_sim_right = st.columns([1.15, 1.85])

    # Left Panel: Crew Selection & Probabilities
    with col_sim_left:
        with st.container(border=True):
            st.markdown("##### 👨‍✈️ 1. 대상 승무원 선택")
            c_list = list(crews_map.keys())
            sel_sim_cid = st.selectbox(
                "시뮬레이션 대상 승무원", c_list,
                format_func=lambda k: f"{crews_map[k].get('crewName')} [{crews_map[k].get('crewType')}] ({k})"
            )
            sim_cdata = crews_map[sel_sim_cid]
            cname = sim_cdata.get("crewName") or sel_sim_cid
            ctype = str(sim_cdata.get("crewType") or "일반").strip()

            st.markdown(f'''
            <div class="info-card" style="border-color: #3b82f6;">
                <div class="info-card-title">👨‍✈️ {cname} [{ctype}]</div>
                <div class="info-grid">
                    <div class="info-item"><span class="info-label">대지위력:</span> <span class="info-val">{sim_cdata.get("crewLandpower",0)}</span></div>
                    <div class="info-item"><span class="info-label">대공위력:</span> <span class="info-val">{sim_cdata.get("crewFlypower",0)}</span></div>
                    <div class="info-item"><span class="info-label">Def:</span> <span class="info-val">{sim_cdata.get("crewDef",0)}</span></div>
                    <div class="info-item"><span class="info-label">생산력:</span> <span class="info-val">{sim_cdata.get("crewProduct",0.0):.1f}</span></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # Primary Stat Detection
            cid_str = str(sel_sim_cid)
            if "전투" in ctype or "공격" in ctype or "Batt" in cid_str:
                main_stat_name = "⚔️ 공격력 (Attack)"
                main_stat_key = "atk"
            elif "방어" in ctype or "Def" in cid_str:
                main_stat_name = "🛡️ 방어력 (Defense)"
                main_stat_key = "def"
            elif "생산" in ctype or "공업" in ctype or "Prod" in cid_str:
                main_stat_name = "🏭 생산/공업 (Production)"
                main_stat_key = "prod"
            else:
                main_stat_name = "⚖️ 밸런스/균등"
                main_stat_key = "even"

            st.markdown(f"##### 🎯 2. 주스탯 확률 설정 (주스탯: **{main_stat_name}**)")
            main_prob = st.slider("⭐ 주스탯 상승 확률 (%)", min_value=0.0, max_value=100.0, value=50.0, step=5.0)
            sub_prob = max(0.0, (100.0 - main_prob) / 2.0)

            # Calculate exact probs
            if main_stat_key == "atk":
                p_atk, p_def, p_prod = main_prob, sub_prob, sub_prob
            elif main_stat_key == "def":
                p_atk, p_def, p_prod = sub_prob, main_prob, sub_prob
            elif main_stat_key == "prod":
                p_atk, p_def, p_prod = sub_prob, sub_prob, main_prob
            else:
                p_atk, p_def, p_prod = main_prob, sub_prob, sub_prob

            st.markdown(f"""
            <div class="info-card">
                <div class="info-grid">
                    <div class="info-item"><span class="info-label">⚔️ 공격력:</span> <span class="info-val">{p_atk:.1f}% {'(⭐주스탯)' if main_stat_key=='atk' else '(보조)'}</span></div>
                    <div class="info-item"><span class="info-label">🛡️ 방어력:</span> <span class="info-val">{p_def:.1f}% {'(⭐주스탯)' if main_stat_key=='def' else '(보조)'}</span></div>
                    <div class="info-item"><span class="info-label">🏭 생산력:</span> <span class="info-val">{p_prod:.1f}% {'(⭐주스탯)' if main_stat_key=='prod' else '(보조)'}</span></div>
                </div>
                <div style="font-size:11px; color:#10b981; margin-top:6px; font-weight:600;">✓ 확률 합계: {p_atk + p_def + p_prod:.1f}% (항상 100% 자동 유지)</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### ⚙️ 3. 시뮬레이션 파라미터")
            sim_target_lvl = st.number_input("목표 레벨 (1~50)", min_value=2, max_value=50, value=50, step=1)
            sim_rolls = sim_target_lvl - 1
            sim_rate = st.number_input("1pt당 스탯 증가율 (%)", min_value=0.1, max_value=100.0, value=1.0, step=0.5)
            sim_trials = st.selectbox("반복 횟수 (Trials)", [1, 100, 1000, 10000], index=2)

            st.markdown("<hr style='margin: 12px 0; border-color: #334155;'>", unsafe_allow_html=True)
            btn_run_sim = st.button("🎲 몬테카를로 시뮬레이션 실행 (Run)", type="primary", use_container_width=True)

            if btn_run_sim:
                w_sum = p_atk + p_def + p_prod
                w_a, w_d, w_p = p_atk/w_sum, p_def/w_sum, p_prod/w_sum

                atk_res, def_res, prod_res = [], [], []
                single_logs = []

                for t_i in range(sim_trials):
                    a_c, d_c, p_c = 0, 0, 0
                    for r_i in range(sim_rolls):
                        rv = random.random()
                        if rv < w_a:
                            a_c += 1
                            tag = "⚔️ 공격력"
                        elif rv < w_a + w_d:
                            d_c += 1
                            tag = "🛡️ 방어력"
                        else:
                            p_c += 1
                            tag = "🏭 생산/공업"

                        if sim_trials == 1:
                            single_logs.append(f"[Lv. {r_i+2:02d}] 🎲 주사위 {rv*100:5.1f}% ➔ {tag} +1pt (누적: ⚔️:{a_c}pt, 🛡️:{d_c}pt, 🏭:{p_c}pt)")

                    atk_res.append(a_c)
                    def_res.append(d_c)
                    prod_res.append(p_c)

                st.session_state.last_crew_sim_result = {
                    "cdata": sim_cdata,
                    "target_lvl": sim_target_lvl,
                    "rolls": sim_rolls,
                    "trials": sim_trials,
                    "rate": sim_rate,
                    "atk_res": atk_res,
                    "def_res": def_res,
                    "prod_res": prod_res,
                    "single_logs": single_logs,
                    "p_atk": p_atk,
                    "p_def": p_def,
                    "p_prod": p_prod
                }

            # Apply to Workshop Button
            if st.session_state.last_crew_sim_result:
                if st.button("🎯 시뮬레이션 결과 워크숍 적용 (동일 승무원 일괄 동기화)", use_container_width=True):
                    s_res = st.session_state.last_crew_sim_result
                    s_cid = s_res["cdata"].get("crewId")
                    s_lvl = s_res["target_lvl"]
                    s_a = s_res["atk_res"][0]
                    s_d = s_res["def_res"][0]
                    s_p = s_res["prod_res"][0]

                    matching_slots = [s for s in train_config.coaches if s.crew and s.crew.get("crewId") == s_cid]
                    if matching_slots:
                        for s in matching_slots:
                            s.set_crew_level(s_lvl)
                            s.set_crew_points(s_a, s_d, s_p)
                        st.success(f"[{s_res['cdata'].get('crewName')}] 승무원이 탑승한 {len(matching_slots)}개 객차에 레벨 및 스탯이 일괄 동기화되었습니다!")
                    else:
                        st.warning(f"현재 열차에 [{s_res['cdata'].get('crewName')}] 승무원이 배치되어 있지 않습니다. 1번 탭에서 승무원을 먼저 배치하세요.")

    # Right Panel: Results & Analytics
    with col_sim_right:
        with st.container(border=True):
            if st.session_state.last_crew_sim_result:
                s_res = st.session_state.last_crew_sim_result
                trials = s_res["trials"]
                rolls = s_res["rolls"]
                rate = s_res["rate"]
                a_res, d_res, p_res = s_res["atk_res"], s_res["def_res"], s_res["prod_res"]

                avg_a, avg_d, avg_p = sum(a_res)/trials, sum(d_res)/trials, sum(p_res)/trials
                min_a, max_a = min(a_res), max(a_res)
                min_d, max_d = min(d_res), max(d_res)
                min_p, max_p = min(p_res), max(p_res)

                st.markdown("##### 📊 몬테카를로 시뮬레이션 통계 대시보드")
                k1, k2, k3 = st.columns(3)
                with k1:
                    st.metric("⚔️ 공격력 포인트 평균", f"{avg_a:.2f} pt", f"{avg_a/rolls*100:.1f}% [최소 {min_a} ~ 최대 {max_a}]")
                with k2:
                    st.metric("🛡️ 방어력 포인트 평균", f"{avg_d:.2f} pt", f"{avg_d/rolls*100:.1f}% [최소 {min_d} ~ 최대 {max_d}]")
                with k3:
                    st.metric("🏭 생산/공업 포인트 평균", f"{avg_p:.2f} pt", f"{avg_p/rolls*100:.1f}% [최소 {min_p} ~ 최대 {max_p}]")

                # Final Expected Stats Table
                cd = s_res["cdata"]
                b_land = float(cd.get("crewLandpower") or 0)
                b_fly = float(cd.get("crewFlypower") or 0)
                b_def = float(cd.get("crewDef") or 0)
                b_prod = float(cd.get("crewProduct") or 0)
                b_ind = float(cd.get("crewIndustry") or 0)

                m_avg_a = 1.0 + (avg_a * rate / 100.0)
                m_avg_d = 1.0 + (avg_d * rate / 100.0)
                m_avg_p = 1.0 + (avg_p * rate / 100.0)

                stats_table_data = [
                    {"스탯 항목": "⚔️ 대지 위력 (Landpower)", "기본 수치": b_land, "평균 획득 pt": f"{avg_a:.2f}", "평균 배율": f"{m_avg_a:.3f}x", "평균 최종 스탯": f"{b_land * m_avg_a:.2f}", "최저(Min)": f"{b_land * (1.0 + min_a*rate/100.0):.2f}", "최고(Max)": f"{b_land * (1.0 + max_a*rate/100.0):.2f}"},
                    {"스탯 항목": "🏹 대공 위력 (Flypower)", "기본 수치": b_fly, "평균 획득 pt": f"{avg_a:.2f}", "평균 배율": f"{m_avg_a:.3f}x", "평균 최종 스탯": f"{b_fly * m_avg_a:.2f}", "최저(Min)": f"{b_fly * (1.0 + min_a*rate/100.0):.2f}", "최고(Max)": f"{b_fly * (1.0 + max_a*rate/100.0):.2f}"},
                    {"스탯 항목": "🛡️ 방어력 (Def)", "기본 수치": b_def, "평균 획득 pt": f"{avg_d:.2f}", "평균 배율": f"{m_avg_d:.3f}x", "평균 최종 스탯": f"{b_def * m_avg_d:.2f}", "최저(Min)": f"{b_def * (1.0 + min_d*rate/100.0):.2f}", "최고(Max)": f"{b_def * (1.0 + max_d*rate/100.0):.2f}"},
                    {"스탯 항목": "🌾 생산력 (Product)", "기본 수치": b_prod, "평균 획득 pt": f"{avg_p:.2f}", "평균 배율": f"{m_avg_p:.3f}x", "평균 최종 스탯": f"{b_prod * m_avg_p:.2f}", "최저(Min)": f"{b_prod * (1.0 + min_p*rate/100.0):.2f}", "최고(Max)": f"{b_prod * (1.0 + max_p*rate/100.0):.2f}"},
                    {"스탯 항목": "⚙️ 공업력 (Industry)", "기본 수치": b_ind, "평균 획득 pt": f"{avg_p:.2f}", "평균 배율": f"{m_avg_p:.3f}x", "평균 최종 스탯": f"{b_ind * m_avg_p:.2f}", "최저(Min)": f"{b_ind * (1.0 + min_p*rate/100.0):.2f}", "최고(Max)": f"{b_ind * (1.0 + max_p*rate/100.0):.2f}"},
                ]
                st.dataframe(pd.DataFrame(stats_table_data), use_container_width=True)

                # Step-by-step Log (1 Trial) or Histogram (Multi trials)
                if trials == 1:
                    st.markdown("##### 📜 단일 회차 레벨업 주사위 판정 상세 로그")
                    st.code("\n".join(s_res["single_logs"]), language="text")
                else:
                    st.markdown("##### 📈 스탯 포인트 획득 분포 히스토그램 (Plotly)")
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(x=a_res, name="⚔️ 공격력 pt", marker_color="#f59e0b", opacity=0.75))
                    fig.add_trace(go.Histogram(x=d_res, name="🛡️ 방어력 pt", marker_color="#3b82f6", opacity=0.75))
                    fig.add_trace(go.Histogram(x=p_res, name="🏭 생산/공업 pt", marker_color="#10b981", opacity=0.75))
                    fig.update_layout(
                        barmode='overlay',
                        template='plotly_dark',
                        height=280,
                        margin=dict(l=20, r=20, t=30, b=20),
                        xaxis_title="획득 포인트 (pt)",
                        yaxis_title="시뮬레이션 회차 빈도"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 좌측에서 파라미터를 설정하고 '몬테카를로 시뮬레이션 실행' 버튼을 누르면 통계 분석 및 히스토그램이 여기에 표시됩니다.")

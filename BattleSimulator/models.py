class CoachSlot:
    def __init__(self, index, couch_data):
        self.index = index            # 1-indexed (1st coach, 2nd coach...)
        self.couch_data = couch_data  # Couch excel record dict
        self.turrets = []             # Max 4 Weapon dicts per coach
        self.crew = None              # Assigned Crew dict on this coach
        self.crew_level = 1           # Crew level (1 ~ 50)
        self.crew_atk_pts = 0         # Allocated Attack Points (대지/대공)
        self.crew_def_pts = 0         # Allocated Defense Points (방어력)
        self.crew_prod_pts = 0        # Allocated Product/Industry Points (생산/공업력)
        self.point_rate = 1.0         # Rate (%) per point (공용 배율, default 1.0%)

    def get_name(self):
        if self.couch_data:
            return self.couch_data.get("couchName") or self.couch_data.get("couchId")
        return f"객차 #{self.index}"

    def get_synergy_power(self):
        if self.couch_data:
            syn = self.couch_data.get("couchSynergyPower")
            if syn is not None:
                return float(syn)
        return 1.0

    def get_max_available_points(self):
        return max(0, self.crew_level - 1)

    def get_used_points(self):
        return self.crew_atk_pts + self.crew_def_pts + self.crew_prod_pts

    def get_remaining_points(self):
        return self.get_max_available_points() - self.get_used_points()

    def set_crew_level(self, lvl):
        self.crew_level = max(1, min(50, int(lvl)))
        max_pts = self.get_max_available_points()
        while self.get_used_points() > max_pts:
            if self.crew_prod_pts > 0:
                self.crew_prod_pts -= 1
            elif self.crew_def_pts > 0:
                self.crew_def_pts -= 1
            elif self.crew_atk_pts > 0:
                self.crew_atk_pts -= 1
            else:
                break

    def set_crew_points(self, atk_pts, def_pts, prod_pts):
        max_pts = self.get_max_available_points()
        a = max(0, int(atk_pts))
        d = max(0, int(def_pts))
        p = max(0, int(prod_pts))
        tot = a + d + p
        if tot > max_pts and tot > 0:
            scale = max_pts / tot
            a = int(a * scale)
            d = int(d * scale)
            p = max_pts - (a + d)
        self.crew_atk_pts = a
        self.crew_def_pts = d
        self.crew_prod_pts = max(0, p)

    def get_effective_crew_stats(self, point_rate=None):
        """Calculates leveled crew stats multiplied by couchSynergyPower"""
        if point_rate is None:
            point_rate = self.point_rate

        syn = self.get_synergy_power()
        if not self.crew:
            return {
                "landpower": 0.0,
                "flypower": 0.0,
                "def": 0.0,
                "product": 0.0,
                "industry": 0.0,
                "raw_landpower": 0.0,
                "raw_flypower": 0.0,
                "raw_def": 0.0,
                "raw_product": 0.0,
                "raw_industry": 0.0,
                "base_landpower": 0.0,
                "base_flypower": 0.0,
                "base_def": 0.0,
                "base_product": 0.0,
                "base_industry": 0.0,
                "level": self.crew_level,
                "atk_pts": 0,
                "def_pts": 0,
                "prod_pts": 0,
                "atk_mult": 1.0,
                "def_mult": 1.0,
                "prod_mult": 1.0,
                "point_rate": point_rate,
                "synergy": syn
            }

        base_land = float(self.crew.get("crewLandpower") or 0.0)
        base_fly = float(self.crew.get("crewFlypower") or 0.0)
        base_def = float(self.crew.get("crewDef") or 0.0)
        base_prod = float(self.crew.get("crewProduct") or 0.0)
        base_ind = float(self.crew.get("crewIndustry") or 0.0)

        # Multipliers based on allocated points & point_rate (%)
        atk_mult = 1.0 + (self.crew_atk_pts * (point_rate / 100.0))
        def_mult = 1.0 + (self.crew_def_pts * (point_rate / 100.0))
        prod_mult = 1.0 + (self.crew_prod_pts * (point_rate / 100.0))

        r_land = base_land * atk_mult
        r_fly = base_fly * atk_mult
        r_def = base_def * def_mult
        r_prod = base_prod * prod_mult
        r_ind = base_ind * prod_mult

        return {
            "landpower": round(r_land * syn, 2),
            "flypower": round(r_fly * syn, 2),
            "def": round(r_def * syn, 2),
            "product": round(r_prod * syn, 2),
            "industry": round(r_ind * syn, 2),
            "raw_landpower": round(r_land, 2),
            "raw_flypower": round(r_fly, 2),
            "raw_def": round(r_def, 2),
            "raw_product": round(r_prod, 2),
            "raw_industry": round(r_ind, 2),
            "base_landpower": base_land,
            "base_flypower": base_fly,
            "base_def": base_def,
            "base_product": base_prod,
            "base_industry": base_ind,
            "level": self.crew_level,
            "atk_pts": self.crew_atk_pts,
            "def_pts": self.crew_def_pts,
            "prod_pts": self.crew_prod_pts,
            "atk_mult": atk_mult,
            "def_mult": def_mult,
            "prod_mult": prod_mult,
            "point_rate": point_rate,
            "synergy": syn
        }

    def get_couch_stats(self):
        if not self.couch_data:
            return {}
        return {
            "hp": float(self.couch_data.get("couchHp") or 0.0),
            "def": float(self.couch_data.get("couchDef") or 0.0),
            "shield": float(self.couch_data.get("couchShield") or 0.0),
            "weight": float(self.couch_data.get("couchWeight") or 0.0),
            "synergy": self.get_synergy_power(),
            "cost": float(self.couch_data.get("couchCost") or 0.0),
        }

    def get_total_coach_def(self):
        """Base couch def + synergy applied crew def for THIS coach only"""
        cstats = self.get_couch_stats()
        eff_crew = self.get_effective_crew_stats()
        return round(cstats.get("def", 0.0) + eff_crew["def"], 1)

    def get_total_coach_shield(self, generator=None):
        """Base couch shield + generator shield bonus applied to ALL coaches"""
        base_shield = float(self.couch_data.get("couchShield") or 0.0) if self.couch_data else 0.0
        gen_shield = float(generator.get("generatorShieldUp") or 0.0) if generator else 0.0
        return round(base_shield + gen_shield, 1)

class TrainConfig:
    def __init__(self):
        self.locomotive = None
        self.locomotive_turrets = []  # list of up to 2 weapon dicts mounted on locomotive
        self.coaches = []             # list of CoachSlot instances
        self.engine = None
        self.generator = None
        self.brake = None
        self.crew_point_rate = 1.0    # Global common rate per point (%)

    def set_crew_point_rate(self, rate):
        self.crew_point_rate = float(rate)
        for slot in self.coaches:
            slot.point_rate = self.crew_point_rate

    def get_locomotive_shield(self):
        """Base locomotive shield + generator shield bonus applied to locomotive"""
        base_shield = float(self.locomotive.get("locomotiveShield") or 0.0) if self.locomotive else 0.0
        gen_shield = float(self.generator.get("generatorShieldUp") or 0.0) if self.generator else 0.0
        return round(base_shield + gen_shield, 1)

    def add_coach(self, couch_data):
        index = len(self.coaches) + 1
        slot = CoachSlot(index, couch_data)
        slot.point_rate = self.crew_point_rate
        self.coaches.append(slot)
        return slot

    add_couch = add_coach

    def remove_coach(self, index_0):
        if 0 <= index_0 < len(self.coaches):
            removed = self.coaches.pop(index_0)
            for idx, c in enumerate(self.coaches):
                c.index = idx + 1
            return removed
        return None

    remove_coach = remove_coach

    def get_all_equipped_turrets(self):
        turrets = []
        for t_idx, w in enumerate(self.locomotive_turrets):
            turrets.append((0, t_idx + 1, w))
        for coach in self.coaches:
            for t_idx, w in enumerate(coach.turrets):
                turrets.append((coach.index, t_idx + 1, w))
        return turrets

    def get_total_turret_count(self):
        return len(self.locomotive_turrets) + sum(len(c.turrets) for c in self.coaches)

    def calculate_stats(self):
        loco_def = float(self.locomotive.get("locomotiveDef") or 0.0) if self.locomotive else 0.0
        coaches_def_list = [c.get_total_coach_def() for c in self.coaches]

        stats = {
            "total_hp": 0.0,
            "locomotive_def": loco_def,
            "coaches_def_list": coaches_def_list,
            "total_def": loco_def + sum(coaches_def_list),
            "total_shield": 0.0,
            "horsepower": 0.0,
            "accel_power": 0.0,
            "brake_power": 0.0,
            "weight_limit": 0.0,
            "current_weight": 0.0,
            "max_couches": 0,
            "current_couches": len(self.coaches),
            "turret_count": self.get_total_turret_count(),
            "max_turrets": 2 + len(self.coaches) * 4,
            "crew_def": 0.0,
            "crew_landpower": 0.0,
            "crew_flypower": 0.0,
        }

        # 1. Locomotive Base Stats
        if self.locomotive:
            stats["total_hp"] += float(self.locomotive.get("locomotiveHp") or 0.0)
            stats["total_shield"] += float(self.locomotive.get("locomotiveShield") or 0.0)
            stats["horsepower"] += float(self.locomotive.get("locomotiveHorsepower") or 0.0)
            stats["accel_power"] += float(self.locomotive.get("locomotiveAccelpower") or 0.0)
            stats["brake_power"] += float(self.locomotive.get("locomotiveBreakpower") or 0.0)
            stats["weight_limit"] += float(self.locomotive.get("locomotiveWeightlimit") or 0.0)
            stats["max_couches"] = int(self.locomotive.get("locomotiveCouch") or 0)

        for w in self.locomotive_turrets:
            stats["current_weight"] += float(w.get("weaponWeight") or 0.0)

        # 2. Couches & Effective Crew Stats
        for coach in self.coaches:
            cstats = coach.get_couch_stats()
            stats["total_hp"] += cstats.get("hp", 0.0)
            stats["total_shield"] += cstats.get("shield", 0.0)
            stats["current_weight"] += cstats.get("weight", 0.0)

            eff_crew = coach.get_effective_crew_stats()
            stats["crew_def"] += eff_crew["def"]
            stats["crew_landpower"] += eff_crew["landpower"]
            stats["crew_flypower"] += eff_crew["flypower"]

            for w in coach.turrets:
                stats["current_weight"] += float(w.get("weaponWeight") or 0.0)

        # 3. Engine Stats
        if self.engine:
            stats["horsepower"] += float(self.engine.get("enginePowerUp") or 0.0)
            stats["current_weight"] += float(self.engine.get("engineWeight") or 0.0)

        # 4. Generator Stats
        if self.generator:
            stats["total_shield"] += float(self.generator.get("generatorShieldUp") or 0.0)
            stats["current_weight"] += float(self.generator.get("generatorWeight") or 0.0)

        # 5. Brake Stats
        if self.brake:
            stats["brake_power"] += float(self.brake.get("breakPowerUp") or 0.0)
            stats["current_weight"] += float(self.brake.get("breakWeigt") or 0.0)

        return stats

    def get_config_details(self):
        lines = []
        loco_name = self.locomotive.get("locomotiveName") if self.locomotive else "기관차 미선택"
        loco_hp = self.locomotive.get("locomotiveHp", 0) if self.locomotive else 0
        loco_def = self.locomotive.get("locomotiveDef", 0) if self.locomotive else 0
        loco_shield = self.get_locomotive_shield()
        lines.append(f"기관차: {loco_name} (HP: {loco_hp} | Def: {loco_def:.0f} | 🛡️보호막: {loco_shield:.0f})")

        e_name = self.engine.get("engineName") if self.engine else "미장착"
        g_name = self.generator.get("generatorName") if self.generator else "미장착"
        b_name = self.brake.get("breakName") if self.brake else "미장착"
        lines.append(f"기관차 파츠: 엔진:[{e_name}] | 제네레이터:[{g_name}] | 제동장치:[{b_name}]")

        lt_names = [f"T{i+1}:{w.get('weaponName') or w.get('weaponId')} [{str(w.get('weaponLandType') or 'L').strip().upper()}]" for i, w in enumerate(self.locomotive_turrets)]
        lt_str = ", ".join(lt_names) if lt_names else "없음"
        lines.append(f"기관차 자체 포탑 ({len(self.locomotive_turrets)}/2개): {lt_str}")

        if self.coaches:
            lines.append(f"연결 객차 수: 총 {len(self.coaches)}칸")
            for slot in self.coaches:
                cname = slot.get_name()
                chp = slot.couch_data.get("couchHp", 500) if slot.couch_data else 500
                cshield = slot.get_total_coach_shield(generator=self.generator)
                cdef = slot.get_total_coach_def()
                syn = slot.get_synergy_power()
                crew_name = slot.crew.get("crewName") if slot.crew else "미배치"
                t_names = [f"T{i+1}:{w.get('weaponName') or w.get('weaponId')}" for i, w in enumerate(slot.turrets)]
                t_str = ", ".join(t_names) if t_names else "없음"
                lines.append(f"  • [{slot.index}번 칸] {cname} (Def:{cdef:.1f} | 🛡️보호막:{cshield:.0f} | HP:{chp}) | 승무원:{crew_name}(시너지 {syn:.1f}x) | 장착 포탑 ({len(slot.turrets)}/4개): {t_str}")
        else:
            lines.append("연결 객차 수: 0칸 (없음)")

        return lines

class TurretConfig:
    def __init__(self, max_slots_per_coach=4):
        self.max_slots_per_coach = max_slots_per_coach

    def calculate_dps_summary(self, train_config):
        equipped = train_config.get_all_equipped_turrets()
        total_dps = 0.0
        total_weight = 0.0
        for coach_idx, t_idx, w in equipped:
            power = float(w.get("weaponPower") or 0.0)
            atk_cycle = float(w.get("weaponAtkcycle") or 1.0)
            dps = power / atk_cycle if atk_cycle > 0 else power
            total_dps += dps
            total_weight += float(w.get("weaponWeight") or 0.0)

        max_tot = len(train_config.coaches) * 4
        return {
            "equipped_count": len(equipped),
            "max_slots": max_tot if max_tot > 0 else 4,
            "total_dps": round(total_dps, 2),
            "total_weight": total_weight
        }

class EnemyGroupConfig:
    def __init__(self):
        self.selected_battle_area_id = None
        self.monster_counts = {}

    def set_monster_count(self, monster_id, count):
        if count <= 0:
            self.monster_counts.pop(monster_id, None)
        else:
            self.monster_counts[monster_id] = count

    def clear(self):
        self.selected_battle_area_id = None
        self.monster_counts.clear()

    def get_summary(self, monster_data_map):
        total_count = sum(self.monster_counts.values())
        total_hp = 0.0
        total_power = 0.0

        for mid, cnt in self.monster_counts.items():
            m_info = monster_data_map.get(mid, {})
            hp = float(m_info.get("monsterHp") or 0.0)
            pwr = float(m_info.get("monsterPower") or 0.0)
            total_hp += hp * cnt
            total_power += pwr * cnt

        return {
            "total_count": total_count,
            "total_hp": round(total_hp, 2),
            "total_power": round(total_power, 2),
            "monster_types_count": len(self.monster_counts)
        }

    def get_config_details(self, monster_data_map):
        lines = []
        ba_str = self.selected_battle_area_id if self.selected_battle_area_id else "직접 지정"
        lines.append(f"전투 구역 (BattleArea) 프리셋: {ba_str}")
        
        m_lines = []
        total_hp = 0.0
        total_power = 0.0
        total_count = 0

        for mid, cnt in self.monster_counts.items():
            m_info = monster_data_map.get(mid, {})
            mname = m_info.get("monsterName") or mid
            hp = float(m_info.get("monsterHp") or 0.0)
            pwr = float(m_info.get("monsterPower") or 0.0)
            m_lines.append(f"{mname} x {cnt}마리 (개별 HP:{hp} | ATK:{pwr})")
            total_hp += hp * cnt
            total_power += pwr * cnt
            total_count += cnt

        lines.append(f"적 몬스터 수량: 총 {total_count}마리 ({len(self.monster_counts)}종)")
        if m_lines:
            lines.append("  • " + " | ".join(m_lines))
        lines.append(f"적 총 HP 합계: {total_hp:.0f} | 적 총 공격력 합계: {total_power:.0f}")

        return lines

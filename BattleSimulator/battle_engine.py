import math
import copy

ATTRIBUTE_BONUS_TABLE = {
    'normal':  {'S': -0.2, 'M':  0.2, 'B':  0.0},
    'spread':  {'S':  0.2, 'M':  0.0, 'B': -0.2},
    'amored':  {'S':  0.0, 'M': -0.2, 'B':  0.2},
    'armored': {'S':  0.0, 'M': -0.2, 'B':  0.2},
}

def get_attribute_bonus(weapon_type, monster_def_type):
    wtype = str(weapon_type or '').strip().lower()
    mtype = str(monster_def_type or '').strip().upper()
    return ATTRIBUTE_BONUS_TABLE.get(wtype, {}).get(mtype, 0.0)

class ActiveDebuffZone:
    def __init__(self, zone_type, shape, location_type, pos, duration, power=0, debuff_effect=None, radius=2.0, turret_name=""):
        self.zone_type = zone_type
        self.shape = str(shape or 'circle').strip().lower()
        self.location_type = location_type
        self.pos = pos
        self.radius = max(0.5, float(radius))
        self.duration = duration
        self.time_left = duration
        self.power = power
        self.debuff_effect = str(debuff_effect or '').strip().lower()
        self.turret_name = turret_name

        # Calculate max capacity (Circle: 4 * R^2, Triangle/Sector/Cone: 2 * R^2)
        if "tri" in self.shape or "sec" in self.shape or "cone" in self.shape:
            self.max_capacity = 2.0 * (self.radius ** 2)
            self.shape_name = "삼각형 범위"
        else:
            self.max_capacity = 4.0 * (self.radius ** 2)
            self.shape_name = "원형 범위"

class ActiveProjectile:
    def __init__(self, turret_obj, pattern, weapon_data, source_pos, target_monster, target_pos):
        self.turret_obj = turret_obj
        self.pattern = pattern.lower()
        self.weapon_data = weapon_data
        self.pos = source_pos
        self.target_monster = target_monster
        self.target_pos = target_pos if target_pos is not None else (target_monster.pos if target_monster else 10.0)
        self.speed = float(weapon_data.get("weaponAmmoSpeed") or 5.0)
        if self.speed <= 0:
            self.speed = 5.0
        self.explosion_range = float(weapon_data.get("weaponExplosionRange") or 1.0)
        self.duration = float(weapon_data.get("weaponAmmoDuration") or 3.0)
        self.time_left = self.duration
        self.hit_monsters = set()

class SimMonster:
    def __init__(self, uid, monster_data, initial_dist=10.0):
        self.uid = uid
        self.id = monster_data.get("monsterId")
        self.name = monster_data.get("monsterName") or self.id
        self.def_type = monster_data.get("monsterDefType") or "S"
        self.grade = monster_data.get("monsterGrade") or "A"
        self.max_hp = float(monster_data.get("monsterHp") or 10.0)
        self.hp = self.max_hp
        self.base_def = float(monster_data.get("monsterDef") or 0.0)
        self.power = float(monster_data.get("monsterPower") or 5.0)
        self.base_speed = float(monster_data.get("monsterSpeed") or 1.0)
        self.range = float(monster_data.get("monsterRange") or 0.5)
        self.atk_cycle = float(monster_data.get("monsterAtkcycle") or 1.5)
        self.atk_cooldown = 0.0
        self.pos = initial_dist

        self.is_stunned = False
        self.is_slowed = False
        self.is_def_down = False

        # Determine hitbox size (Small=1, Medium=2, Large=4, Boss=8)
        raw_size = monster_data.get("monsterSize")
        if raw_size is not None and float(raw_size) > 0:
            self.hitbox_size = float(raw_size)
        else:
            dtype = str(self.def_type).upper()
            mgrade = str(self.grade).upper()
            if "BOSS" in mgrade:
                self.hitbox_size = 8.0
            elif dtype == "B":
                self.hitbox_size = 4.0
            elif dtype == "M":
                self.hitbox_size = 2.0
            else:
                self.hitbox_size = 1.0

    @property
    def current_def(self):
        if self.is_def_down:
            return max(0.0, self.base_def * 0.7)
        return self.base_def

    @property
    def current_speed(self):
        if self.is_stunned:
            return 0.0
        if self.is_slowed:
            return self.base_speed * 0.7
        return self.base_speed

class SimTrainCar:
    def __init__(self, car_type, index, name, hp, shield, armor_def, coach_slot=None):
        self.car_type = car_type    # 'locomotive' or 'coach'
        self.index = index          # 0 for loco, 1..N for coaches
        self.name = name
        self.max_hp = float(hp)
        if self.max_hp <= 0:
            self.max_hp = 500.0
        self.hp = self.max_hp
        self.max_shield = float(shield)
        self.shield = self.max_shield
        self.armor_def = float(armor_def)
        self.is_destroyed = False
        self.coach_slot = coach_slot  # CoachSlot model reference
        self.turrets = []

    def take_damage(self, dmg):
        if self.is_destroyed:
            return 0.0, 0.0, 0.0

        shield_dmg = 0.0
        hp_dmg = 0.0
        rem_dmg = dmg

        if self.shield > 0:
            shield_dmg = min(self.shield, rem_dmg)
            self.shield -= shield_dmg
            rem_dmg -= shield_dmg

        if rem_dmg > 0:
            hp_dmg = min(self.hp, rem_dmg)
            self.hp -= hp_dmg
            if self.hp <= 0:
                self.hp = 0.0
                self.is_destroyed = True

        return shield_dmg + hp_dmg, shield_dmg, hp_dmg

class SimTurret:
    def __init__(self, sim_car, turret_idx, weapon_data, coach_slot=None):
        self.sim_car = sim_car
        self.turret_idx = turret_idx
        self.weapon_data = weapon_data
        self.coach_slot = coach_slot  # CoachSlot instance
        self.id = weapon_data.get("weaponId")
        self.name = weapon_data.get("weaponName") or self.id

        car_name = sim_car.name if sim_car else "기관차"
        self.full_name = f"{car_name}-포탑#{turret_idx}({self.name})"

        self.power = float(weapon_data.get("weaponPower") or 10.0)
        self.range = float(weapon_data.get("weaponRange") or 5.0)
        self.atk_cycle = float(weapon_data.get("weaponAtkcycle") or 1.0)
        self.cooldown = 0.0

        self.land_type = str(weapon_data.get("weaponLandType") or "L").strip().upper() # 'L' (Land), 'F' (Flight)
        self.weapon_type = weapon_data.get("weaponType") or "normal"
        self.pattern = str(weapon_data.get("weaponPaturn") or "single").strip().lower()
        self.ammo_much = int(weapon_data.get("weaponAmmonMuch") or 1)

        self.total_damage_dealt = 0.0
        self.kills = 0

    @property
    def is_active(self):
        return self.sim_car is not None and not self.sim_car.is_destroyed

    def get_effective_crew_bonus(self):
        """Calculates crew bonus matching weaponLandType (L=Land, F=Air) with synergy multiplier"""
        if not self.coach_slot or not self.coach_slot.crew:
            return 0.0, 1.0, 0.0

        eff_crew = self.coach_slot.get_effective_crew_stats()
        syn = eff_crew["synergy"]

        if self.land_type == "L":
            bonus = eff_crew["landpower"] # Synergy already applied
        elif self.land_type == "F":
            bonus = eff_crew["flypower"]  # Synergy already applied
        else:
            bonus = max(eff_crew["landpower"], eff_crew["flypower"])

        return bonus, syn, (eff_crew["raw_landpower"] if self.land_type == "L" else eff_crew["raw_flypower"])

    def calculate_damage_against(self, monster):
        t_power = self.power
        crew_bonus, synergy, raw_bonus = self.get_effective_crew_bonus()
        attr_bonus = get_attribute_bonus(self.weapon_type, monster.def_type)
        m_def = monster.current_def

        # Formal Formula: {(포탑위력 + 승무원위력*시너지) * (1 + 속성보너스)} * {10 / (10 + 방어력)}
        effective_power = t_power + crew_bonus
        base_dmg = effective_power * (1.0 + attr_bonus)
        def_factor = 10.0 / (10.0 + m_def)
        damage = max(0.5, base_dmg * def_factor)
        return round(damage, 2), attr_bonus, crew_bonus

class BattleSimulationEngine:
    def __init__(self, train_config, enemy_group_config, monster_data_map, dt=0.05):
        self.train_config = train_config
        self.enemy_group_config = enemy_group_config
        self.monster_data_map = monster_data_map
        self.dt = dt

        self.locomotive_car = None
        self.coach_cars = []
        self.all_cars = []

        # Locomotive Car Setup (NO crew on locomotive!)
        if train_config.locomotive:
            ldata = train_config.locomotive
            gen_shield = train_config.generator.get("generatorShieldUp", 0) if train_config.generator else 0
            loco_hp = (ldata.get("locomotiveHp") or 1000)
            loco_shield = (ldata.get("locomotiveShield") or 0) + gen_shield
            loco_def = (ldata.get("locomotiveDef") or 10)

            self.locomotive_car = SimTrainCar(
                car_type="locomotive",
                index=0,
                name=f"기관차 ({ldata.get('locomotiveName', '기관차')})",
                hp=loco_hp,
                shield=loco_shield,
                armor_def=loco_def
            )
            self.all_cars.append(self.locomotive_car)

            # Setup Turrets mounted on Locomotive (up to 2 turrets)
            for t_idx, wdata in enumerate(train_config.locomotive_turrets):
                turret_obj = SimTurret(self.locomotive_car, t_idx + 1, wdata, coach_slot=None)
                self.locomotive_car.turrets.append(turret_obj)

        # Coach Cars Setup
        gen_shield = train_config.generator.get("generatorShieldUp", 0) if train_config.generator else 0
        for cslot in train_config.coaches:
            cdata = cslot.couch_data
            eff_crew = cslot.get_effective_crew_stats()
            chp = cdata.get("couchHp") or 500
            cshield = (cdata.get("couchShield") or 0) + gen_shield # Base coach shield + Generator shield bonus!
            cdef = (cdata.get("couchDef") or 10) + eff_crew["def"] # Synergy applied defense

            car_obj = SimTrainCar(
                car_type="coach",
                index=cslot.index,
                name=f"객차 #{cslot.index} ({cslot.get_name()})",
                hp=chp,
                shield=cshield,
                armor_def=cdef,
                coach_slot=cslot
            )
            self.coach_cars.append(car_obj)
            self.all_cars.append(car_obj)

            # Setup Turrets mounted on this Coach
            for t_idx, wdata in enumerate(cslot.turrets):
                turret_obj = SimTurret(car_obj, t_idx + 1, wdata, coach_slot=cslot)
                car_obj.turrets.append(turret_obj)

        # Setup Monsters from Enemy Config
        self.monsters = []
        m_idx = 1
        for mid, cnt in enemy_group_config.monster_counts.items():
            mdata = monster_data_map.get(mid)
            if mdata:
                for _ in range(cnt):
                    m_obj = SimMonster(f"{mdata.get('monsterName', mid)}#{m_idx}", mdata, initial_dist=10.0)
                    self.monsters.append(m_obj)
                    m_idx += 1

        self.projectiles = []
        self.debuff_zones = []
        self.combat_logs = []

        self.current_time = 0.0
        self.max_simulation_time = 600.0  # Max 10 minutes simulation time for slow monsters (e.g. Lava speed 0.1)
        self.result = None

    def get_all_active_turrets(self):
        active = []
        for car in self.all_cars:
            if not car.is_destroyed:
                for t in car.turrets:
                    if t.is_active:
                        active.append(t)
        return active

    def log(self, event_type, attacker, target, damage, target_hp, details=""):
        entry = {
            "time": round(self.current_time, 2),
            "event_type": event_type,
            "attacker": attacker,
            "target": target,
            "damage": round(damage, 2),
            "target_hp": round(max(0.0, target_hp), 2),
            "details": details
        }
        self.combat_logs.append(entry)

    def run_full_simulation(self):
        while self.result is None and self.current_time < self.max_simulation_time:
            self.step()
        
        if self.result is None:
            self.result = "TIMEOUT (시간 초과)"

        return self.get_summary()

    def step(self):
        if self.result is not None:
            return

        self.current_time += self.dt

        # 1. Update Debuff Zones
        active_zones = []
        for z in self.debuff_zones:
            z.time_left -= self.dt
            if z.time_left > 0:
                active_zones.append(z)
        self.debuff_zones = active_zones

        # 2. Reset and Apply Debuffs to Monsters
        living_monsters = [m for m in self.monsters if m.hp > 0]
        if not living_monsters:
            self.result = "VICTORY (승리 - 모든 적 퇴치)"
            return

        for m in living_monsters:
            m.is_stunned = False
            m.is_slowed = False
            m.is_def_down = False

        for z in self.debuff_zones:
            # Filter living monsters in debuff zone range and sort by distance to zone center
            monsters_in_zone = [m for m in self.monsters if m.hp > 0 and abs(m.pos - z.pos) <= z.radius]
            monsters_in_zone.sort(key=lambda m: abs(m.pos - z.pos))

            used_capacity = 0.0
            hit_count = 0
            for m in monsters_in_zone:
                if m.hp <= 0:
                    continue
                if used_capacity + m.hitbox_size <= z.max_capacity or hit_count == 0:
                    used_capacity += m.hitbox_size
                    hit_count += 1

                    eff = z.debuff_effect
                    if "stun" in eff:
                        m.is_stunned = True
                    if "slow" in eff:
                        m.is_slowed = True
                    if "def" in eff:
                        m.is_def_down = True
                    if "dot" in eff:
                        dot_dmg = z.power * self.dt
                        m.hp -= dot_dmg
                        self.log("DoT피해", z.turret_name or "디버프장판", m.uid, dot_dmg, m.hp, f"지속 장판 피해 (용량:{used_capacity:.1f}/{z.max_capacity:.1f}칸)")
                else:
                    break

        living_monsters = [m for m in self.monsters if m.hp > 0]
        if not living_monsters:
            self.result = "VICTORY (승리 - 모든 적 퇴치)"
            return

        # 3. Active Turrets Firing Logic
        active_turrets = self.get_all_active_turrets()
        for t in active_turrets:
            t.cooldown -= self.dt
            if t.cooldown <= 0:
                living_in_range = [m for m in self.monsters if m.hp > 0 and m.pos <= t.range]
                if living_in_range:
                    target = min(living_in_range, key=lambda m: m.pos)
                    self._fire_turret(t, target)
                    t.cooldown = t.atk_cycle

        # 4. Update Projectiles
        remaining_projectiles = []
        for p in self.projectiles:
            p.time_left -= self.dt
            turret = p.turret_obj

            if p.pattern == "single":
                target = p.target_monster
                # If target is dead (hp <= 0), re-target to closest living monster in range
                if not target or target.hp <= 0:
                    living_in_range = [m for m in self.monsters if m.hp > 0 and m.pos <= turret.range]
                    if living_in_range:
                        target = min(living_in_range, key=lambda m: m.pos)
                        p.target_monster = target
                    else:
                        target = None

                if target and target.hp > 0:
                    dist_to_target = abs(p.pos - target.pos)
                    move_dist = p.speed * self.dt
                    if dist_to_target <= move_dist:
                        dmg, attr_bonus, crew_bonus = turret.calculate_damage_against(target)
                        target.hp -= dmg
                        turret.total_damage_dealt += dmg
                        details = f"상성: {attr_bonus*100:+.0f}%, 승무원위력: +{crew_bonus:.1f}, 적방어: {target.current_def:.1f}"
                        self.log("포탑공격", turret.full_name, target.uid, dmg, target.hp, details)

                        if target.hp <= 0:
                            turret.kills += 1
                            self.log("적처치", turret.full_name, target.uid, 0, 0, "몬스터 격파!")
                    else:
                        dir_sign = -1 if target.pos < p.pos else 1
                        p.pos += dir_sign * move_dist
                        remaining_projectiles.append(p)

            elif p.pattern in ("blast", "curved", "debuff"):
                dist = abs(p.pos - p.target_pos)
                move_dist = p.speed * self.dt
                if dist <= move_dist:
                    shape = str(p.weapon_data.get("weaponZoneShape") or "circle").strip().lower()
                    exp_range = max(0.5, p.explosion_range)

                    # Calculate AoE Capacity (Circle: 4 * R^2, Triangle/Sector/Cone: 2 * R^2)
                    if "tri" in shape or "sec" in shape or "cone" in shape:
                        max_capacity = 2.0 * (exp_range ** 2)
                        shape_name = "삼각형 범위"
                    else:
                        max_capacity = 4.0 * (exp_range ** 2)
                        shape_name = "원형 범위"

                    self.log("범위폭발", turret.full_name, f"지점({p.target_pos:.1f})", 0, 0, f"형상:{shape_name}, R={exp_range:.1f}, 수용용량={max_capacity:.1f}칸")

                    # 1. Filter LIVING monsters (hp > 0) within explosion range
                    monsters_in_range = [m for m in self.monsters if m.hp > 0 and abs(m.pos - p.target_pos) <= exp_range]
                    # 2. Sort by distance to explosion center
                    monsters_in_range.sort(key=lambda m: abs(m.pos - p.target_pos))

                    # 3. Apply damage up to max_capacity based on monster hitbox_size
                    used_capacity = 0.0
                    hit_count = 0
                    for m in monsters_in_range:
                        if m.hp <= 0:
                            continue
                        if used_capacity + m.hitbox_size <= max_capacity or hit_count == 0:
                            dmg, attr_bonus, crew_bonus = turret.calculate_damage_against(m)
                            m.hp -= dmg
                            turret.total_damage_dealt += dmg
                            used_capacity += m.hitbox_size
                            hit_count += 1
                            self.log("폭발피해", turret.full_name, m.uid, dmg, m.hp, f"범위피해 (크기:{m.hitbox_size:.0f}칸, 누적용량:{used_capacity:.1f}/{max_capacity:.1f}칸, 상성:{attr_bonus*100:+.0f}%)")
                            if m.hp <= 0:
                                turret.kills += 1
                                self.log("적처치", turret.full_name, m.uid, 0, 0, "몬스터 격파!")
                        else:
                            break
                else:
                    dir_sign = -1 if p.target_pos < p.pos else 1
                    p.pos += dir_sign * move_dist
                    remaining_projectiles.append(p)

            elif p.pattern == "pierce":
                p.pos -= p.speed * self.dt
                for m in self.monsters:
                    if m.hp > 0 and m.uid not in p.hit_monsters and abs(m.pos - p.pos) <= 0.8:
                        p.hit_monsters.add(m.uid)
                        dmg, attr_bonus, crew_bonus = turret.calculate_damage_against(m)
                        m.hp -= dmg
                        turret.total_damage_dealt += dmg
                        self.log("관통피해", turret.full_name, m.uid, dmg, m.hp, f"관통 탄환 (승무원위력: +{crew_bonus:.1f})")
                        if m.hp <= 0:
                            turret.kills += 1
                            self.log("적처치", turret.full_name, m.uid, 0, 0, "몬스터 격파!")

                if p.time_left > 0 and p.pos > 0:
                    remaining_projectiles.append(p)

            elif p.pattern == "shot":
                p.pos -= p.speed * self.dt
                hit = False
                for m in self.monsters:
                    if m.hp > 0 and abs(m.pos - p.pos) <= 0.5:
                        hit = True
                        dmg, attr_bonus, crew_bonus = turret.calculate_damage_against(m)
                        m.hp -= dmg
                        turret.total_damage_dealt += dmg
                        self.log("샷건피해", turret.full_name, m.uid, dmg, m.hp, f"산발 탄환 (승무원위력: +{crew_bonus:.1f})")
                        if m.hp <= 0:
                            turret.kills += 1
                            self.log("적처치", turret.full_name, m.uid, 0, 0, "몬스터 격파!")
                        break
                if not hit and p.time_left > 0 and p.pos > 0:
                    remaining_projectiles.append(p)

        self.projectiles = remaining_projectiles

        # 5. Monster Movement & Targeting Logic
        target_car = None
        for car in reversed(self.all_cars):
            if not car.is_destroyed:
                target_car = car
                break

        if target_car is None:
            self.result = "DEFEAT (패배 - 기관차 및 전 객체 파괴)"
            return

        for m in living_monsters:
            if m.hp <= 0:
                continue

            m.atk_cooldown -= self.dt

            if m.pos > m.range:
                m.pos = max(0.0, m.pos - m.current_speed * self.dt)

            if m.pos <= max(0.5, m.range):
                if m.atk_cooldown <= 0 and not m.is_stunned:
                    enemy_power = m.power
                    def_factor = 10.0 / (10.0 + target_car.armor_def)
                    dmg = max(1.0, enemy_power * def_factor)

                    tot_dmg, shield_dmg, hp_dmg = target_car.take_damage(dmg)
                    m.atk_cooldown = m.atk_cycle

                    log_detail = f"Def: {target_car.armor_def:.1f}"
                    if shield_dmg > 0:
                        log_detail += f", 보호막 {shield_dmg:.1f} 흡수 (남은 🛡️ {target_car.shield:.1f})"
                    log_detail += f", 남은 HP: {target_car.hp:.1f}/{target_car.max_hp:.1f}"

                    self.log(
                        "적공격", m.uid, target_car.name,
                        tot_dmg, target_car.hp,
                        log_detail
                    )

                    if target_car.is_destroyed:
                        if target_car.car_type == "locomotive":
                            self.result = "DEFEAT (패배 - 기관차 파괴)"
                            self.log("기관차파괴", m.uid, target_car.name, 0, 0, "💥 기관차 파괴됨! 게임 오버 (DEFEAT)")
                            return
                        else:
                            disabled_turret_cnt = len(target_car.turrets)
                            self.log("객차파괴", m.uid, target_car.name, 0, 0, f"💥 {target_car.name} 파괴됨! 탑재 포탑 {disabled_turret_cnt}개 무력화!")
                            target_car = None
                            for car in reversed(self.all_cars):
                                if not car.is_destroyed:
                                    target_car = car
                                    break
                            if target_car is None:
                                self.result = "DEFEAT (패배 - 기관차 파괴)"
                                return

    def _fire_turret(self, turret, target):
        pattern = turret.pattern
        if pattern == "debuff":
            shape = turret.weapon_data.get("weaponZoneShape") or "circle"
            debuff_effect = turret.weapon_data.get("weaponDebuff") or "slow"
            sp_loc = str(turret.weapon_data.get("weaponSP") or "target").strip().lower()
            zone_pos = 0.0 if sp_loc == "head" else target.pos
            duration = float(turret.weapon_data.get("weaponAmmoDuration") or 3.0)
            exp_range = float(turret.weapon_data.get("weaponExplosionRange") or 2.0)

            z = ActiveDebuffZone(
                zone_type="debuff",
                shape=shape,
                location_type=sp_loc,
                pos=zone_pos,
                duration=duration,
                power=turret.power,
                debuff_effect=debuff_effect,
                radius=exp_range,
                turret_name=turret.full_name
            )
            self.debuff_zones.append(z)
            self.log("디버프장판", turret.full_name, f"위치({zone_pos:.1f})", 0, 0, f"효과:{debuff_effect}, 지속시간:{duration}s, 형상:{z.shape_name}, R={z.radius:.1f}, 수용용량={z.max_capacity:.1f}칸")

        elif pattern == "shot":
            count = max(1, turret.ammo_much)
            for _ in range(count):
                p = ActiveProjectile(turret, "shot", turret.weapon_data, 0.0, target, target.pos)
                self.projectiles.append(p)
            self.log("포탑발사", turret.full_name, target.uid, 0, target.hp, f"샷건 {count}발 발사")

        else:
            p = ActiveProjectile(turret, pattern, turret.weapon_data, 0.0, target, target.pos)
            self.projectiles.append(p)
            self.log("포탑발사", turret.full_name, target.uid, 0, target.hp, f"패턴: {pattern}")

    def get_summary(self):
        tot_dmg_dealt = sum(sum(t.total_damage_dealt for t in car.turrets) for car in self.all_cars)
        tot_kills = sum(sum(t.kills for t in car.turrets) for car in self.all_cars)

        car_summaries = []
        for car in self.all_cars:
            car_summaries.append({
                "name": car.name,
                "type": car.car_type,
                "hp_left": round(car.hp, 2),
                "max_hp": round(car.max_hp, 2),
                "is_destroyed": car.is_destroyed,
                "turrets_count": len(car.turrets)
            })

        turret_summaries = []
        for car in self.all_cars:
            for t in car.turrets:
                crew_b, syn, raw_b = t.get_effective_crew_bonus()
                turret_summaries.append({
                    "full_name": t.full_name,
                    "land_type": t.land_type,
                    "base_power": t.power,
                    "crew_power_bonus": crew_b,
                    "effective_power": t.power + crew_b,
                    "pattern": t.pattern,
                    "is_active": t.is_active,
                    "total_damage": round(t.total_damage_dealt, 2),
                    "kills": t.kills
                })

        return {
            "result": self.result or "IN_PROGRESS",
            "duration": round(self.current_time, 2),
            "cars": car_summaries,
            "locomotive_alive": self.locomotive_car is not None and not self.locomotive_car.is_destroyed,
            "total_damage_dealt": round(tot_dmg_dealt, 2),
            "total_kills": tot_kills,
            "turrets": turret_summaries,
            "log_count": len(self.combat_logs)
        }

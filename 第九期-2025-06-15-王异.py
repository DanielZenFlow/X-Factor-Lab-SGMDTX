import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# ==============================================================================
# X-Factor Lab - 三国谋定天下王异技能分析工具
# 使用蒙特卡洛方法模拟战斗，找出最优技能搭配
# GitHub: https://github.com/DanielZenFlow/X-Factor-Lab-SGMDTX
# ==============================================================================

"""
X-Factor Lab: 三国谋定天下异技能搭配蒙特卡洛分析

项目描述: 通过蒙特卡洛模拟方法分析三国谋定天下中王异武将的最优技能搭配与辅助组合
版本: 1.0.0
作者: DanielZenFlow
许可证: MIT License
项目地址: https://github.com/DanielZenFlow/X-Factor-Lab-SGMDTX
问题反馈: https://github.com/DanielZenFlow/X-Factor-Lab-SGMDTX/issues

Copyright (c) 2025 DanielZenFlow
Licensed under MIT License - see LICENSE file for details
"""

# ==============================================================================
# 核心参数配置
# ==============================================================================
模拟次数 = 50000
战斗回合数 = 4
ENEMIES = 3

# ==============================================================================
# 技能与武将系数定义
# ==============================================================================
# 王异技能
QCFY_PROB = 0.55
QCFY_DMG_COEFF_PER_TARGET = 1.00
QCFY_TARGETS = 2
YZPM_DMG_BOOST_PER_STACK = 0.078
YZPM_MAX_STACKS = 5
YZPM_NA_PROC_PROB = 0.56
MEHD_BASE_PROB = 0.75
MEHD_EXTRA_HIT_PROB = 0.50
MEHD_DMG_COEFF_T1 = 0.412
MEHD_DMG_COEFF_INCREASE_PER_TURN = 0.123
PASSIVE1_NA_THRESHOLD1 = 2
PASSIVE1_NA_THRESHOLD2 = 4
PASSIVE1_PURSUIT_BOOST = 0.05
PASSIVE2_PURSUIT_BOOST_DURATION = 4
PASSIVE2_PURSUIT_BOOST = 0.05
# 辅助武将
MATENG_DURATION = 3
MATENG_PURSUIT_DMG_BOOST = 0.30
MATENG_EXTRA_NA_PROB = 0.65
ZHANGCH_XINJI_GAIN_PROB = 0.25
ZHANGCH_XINJI_DMG_BOOST_PER_STACK = 0.03
ZHANGCH_XINJI_MAX_STACKS = 10
ZHANGCH_XINJI_PURSUIT_LOCK_THRESHOLD = 6
ZHENJI_LUOSHEN_DMG_BOOST = 0.25
ZHENJI_QIMOU_MULTIPLIER = 1.5
PANGTONG_EFFECTIVE_DMG_MULTIPLIER = 1.42
XUNYU_KANPO_MULTIPLIER = 1.15
XUNYU_QIMOU_CHANCE = 0.56
XUNYU_QIMOU_EFFECT_MULTIPLIER = 1.5
XUNYU_AVG_QIMOU_MULTIPLIER = (1 - XUNYU_QIMOU_CHANCE) * 1.0 + XUNYU_QIMOU_CHANCE * XUNYU_QIMOU_EFFECT_MULTIPLIER
XUNYU_EFFECTIVE_DMG_MULTIPLIER = XUNYU_KANPO_MULTIPLIER * XUNYU_AVG_QIMOU_MULTIPLIER

# --- 辅助函数 ---
def get_mehd_current_coeff(turn_idx):
    return MEHD_DMG_COEFF_T1 + turn_idx * MEHD_DMG_COEFF_INCREASE_PER_TURN

def get_wangyi_mehd_activation_rate_dynamic(cumulative_na_completed_before_this_na, current_turn_idx):
    p1_bonus = 0.0
    if cumulative_na_completed_before_this_na >= PASSIVE1_NA_THRESHOLD1: p1_bonus += PASSIVE1_PURSUIT_BOOST
    if cumulative_na_completed_before_this_na >= PASSIVE1_NA_THRESHOLD2: p1_bonus += PASSIVE1_PURSUIT_BOOST
    p2_bonus = PASSIVE2_PURSUIT_BOOST if current_turn_idx < PASSIVE2_PURSUIT_BOOST_DURATION else 0.0
    return MEHD_BASE_PROB + p1_bonus + p2_bonus

# ==============================================================================
# 模拟核心函数 (战术执行层)
# ==============================================================================
def run_single_simulation_wangyi(support_config=None):
    total_damage_coeff = 0.0
    
    wangyi_status = {
        'yzpm_stacks': 0,
        'cumulative_na': 0,
        'xinji_stacks': 0,
    }

    for current_turn_num in range(1, 战斗回合数 + 1):
        yzpm_na_has_fired_this_turn = False
        
        is_zhenji_active_this_turn = (support_config and support_config['name'] == 'ZhenJi')
        zhenji_qimou_available_this_turn = is_zhenji_active_this_turn

        def process_attack(attack_type):
            nonlocal total_damage_coeff, yzpm_na_has_fired_this_turn, zhenji_qimou_available_this_turn

            wangyi_status['yzpm_stacks'] = min(YZPM_MAX_STACKS, wangyi_status['yzpm_stacks'] + 1)
            wangyi_status['cumulative_na'] += 1
            if support_config and support_config['name'] == 'ZhangChunhua':
                if random.random() < ZHANGCH_XINJI_GAIN_PROB:
                    wangyi_status['xinji_stacks'] = min(ZHANGCH_XINJI_MAX_STACKS, wangyi_status['xinji_stacks'] + 1)

            current_yzpm_boost = (1 + wangyi_status['yzpm_stacks'] * YZPM_DMG_BOOST_PER_STACK)
            current_xinji_boost = 1.0
            if support_config and support_config['name'] == 'ZhangChunhua':
                current_xinji_boost = (1 + wangyi_status['xinji_stacks'] * ZHANGCH_XINJI_DMG_BOOST_PER_STACK)

            strategic_damage_dealt_by_this_na_path = False
            
            # 判定【巧策引锋】
            if random.random() < QCFY_PROB:
                strategic_damage_dealt_by_this_na_path = True
                damage_coeff = (QCFY_DMG_COEFF_PER_TARGET * QCFY_TARGETS) * current_yzpm_boost * current_xinji_boost
                
                # 【甄姬】- 即时应用甄姬增益
                if is_zhenji_active_this_turn:
                    damage_coeff *= (1 + ZHENJI_LUOSHEN_DMG_BOOST)
                    if zhenji_qimou_available_this_turn:
                        damage_coeff *= ZHENJI_QIMOU_MULTIPLIER
                        zhenji_qimou_available_this_turn = False
                total_damage_coeff += damage_coeff

            # 判定【谋而后动】(追击技能)
            is_zch_dud_attack = (attack_type == 'zch_dud_na')
            if not is_zch_dud_attack:
                mehd_rate = get_wangyi_mehd_activation_rate_dynamic(wangyi_status['cumulative_na'] - 1, current_turn_num - 1)
                if random.random() < mehd_rate:
                    strategic_damage_dealt_by_this_na_path = True
                    num_mehd_hits = 1 + (1 if random.random() < MEHD_EXTRA_HIT_PROB else 0)
                    
                    for _ in range(num_mehd_hits):
                        mehd_coeff = get_mehd_current_coeff(current_turn_num - 1)
                        base_skill_coeff = (mehd_coeff * ENEMIES) * current_yzpm_boost * current_xinji_boost
                        if support_config and support_config['name'] == 'MaTeng' and current_turn_num <= MATENG_DURATION:
                            base_skill_coeff *= (1 + MATENG_PURSUIT_DMG_BOOST)
                        
                        # 【甄姬】
                        if is_zhenji_active_this_turn:
                            base_skill_coeff *= (1 + ZHENJI_LUOSHEN_DMG_BOOST)
                            if zhenji_qimou_available_this_turn:
                                base_skill_coeff *= ZHENJI_QIMOU_MULTIPLIER
                                zhenji_qimou_available_this_turn = False
                        total_damage_coeff += base_skill_coeff
                        
                        if random.random() < QCFY_PROB:
                            qcfy_from_mehd_coeff = (QCFY_DMG_COEFF_PER_TARGET * QCFY_TARGETS) * current_yzpm_boost * current_xinji_boost
                            # 【甄姬】
                            if is_zhenji_active_this_turn:
                                qcfy_from_mehd_coeff *= (1 + ZHENJI_LUOSHEN_DMG_BOOST)
                                if zhenji_qimou_available_this_turn:
                                    qcfy_from_mehd_coeff *= ZHENJI_QIMOU_MULTIPLIER
                                    zhenji_qimou_available_this_turn = False
                            total_damage_coeff += qcfy_from_mehd_coeff

            # 判定【运智铺谋】的额外普攻
            yzpm_trigger_opportunity_met = (strategic_damage_dealt_by_this_na_path or (support_config and support_config['name'] == 'ZhangChunhua'))
            
            if yzpm_trigger_opportunity_met and not yzpm_na_has_fired_this_turn:
                if random.random() < YZPM_NA_PROC_PROB:
                    yzpm_na_has_fired_this_turn = True
                    main_attack_list.append("yzpm_na")

        main_attack_list = ["base_na_1", "base_na_2_combo"]
        i = 0
        while i < len(main_attack_list):
            process_attack(main_attack_list[i])
            i += 1
        
        additional_attack_list = []
        if support_config:
            if support_config['name'] == 'MaTeng' and current_turn_num <= MATENG_DURATION and random.random() < MATENG_EXTRA_NA_PROB:
                additional_attack_list.append("mateng_na")
            if support_config['name'] == 'ZhangChunhua':
                if wangyi_status['xinji_stacks'] < ZHANGCH_XINJI_PURSUIT_LOCK_THRESHOLD:
                    additional_attack_list.append("zch_dud_na")
                else:
                    additional_attack_list.append("zch_na")
        
        for attack in additional_attack_list:
            process_attack(attack)

    # 最终伤害系数应用其他辅助的全局乘数类增益
    final_damage_coeff = total_damage_coeff
    if support_config:
        # 甄姬的增益已在每次伤害计算时应用，此处不再需要
        if support_config['name'] == 'PangTong':
            final_damage_coeff *= PANGTONG_EFFECTIVE_DMG_MULTIPLIER
        if support_config['name'] == 'XunYu':
            final_damage_coeff *= XUNYU_EFFECTIVE_DMG_MULTIPLIER
            
    return final_damage_coeff

# ==============================================================================
# 主程序入口 (战略规划层)
# ==============================================================================
if __name__ == '__main__':
    try:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
    except:
        plt.rcParams['font.sans-siraf'] = ['SimHei']

    support_list = [
        {'name': '王异 (单独)', 'config': None},
        {'name': '王异 + 马腾', 'config': {'name': 'MaTeng'}},
        {'name': '王异 + 张春华', 'config': {'name': 'ZhangChunhua'}},
        {'name': '王异 + 甄姬', 'config': {'name': 'ZhenJi'}},
        {'name': '王异 + 庞统', 'config': {'name': 'PangTong'}},
        {'name': '王异 + 荀彧', 'config': {'name': 'XunYu'}}
    ]

    results_list = []
    print(f"分析开始，将对每个配置运行 {模拟次数} 次模拟...")

    for support in support_list:
        total_coeffs_for_this_config = [run_single_simulation_wangyi(support['config']) for _ in range(模拟次数)]
        average_coeff = sum(total_coeffs_for_this_config) / 模拟次数
        
        results_list.append({
            '配置': support['name'],
            '4回合期望总伤害系数(%)': average_coeff * 100
        })
    print("\n模拟完成。")

    df_results = pd.DataFrame(results_list)
    
    baseline_coeff = df_results.loc[df_results['配置'] == '王异 (单独)', '4回合期望总伤害系数(%)'].iloc[0]
    df_results['较单独提升百分比(%)'] = ((df_results['4回合期望总伤害系数(%)'] / baseline_coeff) - 1) * 100
    df_results.loc[df_results['配置'] == '王异 (单独)', '较单独提升百分比(%)'] = 0.0
    
    df_results = df_results.sort_values(by='4回合期望总伤害系数(%)', ascending=False).reset_index(drop=True)
    
    print("\n--- 王异不同辅助下4回合期望总伤害系数对比 ")
    pd.options.display.float_format = '{:,.2f}'.format
    print(df_results.to_string(index=False))
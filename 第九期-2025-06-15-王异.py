import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==============================================================================
# X-Factor Lab - 三国谋定天下王异技能分析工具
# 使用蒙特卡洛方法模拟战斗，找出最优技能搭配
# 版本: 2.0.0 (功能整合版)
# ==============================================================================

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
QCFY_PROB = 0.55; QCFY_DMG_COEFF_PER_TARGET = 1.00; QCFY_TARGETS = 2
YZPM_DMG_BOOST_PER_STACK = 0.078; YZPM_MAX_STACKS = 5; YZPM_NA_PROC_PROB = 0.56
MEHD_BASE_PROB = 0.75; MEHD_EXTRA_HIT_PROB = 0.50; MEHD_DMG_COEFF_T1 = 0.412; MEHD_DMG_COEFF_INCREASE_PER_TURN = 0.123
PASSIVE1_NA_THRESHOLD1 = 2; PASSIVE1_NA_THRESHOLD2 = 4; PASSIVE1_PURSUIT_BOOST = 0.05
PASSIVE2_PURSUIT_BOOST_DURATION = 4; PASSIVE2_PURSUIT_BOOST = 0.05
# 辅助武将
MATENG_DURATION = 3; MATENG_PURSUIT_DMG_BOOST = 0.30; MATENG_EXTRA_NA_PROB = 0.65
ZHANGCH_XINJI_GAIN_PROB = 0.25; ZHANGCH_XINJI_DMG_BOOST_PER_STACK = 0.03; ZHANGCH_XINJI_MAX_STACKS = 10; ZHANGCH_XINJI_PURSUIT_LOCK_THRESHOLD = 6
ZHENJI_LUOSHEN_DMG_BOOST = 0.25; ZHENJI_QIMOU_MULTIPLIER = 1.5
PANGTONG_EFFECTIVE_DMG_MULTIPLIER = 1.42
XUNYU_KANPO_MULTIPLIER = 1.15; XUNYU_QIMOU_CHANCE = 0.56; XUNYU_QIMOU_EFFECT_MULTIPLIER = 1.5
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
    damage_coeffs_per_turn = [0.0] * 战斗回合数
    wangyi_status = {'yzpm_stacks': 0, 'cumulative_na': 0, 'xinji_stacks': 0}

    for current_turn_num in range(1, 战斗回合数 + 1):
        turn_idx = current_turn_num - 1
        yzpm_na_has_fired_this_turn = False
        is_zhenji_active_this_turn = (support_config and support_config['name'] == 'ZhenJi')
        zhenji_qimou_available_this_turn = is_zhenji_active_this_turn

        def process_attack(attack_type):
            nonlocal yzpm_na_has_fired_this_turn, zhenji_qimou_available_this_turn

            wangyi_status['yzpm_stacks'] = min(YZPM_MAX_STACKS, wangyi_status['yzpm_stacks'] + 1)
            wangyi_status['cumulative_na'] += 1
            if support_config and support_config['name'] == 'ZhangChunhua':
                if random.random() < ZHANGCH_XINJI_GAIN_PROB:
                    wangyi_status['xinji_stacks'] = min(ZHANGCH_XINJI_MAX_STACKS, wangyi_status['xinji_stacks'] + 1)
            
            current_yzpm_boost = (1 + wangyi_status['yzpm_stacks'] * YZPM_DMG_BOOST_PER_STACK)
            current_xinji_boost = (1 + wangyi_status['xinji_stacks'] * ZHANGCH_XINJI_DMG_BOOST_PER_STACK) if support_config and support_config['name'] == 'ZhangChunhua' else 1.0

            strategic_damage_dealt = False
            
            if random.random() < QCFY_PROB:
                strategic_damage_dealt = True
                damage_coeff = (QCFY_DMG_COEFF_PER_TARGET * QCFY_TARGETS) * current_yzpm_boost * current_xinji_boost
                if is_zhenji_active_this_turn:
                    damage_coeff *= (1 + ZHENJI_LUOSHEN_DMG_BOOST)
                    if zhenji_qimou_available_this_turn:
                        damage_coeff *= ZHENJI_QIMOU_MULTIPLIER; zhenji_qimou_available_this_turn = False
                damage_coeffs_per_turn[turn_idx] += damage_coeff

            if attack_type != 'zch_dud_na':
                mehd_rate = get_wangyi_mehd_activation_rate_dynamic(wangyi_status['cumulative_na'] - 1, turn_idx)
                if random.random() < mehd_rate:
                    strategic_damage_dealt = True
                    num_mehd_hits = 1 + (1 if random.random() < MEHD_EXTRA_HIT_PROB else 0)
                    for _ in range(num_mehd_hits):
                        mehd_coeff = get_mehd_current_coeff(turn_idx)
                        base_skill_coeff = (mehd_coeff * ENEMIES) * current_yzpm_boost * current_xinji_boost
                        if support_config and support_config['name'] == 'MaTeng' and current_turn_num <= MATENG_DURATION:
                            base_skill_coeff *= (1 + MATENG_PURSUIT_DMG_BOOST)
                        if is_zhenji_active_this_turn:
                            base_skill_coeff *= (1 + ZHENJI_LUOSHEN_DMG_BOOST)
                            if zhenji_qimou_available_this_turn:
                                base_skill_coeff *= ZHENJI_QIMOU_MULTIPLIER; zhenji_qimou_available_this_turn = False
                        damage_coeffs_per_turn[turn_idx] += base_skill_coeff
                        
                        if random.random() < QCFY_PROB:
                            qcfy_from_mehd_coeff = (QCFY_DMG_COEFF_PER_TARGET * QCFY_TARGETS) * current_yzpm_boost * current_xinji_boost
                            if is_zhenji_active_this_turn:
                                qcfy_from_mehd_coeff *= (1 + ZHENJI_LUOSHEN_DMG_BOOST)
                                if zhenji_qimou_available_this_turn:
                                    qcfy_from_mehd_coeff *= ZHENJI_QIMOU_MULTIPLIER; zhenji_qimou_available_this_turn = False
                            damage_coeffs_per_turn[turn_idx] += qcfy_from_mehd_coeff
            
            yzpm_trigger_opportunity = (strategic_damage_dealt or (support_config and support_config['name'] == 'ZhangChunhua'))
            if yzpm_trigger_opportunity and not yzpm_na_has_fired_this_turn:
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
                additional_attack_list.append("zch_dud_na" if wangyi_status['xinji_stacks'] < ZHANGCH_XINJI_PURSUIT_LOCK_THRESHOLD else "zch_na")
        
        for attack in additional_attack_list:
            process_attack(attack)

    if support_config:
        if support_config['name'] == 'PangTong':
            damage_coeffs_per_turn = [d * PANGTONG_EFFECTIVE_DMG_MULTIPLIER for d in damage_coeffs_per_turn]
        if support_config['name'] == 'XunYu':
            damage_coeffs_per_turn = [d * XUNYU_EFFECTIVE_DMG_MULTIPLIER for d in damage_coeffs_per_turn]
            
    return damage_coeffs_per_turn

# ==============================================================================
# 主程序入口 (战略规划层)
# ==============================================================================
if __name__ == '__main__':
    # --- 1. 中文字体设置 ---
    try:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            pass # 修正：移除打印语句，保持静默

    # --- 2. 运行模拟 ---
    support_list = [
        {'name': '王异 (单独)', 'config': None},
        {'name': '王异 + 马腾', 'config': {'name': 'MaTeng'}},
        {'name': '王异 + 张春华', 'config': {'name': 'ZhangChunhua'}},
        {'name': '王异 + 甄姬', 'config': {'name': 'ZhenJi'}},
        {'name': '王异 + 庞统', 'config': {'name': 'PangTong'}},
        {'name': '王异 + 荀彧', 'config': {'name': 'XunYu'}}
    ]
    support_name_map = {item['name']: item['name'] for item in support_list}
    
    results_data = {}
    print(f"分析开始，将对每个配置运行 {模拟次数} 次模拟...")
    for support in support_list:
        all_sim_runs = [run_single_simulation_wangyi(support['config']) for _ in range(模拟次数)]
        avg_per_turn_coeffs = np.mean(all_sim_runs, axis=0)
        results_data[support['name']] = avg_per_turn_coeffs
    print("\n模拟完成。")

    # --- 3. 数据处理与日志打印 ---
    df_results_list = []
    for support_name, per_turn_coeffs in results_data.items():
        total_coeff = sum(per_turn_coeffs)
        df_results_list.append({
            '配置': support_name,
            '4回合期望总伤害系数': total_coeff * 100 # 修正: 乘以100转换为数值
        })
    df_results = pd.DataFrame(df_results_list)
    
    baseline_coeff = df_results.loc[df_results['配置'] == '王异 (单独)', '4回合期望总伤害系数'].iloc[0]
    df_results['较单独提升百分比'] = ((df_results['4回合期望总伤害系数'] / baseline_coeff) - 1) * 100
    df_results.loc[df_results['配置'] == '王异 (单独)', '较单独提升百分比'] = 0.0
    
    df_results = df_results.sort_values(by='4回合期望总伤害系数', ascending=False).reset_index(drop=True)
    
    # 修正: 定义自定义格式化，以满足 "7303%" 的显示要求
    df_display = df_results.copy()
    df_display['4回合期望总伤害系数'] = df_display['4回合期望总伤害系数'].apply(lambda x: f"{x:,.2f}%")
    df_display['较单独提升百分比'] = df_display['较单独提升百分比'].apply(lambda x: f"{x:,.2f}%")
    
    print("\n--- 王异不同辅助下4回合期望总伤害系数对比 ---")
    print(df_display.to_string(index=False)) # 保留精髓：在CMD里显示日志结果

    # --- 4. 数据准备 (用于绘图) ---
    df_plot_source = pd.DataFrame(results_data).rename(columns=support_name_map)
    df_cumulative = pd.DataFrame({
        support_name_map.get(key): {
            "前3回合累计": sum(val[:3]) * 100,
            "前4回合累计": sum(val) * 100
        } for key, val in results_data.items()
    }).T
    df_plot_sorted = df_cumulative.sort_values(by="前4回合累计", ascending=False)
    df_boost_plot = df_plot_sorted[df_plot_sorted.index != '王异 (单独)'].copy()
    df_boost_plot['提升百分比 (%)'] = ((df_boost_plot['前4回合累计'] / baseline_coeff) - 1) * 100

    # --- 5. 绘制并保存所有图表 ---
    # 图表A: 前3回合累计期望伤害条形图
    print("\n正在生成【前3回合】累计伤害图...")
    plt.figure(figsize=(16, 10))
    ax1 = df_plot_sorted["前3回合累计"].plot(kind='bar', color='skyblue', edgecolor='black', zorder=2)
    ax1.set_title('不同辅助下王异【前3回合】累计期望伤害系数', fontsize=24, fontweight='bold', pad=20)
    ax1.set_ylabel('期望伤害系数 (%)', fontsize=18, fontweight='bold')
    ax1.set_xlabel('')
    ax1.tick_params(axis='y', labelsize=14)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=0, ha="center", fontsize=30, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.7, axis='y')
    for p in ax1.patches:
        ax1.annotate(f"{p.get_height():.0f}%", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', xytext=(0, 10), textcoords='offset points', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig("damage_cumulative_3_turns_separate.png", dpi=120)
    plt.close()
    print("图表已保存为 damage_cumulative_3_turns_separate.png")

    # 图表B: 前4回合累计期望伤害条形图
    print("\n正在生成【前4回合】累计伤害图...")
    plt.figure(figsize=(16, 10))
    ax2 = df_plot_sorted["前4回合累计"].plot(kind='bar', color='lightcoral', edgecolor='black', zorder=2)
    ax2.set_title('不同辅助下王异【前4回合】累计期望伤害系数', fontsize=24, fontweight='bold', pad=20)
    ax2.set_ylabel('期望伤害系数 (%)', fontsize=18, fontweight='bold')
    ax2.set_xlabel('')
    ax2.tick_params(axis='y', labelsize=14)
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=0, ha="center", fontsize=30, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.7, axis='y')
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.0f}%", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', xytext=(0, 10), textcoords='offset points', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig("damage_cumulative_4_turns_separate.png", dpi=120)
    plt.close()
    print("图表已保存为 damage_cumulative_4_turns_separate.png")

    # 图表C: 各辅助对王异4回合总伤害提升百分比
    print("\n正在生成【伤害提升百分比】对比图...")
    plt.figure(figsize=(16, 10))
    ax3 = df_boost_plot['提升百分比 (%)'].plot(kind='bar', color='mediumseagreen', edgecolor='black', zorder=2)
    ax3.set_title('各辅助对王异4回合总伤害提升对比', fontsize=24, fontweight='bold', pad=20)
    ax3.set_ylabel('伤害提升百分比 (%)', fontsize=18, fontweight='bold')
    ax3.set_xlabel('')
    ax3.tick_params(axis='y', labelsize=14)
    ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0, ha="center", fontsize=30, fontweight='bold')
    ax3.grid(True, linestyle='--', alpha=0.7, axis='y')
    for p in ax3.patches:
        ax3.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', xytext=(0, 10), textcoords='offset points', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig("support_boost_percentage.png", dpi=120)
    plt.close()
    print("图表已保存为 support_boost_percentage.png")

    # 图表D: 每回合伤害趋势折线图
    print("\n正在生成【每回合伤害趋势】折线图...")
    df_per_turn_cn = df_plot_source.rename(columns=support_name_map)
    df_per_turn_cn.index = [f'第{i+1}回合' for i in range(df_per_turn_cn.shape[0])]
    plt.figure(figsize=(14, 8))
    for support_key_cn in df_per_turn_cn.columns:
        # 修正: 将系数乘以100以显示为百分比
        plt.plot(df_per_turn_cn.index, df_per_turn_cn[support_key_cn] * 100, marker='o', linestyle='-', linewidth=2, label=support_key_cn)
    plt.title('不同辅助下王异「每回合」期望伤害系数趋势', fontsize=16, fontweight='bold')
    plt.xlabel('回合数', fontsize=12)
    plt.ylabel('期望伤害系数 (%)', fontsize=12)
    plt.legend(title='配置')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("damage_trend_per_turn_lineplot.png", dpi=120)
    plt.close()
    print("每回合伤害趋势折线图已保存为 damage_trend_per_turn_lineplot.png。")

    print("\n所有分析和绘图任务已成功完成。")
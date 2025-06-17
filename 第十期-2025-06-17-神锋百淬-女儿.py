import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# ==============================================================================
# X-Factor Lab - 三国谋定天下女儿技能分析工具
# 使用蒙特卡洛方法模拟战斗，找出最优技能搭配
# GitHub: https://github.com/DanielZenFlow/X-Factor-Lab-SGMDTX
# ==============================================================================

"""
X-Factor Lab: 三国谋定天下女儿技能搭配蒙特卡洛分析

项目描述: 通过蒙特卡洛模拟方法分析三国谋定天下中女儿武将的最优技能搭配与辅助组合
版本: 1.0.0
作者: DanielZenFlow
许可证: MIT License
项目地址: https://github.com/DanielZenFlow/X-Factor-Lab-SGMDTX
问题反馈: https://github.com/DanielZenFlow/X-Factor-Lab-SGMDTX/issues

Copyright (c) 2025 DanielZenFlow
Licensed under MIT License - see LICENSE file for details
"""


# ==============================================================================
# 核心参数配置 (用户可修改)
# ==============================================================================
模拟次数 = 50000
战斗回合数 = 5

# ==============================================================================
# 技能系数定义
# ==============================================================================
武女传_增伤 = 0.05
突战_追击增伤 = 0.07
疾战_追击增伤 = 0.09
神锋_基础发动率, 神锋_自带发动率加成, 神锋_伤害系数 = 0.70, 0.06, 0.80
运智_每层谋略增伤, 运智_额外普攻发动率 = 0.078, 0.56
谋而后动_基础发动率, 谋而后动_基础伤害系数, 谋而后动_额外发动率, 谋而后动_每回合伤害提升 = 0.75, 0.412, 0.50, 0.123
铁骑_基础发动率, 铁骑_基础伤害系数, 铁骑_发动后奇谋提升, 铁骑_每回合伤害衰减 = 0.40, 4.00, 0.20, 1.00
智破千军_发动率, 智破千军_伤害系数, 智破千军_增伤概率, 智破千军_增伤幅度 = 0.50, 1.80, 0.40, 0.20
张春华_单次伤害系数, 张春华_心计获得概率, 张春华_每层心计增伤 = 0.721, 0.25, 0.0309
马腾_追击增伤, 马腾_额外普攻发动率 = 0.30, 0.65
甄姬_增伤 = 0.25
庞统_传递增伤 = 0.42
荀彧_奇谋率提升, 荀彧_看破增伤 = 0.56, 0.15
荀彧_新增被动奇谋率, 荀彧_新增被动奇谋伤害 = 0.06, 0.10

# ==============================================================================
# 模拟核心函数
# ==============================================================================
def run_single_simulation(build_配置, support_配置=None):
    总伤害 = 0.0
    女儿状态 = {
        '连击率': 1.0, '追击伤害加成': 突战_追击增伤 + 疾战_追击增伤,
        '总伤害乘数': 1.0 + 武女传_增伤, '奇谋率': 0.0,
        '奇谋伤害加成': 0.5, '运智铺谋层数': 0,
    }
    整备状态池 = list(range(1, 9)); random.shuffle(整备状态池)
    已获得整备 = set()
    张春华心计层数 = 0

    if support_配置:
        if support_配置['name'] == 'PangTong': 女儿状态['总伤害乘数'] += 庞统_传递增伤
        if support_配置['name'] == 'XunYu':
            女儿状态['奇谋率'] += 荀彧_奇谋率提升 + 荀彧_新增被动奇谋率
            女儿状态['总伤害乘数'] += 荀彧_看破增伤
            女儿状态['奇谋伤害加成'] += 荀彧_新增被动奇谋伤害

    for r in range(1, 战斗回合数 + 1):
        本回合运智额外普攻已触发 = False
        本回合甄姬增伤 = 0
        本回合甄姬必定奇谋可用 = False
        if support_配置 and support_配置['name'] == 'ZhenJi':
            本回合甄姬增伤 = 甄姬_增伤; 本回合甄姬必定奇谋可用 = True

        普攻列表 = ["普攻1", "普攻2"]
        def process_attack(attack_type):
            nonlocal 总伤害, 本回合运智额外普攻已触发, 本回合甄姬必定奇谋可用, 已获得整备, 张春华心计层数
            女儿状态['运智铺谋层数'] += 1
            if support_配置 and support_配置['name'] == 'ZhangChunhua':
                当前张春华伤害 = 张春华_单次伤害系数 * (1 + 张春华心计层数 * 张春华_每层心计增伤)
                总伤害 += 当前张春华伤害
                if random.random() < 张春华_心计获得概率 and 张春华心计层数 < 10:
                    张春华心计层数 += 1

            if attack_type != '张春华哑火普攻':
                本次攻击造成了谋略伤害 = False
                神锋当前发动率 = 神锋_基础发动率 + 神锋_自带发动率加成
                if 5 in 已获得整备: 神锋当前发动率 += 0.10
                if random.random() < 神锋当前发动率:
                    本次攻击造成了谋略伤害 = True
                    追击增伤 = 女儿状态['追击伤害加成']
                    if support_配置 and support_配置['name'] == 'MaTeng' and r <= 3: 追击增伤 += 马腾_追击增伤
                    if 4 in 已获得整备: 追击增伤 += 0.20
                    伤害 = (神锋_伤害系数 * 2) * (1 + 追击增伤) * (1 + 本回合甄姬增伤)
                    奇谋伤害加成 = 女儿状态['奇谋伤害加成']
                    if 7 in 已获得整备: 奇谋伤害加成 += 0.20
                    if 本回合甄姬必定奇谋可用:
                        伤害 *= (1 + 奇谋伤害加成); 本回合甄姬必定奇谋可用 = False
                    elif random.random() < 女儿状态['奇谋率']:
                        伤害 *= (1 + 奇谋伤害加成)
                    总伤害 += 伤害
                    if 整备状态池:
                        新整备 = 整备状态池.pop(0); 已获得整备.add(新整备)
                        if 新整备 == 2: 女儿状态['奇谋率'] += 0.20
                if build_配置['skill2'] == 'MouErHouDong' and random.random() < 谋而后动_基础发动率:
                    本次攻击造成了谋略伤害 = True
                    for _ in range(1 + (1 if random.random() < 谋而后动_额外发动率 else 0)):
                        谋系数 = 谋而后动_基础伤害系数 + (r - 1) * 谋而后动_每回合伤害提升
                        追击增伤 = 女儿状态['追击伤害加成']
                        if support_配置 and support_配置['name'] == 'MaTeng' and r <= 3: 追击增伤 += 马腾_追击增伤
                        if 4 in 已获得整备: 追击增伤 += 0.20
                        伤害 = (谋系数 * 3) * (1 + 追击增伤) * (1 + 本回合甄姬增伤)
                        奇谋伤害加成 = 女儿状态['奇谋伤害加成']
                        if 7 in 已获得整备: 奇谋伤害加成 += 0.20
                        if 本回合甄姬必定奇谋可用:
                            伤害 *= (1 + 奇谋伤害加成); 本回合甄姬必定奇谋可用 = False
                        elif random.random() < 女儿状态['奇谋率']:
                            伤害 *= (1 + 奇谋伤害加成)
                        总伤害 += 伤害
                if build_配置['skill2'] == 'Tieqi' and random.random() < 铁骑_基础发动率:
                    本次攻击造成了谋略伤害 = True
                    铁骑系数 = 铁骑_基础伤害系数 - (r - 1) * 铁骑_每回合伤害衰减
                    追击增伤 = 女儿状态['追击伤害加成']
                    if support_配置 and support_配置['name'] == 'MaTeng' and r <= 3: 追击增伤 += 马腾_追击增伤
                    if 4 in 已获得整备: 追击增伤 += 0.20
                    伤害 = 铁骑系数 * (1 + 追击增伤) * (1 + 本回合甄姬增伤)
                    奇谋伤害加成 = 女儿状态['奇谋伤害加成']
                    if 7 in 已获得整备: 奇谋伤害加成 += 0.20
                    当前奇谋率 = 女儿状态['奇谋率'] + 铁骑_发动后奇谋提升
                    if 本回合甄姬必定奇谋可用:
                        伤害 *= (1 + 奇谋伤害加成); 本回合甄姬必定奇谋可用 = False
                    elif random.random() < 当前奇谋率:
                        伤害 *= (1 + 奇谋伤害加成)
                    总伤害 += 伤害
                if build_配置['skill2'] == 'ZhiPoQianJun' and random.random() < 智破千军_发动率:
                    本次攻击造成了谋略伤害 = True
                    for _ in range(2):
                        单次伤害 = 智破千军_伤害系数
                        if random.random() < 智破千军_增伤概率:
                            单次伤害 *= (1 + 智破千军_增伤幅度)
                        追击增伤 = 女儿状态['追击伤害加成']
                        if support_配置 and support_配置['name'] == 'MaTeng' and r <= 3: 追击增伤 += 马腾_追击增伤
                        if 4 in 已获得整备: 追击增伤 += 0.20
                        伤害 = 单次伤害 * (1 + 追击增伤) * (1 + 本回合甄姬增伤)
                        奇谋伤害加成 = 女儿状态['奇谋伤害加成']
                        if 7 in 已获得整备: 奇谋伤害加成 += 0.20
                        if 本回合甄姬必定奇谋可用:
                            伤害 *= (1 + 奇谋伤害加成); 本回合甄姬必定奇谋可用 = False
                        elif random.random() < 女儿状态['奇谋率']:
                            伤害 *= (1 + 奇谋伤害加成)
                        总伤害 += 伤害
                if 本次攻击造成了谋略伤害 and not 本回合运智额外普攻已触发:
                    if random.random() < 运智_额外普攻发动率:
                        本回合运智额外普攻已触发 = True
                        普攻列表.append("运智普攻")
        i = 0
        while i < len(普攻列表):
            process_attack(普攻列表[i]); i += 1
        普攻列表_追加阶段 = []
        if support_配置:
            if support_配置['name'] == 'MaTeng' and r <= 3 and random.random() < 马腾_额外普攻发动率:
                普攻列表_追加阶段.append("马腾普攻")
            if support_配置['name'] == 'ZhangChunhua':
                if 张春华心计层数 < 6:
                    普攻列表_追加阶段.append("张春华哑火普攻")
                else:
                    普攻列表_追加阶段.append("张春华正常普攻")
        for attack_type in 普攻列表_追加阶段:
            process_attack(attack_type)
    最终伤害 = 总伤害 * (1 + 女儿状态['运智铺谋层数'] * 运智_每层谋略增伤)
    最终伤害 *= 女儿状态['总伤害乘数']
    return 最终伤害

# ==============================================================================
# 主程序入口
# ==============================================================================
if __name__ == '__main__':
    plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False

    # 1.【修改】修改图例说明文字
    build1_配置 = {'name': '运智铺谋 + 谋而后动', 'skill2': 'MouErHouDong'}
    build2_配置 = {'name': '运智铺谋 + 铁骑横冲', 'skill2': 'Tieqi'}
    build3_配置 = {'name': '运智铺谋 + 智破千军', 'skill2': 'ZhiPoQianJun'}

    辅助列表 = [
        {'name': '女儿单人', 'config': None},
        {'name': '辅助-马腾', 'config': {'name': 'MaTeng'}},
        {'name': '辅助-张春华', 'config': {'name': 'ZhangChunhua'}},
        {'name': '辅助-甄姬', 'config': {'name': 'ZhenJi'}},
        {'name': '辅助-庞统', 'config': {'name': 'PangTong'}},
        {'name': '辅助-荀彧', 'config': {'name': 'XunYu'}}
    ]

    结果列表 = []
    print(f"正在运行 {模拟次数} 次模拟...")

    for 辅助 in 辅助列表:
        b1_伤害 = sum([run_single_simulation(build1_配置, 辅助['config']) for _ in range(模拟次数)]) / 模拟次数
        b2_伤害 = sum([run_single_simulation(build2_配置, 辅助['config']) for _ in range(模拟次数)]) / 模拟次数
        b3_伤害 = sum([run_single_simulation(build3_配置, 辅助['config']) for _ in range(模拟次数)]) / 模拟次数
        结果列表.append({
            '组合': 辅助['name'],
            build1_配置['name']: b1_伤害,
            build2_配置['name']: b2_伤害,
            build3_配置['name']: b3_伤害,
        })
    print("\n模拟完成。")

    结果DF = pd.DataFrame(结果列表)
    # 3.【修改】按Build 1的伤害对结果进行降序排列
    结果DF = 结果DF.sort_values(by=build1_配置['name'], ascending=False).reset_index(drop=True)
    
    print("\n--- 3回合期望总伤害系数对比 ---")
    print(结果DF.round(2).to_string(index=False))
    
    绘图DF = 结果DF.set_index('组合')
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    bar_width, num_builds = 0.25, len(绘图DF.columns)
    index = np.arange(len(绘图DF.index))
    
    colors = ['cornflowerblue', 'salmon', 'lightgreen']
    bars = []
    for i, col in enumerate(绘图DF.columns):
        offset = bar_width * (i - (num_builds - 1) / 2)
        bar = ax.bar(index + offset, 绘图DF[col], bar_width, label=col, color=colors[i], edgecolor='black')
        bars.append(bar)

    # 2.【修改】调整字体大小和加粗
    ax.set_xlabel('辅助武将组合', fontsize=26, fontweight='bold')
    ax.set_ylabel('3回合期望总伤害系数', fontsize=26, fontweight='bold')
    ax.set_title('女儿不同Build及辅助下的期望伤害对比', fontsize=30, fontweight='bold')
    ax.set_xticks(index)
    ax.set_xticklabels(绘图DF.index, rotation=0, fontsize=24, fontweight='bold')
    ax.tick_params(axis='y', labelsize=22)
    ax.legend(prop={'weight': 'bold', 'size': 20}) # 调整图例字体
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    for bar_group in bars:
        ax.bar_label(bar_group, fmt='%.1f', padding=3, fontsize=12, fontweight='bold')
        
    fig.tight_layout()
    plt.show()
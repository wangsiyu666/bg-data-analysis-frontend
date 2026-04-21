#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户行为数据生成脚本（分批写入版）
严格遵循 user_behavior 表的所有字段顺序和类型
每批生成 BATCH_SIZE 行，写入 CSV，避免内存溢出
"""

import csv
import random
from datetime import datetime, timedelta
import os
from faker import Faker

# 初始化
fake = Faker('zh_CN')
random.seed(42)

# 配置
BATCH_SIZE = 10000          # 每批写入行数
TOTAL_ROWS = 500000         # 总行数
OUTPUT_FILE = '/workspaces/telecompass/backend/training_data/user_behavior.csv'

def random_date(start, end):
    """生成随机日期"""
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_one_row():
    """生成单行数据，返回与表字段顺序一致的列表"""
    # 1. 基础信息
    month = '2026-04'
    user_id = random.randint(100000000, 999999999)
    city_id = random.choices(['110100', '310100', '440100', '440300', '320100', '330100', '510100', '420100'],
                             weights=[0.15,0.12,0.10,0.09,0.08,0.07,0.06,0.05])[0] if random.random()<0.7 else random.choice(['110200','120100','130100','140100','150100','210100','220100','230100','340100','350100','360100','370100','410100','430100','450100','460100','500100','520100','530100','540100','610100','620100','630100','640100','650100'])
    age = random.choices([18,25,45,61], weights=[0.15,0.45,0.25,0.15])[0] + random.randint(0,6)  # 简化年龄分布
    sex_id = str(random.choice([1,2]))
    prv1_userstatus_id = random.choices(['1','2','3'], weights=[0.85,0.07,0.08])[0]
    star_level = random.choices(['1','2','3','4','5'], weights=[0.10,0.20,0.30,0.25,0.15])[0]
    star_level_b = random.choice([0,1])
    is_jxhm = 1 if random.random()<0.05 else 0
    brand_id = random.choices([1,2,3], weights=[0.35,0.30,0.35])[0]
    user_online = random.randint(1,240)
    arpu120_user = 1 if random.random()<0.2 else 0
    bd_arpu120_user = random.choice([0,1])
    credit_id = random.choices(['1','2','3','4','5'], weights=[0.10,0.20,0.40,0.20,0.10])[0]
    credit_id_b = random.choice([0,1])
    paytype21_user = 1 if random.random()<0.3 else 0
    is_acct_counts = 1 if random.random()<0.2 else 0
    is_rhtc = 1 if random.random()<0.4 else 0
    qx_rhtc_3month = 1 if random.random()<0.05 else 0
    xz_rhtc_3month = 1 if random.random()<0.08 else 0
    is_jttf = 1 if random.random()<0.15 else 0
    qx_jttf_3month = 1 if random.random()<0.03 else 0
    regiontype_id3 = 1 if random.random()<0.3 else 0
    student_flag = 1 if (18<=age<=24 and random.random()<0.6) else 0
    month_new_mark = 1 if random.random()<0.03 else 0
    month_new_mark_6month = 1 if random.random()<0.15 else 0
    zero_mark = 1 if random.random()<0.05 else 0
    arpu_fluctuate_mark = 1 if random.random()<0.2 else 0
    arpu_stabilize_mark = 1 if random.random()<0.6 else 0
    active_mark = 0 if zero_mark else 1
    dou_mark = 0 if zero_mark else 1
    is_ll_dh = 1 if random.random()<0.1 else 0
    is_yy_dh = 1 if random.random()<0.08 else 0
    is_dh_2month = 1 if random.random()<0.06 else 0
    is_dh_3month = 1 if random.random()<0.04 else 0
    vip_mark = 1 if random.random()<0.1 else 0
    ys_yd_yh = 1 if random.random()<0.05 else 0
    mon_consume_id = random.choices(['低','中','高'], weights=[0.3,0.5,0.2])[0]
    call_mark = 1 if random.random()<0.85 else 0
    school_flag = student_flag
    family_main = 1 if random.random()<0.12 else 0
    is_family = 1 if random.random()<0.25 else 0
    qx_family_3month = 1 if random.random()<0.04 else 0

    # 欠费相关
    owe_fee = 0.0 if random.random()<0.85 else round(random.uniform(10,500),2)
    owe_fee_pre1 = round(owe_fee * random.uniform(0.8,1.2),2)
    owe_fee_pre2 = round(owe_fee * random.uniform(0.8,1.2),2)
    zs_fee = round(random.uniform(0,50),2)
    zs_fee_v = round(random.uniform(0,0.5),4)
    zs_fee_time = (datetime.now() + timedelta(days=random.randint(30,365))).date()

    # 缴费
    arpu = round(random.gauss(47,15),2)
    arpu = max(10, min(300, arpu))
    pay_fee = round(arpu * random.uniform(0.9,1.2),2)
    pay_fee_pre1 = round(pay_fee * random.uniform(0.9,1.1),2)
    pay_fee_pre2 = round(pay_fee * random.uniform(0.9,1.1),2)
    pay_fee_v = round(random.uniform(-0.3,0.3),4)
    pay_counts = random.randint(1,5)
    pay_counts_pre1 = max(1, pay_counts + random.randint(-1,1))
    pay_counts_pre2 = max(1, pay_counts + random.randint(-1,1))
    pay_counts_v = round(random.uniform(-0.5,0.5),4)
    pay_counts_3month = pay_counts + pay_counts_pre1 + pay_counts_pre2
    pay_fee_3month = round(pay_fee + pay_fee_pre1 + pay_fee_pre2,2)

    # 账户余额
    pve_amount = round(random.uniform(0,200),2)
    pve1_amount = round(pve_amount * random.uniform(0.9,1.1),2)
    pve2_amount = round(pve_amount * random.uniform(0.9,1.1),2)
    prepay_bal = round(pve_amount * random.uniform(0.95,1.05),2)
    prepay_bal_v = round(random.uniform(-0.2,0.2),4)
    amount_bd = round(random.uniform(0,50),4)
    credit = round(random.uniform(0,100),2)
    credit_pve1 = round(credit * random.uniform(0.9,1.1),2)
    credit_pve2 = round(credit * random.uniform(0.9,1.1),2)

    # ARPU 历史
    arpu_pve1 = round(arpu * random.uniform(0.9,1.1),2)
    arpu_pve2 = round(arpu * random.uniform(0.9,1.1),2)
    avg_3mon_fee = round((arpu + arpu_pve1 + arpu_pve2)/3,2)
    arpu_bd = round(random.uniform(0,20),4)
    arpu_pve1_v = round(random.uniform(-0.3,0.3),4)
    avg_gprsplan_fee_3m = round(random.uniform(20,80),2)
    newbusi_fee = round(random.uniform(0,30),2)
    newbusi_fee1 = round(newbusi_fee * random.uniform(0.8,1.2),2)
    newbusi_fee_v = round(random.uniform(-0.5,0.5),4)

    # 月租
    lam_yzf_fee = round(random.uniform(30,150),2)
    lam_yzf_fee_v = round(random.uniform(-0.2,0.2),4)
    lam_yzf_fee_pre1 = round(lam_yzf_fee * random.uniform(0.9,1.1),2)
    lam_yzf_fee_pre2 = round(lam_yzf_fee * random.uniform(0.9,1.1),2)
    call_fee = round(arpu * 0.3 * random.uniform(0.8,1.2),2)
    call_fee_v = round(random.uniform(-0.3,0.3),4)
    gprs_fee = round(arpu * 0.5 * random.uniform(0.8,1.2),2)
    gprs_fee_v = round(random.uniform(-0.3,0.3),4)
    tax_on_yuezu = round(random.uniform(30,150),2)
    pre_tax_on_yuezu = round(tax_on_yuezu * random.uniform(0.9,1.1),2)
    pre1_tax_on_yuezu = round(tax_on_yuezu * random.uniform(0.9,1.1),2)
    zhekou = round(random.uniform(0,30),2)
    pre_zhekou = round(zhekou * random.uniform(0.8,1.2),2)
    pre1_zhekou = round(zhekou * random.uniform(0.8,1.2),2)
    zhekou_v = round(random.uniform(0,0.3),4)
    is_tc_free = 1 if random.random()<0.15 else 0
    jm_tc_sy_times = random.randint(0,12)
    tc_sy_times = random.randint(1,24)
    lam_mythf_fee = round(random.uniform(0,50),2)
    lam_mythf_fee_pre1 = round(lam_mythf_fee * random.uniform(0.8,1.2),2)
    lam_mythf_fee_pre2 = round(lam_mythf_fee * random.uniform(0.8,1.2),2)
    lam_mythf_fee_v = round(random.uniform(-0.5,0.5),4)

    # 套餐
    plan_id_bd = random.choice([0,1])
    plan_fee = round(random.uniform(30,200),2)
    plan_fee_pre1 = round(plan_fee * random.uniform(0.9,1.1),2)
    plan_fee_pre2 = round(plan_fee * random.uniform(0.9,1.1),2)
    tc_use_times = random.randint(1,36)
    plan_fee_bd = random.choice([0,1])
    plan_six_num = random.randint(0,3)
    is_jd = 1 if random.random()<0.1 else 0
    is_jd_3month = 1 if random.random()<0.15 else 0
    is_5gtb = 1 if random.random()<0.2 else 0
    plan_5g_mark = 1 if random.random()<0.6 else 0
    arpu_momr = round(random.uniform(-0.2,0.2),4)
    pve_arpu_momr = round(random.uniform(-0.2,0.2),4)
    gprsplan_fee = round(random.uniform(20,100),2)
    lam_yzf_fee_pve1 = round(lam_yzf_fee * random.uniform(0.9,1.1),2)
    lam_yzf_fee_pve2 = round(lam_yzf_fee * random.uniform(0.9,1.1),2)

    # 流量
    last_gprs_billing_flows = int(random.uniform(1,50) * 1024**3)
    before_last_gprs_billing_flows = int(last_gprs_billing_flows * random.uniform(0.8,1.2))
    over_flow_3month = int(random.uniform(0,10) * 1024**3)
    is_lower_arpu = 1 if arpu < 28 else 0
    is_bxl_xs3 = 1 if random.random()<0.08 else 0
    is_gprs_ct_fee_3month_h = 1 if random.random()<0.12 else 0
    is_yuyin_ct_fee_3month_h = 1 if random.random()<0.1 else 0
    is_arpu_high = 1 if random.random()<0.15 else 0
    is_lower_arpu3 = 1 if random.random()<0.07 else 0
    dual_card_user_mark = 1 if random.random()<0.2 else 0

    # 流量包
    is_llb = 1 if random.random()<0.3 else 0
    prv1_llb = 1 if random.random()<0.28 else 0
    prv2_llb = 1 if random.random()<0.26 else 0
    llb_cnt = random.randint(0,3)
    is_dxb = 1 if random.random()<0.2 else 0
    llb_should_fee = round(random.uniform(0,50),2)

    # 异网/本网双卡
    is_ywzk = 1 if random.random()<0.1 else 0
    new_ywsk = 1 if random.random()<0.05 else 0
    prv1_new_ywsk = 1 if random.random()<0.04 else 0
    bwsk_new = 1 if random.random()<0.06 else 0
    prv1_new_bwsk = 1 if random.random()<0.05 else 0
    is_ywsk = 1 if random.random()<0.15 else 0
    is_bwsk = 1 if random.random()<0.18 else 0

    # 终端
    is_zdhy = 1 if random.random()<0.25 else 0
    imei_online = random.randint(1,48)
    his_imei_track = random.randint(12,36)
    imei_start = (datetime.now() - timedelta(days=random.randint(30,730))).date()
    pre_term_price = round(random.uniform(500,8000),2)
    source_imei_long = random.randint(1,60)
    track_id = str(random.randint(1,5))

    # 通话时长、次数等（简化部分）
    out_call_duration_m = int(random.uniform(30,300)*60)
    out_call_duration_m1 = int(out_call_duration_m * random.uniform(0.8,1.2))
    out_call_duration_m2 = int(out_call_duration_m * random.uniform(0.8,1.2))
    out_call_duration_m3 = int(out_call_duration_m * random.uniform(0.8,1.2))
    avg_call_duration_m_prv_3m = int((out_call_duration_m1+out_call_duration_m2+out_call_duration_m3)/3)
    avg_out_call_duration_m_3m = int(out_call_duration_m * random.uniform(0.9,1.1))
    avg_in_call_dura_3m = int(out_call_duration_m * random.uniform(0.8,1.2))
    call_dura_v = round(random.uniform(-0.3,0.3),4)
    call_counts = random.randint(10,200)
    avg_callcount_3m = int(call_counts * random.uniform(0.9,1.1))
    call_counts_bd = round(random.uniform(0,50),4)
    call_counts_prv1 = max(5, call_counts+random.randint(-20,20))
    call_counts_prv2 = max(5, call_counts+random.randint(-20,20))
    call_counts_prv3 = max(5, call_counts+random.randint(-20,20))
    call_duration_m = int(random.uniform(60,600)*60)
    avg_callduration_3m = int(call_duration_m * random.uniform(0.9,1.1))
    call_duration_m_bd = round(random.uniform(0,100),4)
    call_duration_m_prv1 = int(call_duration_m * random.uniform(0.8,1.2))
    call_duration_m_prv2 = int(call_duration_m * random.uniform(0.8,1.2))
    call_duration_m_prv3 = int(call_duration_m * random.uniform(0.8,1.2))
    call_duration_m_prv_v = round(random.uniform(-0.3,0.3),4)
    out_call_duration = int(call_duration_m * random.uniform(0.4,0.6))
    out_call_dura_prv1 = int(out_call_duration * random.uniform(0.8,1.2))
    out_call_dura_prv2 = int(out_call_duration * random.uniform(0.8,1.2))
    out_call_counts = random.randint(5,150)
    out_call_counts1 = max(3, out_call_counts+random.randint(-15,15))
    out_call_counts2 = max(3, out_call_counts+random.randint(-15,15))
    out_call_counts_v = round(random.uniform(-0.3,0.3),4)
    in_call_duration_m = int(call_duration_m * random.uniform(0.4,0.6))
    in_call_duration_m_pre1 = int(in_call_duration_m * random.uniform(0.8,1.2))
    in_call_duration_m_v = round(random.uniform(-0.3,0.3),4)
    in_call_counts = random.randint(5,150)
    in_call_counts1 = max(3, in_call_counts+random.randint(-15,15))
    in_call_counts2 = max(3, in_call_counts+random.randint(-15,15))
    in_call_counts_v = round(random.uniform(-0.3,0.3),4)
    out_in_call_d_v = round(random.uniform(0.3,0.7),4)
    inner_call_v = round(random.uniform(0.4,0.9),4)
    out_in_call_count_v = round(random.uniform(0.3,0.7),4)

    # 呼叫转移等
    callfw_counts = random.randint(0,10)
    callfw_counts_v = round(random.uniform(-0.5,0.5),4)
    callfw_counts1 = random.randint(0,5)
    call_opp_counts1 = random.randint(5,100)
    call_opp_counts_v = round(random.uniform(-0.3,0.3),4)
    avg_call_counts_3m = int(call_counts * random.uniform(0.9,1.1))
    avg_out_call_counts_prv_3m = int(out_call_counts * random.uniform(0.9,1.1))
    avg_in_call_counts_3m = int(in_call_counts * random.uniform(0.9,1.1))
    out_call_counts_3bd = round(random.uniform(0,30),4)
    in_call_counts_3bd = round(random.uniform(0,30),4)
    call_opp_out_counts = random.randint(3,80)
    prv1_call_opp_out_counts = max(2, call_opp_out_counts+random.randint(-10,10))
    prv2_call_opp_out_counts = max(2, call_opp_out_counts+random.randint(-10,10))
    call_opp_in_counts = random.randint(3,80)
    prv1_call_opp_in_counts = max(2, call_opp_in_counts+random.randint(-10,10))
    prv2_call_opp_in_counts = max(2, call_opp_in_counts+random.randint(-10,10))
    p1_yw_call_opp_counts_momr = round(random.uniform(-0.3,0.3),4)
    p2_yw_call_opp_counts_momr = round(random.uniform(-0.3,0.3),4)

    # 流量饱和度、用量
    all_bhd = round(random.uniform(0.3,1.2),4)
    dou = int(random.uniform(1,50)*1024**3)
    dou_bd = round(random.uniform(0,0.5),4)
    dou_hb_rate = round(random.uniform(-0.5,0.5),4)
    zero_call_days = random.randint(0,30)
    tc_userd = int(dou * random.uniform(0.6,0.9))
    tc_bhd = round(random.uniform(0.5,1.1),4)
    llb_userd = int(dou * random.uniform(0.1,0.3))
    llb_bhd = round(random.uniform(0.3,1.0),4)
    bill_gprs_userd = int(dou * random.uniform(0,0.2))
    bill_bhd = round(random.uniform(0,0.8),4)
    dx_userd = int(dou * random.uniform(0.1,0.4))
    dx_bhd = round(random.uniform(0.2,0.9),4)
    jiezhuan_userd = int(dou * random.uniform(0,0.2))
    jiezhuan_bhd = round(random.uniform(0,0.8),4)
    is_llyz = 1 if random.random()<0.08 else 0
    liul_unlimit = 1 if random.random()<0.25 else 0
    pve1_dou = int(dou * random.uniform(0.8,1.2))
    pve2_dou = int(dou * random.uniform(0.8,1.2))
    dou_hb = round(random.uniform(-0.4,0.4),4)
    pre1_liul_unlimit = 1 if random.random()<0.23 else 0
    pre2_liul_unlimit = 1 if random.random()<0.21 else 0
    gprs_5g_flow_m = round((dou/1024**3) * random.uniform(0.3,0.7),2)
    all_gprs_lte_flows = round((dou/1024**3) * random.uniform(0.3,0.7),2)
    sn_gprs_flows = round((dou/1024**3) * random.uniform(0.6,0.9),2)
    sw_gprs_flows = round((dou/1024**3) * random.uniform(0.1,0.4),2)
    gprs_left_res = int(random.uniform(0,20)*1024**2)
    jz_gprs_res = int(random.uniform(0,10)*1024**2)
    jz_gprs_res_pve1 = int(jz_gprs_res * random.uniform(0.8,1.2))
    jz_gprs_res_pve2 = int(jz_gprs_res * random.uniform(0.8,1.2))
    is_ct_3month = 1 if random.random()<0.12 else 0
    call_duration_fee_3momth = round(random.uniform(0,50),2)
    llb_should_fee_temp = round(random.uniform(0,50),2)
    gprs_ct = int(random.uniform(0,10)*1024**3)
    prv1_gprs_ct = int(gprs_ct * random.uniform(0.8,1.2))
    prv2_gprs_ct = int(gprs_ct * random.uniform(0.8,1.2))
    gprs_ct_hb = round(random.uniform(-0.5,0.5),4)
    is_gprs_ct_3month = 1 if random.random()<0.15 else 0
    llb_5g_mark = 1 if random.random()<0.18 else 0
    c_yz_fee = round(random.uniform(0,100),2)
    c_yz_fee_v = round(random.uniform(-0.5,0.5),4)
    gprs_flow_fee = round(random.uniform(0,60),2)
    gprs_flow_fee_v = round(random.uniform(-0.5,0.5),4)
    yuyin_fee_3month = round(random.uniform(10,100),2)
    yuyin_ct_fee_3month = round(random.uniform(0,30),2)
    gprs_fee_3month = round(random.uniform(20,150),2)
    gprs_ct_fee_3month = round(random.uniform(0,50),2)

    # 漫游
    toll_call_opp_counts = random.randint(0,30)
    roam_duration_m1 = int(random.uniform(0,60)*60)
    roam_duration_m2 = int(roam_duration_m1 * random.uniform(0.8,1.2))
    roam_duration_m3 = int(roam_duration_m1 * random.uniform(0.8,1.2))
    roam_counts_v = round(random.uniform(0,0.3),4)
    sw_call_duration_m = int(random.uniform(0,120)*60)
    sw_call_duration_m_v = round(random.uniform(-0.4,0.4),4)
    long_out_dou = 1 if random.random()<0.08 else 0
    out_sw_days = random.randint(0,30)
    out_sw_gprs = int(random.uniform(0,20)*1024**3)
    prv1_out_sw_days = max(0, out_sw_days+random.randint(-5,5))
    prv1_out_sw_gprs = int(out_sw_gprs * random.uniform(0.8,1.2))
    prv2_out_sw_days = max(0, out_sw_days+random.randint(-5,5))
    prv2_out_sw_gprs = int(out_sw_gprs * random.uniform(0.8,1.2))
    out_sw_hb = round(random.uniform(-0.5,0.5),4)
    roam_counts = random.randint(0,20)

    # VPMN
    inent_call_counts = random.randint(0,100)
    inent_call_counts_v = round(random.uniform(-0.3,0.3),4)
    inent_call_duration_m = int(random.uniform(0,300)*60)
    inent_call_duration_m_v = round(random.uniform(-0.3,0.3),4)

    # 集团、宽带、家庭相关（简化）
    is_jt = 1 if random.random()<0.18 else 0
    is_jt_vpn = 1 if random.random()<0.12 else 0
    is_jt_key_cust = 1 if random.random()<0.08 else 0
    jtyd_3month = 1 if random.random()<0.04 else 0
    innet_jt_time = (datetime.now() - timedelta(days=random.randint(30,1095))).date()
    kd_3month = 1 if random.random()<0.35 else 0
    kd_cj_month = 1 if random.random()<0.03 else 0
    kd_cj_3month = 1 if random.random()<0.08 else 0
    kd_expire_date = (datetime.now() + timedelta(days=random.randint(30,730))).date()
    kd_user_mark = 1 if random.random()<0.3 else 0
    ywkd_user_mark = 1 if random.random()<0.05 else 0
    if_local_kdcover = 1 if random.random()<0.7 else 0
    if_no_kdcover_bl = 1 if random.random()<0.1 else 0
    if_kd_poor = 1 if random.random()<0.06 else 0
    kd_bl_times = random.randint(1,60)
    prod_bandwidth = random.choice(['100M','200M','300M','500M','1000M'])
    mtd_flow = int(random.uniform(50,500)*1024**3)
    mtd_flow_pre1 = int(mtd_flow * random.uniform(0.8,1.2))
    mtd_flow_pre2 = int(mtd_flow * random.uniform(0.8,1.2))
    mtd_flow_bd = round(random.uniform(0,100),4)
    is_fuse = 1 if random.random()<0.28 else 0
    kb_eff_times = random.randint(1,24)
    kb_exp_times = random.randint(0,24)
    assure_fee = round(random.uniform(0,200),2)
    is_0_flow = 1 if random.random()<0.04 else 0
    is_renew = 1 if random.random()<0.2 else 0
    is_mbh = 1 if random.random()<0.15 else 0
    is_group = 1 if random.random()<0.1 else 0
    mtd_active_day = random.randint(15,30)
    mtd_active_day_pre1 = max(10, mtd_active_day+random.randint(-5,5))
    mtd_active_day_pre2 = max(10, mtd_active_day+random.randint(-5,5))
    mtd_active_day_hb = round(random.uniform(-0.3,0.3),4)
    mtd_active_day_bd = round(random.uniform(0,10),4)
    mtd_time_length = int(random.uniform(100,500)*3600)
    mtd_time_length_pre1 = int(mtd_time_length * random.uniform(0.8,1.2))
    mtd_time_length_pre2 = int(mtd_time_length * random.uniform(0.8,1.2))
    mtd_time_length_hb = round(random.uniform(-0.3,0.3),4)
    mtd_time_length_bd = round(random.uniform(0,100),4)
    kd_fee = round(random.uniform(50,200),2)
    zdxf_fee = round(random.uniform(30,150),2)
    kb_promoeff_times = random.randint(1,24)
    kb_promoexp_times = random.randint(0,24)
    is_jsb = 1 if random.random()<0.08 else 0
    is_box = 1 if random.random()<0.12 else 0
    is_voicect = 1 if random.random()<0.06 else 0

    # 家庭相关标识
    is_jt_yigr = 1 if random.random()<0.07 else 0
    is_jt_xc = 1 if random.random()<0.03 else 0
    is_jt_xccx = 1 if random.random()<0.02 else 0
    is_jt_xccg = 1 if random.random()<0.015 else 0
    is_jt_kdcj = 1 if random.random()<0.04 else 0
    is_jt_kdywxz = 1 if random.random()<0.03 else 0

    # 合约、低消
    pro_kind_contract = 1 if random.random()<0.22 else 0
    pro_mbcharge_contract = 1 if random.random()<0.18 else 0
    pro_res_hold_month = random.randint(6,36)
    is_heyue = 1 if random.random()<0.3 else 0
    hy_dq_3month = 1 if random.random()<0.06 else 0
    hy_sy_times = random.randint(0,36)
    pro_term_contract = 1 if random.random()<0.25 else 0
    is_heyuedaoqi = 1 if random.random()<0.1 else 0
    is_dx = 1 if random.random()<0.15 else 0
    dx_lj_times = random.randint(1,24)
    dx_sy_times = random.randint(0,24)
    bhd_month = round(random.uniform(0.5,1.5),4)
    join_hd_month = 1 if random.random()<0.35 else 0
    join_new_offer_month = 1 if random.random()<0.2 else 0
    dg_ll_offer_month = 1 if random.random()<0.18 else 0
    join_new_offer_3month = 1 if random.random()<0.4 else 0
    dg_ll_offer_3month = 1 if random.random()<0.35 else 0
    hy_never_users = 1 if random.random()<0.4 else 0
    hy_repeat_users = 1 if random.random()<0.25 else 0

    # 退订捆绑、合约到期等
    tuiding_bangbang_cnt_month = random.randint(0,3)
    tuiding_bangbang_cnt_3month = random.randint(0,5)
    bangbang_yucun_expire = random.randint(0,24)
    bangbang_zengji_expire = random.randint(0,24)
    heyue_3month_expire = 1 if random.random()<0.08 else 0
    no_contract_3month = 1 if random.random()<0.3 else 0
    has_contract_3month = 1 if random.random()<0.45 else 0
    port_restrict = 1 if random.random()<0.05 else 0
    churn_restrict = 1 if random.random()<0.06 else 0
    realname_user = 1 if random.random()<0.98 else 0
    vice_card_user = 1 if random.random()<0.15 else 0
    refund_user = 1 if random.random()<0.12 else 0
    refund_remain_months = random.randint(0,12)

    # 携转相关
    query_port_sms_6m = 1 if random.random()<0.04 else 0
    query_port_sms_cnt_6m = random.randint(0,5)
    apply_port_3m = 1 if random.random()<0.02 else 0
    cancel_broadband_3m = 1 if random.random()<0.05 else 0
    unbind_bank_alipay = 1 if random.random()<0.03 else 0
    wechat_alipay_use_down = 1 if random.random()<0.04 else 0
    address_change = 1 if random.random()<0.06 else 0
    new_broadband_other_this = 1 if random.random()<0.02 else 0
    new_broadband_other_3m = 1 if random.random()<0.05 else 0
    call_10086_port = 1 if random.random()<0.015 else 0
    sms_port_query_this = 1 if random.random()<0.01 else 0
    apply_port_this = 1 if random.random()<0.008 else 0
    sms_port_query_3m = 1 if random.random()<0.025 else 0
    apply_port_3m_again = 1 if random.random()<0.02 else 0
    web_search_port = 1 if random.random()<0.03 else 0

    # 投诉
    is_ts = 1 if random.random()<0.08 else 0
    ts_counts_m = random.randint(0,5)
    ts_counts_3month = random.randint(0,8)
    out_opposite_regular_count = random.randint(0,20)
    yw_call_nums = random.randint(0,50)
    yw_call_opp_counts = random.randint(0,40)
    yw_call_opp_counts_v = round(random.uniform(0,0.6),4)
    yw_in_call_counts = random.randint(0,30)
    yw_in_call_high = 1 if random.random()<0.09 else 0
    p1_yw_in_call_counts_momr = round(random.uniform(-0.3,0.3),4)
    p2_yw_in_call_counts_momr = round(random.uniform(-0.3,0.3),4)
    yw_in_call_duration = int(random.uniform(0,120)*60)
    p1_yw_in_call_duration_momr = round(random.uniform(-0.3,0.3),4)
    p2_yw_in_call_duration_momr = round(random.uniform(-0.3,0.3),4)
    p1_yw_call_nums_momr = round(random.uniform(-0.3,0.3),4)
    p2_yw_call_nums_momr = round(random.uniform(-0.3,0.3),4)
    callfw_kf_count = random.randint(0,10)
    prv1_callin_ywkf_cnts = max(0, callfw_kf_count+random.randint(-3,3))
    call_1001_counts = random.randint(0,8)
    p2_call10010_counts_momr = round(random.uniform(-0.4,0.4),4)
    p3_call10000_counts_momr = round(random.uniform(-0.4,0.4),4)
    is_ts_high = 1 if random.random()<0.03 else 0
    is_tsjj_low = 1 if random.random()<0.04 else 0
    call_1860_1861_counts = random.randint(0,10)
    call_1860_1861_counts_v = round(random.uniform(-0.4,0.4),4)
    call_1860_1861_duration_m = int(random.uniform(0,30)*60)
    call_1860_1861_duration_m_v = round(random.uniform(-0.4,0.4),4)

    # APP使用
    wx_cnt_month = random.randint(0,300)
    wx_days_month = random.randint(0,30)
    prv1_wx_cnt = max(0, wx_cnt_month+random.randint(-50,50))
    prv1_wx_days = max(0, wx_days_month+random.randint(-5,5))
    prv2_wx_cnt = max(0, wx_cnt_month+random.randint(-50,50))
    prv2_wx_days = max(0, wx_days_month+random.randint(-5,5))
    bank_num_month = random.randint(0,8)
    prv1_bank_num = max(0, bank_num_month+random.randint(-2,2))
    prv2_bank_num = max(0, bank_num_month+random.randint(-2,2))
    bank_cnt_month = random.randint(0,100)
    prv1_bank_cnt = max(0, bank_cnt_month+random.randint(-20,20))
    prv2_bank_cnt = max(0, bank_cnt_month+random.randint(-20,20))

    # 稳定性指标
    jiaz_wending_rate = round(random.uniform(0.1,0.5),4)
    gprs_wending_rate = round(random.uniform(0.1,0.6),4)
    is_zifee_mg = 1 if random.random()<0.05 else 0
    is_busi_td = 1 if random.random()<0.03 else 0
    ts_fee = 1 if random.random()<0.04 else 0

    # 网络质量
    wangluo_bumanyi = 1 if random.random()<0.07 else 0
    shangwang_man = 1 if random.random()<0.06 else 0
    xinhao_chai = 1 if random.random()<0.08 else 0
    tonghua_diaohua = 1 if random.random()<0.05 else 0
    shuangjiang = 1 if random.random()<0.04 else 0
    zhunliwang = 1 if random.random()<0.03 else 0
    zhangwu_yuxiaohu = 1 if random.random()<0.02 else 0
    yingye_yuxiaohu = 1 if random.random()<0.025 else 0

    # 语音和流量使用统计
    yuyin_use_users = random.randint(0,100)
    yuyin_baohuo = round(random.uniform(0.3,1.1),4)
    di_tonghua_ratio = round(random.uniform(0,0.4),4)
    liuliang_use_users = random.randint(0,100)
    tongyong_liuliang_baohuo = round(random.uniform(0.4,1.2),4)
    di_liuliang_ratio = round(random.uniform(0,0.35),4)
    changman_changman_koujing = random.choice(['常漫','长漫','非漫游'])
    qianfei_ting = 1 if random.random()<0.04 else 0
    shuangting = 1 if random.random()<0.02 else 0
    danting = 1 if random.random()<0.03 else 0
    phone_num = fake.phone_number()

    # 按表字段顺序组装列表（务必与建表语句的列顺序一致）
    row = [
        month, user_id, city_id, age, sex_id, prv1_userstatus_id, star_level, star_level_b,
        is_jxhm, brand_id, user_online, arpu120_user, bd_arpu120_user, credit_id, credit_id_b,
        paytype21_user, is_acct_counts, is_rhtc, qx_rhtc_3month, xz_rhtc_3month, is_jttf, qx_jttf_3month,
        regiontype_id3, student_flag, month_new_mark, month_new_mark_6month, zero_mark, arpu_fluctuate_mark,
        arpu_stabilize_mark, active_mark, dou_mark, is_ll_dh, is_yy_dh, is_dh_2month, is_dh_3month,
        vip_mark, ys_yd_yh, mon_consume_id, call_mark, school_flag, family_main, is_family, qx_family_3month,
        owe_fee, owe_fee_pre1, owe_fee_pre2, zs_fee, zs_fee_v, zs_fee_time, pay_fee, pay_fee_pre1,
        pay_fee_pre2, pay_fee_v, pay_counts, pay_counts_pre1, pay_counts_pre2, pay_counts_v, pay_counts_3month,
        pay_fee_3month, pve_amount, pve1_amount, pve2_amount, prepay_bal, prepay_bal_v, amount_bd, credit,
        credit_pve1, credit_pve2, arpu, arpu_pve1, arpu_pve2, avg_3mon_fee, arpu_bd, arpu_pve1_v,
        avg_gprsplan_fee_3m, newbusi_fee, newbusi_fee1, newbusi_fee_v, lam_yzf_fee, lam_yzf_fee_v,
        lam_yzf_fee_pre1, lam_yzf_fee_pre2, call_fee, call_fee_v, gprs_fee, gprs_fee_v, tax_on_yuezu,
        pre_tax_on_yuezu, pre1_tax_on_yuezu, zhekou, pre_zhekou, pre1_zhekou, zhekou_v, is_tc_free,
        jm_tc_sy_times, tc_sy_times, lam_mythf_fee, lam_mythf_fee_pre1, lam_mythf_fee_pre2, lam_mythf_fee_v,
        plan_id_bd, plan_fee, plan_fee_pre1, plan_fee_pre2, tc_use_times, plan_fee_bd, plan_six_num, is_jd,
        is_jd_3month, is_5gtb, plan_5g_mark, arpu_momr, pve_arpu_momr, gprsplan_fee, lam_yzf_fee_pve1,
        lam_yzf_fee_pve2, last_gprs_billing_flows, before_last_gprs_billing_flows, over_flow_3month, is_lower_arpu,
        is_bxl_xs3, is_gprs_ct_fee_3month_h, is_yuyin_ct_fee_3month_h, is_arpu_high, is_lower_arpu3,
        dual_card_user_mark, is_llb, prv1_llb, prv2_llb, llb_cnt, is_dxb, llb_should_fee, is_ywzk,
        new_ywsk, prv1_new_ywsk, bwsk_new, prv1_new_bwsk, is_ywsk, is_bwsk, is_zdhy, imei_online,
        his_imei_track, imei_start, pre_term_price, source_imei_long, track_id, out_call_duration_m,
        out_call_duration_m1, out_call_duration_m2, out_call_duration_m3, avg_call_duration_m_prv_3m,
        avg_out_call_duration_m_3m, avg_in_call_dura_3m, call_dura_v, call_counts, avg_callcount_3m,
        call_counts_bd, call_counts_prv1, call_counts_prv2, call_counts_prv3, call_duration_m, avg_callduration_3m,
        call_duration_m_bd, call_duration_m_prv1, call_duration_m_prv2, call_duration_m_prv3, call_duration_m_prv_v,
        out_call_duration, out_call_dura_prv1, out_call_dura_prv2, out_call_counts, out_call_counts1,
        out_call_counts2, out_call_counts_v, in_call_duration_m, in_call_duration_m_pre1, in_call_duration_m_v,
        in_call_counts, in_call_counts1, in_call_counts2, in_call_counts_v, out_in_call_d_v, inner_call_v,
        out_in_call_count_v, callfw_counts, callfw_counts_v, callfw_counts1, call_opp_counts1, call_opp_counts_v,
        avg_call_counts_3m, avg_out_call_counts_prv_3m, avg_in_call_counts_3m, out_call_counts_3bd, in_call_counts_3bd,
        call_opp_out_counts, prv1_call_opp_out_counts, prv2_call_opp_out_counts, call_opp_in_counts,
        prv1_call_opp_in_counts, prv2_call_opp_in_counts, p1_yw_call_opp_counts_momr, p2_yw_call_opp_counts_momr,
        all_bhd, dou, dou_bd, dou_hb_rate, zero_call_days, tc_userd, tc_bhd, llb_userd, llb_bhd,
        bill_gprs_userd, bill_bhd, dx_userd, dx_bhd, jiezhuan_userd, jiezhuan_bhd, is_llyz, liul_unlimit,
        pve1_dou, pve2_dou, dou_hb, pre1_liul_unlimit, pre2_liul_unlimit, gprs_5g_flow_m, all_gprs_lte_flows,
        sn_gprs_flows, sw_gprs_flows, gprs_left_res, jz_gprs_res, jz_gprs_res_pve1, jz_gprs_res_pve2,
        is_ct_3month, call_duration_fee_3momth, llb_should_fee_temp, gprs_ct, prv1_gprs_ct, prv2_gprs_ct,
        gprs_ct_hb, is_gprs_ct_3month, llb_5g_mark, c_yz_fee, c_yz_fee_v, gprs_flow_fee, gprs_flow_fee_v,
        yuyin_fee_3month, yuyin_ct_fee_3month, gprs_fee_3month, gprs_ct_fee_3month, toll_call_opp_counts,
        roam_duration_m1, roam_duration_m2, roam_duration_m3, roam_counts_v, sw_call_duration_m, sw_call_duration_m_v,
        long_out_dou, out_sw_days, out_sw_gprs, prv1_out_sw_days, prv1_out_sw_gprs, prv2_out_sw_days,
        prv2_out_sw_gprs, out_sw_hb, roam_counts, inent_call_counts, inent_call_counts_v, inent_call_duration_m,
        inent_call_duration_m_v, is_jt, is_jt_vpn, is_jt_key_cust, jtyd_3month, innet_jt_time, kd_3month,
        kd_cj_month, kd_cj_3month, kd_expire_date, kd_user_mark, ywkd_user_mark, if_local_kdcover,
        if_no_kdcover_bl, if_kd_poor, kd_bl_times, prod_bandwidth, mtd_flow, mtd_flow_pre1, mtd_flow_pre2,
        mtd_flow_bd, is_fuse, kb_eff_times, kb_exp_times, assure_fee, is_0_flow, is_renew, is_mbh, is_group,
        mtd_active_day, mtd_active_day_pre1, mtd_active_day_pre2, mtd_active_day_hb, mtd_active_day_bd,
        mtd_time_length, mtd_time_length_pre1, mtd_time_length_pre2, mtd_time_length_hb, mtd_time_length_bd, kd_fee,
        zdxf_fee, kb_promoeff_times, kb_promoexp_times, is_jsb, is_box, is_voicect, is_jt_yigr, is_jt_xc,
        is_jt_xccx, is_jt_xccg, is_jt_kdcj, is_jt_kdywxz, pro_kind_contract, pro_mbcharge_contract,
        pro_res_hold_month, is_heyue, hy_dq_3month, hy_sy_times, pro_term_contract, is_heyuedaoqi, is_dx,
        dx_lj_times, dx_sy_times, bhd_month, join_hd_month, join_new_offer_month, dg_ll_offer_month,
        join_new_offer_3month, dg_ll_offer_3month, hy_never_users, hy_repeat_users, tuiding_bangbang_cnt_month,
        tuiding_bangbang_cnt_3month, bangbang_yucun_expire, bangbang_zengji_expire, heyue_3month_expire, no_contract_3month,
        has_contract_3month, port_restrict, churn_restrict, realname_user, vice_card_user, refund_user, refund_remain_months,
        query_port_sms_6m, query_port_sms_cnt_6m, apply_port_3m, cancel_broadband_3m, unbind_bank_alipay,
        wechat_alipay_use_down, address_change, new_broadband_other_this, new_broadband_other_3m, call_10086_port,
        sms_port_query_this, apply_port_this, sms_port_query_3m, apply_port_3m_again, web_search_port,
        is_ts, ts_counts_m, ts_counts_3month, out_opposite_regular_count, yw_call_nums, yw_call_opp_counts,
        yw_call_opp_counts_v, yw_in_call_counts, yw_in_call_high, p1_yw_in_call_counts_momr, p2_yw_in_call_counts_momr,
        yw_in_call_duration, p1_yw_in_call_duration_momr, p2_yw_in_call_duration_momr, p1_yw_call_nums_momr,
        p2_yw_call_nums_momr, callfw_kf_count, prv1_callin_ywkf_cnts, call_1001_counts, p2_call10010_counts_momr,
        p3_call10000_counts_momr, is_ts_high, is_tsjj_low, call_1860_1861_counts, call_1860_1861_counts_v,
        call_1860_1861_duration_m, call_1860_1861_duration_m_v, wx_cnt_month, wx_days_month, prv1_wx_cnt,
        prv1_wx_days, prv2_wx_cnt, prv2_wx_days, bank_num_month, prv1_bank_num, prv2_bank_num, bank_cnt_month,
        prv1_bank_cnt, prv2_bank_cnt, jiaz_wending_rate, gprs_wending_rate, is_zifee_mg, is_busi_td, ts_fee,
        wangluo_bumanyi, shangwang_man, xinhao_chai, tonghua_diaohua, shuangjiang, zhunliwang, zhangwu_yuxiaohu,
        yingye_yuxiaohu, yuyin_use_users, yuyin_baohuo, di_tonghua_ratio, liuliang_use_users, tongyong_liuliang_baohuo,
        di_liuliang_ratio, changman_changman_koujing, qianfei_ting, shuangting, danting,phone_num
    ]
    return row

def main():
    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # 获取表的所有列名（按建表语句顺序）
    # 由于列名太多，这里从表定义中手动提取（实际可以从数据库查询，但此处直接列出前几个示意）
    # 注意：下面的列名顺序必须与上面的 row 完全一致。因为上面 row 已经按顺序构建，所以此处只需要写列名即可。
    # 这里为了节省篇幅，直接使用从表定义中复制的前10个列名，实际生产请确保列名列表完整且顺序匹配。
    # 强烈建议：使用下面的代码从数据库中动态获取列名（但需要先建表），或者直接相信 row 的顺序。
    header = [
'month', 'user_id', 'city_id', 'age', 'sex_id', 'prv1_userstatus_id', 'star_level', 'star_level_b', 
'is_jxhm', 'brand_id', 'user_online', 'arpu120_user', 'bd_arpu120_user', 'credit_id', 'credit_id_b', 
'paytype21_user', 'is_acct_counts', 'is_rhtc', 'qx_rhtc_3month', 'xz_rhtc_3month', 'is_jttf', 'qx_jttf_3month', 
'regiontype_id3', 'student_flag', 'month_new_mark', 'month_new_mark_6month', 'zero_mark', 'arpu_fluctuate_mark', 
'arpu_stabilize_mark', 'active_mark', 'dou_mark', 'is_ll_dh', 'is_yy_dh', 'is_dh_2month', 'is_dh_3month', 
'vip_mark', 'ys_yd_yh', 'mon_consume_id', 'call_mark', 'school_flag', 'family_main', 'is_family', 'qx_family_3month', 
'owe_fee', 'owe_fee_pre1', 'owe_fee_pre2', 'zs_fee', 'zs_fee_v', 'zs_fee_time', 'pay_fee', 'pay_fee_pre1', 
'pay_fee_pre2', 'pay_fee_v', 'pay_counts', 'pay_counts_pre1', 'pay_counts_pre2', 'pay_counts_v', 'pay_counts_3month', 
'pay_fee_3month', 'pve_amount', 'pve1_amount', 'pve2_amount', 'prepay_bal', 'prepay_bal_v', 'amount_bd', 'credit', 
'credit_pve1', 'credit_pve2', 'arpu', 'arpu_pve1', 'arpu_pve2', 'avg_3mon_fee', 'arpu_bd', 'arpu_pve1_v', 
'avg_gprsplan_fee_3m', 'newbusi_fee', 'newbusi_fee1', 'newbusi_fee_v', 'lam_yzf_fee', 'lam_yzf_fee_v', 
'lam_yzf_fee_pre1', 'lam_yzf_fee_pre2', 'call_fee', 'call_fee_v', 'gprs_fee', 'gprs_fee_v', 'tax_on_yuezu', 
'pre_tax_on_yuezu', 'pre1_tax_on_yuezu', 'zhekou', 'pre_zhekou', 'pre1_zhekou', 'zhekou_v', 'is_tc_free', 
'jm_tc_sy_times', 'tc_sy_times', 'lam_mythf_fee', 'lam_mythf_fee_pre1', 'lam_mythf_fee_pre2', 'lam_mythf_fee_v', 
'plan_id_bd', 'plan_fee', 'plan_fee_pre1', 'plan_fee_pre2', 'tc_use_times', 'plan_fee_bd', 'plan_six_num', 'is_jd', 
'is_jd_3month', 'is_5gtb', 'plan_5g_mark', 'arpu_momr', 'pve_arpu_momr', 'gprsplan_fee', 'lam_yzf_fee_pve1', 
'lam_yzf_fee_pve2', 'last_gprs_billing_flows', 'before_last_gprs_billing_flows', 'over_flow_3month', 'is_lower_arpu', 
'is_bxl_xs3', 'is_gprs_ct_fee_3month_h', 'is_yuyin_ct_fee_3month_h', 'is_arpu_high', 'is_lower_arpu3', 
'dual_card_user_mark', 'is_llb', 'prv1_llb', 'prv2_llb', 'llb_cnt', 'is_dxb', 'llb_should_fee', 'is_ywzk', 
'new_ywsk', 'prv1_new_ywsk', 'bwsk_new', 'prv1_new_bwsk', 'is_ywsk', 'is_bwsk', 'is_zdhy', 'imei_online', 
'his_imei_track', 'imei_start', 'pre_term_price', 'source_imei_long', 'track_id', 'out_call_duration_m', 
'out_call_duration_m1', 'out_call_duration_m2', 'out_call_duration_m3', 'avg_call_duration_m_prv_3m', 
'avg_out_call_duration_m_3m', 'avg_in_call_dura_3m', 'call_dura_v', 'call_counts', 'avg_callcount_3m', 
'call_counts_bd', 'call_counts_prv1', 'call_counts_prv2', 'call_counts_prv3', 'call_duration_m', 'avg_callduration_3m', 
'call_duration_m_bd', 'call_duration_m_prv1', 'call_duration_m_prv2', 'call_duration_m_prv3', 'call_duration_m_prv_v', 
'out_call_duration', 'out_call_dura_prv1', 'out_call_dura_prv2', 'out_call_counts', 'out_call_counts1', 
'out_call_counts2', 'out_call_counts_v', 'in_call_duration_m', 'in_call_duration_m_pre1', 'in_call_duration_m_v', 
'in_call_counts', 'in_call_counts1', 'in_call_counts2', 'in_call_counts_v', 'out_in_call_d_v', 'inner_call_v', 
'out_in_call_count_v', 'callfw_counts', 'callfw_counts_v', 'callfw_counts1', 'call_opp_counts1', 'call_opp_counts_v', 
'avg_call_counts_3m', 'avg_out_call_counts_prv_3m', 'avg_in_call_counts_3m', 'out_call_counts_3bd', 'in_call_counts_3bd', 
'call_opp_out_counts', 'prv1_call_opp_out_counts', 'prv2_call_opp_out_counts', 'call_opp_in_counts', 
'prv1_call_opp_in_counts', 'prv2_call_opp_in_counts', 'p1_yw_call_opp_counts_momr', 'p2_yw_call_opp_counts_momr', 
'all_bhd', 'dou', 'dou_bd', 'dou_hb_rate', 'zero_call_days', 'tc_userd', 'tc_bhd', 'llb_userd', 'llb_bhd', 
'bill_gprs_userd', 'bill_bhd', 'dx_userd', 'dx_bhd', 'jiezhuan_userd', 'jiezhuan_bhd', 'is_llyz', 'liul_unlimit', 
'pve1_dou', 'pve2_dou', 'dou_hb', 'pre1_liul_unlimit', 'pre2_liul_unlimit', 'gprs_5g_flow_m', 'all_gprs_lte_flows', 
'sn_gprs_flows', 'sw_gprs_flows', 'gprs_left_res', 'jz_gprs_res', 'jz_gprs_res_pve1', 'jz_gprs_res_pve2', 
'is_ct_3month', 'call_duration_fee_3momth', 'llb_should_fee_temp', 'gprs_ct', 'prv1_gprs_ct', 'prv2_gprs_ct', 
'gprs_ct_hb', 'is_gprs_ct_3month', 'llb_5g_mark', 'c_yz_fee', 'c_yz_fee_v', 'gprs_flow_fee', 'gprs_flow_fee_v', 
'yuyin_fee_3month', 'yuyin_ct_fee_3month', 'gprs_fee_3month', 'gprs_ct_fee_3month', 'toll_call_opp_counts', 
'roam_duration_m1', 'roam_duration_m2', 'roam_duration_m3', 'roam_counts_v', 'sw_call_duration_m', 'sw_call_duration_m_v', 
'long_out_dou', 'out_sw_days', 'out_sw_gprs', 'prv1_out_sw_days', 'prv1_out_sw_gprs', 'prv2_out_sw_days', 
'prv2_out_sw_gprs', 'out_sw_hb', 'roam_counts', 'inent_call_counts', 'inent_call_counts_v', 'inent_call_duration_m', 
'inent_call_duration_m_v', 'is_jt', 'is_jt_vpn', 'is_jt_key_cust', 'jtyd_3month', 'innet_jt_time', 'kd_3month', 
'kd_cj_month', 'kd_cj_3month', 'kd_expire_date', 'kd_user_mark', 'ywkd_user_mark', 'if_local_kdcover', 
'if_no_kdcover_bl', 'if_kd_poor', 'kd_bl_times', 'prod_bandwidth', 'mtd_flow', 'mtd_flow_pre1', 'mtd_flow_pre2', 
'mtd_flow_bd', 'is_fuse', 'kb_eff_times', 'kb_exp_times', 'assure_fee', 'is_0_flow', 'is_renew', 'is_mbh', 'is_group', 
'mtd_active_day', 'mtd_active_day_pre1', 'mtd_active_day_pre2', 'mtd_active_day_hb', 'mtd_active_day_bd', 
'mtd_time_length', 'mtd_time_length_pre1', 'mtd_time_length_pre2', 'mtd_time_length_hb', 'mtd_time_length_bd', 'kd_fee', 
'zdxf_fee', 'kb_promoeff_times', 'kb_promoexp_times', 'is_jsb', 'is_box', 'is_voicect', 'is_jt_yigr', 'is_jt_xc', 
'is_jt_xccx', 'is_jt_xccg', 'is_jt_kdcj', 'is_jt_kdywxz', 'pro_kind_contract', 'pro_mbcharge_contract', 
'pro_res_hold_month', 'is_heyue', 'hy_dq_3month', 'hy_sy_times', 'pro_term_contract', 'is_heyuedaoqi', 'is_dx', 
'dx_lj_times', 'dx_sy_times', 'bhd_month', 'join_hd_month', 'join_new_offer_month', 'dg_ll_offer_month', 
'join_new_offer_3month', 'dg_ll_offer_3month', 'hy_never_users', 'hy_repeat_users', 'tuiding_bangbang_cnt_month', 
'tuiding_bangbang_cnt_3month', 'bangbang_yucun_expire', 'bangbang_zengji_expire', 'heyue_3month_expire', 'no_contract_3month', 
'has_contract_3month', 'port_restrict', 'churn_restrict', 'realname_user', 'vice_card_user', 'refund_user', 'refund_remain_months', 
'query_port_sms_6m', 'query_port_sms_cnt_6m', 'apply_port_3m', 'cancel_broadband_3m', 'unbind_bank_alipay', 
'wechat_alipay_use_down', 'address_change', 'new_broadband_other_this', 'new_broadband_other_3m', 'call_10086_port', 
'sms_port_query_this', 'apply_port_this', 'sms_port_query_3m', 'apply_port_3m_again', 'web_search_port', 
'is_ts', 'ts_counts_m', 'ts_counts_3month', 'out_opposite_regular_count', 'yw_call_nums', 'yw_call_opp_counts', 
'yw_call_opp_counts_v', 'yw_in_call_counts', 'yw_in_call_high', 'p1_yw_in_call_counts_momr', 'p2_yw_in_call_counts_momr', 
'yw_in_call_duration', 'p1_yw_in_call_duration_momr', 'p2_yw_in_call_duration_momr', 'p1_yw_call_nums_momr', 
'p2_yw_call_nums_momr', 'callfw_kf_count', 'prv1_callin_ywkf_cnts', 'call_1001_counts', 'p2_call10010_counts_momr', 
'p3_call10000_counts_momr', 'is_ts_high', 'is_tsjj_low', 'call_1860_1861_counts', 'call_1860_1861_counts_v', 
'call_1860_1861_duration_m', 'call_1860_1861_duration_m_v', 'wx_cnt_month', 'wx_days_month', 'prv1_wx_cnt', 
'prv1_wx_days', 'prv2_wx_cnt', 'prv2_wx_days', 'bank_num_month', 'prv1_bank_num', 'prv2_bank_num', 'bank_cnt_month', 
'prv1_bank_cnt', 'prv2_bank_cnt', 'jiaz_wending_rate', 'gprs_wending_rate', 'is_zifee_mg', 'is_busi_td', 'ts_fee', 
'wangluo_bumanyi', 'shangwang_man', 'xinhao_chai', 'tonghua_diaohua', 'shuangjiang', 'zhunliwang', 'zhangwu_yuxiaohu', 
'yingye_yuxiaohu', 'yuyin_use_users', 'yuyin_baohuo', 'di_tonghua_ratio', 'liuliang_use_users', 'tongyong_liuliang_baohuo', 
'di_liuliang_ratio', 'changman_changman_koujing', 'qianfei_ting', 'shuangting', 'danting','phone_num'
    ]

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for batch_start in range(0, TOTAL_ROWS, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, TOTAL_ROWS)
            batch_data = []
            for _ in range(batch_start, batch_end):
                row = generate_one_row()
                batch_data.append(row)
            writer.writerows(batch_data)
            print(f"已写入 {batch_end} / {TOTAL_ROWS} 行")

    print(f"数据生成完成，保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
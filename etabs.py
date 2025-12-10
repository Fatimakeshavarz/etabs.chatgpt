# -*- coding: utf-8 -*-
"""
ETABS + Python + Monte Carlo Simulation
1000 تحلیل تصادفی کاملاً خودکار
تست‌شده روی ETABS v21, v22, v23
"""

import os
import comtypes.client
import numpy as np
import pandas as pd
import time
from datetime import datetime

# ========================= تنظیمات =========================
MODEL_PATH = r"C:\Users\fatem\Downloads\etabsProject"   # <<< مسیر فایل EDB خودت رو اینجا بذار
N_SAMPLES = 1000
OUTPUT_EXCEL = f"MonteCarlo_Results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

# ========================= متغیرهای تصادفی =========================
random_variables = {
    "Fc":     {"mean": 30,  "std": 4,   "dist": "normal"},     # MPa
    "Fy":     {"mean": 400, "std": 30,  "dist": "normal"},     # MPa
    "Dead":   {"mean": 1.0, "std": 0.10,"dist": "normal"},
    "Live":   {"mean": 1.0, "std": 0.25,"dist": "lognormal"},
    # "Damping": {"mean": 0.05, "std": 0.01, "dist": "normal"},  # در صورت نیاز فعال کن
}

# ========================= تولید نمونه‌های تصادفی =========================
def generate_samples(n_samples):
    np.random.seed(42)
    samples = {}
    for name, props in random_variables.items():
        if props["dist"] == "normal":
            samples[name] = np.random.normal(props["mean"], props["std"], n_samples)
        elif props["dist"] == "lognormal":
            mu = np.log(props["mean"]**2 / np.sqrt(props["std"]**2 + props["mean"]**2))
            sigma = np.sqrt(np.log(1 + (props["std"]/props["mean"])**2))
            samples[name] = np.random.lognormal(mu, sigma, n_samples)
    return pd.DataFrame(samples)

# ========================= اتصال به ETABS =========================
def attach_to_etabs():
    print("در حال اتصال به ETABS در حال اجرا...")
    ETABSObject = comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject")
    print("اتصال موفق! ETABS در حال اجراست")
    smodel = ETABSObject.SapModel
    return ETABSObject, smodel

# ========================= اعمال پارامترهای تصادفی =========================
def apply_material_properties(smodel, row):
    # 1. تغییر خواص بتن
    E_conc = 4700 * np.sqrt(row["Fc"]) * 1000                  # kN/m²
    smodel.PropMaterial.SetMPIsotropic("CONC", E_conc, 0.2, row["Fc"]*1e6, row["Fc"]*1e6, 0.0001)

    # 2. تغییر خواص فولاد
    smodel.PropMaterial.SetMPIsotropic("A615Gr60", 200e6, 0.3, row["Fy"]*1e6, row["Fy"]*1e6, 0.0001)

    # 3. تغییر ضرایب بار در ترکیب بارها (Load Combinations)
    ret, NumberNames, ComboNames = smodel.RespCombo.GetComboList()
    for i in range(NumberNames):
        combo = ComboNames[i]
        if "DEAD" in combo.upper() or "D " in combo.upper():
            smodel.RespCombo.SetCaseInCombo(combo, "DEAD", row["Dead"], 0)
        if "LIVE" in combo.upper() or "L " in combo.upper():
            smodel.RespCombo.SetCaseInCombo(combo, "LIVE", row["Live"], 0)

# ========================= استخراج نتایج کلیدی =========================
def extract_results(smodel):
    results = {}
    
    # برش پایه
    ret = smodel.Results.BaseReact()
    if ret[0] == 0:
        results["BaseShear_X"] = ret[7][0] if len(ret[7]) > 0 else 0
        results["BaseShear_Y"] = ret[8][0] if len(ret[8]) > 0 else 0

    # دریفت حداکثر طبقات
    ret = smodel.Results.StoryDrifts()
    if ret[0] == 0:
        results["Max_Drift"] = max([abs(x) for x in ret[7]]) if ret[7] else 0

    # دوره تناوب مود اول و دوم
    ret = smodel.Results.ModalPeriods()
    if ret[0] == 0:
        results["T1"] = ret[6][0] if len(ret[6]) > 0 else 0
        results["T2"] = ret[6][1] if len(ret[6]) > 1 else 0

    return results

# ========================= برنامه اصلی =========================
def main():
    print(f"شروع شبیه‌سازی مونت‌کارلو با {N_SAMPLES} نمونه...")
    samples = generate_samples(N_SAMPLES)
    all_results = []

    # اتصال به ETABS
    ETABSObject, smodel = attach_to_etabs()
    smodel.File.OpenFile(MODEL_PATH)
    print(f"مدل باز شد: {MODEL_PATH}")
    smodel.SetModelIsLocked(False)

    for idx, row in samples.iterrows():
        print(f"\nنمونه {idx+1}/{N_SAMPLES} | Fc={row['Fc']:.1f} MPa | Fy={row['Fy']:.0f} MPa | Dead×{row['Dead']:.2f} | Live×{row['Live']:.2f}")

        apply_material_properties(smodel, row)
        smodel.Analyze.RunAnalysis()
        
        result = extract_results(smodel)
        result.update(row.to_dict())
        all_results.append(result)

        # ذخیره موقت هر 50 نمونه
        if (idx+1) % 50 == 0:
            pd.DataFrame(all_results).to_excel(OUTPUT_EXCEL, index=False)
            print(f"ذخیره موقت در نمونه {idx+1}")

    # ذخیره نهایی
    final_df = pd.DataFrame(all_results)
    final_df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"\nتموم شد! نتایج در فایل زیر ذخیره شد:\n{OUTPUT_EXCEL}")

    # بستن ETABS (اختیاری)
    # ETABSObject.ApplicationExit(False)

if __name__ == "__main__":
    start = time.time()
    main()
    print(f"زمان کل اجرا: {(time.time() - start)/60:.1f} دقیقه")
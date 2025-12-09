import time
from datetime import datetime
import numpy as np
import pandas as pd

# تنظیمات پیش‌فرض
DEFAULT_N_SAMPLES = 10
DEFAULT_COMBO_NAME = "Combo 1"
DEFAULT_CONCRETE_NAME = "CONC"
DEFAULT_STEEL_NAME = "A615Gr60"

# متغیرهای تصادفی نمونه
random_variables = {
    "Fc": {"mean": 30, "std": 4, "dist": "normal", "unit": "MPa"},  # مقاومت بتن
    "Fy": {"mean": 400, "std": 30, "dist": "normal", "unit": "MPa"},  # مقاومت فولاد
    "Dead": {"mean": 1.00, "std": 0.10, "dist": "normal"},  # ضریب بار مرده
    "Live": {"mean": 1.00, "std": 0.25, "dist": "lognormal"},  # ضریب بار زنده
    "E_Concrete": {"mean": 1.00, "std": 0.15, "dist": "normal"},  # ضریب اصلاح مدول بتن
}


def _sample_random_variables(rng, config):
    samples = {}
    for name, props in config.items():
        dist = props.get("dist", "normal")
        mean = props.get("mean", 0.0)
        std = props.get("std", 0.0)

        if dist == "normal":
            value = float(rng.normal(mean, std))
        elif dist == "lognormal":
            # تبدیل میانگین/انحراف معیار به پارامترهای لاگ نرمال
            variance = std**2
            mu = np.log((mean**2) / np.sqrt(variance + mean**2))
            sigma = np.sqrt(np.log(1 + variance / (mean**2)))
            value = float(rng.lognormal(mu, sigma))
        else:
            raise ValueError(f"توزیع ناشناخته برای {name}: {dist}")

        samples[name] = value
    return samples


def set_material_properties(smodel, Fc, Fy, e_multiplier=1.0):
    """
    ست کردن خواص متریال‌ها (با حدس امضای تابع ETABS).
    اگر API متفاوت باشد، فقط هشدار چاپ می‌شود.
    """
    conc_name = DEFAULT_CONCRETE_NAME
    steel_name = DEFAULT_STEEL_NAME

    # مدول بتن برحسب MPa (تقریبی)
    E_conc = max(0.0, 4700.0 * np.sqrt(max(Fc, 0.0)) * e_multiplier)
    E_steel = 200000.0  # MPa فرضی برای فولاد

    try:
        ret = smodel.PropMaterial.SetMPIsotropic(conc_name, E_conc, 0.2, 1e-5)
        if ret != 0:
            print("هشدار: تنظیم خواص بتن ناموفق بود.")
    except Exception as exc:
        print(f"هشدار: تنظیم خواص بتن انجام نشد ({exc})")

    try:
        ret = smodel.PropMaterial.SetMPIsotropic(steel_name, E_steel, 0.3, 1.2e-5)
        if ret != 0:
            print("هشدار: تنظیم خواص فولاد ناموفق بود.")
    except Exception as exc:
        print(f"هشدار: تنظیم خواص فولاد انجام نشد ({exc})")


def set_load_multipliers(smodel, dead_mult, live_mult, combo_name=DEFAULT_COMBO_NAME):
    """
    ضرایب بار مرده/زنده را در یک کامبو به‌روز می‌کند.
    اگر API متفاوت باشد، فقط هشدار چاپ می‌شود.
    """
    try:
        res = smodel.RespCombo.GetCaseList(combo_name)
    except Exception as exc:
        print(f"هشدار: خواندن لیست کیس‌های {combo_name} ممکن نشد ({exc})")
        return

    if not res or res[0] != 0:
        print(f"هشدار: دریافت کیس‌های {combo_name} با خطا مواجه شد.")
        return

    _, number_items, load_cases, scale_factors = res
    if number_items == 0:
        print(f"هشدار: کامبو {combo_name} خالی است.")
        return

    new_scale_factors = []
    for lc, sf in zip(load_cases, scale_factors):
        name_upper = str(lc).upper()
        if name_upper.startswith("DEAD"):
            new_scale_factors.append(sf * dead_mult)
        elif name_upper.startswith("LIVE"):
            new_scale_factors.append(sf * live_mult)
        else:
            new_scale_factors.append(sf)

    try:
        smodel.RespCombo.SetCaseList(combo_name, number_items, load_cases, new_scale_factors)
    except Exception as exc:
        print(f"هشدار: به‌روزرسانی ضرایب کامبو ممکن نشد ({exc})")


def run_analysis(smodel):
    ret = smodel.Analyze.RunAnalysis()
    if ret != 0:
        raise RuntimeError(f"RunAnalysis خطا داد (کد {ret})")


def get_max_drift(smodel):
    try:
        res = smodel.Results.StoryDrifts()
    except Exception:
        return None

    if not res or res[0] != 0:
        return None

    _, number_results, *_rest = res
    if number_results == 0:
        return None

    # انتظار داریم Drift نزدیک انتهای تاپل باشد
    Drift = res[-4] if len(res) >= 4 else None
    if Drift is None:
        return None

    try:
        return max(abs(d) for d in Drift if d is not None)
    except Exception:
        return None


def get_base_shear(smodel):
    try:
        res = smodel.Results.BaseReact()
    except Exception:
        return None

    if not res or res[0] != 0:
        return None

    _, number_results, *_rest = res
    if number_results == 0:
        return None

    # انتظار داریم نیروهای محوری در ابتدای تاپل باشند
    try:
        F1 = res[-6]
        F2 = res[-5]
        max_fx = max(abs(f) for f in F1)
        max_fy = max(abs(f) for f in F2)
        return max(max_fx, max_fy)
    except Exception:
        return None


def run_monte_carlo(
    smodel,
    n_samples=DEFAULT_N_SAMPLES,
    rng_seed=None,
    save_csv=None,
    verbose=True,
):
    """
    اجرای مونت‌کارلو روی مدل باز شده در ETABS.
    smodel: SapModel فعال
    n_samples: تعداد نمونه
    save_csv: مسیر فایل خروجی CSV (اختیاری)
    """
    rng = np.random.default_rng(rng_seed)
    results = []
    start = time.time()

    for i in range(n_samples):
        sample = _sample_random_variables(rng, random_variables)
        row = {**sample}
        try:
            set_material_properties(
                smodel,
                Fc=sample["Fc"],
                Fy=sample["Fy"],
                e_multiplier=sample["E_Concrete"],
            )
            set_load_multipliers(
                smodel,
                dead_mult=sample["Dead"],
                live_mult=sample["Live"],
            )
            run_analysis(smodel)
            row["max_drift"] = get_max_drift(smodel)
            row["base_shear"] = get_base_shear(smodel)
            row["error"] = ""
        except Exception as exc:
            row["max_drift"] = None
            row["base_shear"] = None
            row["error"] = str(exc)

        row["timestamp"] = datetime.now().isoformat()
        results.append(row)

        if verbose:
            status = f"[{i+1}/{n_samples}] drift={row['max_drift']} base={row['base_shear']}"
            if row["error"]:
                status += f" | خطا: {row['error']}"
            print(status)

    elapsed = time.time() - start
    if verbose:
        print(f"مونت‌کارلو تمام شد ({n_samples} نمونه) در {elapsed:.1f} ثانیه.")

    if save_csv:
        try:
            pd.DataFrame(results).to_csv(save_csv, index=False)
            if verbose:
                print(f"نتایج در {save_csv} ذخیره شد.")
        except Exception as exc:
            print(f"هشدار: ذخیره CSV ناموفق بود ({exc})")

    return results


__all__ = [
    "run_monte_carlo",
    "random_variables",
    "set_material_properties",
    "set_load_multipliers",
    "get_max_drift",
    "get_base_shear",
]

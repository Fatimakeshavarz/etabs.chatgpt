# main.py
import importlib.util
import importlib.machinery
from pathlib import Path
from etabs_chatgpt import load_model_from_path
from etabs_interface import disconnect_from_etabs, print_model_path


def _load_monte_carlo_module():
    script_path = Path(__file__).with_name("mont.karlo")
    if not script_path.exists():
        # تلاش برای فایل معمولی .py
        script_path = Path(__file__).with_name("mont.py")
    if not script_path.exists():
        raise FileNotFoundError(f"فایل مونت‌کارلو یافت نشد: {script_path}")

    # به صورت صریح لودر را مشخص می‌کنیم تا پسوند غیرمعمول کار کند.
    loader = importlib.machinery.SourceFileLoader("monte_carlo_script", str(script_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise ImportError(f"عدم توانایی در ساخت spec برای {script_path.name}")

    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


if __name__ == "__main__":
    try:
        file_path = input("مسیر فایل ETABS (.edb) را وارد کنید: ").strip().strip('"').strip("'")
        if not file_path:
            print("مسیر خالی است؛ عملیات لغو شد.")
        else:
            etabs_obj, sap_model = load_model_from_path(file_path, visible=True)
            try:
                print_model_path(sap_model)

                # خواندن و اجرای مونت‌کارلو از فایل mont.karlo
                mc_module = _load_monte_carlo_module()
                sample_input = input("تعداد نمونه مونت‌کارلو (خالی = 10): ").strip()
                n_samples = int(sample_input) if sample_input else mc_module.DEFAULT_N_SAMPLES

                print(f"اجرای مونت‌کارلو با {n_samples} نمونه...")
                results = mc_module.run_monte_carlo(
                    sap_model,
                    n_samples=n_samples,
                    verbose=True,
                )
                print(f"تعداد نتایج ثبت‌شده: {len(results)}")

                input("\nETABS باز است؛ Enter بزن تا بسته شود...")
            finally:
                disconnect_from_etabs(etabs_obj, close_etabs=True)
    except Exception as e:
        print(f"خطا: {e}")
        input("Enter بزن تا خارج بشی...")

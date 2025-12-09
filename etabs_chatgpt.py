import os
from etabs_interface import connect_to_etabs, disconnect_from_etabs


def create_grid_system(sapmodel, story_heights, x_coordinates, y_coordinates):
    """
    یک مدل جدید باز می‌کند و گرید ساده ایجاد می‌کند.
    story_heights: [ارتفاع طبقه اول، ارتفاع تکراری] به متر
    x_coordinates / y_coordinates: مختصات خطوط گرید (متر)
    """
    if len(story_heights) < 2:
        raise ValueError("حداقل دو مقدار برای ارتفاع طبقات (اول و تکراری) لازم است")
    if len(x_coordinates) < 2 or len(y_coordinates) < 2:
        raise ValueError("حداقل دو خط گرید در هر جهت لازم است")

    number_of_stories = len(story_heights)
    typical_story_height = story_heights[1]
    bottom_story_height = story_heights[0]
    number_of_lines_x = len(x_coordinates)
    number_of_lines_y = len(y_coordinates)
    spacing_x = x_coordinates[1] - x_coordinates[0]
    spacing_y = y_coordinates[1] - y_coordinates[0]

    ret = sapmodel.InitializeNewModel(6)  # kN-m units
    if ret == 0:
        print("InitializeNewModel موفق بود")
    else:
        raise RuntimeError("InitializeNewModel با خطا مواجه شد")

    ret = sapmodel.File.NewGridOnly(
        number_of_stories,
        typical_story_height,
        bottom_story_height,
        number_of_lines_x,
        number_of_lines_y,
        spacing_x,
        spacing_y,
    )
    if ret == 0:
        print("NewGridOnly موفق بود - گرید ساخته شد")
    else:
        raise RuntimeError("NewGridOnly با خطا مواجه شد")

    # لیست نقاط تقاطع خطوط گرید برای استفاده بعدی
    grid_points = [[(x, y) for y in y_coordinates] for x in x_coordinates]
    return grid_points


def run_sample():
    etabs_obj, sap_model = connect_to_etabs(visible=True)
    try:
        grid_points = create_grid_system(
            sapmodel=sap_model,
            story_heights=[3.2, 3.0, 3.0],  # طبقه همکف + دو طبقه مشابه
            x_coordinates=[0, 6, 12, 18],  # 4 خط در جهت X با فاصله 6 متر
            y_coordinates=[0, 5, 10],  # 3 خط در جهت Y با فاصله 5 متر
        )
        print("گرید ساخته شد. نقاط تقاطع نمونه: ", grid_points[0][:3])
        input("\nETABS باز است؛ Enter بزن تا بسته شود...")
    finally:
        disconnect_from_etabs(etabs_obj, close_etabs=True)


def load_model_from_path(file_path, visible=True):
    """
    یک فایل ETABS (.edb) را از مسیر داده‌شده باز می‌کند.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"فایل یافت نشد: {file_path}")

    etabs_obj, sap_model = connect_to_etabs(visible=visible)
    try:
        ret = sap_model.File.OpenFile(file_path)
        if ret != 0:
            raise RuntimeError(f"باز کردن فایل با خطا مواجه شد (کد {ret})")
        print(f"فایل با موفقیت باز شد: {file_path}")
        return etabs_obj, sap_model
    except Exception:
        disconnect_from_etabs(etabs_obj, close_etabs=True)
        raise

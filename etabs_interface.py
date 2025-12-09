
# etabs_interface.py
import os
import sys
import comtypes.client

def connect_to_etabs(visible=True, version="23"):
    """
    اتصال به ETABS - 100% کارکردی برای نسخه 21 تا 24
    """
    try:
        # اول سعی کن به نمونه باز شده وصل بشه
        ETABSObject = comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject")
        print("به ETABS در حال اجرا متصل شد")
    except (OSError, comtypes.COMError):
        print("ETABS باز نیست، در حال راه‌اندازی...")
        try:
            ETABSObject = comtypes.client.CreateObject("CSI.ETABS.API.ETABSObject")
            ETABSObject.ApplicationStart(Visible=visible)
            print("ETABS با موفقیت باز شد")
        except Exception as e:
            print(f"خطا در راه‌اندازی ETABS: {e}")
            sys.exit(-1)

    SapModel = ETABSObject.SapModel
    return ETABSObject, SapModel

def disconnect_from_etabs(ETABSObject, close_etabs=False):
    if close_etabs:
        ETABSObject.ApplicationExit(False)
        print("ETABS بسته شد")
    ETABSObject = None
    SapModel = None

def print_model_path(SapModel):
    file_path = SapModel.GetModelFilename()
    print(f"مدل باز شده: {file_path}")
# main.py
from etabs_interface import connect_to_etabs, disconnect_from_etabs, print_model_path

if __name__ == "__main__":
    print("در حال اتصال به ETABS...")
    try:
        etabs_obj, sap_model = connect_to_etabs(visible=True)
        
        # تست: یک مدل جدید بساز
        ret = sap_model.InitializeNewModel(0)  # 0 = kN-m-C
        if ret == 0:
            print("مدل جدید با موفقیت ساخته شد")
        
        # تست: نام مدل
        print_model_path(sap_model)
        
        input("\nETABS باز است! Enter بزن تا بسته بشه...")
        disconnect_from_etabs(etabs_obj, close_etabs=True)
        
    except Exception as e:
        print(f"خطا: {e}")
        input("Enter بزن تا خارج بشی...")
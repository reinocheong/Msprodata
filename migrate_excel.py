# --- 这是【终极去重版】的 migrate_excel.py ---

import os
import pandas as pd
from app import create_app, db, Booking, Expense
import uuid
import re

EXCEL_FOLDER = 'excel_data'

def clean_and_convert_to_float(value):
    if value is None or pd.isna(value):
        return 0.0
    cleaned_string = re.sub(r'[^0-9.]', '', str(value))
    if cleaned_string == '' or cleaned_string == '.':
        return 0.0
    return float(cleaned_string)

def migrate_bookings(filepath, processed_ids):
    """迁移预订数据 (增加了去重功能)"""
    print(f"  -> 正在处理预订文件: {filepath}")
    added_count = 0
    skipped_count = 0
    duplicate_count = 0
    try:
        df = pd.read_excel(filepath)
        df.columns = [str(c).strip() for c in df.columns]
        for index, row in df.iterrows():
            try:
                if pd.isna(row.get('Unit Name')) or pd.isna(row.get('CHECKIN')):
                    skipped_count += 1
                    continue
                
                # ### 我在这里为您做了最终修改：增加了ID去重逻辑 ###
                booking_id = row.get('Booking Number')
                is_new_uuid = False
                if pd.isna(booking_id) or str(booking_id).strip() == '':
                    booking_id = str(uuid.uuid4())
                    is_new_uuid = True # 标记这是一个新生成的ID
                else:
                    booking_id = str(booking_id)

                # 检查ID是否已经处理过
                if not is_new_uuid and booking_id in processed_ids:
                    duplicate_count += 1
                    continue # 如果是重复的ID，直接跳过
                
                checkin_date = pd.to_datetime(row['CHECKIN'])
                checkout_date = pd.to_datetime(row['CHECKOUT'])

                new_booking = Booking(
                    id=booking_id, unit_name=row['Unit Name'], checkin=checkin_date,
                    checkout=checkout_date, channel=row.get('Channel'), on_offline=row.get('ON/OFFLINE'),
                    pax=int(row.get('Pax', 0)), duration=int(row.get('Duration', 0)),
                    price=clean_and_convert_to_float(row.get('Price')), 
                    cleaning_fee=clean_and_convert_to_float(row.get('CLEANING FEE')),
                    platform_charge=clean_and_convert_to_float(row.get('Platform Charge')), 
                    total=clean_and_convert_to_float(row.get('TOTAL'))
                )
                db.session.add(new_booking)
                processed_ids.add(booking_id) # 将处理过的ID加入到“记忆大脑”中
                added_count += 1

            except (pd.errors.OutOfBoundsDatetime, ValueError, TypeError) as e:
                print(f"     [警告] 跳过第 {index + 2} 行，因为数据格式问题: {e}")
                skipped_count += 1
                continue
        
        if added_count > 0: print(f"  -> 成功准备了 {added_count} 条【预订】记录。")
        if skipped_count > 0: print(f"  -> 因数据问题跳过了 {skipped_count} 条记录。")
        if duplicate_count > 0: print(f"  -> 因ID重复跳过了 {duplicate_count} 条记录。")

    except Exception as e:
        print(f"  [严重错误] 处理文件 {filepath} 时发生错误: {e}")
        raise

def migrate_expenses(filepath):
    # (支出部分保持不变)
    # ... 省略支出部分代码，与上一版相同 ...
    print(f"  -> 正在处理支出文件: {filepath}")
    added_count = 0
    skipped_count = 0
    try:
        df = pd.read_excel(filepath)
        df.columns = [str(c).strip() for c in df.columns]
        for index, row in df.iterrows():
            try:
                if pd.isna(row.get('DEBIT')) or pd.isna(row.get('Date')):
                    skipped_count += 1
                    continue
                new_expense = Expense(unit_name=row['Unit Name'], date=pd.to_datetime(row['Date']), description=row.get('PARTICULARS'), debit=clean_and_convert_to_float(row.get('DEBIT')))
                db.session.add(new_expense)
                added_count += 1
            except (pd.errors.OutOfBoundsDatetime, ValueError, TypeError) as e:
                print(f"     [警告] 跳过第 {index + 2} 行，因为数据格式问题: {e}")
                skipped_count += 1
                continue
        if added_count > 0: print(f"  -> 成功准备了 {added_count} 条【支出】记录。")
        if skipped_count > 0: print(f"  -> 跳过了 {skipped_count} 条无效的支出记录。")
    except Exception as e:
        print(f"  [严重错误] 处理文件 {filepath} 时发生错误: {e}")
        raise


def main():
    app = create_app()
    with app.app_context():
        print("\n开始进行Excel数据大搬家...")
        if not os.path.exists(EXCEL_FOLDER):
            print(f"\n[严重错误] 文件夹 '{EXCEL_FOLDER}' 不存在！")
            return
        
        processed_booking_ids = set() # 创建一个空的“记忆大脑”

        try:
            for filename in os.listdir(EXCEL_FOLDER):
                if filename.endswith(('.xlsx', '.xls')) and not filename.startswith('~'):
                    filepath = os.path.join(EXCEL_FOLDER, filename)
                    if 'expense' in filename.lower() or '支出' in filename.lower() or 'debit' in filename.lower():
                        migrate_expenses(filepath)
                    else:
                        migrate_bookings(filepath, processed_booking_ids) # 把“记忆大脑”传进去
            
            print("\n正在将所有数据写入数据库，请稍候...")
            db.session.commit()
            print("\n" + "="*50)
            print("恭喜！数据大搬家圆满完成！所有Excel数据已成功导入数据库。")
            print("="*50)
            print("现在您可以重新运行 `flask run` 来查看您的网站了。")

        except Exception as e:
            print(f"\n[严重错误] 数据迁移过程中断: {e}")
            db.session.rollback()

if __name__ == '__main__':
    main()
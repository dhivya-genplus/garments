import shutil
import os

def sync_all_trackers():
    src = 'docs/GARMENTS_ERP_MASTER_TRACKER.xlsx'
    if not os.path.exists(src):
        print(f"Source file {src} does not exist.")
        return

    targets = ['docs/GARMENTS_ERP_TRACKER.xlsx', 'docs/TRACKER.xlsx']
    for target in targets:
        try:
            shutil.copyfile(src, target)
            print(f"Successfully updated {target}")
        except Exception as e:
            print(f"Could not update {target}: {e} (File may be open in Excel. Close Excel and rerun).")

if __name__ == '__main__':
    sync_all_trackers()

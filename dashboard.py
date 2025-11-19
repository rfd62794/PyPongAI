# dashboard.py
import os
import pandas as pd
import glob
import config

def generate_report():
    print("--- Project PaddleMind Analytics Dashboard ---")
    
    # 1. Analyze Game Logs (AI vs AI training logs usually, or PvP if logged)
    # Currently analytics.py logs games. Let's see if we have any.
    log_files = glob.glob(os.path.join(config.LOG_DIR, "*.csv"))
    if log_files:
        print(f"\nFound {len(log_files)} game log files.")
        # Combine all logs
        df_list = []
        for f in log_files:
            try:
                df = pd.read_csv(f)
                df_list.append(df)
            except Exception as e:
                print(f"Error reading {f}: {e}")
        
        if df_list:
            full_df = pd.concat(df_list, ignore_index=True)
            print(f"Total Frames Recorded: {len(full_df)}")
            print(f"Average Ball Speed X: {full_df['ball_vel_x'].abs().mean():.2f}")
            print(f"Max Score Left: {full_df['score_left'].max()}")
            print(f"Max Score Right: {full_df['score_right'].max()}")
    else:
        print("\nNo game logs found in logs/ directory.")

    # 2. Analyze Human Data
    human_dir = "human_data"
    human_files = glob.glob(os.path.join(human_dir, "*.csv"))
    if human_files:
        print(f"\nFound {len(human_files)} human gameplay logs.")
        h_df_list = []
        for f in human_files:
            try:
                df = pd.read_csv(f)
                h_df_list.append(df)
            except Exception as e:
                print(f"Error reading {f}: {e}")
        
        if h_df_list:
            human_df = pd.concat(h_df_list, ignore_index=True)
            print(f"Total Human Frames: {len(human_df)}")
            action_counts = human_df['human_action'].value_counts()
            print("Human Action Distribution:")
            print(action_counts)
    else:
        print("\nNo human data found in human_data/ directory.")

    # 3. Model Inventory
    models = glob.glob(os.path.join(config.MODEL_DIR, "*.pkl"))
    print(f"\nTotal Models Saved: {len(models)}")

if __name__ == "__main__":
    try:
        generate_report()
    except KeyboardInterrupt:
        print("\n[!] Dashboard interrupted by user.")
    except Exception as e:
        print(f"\n[!] An error occurred: {e}")

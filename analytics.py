# analytics.py
    row = [
        current_time,
        score_data["ball_x"],
        score_data["ball_y"],
        score_data["ball_vel_x"],
        score_data["ball_vel_y"],
        score_data["paddle_left_y"],
        score_data["paddle_right_y"],
        score_data["score_left"],
        score_data["score_right"]
    ]
    
    with open(log_filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)

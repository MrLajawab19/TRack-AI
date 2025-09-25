mock_trains = {
    "12951": {
        "trainNo": "12951",
        "trainName": "Mumbai Rajdhani Express",
        "source": "New Delhi",
        "destination": "Mumbai Central",
        "status": "Delayed 20 min",
        "delayReason": "Signal congestion",
        "stations": [
            {"name": "New Delhi", "schDep": "16:55", "actDep": "16:55"},
            {"name": "Ghaziabad", "schDep": "17:35", "actDep": "17:50"},
            {"name": "Aligarh", "schDep": "19:05", "actDep": "19:05"},
            {"name": "Kanpur", "schArr": "21:45", "expArr": "22:05"}
        ],
        "liveLocation": "Between Aligarh and Etawah"
    },
    "12033": {
        "trainNo": "12033",
        "trainName": "Kanpur Shatabdi Express",
        "source": "New Delhi",
        "destination": "Kanpur Central",
        "status": "On Time",
        "delayReason": None,
        "stations": [
            {"name": "New Delhi", "schDep": "15:50", "actDep": "15:50"},
            {"name": "Ghaziabad", "schDep": "16:25", "actDep": "16:25"},
            {"name": "Etawah", "schDep": "18:42", "actDep": "18:42"},
            {"name": "Kanpur", "schArr": "20:20", "expArr": "20:20"}
        ],
        "liveLocation": "Approaching Etawah"
    },
    "12452": {
        "trainNo": "12452",
        "trainName": "Shram Shakti Express",
        "source": "New Delhi",
        "destination": "Kanpur Central",
        "status": "Delayed 10 min",
        "delayReason": "Heavy traffic near Tundla",
        "stations": [
            {"name": "New Delhi", "schDep": "23:55", "actDep": "23:55"},
            {"name": "Ghaziabad", "schDep": "00:30", "actDep": "00:30"},
            {"name": "Tundla", "schDep": "02:47", "actDep": "02:57"},
            {"name": "Kanpur", "schArr": "04:55", "expArr": "05:05"}
        ],
        "liveLocation": "Between Tundla and Etawah"
    }
}

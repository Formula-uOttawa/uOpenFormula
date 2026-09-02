import ctypes

AIM_DLL_FUNCTION_PROTOTYPES = {
    # Library
    "get_library_date": ctypes.CFUNCTYPE(
        ctypes.c_char_p
    ),
    "get_library_time": ctypes.CFUNCTYPE(
        ctypes.c_char_p
    ),

    # File management
    "open_file": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_char_p
    ),
    "open_file_with_licence": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_char_p
    ),
    "get_last_open_error": ctypes.CFUNCTYPE(
        ctypes.c_char_p
    ),
    "close_file_n": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_char_p
    ),
    "close_file_i": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_logger_id": ctypes.CFUNCTYPE(
        ctypes.c_uint,
        ctypes.c_int
    ),

    # Device information
    "get_number_of_devices": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_device_id": ctypes.CFUNCTYPE(
        ctypes.c_uint,
        ctypes.c_int,
        ctypes.c_int
    ),

    # Session / metadata
    "get_vehicle_name": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int
    ),
    "get_track_name": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int
    ),
    "get_racer_name": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int
    ),
    "get_championship_name": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int
    ),
    "get_session_type_name": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int
    ),
    "get_date_and_time": ctypes.CFUNCTYPE(
        ctypes.c_void_p,
        ctypes.c_int
    ),

    # Laps
    "get_laps_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_lap_info": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double)
    ),

    # Session duration
    "get_session_duration": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double)
    ),

    # Channels
    "get_channels_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_channel_name": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_channel_name_no_spaces": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_channel_units": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_channel_samples_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_channel_samples": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int
    ),
    "get_lap_channel_samples_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_lap_channel_samples": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int
    ),

    # GPS channels
    "set_GPS_sample_freq": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_double
    ),
    "get_GPS_channels_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_channel_name": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_channel_name_no_spaces": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_channel_units": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_channel_samples_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_channel_samples": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int
    ),
    "get_lap_GPS_channel_samples_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_lap_GPS_channel_samples": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int
    ),

    # GPS raw channels
    "get_GPS_raw_channels_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_raw_channel_name": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_raw_channel_name_no_spaces": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_raw_channel_units": ctypes.CFUNCTYPE(
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_raw_channel_samples_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_GPS_raw_channel_samples": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int
    ),
    "get_lap_GPS_raw_channel_samples_count": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ),
    "get_lap_GPS_raw_channel_samples": ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int
    ),

    # Testing / diagnostics
    "library_test_on_open_files": ctypes.CFUNCTYPE(
        ctypes.c_char_p
    ),
}
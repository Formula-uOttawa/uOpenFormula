# Telemetry Application Architecture

This diagram shows how the main classes interact.

```mermaid


classDiagram
    class Runtime{
        +DataManager DataManager
 	    +home_page HomePage
 	    +render_manager RenderManager
        +init (self)
 	    +boot (self)
 	    +init_menu_bar (self)
 	    +update_break_temp (self, temps)
 	    +play_brake_temps (self, flag)
 	    +set_brake_temp_step (self, playrate)
 	    +set_brake_texture (self, texture)
    }
    class DataManager {
        +dict datasets
        +func update_brake_temps
 	    +func play_brake_temps
 	    +func set_brake_temp_step
 	    +func generate_disc_function
 	    +list brake_temps
        +init(self, update_brake_temps, play_brake_temps, set_brake_temp_step, generate_disc_function)
        +get_file (self)
 	    +create_dataset (self)
 	    +get_dataset (self, dataset_id)
 	    +set_brake_temps (self, temps)
    }
    class HomePage {
        +DataManager DataManager
 	    +theme_nav_active 
 	    +theme_nav_inactive
 	    +nav Tree
        +list nav_stack
        +dict views
 	    +str message
        +list SWAPPABLE_WINDOWS
        +init (self, DataManager)
 	    +nav_themes (self)
 	    +push_nav (self, view_key)
 	    +pop_nav (self)
 	    +show_landing (self)
 	    +new_project (self)
 	    +load_project (self)
 	    +load_file (self)
 	    +load_new_data_file (self)
 	    +new_dataset (self)
 	    +show_home (self)
 	    +get_motm (self)
 	    +make_home_view (self)
 	    +positon_motm (self)
 	    +resize_windows (self)
        +_build_nav_tree (self)
 	    +_update_highlights (self, active_key)
 	    +_switch_main_view (self, view_key)
 	    +_refresh_sidebar (self)
 	    +_build_sidebar_for (self, view_key)
        
    }
    class DataSet {
        +str path
        +DataFrame df
        +DataFrame df_excl_time
        +dict metadata
        +dict channels
        +int header_index
        +str name
        +init (self)
        +import_and_validate (self, path, name)
        #_load (self)
        #_find_header_index_and_metadata (self)
        #_validate_not_all_zero (self)
        #_validate_variation (self)
    }
    class RenderManager {
        +bool play_brake_temps
        +list brake_temps
 	    +generate_brake_texture
        +int index
        +int step
        +int update_interval
        +init (self)
 	    +start (self)
    }
    class OilStarvationView {
        +DataSet ds
        +DataFrame df
        +str path 
        +str current_graph
        +list oil_default_upper 
        +list oil_default_lower 
        +list oil_operating_upper 
        +list oil_operating_lower 
        +list oil_operating_RPM 
        +list lat_g_low
        +list lat_g_normal
        +list lat_g_high
        +list time
        +list rpm 
        +list oil_pressure 
        +list oil_p_scaled
        +list lat_g 
        +list lat_g_scaled
        +list long_g_scaled
        +list long_g 
        +list rad_temp 
        +list starvation_distrobution_keys
        +list starvation_distrobution_percentages
        +init (self, DataManager)
        +show_graph (self, showing_graph)
        +build (self, parent_tag)
        +reset_oil_graphs (self)
        +reset_oil_ranges (self)
        +update_graphs (self)
        +refresh (self)
    }
    class DataFilesView {
        +data_manager DataManager
        +init (self, DataManager)
 	    +build (self, parent_tag)
 	    +refresh (self)
 	    +add_file (self, dataset_id, dataset)
 	    +table (self)
    }
    class BrakeTempView {
        +DataManager dm
        +DataSet ds
        +DataFrame df
        +str path
        +int size
        +float inner_radius
        +int outer_radius
        +int bands
        +list generate_disc_texture
        +list visible_mask
        +int band_index 
        +list band_masks
        +init (self, DataManager)
        +build (self, parent_tag)
        +refresh (self)
        +temp_to_color (self, temp)
        +setup_disc_geometry (self)
        +generate_disc_texture (self, temperatures)
    }
    
    Runtime --> HomePage : creates
    Runtime --> DataManager : creates
    Runtime --> RenderManager : creates

    DataManager --> DataSet : creates
    
    HomePage --> BrakeTempView : creates
    HomePage --> OilStarvationView : creates
    HomePage --> DataFilesView : creates
    HomePage --> DataManager : uses

    BrakeTempView --> DataManager : uses
    OilStarvationView --> DataManager : uses
    DataFilesView --> DataManager : uses

```
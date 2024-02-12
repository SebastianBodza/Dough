import json
import time
import streamlit as st
from typing import List
from shared.constants import AnimationStyleType, AnimationToolType
from ui_components.constants import DEFAULT_SHOT_MOTION_VALUES, DefaultProjectSettingParams, ShotMetaData
from ui_components.methods.video_methods import create_single_interpolated_clip
from utils.data_repo.data_repo import DataRepo
from utils.ml_processor.motion_module import AnimateDiffCheckpoint
from ui_components.models import InternalFrameTimingObject, InternalShotObject
from utils import st_memory
import numpy as np
import matplotlib.pyplot as plt

def animation_style_element(shot_uuid):
    disable_generate = False
    help = ""
    motion_modules = AnimateDiffCheckpoint.get_name_list()
    variant_count = 1
    current_animation_style = AnimationStyleType.CREATIVE_INTERPOLATION.value    # setting a default value
    data_repo = DataRepo()
    
    shot: InternalShotObject = data_repo.get_shot_from_uuid(st.session_state["shot_uuid"])
    st.session_state['project_uuid'] = str(shot.project.uuid)
    timing_list: List[InternalFrameTimingObject] = shot.timing_list
    buffer = 4
    

    settings = {
        'animation_tool': AnimationToolType.ANIMATEDIFF.value,
    }

    interpolation_style = 'ease-in-out'
    
    advanced1, advanced2, advanced3 = st.columns([0.5,1.5, 0.5])
    with advanced1:
        st.markdown("#### Animation Settings")


    with advanced3:
        with st.expander("Bulk edit"):
            what_would_you_like_to_edit = st.selectbox("What would you like to edit?", options=["Distance to next frames", "Speed of transitions", "Freedom between frames","Strength of frames",  "Motion during frames"], key="what_would_you_like_to_edit")
            if what_would_you_like_to_edit == "Distance to next frames":
                what_to_change_it_to = st.slider("What would you like to change it to?", min_value=4, max_value=96, step=4, value=16, key="what_to_change_it_to")
            if what_would_you_like_to_edit == "Strength of frames":
                what_to_change_it_to = st.slider("What would you like to change it to?", min_value=0.25, max_value=1.0, step=0.01, value=0.5, key="what_to_change_it_to")
            elif what_would_you_like_to_edit == "Speed of transitions":
                what_to_change_it_to = st.slider("What would you like to change it to?", min_value=0.45, max_value=0.7, step=0.01, value=0.6, key="what_to_change_it_to")
            elif what_would_you_like_to_edit == "Freedom between frames":
                what_to_change_it_to = st.slider("What would you like to change it to?", min_value=0.2, max_value=0.95, step=0.01, value=0.5, key="what_to_change_it_to")
            elif what_would_you_like_to_edit == "Motion during frames":
                what_to_change_it_to = st.slider("What would you like to change it to?", min_value=0.2, max_value=0.95, step=0.01, value=0.5, key="what_to_change_it_to")
            
            if st.button("Bulk edit", key="bulk_edit"):
                if what_would_you_like_to_edit == "Strength of frames":
                    for idx, timing in enumerate(timing_list):
                        st.session_state[f'strength_of_frame_{shot.uuid}_{idx}'] = what_to_change_it_to
                elif what_would_you_like_to_edit == "Distance to next frames":
                    for idx, timing in enumerate(timing_list):
                        st.session_state[f'distance_to_next_frame_{shot.uuid}_{idx}'] = what_to_change_it_to
                elif what_would_you_like_to_edit == "Speed of transitions":
                    for idx, timing in enumerate(timing_list):
                        st.session_state[f'speed_of_transition_{shot.uuid}_{idx}'] = what_to_change_it_to
                elif what_would_you_like_to_edit == "Freedom between frames":
                    for idx, timing in enumerate(timing_list):
                        st.session_state[f'freedom_between_frames_{shot.uuid}_{idx}'] = what_to_change_it_to
                elif what_would_you_like_to_edit == "Motion during frames":
                    for idx, timing in enumerate(timing_list):
                        st.session_state[f'motion_during_frame_{shot.uuid}_{idx}'] = what_to_change_it_to
    
    st.markdown("***")
    type_of_setting = "Individual"
    if type_of_setting == "Individual":        
        items_per_row = 3
        strength_of_frames = []
        distances_to_next_frames = []
        speeds_of_transitions = []
        freedoms_between_frames = []
        individual_prompts = []
        individual_negative_prompts =[]
        motions_during_frames = []

        for i in range(0, len(timing_list) , items_per_row):
            with st.container():
                grid = st.columns([2 if j%2==0 else 1 for j in range(2*items_per_row)])  # Adjust the column widths
                for j in range(items_per_row):                    
                    idx = i + j
                    if idx < len(timing_list):                        
                        with grid[2*j]:  # Adjust the index for image column
                            timing = timing_list[idx]
                            if timing.primary_image and timing.primary_image.location:
                                st.info(f"**Frame {idx + 1}**")
                                st.image(timing.primary_image.location, use_column_width=True)
                                
                                motion_data = DEFAULT_SHOT_MOTION_VALUES
                                # setting default parameters (fetching data from the shot if it's present)
                                if f'strength_of_frame_{shot.uuid}_{idx}' not in st.session_state:
                                    shot_meta_data = shot.meta_data_dict.get(ShotMetaData.MOTION_DATA.value, json.dumps({}))
                                    timing_data = json.loads(shot_meta_data).get("timing_data", [])
                                    if timing_data and len(timing_data) >= idx + 1:
                                        motion_data = timing_data[idx]

                                    for k, v in motion_data.items():
                                        st.session_state[f'{k}_{shot.uuid}_{idx}'] = v
                                                                                                                           
                                # settings control
                                with st.expander("Advanced settings:"):
                                    strength_of_frame = st.slider("Strength of current frame:", min_value=0.25, max_value=1.0, step=0.01, key=f"strength_of_frame_widget_{shot.uuid}_{idx}", value=st.session_state[f'strength_of_frame_{shot.uuid}_{idx}'])
                                    strength_of_frames.append(strength_of_frame)                                    
                                    individual_prompt = st.text_input("What to include:", key=f"individual_prompt_widget_{idx}_{timing.uuid}", value=st.session_state[f'individual_prompt_{shot.uuid}_{idx}'], help="Use this sparingly, as it can have a large impact on the video and cause weird distortions.")
                                    individual_prompts.append(individual_prompt)
                                    individual_negative_prompt = st.text_input("What to avoid:", key=f"negative_prompt_widget_{idx}_{timing.uuid}", value=st.session_state[f'individual_negative_prompt_{shot.uuid}_{idx}'],help="Use this sparingly, as it can have a large impact on the video and cause weird distortions.")
                                    individual_negative_prompts.append(individual_negative_prompt)
                                    motion_during_frame = st.slider("Motion during frame:", min_value=0.2, max_value=0.95, step=0.01, key=f"motion_during_frame_widget_{idx}_{timing.uuid}", value=st.session_state[f'motion_during_frame_{shot.uuid}_{idx}'])
                                    motions_during_frames.append(motion_during_frame)
                            else:                        
                                st.warning("No primary image present.")    

                        # distance, speed and freedom settings (also aggregates them into arrays)
                        with grid[2*j+1]:  # Add the new column after the image column
                            if idx < len(timing_list) - 1:                                                                       
                                st.write("")
                                st.write("")
                                st.write("")
                                st.write("")                   
                                distance_to_next_frame = st.slider("Distance to next frame:", min_value=4, max_value=96, step=4, key=f"distance_to_next_frame_widget_{idx}_{timing.uuid}", value=st.session_state[f'distance_to_next_frame_{shot.uuid}_{idx}'])
                                distances_to_next_frames.append(distance_to_next_frame)                                                                                                              
                                speed_of_transition = st.slider("Speed of transition:", min_value=0.45, max_value=0.7, step=0.01, key=f"speed_of_transition_widget_{idx}_{timing.uuid}", value=st.session_state[f'speed_of_transition_{shot.uuid}_{idx}'])
                                speeds_of_transitions.append(speed_of_transition)                                      
                                freedom_between_frames = st.slider("Freedom between frames:", min_value=0.2, max_value=0.95, step=0.01, key=f"freedom_between_frames_widget_{idx}_{timing.uuid}", value=st.session_state[f'freedom_between_frames_{shot.uuid}_{idx}'])
                                freedoms_between_frames.append(freedom_between_frames)
                                               
                if (i < len(timing_list) - 1)  or (len(timing_list) % items_per_row != 0):
                    st.markdown("***")
        
        with advanced1:
            if st.button("Save current settings", key="save_current_settings"):
                update_session_state_with_animation_details(shot.uuid, timing_list, strength_of_frames, distances_to_next_frames, speeds_of_transitions, freedoms_between_frames, motions_during_frames, individual_prompts, individual_negative_prompts)
                st.success("Settings saved successfully.")
                time.sleep(0.7)
                st.rerun()

        def transform_data(strength_of_frames, movements_between_frames, speeds_of_transitions, distances_to_next_frames):
            def adjust_and_invert_relative_value(middle_value, relative_value):
                if relative_value is not None:
                    adjusted_value = middle_value * relative_value
                    return round(middle_value - adjusted_value, 2)
                return None

            def invert_value(value):
                return round(1.0 - value, 2) if value is not None else None

            # Creating output_strength with relative and inverted start and end values
            output_strength = []
            for i, strength in enumerate(strength_of_frames):
                start_value = None if i == 0 else movements_between_frames[i - 1]
                end_value = None if i == len(strength_of_frames) - 1 else movements_between_frames[i]

                # Adjusting and inverting start and end values relative to the middle value
                adjusted_start = adjust_and_invert_relative_value(strength, start_value)
                adjusted_end = adjust_and_invert_relative_value(strength, end_value)

                output_strength.append((adjusted_start, strength, adjusted_end))

            # Creating output_speeds with inverted values
            output_speeds = [(None, None) for _ in range(len(speeds_of_transitions) + 1)]
            for i in range(len(speeds_of_transitions)):
                current_tuple = list(output_speeds[i])
                next_tuple = list(output_speeds[i + 1])

                inverted_speed = invert_value(speeds_of_transitions[i])
                current_tuple[1] = inverted_speed * 2
                next_tuple[0] = inverted_speed * 2

                output_speeds[i] = tuple(current_tuple)
                output_speeds[i + 1] = tuple(next_tuple)

            # Creating cumulative_distances
            cumulative_distances = [0]
            for distance in distances_to_next_frames:
                cumulative_distances.append(cumulative_distances[-1] + distance)
                                                
            return output_strength, output_speeds, cumulative_distances
        
        dynamic_strength_values, dynamic_key_frame_influence_values, dynamic_frame_distribution_values = transform_data(strength_of_frames, freedoms_between_frames, speeds_of_transitions, distances_to_next_frames)
        type_of_frame_distribution = "dynamic"
        type_of_key_frame_influence = "dynamic"
        type_of_strength_distribution = "dynamic"
        linear_frame_distribution_value = 16
        linear_key_frame_influence_value = 1.0
        linear_cn_strength_value = 1.0
        with advanced2:
            with st.expander("Visualise motion data"):
                if st.button("Visualise motion data"):
                    columns = st.columns(max(7, len(timing_list))) 
                    for idx, timing in enumerate(timing_list):

                        markdown_text = f'##### **Frame {idx + 1}** ___'

                        with columns[idx]:
                            st.markdown(markdown_text)

                    keyframe_positions = get_keyframe_positions(type_of_frame_distribution, dynamic_frame_distribution_values, timing_list, linear_frame_distribution_value)
                    keyframe_positions = [position + 4 - 1 for position in keyframe_positions]
                    keyframe_positions.insert(0, 0)

                    last_key_frame_position = (keyframe_positions[-1] + 1)
                    strength_values = extract_strength_values(type_of_strength_distribution, dynamic_strength_values, keyframe_positions, linear_cn_strength_value)
                    key_frame_influence_values = extract_influence_values(type_of_key_frame_influence, dynamic_key_frame_influence_values, keyframe_positions, linear_key_frame_influence_value)                                        
                    # calculate_weights(keyframe_positions, strength_values, buffer, key_frame_influence_values):
                    weights_list, frame_numbers_list = calculate_weights(keyframe_positions, strength_values, 4, key_frame_influence_values,last_key_frame_position)            
                    plot_weights(weights_list, frame_numbers_list)
                    '''
                    st.write(f"distribution: {str(dynamic_frame_distribution_values)[1:-1]}")
                    st.write(f"influence: {str(dynamic_key_frame_influence_values)[1:-1]}")
                    st.write(f"strength: {str(dynamic_strength_values)[1:-1]}")

                    formatted_individual_prompts = format_frame_prompts_with_buffer(dynamic_frame_distribution_values, individual_prompts, buffer)
                    st.write(f"prompts: {formatted_individual_prompts}")
                    formatted_negative_prompts = format_frame_prompts_with_buffer(dynamic_frame_distribution_values, individual_negative_prompts, buffer)
                    st.write(f"negative prompts: {formatted_negative_prompts}")
                    '''

            # drop all the first values in each list
            # keyframe_positions = keyframe_positions[1:]
            # strength_values = strength_values[1:]
            #key_frame_influence_values = key_frame_influence_values[1:]

            # shirt all the keyframe values back by 4
            # keyframe_positions = [position - 3 for position in keyframe_positions]

            # make keyframe into a plain list
            
            # st.write(keyframe_positions)
            # st.write(strength_values)
            # st.write(key_frame_influence_values)

    elif type_of_setting == "Bulk":
        st.session_state['frame_position'] = 0
        type_of_frame_distribution = "linear"
        type_of_key_frame_influence = "linear"
        type_of_strength_distribution = "linear"
        columns = st.columns(max(7, len(timing_list))) 
        disable_generate = False
        help = ""            
        dynamic_frame_distribution_values = []
        dynamic_key_frame_influence_values = []
        dynamic_strength_values = []         


        for idx, timing in enumerate(timing_list):
            # Use modulus to cycle through colors
            # color = color_names[idx % len(color_names)]
            # Only create markdown text for the current index
            markdown_text = f'##### **Frame {idx + 1}** ___'

            with columns[idx]:
                st.markdown(markdown_text)

            if timing.primary_image and timing.primary_image.location:                
                columns[idx].image(timing.primary_image.location, use_column_width=True)
                b = timing.primary_image.inference_params     
        d1, d2 = st.columns([1, 5])           
        with d1:          

            linear_frame_distribution_value = st_memory.number_input("Frames per key frame:", min_value=8, max_value=36, value=16, step=1, key="linear_frame_distribution_value")
            linear_key_frame_influence_value = st_memory.number_input("Length of key frame influence:", min_value=0.1, max_value=5.0, value=0.75, step=0.01, key="linear_key_frame_influence_value")
            strength1, strength2 = st.columns([1, 1])
            with strength1:
                bottom_of_strength_range = st_memory.number_input("Bottom of strength range:", min_value=0.0, max_value=1.0, value=0.35, step=0.01, key="bottom_of_strength_range")
            with strength2:
                top_of_strength_range = st_memory.number_input("Top of strength range:", min_value=0.0, max_value=1.0, value=0.5, step=0.01, key="top_of_strength_range")
            
            linear_cn_strength_value = (bottom_of_strength_range, top_of_strength_range)
                                            
            footer1, _ = st.columns([2, 1])
            with footer1:
                interpolation_style = 'ease-in-out'
                                        
            if st.button("Reset to default settings", key="reset_animation_style"):
                update_interpolation_settings(timing_list=timing_list)
                st.rerun()
        with d2:
            columns = st.columns(max(7, len(timing_list))) 
            disable_generate = False
            help = ""            
                                                                                                    
            keyframe_positions = get_keyframe_positions(type_of_frame_distribution, dynamic_frame_distribution_values, timing_list, linear_frame_distribution_value)
            keyframe_positions = [position + 4 - 1 for position in keyframe_positions]
            keyframe_positions.insert(0, 0)

            last_key_frame_position = (keyframe_positions[-1] + 1)
            strength_values = extract_strength_values(type_of_strength_distribution, dynamic_strength_values, keyframe_positions, linear_cn_strength_value)                        
            key_frame_influence_values = extract_influence_values(type_of_key_frame_influence, dynamic_key_frame_influence_values, keyframe_positions, linear_key_frame_influence_value)                                        
            # calculate_weights(keyframe_positions, strength_values, buffer, key_frame_influence_values):
            weights_list, frame_numbers_list = calculate_weights(keyframe_positions, strength_values, 4, key_frame_influence_values,last_key_frame_position)            
            plot_weights(weights_list, frame_numbers_list)

    st.markdown("***")
    st.markdown("#### Overall style settings")
    e1, e2, e3 = st.columns([1, 1,1])

    with e1:
        strength_of_adherence = st_memory.slider("How much would you like to force adherence to the input images?", min_value=0.0, max_value=1.0, value=0.3, step=0.01, key="stregnth_of_adherence")
        base_end_percent = 0.05
        base_adapter_strength = 0.05
        
        # 0.1 value = 1x multipler, 0.2 = 2x multipler, 0.3 = 3x multipler, 0.4 = 4x multipler, 0.5 = 5x multipler
        multipled_base_end_percent = base_end_percent * (strength_of_adherence * 10)
        multipled_base_adapter_strength = base_adapter_strength * (strength_of_adherence * 20)

        # st.write(f"multiplied base end percent: {multipled_base_end_percent}")
        # st.write(f"multiplied base adapter strength: {multipled_base_adapter_strength}")

        sd_model_list = [
            "Realistic_Vision_V5.1.safetensors",
            "counterfeitV30_v30.safetensors",
            "epicrealism_pureEvolutionV5.safetensors",
            "dreamshaper_8.safetensors"
        ]

        # remove .safe tensors from the end of each model name
        # motion_scale = st_memory.slider("Motion scale:", min_value=0.0, max_value=2.0, value=1.3, step=0.01, key="motion_scale")
        motion_scale = 1.3
        sd_model = st_memory.selectbox("Which model would you like to use?", options=sd_model_list, key="sd_model_video")
    with e2:
        st.info("Higher values may cause flickering and sudden changes in the video. Lower values may cause the video to be less influenced by the input images but can also fix colouring issues.")

    f1, f2, f3 = st.columns([1, 1, 1])
    
    with f1:
        positive_prompt = st_memory.text_area("What would you like to see in the videos?", value="", key="positive_prompt_video")
    with f2:
        negative_prompt = st_memory.text_area("What would you like to avoid in the videos?", value="bad image, worst quality", key="negative_prompt_video")
    
    with f3:
        st.write("")
        st.write("")
        st.info("Use these sparingly, as they can have a large impact on the video. You can also edit them for individual frames in the advanced settings above.")
        soft_scaled_cn_weights_multiplier = ""

        # relative_ipadapter_strength = st_memory.slider("How much would you like to influence the style?", min_value=0.0, max_value=5.0, value=1.1, step=0.1, key="ip_adapter_strength")
        # relative_ipadapter_influence = st_memory.slider("For how long would you like to influence the style?", min_value=0.0, max_value=5.0, value=1.1, step=0.1, key="ip_adapter_influence")
        # soft_scaled_cn_weights_multipler = st_memory.slider("How much would you like to scale the CN weights?", min_value=0.0, max_value=10.0, value=0.85, step=0.1, key="soft_scaled_cn_weights_multiple_video")
        # append_to_prompt = st_memory.text_input("What would you like to append to the prompts?", key="append_to_prompt")


    st.markdown("***")
    st.markdown("#### Overall motion settings")
    h1, h2, h3 = st.columns([0.5, 1.5, 1])
    with h1:
        type_of_motion_context = st_memory.radio("Type of motion context:", options=["Low", "Standard", "High"], key="type_of_motion_context", horizontal=False, index=1)
    with h2: 
        st.info("This is how much the motion will be informed by the previous and next frames. High means the motion will be very influenced by the previous and next frames - this can make it smoother but increase artifacts - while lower values make the motion less smooth but removes artifacts. Naturally, we recommend Standard.")

    if type_of_motion_context == "Low":
        context_length = 16
        context_stride = 1
        context_overlap = 2

    elif type_of_motion_context == "Standard":
        context_length = 16
        context_stride = 2
        context_overlap = 4
    
    elif type_of_motion_context == "High":
        context_length = 16
        context_stride = 4
        context_overlap = 4

    normalise_speed = True

    relative_ipadapter_strength = 1.0
    relative_ipadapter_influence = 0.0
    
    project_settings = data_repo.get_project_setting(shot.project.uuid)
    width = project_settings.width
    height = project_settings.height
    img_dimension = f"{width}x{height}"

    settings.update(
        ckpt=sd_model,
        buffer=4,
        motion_scale=motion_scale,
        image_dimension=img_dimension,
        output_format="video/h264-mp4",
        negative_prompt=negative_prompt,
        interpolation_type=interpolation_style,
        stmfnet_multiplier=2,
        relative_ipadapter_strength=relative_ipadapter_strength,
        relative_ipadapter_influence=relative_ipadapter_influence,        
        type_of_cn_strength_distribution=type_of_strength_distribution,
        linear_cn_strength_value=str(linear_cn_strength_value),
        dynamic_strength_values=str(dynamic_strength_values),
        type_of_frame_distribution=type_of_frame_distribution,
        linear_frame_distribution_value=linear_frame_distribution_value,
        dynamic_frame_distribution_values=dynamic_frame_distribution_values,
        type_of_key_frame_influence=type_of_key_frame_influence,
        linear_key_frame_influence_value=float(linear_key_frame_influence_value),
        dynamic_key_frame_influence_values=dynamic_key_frame_influence_values,
        normalise_speed=normalise_speed,
        animation_style=AnimationStyleType.CREATIVE_INTERPOLATION.value
    )
    
    st.markdown("***")
    st.markdown("#### Generation Settings")
    animate_col_1, animate_col_2, _ = st.columns([1, 1, 2])
    with animate_col_1:
        variant_count = st.number_input("How many variants?", min_value=1, max_value=5, value=1, step=1, key="variant_count")
        '''
        st.download_button(
                label="Download images",
                data=prepare_workflow_images(shot_uuid),
                file_name='data.zip'
            )
        '''
        
        if st.button("Generate Animation Clip", key="generate_animation_clip", disabled=disable_generate, help=help):
            update_session_state_with_animation_details(shot.uuid, timing_list, strength_of_frames, distances_to_next_frames, speeds_of_transitions, freedoms_between_frames, motions_during_frames, individual_prompts, individual_negative_prompts)
            vid_quality = "full"    # TODO: add this if video_resolution == "Full Resolution" else "preview"
            st.success("Generating clip - see status in the Generation Log in the sidebar. Press 'Refresh log' to update.")

            positive_prompt = ""
            append_to_prompt = ""       # TODO: add this
            for idx, timing in enumerate(timing_list):
                if timing.primary_image and timing.primary_image.location:
                    b = timing.primary_image.inference_params
                    prompt = b['prompt'] if b else ""
                    prompt += append_to_prompt
                    frame_prompt = f"{idx * linear_frame_distribution_value}_" + prompt
                    positive_prompt += ":" + frame_prompt if positive_prompt else frame_prompt
                else:
                    st.error("Please generate primary images")
                    time.sleep(0.7)
                    st.rerun()

            settings.update(
                image_prompt_list=positive_prompt,
                animation_stype=current_animation_style,
            )

            create_single_interpolated_clip(
                shot_uuid,
                vid_quality,
                settings,
                variant_count
            )
            st.rerun()

    with animate_col_2:
            number_of_frames = len(timing_list)
            if height==width:
                cost_per_key_frame = 0.035
            else:
                cost_per_key_frame = 0.045

            cost_per_generation = cost_per_key_frame * number_of_frames * variant_count
            st.info(f"Generating a video with {number_of_frames} frames in the cloud will cost c. ${cost_per_generation:.2f} USD.")
    
def update_session_state_with_animation_details(shot_uuid, timing_list, strength_of_frames, distances_to_next_frames, speeds_of_transitions, freedoms_between_frames, motions_during_frames, individual_prompts, individual_negative_prompts):
    data_repo = DataRepo()
    shot = data_repo.get_shot_from_uuid(shot_uuid)
    meta_data = shot.meta_data_dict
    timing_data = []
    for idx, timing in enumerate(timing_list):
        if idx < len(timing_list):
            st.session_state[f'strength_of_frame_{shot_uuid}_{idx}'] = strength_of_frames[idx]
            st.session_state[f'individual_prompt_{shot_uuid}_{idx}'] = individual_prompts[idx]
            st.session_state[f'individual_negative_prompt_{shot_uuid}_{idx}'] = individual_negative_prompts[idx]
            st.session_state[f'motion_during_frame_{shot_uuid}_{idx}'] = motions_during_frames[idx]
            if idx < len(timing_list) - 1:                             
                st.session_state[f'distance_to_next_frame_{shot_uuid}_{idx}'] = distances_to_next_frames[idx]
                st.session_state[f'speed_of_transition_{shot_uuid}_{idx}'] = speeds_of_transitions[idx]
                st.session_state[f'freedom_between_frames_{shot_uuid}_{idx}'] = freedoms_between_frames[idx]

        # adding into the meta-data
        state_data = {
            "strength_of_frame" : strength_of_frames[idx],
            "individual_prompt" : individual_prompts[idx],
            "individual_negative_prompt" : individual_negative_prompts[idx],
            "motion_during_frame" : motions_during_frames[idx],
            "distance_to_next_frame" : distances_to_next_frames[idx] if idx < len(timing_list) - 1 else DEFAULT_SHOT_MOTION_VALUES["distance_to_next_frame"],
            "speed_of_transition" : speeds_of_transitions[idx] if idx < len(timing_list) - 1 else DEFAULT_SHOT_MOTION_VALUES["speed_of_transition"],
            "freedom_between_frames" : freedoms_between_frames[idx] if idx < len(timing_list) - 1 else DEFAULT_SHOT_MOTION_VALUES["freedom_between_frames"],
        }

        timing_data.append(state_data)

    meta_data.update({ShotMetaData.MOTION_DATA.value : json.dumps({"timing_data": timing_data})})
    data_repo.update_shot(**{"uuid": shot_uuid, "meta_data": json.dumps(meta_data)})

def prepare_workflow_json(shot_uuid, settings):
    data_repo = DataRepo()
    shot = data_repo.get_shot_from_uuid(shot_uuid)

    positive_prompt = ""
    for idx, timing in enumerate(shot.timing_list):
        b = None
        if timing.primary_image and timing.primary_image.location:
            b = timing.primary_image.inference_params
        prompt = b['prompt'] if b else ""
        frame_prompt = f'"{idx * settings["linear_frame_distribution_value"]}":"{prompt}"' + ("," if idx != len(shot.timing_list) - 1 else "")
        positive_prompt +=  frame_prompt

    settings['image_prompt_list'] = positive_prompt
    workflow_data = create_workflow_json(shot.timing_list, settings)

    return workflow_data

def format_frame_prompts_with_buffer(frame_numbers, individual_prompts, buffer):

    adjusted_frame_numbers = [frame + buffer for frame in frame_numbers]
    
    # Format the adjusted frame numbers and prompts
    formatted = ', '.join(f'"{frame}": "{prompt}"' for frame, prompt in zip(adjusted_frame_numbers, individual_prompts))
    return formatted



def prepare_workflow_images(shot_uuid):
    import requests
    import io
    import zipfile

    data_repo = DataRepo()
    shot = data_repo.get_shot_from_uuid(shot_uuid)
    image_locations = [t.primary_image.location if t.primary_image else None for t in shot.timing_list]

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for idx, image_location in enumerate(image_locations):
            if not image_location:
                continue

            image_name = f"{idx}.png"
            if image_location.startswith('http'):
                response = requests.get(image_location)
                image_data = response.content
                zip_file.writestr(image_name, image_data)
            else:
                zip_file.write(image_location, image_name)

    buffer.seek(0)
    return buffer.getvalue()

def extract_strength_values(type_of_key_frame_influence, dynamic_key_frame_influence_values, keyframe_positions, linear_key_frame_influence_value):

    if type_of_key_frame_influence == "dynamic":
        # Process the dynamic_key_frame_influence_values depending on its format
        if isinstance(dynamic_key_frame_influence_values, str):
            dynamic_values = eval(dynamic_key_frame_influence_values)
        else:
            dynamic_values = dynamic_key_frame_influence_values

        # Iterate through the dynamic values and convert tuples with two values to three values
        dynamic_values_corrected = []
        for value in dynamic_values:
            if len(value) == 2:
                value = (value[0], value[1], value[0])
            dynamic_values_corrected.append(value)

        return dynamic_values_corrected
    else:
        # Process for linear or other types
        if len(linear_key_frame_influence_value) == 2:
            linear_key_frame_influence_value = (linear_key_frame_influence_value[0], linear_key_frame_influence_value[1], linear_key_frame_influence_value[0])
        return [linear_key_frame_influence_value for _ in range(len(keyframe_positions) - 1)]

def create_workflow_json(image_locations, settings):
    import os

    # get the current working directory
    current_working_directory = os.getcwd()

    # print output to the console
    print(current_working_directory)

    with open('./sample_assets/interpolation_workflow.json', 'r') as json_file:
        json_data = json.load(json_file)

    image_prompt_list = settings['image_prompt_list']
    negative_prompt = settings['negative_prompt']
    type_of_frame_distribution = settings['type_of_frame_distribution']
    linear_frame_distribution_value = settings['linear_frame_distribution_value']
    dynamic_frame_distribution_values = settings['dynamic_frame_distribution_values']
    type_of_key_frame_influence = settings['type_of_key_frame_influence']
    linear_key_frame_influence_value = settings['linear_key_frame_influence_value']
    dynamic_key_frame_influence_values = settings['dynamic_key_frame_influence_values']
    type_of_cn_strength_distribution=settings['type_of_cn_strength_distribution']
    linear_cn_strength_value=settings['linear_cn_strength_value']
    buffer = settings['buffer']
    dynamic_strength_values = settings['dynamic_strength_values']
    interpolation_type = settings['interpolation_type']
    ckpt = settings['ckpt']
    motion_scale = settings['motion_scale']    
    relative_ipadapter_strength = settings['relative_ipadapter_strength']
    relative_ipadapter_influence = settings['relative_ipadapter_influence']
    image_dimension = settings['image_dimension']
    output_format = settings['output_format']
    # soft_scaled_cn_weights_multiplier = settings['soft_scaled_cn_weights_multiplier']
    stmfnet_multiplier = settings['stmfnet_multiplier']

    if settings['type_of_frame_distribution'] == 'linear':
        batch_size = (len(image_locations) - 1) * settings['linear_frame_distribution_value'] + int(buffer)
    else:
        batch_size = int(settings['dynamic_frame_distribution_values'].split(',')[-1]) + int(buffer)

    img_width, img_height = image_dimension.split("x")

    for node in json_data['nodes']:
        if node['id'] == 189:
            node['widgets_values'][-3] = int(img_width)
            node['widgets_values'][-2] = int(img_height)
            node['widgets_values'][0] = ckpt
            node['widgets_values'][-1] = batch_size

        elif node['id'] == 187:
            node['widgets_values'][-2] = motion_scale

        elif node['id'] == 347:
            node['widgets_values'][0] = image_prompt_list

        elif node['id'] == 352:
            node['widgets_values'] = [negative_prompt]

        elif node['id'] == 365:
            node['widgets_values'][1] = type_of_frame_distribution
            node['widgets_values'][2] = linear_frame_distribution_value
            node['widgets_values'][3] = dynamic_frame_distribution_values
            node['widgets_values'][4] = type_of_key_frame_influence
            node['widgets_values'][5] = linear_key_frame_influence_value
            node['widgets_values'][6] = dynamic_key_frame_influence_values
            node['widgets_values'][7] = type_of_cn_strength_distribution
            node['widgets_values'][8] = linear_cn_strength_value
            node['widgets_values'][9] = dynamic_strength_values
            node['widgets_values'][-1] = buffer
            node['widgets_values'][-2] = interpolation_type
            node['widgets_values'][-3] = soft_scaled_cn_weights_multiplier

        elif node['id'] == 292:
            node['widgets_values'][-2] = stmfnet_multiplier

        elif node['id'] == 301:
            node['widgets_values'] = [ip_adapter_model_weight]

        elif node['id'] == 281:
            # Special case: 'widgets_values' is a dictionary for this node
            node['widgets_values']['output_format'] = output_format
        
        # st.write(json_data)
    
    return json_data
            

def update_interpolation_settings(values=None, timing_list=None):
    default_values = {
        'type_of_frame_distribution': 0,
        'frames_per_keyframe': 16,
        'type_of_key_frame_influence': 0,
        'length_of_key_frame_influence': 1.0,
        'type_of_cn_strength_distribution': 0,
        'linear_cn_strength_value': (0.0,0.7),
        'linear_frame_distribution_value': 16,
        'linear_key_frame_influence_value': 1.0,
        'interpolation_style': 0,
        'motion_scale': 1.0,            
        'negative_prompt_video': 'bad image, worst quality',        
        'ip_adapter_strength': 1.0,
        'ip_adapter_influence': 1.0,
        'soft_scaled_cn_weights_multiple_video': 0.85
    }

    for idx in range(0, len(timing_list)):
        default_values[f'dynamic_frame_distribution_values_{idx}'] = (idx) * 16
        default_values[f'dynamic_key_frame_influence_values_{idx}'] = 1.0
        default_values[f'dynamic_strength_values_{idx}'] = (0.0,0.7)

    for key, default_value in default_values.items():
        st.session_state[key] = values.get(key, default_value) if values and values.get(key) is not None else default_value
        # print(f"{key}: {st.session_state[key]}")


def calculate_dynamic_influence_ranges(keyframe_positions, key_frame_influence_values, allow_extension=True):
    if len(keyframe_positions) < 2 or len(keyframe_positions) != len(key_frame_influence_values):
        return []

    influence_ranges = []
    for i, position in enumerate(keyframe_positions):
        influence_factor = key_frame_influence_values[i]
        range_size = influence_factor * (keyframe_positions[-1] - keyframe_positions[0]) / (len(keyframe_positions) - 1) / 2

        start_influence = position - range_size
        end_influence = position + range_size

        # If extension beyond the adjacent keyframe is allowed, do not constrain the start and end influence.
        if not allow_extension:
            start_influence = max(start_influence, keyframe_positions[i - 1] if i > 0 else 0)
            end_influence = min(end_influence, keyframe_positions[i + 1] if i < len(keyframe_positions) - 1 else keyframe_positions[-1])

        influence_ranges.append((round(start_influence), round(end_influence)))

    return influence_ranges
        
def extract_influence_values(type_of_key_frame_influence, dynamic_key_frame_influence_values, keyframe_positions, linear_key_frame_influence_value):
    # Check and convert linear_key_frame_influence_value if it's a float or string float        
    # if it's a string that starts with a parenthesis, convert it to a tuple
    if isinstance(linear_key_frame_influence_value, str) and linear_key_frame_influence_value[0] == "(":
        linear_key_frame_influence_value = eval(linear_key_frame_influence_value)


    if not isinstance(linear_key_frame_influence_value, tuple):
        if isinstance(linear_key_frame_influence_value, (float, str)):
            try:
                value = float(linear_key_frame_influence_value)
                linear_key_frame_influence_value = (value, value)
            except ValueError:
                raise ValueError("linear_key_frame_influence_value must be a float or a string representing a float")

    number_of_outputs = len(keyframe_positions) - 1

    if type_of_key_frame_influence == "dynamic":
        # Convert list of individual float values into tuples
        if all(isinstance(x, float) for x in dynamic_key_frame_influence_values):
            dynamic_values = [(value, value) for value in dynamic_key_frame_influence_values]
        elif isinstance(dynamic_key_frame_influence_values[0], str) and dynamic_key_frame_influence_values[0] == "(":
            string_representation = ''.join(dynamic_key_frame_influence_values)
            dynamic_values = eval(f'[{string_representation}]')
        else:
            dynamic_values = dynamic_key_frame_influence_values if isinstance(dynamic_key_frame_influence_values, list) else [dynamic_key_frame_influence_values]
        return dynamic_values[:number_of_outputs]
    else:
        return [linear_key_frame_influence_value for _ in range(number_of_outputs)]


def get_keyframe_positions(type_of_frame_distribution, dynamic_frame_distribution_values, images, linear_frame_distribution_value):
    if type_of_frame_distribution == "dynamic":
        # Check if the input is a string or a list
        if isinstance(dynamic_frame_distribution_values, str):
            # Sort the keyframe positions in numerical order
            return sorted([int(kf.strip()) for kf in dynamic_frame_distribution_values.split(',')])
        elif isinstance(dynamic_frame_distribution_values, list):
            return sorted(dynamic_frame_distribution_values)
    else:
        # Calculate the number of keyframes based on the total duration and linear_frames_per_keyframe
        return [i * linear_frame_distribution_value for i in range(len(images))]

def extract_keyframe_values(type_of_key_frame_influence, dynamic_key_frame_influence_values, keyframe_positions, linear_key_frame_influence_value):
    if type_of_key_frame_influence == "dynamic":
        return [float(influence.strip()) for influence in dynamic_key_frame_influence_values.split(',')]
    else:
        return [linear_key_frame_influence_value for _ in keyframe_positions]

def extract_start_and_endpoint_values(type_of_key_frame_influence, dynamic_key_frame_influence_values, keyframe_positions, linear_key_frame_influence_value):
    if type_of_key_frame_influence == "dynamic":
        # If dynamic_key_frame_influence_values is a list of characters representing tuples, process it
        if isinstance(dynamic_key_frame_influence_values[0], str) and dynamic_key_frame_influence_values[0] == "(":
            # Join the characters to form a single string and evaluate to convert into a list of tuples
            string_representation = ''.join(dynamic_key_frame_influence_values)
            dynamic_values = eval(f'[{string_representation}]')
        else:
            # If it's already a list of tuples or a single tuple, use it directly
            dynamic_values = dynamic_key_frame_influence_values if isinstance(dynamic_key_frame_influence_values, list) else [dynamic_key_frame_influence_values]
        return dynamic_values
    else:
        # Return a list of tuples with the linear_key_frame_influence_value as a tuple repeated for each position
        return [linear_key_frame_influence_value for _ in keyframe_positions]

def calculate_weights(keyframe_positions, strength_values, buffer, key_frame_influence_values,last_key_frame_position):

    def calculate_influence_frame_number(key_frame_position, next_key_frame_position, distance):
        # Calculate the absolute distance between key frames
        key_frame_distance = abs(next_key_frame_position - key_frame_position)
        
        # Apply the distance multiplier
        extended_distance = key_frame_distance * distance

        # Determine the direction of influence based on the positions of the key frames
        if key_frame_position < next_key_frame_position:
            # Normal case: influence extends forward
            influence_frame_number = key_frame_position + extended_distance
        else:
            # Reverse case: influence extends backward
            influence_frame_number = key_frame_position - extended_distance
        
        # Return the result rounded to the nearest integer
        return round(influence_frame_number)

    def find_curve(batch_index_from, batch_index_to, strength_from, strength_to, interpolation,revert_direction_at_midpoint, last_key_frame_position,i, number_of_items,buffer):

        # Initialize variables based on the position of the keyframe
        range_start = batch_index_from
        range_end = batch_index_to
        # if it's the first value, set influence range from 1.0 to 0.0
        if buffer > 0:
            if i == 0:
                range_start = 0
            elif i == 1:
                range_start = buffer
        else:
            if i == 1:
                range_start = 0
        
        if i == number_of_items - 1:
            range_end = last_key_frame_position

        steps = range_end - range_start
        diff = strength_to - strength_from

        # Calculate index for interpolation
        index = np.linspace(0, 1, steps // 2 + 1) if revert_direction_at_midpoint else np.linspace(0, 1, steps)

        # Calculate weights based on interpolation type
        if interpolation == "linear":
            weights = np.linspace(strength_from, strength_to, len(index))
        elif interpolation == "ease-in":
            weights = diff * np.power(index, 2) + strength_from
        elif interpolation == "ease-out":
            weights = diff * (1 - np.power(1 - index, 2)) + strength_from
        elif interpolation == "ease-in-out":
            weights = diff * ((1 - np.cos(index * np.pi)) / 2) + strength_from
        
        if revert_direction_at_midpoint:
            weights = np.concatenate([weights, weights[::-1]])
                        
        # Generate frame numbers
        frame_numbers = np.arange(range_start, range_start + len(weights))

        # "Dropper" component: For keyframes with negative start, drop the weights
        if range_start < 0 and i > 0:
            drop_count = abs(range_start)
            weights = weights[drop_count:]
            frame_numbers = frame_numbers[drop_count:]

        # Dropper component: for keyframes a range_End is greater than last_key_frame_position, drop the weights
        if range_end > last_key_frame_position and i < number_of_items - 1:
            drop_count = range_end - last_key_frame_position
            weights = weights[:-drop_count]
            frame_numbers = frame_numbers[:-drop_count]

        return weights, frame_numbers 
    weights_list = []
    frame_numbers_list = []

    for i in range(len(keyframe_positions)):

        keyframe_position = keyframe_positions[i]                                    
        interpolation = "ease-in-out"
        # strength_from = strength_to = 1.0
                                    
        if i == 0: # buffer
            
            if buffer > 0:  # First image with buffer
                
                strength_from = strength_to = strength_values[0][1]                    
            else:
                continue  # Skip first image without buffer
            batch_index_from = 0
            batch_index_to_excl = buffer
            weights, frame_numbers = find_curve(batch_index_from, batch_index_to_excl, strength_from, strength_to, interpolation, False, last_key_frame_position, i, len(keyframe_positions), buffer)                                    
        
        elif i == 1: # first image 

            # GET IMAGE AND KEYFRAME INFLUENCE VALUES                                     
            key_frame_influence_from, key_frame_influence_to = key_frame_influence_values[0]                                
            start_strength, mid_strength, end_strength = strength_values[0]
                            
            keyframe_position = keyframe_positions[i]
            next_key_frame_position = keyframe_positions[i+1]
            
            batch_index_from = keyframe_position                
            batch_index_to_excl = calculate_influence_frame_number(keyframe_position, next_key_frame_position, key_frame_influence_to)
            weights, frame_numbers = find_curve(batch_index_from, batch_index_to_excl, mid_strength, end_strength, interpolation, False, last_key_frame_position, i, len(keyframe_positions), buffer)                                    
            # interpolation = "ease-in"                                
        
        elif i == len(keyframe_positions) - 1:  # last image
            
            # GET IMAGE AND KEYFRAME INFLUENCE VALUES            
            key_frame_influence_from,key_frame_influence_to = key_frame_influence_values[i-1]       
            start_strength, mid_strength, end_strength = strength_values[i-1]
            # strength_from, strength_to = cn_strength_values[i-1]

            keyframe_position = keyframe_positions[i]
            previous_key_frame_position = keyframe_positions[i-1]

            batch_index_from = calculate_influence_frame_number(keyframe_position, previous_key_frame_position, key_frame_influence_from)
            batch_index_to_excl = keyframe_position
            weights, frame_numbers = find_curve(batch_index_from, batch_index_to_excl, start_strength, mid_strength, interpolation, False, last_key_frame_position, i, len(keyframe_positions), buffer)                                    
            # interpolation =  "ease-out"                                
        
        else:  # middle images

            # GET IMAGE AND KEYFRAME INFLUENCE VALUES              
            key_frame_influence_from,key_frame_influence_to = key_frame_influence_values[i-1]             
            start_strength, mid_strength, end_strength = strength_values[i-1]
            keyframe_position = keyframe_positions[i]
                        
            # CALCULATE WEIGHTS FOR FIRST HALF
            previous_key_frame_position = keyframe_positions[i-1]   
            batch_index_from = calculate_influence_frame_number(keyframe_position, previous_key_frame_position, key_frame_influence_from)                
            batch_index_to_excl = keyframe_position                
            first_half_weights, first_half_frame_numbers = find_curve(batch_index_from, batch_index_to_excl, start_strength, mid_strength, interpolation, False, last_key_frame_position, i, len(keyframe_positions), buffer)                
            
            # CALCULATE WEIGHTS FOR SECOND HALF                
            next_key_frame_position = keyframe_positions[i+1]
            batch_index_from = keyframe_position
            batch_index_to_excl = calculate_influence_frame_number(keyframe_position, next_key_frame_position, key_frame_influence_to)                                
            second_half_weights, second_half_frame_numbers = find_curve(batch_index_from, batch_index_to_excl, mid_strength, end_strength, interpolation, False, last_key_frame_position, i, len(keyframe_positions), buffer)
            
            # COMBINE FIRST AND SECOND HALF
            weights = np.concatenate([first_half_weights, second_half_weights])                
            frame_numbers = np.concatenate([first_half_frame_numbers, second_half_frame_numbers])
        
        weights_list.append(weights)
        frame_numbers_list.append(frame_numbers)

    return weights_list, frame_numbers_list

def plot_weights(weights_list, frame_numbers_list):
    plt.figure(figsize=(12, 6))

    # Drop the first list of values from both lists
    weights_list = weights_list[1:]
    frame_numbers_list = frame_numbers_list[1:]

    for i, weights in enumerate(weights_list):
        frame_numbers = frame_numbers_list[i]
        plt.plot(frame_numbers, weights, label=f'Frame {i + 1}')

    # Plot settings
    plt.xlabel('Frame Number')
    plt.ylabel('Weight')
    plt.legend()
    plt.ylim(0, 1.0)
    plt.show()
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot()
import gradio as gr
from datetime import datetime
import os
from api_interaction import analyze_image_with_api
from PIL import Image
import numpy as np
from database import Entry, Session
import pandas as pd
import sqlite3
from pathlib import Path


# Directory to save images and other data
flagging_directory = os.path.join(os.path.expanduser("~"), "MyAppData")
if not os.path.exists(flagging_directory):
    os.makedirs(flagging_directory)

# Function to create a color block image from a hex color
def create_color_block(hex_color):
    hex_color = hex_color.lstrip('#')
    rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    width, height = 80, 80
    color_block = np.full((height, width, 3), rgb_color, dtype=np.uint8)
    color_image = Image.fromarray(color_block, 'RGB')
    return color_image


# Function to process the image and return analysis results
def process_image(image):
    try:
        result = analyze_image_with_api(image)
        timestamp = datetime.now()

        # Save the uploaded image to the disk and get the path
        uploaded_image_path = os.path.join(flagging_directory, f"uploaded_{timestamp.strftime('%Y%m%d_%H%M%S')}.png")
        Image.open(image).save(uploaded_image_path)

        # Create the color block image, save it to disk, and get the path
        skin_shade_color_pil = create_color_block(result[0])
        skin_color_image_path = os.path.join(flagging_directory, f"color_block_{timestamp.strftime('%Y%m%d_%H%M%S')}.png")
        skin_shade_color_pil.save(skin_color_image_path)

        entry_id = add_entry_to_db(result[0], result[1], uploaded_image_path, skin_color_image_path)

        return result[0], result[1], timestamp.strftime("%Y-%m-%d %H:%M:%S"), skin_shade_color_pil, entry_id
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


# Function to add an entry to the database
def add_entry_to_db(skin_shade, tone_range, uploaded_image_path, skin_color_image_path, notes=''):
    session = Session()
    try:
        # Create a new entry with the given details and save to the database
        new_entry = Entry(
            skin_shade=skin_shade,
            tone_range=tone_range,
            timestamp=datetime.utcnow(),
            notes=notes,
            uploaded_image_path=uploaded_image_path,
            skin_color_image_path=skin_color_image_path
        )
        session.add(new_entry)
        session.commit()
        entry_id = new_entry.id  # Get the id of the newly created entry
        return entry_id  # Return the entry ID for later reference
    except Exception as e:
        session.rollback()
        print(f"An error occurred while adding the entry: {e}")
        return None  # Return None if there was an error
    finally:
        session.close()



# Function to save the notes for an entry in the database
def save_notes(entry_id, notes):
    session = Session()
    try:
        entry = session.get(Entry, entry_id)
        if entry:
            entry.notes = notes
            session.commit()
            return "Notes saved!"
        else:
            return "Entry not found."
    except Exception as e:
        session.rollback()
        return f"An error occurred: {e}"
    finally:
        session.close()



# Function to get the history of all entries from the database
def get_history():
    session = Session()
    entries = session.query(Entry).order_by(Entry.timestamp.desc()).all()
    history = []
    for entry in entries:
        entry_data = {
            "Skin Shade": entry.skin_shade,
            "Tone Range": entry.tone_range,
            "Timestamp": entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Notes": entry.notes,
            "Uploaded Image Path": entry.uploaded_image_path,
            "Skin Color Image Path": entry.skin_color_image_path
        }
        history.append(entry_data)
    session.close()
    
    # Convert the list of dictionaries into a Pandas DataFrame
    history_df = pd.DataFrame(history)
    return history_df


def export_db_to_csv(db_filename, csv_filename, table_name):
    # Construct the full paths for the database and the CSV file
    db_path = Path(db_filename)
    csv_path = csv_filename  # CSV file will be saved in the /mnt/data directory
    
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    
    # Read data from the specified table into a pandas DataFrame
    query = f"SELECT * FROM {table_name};"
    df = pd.read_sql_query(query, conn)
    
    # Export the DataFrame to a CSV file
    df.to_csv(csv_path, index=False)
    
    # Close the database connection
    conn.close()
    
    return csv_path 


# Gradio interface setup
with gr.Blocks() as demo:
    gr.Markdown("## MySkin Shade Journal")
    with gr.Column():
        image_input = gr.Image(type="filepath", label="Upload your image")
        submit_button = gr.Button("Analyze Image")
        skin_shade_color = gr.Image(type="pil", label="Skin Shade Color", height=60, width=60)
        skin_shade_output = gr.Textbox(label="Skin Shade", interactive=False)
        tone_range_output = gr.Textbox(label="Tone Range", interactive=False)
        timestamp_output = gr.Textbox(label="Timestamp", interactive=False)
        notes_input = gr.Textbox(lines=4, placeholder="Enter notes about your skin, products used, and other important information", label="Notes")
        save_notes_button = gr.Button("Save Notes")
        get_history_button = gr.Button("Get History")
        history_output = gr.Dataframe()
        entry_id_output = gr.Textbox(label="Entry ID", visible=False)
        export_button = gr.Button("Export History")



    # Define button click actions
    submit_button.click(
        fn=process_image,
        inputs=[image_input],
        outputs=[skin_shade_output, tone_range_output, timestamp_output, skin_shade_color, entry_id_output]
    )

    # Update the action for the save notes button to update the database
    save_notes_button.click(
        fn=save_notes,
        inputs=[entry_id_output, notes_input],
        outputs=[]
    )

    get_history_button.click(
        fn=get_history,
        inputs=[],
        outputs=[history_output]
    
    )

    export_button.click(
        fn=lambda: export_db_to_csv('myapp.db', 'exported_history.csv', 'entries'),
        inputs=[],
        outputs=[gr.File(label="Download CSV", type="filepath")]
    )



if __name__ == "__main__":
    demo.launch(debug=True)

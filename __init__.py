from aqt import mw
from aqt.qt import *
from aqt.reviewer import Reviewer
from anki.hooks import addHook
from functools import wraps
import os
import json

# File to store XP progress (Global across all decks)
XP_FILE = os.path.join(mw.addonManager.addonsFolder(), "civilizationevolution", "xp_data.json")

# Resource folder for images (700x700)
RESOURCE_FOLDER = os.path.join(mw.addonManager.addonsFolder(), "civilizationevolution", "resources")

def load_xp():
    """Load XP from the saved file or initialize XP at 0 if it's the first install."""
    if os.path.exists(XP_FILE):
        with open(XP_FILE, "r") as f:
            return json.load(f)
    
    # If file does not exist, start XP at 0 and Level at 0
    initial_xp = {"xp": 0.0, "level": 0}
    save_xp(initial_xp)
    return initial_xp

def save_xp(xp_data):
    """Save XP data to a file."""
    with open(XP_FILE, "w") as f:
        json.dump(xp_data, f)

def add_xp(ease):
    """Grant XP based on review answer."""
    xp_data = load_xp()
    previous_xp = xp_data["xp"]  # Store previous XP before adding

    # Fix XP gains: "Good" (Ease=3) → +0.2 XP, "Easy" (Ease=4) → +0.4 XP
    if ease == 3:  # "Good"
        xp_data["xp"] += 0.2
    elif ease == 4:  # "Easy"
        xp_data["xp"] += 0.4

    # Show lvl_0.png ONLY at exactly 0.4 XP
    if previous_xp < 0.4 and xp_data["xp"] >= 0.4:
        show_level_up_popup("0")  # This will display lvl_0.png

    # Show lvl_0.5.png (Quest Info) ONLY when XP crosses 4 XP
    if previous_xp < 4 and xp_data["xp"] >= 4:
        show_level_up_popup("0.5")  # This will display lvl_0.5.png

    # Standard level-up logic (every 20 XP)
    new_level = min(52, int(xp_data["xp"] // 20))
    previous_level = int(previous_xp // 20)

    if new_level > previous_level and new_level > 0:
        xp_data["level"] = new_level
        show_level_up_popup(str(new_level))

    save_xp(xp_data)
    update_xp_meter()

def show_level_up_popup(level):
    """Show a pop-up when the player levels up with full image scaling for 700x700 images."""
    if level == "0":
        image_path = os.path.join(RESOURCE_FOLDER, "lvl_0.png")
        msg = "🌟 Welcome, Player! Your civilization journey begins now!"
    elif level == "0.5":
        image_path = os.path.join(RESOURCE_FOLDER, "lvl_0.5.png")
        msg = (
            "📜 <b>Quest Info</b> <br><br>"
            "<b>Instructions:</b><br>"
            "Build the Hunter-Gatherer Age ~300,000 BCE - ~10,000 BCE<br><br>"
            "1. 🌱 <b>Level 1-10:</b> The Dawn of Humanity (Pre-Homo Sapiens)<br>"
            "2. 🔥 <b>Level 11-20:</b> Early Homo Sapiens (Advanced Tool Use & Survival)<br>"
            "3. 🏹 <b>Level 21-30:</b> Advanced Hunting & Tribal Life<br>"
            "4. 🌾 <b>Level 31-40:</b> Early Settlements & Complex Society<br>"
            "5. 🚀 <b>Level 41-50:</b> Towards the Neolithic Revolution"
        )
    else:
        image_path = os.path.join(RESOURCE_FOLDER, f"lvl_{level}.png")
        msg = f"🎉 <b>Level Up! You have reached Level {level}!</b><br>Your civilization is evolving!"

    # Ensure image exists
    if not os.path.exists(image_path):
        return  # If image is missing, do nothing

    popup = QDialog()
    popup.setWindowTitle("Level Up!")

    # Load the image
    pixmap = QPixmap(image_path)

    # Create a layout
    layout = QVBoxLayout()

    # Add text message
    label_text = QLabel(msg)
    label_text.setAlignment(Qt.AlignCenter)
    label_text.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")

    # Add image label
    label_image = QLabel()
    label_image.setPixmap(pixmap)
    label_image.setAlignment(Qt.AlignCenter)
    label_image.setScaledContents(True)

    # Resize the pop-up dynamically based on image size (700x700)
    popup.setFixedSize(750, 780)  # Slightly larger for spacing

    # Add OK button
    button = QPushButton("OK")
    button.setStyleSheet("font-size: 16px; padding: 10px;")
    button.clicked.connect(popup.accept)

    # Add widgets to layout
    layout.addWidget(label_text)
    layout.addWidget(label_image)
    layout.addWidget(button)

    popup.setLayout(layout)
    popup.exec_()

def update_xp_meter():
    """Update the XP meter globally in the main Anki window."""
    xp_data = load_xp()
    mw.xp_label.setText(f"🌟 XP: {xp_data['xp']:.2f} | Level: {xp_data['level']} / 52")
    mw.app.processEvents()  # Forces UI update immediately

def add_xp_meter_to_ui():
    """Add XP meter to the main Anki window."""
    xp_data = load_xp()

    # Create label for XP meter
    mw.xp_label = QLabel(f"🌟 XP: {xp_data['xp']:.2f} | Level: {xp_data['level']} / 52")
    mw.xp_label.setAlignment(Qt.AlignCenter)
    mw.xp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: blue;")

    # Add XP label to the Anki main window
    mw.statusBar().addPermanentWidget(mw.xp_label)

    # Update it whenever the user changes decks
    addHook("deckBrowserDidRender", update_xp_meter)

# Hook into Anki's review system to track XP properly
original_answer_card = Reviewer._answerCard

@wraps(original_answer_card)
def new_answer_card(self, ease):
    """Hook into Anki when a review is answered."""
    add_xp(ease)  # Update XP immediately
    update_xp_meter()  # Ensure the UI updates instantly
    original_answer_card(self, ease)  # Call Anki's original function

# Override Anki's default review function
Reviewer._answerCard = new_answer_card

# Add XP meter to Anki's UI
addHook("profileLoaded", add_xp_meter_to_ui)
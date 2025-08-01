import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import QSize, QCoreApplication, Qt, QTimer
from PyQt6.QtGui import QIcon, QKeyEvent

from chat_ui.voice_recorder import VoiceRecorder
from chat_ui.components.VoiceToggleSwitch import VoiceToggleSwitch
from chat_ui.right.chat_window import UserInputEvent
from chat_ui.services.persona_service import PersonaService


class ChatInputTextEdit(QTextEdit):

    # === Initialization
    # ✅ Sets up the text edit with custom key handling for sending messages
    def __init__(self, parent=None, send_callback=None):
        super().__init__(parent)
        self.send_callback = send_callback

    # === Key Press Event
    # ✅ Handles Enter/Return key for sending messages, Shift+Enter for new line
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                if self.send_callback:
                    self.send_callback()
        else:
            super().keyPressEvent(event)


class ChatInput(QWidget):

    # === Initialization
    # ✅ Sets up the chat input UI with voice toggle and text entry
    def __init__(self, chat_window, parent=None):
        super().__init__(parent)
        self.chat_window = chat_window
        self.recorder = VoiceRecorder()
        self.voice_mode = False

        # === Main Layout ===
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # === Outer Layout ===
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 20)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

        # === Voice toggle row ===
        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 0, 6, 0)
        toggle_row.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.voice_toggle = VoiceToggleSwitch()
        toggle_row.addWidget(self.voice_toggle)
        outer_layout.addLayout(toggle_row)

        # === Chat input bubble ===
        self.bubble = QFrame()
        self.bubble.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        self.bubble.setStyleSheet("""
            QFrame {
                background-color: #333;
                border-radius: 12px;
            }
        """)
        self.bubble_layout = QVBoxLayout(self.bubble)
        self.bubble_layout.setContentsMargins(6, 8, 6, 6)
        self.bubble_layout.setSpacing(4)

        # === Text entry area ===
        self.entry = ChatInputTextEdit(send_callback=self.send_message)
        self.entry.setPlaceholderText("Start typing...")
        self.entry.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 6px;
                font-size: 14px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 4px 0;
            }
            QScrollBar::handle:vertical {
                background: #888;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #aaa;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # === Size and Scroll Behavior ===
        self.entry.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.entry.setMinimumHeight(36)
        self.entry.setMaximumHeight(120)
        self.entry.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.entry.textChanged.connect(self.adjust_textedit_height)
        self.bubble_layout.addWidget(self.entry)

        # === Bottom row with buttons ===
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(8)

        # === Left and Right Button Layouts ===
        left_buttons = QHBoxLayout()
        left_buttons.setSpacing(6)
        left_buttons.setAlignment(Qt.AlignmentFlag.AlignLeft)

        right_buttons = QHBoxLayout()
        right_buttons.setSpacing(6)
        right_buttons.setAlignment(Qt.AlignmentFlag.AlignRight)

        # === Chat Toggle Button ===
        self.chat_toggle_button = QPushButton()
        self.chat_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_toggle_button.setIcon(QIcon("chat_ui/assets/chat.svg"))
        self.chat_toggle_button.setIconSize(QSize(18, 18))
        self.chat_toggle_button.setFixedSize(30, 30)
        self.chat_toggle_button.setCheckable(True)
        self.chat_toggle_button.setChecked(True)
        self.chat_toggle_button.clicked.connect(self.toggle_chat_window)

        # === Microphone Button ===
        self.mic_button = QPushButton()
        self.mic_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_button.setIcon(QIcon("chat_ui/assets/mic.svg"))
        self.mic_button.setIconSize(QSize(18, 18))
        self.mic_button.setFixedSize(30, 30)
        self.mic_button.setCheckable(True)
        self.mic_button.clicked.connect(self.toggle_mic)

        # === Send Button ===
        self.send_button = QPushButton()
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.setIcon(QIcon("chat_ui/assets/arrow-up-circle-fill.svg"))
        self.send_button.setIconSize(QSize(22, 22))
        self.send_button.setFixedSize(32, 32)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("border: none; background-color: transparent;")

        # === Style for Toggle Buttons ===
        toggle_style = """
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:checked {
                background-color: #555;
                border-radius: 6px;
            }
        """
        for btn in [self.chat_toggle_button, self.mic_button]:
            btn.setStyleSheet(toggle_style)

        # === Add buttons to layouts ===
        right_buttons.addWidget(self.chat_toggle_button)
        right_buttons.addWidget(self.mic_button)
        right_buttons.addWidget(self.send_button)

        bottom_row.addLayout(left_buttons)
        bottom_row.addStretch()
        bottom_row.addLayout(right_buttons)
        self.bubble_layout.addLayout(bottom_row)

        outer_layout.addWidget(self.bubble)

        # === Final adjustments ===
        self.set_input_mode("keyboard")
        self.adjust_textedit_height()

    # === Adjust TextEdit Height
    # ✅ Dynamically adjusts the height of the text entry based on content
    def adjust_textedit_height(self):
        doc_height = self.entry.document().size().height()
        padding = 20
        total_height = int(doc_height + padding)
        capped_height = min(max(36, total_height), 120)
        self.entry.setFixedHeight(capped_height)

    # === Set Input Mode
    # ✅ Switches between keyboard and voice input modes
    def set_input_mode(self, mode):
        self.voice_mode = (mode == "mic")

        if self.voice_mode:
            self.entry.setPlaceholderText("Listening...")
            self.send_button.setEnabled(False)
            self.mic_button.setIcon(QIcon("chat_ui/assets/stop.svg"))
            self.mic_button.setChecked(True)

            self.recorder.continuous_mode = True
            self.recorder.start_recording_async(
                self.voice_input_callback,
                on_status=self.update_status
            )
        else:
            self.recorder.stop()
            self.entry.setPlaceholderText("Start typing...")
            self.send_button.setEnabled(True)
            self.mic_button.setIcon(QIcon("chat_ui/assets/mic.svg"))
            self.mic_button.setChecked(False)

    # === Send Message
    # ✅ Handles sending messages from the text entry
    def send_message(self):
        message = self.entry.toPlainText().strip()
        if not message:
            return

        self.entry.clear()
        self.adjust_textedit_height()

        # Detect "switch to ..." or "swap to ..."
        match = re.match(r"^(?:switch|swap)\s+to\s+(.+)$", message.lower())
        if match:
            persona_name = match.group(1).strip()
            print(f"🔄 Typed command detected — switching to persona: {persona_name}")
            PersonaService.select_persona(persona_name)

            self.entry.setPlaceholderText(f"Switched to {persona_name}")
            QTimer.singleShot(2000, lambda: self.entry.setPlaceholderText("Start typing..."))
            return

        # Normal message
        QCoreApplication.postEvent(self.chat_window, UserInputEvent(message))

    # === Status Updates
    # ✅ Updates the input box placeholder based on voice recorder status
    def update_status(self, text):
        if "stopped" in text.lower():
            self.set_input_mode("keyboard")
        elif "listening" in text.lower():
            self.entry.setPlaceholderText("Listening…")
        else:
            self.entry.setPlaceholderText(text)

    # === Voice Input Callback
    # ✅ Called by the voice recorder with transcribed text
    def voice_input_callback(self, transcript):
        QCoreApplication.postEvent(self.chat_window, UserInputEvent(transcript))

    # === Toggle Chat Window
    # ✅ Toggles the visibility of the chat window
    def toggle_chat_window(self):
        is_visible = self.chat_window.isVisible()
        self.chat_window.setVisible(not is_visible)
        self.chat_toggle_button.setChecked(not is_visible)

    # === Toggle Microphone
    # ✅ Toggles the microphone input mode
    def toggle_mic(self):
        if self.voice_mode:
            self.set_input_mode("keyboard")
        else:
            self.set_input_mode("mic")

    # === Check if voice input is enabled
    # ✅ Returns whether the voice toggle is enabled
    def is_voice_enabled(self):
        return self.voice_toggle.is_enabled()
    
    # === Send Greeting Message
    # ✅ Automatically sends a greeting message after persona switch
    def send_greeting_message(self):
        """
        Sends an automatic greeting request after persona swap.
        This triggers AI bubble + TTS if enabled.
        """
        message = "Introduce yourself briefly as the new persona."
        print(f"🤖 Auto-sending greeting message: {message}")
        QCoreApplication.postEvent(self.chat_window, UserInputEvent(message))


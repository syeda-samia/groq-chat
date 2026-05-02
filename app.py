import streamlit as st
from groq import Groq
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import io
import tempfile
import os
import subprocess
import numpy as np
import librosa
from scipy.io import wavfile

# 🔥 SMART FFMPEG DETECTION
FFMPEG_AVAILABLE = False
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    FFMPEG_AVAILABLE = True
except:
    pass

try:
    LIBROSA_AVAILABLE = True
except:
    LIBROSA_AVAILABLE = False

# PAGE CONFIG
st.set_page_config(page_title="Samia's Chatbot", layout="wide")

# 🔥 HUGGING FACE SECRETS (instead of st.secrets)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.warning("GROQ_API_KEY is not set in Space Secrets.")
else:
    client = Groq(api_key=GROQ_API_KEY)


client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# SESSION STATE
# -----------------------------
if "last_voice_text" not in st.session_state:
    st.session_state.last_voice_text = ""
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None
if "show_about" not in st.session_state:
    st.session_state.show_about = False

# -----------------------------
# FUNCTIONS
# -----------------------------
@st.dialog("ℹ️ About Nova AI")
def show_about():
    st.markdown("""
    # 🚀 Nova AI SaaS Chatbot
    ✔ Groq AI powered  
    ✔ Streamlit UI  
    ✔ Chat history system  
    ✔ Smart AI Assistant  
    ✔ Voice input (Smart FFmpeg)
    ✔ Full animations!
    """)

def generate_chat_title(user_message):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Generate a very short title (max 5-6 words). Return ONLY the title."},
                {"role": "user", "content": user_message}
            ],
            stream=False,
            temperature=0.3
        )
        title = response.choices[0].message.content.strip()
        if len(title) > 30:
            title = title[:27] + "..."
        return title
    except:
        return user_message[:25] + ("..." if len(user_message) > 25 else "")

def create_chat(first_msg=None):
    chat_id = f"chat_{len(st.session_state.chats) + 1}"
    if first_msg:
        name = generate_chat_title(first_msg)
    else:
        name = "New Chat"
    st.session_state.chats[chat_id] = {"name": name, "messages": []}
    st.session_state.current_chat = chat_id

if not st.session_state.chats:
    create_chat()

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.title("💬 Chats")
    if st.button("➕ New Chat"):
        create_chat()
        st.rerun()
    if st.button("ℹ️ About App"):
        st.session_state.show_about = True

    st.title("🔍 History")   
    for chat_id, chat in st.session_state.chats.items():
        col1, col2, col3 = st.columns([3, 1, 1])
        if col1.button(chat["name"], key=chat_id, use_container_width=True):
            st.session_state.current_chat = chat_id
            st.rerun()
        
        if col2.button("✏️", key="edit_" + chat_id):
            st.session_state[f"editing_{chat_id}"] = True
        
        if col3.button("🗑", key="del_" + chat_id):
            del st.session_state.chats[chat_id]
            if st.session_state.chats:
                st.session_state.current_chat = list(st.session_state.chats.keys())[0]
            else:
                create_chat()
            st.rerun()
        
        if st.session_state.get(f"editing_{chat_id}", False):
            new_name = st.text_input("Rename chat:", value=chat["name"], key=f"rename_{chat_id}")
            col_ok, col_cancel = st.columns(2)
            if col_ok.button("✅", key=f"save_{chat_id}"):
                if new_name.strip():
                    st.session_state.chats[chat_id]["name"] = new_name.strip()
                st.session_state[f"editing_{chat_id}"] = False
                st.rerun()
            if col_cancel.button("❌", key=f"cancel_{chat_id}"):
                st.session_state[f"editing_{chat_id}"] = False
                st.rerun()

    st.markdown("---")
    st.caption("Nova AI")

if st.session_state.show_about:
    show_about()
    st.session_state.show_about = False

# -----------------------------
# CURRENT CHAT
# -----------------------------
chat_id = st.session_state.current_chat
chat = st.session_state.chats[chat_id]
messages = chat["messages"]

if chat["name"] == "New Chat" and messages:
    first_user_msg = None
    for msg in messages:
        if msg["role"] == "user":
            first_user_msg = msg["content"]
            break
    if first_user_msg:
        chat["name"] = generate_chat_title(first_user_msg)

# -----------------------------
# 🔥 ALL ORIGINAL CSS ANIMATIONS
# -----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {animation: fadeInApp 0.8s ease-in;}
@keyframes fadeInApp {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: translateY(0);}}
[data-testid="stChatMessage"] {animation: popIn 0.35s ease forwards;}
@keyframes popIn {from {opacity:0; transform: scale(0.96) translateY(8px);} to {opacity:1; transform: scale(1) translateY(0);}}
.typing-cursor {animation: blink 1s infinite;}
@keyframes blink {0% {opacity: 1;} 50% {opacity: 0;} 100% {opacity: 1;}}
section[data-testid="stSidebar"] button:hover {transform: scale(1.03); transition: 0.2s; box-shadow: 0 0 10px #8b5cf6;}
[data-testid="stChatInput"] textarea:focus {box-shadow: 0 0 12px #22c55e;}
.avatar-pulse img {animation: pulse 2.5s infinite;}
@keyframes pulse {0% {box-shadow: 0 0 0 0 rgba(14,165,233,0.7);} 70% {box-shadow: 0 0 0 15px rgba(14,165,233,0);} 100% {box-shadow: 0 0 0 0 rgba(14,165,233,0);}}
.header-float {animation: floatHeader 4s ease-in-out infinite;}
@keyframes floatHeader {0% {transform: translateY(0px);} 50% {transform: translateY(-6px);} 100% {transform: translateY(0px);}}
.main .block-container {padding-bottom: 100px !important;}
.stChatInputContainer {position: fixed !important; bottom: 0px !important; left: 0 !important; right: 0 !important; background-color: #0e1117 !important; padding: 15px 20px !important; z-index: 999 !important; border-top: 1px solid #2d2d2d !important;}
.header-float h2 {background: linear-gradient(to right, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #ffeaa7, #dfe6e9); background-size: 300% auto; -webkit-background-clip: text; background-clip: text; color: transparent; animation: textShine 4s linear infinite;}
@keyframes textShine {0% { background-position: 0% 50%; } 100% { background-position: 200% 50%; }}
section[data-testid="stSidebar"] button {background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #f5576c); background-size: 200% auto; transition: all 0.3s ease; animation: sidebarButtonPulse 2s ease-in-out infinite;}
section[data-testid="stSidebar"] button:hover {background-position: right center; transform: scale(1.02) translateX(5px); box-shadow: 0 0 15px rgba(102, 126, 234, 0.5);}
@keyframes sidebarButtonPulse {0% {opacity: 1;} 50% {opacity: 0.85; box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);} 100% {opacity: 1;}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
col1, col2 = st.columns([1, 8])
with col1:
    st.markdown('<div class="avatar-pulse">', unsafe_allow_html=True)
    # Add your pic.png to the repo or use this placeholder
    st.image("https://via.placeholder.com/100x100/667eea/ffffff?text=AI", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="header-float"><h2>WELCOME SAMIA\'S CHATBOT</h2></div>', unsafe_allow_html=True)
    st.caption("Smart AI Chat Assistant")
st.markdown("---")

# -----------------------------
# CHAT HISTORY
# -----------------------------
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.markdown("<div id='bottom-anchor' style='height: 80px;'></div>", unsafe_allow_html=True)

# -----------------------------
# INPUT SECTION (HF READY)
# -----------------------------
col_input, col_mic = st.columns([0.85, 0.15])

with col_input:
    # ✅ HF READY: Using st.chat_input()
    text_input = st.chat_input("Ask something...", key="chat_input")

with col_mic:
    st.markdown("<div style='margin-top: 5px;'>", unsafe_allow_html=True)
    audio = mic_recorder(
        start_prompt="🎤", 
        stop_prompt="⏹", 
        key=f"mic_{st.session_state.current_chat}",
        just_once=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# TEXT INPUT HANDLING
# -----------------------------
if text_input:
    messages.append({"role": "user", "content": text_input})
    with st.chat_message("user"):
        st.markdown(text_input)
    
    with st.chat_message("assistant"):
        with st.spinner("🤖 AI is thinking..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=messages, 
                stream=False
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            messages.append({"role": "assistant", "content": reply})
    
    st.rerun()

# -----------------------------
# 🔥 VOICE INPUT (HF READY)
# -----------------------------
if audio and isinstance(audio, dict) and audio.get("bytes"):
    try:
        audio_bytes = audio["bytes"]
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path.close()
        
        # 🔥 SMART PROCESSING
        if FFMPEG_AVAILABLE:
            from pydub import AudioSegment
            sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
            sound = sound.set_channels(1).set_frame_rate(16000)
            sound.export(temp_path.name, format="wav")
            st.info("🎵 FFmpeg (Max Quality)")
        elif LIBROSA_AVAILABLE:
            audio_array, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000, mono=True)
            wavfile.write(temp_path.name, 16000, (audio_array * 32767).astype(np.int16))
            st.info("🎵 Librosa (Pure Python)")
        else:
            st.warning("📱 Install: `pip install librosa scipy` for voice")
            st.rerun()
        
        # Speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_path.name) as source:
            audio_data = recognizer.record(source)
        voice_text = ""
        try:
            voice_text = recognizer.recognize_google(audio_data)
            st.success(f"🎤 Heard: {voice_text}")
        except:
            st.error("🤷 Could not understand audio")
        
        # Cleanup
        try:
            os.unlink(temp_path.name)
        except:
            pass
        
        if voice_text and voice_text != st.session_state.last_voice_text:
            st.session_state.last_voice_text = voice_text
            messages.append({"role": "user", "content": voice_text})
            with st.chat_message("user"):
                st.markdown(voice_text)
            
            with st.chat_message("assistant"):
                with st.spinner("🤖 AI is thinking..."):
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant", 
                        messages=messages, 
                        stream=False
                    )
                    reply = response.choices[0].message.content
                    st.markdown(reply)
                    messages.append({"role": "assistant", "content": reply})
            st.rerun()
            
    except Exception as e:
        st.error(f"Voice error: {e}")

# -----------------------------
# 🔥 FULL AUTO-SCROLL
# -----------------------------
st.markdown("""
<script>
    function scrollToBottom() {
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
        const anchor = document.getElementById('bottom-anchor');
        if (anchor) {
            anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }
    
    setTimeout(scrollToBottom, 100);
    
    const observer = new MutationObserver(function() {
        setTimeout(scrollToBottom, 50);
    });
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)
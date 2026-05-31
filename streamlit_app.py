import streamlit as st
import yt_dlp
import os
import shutil
import re
import tempfile
import platform

# Resolve paths robustly for local and Streamlit Cloud environments
script_dir = os.path.dirname(os.path.abspath(__file__))
cookie_path = os.path.join(script_dir, 'cookies.txt')
is_mac = platform.system() == 'Darwin'

# Page configuration
st.set_page_config(
    page_title="Taher YouTube Downloader",
    page_icon="🎥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom premium CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Main body background */
    .stApp {
        background: linear-gradient(180deg, #07070a 0%, #000000 100%);
        font-family: 'Outfit', sans-serif;
        color: #ffffff;
    }
    
    /* Container styling */
    .main-card {
        background: rgba(10, 10, 10, 0.95);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 35px;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.95);
        margin-bottom: 25px;
    }
    
    /* Header typography */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        background: linear-gradient(45deg, #ff0055, #ffaa00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Custom button styling */
    div.stButton > button {
        background: linear-gradient(90deg, #ff0055 0%, #ff5500 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(255, 0, 85, 0.35) !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(255, 0, 85, 0.5) !important;
    }
    
    /* Input field styling */
    .stTextInput input {
        background: #000000 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 14px !important;
        color: #ffffff !important;
        padding: 14px !important;
        font-size: 16px !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.6) !important;
    }
    .stTextInput input:focus {
        border-color: #ff0055 !important;
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.3) !important;
    }
    
    /* Dropdown selection */
    .stSelectbox div[data-baseweb="select"] {
        background: #000000 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to find JS runtime (Node/Deno) for macOS and general environments
def find_js_runtime():
    path = shutil.which("node") or shutil.which("deno")
    if path:
        return path
    
    common_paths = [
        "/usr/local/bin/node",
        "/opt/homebrew/bin/node",
        "/usr/local/bin/deno",
        "/opt/homebrew/bin/deno",
        os.path.expanduser("~/.deno/bin/deno"),
    ]
    for p in common_paths:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
            
    return None

# App Layout
st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>🎥 Taher YouTube Downloader</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #b3b3b3; font-size: 1.1rem; margin-bottom: 30px;'>A stunning Streamlit-native client for lightning-fast HD downloads</p>", unsafe_allow_html=True)

st.markdown("<div class='main-card'>", unsafe_allow_html=True)

url = st.text_input("YouTube Video Link:", placeholder="Paste your link here (e.g. https://www.youtube.com/watch?v=...)")

if url:
    # Set up options
    runtime_path = find_js_runtime()
    ydl_opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['web_embedded', 'android']}},
    }
    if os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path
    if is_mac:
        ydl_opts['cookiesfrombrowser'] = ('safari',)
    if runtime_path:
        runtime_name = "deno" if "deno" in runtime_path.lower() else "node"
        ydl_opts['js_runtimes'] = {runtime_name: {'path': runtime_path}}
        
    with st.spinner("🔍 Fetching high-quality format choices..."):
        try:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as first_err:
                # Self-healing fallback: if signed-in cookie session fails, retry anonymously
                if 'cookiefile' in ydl_opts:
                    st.toast("⚠️ Cookie-access failed (YouTube security challenge). Retrying anonymously...")
                    ydl_opts_fallback = ydl_opts.copy()
                    ydl_opts_fallback.pop('cookiefile', None)
                    with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
                        info = ydl.extract_info(url, download=False)
                else:
                    raise first_err
                title = info.get('title', 'Unknown Title')
                thumbnail = info.get('thumbnail', '')
                duration = info.get('duration', 0)
                formats = info.get('formats', [])
                
                # Filter formats to unique resolutions
                available_formats = []
                for f in formats:
                    if f.get('vcodec') != 'none':
                        res = f.get('resolution') or f"{f.get('width', '')}x{f.get('height', '')}"
                        if res and res != "x":
                            available_formats.append({
                                'format_id': f['format_id'],
                                'ext': f['ext'],
                                'resolution': res,
                                'filesize': f.get('filesize'),
                                'acodec': f.get('acodec'),
                                'fps': f.get('fps'),
                            })
                
                unique_formats = {}
                for f in available_formats:
                    res = f['resolution']
                    if res not in unique_formats:
                        unique_formats[res] = f
                    else:
                        if f.get('acodec') != 'none' and unique_formats[res].get('acodec') == 'none':
                            unique_formats[res] = f
                            
                sorted_formats = sorted(unique_formats.values(), key=lambda x: int(str(x['resolution']).split('x')[-1]) if 'x' in str(x['resolution']) else 0, reverse=True)
                
            # Display details
            col1, col2 = st.columns([1, 1.3], gap="medium")
            with col1:
                if thumbnail:
                    st.image(thumbnail, use_container_width=True)
            with col2:
                st.subheader(title)
                h = duration // 3600
                m = (duration % 3600) // 60
                s = duration % 60
                duration_str = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"
                st.markdown(f"**⏱️ Duration:** {duration_str}")
                
                # Format selection
                format_options = ["🌟 Auto - Best Quality (4K/HD)"]
                format_mapping = {"🌟 Auto - Best Quality (4K/HD)": "best"}
                
                for f in sorted_formats:
                    size_mb = f"{round(f['filesize'] / (1024 * 1024), 1)} MB" if f['filesize'] else "Size unknown"
                    fps_str = f" @ {f['fps']}fps" if f['fps'] else ""
                    option_text = f"{f['resolution']} ({f['ext'].upper()}){fps_str} - {size_mb}"
                    format_options.append(option_text)
                    format_mapping[option_text] = f['format_id']
                    
                selected_option = st.selectbox("Choose Quality:", format_options)
                selected_format_id = format_mapping[selected_option]
                
                # Download process
                if st.button("🚀 Fetch and Process"):
                    with st.spinner("📥 Downloading and merging streams with FFMPEG..."):
                        temp_dir = tempfile.mkdtemp()
                        output_template = os.path.join(temp_dir, "video.%(ext)s")
                        
                        dl_format = "bestvideo+bestaudio/best" if selected_format_id == "best" else f"{selected_format_id}+bestaudio/best"
                        
                        dl_opts = {
                            'format': dl_format,
                            'outtmpl': output_template,
                            'merge_output_format': 'mp4',
                            'quiet': True,
                            'nocheckcertificate': True,
                            'concurrent_fragment_downloads': 5,
                            'extractor_args': {'youtube': {'player_client': ['web_embedded', 'android']}},
                        }
                        if os.path.exists(cookie_path):
                            dl_opts['cookiefile'] = cookie_path
                        if is_mac:
                            dl_opts['cookiesfrombrowser'] = ('safari',)
                        if runtime_path:
                            dl_opts['js_runtimes'] = {runtime_name: {'path': runtime_path}}
                            
                        try:
                            try:
                                with yt_dlp.YoutubeDL(dl_opts) as ydl:
                                    dl_info = ydl.extract_info(url, download=True)
                            except Exception as dl_first_err:
                                # Fallback to anonymous download if cookies fail
                                if 'cookiefile' in dl_opts:
                                    st.toast("⚠️ Secure download failed. Retrying anonymously...")
                                    dl_opts_fallback = dl_opts.copy()
                                    dl_opts_fallback.pop('cookiefile', None)
                                    with yt_dlp.YoutubeDL(dl_opts_fallback) as ydl:
                                        dl_info = ydl.extract_info(url, download=True)
                                else:
                                    raise dl_first_err
                                
                                # Find downloaded file
                                downloaded_file = None
                                if 'requested_downloads' in dl_info and len(dl_info['requested_downloads']) > 0:
                                    downloaded_file = dl_info['requested_downloads'][0]['filepath']
                                else:
                                    downloaded_file = ydl.prepare_filename(dl_info)
                                    
                                base = os.path.splitext(downloaded_file)[0]
                                if not os.path.exists(downloaded_file):
                                    if os.path.exists(base + '.mp4'):
                                        downloaded_file = base + '.mp4'
                                    elif os.path.exists(base + '.mkv'):
                                        downloaded_file = base + '.mkv'
                                        
                                if downloaded_file and os.path.exists(downloaded_file):
                                    with open(downloaded_file, "rb") as f:
                                        video_bytes = f.read()
                                        
                                    clean_title = re.sub(r'[^\w\-_\. ]', '_', title)
                                    st.balloons()
                                    st.success("🎉 Processing complete! Save your video below.")
                                    st.download_button(
                                        label="💾 Save Video to Device",
                                        data=video_bytes,
                                        file_name=f"{clean_title}.mp4",
                                        mime="video/mp4",
                                        use_container_width=True
                                    )
                                else:
                                    st.error("Failed to locate downloaded file.")
                        except Exception as dl_err:
                            st.error(f"Download Error: {dl_err}")
                        finally:
                            # Cleanup temp folder
                            try:
                                shutil.rmtree(temp_dir)
                            except:
                                pass
        except Exception as err:
            st.error(f"Error fetching details: {err}")

st.markdown("</div>", unsafe_allow_html=True)

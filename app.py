from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import shutil

app = Flask(__name__)

DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url'].strip()
        if not url:
            return render_template('index.html', error="Please enter a valid YouTube URL.")

        try:
            ydl_opts = {}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])

            available_formats = []
            for f in formats:
                # Show both video-only and video+audio streams
                if f.get('vcodec') != 'none':
                    resolution = f.get('format_note') or f.get('height')
                    filesize_mb = f.get('filesize', 0)
                    filesize_str = f"{round(filesize_mb / (1024*1024), 2)} MB" if filesize_mb else "N/A"
                    available_formats.append({
                        'format_id': f['format_id'],
                        'ext': f['ext'],
                        'resolution': resolution,
                        'filesize': filesize_str,
                        'vcodec': f.get('vcodec'),
                        'acodec': f.get('acodec')
                    })

            return render_template('index.html', url=url, formats=available_formats, title=info.get('title'))

        except Exception as e:
            return render_template('index.html', error=f"Error: {str(e)}")

    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    url = request.form['url'].strip()
    format_id = request.form['format_id'].strip()

    if not url or not format_id:
        return "URL or Format ID missing.", 400

    try:
        ydl_opts = {
            'format': format_id + '+bestaudio/best',  # merge video+audio if separate
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Download error: {str(e)}", 500

@app.after_request
def cleanup(response):
    """Clean downloads folder after each request to save space."""
    try:
        shutil.rmtree(DOWNLOAD_DIR)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    except Exception as e:
        print(f"Cleanup error: {e}")
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
